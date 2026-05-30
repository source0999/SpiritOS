# Increment 4.2 Volume Export Restore Proof

Date: 2026-05-29

Checks run:

- isolated restore target creation under `/mnt/spirit-8tb/spiritos-backups/restore-drills/`: PASS
- volume export snapshot lookup by tag `spiritos-docker-volume-export`: PASS
- `restic restore "$vol_snapshot" --target "$target" --include "/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/**"`: PASS
- restored archive listing by path only: PASS
- `gzip -t` for restored `.tar.gz` archives: PASS
- `git diff --check`: PASS

Observed:

```text
VOLUME_EXPORT_SNAPSHOT=8e09ed34
Target=/mnt/spirit-8tb/spiritos-backups/restore-drills/docker-volume-export-20260529T185658Z
Summary: Restored 15 / 10 files/dirs (314.590 MiB / 314.590 MiB) in 0:01
Restored archives:
backend_openedai_voices.tar.gz
backend_searxng_data.tar.gz
backend_source_postgres_data.tar.gz
backend_whisper_cache.tar.gz
```

Result: GO. Docker volume export archives restored into an isolated folder, are non-empty, and gzip integrity passed.
