# Self-contained Source Proxy ChatGPT mini context pack

- Date/time: 2026-06-13T15:43:57.991952+00:00
- Repo path: `Z:/`
- Evidence folders summarized: `docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613`, `docs/evidence/source-proxy-level-3-failure-family-stabilization-20260613`
- Current phase name: Level 3 semantic intake and behavior generalization review
- Current verdict: NO-GO

## One-Screen Executive Summary

- current grade recommendation: Do not accept Level 3 as GO; keep Level 3 NEEDS-FIX/NO-GO until fresh similar wording clears at least 8/10.
- level 3 status: NO-GO for final acceptance: fresh similar holdout reached 5/10 behavior PASS against an 8/10 threshold.
- why not final go: Locked 10d/10e reruns went green after stabilization, but fresh nearby wording exposed route/intake brittleness and two behavior/repair failures.
- cheated or tailored: No exact prompt tailoring found in the searched source/runtime scopes.
- failure clean honest: Yes. The run recorded failures as FAIL/NO-GO with no score warnings, false-positive corrections, fallback, scaffold, backend-authored rescue, cloud fallback, or real app mutation.
- best next step: Level 3 semantic intake and behavior generalization repair, no new batches.
- what not to do next: Do not proceed to Level 4, scale batch size, hard-code failed prompts, patch the scorer green, or claim inactive lanes are active.

## Timeline Of Recent Evidence

| event | behavior | threshold | verdict | prompt set | scope | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 10d before stabilization | 5/10 behavior PASS, 5 FAIL | 8/10 | NO-GO before stabilization | old locked 10d | pre-stabilization evidence | `docs/evidence/source-proxy-level-3-failure-family-stabilization-20260613/index.md` |
| 10e before stabilization | 6/10 behavior PASS, 4 FAIL | 8/10 | NO-GO before stabilization | old locked 10e | pre-stabilization evidence | `docs/evidence/source-proxy-level-3-failure-family-stabilization-20260613/index.md` |
| failure-family stabilization rerun | 10d 10/10 PASS; 10e 10/10 PASS | 8/10 | GO on locked reruns | old locked 10d/10e | source patches had happened in prior stabilization work; no new large batch | `docs/evidence/source-proxy-level-3-failure-family-stabilization-20260613/` |
| evidence consistency audit | anti-cheat clean; remaining locked failures none | not a behavior batch | clean evidence for locked stabilization | locked 10d/10e evidence | reporting/evidence review | `docs/evidence/source-proxy-level-3-failure-family-stabilization-20260613/anti-cheat-integrity.md` |
| final clean similar 10 | 5/10 behavior PASS, 5 FAIL | 8/10 | NO-GO | fresh similar 10 locked before run | evidence-only final proof; no fixes after seeing prompt set | `docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/` |

## Current Final Proof Result Table

| id | prompt | family | route | open | raw | strict | result | bucket | repairs | model | preview | before | after | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| final-l3-clean-01 | make a laundry flip countdown | timer/countdown | GO | PASS | PASS | PASS | PASS |  | 0 | qwen2.5-coder:7b | `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\01-make-a-laundry-flip-countdown\workspace\index.html` | 60 Start Stop Reset | 59 Start Stop Reset | Behavior proof passed cleanly. |
| final-l3-clean-02 | make a parking garage cost sharer | calculator/splitter | EXPECTED-BLOCKED | FAIL | FAIL | FAIL | FAIL | route_blocked_no_preview | 0 | qwen2.5-coder:7b | `NO_PREVIEW` | NO_PREVIEW | NOT_RECORDED | Semantic intake/router did not treat this as disposable browser artifact, so no preview behavior proof was possible. |
| final-l3-clean-03 | make a dusk dawn palette switch | theme/mode toggle | EXPECTED-BLOCKED | FAIL | FAIL | FAIL | FAIL | route_blocked_no_preview | 0 | qwen2.5-coder:7b | `NO_PREVIEW` | NO_PREVIEW | NOT_RECORDED | Semantic intake/router did not treat this as disposable browser artifact, so no preview behavior proof was possible. |
| final-l3-clean-04 | make a beach bag checklist app | checklist/list | GO | PASS | PASS | PASS | PASS |  | 0 | qwen2.5-coder:7b | `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\04-make-a-beach-bag-checklist-app\workspace\index.html` | Beach Bag Checklist  Add Item | Beach Bag Checklist  Add Item bananas | Behavior proof passed cleanly. |
| final-l3-clean-05 | make a pretend balcony forecast tile | weather/forecast/tile | GO | PASS | FAIL | FAIL | FAIL | weather_static_when_update_expected | 1 | qwen2.5-coder:7b | `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\05-make-a-pretend-balcony-forecast-tile\workspace\index.html` | City: San Francisco  Temperature: 68°F  Condition: Sunny  Change Weather to New York | City: San Francisco  Temperature: 68°F  Condition: Sunny  Change Weather to New York | Preview opened, repair ran, but final browser behavior remained failing. |
| final-l3-clean-06 | make a campfire podcast mini player | player/radio/audio | GO | PASS | PASS | PASS | PASS |  | 0 | qwen2.5-coder:7b | `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\06-make-a-campfire-podcast-mini-player\workspace\index.html` | Track Title Play Skip | Track Title Pause Skip | Behavior proof passed cleanly. |
| final-l3-clean-07 | make a stair step tally counter | counter/tracker | GO | PASS | PASS | PASS | PASS |  | 0 | qwen2.5-coder:7b | `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\07-make-a-stair-step-tally-counter\workspace\index.html` | 0 Increment | 1 Increment | Behavior proof passed cleanly. |
| final-l3-clean-08 | make a sticky thought memo board | notes/memo | GO | PASS | PASS | PASS | PASS |  | 0 | qwen2.5-coder:7b | `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\08-make-a-sticky-thought-memo-board\workspace\index.html` |  Add Memo | scratch proof note  Add Memo | Behavior proof passed cleanly. |
| final-l3-clean-09 | make a secret phrase strength gauge | password/passphrase strength | EXPECTED-BLOCKED | FAIL | FAIL | FAIL | FAIL | route_blocked_no_preview | 0 | qwen2.5-coder:7b | `NO_PREVIEW` | NO_PREVIEW | NOT_RECORDED | Semantic intake/router did not treat this as disposable browser artifact, so no preview behavior proof was possible. |
| final-l3-clean-10 | make a finger paint doodle pad | drawing/canvas/sketch | GO | PASS | FAIL | FAIL | FAIL | drawing_canvas_no_pixel_change | 1 | qwen2.5-coder:7b | `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\10-make-a-finger-paint-doodle-pad\workspace\index.html` | NOT_RECORDED | NOT_RECORDED | Preview opened, repair ran, but final browser behavior remained failing. |

## Failed Prompt Deep Dive

### final-l3-clean-02 - make a parking garage cost sharer

- expected behavior: Entered cost/share values visibly change a calculated result.
- inferred family: calculator/splitter
- normalized intent: clarification_required_real_repo_implementation
- route decision: EXPECTED-BLOCKED
- selected preview path: `NO_PREVIEW`
- route blocked before model/app proof: True
- behavior contract/probe id: "calculator-derived-total"
- observed before: {"reason": "behavior probe did not record before", "value": "NOT_RECORDED"}
- observed after: {"reason": "behavior probe did not record a standard after value", "value": "NOT_RECORDED"}
- primary failure bucket: route_blocked_no_preview
- secondary failure bucket: none
- repair ran: False
- repair result: SKIPPED
- model transcript path: `final-clean-similar-10-runs/02-make-a-parking-garage-cost-sharer/transcript.txt`
- behavior probe path: `final-clean-similar-10-runs/02-make-a-parking-garage-cost-sharer/behavior-probe.json`
- score path: `final-clean-similar-10-runs/02-make-a-parking-garage-cost-sharer/score.json`
- receipt path: `final-clean-similar-10-runs/02-make-a-parking-garage-cost-sharer/receipt.json`
- workspace diff path: `final-clean-similar-10-runs/02-make-a-parking-garage-cost-sharer/workspace.diff`
- likely root cause: Intake/router treated cost sharer as target-unresolved real repo work instead of disposable calculator artifact.
- issue type: route/intake
- exact files Codex should inspect next: `source_proxy/decision/task_spec_intake.py`, `source_proxy/decision/human_messy_homepage.py`, `source_proxy/decision/artifact_behavior_contract.py`, `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`

### final-l3-clean-03 - make a dusk dawn palette switch

- expected behavior: A control visibly changes theme, palette, color, class, or computed body colors.
- inferred family: theme/mode toggle
- normalized intent: clarification_required_real_repo_implementation
- route decision: EXPECTED-BLOCKED
- selected preview path: `NO_PREVIEW`
- route blocked before model/app proof: True
- behavior contract/probe id: {"reason": "behavior contract did not record a probe target", "value": "NOT_RECORDED"}
- observed before: {"reason": "behavior probe did not record before", "value": "NOT_RECORDED"}
- observed after: {"reason": "behavior probe did not record a standard after value", "value": "NOT_RECORDED"}
- primary failure bucket: route_blocked_no_preview
- secondary failure bucket: none
- repair ran: False
- repair result: SKIPPED
- model transcript path: `final-clean-similar-10-runs/03-make-a-dusk-dawn-palette-switch/transcript.txt`
- behavior probe path: `final-clean-similar-10-runs/03-make-a-dusk-dawn-palette-switch/behavior-probe.json`
- score path: `final-clean-similar-10-runs/03-make-a-dusk-dawn-palette-switch/score.json`
- receipt path: `final-clean-similar-10-runs/03-make-a-dusk-dawn-palette-switch/receipt.json`
- workspace diff path: `final-clean-similar-10-runs/03-make-a-dusk-dawn-palette-switch/workspace.diff`
- likely root cause: Intake/router treated palette switch as target-unresolved real repo work; probe id was not recorded on the blocked path.
- issue type: route/intake
- exact files Codex should inspect next: `source_proxy/decision/task_spec_intake.py`, `source_proxy/decision/human_messy_homepage.py`, `source_proxy/decision/artifact_behavior_contract.py`, `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`

### final-l3-clean-05 - make a pretend balcony forecast tile

- expected behavior: Weather-like fields are visible, and any provided local demo control changes forecast/weather state.
- inferred family: weather/forecast/tile
- normalized intent: disposable_small_file_bundle
- route decision: GO
- selected preview path: `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\05-make-a-pretend-balcony-forecast-tile\workspace\index.html`
- route blocked before model/app proof: False
- behavior contract/probe id: "weather-card-fields"
- observed before: City: San Francisco  Temperature: 68°F  Condition: Sunny  Change Weather to New York
- observed after: City: San Francisco  Temperature: 68°F  Condition: Sunny  Change Weather to New York
- primary failure bucket: weather_static_when_update_expected
- secondary failure bucket: none
- repair ran: True
- repair result: READY_FOR_RETEST
- model transcript path: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/transcript.txt`
- behavior probe path: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/behavior-probe.json`
- score path: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/score.json`
- receipt path: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/receipt.json`
- workspace diff path: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/workspace.diff`
- likely root cause: Generated forecast preview opened, but click did not change DOM; repair wrote files but still left observed text unchanged.
- issue type: repair
- exact files Codex should inspect next: `source_proxy/decision/task_spec_intake.py`, `source_proxy/decision/human_messy_homepage.py`, `source_proxy/decision/artifact_behavior_contract.py`, `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`, `source_proxy/decision/artifact_repair_loop.py`, `source_proxy/decision/artifact_repair_contract.py`

### final-l3-clean-09 - make a secret phrase strength gauge

- expected behavior: Weak and stronger phrase inputs visibly change strength feedback.
- inferred family: password/passphrase strength
- normalized intent: clarification_required_real_repo_implementation
- route decision: EXPECTED-BLOCKED
- selected preview path: `NO_PREVIEW`
- route blocked before model/app proof: True
- behavior contract/probe id: "password-strength-feedback-change"
- observed before: {"reason": "behavior probe did not record before", "value": "NOT_RECORDED"}
- observed after: {"reason": "behavior probe did not record a standard after value", "value": "NOT_RECORDED"}
- primary failure bucket: route_blocked_no_preview
- secondary failure bucket: none
- repair ran: False
- repair result: SKIPPED
- model transcript path: `final-clean-similar-10-runs/09-make-a-secret-phrase-strength-gauge/transcript.txt`
- behavior probe path: `final-clean-similar-10-runs/09-make-a-secret-phrase-strength-gauge/behavior-probe.json`
- score path: `final-clean-similar-10-runs/09-make-a-secret-phrase-strength-gauge/score.json`
- receipt path: `final-clean-similar-10-runs/09-make-a-secret-phrase-strength-gauge/receipt.json`
- workspace diff path: `final-clean-similar-10-runs/09-make-a-secret-phrase-strength-gauge/workspace.diff`
- likely root cause: Intake/router treated secret phrase strength gauge as target-unresolved real repo component work instead of disposable password/passphrase artifact.
- issue type: route/intake
- exact files Codex should inspect next: `source_proxy/decision/task_spec_intake.py`, `source_proxy/decision/human_messy_homepage.py`, `source_proxy/decision/artifact_behavior_contract.py`, `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`

### final-l3-clean-10 - make a finger paint doodle pad

- expected behavior: Pointer or mouse interaction visibly marks the drawing surface, canvas, or equivalent sketch area.
- inferred family: drawing/canvas/sketch
- normalized intent: disposable_small_file_bundle
- route decision: GO
- selected preview path: `\\10.0.0.186\SpiritOS\docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-clean-similar-10-runs\10-make-a-finger-paint-doodle-pad\workspace\index.html`
- route blocked before model/app proof: False
- behavior contract/probe id: "drawing-surface-changes"
- observed before: {"reason": "behavior probe did not record before", "value": "NOT_RECORDED"}
- observed after: {"reason": "behavior probe did not record a standard after value", "value": "NOT_RECORDED"}
- primary failure bucket: drawing_canvas_no_pixel_change
- secondary failure bucket: none
- repair ran: True
- repair result: READY_FOR_RETEST
- model transcript path: `final-clean-similar-10-runs/10-make-a-finger-paint-doodle-pad/transcript.txt`
- behavior probe path: `final-clean-similar-10-runs/10-make-a-finger-paint-doodle-pad/behavior-probe.json`
- score path: `final-clean-similar-10-runs/10-make-a-finger-paint-doodle-pad/score.json`
- receipt path: `final-clean-similar-10-runs/10-make-a-finger-paint-doodle-pad/receipt.json`
- workspace diff path: `final-clean-similar-10-runs/10-make-a-finger-paint-doodle-pad/workspace.diff`
- likely root cause: Canvas preview opened, but pointer/mouse interaction did not mutate pixels; repair changed markup but not working drawing behavior.
- issue type: repair
- exact files Codex should inspect next: `source_proxy/decision/task_spec_intake.py`, `source_proxy/decision/human_messy_homepage.py`, `source_proxy/decision/artifact_behavior_contract.py`, `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`, `source_proxy/decision/artifact_repair_loop.py`, `source_proxy/decision/artifact_repair_contract.py`, `source_proxy/decision/artifact_final_verdict.py`

## Passed Prompt Compact Summary

- final-l3-clean-01 (timer/countdown): `make a laundry flip countdown` passed; observed before=60 Start Stop Reset; afterStart=59 Start Stop Reset. Shows this family can still produce an interactive disposable artifact under fresh nearby wording. Evidence: `per-prompt-traces/final-l3-clean-01.json`
- final-l3-clean-04 (checklist/list): `make a beach bag checklist app` passed; observed appears=True. Shows this family can still produce an interactive disposable artifact under fresh nearby wording. Evidence: `per-prompt-traces/final-l3-clean-04.json`
- final-l3-clean-06 (player/radio/audio): `make a campfire podcast mini player` passed; observed before=Track Title Play Skip; after=Track Title Pause Skip. Shows this family can still produce an interactive disposable artifact under fresh nearby wording. Evidence: `per-prompt-traces/final-l3-clean-06.json`
- final-l3-clean-07 (counter/tracker): `make a stair step tally counter` passed; observed before=0 Increment; after=1 Increment. Shows this family can still produce an interactive disposable artifact under fresh nearby wording. Evidence: `per-prompt-traces/final-l3-clean-07.json`
- final-l3-clean-08 (notes/memo): `make a sticky thought memo board` passed; observed appears=True. Shows this family can still produce an interactive disposable artifact under fresh nearby wording. Evidence: `per-prompt-traces/final-l3-clean-08.json`

## Failure Pattern Diagnosis

- route intake generalization failures: ['final-l3-clean-02', 'final-l3-clean-03', 'final-l3-clean-09']
- behavior generation failures: ['final-l3-clean-05', 'final-l3-clean-10']
- possible probe instrumentation ambiguity: ['final-l3-clean-03 has NOT_RECORDED probe id in trace because the blocked route did not record a probe target']
- repair loop limitations: ['final-l3-clean-05 repair wrote model-authored files but behavior stayed static', 'final-l3-clean-10 repair kept canvas visible but pixels did not change']
- main diagnosis: The system appears clean but keyword-brittle. It handled some known-family wording but failed fresh nearby synonyms like cost sharer, palette switch, secret phrase gauge, and finger paint doodle pad.

## Anti-Tailoring Audit Summary

- summary: No exact new prompt tailoring found in searched source/runtime scopes; new prompt strings exist only in this evidence folder.
- searched paths: ['source_proxy/', 'src/', 'apps/', 'scripts/', 'docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613', 'batch runner scripts under docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/']
- exact prompt string search result: No runtime/source/runner matches before or after run; evidence-folder matches expected after lock/run.
- prompt id search result: No runtime/source/runner matches before run; evidence-folder matches expected.
- old 10d 10e string search result: No matches in runtime decision/app/script scopes; YES in tests as historical regression fixtures.
- runtime source result: No exact prompt tailoring found in the searched source/runtime scopes.
- evidence only result: New prompt strings and ids are present in prompt lock, receipts, transcripts, scores, traces, and reports as expected evidence.
- suspicious branch search result: NO exact prompt branches found.
- canned artifact output search result: NO exact new prompt-coupled canned outputs found.
- backend authored rescue content result: NO
- deterministic scaffold result: NO
- fallback result: NO
- cloud fallback result: NO
- real app touch result: NO

Required exact claim: No exact prompt tailoring found in the searched source/runtime scopes.
Do not claim: Prompt tailoring does not exist anywhere.

## Anti-Cheat Integrity Summary

- backend_created_content: False
- cloud_api_fallback_used: False
- deterministic_scaffold_used: False
- fallback_used: False
- false_negative_corrections: 0
- false_positive_corrections: 0
- missing_behavior_evidence: False
- missing_transcript: False
- real_app_touched: False
- repair_attempts_used: 2
- report_verdict_mismatch: False
- score_integrity_failure: False

## Full Proxy Process Summary

Observed pipeline:
human prompt -> task intake -> intent/family inference -> route decision -> context packet -> model lane decision -> Qwen invocation -> model output -> action/file-block parse -> sandbox writes -> preview selection -> browser behavior probe -> repair if needed -> final verdict -> anti-cheat audit

- Real steps: task intake, behavior contract, Qwen invocation, tool-action parsing, disposable workspace writes or blocked execution, browser probe, limited repair on eligible failures, strict final verdict
- Preview-only steps: Gemma sidecar context/verifier, Hermes sidecar verifier, Cartographer routing ownership

## Model Lane Summary

- qwen status: INVOKED for all 10 prompts via qwen2.5-coder:7b
- gemma status: NOT_INVOKED / PREVIEW_ONLY; no Gemma transcript exists.
- hermes status: NOT_INVOKED / PREVIEW_ONLY; no Hermes verifier transcript exists.
- cartographer routing status: PREVIEW_ONLY metadata/status only; no live Cartographer route ownership invocation recorded.
- verifier lane: NOT active unless a real transcript/log exists; this pack found none.

## Source Files Likely Relevant Next

- task spec intake: `source_proxy/decision/task_spec_intake.py` (likely relevant)
- disposable artifact routing: `source_proxy/decision/human_messy_homepage.py` (likely relevant)
- behavior contract: `source_proxy/decision/artifact_behavior_contract.py` (likely relevant)
- final verdict/scoring: `source_proxy/decision/artifact_final_verdict.py` (likely relevant)
- repair loop: `source_proxy/decision/artifact_repair_loop.py` (likely relevant)
- repair contract: `source_proxy/decision/artifact_repair_contract.py` (likely relevant)
- model lane registry: `source_proxy/decision/model_lanes.py` (likely relevant)
- verifier lane: `source_proxy/decision/verifier_lane.py` (likely relevant)
- Cartographer routing preview: `source_proxy/decision/cartographer_routing.py` (likely relevant)
- anti-tailoring runner: `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py` (likely relevant)
- behavior probe: `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs` (likely relevant)

## Suggested Next Action, But Not A Prompt

- recommended next task name: Level 3 semantic intake and behavior generalization repair, no new batches.
- goal: Fix semantic intake/router coverage and behavior-generation/repair robustness for the observed failure families without hard-coding the five failed prompts.
- non negotiables: ['no Level 4', 'no new batches', 'no scorer-only green', 'no exact prompt branches', 'no cloud fallback']
- likely files to inspect: ['source_proxy/decision/task_spec_intake.py', 'source_proxy/decision/human_messy_homepage.py', 'source_proxy/decision/artifact_behavior_contract.py', 'source_proxy/decision/artifact_final_verdict.py', 'source_proxy/decision/artifact_repair_loop.py', 'source_proxy/decision/artifact_repair_contract.py', 'source_proxy/decision/model_lanes.py', 'source_proxy/decision/verifier_lane.py', 'source_proxy/decision/cartographer_routing.py', 'docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py', 'docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs']
- expected evidence: ['focused unit tests for synonym intake', 'targeted behavior-contract/repair tests', 'rerun only the existing final clean 10 after fixes are approved']
- stop condition: Stop after a focused repair plan/evidence gate; do not write the next implementation prompt in this pack.

## What Not To Do Next

- Do not proceed to Level 4
- Do not create 25/50/100 batches
- Do not patch scorer to green
- Do not hard-code the five failed prompts
- Do not activate cloud fallback to hide local weakness
- Do not claim Gemma/Cartographer are active until transcripts prove it
- Do not accept Level 3 GO until a fresh similar holdout passes

## Upload Guidance For Britton

- Upload `docs/evidence/source-proxy-chatgpt-mini-context-pack-20260613/source-proxy-chatgpt-context-pack.md` first.
- Only upload extra files if ChatGPT asks.
- Extra useful files if needed:
  - `source-proxy-chatgpt-context-pack.json`
  - `source-proxy-chatgpt-context-pack.xml`
  - `final-proof-results.json`
  - `failing per-prompt trace JSONs`

## Context Sufficiency Checklist

- [x] run verdict
- [x] prompt set
- [x] pass fail table
- [x] failed trace details
- [x] anti tailoring status
- [x] anti cheat status
- [x] model lane status
- [x] commands run
- [x] relevant files
- [x] next recommended step
- [x] upload guidance
