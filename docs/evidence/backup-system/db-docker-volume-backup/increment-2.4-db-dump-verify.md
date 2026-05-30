# Increment 2.4 DB Dump Verify

Date: 2026-05-29

Checks run:

- latest dump discovery: PASS
- `test -s "$latest_dump"`: PASS
- `gzip -t "$latest_dump"`: PASS
- `sha256sum -c "$latest_dump.sha256"`: PASS
- `git diff --check`: PASS

Observed:

```text
LATEST_DB_DUMP=/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps/postgres-dumpall-20260529T185317Z.sql.gz
/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps/postgres-dumpall-20260529T185317Z.sql.gz: OK
```

Result: GO. Dump is non-empty, gzip integrity passes, and checksum passes.
