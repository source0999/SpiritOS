# Mac Node First Backup Approval Packet

APPROVAL REQUIRED before any real Mac backup command is run.

## Restic Install Check On Mac

```bash
ssh spirit-mac-mini 'command -v restic'
```

Installing restic on the Mac is a separate critical action and is not approved by this packet unless Britton says so explicitly.

## Repo Target On Dell

```bash
/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-mac-mini
```

## Approach

Preferred v0.1 approach: Mac pushes to the Dell restic repository over an operator-approved SSH/SFTP or local-mounted path. Alternative: Dell pulls path inventory over SSH and then a later approved copy/export lane handles data.

## Future Approval Commands

```bash
cd /Users/spiritmac/spiritos-worker/SpiritOS
SPIRIT_BACKUP_MODE=real \
SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true \
RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-mac-mini \
restic backup --exclude node_modules --exclude .next --exclude dist /Users/spiritmac/spiritos-worker/SpiritOS
```

Rollback/no-delete note: v0.1 does not prune, delete, or expire snapshots.
