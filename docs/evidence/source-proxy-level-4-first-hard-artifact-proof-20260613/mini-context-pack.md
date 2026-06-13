# Level 4 Mini Context Pack

Level 4 verdict: NO-GO

Level 3 accepted baseline: Gate B GO, 9/10 behavior PASS, threshold 8/10, one dusk/dawn theme behavior backlog item.

## Pass/Fail Table

- `level4-clean-01` timer/history: PASS (3/2 observations), route GO, failure ``
- `level4-clean-02` calculator/reset: PASS (2/2 observations), route GO, failure ``
- `level4-clean-03` theme/settings: FAIL (1/2 observations), route GO, failure `theme_text_size_no_visible_change`
- `level4-clean-04` checklist/progress: FAIL (1/2 observations), route GO, failure `checklist_toggle_or_count_no_change`
- `level4-clean-05` weather/dual-control: FAIL (1/2 observations), route GO, failure `weather_city_control_no_visible_change`
- `level4-clean-06` player/queue: PASS (2/2 observations), route GO, failure ``
- `level4-clean-07` tracker/totals: FAIL (0/2 observations), route GO, failure `tracker_add_set_no_visible_change`
- `level4-clean-08` notes/edit-delete: FAIL (0/2 observations), route EXPECTED-BLOCKED, failure `preview_resolution_failed`
- `level4-clean-09` password/show-hide: PASS (2/2 observations), route GO, failure ``
- `level4-clean-10` drawing/tools: PASS (2/2 observations), route GO, failure ``

## Integrity

Anti-tailoring: No exact prompt tailoring found in searched runtime/source scopes.
Anti-cheat: {"backend_created_content": false, "cloud_api_fallback_used": false, "deterministic_scaffold_used": false, "fallback_used": false, "false_negative_corrections": 0, "false_positive_corrections": 0, "final_verdict_logic_changes": "no", "level_4_probe_wrapper_changed_after_run": "no", "missing_behavior_evidence": false, "missing_transcript": false, "real_app_touched": false, "repair_attempts_used": 3, "report_verdict_mismatch": false, "score_integrity_failure": false, "scorer_changes": "no"}

## Model Lane Truth

Qwen: Qwen/local Source Proxy path requested via qwen2.5-coder:7b; transcripts and receipts preserved per run.
Gemma/Hermes: Not invoked as live verifier lanes unless a per-prompt trace explicitly proves otherwise.
Cartographer: Not invoked as live route owner; route traces are evidence sidecars.

## Files Written

- `__pycache__/build_level4_reports.cpython-313.pyc`
- `anti-cheat-integrity.md`
- `anti-tailoring-audit.md`
- `build_level4_reports.py`
- `index.md`
- `level-4-browser-behavior-results.json`
- `level-4-contract.md`
- `level-4-level3-before-repair-post-behavior-repair-summary.json`
- `level-4-level3-browser-behavior-results-before-repair.json`
- `level-4-level3-browser-behavior-results.json`
- `level-4-post-behavior-repair-summary.json`
- `level-4-prompt-set.json`
- `level-4-results.json`
- `level-4-run-receipt.json`
- `level-4-runner-results.json`
- `level-4-runner.html`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/behavior-probe.json`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/browser-open-console.json`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/generation-result.json`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/receipt.json`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/route_trace.json`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/score.json`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/transcript.txt`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/workspace.diff`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/workspace/laundry_timer.css`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/workspace/laundry_timer.html`
- `level-4-runs/01-make-a-laundry-timer-that-can-start-pause-reset-and-log-a-finished-load/workspace/laundry_timer.js`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/behavior-probe.json`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/browser-open-console.json`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/generation-result.json`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/receipt.json`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/route_trace.json`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/score.json`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/transcript.txt`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/workspace.diff`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/workspace/index.html`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/workspace/script.js`
- `level-4-runs/02-make-a-parking-trip-cost-planner-with-fee-people-tip-and-a-reset-button/workspace/styles.css`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/behavior-failure-packet.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/behavior-probe-before-repair.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/behavior-probe.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/browser-open-console.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/generation-result.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/post-behavior-repair-result.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/receipt.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/route_trace.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/score.json`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/transcript.txt`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/workspace.diff`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/workspace/index.html`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/workspace/script.js`
- `level-4-runs/03-make-a-dusk-dawn-reading-panel-with-a-palette-switch-and-text-size-control/workspace/styles.css`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/behavior-probe.json`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/browser-open-console.json`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/generation-result.json`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/receipt.json`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/route_trace.json`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/score.json`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/transcript.txt`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/workspace.diff`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/workspace/index.html`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/workspace/script.js`
- `level-4-runs/04-make-a-beach-packing-board-where-i-can-add-items-check-them-off-and-see-packed-c/workspace/styles.css`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/behavior-failure-packet.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/behavior-probe-before-repair.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/behavior-probe.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/browser-open-console.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/generation-result.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/post-behavior-repair-result.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/receipt.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/route_trace.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/score.json`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/transcript.txt`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/workspace.diff`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/workspace/index.html`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/workspace/script.js`
- `level-4-runs/05-make-a-balcony-forecast-tile-with-a-city-switch-and-f-c-temp-toggle/workspace/styles.css`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/behavior-probe.json`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/browser-open-console.json`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/generation-result.json`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/receipt.json`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/route_trace.json`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/score.json`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/transcript.txt`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/workspace.diff`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/workspace/index.html`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/workspace/script.js`
- `level-4-runs/06-make-a-campfire-podcast-queue-with-play-pause-and-next-episode/workspace/styles.css`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/behavior-failure-packet.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/behavior-probe-before-repair.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/behavior-probe.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/browser-open-console.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/generation-result.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/post-behavior-repair-result.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/receipt.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/route_trace.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/score.json`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/transcript.txt`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/workspace.diff`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/workspace/stair_tracker.css`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/workspace/stair_tracker.html`
- `level-4-runs/07-make-a-stair-workout-tracker-where-i-can-add-a-set-increase-reps-and-see-total-s/workspace/stair_tracker.js`
- `level-4-runs/08-make-a-sticky-memo-board-where-i-can-add-a-thought-edit-it-delete-it-and-see-sav/behavior-probe.json`
- `level-4-runs/08-make-a-sticky-memo-board-where-i-can-add-a-thought-edit-it-delete-it-and-see-sav/browser-open-console.json`
- `level-4-runs/08-make-a-sticky-memo-board-where-i-can-add-a-thought-edit-it-delete-it-and-see-sav/generation-result.json`
- `level-4-runs/08-make-a-sticky-memo-board-where-i-can-add-a-thought-edit-it-delete-it-and-see-sav/receipt.json`
- `level-4-runs/08-make-a-sticky-memo-board-where-i-can-add-a-thought-edit-it-delete-it-and-see-sav/route_trace.json`
- `level-4-runs/08-make-a-sticky-memo-board-where-i-can-add-a-thought-edit-it-delete-it-and-see-sav/score.json`
- `level-4-runs/08-make-a-sticky-memo-board-where-i-can-add-a-thought-edit-it-delete-it-and-see-sav/transcript.txt`
- `level-4-runs/08-make-a-sticky-memo-board-where-i-can-add-a-thought-edit-it-delete-it-and-see-sav/workspace.diff`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/behavior-probe.json`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/browser-open-console.json`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/generation-result.json`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/receipt.json`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/route_trace.json`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/score.json`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/transcript.txt`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/workspace.diff`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/workspace/index.html`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/workspace/script.js`
- `level-4-runs/09-make-a-secret-phrase-safety-lab-with-strength-feedback-and-a-show-hide-switch/workspace/styles.css`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/behavior-probe.json`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/browser-open-console.json`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/generation-result.json`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/receipt.json`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/route_trace.json`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/score.json`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/transcript.txt`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/workspace.diff`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/workspace/index.html`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/workspace/script.js`
- `level-4-runs/10-make-a-finger-paint-pad-with-color-choice-brush-size-draw-and-clear/workspace/styles.css`
- `level-4.html`
- `level4_behavior_probe.mjs`
- `mini-context-pack.json`
- `mini-context-pack.md`
- `mini-context-pack.xml`
- `per-prompt-traces/level4-clean-01.json`
- `per-prompt-traces/level4-clean-01.md`
- `per-prompt-traces/level4-clean-02.json`
- `per-prompt-traces/level4-clean-02.md`
- `per-prompt-traces/level4-clean-03.json`
- `per-prompt-traces/level4-clean-03.md`
- `per-prompt-traces/level4-clean-04.json`
- `per-prompt-traces/level4-clean-04.md`
- `per-prompt-traces/level4-clean-05.json`
- `per-prompt-traces/level4-clean-05.md`
- `per-prompt-traces/level4-clean-06.json`
- `per-prompt-traces/level4-clean-06.md`
- `per-prompt-traces/level4-clean-07.json`
- `per-prompt-traces/level4-clean-07.md`
- `per-prompt-traces/level4-clean-08.json`
- `per-prompt-traces/level4-clean-08.md`
- `per-prompt-traces/level4-clean-09.json`
- `per-prompt-traces/level4-clean-09.md`
- `per-prompt-traces/level4-clean-10.json`
- `per-prompt-traces/level4-clean-10.md`
- `probe-capability-audit.md`
- `prompt-lock-receipt.md`
- `remaining-failures.md`
- `terminal-verification.md`
- `transparent-proxy-trace-index.md`

## Commands Run

- `git status --branch --short --untracked-files=normal`
- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json`
- `node --check docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs`
- `python -m py_compile docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py`
- `python Z:/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py --prompt-file Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json --run-root Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runs --title "Source Proxy Level 4 first hard artifact complexity proof locked 10" --results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runner-results.json --html Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runner.html --run-receipt Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-run-receipt.json --browser-results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-level3-browser-behavior-results.json --repair-summary Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b`
- `node docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runs Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-browser-behavior-results.json Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/per-prompt-traces`
- `python docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py ...`
- `rg --fixed-strings for locked Level 4 prompt strings and prompt ids across source_proxy, src, scripts/agent-trials, source-proxy scripts, and config`
- `rg --fixed-strings for old Level 3 strings, prompt equality markers, scaffold/rescue/cloud fallback markers across source_proxy, src, scripts/agent-trials, source-proxy scripts, and config`
- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-results.json`
- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-browser-behavior-results.json`
- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/mini-context-pack.json`
- `python -c "import xml.etree.ElementTree as ET; ET.parse('docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/mini-context-pack.xml')"`
- `Get-ChildItem docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/per-prompt-traces/*.json | ForEach-Object { python -m json.tool $_.FullName }`
- `python -m py_compile docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py`
- `node --check docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs`
- `link audit for level-4.html evidence hrefs`
- `git diff --check -- docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613`
- `git status --branch --short --untracked-files=normal`

Runtime source code changed: False
Level 4 evidence-only probe wrapper created: True
Next recommended step: Review Level 4 failures without starting Level 5; decide whether to repair instrumentation or runtime in a separately approved pass.
Upload next: `docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/mini-context-pack.md`
