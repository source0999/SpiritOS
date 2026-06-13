# Failure Bucket Audit

Status: COMPLETE BEFORE PATCHING

## Current Bucket Problems

| Prompt | Current bucket | Strict bucket needed | Problem |
|---|---|---|---|
| build me a snack break countdown | behavior_failed_verified | timer_no_visible_change_after_start | Too generic |
| make a day night color flipper | not_eligible_for_behavior_repair | theme_preview_resolution_failed / route_blocked_no_preview | Missing preview-specific bucket |
| make a quick jot pad app | none | notes_saved_status_without_note_text | False-positive PASS |
| make a login safety gauge | behavior_failed_verified | password_no_visible_strength_text_change | Too generic |
| make a scribble sketch pad | free_floating_code_no_path_action | drawing_canvas_no_pixel_change plus repair_free_floating_code_no_path_action | Repair failure hid primary behavior failure |

## Required Report Shape

Reports should carry both:

- `primary_behavior_failure_bucket`
- `repair_failure_bucket`

This prevents a repair-contract failure from hiding the original behavior failure.
