# Increment 3.4 Playback Test

Purpose:

- Prove playback using an owned or explicitly approved safe test media file.

Terminal-safe pre-check:

```bash
find /mnt/spirit-8tb/media -maxdepth 2 -type f -printf '%M %u %g %s %p\n' | sort | head -100
```

Pre-check output:

```text
No media files printed.
```

Follow-up after user placed media files:

```bash
find /mnt/spirit-8tb/media -maxdepth 3 -type f -printf '%M %u %g %s %TY-%Tm-%TdT%TH:%TM:%TS %p\n' | sort
docker exec spirit-jellyfin sh -lc 'ls -l /media/other'
docker exec spirit-jellyfin /usr/lib/jellyfin-ffmpeg/ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name -of default=noprint_wrappers=1 '/media/other/2024-07-23 01-17-41.mp4' | head -40
docker logs --since 15m spirit-jellyfin 2>&1 | grep -Ei 'Scan Media Library|Validating media library|Library folder|media/other|2024-07-23|ffprobe|Refresh|Playback|error|warn' | tail -160 || true
```

Follow-up output:

```text
-rw-rw-r-- source source 392858929 2024-07-23T01:27:36.3307984000 /mnt/spirit-8tb/media/other/2024-07-23 01-17-41.mp4
-rw-rw-r-- source source 701222377 2024-07-23T02:15:58.5295602000 /mnt/spirit-8tb/media/other/2024-07-23 01-27-43.mp4

/media/other/2024-07-23 01-17-41.mp4
/media/other/2024-07-23 01-27-43.mp4

codec_name=h264
codec_type=video
codec_name=aac
codec_type=audio
duration=594.450000
size=392858929
```

Result:

- Two user-provided MP4 files now exist under `/mnt/spirit-8tb/media/other`.
- The Jellyfin container can see the files at `/media/other`.
- Jellyfin ffprobe can read the first MP4 as H.264 video with AAC audio.
- The latest logged scan still predates the newly placed files, so a manual library scan/playback check is still required.

Remaining blocker:

- Codex cannot log into the user's Jellyfin browser session or press Play without handling credentials.
- Codex cannot fake playback proof.
- Jellyfin playback must be verified by the user in the browser.

Next safe step:

- In Jellyfin, run Dashboard -> Libraries -> Scan All Libraries.
- Open the `Home Videos and Photos` library.
- Confirm one of the `2024-07-23 ... .mp4` files appears.
- Press Play and confirm video/audio starts.
- Then ask Codex to continue from Phase 3.4 with the playback result.

Rollback:

```bash
rm -i /mnt/spirit-8tb/media/other/<approved-test-file-name>
```

Status: PARTIAL-GO_BLOCKED_ON_PLAYBACK_CONFIRMATION
