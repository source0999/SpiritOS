# Phase 3 Closeout

Status: PARTIAL-GO

Checks:

- Jellyfin first-run web app reachable locally: GO
- Admin setup complete according to Jellyfin public API: GO
- Library folder mappings exist for Movies, TV, Music, Anime, Other: GO
- Library display names exactly match plan: PARTIAL
- Metadata and scan check completed: GO
- At least one owned test file exists on disk and is container-readable: GO
- At least one owned test file is visible in Jellyfin UI: USER_MANUAL_CHECK_PENDING
- Playback starts locally: USER_MANUAL_CHECK_PENDING
- No SpiritOS app UI was touched: GO
- No secrets were written to docs, `.env`, screenshots, or chat: GO

Blocker:

- Phase 3.4 now has actual user-provided MP4 files under `/mnt/spirit-8tb/media/other`.
- The files are visible to the Jellyfin container and readable by ffprobe.
- The latest logged scan still predates the media placement, and browser playback requires the user's authenticated Jellyfin session.
- Codex must not fake playback proof.

Final phase-level terminal-safe check:

```text
PHASE_3_FINAL_CHECK_TERMINAL_SAFE
CONTAINER_STATE running healthy
StartupWizardCompleted:true
Movies -> /media/movies
Shows -> /media/tv
Music -> /media/music
Anime -> /media/anime
Home Videos and Photos -> /media/other
Scan Media Library Completed after 0 minute(s) and 0 seconds
Two MP4 files exist under /mnt/spirit-8tb/media/other
Jellyfin container can read /media/other/2024-07-23 01-17-41.mp4
ffprobe: h264 video, aac audio, duration 594.45 seconds
```

Decision:

- Phase 3 terminal-safe work is PARTIAL-GO.
- Continue remaining non-dependent phases.
- Do not claim final playback GO until the user runs a scan if needed and verifies playback in Jellyfin.

Next safe step:

- User runs Dashboard -> Libraries -> Scan All Libraries, opens `Home Videos and Photos`, and presses Play on one of the MP4 files.
- Record the result as the browser manual check for final acceptance.
