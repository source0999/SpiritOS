# Postpatch Diagnostic Results

Date: 2026-06-13

## Old 10d Versus Rerun

- Old 10d report before this pass: 6/10 PASS, 4 FAIL, NO-GO.
- Prepatch strict audit of the same evidence: 5/10 PASS, 5 FAIL, NO-GO.
- 10d rerun after score-integrity patch: 5/10 PASS, 5 FAIL, NO-GO.
- Corrected false-positive: `make a quick jot pad app`.
- Fresh 10d HTML: `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d.html`

## Fresh 10e

- 10e fresh blind run: 6/10 PASS, 4 FAIL, NO-GO.
- Fresh 10e HTML: `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e.html`

## 10d Failure Buckets

- `timer_no_visible_change_after_start`: 1
- `route_blocked_no_preview`: 1
- `notes_saved_status_without_note_text`: 1
- `password_no_visible_strength_text_change`: 1
- `drawing_canvas_no_pixel_change`: 1

Repair buckets:

- `repair_handoff_missing_probe_metadata`: 2
- `repair_free_floating_code_no_path_action`: 1

## 10e Failure Buckets

- `timer_no_visible_change_after_start`: 1
- `route_blocked_no_preview`: 1
- `player_control_no_visible_state_change`: 1
- `password_no_visible_strength_text_change`: 1

Repair buckets:

- `repair_free_floating_code_no_path_action`: 2
- `repair_handoff_missing_probe_metadata`: 1

## False Positives / False Negatives

- Prepatch audit: 1 false-positive PASS, 0 false-negative FAIL.
- 10d rerun report after patch: 0 score-integrity warnings, 0 false-positive corrections remaining, 0 false-negative corrections remaining.
- 10e fresh report after patch: 0 score-integrity warnings, 0 false-positive corrections remaining, 0 false-negative corrections remaining.

## Level 3

Level 3 remains NO-GO. The score-integrity patch corrected scoring, but the product behavior gate is still below 8/10 on both 10d rerun and fresh 10e.
