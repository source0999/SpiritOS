# CRUD and Sync Contract

## Purpose

Every user action must update or explicitly mark pending state for every layer it affects. No action should leave Organizer, generated JSON, sidecars, known performer DB, audit pages, and SpiritFlix 3001 disagreeing silently.

## Layers

- Sidecar: per-video `.face-meta.json` and face match decisions.
- Known performer DB: `scripts/media/known_performers/`.
- Enrolled JSON: `scripts/media/face_enrolled_performers.json`.
- Queue JSON: `scripts/media/face_enrollment_queue.json`.
- Audit report: `scripts/media/known_db_audit.html` and related JSON.
- SpiritFlix face metadata API: `src/app/api/spiritflix/face-metadata/route.ts` or later ledger adapter.
- SpiritFlix UI counts: visible Jellyfin grouping and face/ledger labels.
- 3001 lane: `/tmp/spiritos-spiritflix-stable-3001`, build, restart, live verification.
- Receipts/backups: append-only decision receipts and state backups before destructive changes.

## Action contracts

### Accept recommended screen

Expected updates:
- Sidecar: link selected screen/crop to scan evidence where applicable.
- Known performer DB: add embedding/sample only after explicit confirmation and backup.
- Enrolled JSON: accepted sample count increases after regeneration.
- Queue JSON: accepted item removed from needs-confirmation queue.
- Audit report: embedding/sample counts updated.
- SpiritFlix API/UI: enrollment readiness updates after regeneration and API refresh.
- 3001: build/restart only if source frontend/API implementation changed.
- Receipt/backup: backup DB/embedding files before mutation; receipt includes crop/still/source video/similarity/quality.

### Reject recommended screen

Expected updates:
- Sidecar: optional rejection decision reference.
- Known performer DB: no embedding add.
- Enrolled JSON: recommendation excluded after regeneration.
- Queue JSON: recommendation removed or marked rejected.
- Audit report: rejection count available in debug.
- SpiritFlix API/UI: no face-rec increase.
- Receipt/backup: append rejection receipt with reason.

### Remove accepted screen

Expected updates:
- Sidecar: no source face evidence deletion unless explicitly approved.
- Known performer DB: remove embedding/sample only after backup.
- Enrolled JSON: accepted sample count decreases after regeneration.
- Queue JSON: if still useful, sample may reappear as candidate only if not rejected.
- Audit report: embedding/sample counts updated.
- SpiritFlix API/UI: readiness updates.
- Receipt/backup: mandatory backup and removal receipt.

### Confirm video match

Expected updates:
- Sidecar: append accepted decision with visual confirmation and actor.
- Known performer DB: no new embedding unless screen accepted separately.
- Enrolled JSON: match appears as manual-confirmed or face-rec-supported based on evidence type.
- Queue JSON: video removed from pending match queue.
- Audit report: decision visible.
- SpiritFlix API/UI: status label uses correct evidence type.
- Receipt/backup: append decision receipt.

### Deny video match

Expected updates:
- Sidecar: append denied decision.
- Known performer DB: no embedding change.
- Enrolled JSON/queue JSON: denied video excluded from match suggestions for that model.
- Audit report: denial visible in debug.
- SpiritFlix API/UI: must not show denied model as face-rec match.
- Receipt/backup: append denial receipt.

### Mark video faceless-from-creator

Expected updates:
- Sidecar or ledger state: set `faceless_video: true` with actor/reason.
- Known performer DB: no embedding change.
- Enrolled JSON/queue JSON: video removed from face-rec recommendation panels and moved to faceless review/maintenance.
- Audit report: faceless video count and receipts visible.
- SpiritFlix API/UI: video can still be assigned manually/metadata-only but not shown as face-rec evidence.
- Receipt/backup: append faceless-video receipt.

### Unmark video faceless

Expected updates:
- Sidecar or ledger state: clear faceless flag with actor/reason.
- Enrolled JSON/queue JSON: video may re-enter scan/review flow if it has usable evidence.
- Audit report: undo receipt visible.
- SpiritFlix API/UI: faceless badge removed after refresh.
- Receipt/backup: append undo receipt.

### Mark model/creator as faceless

Expected updates:
- Registry/ledger: set `faceless_creator: true`.
- Known performer DB: no embedding change unless approved separately.
- Enrolled JSON/queue JSON: model exits normal "needs face enrollment" pressure and enters faceless maintenance state.
- Audit report: creator-level faceless state visible.
- SpiritFlix API/UI: model can still contain videos but should not imply face-rec readiness failure.
- Receipt/backup: backup registry and append creator faceless receipt.

### Unmark model/creator as faceless

Expected updates:
- Registry/ledger: clear `faceless_creator`.
- Queue/enrolled JSON: model re-enters appropriate review/enrollment state after regeneration.
- Audit report: undo visible.
- Receipt/backup: backup registry and append undo receipt.

### Merge duplicate model labels

Expected updates:
- Sidecars: decisions/performer IDs reconciled or old labels mapped.
- Known performer DB: performer IDs and aliases merged only after backup.
- Enrolled JSON/queue JSON/audit: one canonical label after regeneration.
- SpiritFlix API/UI: alias map consumes canonical ledger names.
- Receipt/backup: mandatory backup of registry/known DB and merge receipt.

### Rescan enrolled model

Expected updates:
- Sidecars/review artifacts: scan outputs refreshed for selected model scope only.
- Known performer DB: no direct mutation unless accept actions follow.
- Enrolled JSON/queue JSON: regenerated from scan and ledger.
- Audit report: scan timestamp and counts updated.
- SpiritFlix API/UI: no live source/API code change unless adapter changed.
- Receipt/backup: scan receipt with command, scope, and artifact paths.

### Ingest/upload/update video

Expected updates:
- Media ingest receipt: source/final path, job ID, timestamps, and profile.
- Ledger: new or updated canonical video row.
- Sidecar: scan pending until face-rec run creates/refreshes it.
- Enrolled/queue/audit: regenerated after scan or explicit refresh.
- SpiritFlix API/UI: item appears only after Jellyfin exposes it.
- 3001: no code build unless frontend/API changed; Jellyfin visibility must be checked separately.
- Receipt/backup: upload/update receipt preserved.

### Regenerate organizer pages

Expected updates:
- Enrolled JSON/HTML, queue JSON/HTML, verification report, known DB audit generated from ledger-derived state.
- Sidecars/known DB: no mutation unless action explicitly requested.
- SpiritFlix API/UI: metadata changes visible after API rereads generated/ledger files.
- Receipt/backup: generation receipt or command log.

### Sync SpiritFlix 3001 lane

Expected updates:
- Source repo frontend/API changes copied to `/tmp/spiritos-spiritflix-stable-3001`.
- 3001 working copy built.
- Port 3001 restarted.
- Live `http://10.0.0.186:3001/spiritflix` verified.
- SpiritFlix UI counts separated as Jellyfin visible count vs ledger/source/model counts.
- Receipt/backup: record copy/build/restart commands and verification.

## Global checks

- Each action must be idempotent or produce a clear duplicate-action error.
- Each action must have an undo path when state is user-driven.
- Each generated surface must show the same ledger-derived evidence type.
- No UI label may say or imply face-rec confidence for metadata/manual/OCR-only evidence.
