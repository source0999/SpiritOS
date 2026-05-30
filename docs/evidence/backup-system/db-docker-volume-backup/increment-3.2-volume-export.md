# Increment 3.2 Volume Export

Date: 2026-05-29

Local image check:

- Existing local image used: `postgres:16-alpine`
- No Docker image was pulled.

Export output directory:

- `/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z`

Volumes exported:

- `backend_source_postgres_data`
- `backend_searxng_data`
- `backend_openedai_voices`
- `backend_whisper_cache`

Volume deferred:

- `backend_ollama_data`: deferred because it is 21.6G and classified as rebuildable/huge unless Britton separately approves.

Checks run:

- `docker images --format '{{.Repository}}:{{.Tag}}' | sort | head -80`: PASS
- `docker image inspect postgres:16-alpine`: PASS
- read-only tar exports through short-lived helper containers: PASS
- `sha256sum` files created: PASS
- `gzip -t` for each archive: PASS
- `ls -lh` for each archive: PASS
- `git diff --check`: PASS

Observed archive sizes:

- `backend_source_postgres_data.tar.gz`: 6.5M
- `backend_searxng_data.tar.gz`: 89 bytes
- `backend_openedai_voices.tar.gz`: 181M
- `backend_whisper_cache.tar.gz`: 128M

Result: GO. Selected volume archives exist, are non-empty, gzip integrity passed, and checksums exist.

Safety:

- No running containers were stopped or restarted.
- No Docker image was pulled.
- No volume contents were listed or printed.
