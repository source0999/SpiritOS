# Increment 1.2 State Classification

Date: 2026-05-29

Checks run:

- `grep -R "volumes:" -n backend/docker-compose.yml scout/docker-compose.scout.yml docker-compose*.yml 2>/dev/null || true`: PASS
- `grep -R "source_postgres_data\|ollama_data\|whisper_cache\|openedai_voices\|searxng_data" -n backend scout docker-compose*.yml 2>/dev/null || true`: PASS
- `git diff --check`: PASS

Compose-declared volumes:

- `source_postgres_data`
- `ollama_data`
- `whisper_cache`
- `openedai_voices`
- `searxng_data`

Observed running Docker volume names use the Compose project prefix:

- `backend_source_postgres_data`
- `backend_ollama_data`
- `backend_whisper_cache`
- `backend_openedai_voices`
- `backend_searxng_data`

Classification:

- PostgreSQL logical dump: critical.
- Scout/source SQLite or data DBs if present: critical.
- `backend_source_postgres_data`: critical physical backup, but logical dump is preferred first.
- `backend_searxng_data`: useful state/cache/config, backup after DB.
- `backend_openedai_voices`: useful voice/runtime asset state, backup if volume exists.
- `backend_whisper_cache`: rebuildable but potentially expensive, optional if not huge.
- `backend_ollama_data`: rebuildable but huge, defer unless size-check shows it is reasonable or Britton separately approves.

Result: GO. State is classified. No secret contents were printed.
