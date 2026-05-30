# Increment 2.1R Directory Permission Fixed

Date: 2026-05-29

Checks run:

- `findmnt /mnt/spirit-8tb`: PASS
- `df -h /mnt/spirit-8tb`: PASS
- `ls -ld /mnt/spirit-8tb /mnt/spirit-8tb/spiritos-backups`: PASS
- `test -w /mnt/spirit-8tb/spiritos-backups && echo SOURCE_CAN_WRITE_BACKUP_DIR`: PASS
- approved `mkdir -p` commands for restic repo, restore drills, and logs: PASS
- `find /mnt/spirit-8tb/spiritos-backups -maxdepth 3 -type d | sort`: PASS
- `git diff --check`: PASS

Observed:

```text
/mnt/spirit-8tb mounted as ext4 rw
/dev/sda1 7.3T size, 6.9T available
/mnt/spirit-8tb/spiritos-backups owner: source source, mode drwx------
SOURCE_CAN_WRITE_BACKUP_DIR
/mnt/spirit-8tb/spiritos-backups/logs
/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server
/mnt/spirit-8tb/spiritos-backups/restore-drills
```

Result: GO. The `source` user can write to the approved backup directory, and required subdirectories exist.
