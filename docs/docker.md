# Docker Notes

## Core concepts
- **Image**: a read-only template (e.g. `postgres:16`). Built from a `Dockerfile`.
- **Container**: a running instance of an image.
- **Volume**: persistent storage that survives container restarts and removal.
- **Network**: containers in the same Compose project share a default network and
  can reach each other by service name (e.g. `postgres:5432`).

## Everyday commands
```bash
docker compose up -d          # start the stack in the background
docker compose ps             # list running services
docker compose logs -f n8n    # follow logs for one service
docker compose down           # stop and remove containers (volumes are kept)
docker compose down -v        # also delete volumes (destroys data!)
docker exec -it ollama bash   # open a shell inside a container
```

## Tips
- Use named volumes for databases so data persists.
- `localhost` inside a container means the container itself, not your machine.
  Use the service name to talk to another container.
- `restart: unless-stopped` brings services back after a reboot.
