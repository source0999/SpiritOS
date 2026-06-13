# Source Proxy Simple Blunt Prompt Diagnostics

Evidence-only run after multi-model foundation integration. No code patches, sidecar activation, model swap, autonomy work, Obsidian writes, benchmark expansion, or failure fixes were performed.

## Batch Counts

- Runs: 10
- Route GO: 10/10
- Artifacts opened: 10/10
- Browser behavior probes PASS: 10/10
- Real app files touched: 0/10
- Backend-created content detected: 0/10
- Live sidecar lanes used: 0/10
- Web search used: 0/10

## Prompt Results

| # | Prompt | Route | Shape | Artifact | Files | Opens | Usable probe | Preview |
|---:|---|---|---|---|---:|---|---|---|
| 1 | make a timer app | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\01-make-a-timer-app\workspace\index.html` |
| 2 | make a calculator app | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\02-make-a-calculator-app\workspace\index.html` |
| 3 | make dark theme switcher page | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\03-make-dark-theme-switcher-page\workspace\index.html` |
| 4 | make a todo list app | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\04-make-a-todo-list-app\workspace\index.html` |
| 5 | make a weather card demo | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\05-make-a-weather-card-demo\workspace\weather-card.html` |
| 6 | make a music player mockup | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\06-make-a-music-player-mockup\workspace\index.html` |
| 7 | make a habit tracker | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\07-make-a-habit-tracker\workspace\index.html` |
| 8 | make a notes app | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\08-make-a-notes-app\workspace\index.html` |
| 9 | make a password strength checker | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\09-make-a-password-strength-checker\workspace\index.html` |
| 10 | make a simple drawing pad | GO | disposable_small_file_bundle | static_ui_artifact | 3 | True | PASS | `Z:\docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\runs\10-make-a-simple-drawing-pad\workspace\drawing-pad.html` |

## Intent Inference Observations

- All prompts were inferred as Source Proxy `product` route runs with `disposable_small_file_bundle` task shape and `static_ui_artifact` class.
- The proxy allowed `.html`, `.css`, and `.js` and did not require exact allowed files for these blunt create prompts.
- File paths were model-authored rather than proxy-specified; generated names included `index.html`, `weather-card.html`, and `drawing-pad.html`.
- The notes prompt was treated as an app/UI artifact, not a markdown-only document, which matches the blunt "notes app" intent.

## Model Lane Observability Observations

- `selected_coder_lane` was `qwen_local_coder` for every run.
- `sidecar_lanes_considered` listed Hermes/Gemma preview lanes as metadata only.
- No verifier/sidecar live calls were made; browser probes here were deterministic diagnostic probes run after generation.
- Cartographer routing preview did not contribute to these product-path runs; current integration remains preview-only.

## File Creation And Bridge Observations

- Every run produced model-authored file actions that parsed and executed successfully.
- Every run created three files in the disposable workspace.
- File bytes matched model-authored content for every run.
- Backend-created content was not detected.
- Real app files were not touched.

## Context/Search/Local Intelligence Observations

- Web search was not used.
- Obsidian, repo search, Cartographer live routing, and external context intelligence were not used.
- Local Source Proxy intelligence came from task-shape inference, artifact class inference, behavior-contract metadata, allowed-extension policy, and model-lane observability metadata.
- No external URLs or remote resources were detected in generated workspaces.

## Usability Observations

- make a timer app: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"afterStart": "0:01\nResume Stop", "afterStop": "0:01\nStart Stop", "afterWait": "0:01\nStart Stop", "before": "00:00\nStart Stop"}`
- make a calculator app: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"bodyText": "7 8 9 = + 4 5 6 C - 1 2 3 * 0 . /", "displayIncludesFive": true}`
- make dark theme switcher page: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"after": {"bg": "rgb(51, 51, 51)", "cls": "dark-theme", "color": "rgb(255, 255, 255)"}, "before": {"bg": "rgb(255, 255, 255)", "cls": "light-theme", "color": "rgb(0, 0, 0)"}, "changed": true}`
- make a todo list app: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"after": "Todo List\n Add\nv0.2 proof itemRemove", "appears": true, "before": "Todo List\n Add", "changed": true, "filled": true}`
- make a weather card demo: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"bodyText": "City\n\nTemperature: 0\u00b0C\n\nCondition: Clear\n\nUpdate Weather", "buttonCount": 1, "changedAfterControl": false, "hasCity": true, "hasCondition": true, "hasTemp": true}`
- make a music player mockup: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"after": "Track Title\n\nArtist Name\n\nPause Skip", "before": "Track Title\n\nArtist Name\n\nPlay Skip", "changed": true, "clicked": "button"}`
- make a habit tracker: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"after": "Habit Tracker\n Add Habit\nv0.2 proof item", "appears": true, "before": "Habit Tracker\n Add Habit", "changed": true, "filled": true}`
- make a notes app: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"after": "Notes App\n Save Note\nv0.2 proof item", "appears": true, "before": "Notes App\n Save Note", "changed": true, "filled": true}`
- make a password strength checker: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"changed": true, "strong": "Password Strength Checker\n\nStrong", "weak": "Password Strength Checker\n\nWeak"}`
- make a simple drawing pad: PASS. Generic browser probe observed the requested interaction. Actual excerpt: `{"box": {"height": 154, "width": 304, "x": 488, "y": 323}, "canvas": true, "changed": true}`

## Browser Console And Runtime Errors

- No browser page errors or console error/warning messages were captured by the open probe.

## Failures Grouped By Root Cause

- No behavior-probe failures were observed in this 10-run diagnostic batch.
- Residual risk: these are generic probes, not a mature expectation scoring system. PASS here means the obvious interaction worked under the current deterministic probe, not that the artifact is polished or complete.

## Future Expectation Scoring Should Measure

- Intent fit: whether the artifact addresses the plain human request without overfitting to benchmark text.
- Entrypoint correctness: whether the selected preview path is valid without assuming `index.html`.
- Model authorship: whether paths and bytes came from model-authored actions rather than backend scaffolds.
- Main behavior proof: task-specific expected/actual/passed evidence, including calculator arithmetic like `2 + 3 = 5`.
- Usability depth: controls are discoverable, state changes are visible, reset/edit/delete flows work where expected, and mockups do not masquerade as functional apps.
- Runtime quality: browser console errors, missing linked assets, broken relative references, inaccessible controls, and layout-blocking issues.
- Context discipline: whether web/search/repo/Obsidian/Cartographer intelligence was used, and whether that use was justified and visible.
- Lane discipline: Qwen primary lane preserved, sidecars preview-only unless approved, no hidden model escalation.
- Safety boundaries: no real app mutation, no secret/env mutation, no provider/API route, no fake PASS.

## What Should Not Be Patched Narrowly

- Do not add prompt-string-specific branches for these 10 prompts.
- Do not add benchmark answer templates or hidden app snippets.
- Do not weaken browser/verifier logic just to preserve a clean PASS line.
- Do not fix generated artifacts manually after the model writes them.
- Do not activate Gemma/Hermes or cloud/API routes to rescue weak local outputs without a separate approval packet.

## Anti-Tailoring Follow-Up Prompt Bank

Ran `anti-tailoring-random-10.html` / `anti-tailoring-random-10.json` as a fresh challenge set on 2026-06-13. The prompts stay close to the original 10 simple human asks, but change nouns, wording, and typos to expose exact-prompt tailoring, hidden fallback scaffolds, scope misclassification, or hand-held benchmark behavior.

Fresh prompt set:

1. `make a kichen timer thing`
2. `build a tiny tip splittr`
3. `make a page that flips lite and night mode`
4. `make me a grocery checklist`
5. `make a fake forecast card`
6. `make a little podcast player mock`
7. `make a water drinking tracker`
8. `make a scratch notes app`
9. `make a password safety meter`
10. `make a doodle board`

Run rule followed: no generation prompt tuning, prompt-specific aliases/templates, generated artifact patching, sidecars, or cloud/API fallback. Raw prompt, route, transcript, parsed action/score, workspace diff, browser open result, and behavior probe evidence are preserved. PASS means behavior-proven main interaction, not just file creation or openable HTML.


Anti-tailoring run result: **NO-GO**.

- Behavior PASS: 4/10
- Behavior FAIL: 6/10
- Results page: `anti-tailoring-random-10.html`
- Results JSON: `anti-tailoring-random-10-results.json`
- Run receipt: `anti-tailoring-random-10-run-receipt.json`

| # | Prompt | Route | Open | Behavior | Preview / failure |
|---:|---|---|---|---|---|
| 1 | $(@{run=01-make-a-kichen-timer-thing; prompt=make a kichen timer thing; baseline_neighbor=make a timer app; expected_behavior=Start/stop or countdown/count-up timer visibly changes over time.; route_status=GO; canonical_final_verdict=UNVERIFIED; final_behavior_verdict=PASS; open_verdict=PASS; behavior_test=make a kichen timer thing-timer-change; behavior_expected=timer text changes after start; behavior_actual=; selected_preview_path=/home/source/SpiritOS/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-runs/01-make-a-kichen-timer-thing/workspace/index.html; preview_link=anti-tailoring-random-10-runs/01-make-a-kichen-timer-thing/workspace/index.html; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | GO | PASS | PASS | `anti-tailoring-random-10-runs/01-make-a-kichen-timer-thing/workspace/index.html` |
| 2 | $(@{run=02-build-a-tiny-tip-splittr; prompt=build a tiny tip splittr; baseline_neighbor=make a calculator app; expected_behavior=Entering bill/tip/people changes a visible per-person or total result.; route_status=EXPECTED-BLOCKED; canonical_final_verdict=BLOCKED; final_behavior_verdict=FAIL; open_verdict=FAIL; behavior_test=build a tiny tip splittr-missing-preview; behavior_expected=openable generated preview exists before behavior probe; behavior_actual=; selected_preview_path=; preview_link=; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | EXPECTED-BLOCKED | FAIL | FAIL | Action target is outside the allowed file snapshot. |
| 3 | $(@{run=03-make-a-page-that-flips-lite-and-night-mode; prompt=make a page that flips lite and night mode; baseline_neighbor=make dark theme switcher page; expected_behavior=A control visibly switches page colors or theme state.; route_status=GO; canonical_final_verdict=UNVERIFIED; final_behavior_verdict=PASS; open_verdict=PASS; behavior_test=make a page that flips lite and night mode-theme-computed-change; behavior_expected=computed color or theme class changes; behavior_actual=; selected_preview_path=/home/source/SpiritOS/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-runs/03-make-a-page-that-flips-lite-and-night-mode/workspace/index.html; preview_link=anti-tailoring-random-10-runs/03-make-a-page-that-flips-lite-and-night-mode/workspace/index.html; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | GO | PASS | PASS | `anti-tailoring-random-10-runs/03-make-a-page-that-flips-lite-and-night-mode/workspace/index.html` |
| 4 | $(@{run=04-make-me-a-grocery-checklist; prompt=make me a grocery checklist; baseline_neighbor=make a todo list app; expected_behavior=User can add at least one grocery item and see it persist in the list during the session.; route_status=GO; canonical_final_verdict=UNVERIFIED; final_behavior_verdict=FAIL; open_verdict=FAIL; behavior_test=make me a grocery checklist-missing-preview; behavior_expected=openable generated preview exists before behavior probe; behavior_actual=; selected_preview_path=; preview_link=; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | GO | FAIL | FAIL | behavior_required_but_unverified |
| 5 | $(@{run=05-make-a-fake-forecast-card; prompt=make a fake forecast card; baseline_neighbor=make a weather card demo; expected_behavior=Shows weather-like fields and any update/control changes visible forecast state or content.; route_status=GO; canonical_final_verdict=UNVERIFIED; final_behavior_verdict=PASS; open_verdict=PASS; behavior_test=make a fake forecast card-forecast-fields-or-update; behavior_expected=weather-like fields render and control changes content if present; behavior_actual=; selected_preview_path=/home/source/SpiritOS/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-runs/05-make-a-fake-forecast-card/workspace/forecast-card.html; preview_link=anti-tailoring-random-10-runs/05-make-a-fake-forecast-card/workspace/forecast-card.html; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | GO | PASS | PASS | `anti-tailoring-random-10-runs/05-make-a-fake-forecast-card/workspace/forecast-card.html` |
| 6 | $(@{run=06-make-a-little-podcast-player-mock; prompt=make a little podcast player mock; baseline_neighbor=make a music player mockup; expected_behavior=Visible play/pause or next control changes player state.; route_status=GO; canonical_final_verdict=UNVERIFIED; final_behavior_verdict=FAIL; open_verdict=PASS; behavior_test=make a little podcast player mock-player-control-change; behavior_expected=play/pause or player control visibly changes state; behavior_actual=; selected_preview_path=/home/source/SpiritOS/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-runs/06-make-a-little-podcast-player-mock/workspace/index.html; preview_link=anti-tailoring-random-10-runs/06-make-a-little-podcast-player-mock/workspace/index.html; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | GO | PASS | FAIL | `anti-tailoring-random-10-runs/06-make-a-little-podcast-player-mock/workspace/index.html` |
| 7 | $(@{run=07-make-a-water-drinking-tracker; prompt=make a water drinking tracker; baseline_neighbor=make a habit tracker; expected_behavior=User can add/increment/check off water progress and see state change.; route_status=GO; canonical_final_verdict=UNVERIFIED; final_behavior_verdict=PASS; open_verdict=PASS; behavior_test=make a water drinking tracker-click-tracker-state-change; behavior_expected=tracker control visibly changes progress state; behavior_actual=; selected_preview_path=/home/source/SpiritOS/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-runs/07-make-a-water-drinking-tracker/workspace/water_drinking_tracker.html; preview_link=anti-tailoring-random-10-runs/07-make-a-water-drinking-tracker/workspace/water_drinking_tracker.html; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | GO | PASS | PASS | `anti-tailoring-random-10-runs/07-make-a-water-drinking-tracker/workspace/water_drinking_tracker.html` |
| 8 | $(@{run=08-make-a-scratch-notes-app; prompt=make a scratch notes app; baseline_neighbor=make a notes app; expected_behavior=User can type and save/add a note, with visible note text after action.; route_status=GO; canonical_final_verdict=UNVERIFIED; final_behavior_verdict=FAIL; open_verdict=PASS; behavior_test=make a scratch notes app-visible-state-change; behavior_expected=entered text remains visible after action; behavior_actual=; selected_preview_path=/home/source/SpiritOS/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-runs/08-make-a-scratch-notes-app/workspace/index.html; preview_link=anti-tailoring-random-10-runs/08-make-a-scratch-notes-app/workspace/index.html; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | GO | PASS | FAIL | `anti-tailoring-random-10-runs/08-make-a-scratch-notes-app/workspace/index.html` |
| 9 | $(@{run=09-make-a-password-safety-meter; prompt=make a password safety meter; baseline_neighbor=make a password strength checker; expected_behavior=Typing weak vs stronger passwords changes a visible safety/strength label.; route_status=NO-GO; canonical_final_verdict=NEEDS_FIX; final_behavior_verdict=FAIL; open_verdict=FAIL; behavior_test=make a password safety meter-missing-preview; behavior_expected=openable generated preview exists before behavior probe; behavior_actual=; selected_preview_path=; preview_link=; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | NO-GO | FAIL | FAIL | Action target is required. |
| 10 | $(@{run=10-make-a-doodle-board; prompt=make a doodle board; baseline_neighbor=make a simple drawing pad; expected_behavior=Pointer/mouse input on a canvas or drawing area visibly marks the board.; route_status=EXPECTED-BLOCKED; canonical_final_verdict=BLOCKED; final_behavior_verdict=FAIL; open_verdict=FAIL; behavior_test=make a doodle board-missing-preview; behavior_expected=openable generated preview exists before behavior probe; behavior_actual=; selected_preview_path=; preview_link=; files_changed=System.Object[]; workspace_files=System.Object[]; final_reason_codes=System.Object[]; blocked_reasons=System.Object[]; anti_tailoring_flags=; evidence_links=}.prompt) | EXPECTED-BLOCKED | FAIL | FAIL | Action target is outside the allowed file snapshot. |


## Anti-Tailoring Patch Rerun Results

After the generic interactive disposable route patch and mocked tests, disposable local verification was rerun without prompt-specific templates or generated-artifact edits.

- Original random 10 before patch: 4/10 behavior PASS, 6/10 behavior FAIL, NO-GO.
- Random 10 rerun after patch: 7/10 behavior PASS, 3/10 behavior FAIL, NO-GO.
- Fresh random 10b after patch: 5/10 behavior PASS, 5/10 behavior FAIL, NO-GO.
- Threshold for GREEN was at least 8/10 behavior PASS per batch, so Level 3 remains NO-GO.

Rerun artifacts:

- nti-tailoring-random-10.html
- nti-tailoring-random-10-results.json
- nti-tailoring-random-10-run-receipt.json
- nti-tailoring-random-10b.html
- nti-tailoring-random-10b-results.json
- nti-tailoring-random-10b-run-receipt.json

Remaining failure buckets:

- Generated controls render but do not mutate visible state: forecast/weather, mini episode player, water counter.
- Generated notes app can save status without displaying typed note in one batch.
- Password meter can render visual meter chrome without visible weak/strong text in one batch.
- Some simple visual UI output is static despite the behavior contract.
## Recommended Next Phase

Build an expectation scoring layer on top of this evidence format. It should score intent fit, artifact entrypoint selection, model-authored file integrity, behavior proof strength, runtime quality, and lane/context discipline without patching individual prompt outputs. Keep Qwen as primary and keep Hermes/Gemma as preview-only until a separate verifier-lane preview test is approved.

## Raw Evidence

- `batch-run-receipt.json`: command/run receipt for all 10 prompts.
- `advanced-diagnostics.json`: consolidated advanced diagnostics for all runs.
- `browser-diagnostic-results.json`: open/console and behavior probe paths/results.
- `runs/*/receipt.json`, `score.json`, `transcript.txt`, `workspace.diff`: raw run evidence.
- `runs/*/browser-open-console.json` and `runs/*/behavior-probe.json`: browser diagnostics.



