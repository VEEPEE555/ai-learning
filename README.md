# ai-learning

A minimal local RAG (retrieval-augmented generation) playground:
**Qdrant** (vector DB) + **Ollama** (embeddings + LLM), with **Postgres** and **n8n** alongside.

```
ai-learning/
├── docker-compose.yml   # qdrant, ollama, postgres, n8n
├── .env                 # local config (copy from .env.example; git-ignored)
├── docs/                # sample notes to search
├── requirements.txt
├── ingest.py            # Step 1: embed docs into Qdrant
└── ask.py               # Step 2: retrieve + answer with Ollama
```

## Quick start

```bash
cp .env.example .env
docker compose up -d
docker exec ollama ollama pull nomic-embed-text
docker exec ollama ollama pull llama3.2
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ingest.py
python ask.py "How do I back up Postgres?"
```

Services: Qdrant dashboard http://localhost:6333/dashboard · Ollama http://localhost:11434 · n8n http://localhost:5678
