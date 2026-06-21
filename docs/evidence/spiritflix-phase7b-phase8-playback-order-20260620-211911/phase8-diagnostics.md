# Phase 8 Diagnostics

## Player Diagnostics Added

The SpiritFlix player diagnostics now expose:

- selected playback source
- selected-source reason
- optimized receipt present yes/no
- optimized output path availability
- canonical MP4 present yes/no
- content type
- Range support yes/unknown
- current container/codecs from item metadata
- Dell ffmpeg active yes/no/unknown
- HLS fallback used yes/no
- source URL class without secrets

## Source Classes

- `mac_optimized_mp4`
- `canonical_mp4`
- `jellyfin_direct_mp4`
- `jellyfin_hls_fallback`
- `jellyfin_transcode_fallback`

## API Added

`/api/spiritflix/system-diagnostics` checks the local process table and returns secret-safe ffmpeg process status, classifying paths as media-processing, Jellyfin transcode, or other.
