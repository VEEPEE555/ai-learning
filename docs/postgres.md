# PostgreSQL Notes

## Connecting
```bash
docker exec -it postgres psql -U ai -d n8n
```

## Useful psql meta-commands
- `\l` list databases
- `\c dbname` connect to a database
- `\dt` list tables
- `\d tablename` describe a table
- `\q` quit

## Common SQL
```sql
CREATE TABLE notes (id SERIAL PRIMARY KEY, title TEXT, body TEXT, created_at TIMESTAMPTZ DEFAULT now());
INSERT INTO notes (title, body) VALUES ('hello', 'first note');
SELECT * FROM notes ORDER BY created_at DESC LIMIT 10;
```

## Backups
```bash
docker exec postgres pg_dump -U ai n8n > backup.sql
cat backup.sql | docker exec -i postgres psql -U ai -d n8n
```

## Tips
- Add indexes on columns you filter or join on frequently.
- The `pgvector` extension adds a vector type for embeddings, an alternative to Qdrant.
