# Restore Drill Repair Closeout

Date: 2026-05-29

Status: GO

Root cause:

The restore helper used `/docs/backup-system/backup-system-v0.1-contract.md`, but the restic snapshot stores paths under `/home/source/SpiritOS/docs/...`.

Repair:

- Updated `scripts/backups/spiritos-restore-drill.sh` to restore `/home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md` by default.
- Added unique timestamped restore targets.
- Added restore-drills path containment check.
- Kept refusal to restore over `/home/source/SpiritOS`.
- Added zero-file restore rejection.
- Added restored path listing without contents.

Proof:

- Snapshot `12865b16` restored one non-secret runbook markdown file into:
  `/mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/184651Z/source-server/home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md`
- Restored file exists and is non-empty.

Safety:

- No DB dumps ran.
- No Docker volume exports ran.
- No Mac backup ran.
- No Windows backup ran.
- No containers were stopped or restarted.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion ran.
- No commit/push ran.
- No secrets were printed.
