# Implementation Gate B Plan

This is a review plan only. It is not an implementation prompt.

## Likely Source Files To Touch

- `source_proxy/decision/task_spec_intake.py`
- `source_proxy/decision/artifact_behavior_contract.py`
- `source_proxy/decision/human_messy_homepage.py`
- `source_proxy/decision/artifact_repair_contract.py`
- Possibly `source_proxy/decision/artifact_repair_loop.py` if repair trace metadata needs to be carried into result records.
- Evidence/report code that emits per-prompt traces or optional route trace sidecars.

## Likely Test Files To Touch Or Add

- `source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- `source_proxy/tests/test_artifact_behavior_contract.py`
- `source_proxy/tests/test_artifact_repair_contract.py`
- `source_proxy/tests/test_artifact_repair_loop.py`
- Optional new test file: `source_proxy/tests/test_task_spec_intake_semantic_generalization.py`

## Positive Synonym Tests

Add intake and behavior-contract tests for:

- cost sharer
- parking cost splitter
- garage cost sharer
- split parking fee tool
- share a garage bill widget
- make something that splits parking costs
- palette switch
- dusk dawn switch
- theme palette flipper
- sunrise sunset mode switch
- make the screen change when it gets dark
- color mood switcher
- phrase strength gauge
- secret phrase meter
- passphrase strength checker
- login phrase safety gauge
- show me how strong this passphrase is, if the team agrees this should count as a create request
- password safety meter

Expected positive result: disposable static UI artifact with behavior probe family selected.

## Negative Route-Control Tests

Add regression tests that stay real-repo clarification or explicit-target scoped:

- add a parking cost sharer to the existing dashboard
- update the login safety gauge component in src
- modify the production theme switcher
- fix the existing drawing canvas bug in the repo
- change the real weather tile in the app
- edit src/components/ThemeSwitcher.tsx to use dawn colors
- update the existing password meter test file
- repair the dashboard's forecast tile component
- modify the app's real billing splitter route

Expected negative result: do not force disposable workspace merely because family terms are present.

## Weather Generation Requirement

Add a weather-family implementation checklist keyed by `weather-card-fields`:

If a weather/forecast artifact includes a local demo control, that control must mutate visible DOM text such as city, temperature, condition, forecast, or status.

## Drawing Generation Requirement

Strengthen the drawing-family checklist keyed by `drawing-surface-changes`:

For drawing/canvas/sketch artifacts, prefer a real canvas element with pointer/mouse handlers that mutate visible pixels. Keep canvas ids and JS selectors consistent. Do not clear marks on mouseup unless there is a separate clear control.

## Repair Template Upgrade

Revise `build_repair_prompt_from_failure_packet()` to include structured fields:

- artifact_family
- original_prompt
- selected_preview_path
- allowed_files
- failed_probe_id
- expected_behavior
- primary_failure_bucket
- observed_before
- observed_after
- observed_interaction
- why_this_failed
- current_files_summary
- required_repair
- required_output_format

Require path-bound WriteFile JSON or `<file path="...">` output only.

## Trace Instrumentation Upgrade

Add route trace sidecars or per-prompt trace fields for:

- normalized prompt
- family candidates/reasons
- standalone artifact signals
- real repo signals
- explicit target detection
- disposable candidate boolean
- route decision reason
- blocking reason
- why no preview if blocked

Do not mutate stable behavior-probe, score, or receipt schemas.

## Final Holdout Rerun Path

After Gate B implementation and focused tests pass, rerun only the existing final clean similar 10 holdout using the locked prompt set and existing evidence harness. Do not create a new prompt batch.

Expected rerun evidence folder should be separate from Gate A and Gate B implementation evidence.

## Evidence Outputs Required After Gate B

- changed-files.md
- focused-test-output.md
- route-trace-sample.json or equivalent trace proof
- final-clean-similar-10-rerun-results.json
- final-clean-similar-10-rerun-summary.md
- anti-tailoring-audit.md
- anti-cheat-integrity.md
- terminal-verification.md
- mini-context-pack.md
- mini-context-pack.xml
- mini-context-pack.json

## Mini Context Pack Requirements After Gate B

The Gate B mini context pack must include:

- exact source files changed
- exact tests added/changed
- focused test results
- final clean similar 10 rerun result
- anti-tailoring status
- anti-cheat status
- whether browser/model calls occurred
- whether Level 4 or new batches were avoided
- upload guidance for Britton

## Stop Condition

Stop after focused implementation, focused tests, and rerunning the existing final clean similar 10 holdout. Do not start Level 4. Do not create new batches. Do not patch scorer green. Do not add exact prompt branches. Do not use cloud fallback. Do not add backend rescue content. Do not add hidden deterministic scaffold.
