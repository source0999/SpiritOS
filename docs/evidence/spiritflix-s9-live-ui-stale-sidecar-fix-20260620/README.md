# SpiritFlix S9 stale sidecar refresh proof

Date: 2026-06-20

Scope: exact rows reported from the Smart Tags operator panel:

- `/mnt/spirit-8tb/media/yes/models/aaliyah-yasan/540598_720p.mkv`
- `/mnt/spirit-8tb/media/yes/models/aaliyah-yasan/Aaliyah Yasin Has Unprotected Sex With A Stranger.mkv`

## Baseline

`raw/00-baseline-screenshot-rows.txt` confirmed the live admin API was serving stale reviewed sidecars:

- `visualTaggingAvailable: false`
- `tags: []`
- `analysisStatus: approved`
- `reviewStatus: reviewed`
- recommended names still based on old title/quality heuristics

## Final live proof

`raw/31-preview-final.json` was captured from the live HTTPS admin API after force-refreshing the two exact files.

Observed final UI payload:

- `540598_720p.mkv`
  - smart tags: `solo`, `indoor`
  - quality/technical: `HD`, `mkv`
  - status: `needs_review`, `unreviewed`
  - recommended name: `Aaliyah Yasan - solo indoor 540598`
  - no duplicate-target warning
- `Aaliyah Yasin Has Unprotected Sex With A Stranger.mkv`
  - smart tags: `solo`, `indoor`
  - quality/technical: `HD`, `long`, `mkv`
  - status: `needs_review`, `unreviewed`
  - recommended name: `Aaliyah Yasan - solo indoor 01`
  - no duplicate-target warning

No media files were renamed, moved, or deleted.
