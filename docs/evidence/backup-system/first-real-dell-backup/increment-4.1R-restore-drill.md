# Increment 4.1R Restore Drill

Date: 2026-05-29

Environment used:

- `SPIRIT_BACKUP_MODE=real`
- `SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true`
- `RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- `RESTIC_PASSWORD_FILE=/home/source/.config/spiritos-backup/restic-source-server.pass`

Checks run:

- `scripts/backups/spiritos-restore-drill.sh`: PASS command execution, but restore drill result failed acceptance
- `find /mnt/spirit-8tb/spiritos-backups/restore-drills -maxdepth 4 -type f | sort | tail -50`: PASS command execution, no restored file observed
- `git diff --check`: PASS

Observed:

```text
[spirit-backup] Restore drill planner mode=real
[spirit-backup] Target isolated restore-drills path: /mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/source-server
[spirit-backup] Refuse overwrite is active.
restoring <Snapshot 12865b16 ...> to /mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/source-server
Summary: Restored 0 files/dirs (0 B) in 0:00
```

Result: NO-GO. The helper ran safely, but no non-secret file was restored into the isolated drill folder.

Likely cause:

- The restore helper requested `--include /docs/backup-system/backup-system-v0.1-contract.md`, while the snapshot contains absolute paths under `/home/source/SpiritOS/...`.

Safety:

- Restore target was isolated under `/mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/source-server`.
- Nothing was restored over `/home/source/SpiritOS`.
- No secret contents were printed.
