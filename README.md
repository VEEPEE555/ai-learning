# ai-learning

A minimal local RAG (retrieval-augmented generation) playground:
**Qdrant** (vector DB) + **Ollama** (embeddings + LLM), with **Open WebUI**, **Postgres** and **n8n** alongside.

```
ai-learning/
├── docker-compose.yml   # ollama, open-webui, postgres, qdrant, n8n
├── .env                 # local config (copy from .env.example; git-ignored)
├── docs/                # sample notes to search
├── requirements.txt
├── ingest.py            # Step 1: embed docs into Qdrant
└── ask.py               # Step 2: retrieve + answer with Ollama
```

## Quick start

Run everything from the repo root, since the scripts read `docs/` and `.env` relative to the current directory.

```bash
cp .env.example .env          # then set POSTGRES_PASSWORD in .env
docker compose up -d          # also pulls llama3.2 and nomic-embed-text into Ollama
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ingest.py
python ask.py "How do I back up Postgres?"
```

Re-run `python ingest.py` whenever the docs change. Each run rebuilds the index and swaps it in atomically.

Services:
- Qdrant dashboard: http://localhost:6333/dashboard
- Ollama: http://localhost:11434
- Open WebUI: http://localhost:3000
- n8n: http://localhost:5678

Postgres credentials come from `.env`. If you change `POSTGRES_USER`, `POSTGRES_PASSWORD`, or `POSTGRES_DB` after the `pgdata` volume was first created, Postgres keeps the original values. Recreate the volume with `docker compose down -v` (this deletes data) to apply them.
