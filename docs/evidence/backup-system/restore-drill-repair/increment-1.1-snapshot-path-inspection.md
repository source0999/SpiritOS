# Increment 1.1 Snapshot Path Inspection

Date: 2026-05-29

Environment:

- `RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- `RESTIC_PASSWORD_FILE=/home/source/.config/spiritos-backup/restic-source-server.pass`

Checks run:

- `restic snapshots`: PASS
- `restic ls 12865b16 | grep -E '/home/source/SpiritOS/docs/(backup-system|runbooks|evidence)' | head -80`: PASS
- `git diff --check`: PASS

Observed:

- Snapshot `12865b16` is visible.
- Safe non-secret docs paths are present under `/home/source/SpiritOS/docs/...`, including:
  - `/home/source/SpiritOS/docs/backup-system/backup-system-v0.1-contract.md`
  - `/home/source/SpiritOS/docs/backup-system/backup-system-v0.1-plan.md`
  - `/home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md`

Result: GO. Snapshot paths use absolute `/home/source/SpiritOS/...` paths. No file contents or secrets were printed.
