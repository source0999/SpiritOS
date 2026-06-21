# SpiritFlix Post-MP4 / MKV-Delete Audit

Generated: 2026-06-21T00:22:28.881Z

## Current Live YES Library

- Current MP4 count: 354
- Current MKV count: 0
- Current TS count: 0
- Current non-MP4 video count: 0
- Current live video count: 354

## Prior 65

- Prior 65 with valid current MP4 replacement: 64
- Prior 65 still unresolved: 1
- Deleted/preserved old MKVs recoverable: 1
- Deleted/preserved old MKVs appearing unrecoverable: 0

## Stale References

- Jellyfin stale MKV/TS occurrence count: 2
- YES Folder Queue stale reference count: 0
- Live sidecar stale reference count: 2901
- Jellyfin/config text stale reference count: 0

## MP4 Quality

- MP4s checked: 354
- Mobile-safe H.264/AAC MP4s: 345
- MP4s needing Mac optimization: 9

## Inventory By Location/Extension

- android-backup .m4v: 6 (1.24 GiB)
- android-backup .mov: 1 (4.83 MiB)
- android-backup .mp4: 122 (14.79 GiB)
- current-yes-models .mp4: 150 (19.97 GiB)
- current-yes .mp4: 354 (49.44 GiB)
- preserved-keep-30 .m4v: 7 (144.14 MiB)
- preserved-keep-30 .mkv: 6 (1.07 GiB)
- preserved-keep-30 .mp4: 167 (27.62 GiB)
- recent-preservation:clean-yes-non-mp4-and-dupes-20260620-200937 .mkv: 1 (23.45 MiB)
- recent-preservation:clean-yes-non-mp4-and-dupes-20260620-200937 .mp4: 6 (1.50 GiB)
- recent-preservation:final-non-mp4-cleanup-20260620-200321 .mkv: 2 (202.28 MiB)
- recent-preservation:final-ts-remux-20260620-200357 .ts: 4 (1.24 GiB)
- recent-preservation:full-batch-replaced-by-mp4-20260620-190819 .mkv: 287 (20.22 GiB)
- recent-preservation:removed-from-library-20260620-184733 .mkv: 1 (1.45 MiB)
- recent-preservation:replaced-by-mp4-20260620-184733 .mkv: 12 (609.54 MiB)
- windows-backup .m4v: 13 (1.38 GiB)
- windows-backup .mov: 3 (9.42 MiB)
- windows-backup .mp4: 343 (47.50 GiB)
- windows-backup .ts: 4 (1.24 GiB)
- windows-missing-downloads .mp4: 12 (2.28 GiB)

## HLS/Cleanup Status

HLS/cache cleanup is **not safe yet** because Jellyfin still has stale .mkv/.ts references. The live filesystem is MP4-only for videos, but Jellyfin metadata must be scanned/migrated first.

## Notes

No media files were deleted by this audit. No HLS/cache was cleaned. Jellyfin was not restarted.
