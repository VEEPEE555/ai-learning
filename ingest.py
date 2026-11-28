"""Step 1: chunk markdown docs, embed them with Ollama, and store them in Qdrant.

Re-running is safe. Each run builds a fresh staging collection, then atomically
points the COLLECTION alias at it, so queries never see an empty or half-built index.
"""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from ollama import Client as OllamaClient
from qdrant_client import QdrantClient
from qdrant_client.models import (
    CreateAlias,
    CreateAliasOperation,
    Distance,
    DeleteAlias,
    DeleteAliasOperation,
    PointStruct,
    VectorParams,
)

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "docs")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DOCS_DIR = Path(os.getenv("DOCS_DIR", "docs"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
EMBED_BATCH = int(os.getenv("EMBED_BATCH", 64))
UPSERT_BATCH = 256

# Preferred split points, strongest first: paragraph, line, word.
SPLIT_SEPARATORS = ("\n\n", "\n", " ")


def _find_split(text: str, start: int, end: int) -> int:
    """Pick the best split inside [start, end), preferring stronger separators.

    Only accepts a split in the second half of the window so chunks stay near
    CHUNK_SIZE. Falls back to a hard cut when the window has no whitespace.
    """
    floor = start + (end - start) // 2
    for sep in SPLIT_SEPARATORS:
        pos = text.rfind(sep, floor, end)
        if pos != -1:
            return pos
    return end


def _snap_to_word(text: str, start: int, limit: int) -> int:
    """Move an overlap start forward to the first word boundary before `limit`."""
    for i in range(start, min(limit, len(text))):
        if text[i - 1].isspace():
            return i
    return start


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks that prefer paragraph, line, then word breaks."""
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(start + size, n)
        if end < n:
            end = _find_split(text, start, end)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        next_start = max(end - overlap, start + 1)
        start = _snap_to_word(text, next_start, end) if next_start > start + 1 else next_start
    return chunks


def embed_all(ollama: OllamaClient, texts: list[str]) -> list[list[float]]:
    """Embed texts in batches instead of one request per chunk."""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i : i + EMBED_BATCH]
        vectors.extend(ollama.embed(model=EMBED_MODEL, input=batch)["embeddings"])
        print(f"embedded {min(i + EMBED_BATCH, len(texts))}/{len(texts)} chunks")
    return vectors


def publish(qdrant: QdrantClient, staging: str) -> None:
    """Point the COLLECTION alias at `staging` in one atomic step, then drop old data."""
    aliases = qdrant.get_aliases().aliases
    old_targets = [a.collection_name for a in aliases if a.alias_name == COLLECTION]

    ops = []
    if old_targets:
        ops.append(DeleteAliasOperation(delete_alias=DeleteAlias(alias_name=COLLECTION)))
    elif qdrant.collection_exists(COLLECTION):
        # Legacy setup: 'docs' was a real collection, not an alias. An alias
        # cannot share a name with a collection, so it has to go first.
        qdrant.delete_collection(COLLECTION)
    ops.append(
        CreateAliasOperation(create_alias=CreateAlias(collection_name=staging, alias_name=COLLECTION))
    )
    qdrant.update_collection_aliases(change_aliases_operations=ops)

    # Remove the previous build and any staging collections left by failed runs.
    stale = set(old_targets)
    stale |= {
        c.name
        for c in qdrant.get_collections().collections
        if c.name.startswith(f"{COLLECTION}__") and c.name != staging
    }
    for name in stale:
        qdrant.delete_collection(name)


def main() -> None:
    files = sorted(DOCS_DIR.glob("**/*.md"))
    if not files:
        raise SystemExit(f"No .md files found in {DOCS_DIR}/")

    # Chunk everything first, so an empty corpus fails before touching Qdrant.
    records: list[tuple[Path, int, str]] = []
    for path in files:
        chunks = chunk_text(path.read_text(encoding="utf-8"), CHUNK_SIZE, CHUNK_OVERLAP)
        records.extend((path, i, c) for i, c in enumerate(chunks))
        print(f"chunked {path} ({len(chunks)} chunks)")
    if not records:
        raise SystemExit(f"All .md files in {DOCS_DIR}/ are empty; nothing to index.")

    ollama = OllamaClient(host=OLLAMA_HOST)
    qdrant = QdrantClient(url=QDRANT_URL)

    vectors = embed_all(ollama, [text for _, _, text in records])
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{path}#{i}")),
            vector=vector,
            payload={"source": str(path), "chunk": i, "text": text},
        )
        for (path, i, text), vector in zip(records, vectors)
    ]

    staging = f"{COLLECTION}__{uuid.uuid4().hex[:8]}"
    qdrant.create_collection(
        staging,
        vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
    )
    for i in range(0, len(points), UPSERT_BATCH):
        qdrant.upsert(staging, points=points[i : i + UPSERT_BATCH])

    publish(qdrant, staging)
    print(f"Stored {len(points)} chunks from {len(files)} files in '{COLLECTION}'.")


if __name__ == "__main__":
    main()
