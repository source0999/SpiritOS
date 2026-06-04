# Increment 3.3 Metadata And Scan

Purpose:

- Keep metadata simple for the first working server and verify a library scan.

Terminal-safe verification commands:

```bash
cd /home/source/SpiritOS
curl -fsS http://127.0.0.1:8096/System/Info/Public
docker logs --tail 180 spirit-jellyfin 2>&1 | grep -Ei 'Scan Media Library|Validating media library|Library folder|Completed|metadata|Plugin' | tail -120
find /mnt/spirit-8tb/media -maxdepth 2 -type f -printf '%M %u %g %s %p\n' | sort | head -100
```

Verification output summary:

```text
StartupWizardCompleted:true
Loaded plugin: TMDb 10.11.10.0
Loaded plugin: Studio Images 10.11.10.0
Loaded plugin: OMDb 10.11.10.0
Loaded plugin: MusicBrainz 10.11.10.0
Loaded plugin: AudioDB 10.11.10.0
Validating media library
Scan Media Library Completed after 0 minute(s) and 0 seconds
```

Scan warnings:

```text
Library folder /media/music is inaccessible or empty, skipping
Library folder /media/movies is inaccessible or empty, skipping
Library folder /media/other is inaccessible or empty, skipping
Library folder /media/anime is inaccessible or empty, skipping
Library folder /media/tv is inaccessible or empty, skipping
```

Interpretation:

- Jellyfin ran the library scan.
- The warnings are expected at this point because no test media file has been placed in the media folders.
- No advanced plugins were installed by Codex.
- No metadata provider settings were changed by Codex.

Rollback:

- Correct library folder/type in the Jellyfin dashboard and rescan if the user wants different display names or types.

Status: GO
