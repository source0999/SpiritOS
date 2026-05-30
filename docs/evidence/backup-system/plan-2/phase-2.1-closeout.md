# Phase 2.1 Closeout

Date: 2026-05-29

Artifacts:

- `scripts/backups/lib/spirit-backup-common.sh`
- `scripts/backups/spiritos-backup-inventory.sh`
- `scripts/backups/spiritos-backup-manifest.sh`

Checks required:

- Bash syntax for all three scripts.
- Manifest dry-run contains `source_proxy/data`, `backend/volumes`, `source_postgres_data`, `spirit-mac-mini`, and `C:\Projects`.
- `git diff --check`.

Phase 3.1 status: GO after checks pass.
