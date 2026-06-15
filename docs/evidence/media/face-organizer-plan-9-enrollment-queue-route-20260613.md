# Face Organizer Plan 9 Enrollment Queue Route - 2026-06-13

## Files changed

- `scripts/media/face_organizer.py`
- `scripts/media/test_face_organizer_schema.py`
- Generated: `scripts/media/face_verification_report.html`
- Generated: `scripts/media/face_enrollment_queue.html`
- Generated: `scripts/media/face_enrollment_queue.json`
- Generated: `scripts/media/known_db_audit.html`
- Generated: `scripts/media/known_db_audit.json`
- Generated: `scripts/media/face_verification_full_audit.html`
- Generated: `scripts/media/manual_crop.html`
- Review artifacts: `/DATA/yes/.face-review/enrollment/enrollment_candidates.json` and crop/still files under `/DATA/yes/.face-review/enrollment/`

## Route type and URLs

Route type: static generated report pages plus a dynamic local review server for POST actions.

Start command:

```bash
cd /home/source/SpiritOS
.venv-face-organizer/bin/python scripts/media/face_organizer.py --serve-review --source /DATA/yes --host 0.0.0.0 --port 8765 --ctx-id -1
```

Open URLs:

- Verification queue: `http://10.0.0.186:8765/face_verification_report.html`
- Face enrollment queue: `http://10.0.0.186:8765/face_enrollment_queue.html`
- Known DB audit: `http://10.0.0.186:8765/known_db_audit.html`
- Manual crop tool: `http://10.0.0.186:8765/manual_crop.html`
- Full audit: `http://10.0.0.186:8765/face_verification_full_audit.html`

## Candidate generation summary

Command run:

```bash
.venv-face-organizer/bin/python scripts/media/face_organizer.py --source /DATA/yes --generate-enrollment-candidates --ctx-id -1 --sample-limit 1
```

Result:

- Groups found in bounded candidate run: 1
- Groups missing embeddings in bounded candidate run: 1
- Candidate crops generated: 10
- Blocked groups in bounded candidate run: 0
- Final queue groups found: 37
- Final queue groups missing embeddings: 36
- Final queue candidate crops visible after regeneration: 10
- Final queue blocked groups: 36

## Nav and route proof

Clean route smoke on port 8768 returned:

- `GET /face_verification_report.html`: 200, 29,877,347 bytes
- `GET /face_enrollment_queue.html`: 200, 82,883 bytes
- `GET /known_db_audit.html`: 200, 6,231 bytes
- `GET /api/enrollment/groups`: 200, 66,373 bytes, 37 groups
- Verification report contained `Face Enrollment Queue`: true
- Verification report contained `Known DB Audit`: true

Manual crop route smoke on port 8769 returned:

- `GET /manual_crop.html`: 200, 7,730 bytes
- Contains canvas tool: true
- Posts to `/api/enrollment/manual-crop`: true

Both smoke servers were stopped after verification.

## Known performer DB counts

Before and after this task:

- Known performers: 1
- Embedding rows: 1
- Embedding shape: `(1, 512)`

No real production enrollment was performed.

## Tests run

```powershell
git status --branch --short --untracked-files=normal
python -m py_compile scripts/media/face_organizer.py
python -m unittest scripts.media.test_face_organizer_schema
```

Result: 38 focused tests passed.

JSON and numpy checks:

- `scripts/media/performer_verification.json`: parsed OK
- `scripts/media/model_index.json`: parsed OK
- `scripts/media/known_performers/index.json`: parsed OK
- `scripts/media/known_performers/performer_map.json`: parsed OK
- `scripts/media/known_performers/embeddings.npy`: shape `(1, 512)`, dtype `float32`

Dell-side report generation:

```bash
.venv-face-organizer/bin/python scripts/media/face_organizer.py --source /DATA/yes --report --ctx-id -1 --sample-limit 1
```

Result: regenerated verification report, enrollment queue, known DB audit, and full audit pages.

## Safety confirmations

- No media files were moved, renamed, deleted, relocated, or organized.
- No organizer apply batch was run.
- No verify-performers apply was run.
- No real production `known_performers` enrollment happened.
- Candidate crops/stills were written only under `/DATA/yes/.face-review/enrollment/`.
- No web images, videos, thumbnails, adult media, or leaked content were downloaded.
- No internet face recognition was added or performed.
- No filename-to-model hardcoding was added for Britton's examples.
- Existing Sava Schultz embedding row remained intact.

## NEEDS_FIX items

- None for Plan 9 route/candidate/manual-crop/enrollment-gate implementation found in the focused verification.

## Next step for Britton

Start the review server, open the Face Enrollment Queue, choose a performer, review the recommended crops, optionally use Manual crop from still, then type the performer name or slug exactly before enrolling selected crops.
