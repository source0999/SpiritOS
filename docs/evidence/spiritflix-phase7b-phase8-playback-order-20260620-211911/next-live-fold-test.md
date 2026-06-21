# Next Live Fold Test

Britton should run this before approving the full-library batch.

1. Open SpiritFlix on the Fold/mobile path.
2. Play a Phase 7 optimized item, for example `RisqueCore Vid 10`.
3. Open the player diagnostics panel.
4. Confirm selected source is `mac_optimized_mp4`.
5. Confirm optimized receipt is present.
6. Confirm Range support is yes or playback/seek works normally.
7. Confirm HLS fallback is no at initial playback.
8. Confirm the video starts faster and seeking works.
9. On the Dell, verify no new `ffmpeg`, `libx265`, or media-ingest worker starts.
10. Confirm Dell CPU stays low during playback.

If all pass, give GO for the full-library Mac optimization batch.
