# Phase 7 Summary

- Candidates found: 9
- Optimized derivatives produced: 9
- remux-faststart-only: 1
- audio-aac-only: 0
- full transcode: 8
- failed/manual-review: 0
- Total source size: 468113173 bytes
- Total optimized size: 178986291 bytes
- Total space saved: 289126882 bytes
- Worker host used: spirit-mac-mini
- Output root: `/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized/20260621`
- Jellyfin restarted: no
- HLS/cache cleaned: no
- Media/MP4/preserved MKV deletion: no

Tests run are recorded in final response; focused optimizer/API tests passed before batch.


## Post-Run Live Library Caveat

A final live inventory after Phase 7 found `352` MP4 and `1` MKV under `/mnt/spirit-8tb/media/yes`.
The MKV is `/mnt/spirit-8tb/media/yes/video-2026-06-19T10-42-52.202Z.mkv`, timestamped 2026-06-20 20:55:08, and was produced by the pre-existing `scripts/media-ingest-worker.mjs` Dell `libx265` lane, not by Phase 7.

A second Dell `ffmpeg libx265` media-ingest job was still active after Phase 7:
`/mnt/spirit-8tb/media-processing/active/mi-mqn1p2rn-9f81ddb3/video-2026-06-19T10-12-48.740Z.tmp.mkv`.

Phase 7 optimizer outputs were all written to `/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized/20260621` and did not overwrite source media.
Before Phase 8 playback proof, the old Dell media-ingest HEVC/MKV worker lane should be retired or disabled so the live YES folder stays MP4-only.
