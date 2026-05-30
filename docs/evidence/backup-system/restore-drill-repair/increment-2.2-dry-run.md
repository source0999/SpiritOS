# Increment 2.2 Dry-run

Date: 2026-05-29

Environment:

- `RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- `RESTIC_PASSWORD_FILE=/home/source/.config/spiritos-backup/restic-source-server.pass`

Checks run:

- `scripts/backups/spiritos-restore-drill.sh --dry-run | tee /tmp/spiritos-restore-drill-repair-dry-run.txt`: PASS
- `grep -E "DRY|dry-run|restore-drills|12865b16|/home/source/SpiritOS" /tmp/spiritos-restore-drill-repair-dry-run.txt`: PASS
- `git diff --check`: PASS

Observed:

```text
[spirit-backup] Restore drill planner mode=dry-run
[spirit-backup] Target isolated restore-drills path: /mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/184626Z/source-server
[spirit-backup] Snapshot source path: /home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md
[spirit-backup] Snapshot selector: latest
[DRY-RUN] restic -r /mnt/spirit-8tb/spiritos-backups/restic-repos/source-server restore latest --target ... --include /home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md
```

Result: GO. Dry-run shows the correct snapshot source path and isolated restore target. No actual restore happened. No secret contents were printed.
