# n8n Notes

n8n is a workflow automation tool (open-source alternative to Zapier/Make).
Open the editor at http://localhost:5678.

## Concepts
- **Workflow**: a graph of nodes that runs when triggered.
- **Trigger node**: starts a workflow (Webhook, Cron/Schedule, Manual, etc.).
- **Node**: one step, e.g. HTTP Request, Postgres, IF, Code.
- **Credentials**: stored secrets used by nodes (encrypted in the n8n database).

## Talking to other services in this stack
- Postgres: host `postgres`, port `5432`.
- Ollama: base URL `http://ollama:11434`.
- Qdrant: URL `http://qdrant:6333`.

## Tips
- Use the **Webhook** node to expose a workflow as an HTTP endpoint.
- The **Code** node runs JavaScript (or Python) for custom logic.
- Pin node output data while building to avoid re-running earlier steps.
- Export workflows as JSON to version them in git.
