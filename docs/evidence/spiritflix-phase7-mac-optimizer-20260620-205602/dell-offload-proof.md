# Dell Offload Proof

- Worker host in every receipt: `spirit-mac-mini`.
- ffmpeg path in every receipt: `/usr/local/bin/ffmpeg` on Mac.
- Output files and receipts are visible on Dell under `/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized/20260621`.
- Dell role recorded in receipts: orchestration, ffprobe verification, scp only; no heavy ffmpeg encode.
- Source MP4s remained in `/mnt/spirit-8tb/media/yes`; no overwrite path was used.

Current Dell ffmpeg process snapshot after jobs:

```text
3848932 ffmpeg          ffmpeg -y -hide_banner -progress pipe:1 -nostats -i /mnt/spirit-8tb/media-processing/active/mi-mqn1p2rn-9f81ddb3/video-2026-06-19T10-12-48.740Z.mp4 -map 0 -c:v libx265 -preset medium -crf 22 -pix_fmt yuv420p10le -threads 2 -x265-params pools=2 -c:a copy -c:s copy /mnt/spirit-8tb/media-processing/active/mi-mqn1p2rn-9f81ddb3/video-2026-06-19T10-12-48.740Z.tmp.mkv
```

Note: any listed `/mnt/spirit-8tb/media-processing/active` ffmpeg process is unrelated existing media-ingest work, not a Phase 7 optimizer command. Phase 7 optimizer command summaries all begin with `ssh spirit-mac-mini /usr/local/bin/ffmpeg` or `ssh spirit-mac-mini bash -lc .../usr/local/bin/ffmpeg`.


## Important Caveat

Phase 7 optimization jobs were Mac-offloaded, but the Dell still had an unrelated pre-existing media-ingest worker active after the Phase 7 batch. That worker invoked Dell-side `ffmpeg libx265` under `/mnt/spirit-8tb/media-processing/active` and produced/recognized a live MKV. This does not appear in any Phase 7 receipt or command summary, but it means the broader system is not fully Dell-CPU-offloaded until that old worker lane is disabled.
