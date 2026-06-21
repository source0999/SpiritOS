# Phase 8 Source Selection

## Implemented Playback Order

1. Valid Mac optimized MP4 derivative with receipt and existing output.
2. Canonical/restored MP4 direct stream with Range support.
3. Direct Jellyfin MP4 stream.
4. Jellyfin HLS/transcode fallback only after direct playback failure or incompatibility.

## Code Paths

- `src/lib/spiritflix-jellyfin-client.ts`
- `src/lib/spiritflix/mobile-optimized.ts`
- `src/app/api/spiritflix/mobile-optimized/route.ts`
- `src/components/spiritflix/SpiritFlixPlayer.tsx`

## Receipt Alias Fix

Mobile optimized lookup now accepts `sourcePath` and expands aliases between:

- `/media/yes/...`
- `/mnt/spirit-8tb/media/yes/...`

This lets Jellyfin-style source paths match receipts written with Dell filesystem paths.

## Verification

Component and API tests verify that a valid Mac optimized receipt/output wins and that canonical MP4 is used when optimized output is absent.
