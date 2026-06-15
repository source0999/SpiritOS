# Face Organizer Mini Packet

Generated: 2026-06-13
Repo: `Z:\` / `/home/source/SpiritOS`
Media source: `/DATA/yes`
Main script: `scripts/media/face_organizer.py`
Report: `scripts/media/face_verification_report.html`

## Current State

- Git-visible work: `scripts/media/face_organizer.py` modified; `scripts/media/test_face_organizer_schema.py` untracked.
- Live report regenerated: `2026-06-13T22:58:23+00:00`; size `38194857` bytes.
- Registry: 37 performers, 46 aliases, updated `2026-06-05T21:01:44+00:00`.
- Model index: 37 models: 7 `user-confirmed`, 9 `local-auto`, 21 `profile-url`.
- Known performer DB: 1 performer, `Sava Schultz`; 1 embedding row.
- Dell media snapshot: 134 video files, 105 `.face-meta.json` sidecars, 14 unknown video files, 37 model dirs.

## Implemented In This Workflow

- Plan 0: refreshed report and locked current state.
- Plan 1: added optional schema readers/defaults for `web_text_evidence`, `identity_trace`, and `assignment_decision`.
- Plan 2: added normalized OCR/filename candidates, variants, dedupe/ranking, and deterministic text query generation.
- Plan 3: added text-only provider abstraction, generated URL provider, configured-domain provider, mocked result normalization, and trust tiers.
- Plan 4: added pure assignment scorer producing `identity_trace` and `assignment_decision`.
- Plan 5: added report sections for why/trace, generated text queries, web text evidence, action snippets, and `--report-all`.
- Plan 6: hardened confirmed-crop enrollment with aliases, profile handles/URLs, `--confirmed-by`, single-face safeguards, and audit metadata.
- Plan 7: ran dry-run batch only; no media/artifact writes; stopped before small apply gate.
- Correction: `Angetawhite` now canonicalizes to `Angela White`; report regenerated after the alias update.

## Verification

- Focused tests pass locally and on Dell: 21 tests.
- Dell compile passes via `.venv-face-organizer/bin/python` with `/tmp` pyc output.
- Plan 7 dry-run sample:
  - `334120.mp4` -> `unknown performer - verification needed`.
  - `432038_720p.mp4` -> `Angetawhite (89% combined confidence)` before alias correction.
  - Dry-run reported no sidecars, crops, NFO files, or organization changes written.
  - Would-write sidecars remained absent.

## Important Boundaries

- No internet face recognition.
- No web image/video/media downloads.
- No local face-to-web-image comparison.
- No media move, rename, delete, organize, or real `--apply` was performed.
- No git branch, stash, stage, commit, push, checkout, reset, or clean was performed.
- Plan 7 small `--apply` batch still requires explicit approval before any apply command begins.
