# Safe Next Actions

1. Do not delete preservation folders yet. Keep rollback roots until Jellyfin and SpiritFlix metadata are verified after a scan.
2. Run a Jellyfin library scan for the YES library; do not restart unless the scan gets stuck.
3. Patch/migrate stale Jellyfin playlist/BaseItems paths from old .mkv/.ts to .mp4 after backing up jellyfin.db and playlist.xml.
4. Re-run this audit after scan/path migration.
5. HLS/cache cleanup is not safe until stale Jellyfin references are fixed and playback is verified from MP4 paths.

MP4s needing Mac optimization: 9
