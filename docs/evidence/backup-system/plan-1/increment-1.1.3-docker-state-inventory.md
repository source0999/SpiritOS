# Increment 1.1.3 Docker State Inventory

Date: 2026-05-29

Expected named volumes to account for:

- `source_postgres_data`: critical database state
- `ollama_data`: model/runtime state, potentially large
- `whisper_cache`: rebuildable cache unless operator marks otherwise
- `openedai_voices`: voice/runtime asset state
- `searxng_data`: SearXNG runtime state

Compose and bind-mount review targets:

- `backend/docker-compose.yml`
- `scout/docker-compose.scout.yml`
- `docker-compose*.yml`
- `backend/searxng_data`
- `backend/volumes`
- `source_proxy/data`

Safety result:

- No containers were stopped, restarted, modified, or exported by this increment.
- Docker command failures, if Docker is unavailable on the host, are acceptable and must be recorded honestly in closeout evidence.

Manual checks to rerun:

```bash
cd /home/source/SpiritOS
grep -R "volumes:" -n backend/docker-compose.yml scout/docker-compose.scout.yml docker-compose*.yml 2>/dev/null || true
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null || true
docker volume ls 2>/dev/null || true
git diff --check
```
