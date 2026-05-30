# Increment 3.1 Real Restore Drill

Date: 2026-05-29

Environment:

- `SPIRIT_BACKUP_MODE=real`
- `SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true`
- `RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- `RESTIC_PASSWORD_FILE=/home/source/.config/spiritos-backup/restic-source-server.pass`

Checks run:

- `scripts/backups/spiritos-restore-drill.sh 2>&1 | tee /mnt/spirit-8tb/spiritos-backups/logs/restore-drill-repair-$(date -u +%Y%m%dT%H%M%SZ).log`: PASS
- `find /mnt/spirit-8tb/spiritos-backups/restore-drills -maxdepth 6 -type f | sort | tail -80`: PASS
- `git diff --check`: PASS

Observed:

```text
Target isolated restore-drills path: /mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/184651Z/source-server
Snapshot source path: /home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md
restoring <Snapshot 12865b16 ...> to /mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/184651Z/source-server
Summary: Restored 6 / 1 files/dirs (1.812 KiB / 1.812 KiB) in 0:00
Restored file count: 1
/mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/184651Z/source-server/home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md
```

Result: GO. A non-secret runbook markdown file restored into the isolated restore-drill folder. Nothing was restored over `/home/source/SpiritOS`. No secret contents were printed.
