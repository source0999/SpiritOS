# Increment 2.2 Postgres Logical Dump

Date: 2026-05-29

Source:

- Container: `source-postgres`
- Method: `pg_dumpall` inside the running container

Checks run:

- `docker exec source-postgres sh -lc 'pg_dumpall -U "${POSTGRES_USER:-postgres}"' > "$dump"`: PASS
- `gzip -9 "$dump"`: PASS
- `sha256sum "$dump.gz" > "$dump.gz.sha256"`: PASS
- `ls -lh "$dump.gz" "$dump.gz.sha256"`: PASS
- `gzip -t "$dump.gz"`: PASS
- `git diff --check`: PASS

Artifacts:

- `/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps/postgres-dumpall-20260529T185317Z.sql.gz`
- `/mnt/spirit-8tb/spiritos-backups/staging/source-server/db-dumps/postgres-dumpall-20260529T185317Z.sql.gz.sha256`

Observed metadata:

```text
postgres dump gzip size: 2.0K
checksum file size: 171 bytes
```

Result: GO. Dump succeeded and gzip integrity passed. No secret contents or DB contents were printed.
