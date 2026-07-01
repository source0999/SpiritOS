# SpiritFlix AI Subtitles Final Evidence

- verdict: GO
- generatedAt: 2026-06-27T23:13:00Z
- repo: /home/source/SpiritOS
- pilot media: /mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 02/Rurouni Kenshin (1996) - S02E03 [DVD 576p Mobile].mp4
- mediaKey: 7902d559989f124c188ca3b2
- backend: faster-whisper/base
- backend python: /mnt/spirit-8tb/media/.spiritflix-admin/captions/venv/bin/python
- selected audio: ffmpeg map 0:2, language eng

## Generated VTT

- path: /mnt/spirit-8tb/media/.spiritflix-admin/captions/generated/7902d559989f124c188ca3b2/ai-en.vtt
- size: 20855 bytes
- startsWithWebVtt: true
- cueCount: 238
- emptyCueCount: 0
- zeroDurationCueCount: 0
- overlapCount: 0
- firstCueTime: 00:02:19.310
- lastCueTime: 00:23:14.680
- totalCaptionedDurationSeconds: 1229.62

## Manifest/API Proof

- manifest path: /mnt/spirit-8tb/media/.spiritflix-admin/captions/manifests/7902d559989f124c188ca3b2.json
- manifest tracks: 3
- source tracks preserved:
  - caption-282894e9d081f31c, embedded, SubtitleHandler
  - caption-48c402f3d2476d3e, embedded, English Forced
- generated track:
  - id: ai-en
  - sourceType: generated
  - label: English Dub AI Captions
  - kind: captions
  - reviewStatus: draft
  - generatedBy: faster-whisper/base
  - publicUrl: /api/spiritflix/captions/file?key=7902d559989f124c188ca3b2&track=ai-en
- live manifest endpoint returned the generated track.
- live VTT endpoint returned HTTP 200 with `content-type: text/vtt; charset=utf-8` and body starting with `WEBVTT`.

## Player Proof

- browser evidence: docs/evidence/spiritflix-ai-subtitles-browser-20260627-2311/player-generated-ai-track.json
- screenshot: docs/evidence/spiritflix-ai-subtitles-browser-20260627-2311/player-generated-ai-track.png
- Playwright result:
  - videoPresent: true
  - trackCount: 3
  - generated track label: English Dub AI Captions
  - generated track src: /api/spiritflix/captions/file?key=7902d559989f124c188ca3b2&track=ai-en
  - source tracks remained rendered as native track elements.

## Verification Commands

- `python -m py_compile scripts\\media\\spiritflix_ai_subtitles.py`: pass
- `python3 -m py_compile scripts/media/spiritflix_ai_subtitles.py`: pass
- `python3 scripts/media/spiritflix_ai_subtitles.py --detect-only --no-install`: pass, faster-whisper venv backend detected
- `python3 scripts/media/spiritflix_ai_subtitles.py --file ... --model base --language en --skip-existing --force`: pass
- `python3 scripts/media/spiritflix_ai_subtitles.py --root /mnt/spirit-8tb/media/yes --limit 5 --model base --language en --skip-existing --dry-run`: pass
- `npx tsc --noEmit --pretty false`: pass
- `npm exec vitest run src/app/api/spiritflix/captions/__tests__/captions-route.test.ts src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx`: pass, 49 tests
- Playwright browser check against `https://127.0.0.1:3000/spiritflix/benchmark/player`: pass

## Boundaries

- original media files were not overwritten, moved, deleted, renamed, or transcoded.
- Jellyfin DB/config were not edited.
- Jellyfin was not restarted.
- no paid or cloud ASR/transcription API was called; transcription ran locally through the caption-root faster-whisper venv.
- temporary audio directory for the pilot key exists but is empty after cleanup.
