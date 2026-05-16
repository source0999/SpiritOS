# Packet Synthesis Manual Check

Use this smoke after rebuilding Scout to verify the full raw event to verdict path.

```bash
cd ~/SpiritOS
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate
curl -s http://localhost:8077/v1/scout/status | jq
curl -s -X POST http://localhost:8077/v1/scout/_debug/poll \
  -H "Content-Type: application/json" \
  -d '{"kind":"rss","url":"https://blog.python.org/feeds/posts/default"}' | jq
```

Wait for the extractor, packet synthesis, and debugger jobs to run, then inspect counts:

```bash
docker exec -i scout_v0_1 python - <<'PY'
from scout.config import get_settings
from scout.storage.db import open_connection

settings = get_settings()
conn = open_connection(settings.database_path)

for table in [
    "raw_event_index",
    "extracted_artifacts",
    "packets",
    "verdicts",
    "packet_embeddings",
]:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")
    except Exception as e:
        print(f"{table}: ERROR {e}")
PY
```

Expected sequence:

- The forced RSS poll creates `raw_event_index > 0`.
- The extractor job creates `extracted_artifacts > 0`.
- `packets:synthesize_pending_artifacts` creates `packets > 0`.
- The debugger job later creates `verdicts > 0`.
- `packet_embeddings` may remain `0` unless Tier 3 embedding storage runs.
