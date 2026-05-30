# Increment 4.1 DB Dump Restore Proof

Date: 2026-05-29

Checks run:

- isolated restore target creation under `/mnt/spirit-8tb/spiritos-backups/restore-drills/`: PASS
- DB snapshot lookup by tag `spiritos-db-dump`: PASS
- `restic restore "$db_snapshot" --target "$target" --include "/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps/**"`: PASS
- restored file listing by path only: PASS
- `test -s "$latest_restored_dump"`: PASS
- `gzip -t "$latest_restored_dump"`: PASS
- `git diff --check`: PASS

Observed:

```text
DB_SNAPSHOT=cb127b36
Target=/mnt/spirit-8tb/spiritos-backups/restore-drills/db-docker-20260529T185636Z
Summary: Restored 8 / 3 files/dirs (2.113 KiB / 2.113 KiB) in 0:00
Restored dump: postgres-dumpall-20260529T185317Z.sql.gz
```

Result: GO. DB dump restored into an isolated folder, is non-empty, and gzip integrity passed.
