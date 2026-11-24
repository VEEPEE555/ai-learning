"""Step 1: chunk markdown docs, embed them with Ollama, and store them in Qdrant."""
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from ollama import Client as OllamaClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "docs")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
DOCS_DIR = Path(os.getenv("DOCS_DIR", "docs"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping character windows, preferring paragraph breaks."""
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            br = text.rfind("\n\n", start, end)
            if br > start + size // 2:
                end = br
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def main() -> None:
    ollama = OllamaClient(host=OLLAMA_HOST)
    qdrant = QdrantClient(url=QDRANT_URL)

    files = sorted(DOCS_DIR.glob("**/*.md"))
    if not files:
        raise SystemExit(f"No .md files found in {DOCS_DIR}/")

    points = []
    for path in files:
        for i, chunk in enumerate(chunk_text(path.read_text(encoding="utf-8"), CHUNK_SIZE, CHUNK_OVERLAP)):
            vector = ollama.embed(model=EMBED_MODEL, input=chunk)["embeddings"][0]
            points.append(
                PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{path}#{i}")),
                    vector=vector,
                    payload={"source": str(path), "chunk": i, "text": chunk},
                )
            )
        print(f"embedded {path}")

    # Recreate the collection so re-running ingest gives a clean index.
    if qdrant.collection_exists(COLLECTION):
        qdrant.delete_collection(COLLECTION)
    qdrant.create_collection(
        COLLECTION,
        vectors_config=VectorParams(size=len(points[0].vector), distance=Distance.COSINE),
    )
    qdrant.upsert(COLLECTION, points=points)
    print(f"Stored {len(points)} chunks from {len(files)} files in '{COLLECTION}'.")


if __name__ == "__main__":
    main()
