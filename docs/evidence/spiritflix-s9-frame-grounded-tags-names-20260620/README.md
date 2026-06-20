# SpiritFlix S9 frame-grounded tags and names

Date: 2026-06-20

## Scope

- Added title-worthy vocabulary for frame-grounded naming: `hotel-room`, `threesome`, `traditional-dress`, `dress`, and `smoking`.
- Changed naming so readable source titles are preserved, while random/spam names use model-folder numbering: `Model 03 - descriptor` or `Model 03 - Untitled`.
- Split tag chips from title phrases. Body/apparel tags can remain review chips without automatically becoming the whole recommended name.
- Added a video-level visual pass over multiple sampled frames, while gating free-text observations so they do not create visible tags unless structured tag IDs are returned.
- Bumped frame cache from `v1` 480px frames to `v2` 768px frames so future forced analyses use larger fresh frames.
- No media files were renamed, moved, or deleted.

## Live proof

Final safe live refresh was run against the two rows that showed the clearest bad behavior:

- `HkkzMtwQexuQzwkQMekM.mkv` -> no visible smart tags; proposed `Aaliyah Yasan 03 - Untitled`
- `Visit onlyshare.io for MORE 130.mkv` -> no visible smart tags; proposed `Aaliyah Yasan 10 - Untitled`

This is intentionally conservative. The installed local vision model (`gemma3n:e4b`) repeatedly returned unparseable JSON or incorrect free-text descriptions for these sampled frames. The app now keeps that free text out of tag chips and names instead of showing wrong `hotel-room`/`lingerie` tags.

Raw proof:

- `raw/70-safe-video-pass-refresh-hkkz-more130.json`
- `raw/71-safe-video-pass-preview-hkkz-more130.json`
- `raw/72-safe-video-pass-sidecar-summary.json`

## Boundary

The remaining gap is model quality, not a hardcoded-path or UI-only issue. The pipeline now samples fresh larger frames and asks for structured frame-grounded tags, but it will not invent tags when the local model cannot return reliable structured evidence.
