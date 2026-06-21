# Old Dell Worker Discovery

## Running Process Found

- Worker process: `node scripts/media-ingest-worker.mjs`
- PID: 1856187
- Parent PID: 1
- Active ffmpeg PID: 3848932
- Active encoder: `libx265`
- Active output candidate: `/mnt/spirit-8tb/media-processing/active/mi-mqn1p2rn-9f81ddb3/video-2026-06-19T10-12-48.740Z.tmp.mkv`

## Launcher

No systemd unit, cron/timer, or pm2 launcher was found for the running worker. The process appeared to be a manually/background-launched orphan with parent PID 1.

## Code Path Producing MKV

`scripts/media-ingest-worker.mjs` defaulted to `MEDIA_INGEST_ENCODER || "cpu-x265"` and published `.mkv` outputs into live SpiritFlix media. That default was the MKV-producing path.

## Safe Stop Assessment

The active job had a source MP4 present in the active processing directory, and the new live MKV had a preserved original MP4 available under `/mnt/spirit-8tb/media-originals/keep-for-30-days/yes`, so it was safe to stop the worker and preserve/quarantine the MKV artifacts.
