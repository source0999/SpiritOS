# Live Verification Notes

## Five Replaced MP4 Samples

Checked these five current MP4 paths against the live Jellyfin DB and filesystem:

- `/media/yes/484374_720p.mp4`
- `/media/yes/550807_720p.mp4`
- `/media/yes/14318872.mp4`
- `/media/yes/models/cute-geekie/51591.mp4`
- `/media/yes/models/sava-schultz/(28).mp4`

Result: all five files exist on disk, all five have Jellyfin `BaseItems` rows pointing at the `.mp4` path, and none had a matching old `.mkv` row for the same stem.

## Transcode / FFmpeg State

An active `ffmpeg` job was present, but it was a media-ingest worker encode under `/mnt/spirit-8tb/media-processing/active/...`, not a Jellyfin playback transcode for the five sampled MP4s.

## HLS / Cache State

- Permanent `.m3u8` or `.ts` files under `/mnt/spirit-8tb/media/yes`: none found.
- Jellyfin cache `.m3u8` count: 7.
- Jellyfin transcodes file count: 1.

No HLS/cache files were deleted.
