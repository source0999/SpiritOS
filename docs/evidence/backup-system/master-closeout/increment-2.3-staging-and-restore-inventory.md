# Increment 2.3 Staging and Restore-Drill Inventory

Date/time: 2026-05-29T16:10:41-04:00

## Scope

Inventoried existing backup staging paths, restore-drill paths, and backup log paths by file name/path only.

No file contents were read or printed.

No backup, dump, export, timer install, cloud sync, prune, delete, forget, container restart, commit, or push was run.

## Commands Run

```bash
cd /home/source/SpiritOS

echo "=== STAGING ==="
find /mnt/spirit-8tb/spiritos-backups/staging -maxdepth 5 -type f 2>/dev/null | sort | tail -200

echo "=== RESTORE DRILLS ==="
find /mnt/spirit-8tb/spiritos-backups/restore-drills -maxdepth 8 -type f 2>/dev/null | sort | tail -200

echo "=== BACKUP LOGS ==="
find /mnt/spirit-8tb/spiritos-backups/logs -maxdepth 1 -type f 2>/dev/null | sort | tail -80

git diff --check
```

Additional path-only count checks:

```bash
find /mnt/spirit-8tb/spiritos-backups/staging -maxdepth 5 -type f 2>/dev/null | wc -l
find /mnt/spirit-8tb/spiritos-backups/restore-drills -maxdepth 8 -type f 2>/dev/null | wc -l
find /mnt/spirit-8tb/spiritos-backups/logs -maxdepth 1 -type f 2>/dev/null | wc -l
find /mnt/spirit-8tb/spiritos-backups/staging/source-server -maxdepth 5 -type f 2>/dev/null | sort
```

## Path-Only Inventory Summary

- Staging files at checked depth: `769`
- Restore-drill files at checked depth: `40`
- Backup log files at checked depth: `3`

## Dell Source-Server Staging Paths Observed

```text
/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps/postgres-dumpall-20260529T185317Z.sql.gz
/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps/postgres-dumpall-20260529T185317Z.sql.gz.sha256
/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z/backend_openedai_voices.tar.gz
/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z/backend_openedai_voices.tar.gz.sha256
/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z/backend_searxng_data.tar.gz
/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z/backend_searxng_data.tar.gz.sha256
/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z/backend_source_postgres_data.tar.gz
/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z/backend_source_postgres_data.tar.gz.sha256
/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z/backend_whisper_cache.tar.gz
/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z/backend_whisper_cache.tar.gz.sha256
```

## Restore-Drill Paths Observed

The path-only restore-drill inventory included:

- DB dump restore drill paths under `/mnt/spirit-8tb/spiritos-backups/restore-drills/db-docker-20260529T185636Z/`
- Mac node restore drill paths under `/mnt/spirit-8tb/spiritos-backups/restore-drills/mac-node-20260529T193726Z/`

## Backup Log Paths Observed

```text
/mnt/spirit-8tb/spiritos-backups/logs/first-real-dell-backup-20260529T184227Z.log
/mnt/spirit-8tb/spiritos-backups/logs/mac-node-rsync-20260529T193603Z.log
/mnt/spirit-8tb/spiritos-backups/logs/restore-drill-repair-20260529T184651Z.log
```

## Manual Check Results

- Staging inventoried by path only: GO
- Restore drills inventoried by path only: GO
- Backup logs inventoried by path only: GO
- File contents printed: NO
- Secrets printed: NO
- `git diff --check`: GO, no output

## Increment Decision

GO.
