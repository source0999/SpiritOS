# Increment 3.1.1 Dell Restic Wrapper

Date: 2026-05-29

Artifact: `scripts/backups/spiritos-backup-dell.sh`

Checks run:

- `bash -n scripts/backups/spiritos-backup-dell.sh`: PASS
- `scripts/backups/spiritos-backup-dell.sh --dry-run | head -180`: PASS
- Grep for restic, exclude, `/mnt/spirit-8tb`, `source_proxy/data`, and `backend/volumes`: PASS
- `git diff --check`: PASS

Observed facts:

- `restic` was not found on this host; no install was attempted.
- `/mnt/spirit-8tb` was visible in prior checks.
- Dry-run printed planned `restic backup` and `restic snapshots` commands only.

Result: GO. No `restic init` or real backup was executed.
