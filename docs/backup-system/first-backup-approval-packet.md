# First Dell Backup Approval Packet

APPROVAL REQUIRED before any command in this packet is run for real.

## Install Restic If Missing

```bash
command -v restic || sudo apt-get update
command -v restic || sudo apt-get install -y restic
```

## Initialize Restic Repo

```bash
export RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server
export RESTIC_PASSWORD_FILE=REPLACE_ME_OPERATOR_MANAGED_PASSWORD_FILE
restic -r "$RESTIC_REPOSITORY" init
```

## Run First Dell Backup

```bash
cd /home/source/SpiritOS
SPIRIT_BACKUP_MODE=real \
SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true \
RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server \
RESTIC_PASSWORD_FILE=REPLACE_ME_OPERATOR_MANAGED_PASSWORD_FILE \
scripts/backups/spiritos-backup-dell.sh --real
```

## Snapshot List

```bash
restic -r /mnt/spirit-8tb/spiritos-backups/restic-repos/source-server snapshots
```

## Restore Drill

```bash
cd /home/source/SpiritOS
SPIRIT_BACKUP_MODE=real \
SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true \
RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server \
scripts/backups/spiritos-restore-drill.sh --real
```

Do not run these from Codex without Britton approving the exact gate.
