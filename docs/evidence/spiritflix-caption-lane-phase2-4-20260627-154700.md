# SpiritFlix Caption Lane Phases 2-4 Evidence

## Verdict

GO for Phases 2-3 and Phase 4 plumbing.

AI runtime is NO-GO until a local transcription backend is installed. The AI script reports `AI_BACKEND_UNAVAILABLE` and does not download models or call cloud APIs.

## Git

- Branch: `integration/cleanup-plan3-debug-20260623`
- Starting HEAD: `83330069596c781d92b65153b0fc50ab04df29f6`
- Ending HEAD: `83330069596c781d92b65153b0fc50ab04df29f6`
- Commit made: no
- Dirty state before: existing working tree was already dirty from SpiritFlix work in this session.
- Dirty state after: caption files changed plus unrelated existing untracked Source Proxy evidence receipts under `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`.

## Files Changed

- `scripts/media/spiritflix_caption_extract.py`
- `scripts/media/spiritflix_caption_generate_ai.py`
- `scripts/media/spiritflix_caption_inventory.py`
- `src/lib/spiritflix-types.ts`
- `src/lib/spiritflix/captions.ts`
- `src/app/api/spiritflix/captions/manifest/route.ts`
- `src/app/api/spiritflix/captions/file/route.ts`
- `src/app/api/spiritflix/captions/__tests__/captions-route.test.ts`
- `src/components/spiritflix/SpiritFlixPlayer.tsx`
- `src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx`
- `docs/evidence/spiritflix-caption-lane-phase2-4-20260627-154700.md`

## Commands Run

```bash
python3 -m py_compile scripts/media/spiritflix_caption_inventory.py scripts/media/spiritflix_caption_extract.py scripts/media/spiritflix_caption_generate_ai.py
python3 scripts/media/spiritflix_caption_extract.py --dry-run --pilot 'S01E01'
python3 scripts/media/spiritflix_caption_extract.py --pilot 'S01E01'
python3 scripts/media/spiritflix_caption_extract.py --dry-run
python3 scripts/media/spiritflix_caption_generate_ai.py --media-file '/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01 [DVD 576p Mobile].mp4'
python3 scripts/media/spiritflix_caption_generate_ai.py --media-file '/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01 [DVD 576p Mobile].mp4' --allow-when-source-captions-exist --dry-run
npx tsc --noEmit --pretty false
npx vitest run src/app/api/spiritflix/captions/__tests__/captions-route.test.ts src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx
curl -k 'https://127.0.0.1:3000/api/spiritflix/captions/manifest?key=a9dd8afd23dd9ac58986413f'
curl -k -D - 'https://127.0.0.1:3000/api/spiritflix/captions/file?key=a9dd8afd23dd9ac58986413f&track=caption-af65a446e1884490'
curl -k -D - 'https://127.0.0.1:3000/api/spiritflix/captions/file?key=a9dd8afd23dd9ac58986413f&track=caption-736a4bfbb9964566'
node /tmp/spiritflix-caption-track-proof.js
```

## Checks

- Python compile with `python3 -m py_compile`: PASS
- Exact `python -m py_compile ...`: environment alias NO-GO, `bash: line 1: python: command not found`
- TypeScript: PASS
- Focused Vitest: PASS, 3 files, 63 tests
- Existing SpiritFlix player/home tests in focused run: PASS
- API route tests: PASS

Vitest emitted existing React `act(...)` warnings in older SpiritFlix tests, but all focused tests passed.

## Extraction

Latest inventory: `/mnt/spirit-8tb/media/.spiritflix-admin/captions/inventory/20260627.jsonl`

Full dry-run:

```json
{"extractable":20,"extracted":0,"failed":0,"manifestsWritten":0,"skipped":3}
```

Pilot dry-run:

```json
{"extractable":2,"extracted":0,"failed":0,"manifestsWritten":0,"skipped":0}
```

Pilot real extraction:

```json
{"extractable":2,"extracted":2,"failed":0,"manifestsWritten":1,"skipped":0}
```

Extraction evidence:

- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/evidence/caption-extract-20260627-193721.json`
- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/evidence/caption-extract-20260627-193734.json`
- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/evidence/caption-extract-20260627-194430.json`

## Kenshin Pilot

Media:

`/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01 [DVD 576p Mobile].mp4`

Manifest:

`/mnt/spirit-8tb/media/.spiritflix-admin/captions/manifests/a9dd8afd23dd9ac58986413f.json`

Extracted VTT files:

- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/cache/a9dd8afd23dd9ac58986413f/caption-af65a446e1884490.vtt`, 28290 bytes, starts with `WEBVTT`
- `/mnt/spirit-8tb/media/.spiritflix-admin/captions/cache/a9dd8afd23dd9ac58986413f/caption-736a4bfbb9964566.vtt`, 861 bytes, starts with `WEBVTT`

Manifest tracks:

```json
[
  {
    "id": "caption-af65a446e1884490",
    "sourceType": "embedded",
    "sourceFormat": "mov_text",
    "outputFormat": "vtt",
    "language": "eng",
    "label": "SubtitleHandler",
    "default": true,
    "forced": false
  },
  {
    "id": "caption-736a4bfbb9964566",
    "sourceType": "embedded",
    "sourceFormat": "mov_text",
    "outputFormat": "vtt",
    "language": "eng",
    "label": "English Forced",
    "default": false,
    "forced": true
  }
]
```

## API Proof

Manifest endpoint:

`GET https://127.0.0.1:3000/api/spiritflix/captions/manifest?key=a9dd8afd23dd9ac58986413f`

Result: HTTP 200 with two tracks and public URLs for both cached VTT files.

Caption file endpoints:

- `GET /api/spiritflix/captions/file?key=a9dd8afd23dd9ac58986413f&track=caption-af65a446e1884490`
- `GET /api/spiritflix/captions/file?key=a9dd8afd23dd9ac58986413f&track=caption-736a4bfbb9964566`

Both returned:

- HTTP 200
- `content-type: text/vtt; charset=utf-8`
- body prefix `WEBVTT`

## Player Proof

Focused player test proves `SpiritFlixPlayer` renders native `<track>` elements from the caption manifest and keeps playback alive if manifest fetch fails.

Browser proof was run on the live SpiritFlix HTTPS origin without logging into Jellyfin. It fetched the real caption manifest/file APIs and attached the returned tracks to a native browser `video` element:

```json
{
  "manifestTrackCount": 2,
  "domTrackCount": 2,
  "tracks": [
    {
      "kind": "subtitles",
      "src": "/api/spiritflix/captions/file?key=a9dd8afd23dd9ac58986413f&track=caption-af65a446e1884490",
      "srclang": "eng",
      "label": "SubtitleHandler",
      "default": true,
      "sourceType": "embedded"
    },
    {
      "kind": "subtitles",
      "src": "/api/spiritflix/captions/file?key=a9dd8afd23dd9ac58986413f&track=caption-736a4bfbb9964566",
      "srclang": "eng",
      "label": "English Forced",
      "default": false,
      "sourceType": "embedded"
    }
  ],
  "fileResponses": [
    {
      "status": 200,
      "contentType": "text/vtt; charset=utf-8",
      "prefix": "WEBVTT"
    },
    {
      "status": 200,
      "contentType": "text/vtt; charset=utf-8",
      "prefix": "WEBVTT"
    }
  ]
}
```

Screenshot artifact:

`/tmp/spiritflix-caption-track-proof.png`

## AI Phase 4

Backend detection:

- `ffmpeg`: `/usr/bin/ffmpeg`
- `faster-whisper`: unavailable
- `whisper`: unavailable
- `whisper-cli`: unavailable
- `main`/whisper.cpp generic binary: unavailable

Guardrail proof:

- Running against Kenshin without override refused with `SOURCE_CAPTIONS_EXIST`.
- Running with `--allow-when-source-captions-exist --dry-run` refused with `AI_BACKEND_UNAVAILABLE`.
- Script requires `--media-file`; no-argument execution fails with argparse required-file error.

AI generation is manual, single-file only, does not batch, does not call cloud APIs, and does not download models.

## Safety

- No media files were modified, moved, renamed, deleted, transcoded, or rewritten.
- No Jellyfin DB/config/cache was edited.
- Jellyfin was not restarted.
- Cached/generated caption writes are under `/mnt/spirit-8tb/media/.spiritflix-admin/captions/`.
- Temporary path policy is reserved under `/mnt/spirit-8tb/media/.spiritflix-admin/captions/tmp/`.
- Existing cached VTT files are not overwritten unless extraction is run with `--force`.

## Final Verdict

GO for caption discovery, extraction to WebVTT cache, manifest/file APIs, and SpiritFlix player integration.

Phase 4 plumbing GO; AI runtime NO-GO because no local transcription backend is installed.
