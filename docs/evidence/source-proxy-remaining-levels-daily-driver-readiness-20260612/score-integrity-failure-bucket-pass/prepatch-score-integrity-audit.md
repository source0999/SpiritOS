# Prepatch Score-Integrity Audit

Status: COMPLETE BEFORE PATCHING

Source: `anti-tailoring-random-10d-results.json` plus per-row `behavior-probe.json`, `score.json`, and repair summaries.

## Summary

Strict human review found 1 false-positive PASS in 10d before this patch: `make a quick jot pad app`.

The current report says 6/10 PASS. Strict review says 5/10 PASS, because a notes/jot app must display the typed note text, not only a saved-status message.

## Row Review

| Row | Prompt | Category | Route | Open | Report behavior/final | Strict final | Classification | Strict bucket |
|---|---|---|---|---|---|---|---|---|
| 01 | build me a snack break countdown | timer | GO | PASS | FAIL/FAIL | FAIL | correct_as_reported | timer_no_visible_change_after_start |
| 02 | make a pizza money splitter | calculator/splitter | GO | PASS | PASS/PASS | PASS | correct_as_reported |  |
| 03 | make a day night color flipper | theme toggle | EXPECTED-BLOCKED | FAIL | FAIL/FAIL | FAIL | correct_as_reported | theme_preview_resolution_failed |
| 04 | make a farmers market checklist app | checklist/list | GO | PASS | PASS/PASS | PASS | correct_as_reported |  |
| 05 | make a pretend weekend forecast card | weather/forecast/card | GO | PASS | PASS/PASS | PASS | correct_as_reported |  |
| 06 | make a tiny mixtape player | player/podcast/music | GO | PASS | PASS/PASS | PASS | correct_as_reported |  |
| 07 | make a coffee cup counter | tracker/counter | GO | PASS | PASS/PASS | PASS | correct_as_reported |  |
| 08 | make a quick jot pad app | notes app | GO | PASS | PASS/PASS | FAIL | false_positive_pass | notes_saved_status_without_note_text |
| 09 | make a login safety gauge | password meter/checker | GO | PASS | FAIL/FAIL | FAIL | correct_as_reported | password_no_visible_strength_text_change |
| 10 | make a scribble sketch pad | drawing/canvas/sketch | GO | PASS | FAIL/FAIL | FAIL | correct_as_reported | drawing_canvas_no_pixel_change |

## Specific Findings

- `make a quick jot pad app`: `appears: false`; visible output was only `Note saved successfully.`. This is a false-positive PASS.
- `make a pizza money splitter`: `appears: false` is irrelevant for splitter criteria; the visible numeric result changed to `21.00`, so PASS is correct.
- `build me a snack break countdown`: `afterStart` stayed `25:00`; `afterStop` became `24:59`, so start behavior is not proven. The right bucket is `timer_no_visible_change_after_start` with possible probe/action ambiguity.
- `make a day night color flipper`: no preview opened; bucket should be preview/theme resolution, not behavior repair.
- `make a login safety gauge`: weak/strong visible text did not change; bucket should be password strength text unchanged.
- `make a scribble sketch pad`: canvas existed but pixels did not change; repair then failed as free-floating code without path/action.
