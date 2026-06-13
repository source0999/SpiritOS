# Source Proxy Level 3 Semantic Generalization Gate A Mini Context Pack

Date: 2026-06-13

Verdict: PACK_READY

## Current Verdict

The latest final clean similar 10 proof remains NO-GO: 5/10 behavior PASS against an 8/10 threshold.

## What Was Read

- Prior ChatGPT context pack in Markdown, XML, and JSON.
- Final clean similar 10 results and transparent trace index.
- Failing per-prompt traces for final-l3-clean-02, 03, 05, 09, and 10.
- Failed run receipts, scores, transcripts, behavior probes, failure packets, repair results, and workspace diffs where available.
- Failure-family stabilization root-cause matrix and index.
- Intake, routing, behavior contract, repair, final verdict, anti-tailoring runner, and browser behavior probe source files.

## What Was Written

Gate A evidence only under:

`docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/`

No runtime source implementation was performed.

## Source Files Reviewed

- `source_proxy/decision/task_spec_intake.py`
- `source_proxy/decision/human_messy_homepage.py`
- `source_proxy/decision/artifact_behavior_contract.py`
- `source_proxy/decision/artifact_repair_loop.py`
- `source_proxy/decision/artifact_repair_contract.py`
- `source_proxy/decision/artifact_final_verdict.py`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`

## Current Failure Diagnosis

Three failures are route/intake failures:

- cost sharer: behavior contract recognized calculator/splitter, but disposable resolver missed sharer/share/fee semantics.
- palette switch: standalone theme switch wording missed resolver terms because it used switch/palette rather than switcher/toggle/mode/color/picker style terms.
- secret phrase strength gauge: behavior contract recognized password/passphrase strength, but disposable resolver missed phrase/passphrase/strength/gauge as browser UI terms.

Two failures are behavior/repair failures:

- weather: a weather control was clicked, but visible text stayed static. The artifact/repaired file used a wrong selector for city.
- drawing: canvas existed, but mouse drawing did not change pixels. Repair changed the canvas id without updating the script selector, and the initial script also cleared marks on mouseup.

## Decision-Boundary Findings

Family/probe inference and disposable routing are separate. A prompt can receive a good behavior contract and still fall into `clarification_required_real_repo_implementation`.

Safest Gate B rule:

Standalone creation verb plus small tool/widget/app noun or interactive family signal plus no explicit repo/file/component target should become a disposable artifact candidate. Existing app/component/src/file/dashboard/production/repo wording should remain real-repo clarification or explicit-target work.

## Proposed Tests

Positive synonym tests cover calculator/splitter, theme/mode, and password/passphrase variants such as cost sharer, parking cost splitter, dusk dawn switch, palette switch, phrase strength gauge, and passphrase strength checker.

Negative controls cover existing dashboard, src component, production switcher, existing drawing bug, real weather tile, explicit ThemeSwitcher path, existing test file, dashboard forecast component, and real billing splitter route.

## Proposed Gate B Source Changes

- Expand generic disposable resolver concept groups in `task_spec_intake.py`.
- Align behavior contract coverage for dusk/dawn/palette switch terms.
- Add weather first-pass generation checklist.
- Strengthen drawing first-pass generation wording.
- Upgrade repair prompt structure with explicit failure deltas and path-bound output requirements.
- Add non-breaking route trace sidecar fields.

## Anti-Cheat Boundary

Gate B may change generic routing, behavior contracts, model packet wording, repair packet wording, tests, and additive traces. It must not add exact prompt branches, scorer padding, cloud fallback, backend rescue content, hidden scaffold, new batches, or Level 4.

Weather and drawing must prove behavior through browser probes, not model self-report.

## Execution Boundary

- Source runtime code changed in Gate A: no.
- Browser holdout rerun in Gate A: no.
- Model calls in Gate A: no.
- New prompt batches in Gate A: no.
- Level 4 started in Gate A: no.

## Next Recommended Action

Britton should upload this file next:

`docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/mini-context-pack.md`

Then review `implementation-gate-b-plan.md` before approving any Gate B implementation.
