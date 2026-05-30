# Increment 3.4 Volume Export Verify

Date: 2026-05-29

Checks run:

- latest export directory discovery: PASS
- `find "$latest_volume_export_dir" -type f -name '*.tar.gz' -print -exec gzip -t {} \;`: PASS
- `find "$latest_volume_export_dir" -type f -name '*.sha256' -print -exec sha256sum -c {} \;`: PASS
- `git diff --check`: PASS

Observed:

```text
LATEST_VOLUME_EXPORT_DIR=/mnt/spirit-8tb/spiritos-backups/staging/source-server/docker-volume-exports/20260529T185503Z
backend_searxng_data.tar.gz: OK
backend_source_postgres_data.tar.gz: OK
backend_whisper_cache.tar.gz: OK
backend_openedai_voices.tar.gz: OK
```

Result: GO. Every exported archive passed gzip integrity, and every checksum passed.
