# DB Docker Volume Backup Closeout

Date: 2026-05-29

Status: GO

DB dump created:

- `/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps/postgres-dumpall-20260529T185317Z.sql.gz`

Docker volumes exported:

- `backend_source_postgres_data`
- `backend_searxng_data`
- `backend_openedai_voices`
- `backend_whisper_cache`

Volumes deferred:

- `backend_ollama_data`: 21.6G, rebuildable/huge, requires separate approval.

Restic snapshots created:

- `cb127b36`: DB dump backup, tags `spiritos-db-dump,source-server`
- `8e09ed34`: Docker volume export backup, tags `spiritos-docker-volume-export,source-server`

Restore proof:

- DB dump restore proof: GO
- Docker volume export restore proof: GO

Safety:

- No Mac backup ran.
- No Windows backup ran.
- No containers were stopped or restarted.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion ran.
- No commit/push ran.
- No secrets were printed.
