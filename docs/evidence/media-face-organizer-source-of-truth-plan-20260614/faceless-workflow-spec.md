# Faceless Workflow Spec

## Purpose

Some videos are faceless-from-creator, and some creators/models may be fully faceless. Those cases should not endlessly appear as bad face-enrollment candidates. They still need organization, ownership, receipts, and undo.

## State model

### Faceless video

Fields:
- `canonical_video_id`
- `basename`
- `resolved_path`
- `model_label`
- `performer_id`
- `faceless_video: true`
- `faceless_reason`
- `faceless_confirmed_by`
- `faceless_confirmed_at`
- `faceless_receipt_path`
- `previous_match_state`
- `undo_available`

Meaning:
- This video does not show a usable creator face for enrollment.
- It can still belong to a model by manual, metadata, OCR, creator-folder, or confirmed visual evidence.
- It must stay out of face-rec recommendation panels.

### Faceless creator/model

Fields:
- `model_label`
- `performer_id`
- `faceless_creator: true`
- `faceless_reason`
- `faceless_confirmed_by`
- `faceless_confirmed_at`
- `faceless_receipt_path`
- `maintenance_state`
- `undo_available`

Meaning:
- The model/creator should not be treated as an endlessly failing face-enrollment candidate.
- Videos can still be organized under the creator.
- If future visible-face media appears, Britton can unmark the creator/model and enroll samples.

## Actions

### Mark current video as faceless-from-creator

Available from:
- Verification queue.
- Enrolled page video match row.
- Organization page when a current video is being reviewed.

Expected behavior:
- Set video faceless state.
- Remove its frames from face-rec recommendations.
- Keep model association if supported by manual/metadata/folder/OCR evidence.
- Add receipt with actor, reason, path, prior state, and timestamp.

### Unmark current video faceless

Available from:
- Faceless review section.
- Debug/raw evidence drawer.

Expected behavior:
- Clear video faceless state.
- Recompute whether it should enter scan, needs-decision, or unknown state.
- Add undo receipt.

### Mark entire model/creator as faceless

Available from:
- Enrolled page.
- Face enrollment queue.
- Organization page model summary.

Expected behavior:
- Set model/creator faceless state.
- Move creator out of normal face-enrollment candidate pressure.
- Keep videos associated by non-face-rec evidence when appropriate.
- Add receipt and backup registry/ledger state.

### Unmark model/creator as faceless

Available from:
- Faceless review section.
- Enrolled page debug/details.

Expected behavior:
- Clear creator faceless state.
- Recompute enrollment needs.
- Add undo receipt.

## UI locations

- Verification queue: show "Mark video faceless" for a specific video/frame group.
- Enrolled page: show "Mark model faceless" and faceless video rows in a faceless review section.
- Organization page: show faceless action where a video can be manually classified.
- Debug/raw evidence drawer: show receipts, old state, and undo controls.

## Filtering rules

- Faceless videos do not appear in face-rec recommendation panels.
- Faceless frames do not count toward enrollment readiness.
- Faceless videos can count toward model-associated videos only when labeled as faceless/manual or faceless/metadata.
- Faceless creator models should have their own maintenance state instead of "needs more screens."

## Evidence and receipt expectations

Every faceless action must record:
- Actor.
- Timestamp.
- Video/model identifier.
- Old state.
- New state.
- Reason.
- Source page/action.
- A path to the receipt.

Undo actions must also record old/new state and point back to the original receipt.
