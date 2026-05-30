# Increment 2.1 Directory Create

Date: 2026-05-29

Approved target directories:

- `/mnt/spirit-8tb/spiritos-backups/`
- `/mnt/spirit-8tb/spiritos-backups/restic-repos/`
- `/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server/`
- `/mnt/spirit-8tb/spiritos-backups/restore-drills/`
- `/mnt/spirit-8tb/spiritos-backups/logs/`

Checks run:

```bash
mkdir -p /mnt/spirit-8tb/spiritos-backups/restic-repos/source-server
mkdir -p /mnt/spirit-8tb/spiritos-backups/restore-drills
mkdir -p /mnt/spirit-8tb/spiritos-backups/logs
find /mnt/spirit-8tb/spiritos-backups -maxdepth 3 -type d | sort
git diff --check
```

Observed:

```text
mkdir: cannot create directory '/mnt/spirit-8tb/spiritos-backups': Permission denied
mkdir: cannot create directory '/mnt/spirit-8tb/spiritos-backups': Permission denied
mkdir: cannot create directory '/mnt/spirit-8tb/spiritos-backups': Permission denied
find: '/mnt/spirit-8tb/spiritos-backups': No such file or directory
```

Result: NO-GO. The 8TB mount is present, but `/mnt/spirit-8tb` is not writable by the `source` user for the approved backup directory creation.

Stopped before restic repo initialization, first backup, snapshots, and restore drill.
