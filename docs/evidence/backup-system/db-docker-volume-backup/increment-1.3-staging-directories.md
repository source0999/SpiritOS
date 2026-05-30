# Increment 1.3 Staging Directories

Date: 2026-05-29

Checks run:

- `mkdir -p /mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps`: PASS
- `mkdir -p /mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports`: PASS
- `mkdir -p /mnt/spirit-8tb/spiritos-backups/logs`: PASS
- `find /mnt/spirit-8tb/spiritos-backups/staging/source-server -maxdepth 3 -type d | sort`: PASS
- `git diff --check`: PASS

Observed directories:

- `/mnt/spirit-8tb/spiritos-backups/staging/source-server`
- `/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps`
- `/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports`

Result: GO.
