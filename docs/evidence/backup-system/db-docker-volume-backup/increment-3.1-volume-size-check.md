# Increment 3.1 Volume Size Check

Date: 2026-05-29

Checks run:

- `docker volume ls --format '{{.Name}}' | sort`: PASS
- requested unprefixed volume inspect loop: PASS, all requested unprefixed names missing
- actual `backend_*` volume metadata size check using existing local image `postgres:16-alpine`: PASS
- `git diff --check`: PASS

Requested volume names:

- `source_postgres_data`: missing
- `ollama_data`: missing
- `whisper_cache`: missing
- `openedai_voices`: missing
- `searxng_data`: missing

Actual Compose-prefixed volume sizes:

- `backend_source_postgres_data`: 46.2M
- `backend_ollama_data`: 21.6G
- `backend_whisper_cache`: 141.0M
- `backend_openedai_voices`: 195.7M
- `backend_searxng_data`: 4.0K

Export decision:

- Export `backend_source_postgres_data` as secondary physical DB backup.
- Export `backend_searxng_data`.
- Export `backend_openedai_voices`.
- Export `backend_whisper_cache`.
- Defer `backend_ollama_data` because it is 21.6G and classified as rebuildable/huge unless Britton separately approves.

Result: GO. Volume existence and aggregate sizes were recorded. No volume contents were printed.
