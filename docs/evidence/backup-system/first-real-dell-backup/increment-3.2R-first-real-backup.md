# Increment 3.2R First Real Backup

Date: 2026-05-29

Environment used:

- `SPIRIT_BACKUP_MODE=real`
- `SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true`
- `RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- `RESTIC_PASSWORD_FILE=/home/source/.config/spiritos-backup/restic-source-server.pass`

Checks run:

- `scripts/backups/spiritos-backup-dell.sh 2>&1 | tee /mnt/spirit-8tb/spiritos-backups/logs/first-real-dell-backup-$(date -u +%Y%m%dT%H%M%SZ).log`: PASS
- `restic snapshots`: PASS
- `git diff --check`: PASS

Observed backup output:

```text
Files:        2351 new,     0 changed,     0 unmodified
Dirs:          606 new,     0 changed,     0 unmodified
Added to the repository: 311.986 MiB (243.387 MiB stored)
processed 2351 files, 402.460 MiB in 0:10
snapshot 12865b16 saved
```

Observed snapshot:

```text
12865b16  2026-05-29 14:42:27  source-server
Paths:
/home/source/SpiritOS/.spirit-backups
/home/source/SpiritOS/backend
/home/source/SpiritOS/config
/home/source/SpiritOS/docs
/home/source/SpiritOS/scout
/home/source/SpiritOS/scripts
/home/source/SpiritOS/src
```

Result: GO. First Dell/source-server file-level restic snapshot exists.

Safety:

- No secret contents were printed into evidence.
- No DB dump/export happened.
- No Docker volume export happened.
- No Mac, Windows, cloud, timer, prune, delete, commit, or push action happened.
