# Disabled MKV Output Paths

## Code Change

`scripts/media-ingest-worker.mjs` now defaults `MEDIA_INGEST_ENCODER` to `disabled` instead of `cpu-x265`.

The legacy MKV path now requires an explicit escape hatch:

```bash
MEDIA_INGEST_ALLOW_LEGACY_MKV_OUTPUT=1
```

Without that flag, the worker throws before processing legacy HEVC/MKV jobs and also blocks any `.mkv` live output candidate.

## Current Runtime Check

Post-stop process scan showed no active media-ingest worker, no ffmpeg optimization process, and no libx265 process. Only a passive `tail -f /mnt/spirit-8tb/media-processing/logs/worker.log` process was visible.

## Guardrail Tests

`scripts/__tests__/media-ingest-worker-guardrail.test.ts` verifies:

- default encoder is disabled
- explicit legacy escape hatch is required
- disabled-worker message is present
- live `.mkv` output candidates are blocked
