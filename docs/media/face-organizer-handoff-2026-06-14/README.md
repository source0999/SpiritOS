# Media Face Organizer / SpiritFlix Handoff Pack

Generated: 2026-06-14

This is a compact context pack for another model or agent. It summarizes the current Media Face Organizer work, the conversion/ingest system behavior, the organization/verification flow, and the SpiritFlix `:3001` lane without requiring a full repo dump.

## Live Lanes

- Face Organizer review server: `http://100.111.32.31:8765/face_enrolled_performers.html`
- Face Organizer command:
  ```bash
  cd /home/source/SpiritOS
  .venv-face-organizer/bin/python -u scripts/media/face_organizer.py --serve-review --source /DATA/yes --host 0.0.0.0 --port 8765 --ctx-id -1 --apply
  ```
- Face Organizer log: `/tmp/face-organizer-8765.log`
- SpiritFlix sidecar lane: `http://10.0.0.186:3001/spiritflix`
- SpiritFlix sidecar working copy: `/tmp/spiritos-spiritflix-stable-3001`
- Main repo on Dell: `/home/source/SpiritOS`
- Windows mapped repo: `Z:\`

## Key Files Changed

- `scripts/media/face_organizer.py`
  - Face verification, enrollment, enrolled performer page, manual crop flow, duplicate merge flow, faceless marking, enrolled video match review, targeted face-rec scan.
  - Important functions:
    - `collect_metadata`
    - `dedupe_metadata_records`
    - `resolve_metadata_video_path`
    - `generate_enrollment_candidates`
    - `enrolled_model_scan_videos`
    - `scan_library_for_enrolled_model`
    - `enrolled_video_matches`
    - `generate_enrolled_page`
    - review server `_serve_file`
- `scripts/media-ingest-worker.mjs`
  - Conversion/ingest worker.
  - Now watches configured library roots, writes receipts, and preserves library originals by default unless `MEDIA_INGEST_DELETE_LIBRARY_ORIGINALS=1`.
- `src/app/api/spiritflix/face-metadata/route.ts`
  - SpiritFlix API bridge for Face Organizer sidecars and enrolled source metadata.
  - Uses basename/stem matching so `.mp4` sidecars can match `.mkv` Jellyfin items.
  - Requires `visual_confirmed: true` for user-confirmed video matches.
- `src/components/spiritflix/SpiritFlixHome.tsx`
  - SpiritFlix model grouping and model card count display.
  - Counts visible Jellyfin items, not organizer-only source counts.
- `src/lib/spiritflix-jellyfin-client.ts`
  - Client call for `/api/spiritflix/face-metadata`.

## Current Behavior After Latest Fix

- Enrolled/queue HTML routes no longer regenerate heavy pages on every navigation.
- Static review HTML is streamed with `Content-Length` and `Cache-Control: no-store`.
- Generated enrolled/queue pages use lazy image loading.
- Video match cards have responsive layout so text does not collapse into vertical letters.
- `Run face-rec scan for this model` now runs actual face recognition on linked model videos.
- Stale duplicate sidecars are deduped by resolved video path. If both stale zero-support `.MP4.face-meta.json` and newer `.mkv.face-meta.json` exist, the one with real face evidence wins.
- Rows without saved face evidence no longer count as strong/review face-rec matches.
- `6513.mp4` is not treated as a Sava face match after real scanning.

## Sava Schultz Scan Truth

Latest targeted scan on Sava linked videos:

- Candidate videos scanned: `11`
- Strong face matches: `6`
- Review-level face matches: `2`
- Not matched by face-rec: `3`

Important per-video results:

- `(19).mkv`: `36` faces, Sava auto match, similarity `0.9005`, `25` supporting faces.
- `(28).mkv`: `16` faces, Sava auto match, similarity `0.8374`, `13` supporting faces.
- `(31).mkv`: `17` faces, Sava auto match, similarity `0.8308`, `14` supporting faces.
- `169901_1080p.mkv`: `33` faces, Sava possible match, similarity `0.6572`, `2` supporting faces.
- `169902_1080p.mkv`: `18` faces, Sava auto match, similarity `0.8586`, `10` supporting faces.
- `46783.mkv`: `13` faces, Sava auto match, similarity `0.8028`, `3` supporting faces.
- `Sava.schultz Nude Solo Tease OnlyFans Video Leaked.mp4`: `18` faces, Sava possible match, similarity `0.7721`, `16` supporting faces.
- `6513.mp4`: `11` faces, best similarity only `0.4608`; it should not be auto-confirmed as Sava.

## Known Caveats

- Some old sidecars still exist on disk and may say `auto` with `0` supporting faces. `collect_metadata` now dedupes them out when a better sidecar exists for the same resolved video.
- `Sava-Schultz-2.mkv` had metadata/manual evidence but no face evidence in the latest scan.
- The Face Organizer review server startup command often times out in the SSH wrapper even when the service starts. Always verify with `ss -ltnp | grep ":8765"` and route timing.
- The large verification report remains around 29 MB. Prefer the enrolled and enrollment pages for interactive curation.
- SpiritFlix `:3001` only shows what Jellyfin exposes in its library view. Organizer/source counts can differ from visible SpiritFlix counts.

## Useful Commands

Check review server:

```bash
ssh source@10.0.0.186 'ss -ltnp | grep ":8765" || true; pgrep -af "face_organizer.py" || true; tail -40 /tmp/face-organizer-8765.log 2>/dev/null || true'
```

Regenerate enrolled page only:

```bash
ssh source@10.0.0.186 'cd /home/source/SpiritOS && .venv-face-organizer/bin/python -u scripts/media/face_organizer.py --enrolled-page --source /DATA/yes --ctx-id -1 --apply'
```

Start review server cleanly:

```bash
ssh source@10.0.0.186 'cd /home/source/SpiritOS && nohup .venv-face-organizer/bin/python -u scripts/media/face_organizer.py --serve-review --source /DATA/yes --host 0.0.0.0 --port 8765 --ctx-id -1 --apply > /tmp/face-organizer-8765.log 2>&1 < /dev/null &'
```

Rebuild/restart SpiritFlix `:3001` lane after frontend/API changes:

```bash
ssh source@10.0.0.186 'cp /home/source/SpiritOS/src/app/api/spiritflix/face-metadata/route.ts /tmp/spiritos-spiritflix-stable-3001/src/app/api/spiritflix/face-metadata/route.ts'
ssh source@10.0.0.186 'cp /home/source/SpiritOS/src/components/spiritflix/SpiritFlixHome.tsx /tmp/spiritos-spiritflix-stable-3001/src/components/spiritflix/SpiritFlixHome.tsx'
ssh source@10.0.0.186 'cp /home/source/SpiritOS/src/lib/spiritflix-jellyfin-client.ts /tmp/spiritos-spiritflix-stable-3001/src/lib/spiritflix-jellyfin-client.ts'
ssh source@10.0.0.186 'cd /tmp/spiritos-spiritflix-stable-3001 && npm run build'
ssh source@10.0.0.186 'fuser -k 3001/tcp; cd /tmp/spiritos-spiritflix-stable-3001 && PORT=3001 nohup npm run start > /tmp/spiritos-3001/next-start.log 2>&1 &'
```

## Pack Files

- `README.md`: this overview.
- `current-state.xml`: compact machine-readable state.
- `systems.xml`: system architecture and file responsibilities.
- `verification.xml`: latest proof and known truth about Sava/6513.
