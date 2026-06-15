# SpiritOS Media Model Sorting Diagnostic

Generated: 2026-06-13
Repo path: `Z:\` / `/home/source/SpiritOS`
Main script: `scripts/media/face_organizer.py`
Media source used by current artifacts: `/DATA/yes`

## Short Verdict

The current system is a local media model organizer. It does look at faces, but the local face database currently has only one enrolled performer embedding, so face recognition is narrow. In practice, most model naming is coming from visible watermark/profile OCR, filename hints, alias cleanup, profile-handle extraction, and user-confirmed corrections.

It does not currently perform live Yandex/private/Mac/browser searches during batch scanning. The only executable online provider hook is optional pAPI/RapidAPI metadata behind `--online-metadata` and `PAPI_RAPIDAPI_KEY`; current registry state says online metadata was not requested. The report generator has been patched to add manual text-verification links for Yandex, Yandex scoped to `pimpbunny.com`, Yandex scoped to `coomer.st`, and direct `coomer.st` search, but the live HTML report has not been regenerated since that patch.

## Current Artifact State

- `scripts/media/performer_verification.json`
  - Schema: `media-performer-verification/v1`
  - Source dir: `/DATA/yes`
  - Generated: `2026-06-05T20:58:47+00:00`
  - Updated: `2026-06-05T21:01:44+00:00`
  - Performer count: 37
  - Alias count: 46
  - `online_metadata_requested`: false
- `scripts/media/model_index.json`
  - Schema: `spiritflix-model-index/v1`
  - Generated: `2026-06-05T21:01:44+00:00`
  - Model count: 37
  - Status counts:
    - `user-confirmed`: 7
    - `local-auto`: 9
    - `profile-url`: 21
  - Models with extracted profile handles: 21
- `scripts/media/known_performers/`
  - `index.json`: 1 performer, `Sava Schultz`
  - `performer_map.json`: 1 embedding row mapped to `sava-schultz`
  - `embeddings.npy`: 2176 bytes
- `scripts/media/face_verification_report.html`
  - Generated before the new verifier-link patch.
  - Current report contains 15 review cards, all `needs-review`.
  - Current report includes `407017_720p.mp4`.
  - Current report does not yet include the new `Text verification links` section because it needs regeneration on the Dell host.
- Current git-visible code change:
  - `scripts/media/face_organizer.py` modified to add report-side manual verifier links.

## What Happens In A Batch

Typical scan command:

```bash
cd /home/source/SpiritOS
. .venv-face-organizer/bin/activate
python scripts/media/face_organizer.py --source /DATA/yes --sample-limit 30 --apply --ctx-id -1
```

Batch scan lifecycle:

1. Build config from CLI/env.
   - Default source is `/mnt/spirit-8tb/media/other`, but current working media source is `/DATA/yes`.
   - Default model is InsightFace `buffalo_l`.
   - Default frame count is 6.
   - Default OCR is enabled through `--ocr-watermarks`.
   - Default thresholds are `HIGH_CONFIDENCE = 0.80` and `POSSIBLE_CONFIDENCE = 0.55`.
2. Load local known performer DB from `scripts/media/known_performers`.
3. Initialize InsightFace.
   - `--ctx-id -1` means CPU.
   - Non-negative ctx uses CUDA first, then CPU fallback.
4. Find videos under the source directory.
   - Excludes `.face-review`, `models`, `unknown`, `backups`, `review_exports`, and `known_performers`.
   - Skips fresh already-approved sidecars unless `--force`.
   - Re-scans missing sidecars, stale sidecars, or sidecars where `verification_needed` is true.
5. For each video:
   - Run `ffprobe` for duration.
   - Extract evenly spaced frames with `ffmpeg`.
   - If `--apply`, persist review frames under `.face-review/<video-stem>/frames/`.
6. Face path:
   - Run InsightFace detection on extracted frames.
   - Reject weak faces below `min_face_score` or tiny faces below `min_face_area_ratio`.
   - Normalize embeddings for accepted faces.
   - Compare against local `known_performers/embeddings.npy`.
   - `>= 0.80` similarity becomes `auto`.
   - `>= 0.55` and `< 0.80` becomes `possible`, requiring review.
   - No match becomes `unknown performer`.
   - If `--apply`, save crops and source frames for review.
7. Watermark/text path:
   - OCR full frame plus watermark-heavy crops:
     - full
     - bottom strip
     - top strip
     - bottom left
     - bottom right
     - top left
     - top right
   - Uses `rapidocr_onnxruntime` if installed.
   - Parses patterns like:
     - `OnlyFans.com/<handle>`
     - `Fansly.com/<handle>`
     - `Fanvue.com/<handle>`
     - `stolen from <handle>`
     - `leaked from <handle>`
     - `@handle`
   - Filters obvious host/repost/noise strings such as Telegram, Thothub, Viraixxxporn-like strings, `OnlyFans.c` fragments, long hashes, and generic junk.
8. Filename path:
   - Extracts weak candidate names from filename/stem and parent folder.
   - These are lower-confidence hints, not strong verification.
9. Optional online path:
   - Only used by `--enrich-metadata`/backfill style flows when `--online-metadata` is passed.
   - Calls pAPI/RapidAPI only if `PAPI_RAPIDAPI_KEY` is configured.
   - No Yandex, browser, private search, Coomer, or PimpBunny API search runs during batch scanning today.
10. Combined identity path:
   - Chooses best watermark hint.
   - If watermark has a full profile URL and confidence >= 0.75, it can auto-approve.
   - If watermark agrees with a face match and face similarity >= possible threshold, it can auto-approve.
   - Otherwise it remains review/probable/unknown.
11. Write sidecar if `--apply`.
   - Sidecar path: `<video filename>.face-meta.json`.
   - Contains performers, review frames, OCR hints, face counts, rejected faces, thresholds, suggested organization, and verification flag.

## What Verify-Performers Does

Typical command:

```bash
python scripts/media/face_organizer.py --source /DATA/yes --verify-performers --apply --ctx-id -1
```

This command does not scan frames. It reads existing sidecars and:

1. Loads/preserves alias registry.
2. Rebuilds `performer_verification.json` from sidecars.
3. Canonicalizes performer names through seed aliases plus learned registry aliases.
4. Extracts trusted profile handles from OCR hints.
5. Marks performer status:
   - `user-confirmed` if correction signal exists.
   - `profile-url` if a trusted profile handle was extracted.
   - `local-auto` if a local face auto match exists.
   - `needs-review` otherwise.
6. Writes `model_index.json` for SpiritFlix model cards.
7. Calls `organize_videos()` when `--apply`.
8. Removes empty model folders.

Important: `verify_performers` receives `enable_online`, but current implementation only records `online_metadata_requested`; it does not call any web search provider itself.

## What Organize Does After Verification

`organize_videos()` reads sidecars and moves media:

- If a record has an auto performer and no verification needed:
  - Move video into `/DATA/yes/models/<model-slug>/`.
- Otherwise:
  - Move video into `/DATA/yes/unknown/`.
- It moves matching `.face-meta.json` and `.nfo` sidecars too.
- It updates embedded `video_path`, `path`, `filename`, organization bucket, and final path.
- It writes `scripts/media/organize_manifest.json`.
- With `--apply`, it first creates selected backups.

## What The Report Does

Typical command:

```bash
python scripts/media/face_organizer.py --source /DATA/yes --report --ctx-id -1
```

Report generation:

- Reads sidecars from source.
- Shows only records where `verification_needed` is true.
- Embeds review frames and face crops as base64 image data.
- Shows performer badges, OCR/metadata hints, face counts, and action commands.
- After the latest code patch, it also renders manual text verification links for top OCR hints:
  - Yandex exact query
  - Yandex exact query scoped to `site:pimpbunny.com`
  - Yandex exact query scoped to `site:coomer.st`
  - Direct `coomer.st` search

The live HTML currently predates that patch, so regenerate it on the Dell to see the links.

## 407017_720p.mp4 Snapshot

Current report entry:

- File: `407017_720p.mp4`
- Sidecar path in report: `/DATA/yes/unknown/407017_720p.mp4.face-meta.json`
- Status: `needs-review`
- Faces: 0
- OCR hints:
  - `M Anyuitio`
  - `M Anvuitio`
  - `Mulan T`
  - `M Muanvuitto`
  - `RETO`
- No saved face crops.

Interpretation: this file cannot be resolved by the current local face DB because no usable face was detected/saved in the report. The best next path is text/watermark verification and improved OCR/candidate parsing.

## Key Files

- `scripts/media/face_organizer.py`
  - Main pipeline: scan, OCR, face matching, sidecars, registry, report, organization.
- `scripts/media/known_performers/index.json`
  - Human-added known performer records.
- `scripts/media/known_performers/embeddings.npy`
  - Local face embedding matrix.
- `scripts/media/known_performers/performer_map.json`
  - Embedding-row to performer-id map.
- `scripts/media/performer_verification.json`
  - Canonical performer registry, aliases, evidence, profile handles, statuses.
- `scripts/media/model_index.json`
  - SpiritFlix-readable model index.
- `scripts/media/face_verification_report.html`
  - Review UI/report served on port 8765.
- `scripts/media/organize_manifest.json`
  - Last organization move manifest.
- `scripts/media/rename_plan.json`
  - Review-only rename plan; does not apply renames.

## Code Reference Map

- Constants/exclusions/thresholds: `face_organizer.py:84`
- pAPI online provider hook: `face_organizer.py:275`
- OCR region crops: `face_organizer.py:318`
- OCR execution: `face_organizer.py:359`
- Watermark parsing: `face_organizer.py:585`
- Metadata hint build: `face_organizer.py:647`
- Local known performer DB: `face_organizer.py:690`
- Face match thresholds: `face_organizer.py:786`
- Seed aliases: `face_organizer.py:805`
- Trusted profile handles: `face_organizer.py:856`
- Registry schema: `face_organizer.py:882`
- Profile-handle extraction: `face_organizer.py:938`
- Combined watermark/face identity: `face_organizer.py:1113`
- InsightFace recognizer: `face_organizer.py:1177`
- Video discovery: `face_organizer.py:1236`
- Frame extraction: `face_organizer.py:1293`
- Face filtering: `face_organizer.py:1327`
- Face result aggregation: `face_organizer.py:1341`
- Per-video scan: `face_organizer.py:1424`
- Batch scan: `face_organizer.py:1525`
- Metadata collection: `face_organizer.py:1572`
- Metadata enrichment: `face_organizer.py:1696`
- Organization moves: `face_organizer.py:1854`
- Performer verification/model index: `face_organizer.py:1921`
- Frame backfill: `face_organizer.py:2062`
- New manual verifier links: `face_organizer.py:2140`
- Report render: `face_organizer.py:2181`
- Add performer from crop: `face_organizer.py:2407`
- CLI args: `face_organizer.py:2428`

## Important Boundaries

- The system should not do internet face recognition or identify people by comparing faces to web images.
- It is safe to use visible text, watermarks, profile URLs, handles, filenames, sidecars, and user corrections.
- Host/repost sites must not become model names.
- Full creator profile watermarks are stronger than vague face similarity.
- Weak OCR noise should stay review/unknown.
- Online metadata should be text-based and evidence-preserving, not face identification.

## Current Gaps / Patch Targets

1. Live report is stale relative to code.
   - Regenerate `face_verification_report.html` on the Dell host.
2. No batch web text search.
   - Current batch does not query Yandex, Coomer, PimpBunny, or private search.
   - Patch target: add a text-only provider abstraction that accepts OCR/filename candidates and returns evidence URLs/snippets without face-image matching.
3. Local face DB is too small.
   - Only Sava Schultz has an enrolled embedding.
   - Patch target: add a review workflow to enroll confirmed crops from report actions.
4. OCR candidate quality is noisy.
   - Example: `407017_720p.mp4` has likely OCR distortions.
   - Patch target: add better OCR region weighting, multi-frame dedupe, candidate spell variants, and manual search links for all plausible variants.
5. `verify_performers(enable_online=True)` does not actually enrich online.
   - It only records that online metadata was requested.
   - Patch target: either remove misleading flag or wire it into text-only lookup evidence.
6. Report only shows review-needed records.
   - Useful for queue, but hides auto/profile-url evidence from quick audit.
   - Patch target: add report mode/filter for all records or model index audit.
7. Generated outputs are not automatically served/refreshed after code changes.
   - Patch target: add a safe refresh command or watcher for report regeneration.
8. No durable web-verification evidence schema yet.
   - Patch target: add fields like `web_text_evidence`, `provider`, `query`, `url`, `matched_handle`, `confidence`, `review_required`.

## Recommended Patch Order

1. Regenerate report and verify new links render.
2. Add text-only web evidence schema to sidecars/registry.
3. Add provider config for manual-safe sources:
   - Yandex search URL generation
   - Coomer text/profile URL lookup
   - PimpBunny site-scoped query
   - user-provided source list
4. Add dry-run evidence collection mode before any organizer moves.
5. Improve OCR candidate variants and report display.
6. Add report sections for web evidence and explicit "why this model name" traces.

## Commands For Next Chat

Regenerate report on Dell:

```bash
cd /home/source/SpiritOS
. .venv-face-organizer/bin/activate
python scripts/media/face_organizer.py --source /DATA/yes --report --ctx-id -1
```

Run a small scan batch:

```bash
cd /home/source/SpiritOS
. .venv-face-organizer/bin/activate
python scripts/media/face_organizer.py --source /DATA/yes --sample-limit 30 --apply --ctx-id -1
python scripts/media/face_organizer.py --source /DATA/yes --verify-performers --apply --ctx-id -1
python scripts/media/face_organizer.py --source /DATA/yes --report --ctx-id -1
```

Serve report:

```bash
cd /home/source/SpiritOS/scripts/media
python3 -m http.server 8765 --bind 0.0.0.0
```

Current URLs:

- Tailscale/mobile: `http://100.111.32.31:8765/face_verification_report.html`
- LAN: `http://10.0.0.186:8765/face_verification_report.html`
