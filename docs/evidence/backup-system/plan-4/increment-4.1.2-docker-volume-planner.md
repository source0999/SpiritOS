# Increment 4.1.2 Docker Volume Export Planner

Date: 2026-05-29

Artifact: `scripts/backups/spiritos-backup-docker-volumes.sh`

Checks run:

- `bash -n scripts/backups/spiritos-backup-docker-volumes.sh`: PASS
- `scripts/backups/spiritos-backup-docker-volumes.sh --dry-run | head -180`: PASS
- Grep for expected volume names and approval guard path: PASS
- `git diff --check`: PASS

Observed facts:

- Live Docker volume names include backend-prefixed variants such as `backend_source_postgres_data`, `backend_ollama_data`, `backend_whisper_cache`, `backend_openedai_voices`, and `backend_searxng_data`.
- Planner lists the expected v0.1 names and prints export commands as dry-run only.
- No Docker volume export was executed.

Result: GO.
