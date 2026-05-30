# Operator Next Approval Packet

## What was built

Backup System v0.1 docs, dry-run Bash and PowerShell planners, restore drill helper, scheduler templates, and evidence files.

## What was not executed

No real backup, restore, restic initialization, package install, DB dump, Docker volume export, timer install, prune/delete, cloud sync, commit, or push was executed.

## Current safety status

All scripts default to dry-run/read-only. Real writes require `SPIRIT_BACKUP_MODE=real` and `SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true` after Britton approval.

## APPROVAL REQUIRED: first real Dell backup

```bash
sudo apt-get update
sudo apt-get install -y restic
export RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server
export RESTIC_PASSWORD_FILE=REPLACE_ME_OPERATOR_MANAGED_PASSWORD_FILE
restic -r "$RESTIC_REPOSITORY" init
cd /home/source/SpiritOS
SPIRIT_BACKUP_MODE=real SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true scripts/backups/spiritos-backup-dell.sh --real
restic -r "$RESTIC_REPOSITORY" snapshots
```

## APPROVAL REQUIRED: first real restore drill

```bash
cd /home/source/SpiritOS
SPIRIT_BACKUP_MODE=real \
SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true \
RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server \
scripts/backups/spiritos-restore-drill.sh --real
```

## Optional later approval gates

- Mac backup: approve Mac restic availability/install, repo target, and first backup command.
- Windows backup: approve PowerShell execution on `C:\Projects` scope.
- DB dumps: approve pg_dump/sqlite backup commands and output path.
- Docker volume exports: approve each volume export.
- Timers: approve systemd, launchd, or Windows Task Scheduler installation.
- Offsite mirror: approve rclone config and first cloud sync.
