"""Step 2: retrieve relevant chunks from Qdrant and answer with an Ollama chat model.

Usage:
    python ask.py "How do I back up Postgres?"
    python ask.py            # interactive mode
"""
import os
import sys

from dotenv import load_dotenv
from ollama import Client as OllamaClient
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "docs")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2")
TOP_K = int(os.getenv("TOP_K", 4))

SYSTEM_PROMPT = (
    "You answer questions using only the provided context from the user's notes. "
    "If the context does not contain the answer, say you don't know. "
    "Cite sources in square brackets, e.g. [docs/docker.md]."
)


def make_clients() -> tuple[OllamaClient, QdrantClient]:
    """Create clients on demand, so importing this module has no side effects."""
    return OllamaClient(host=OLLAMA_HOST), QdrantClient(url=QDRANT_URL)


def retrieve(ollama: OllamaClient, qdrant: QdrantClient, question: str):
    vector = ollama.embed(model=EMBED_MODEL, input=question)["embeddings"][0]
    return qdrant.query_points(COLLECTION, query=vector, limit=TOP_K, with_payload=True).points


def answer(question: str) -> None:
    try:
        ollama, qdrant = make_clients()
        hits = retrieve(ollama, qdrant, question)
    except Exception as exc:  # connection, missing collection, missing model, etc.
        print(f"\nRetrieval failed: {exc}")
        print(
            f"Check that Qdrant is running at {QDRANT_URL}, Ollama is running at {OLLAMA_HOST} "
            f"with '{EMBED_MODEL}' pulled, and that ingest.py has been run."
        )
        return

    if not hits:
        print("\nNo matching chunks found in the index.")
        return

    context = "\n\n---\n\n".join(f"[{h.payload['source']}]\n{h.payload['text']}" for h in hits)

    print("\nRetrieved:")
    for h in hits:
        print(f"  {h.score:.3f}  {h.payload['source']} (chunk {h.payload['chunk']})")
    print("\nAnswer:")

    try:
        stream = ollama.chat(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            stream=True,
        )
        for part in stream:
            print(part["message"]["content"], end="", flush=True)
    except Exception as exc:
        print(f"\nChat failed: {exc}\nIs the model '{CHAT_MODEL}' pulled in Ollama?")
        return
    print("\n")


def main() -> None:
    if len(sys.argv) > 1:
        answer(" ".join(sys.argv[1:]))
        return
    while True:
        try:
            q = input("ask> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q in {"exit", "quit"}:
            break
        if q:
            answer(q)


if __name__ == "__main__":
    main()
