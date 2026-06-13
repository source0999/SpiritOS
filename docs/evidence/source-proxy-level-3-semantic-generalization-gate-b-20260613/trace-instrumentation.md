# Trace Instrumentation

## What Was Added

`anti_tailoring_run_batch.py` now writes a `route_trace.json` sidecar for each run.

Each sidecar includes:

- `original_prompt`
- `normalized_prompt`
- `family_candidates`
- `family_match_reasons`
- `standalone_artifact_signals`
- `real_repo_signals`
- `explicit_target_path_detected`
- `selected_artifact_family`
- `behavior_contract_probe_id`
- `normalized_intent_before_route`
- `normalized_intent_after_route`
- `route_decision`
- `route_decision_reason`
- `disposable_candidate_true_false`
- `blocking_reason_if_any`
- `selected_preview_path`
- `why_no_preview_if_blocked`

The results evidence links now include `route_trace` when present.

## Where Written

Per-run files:

`docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-runs/<run>/route_trace.json`

## Schema Compatibility

The change is additive. It does not alter:

- `behavior-probe.json`
- `score.json`
- `receipt.json`

Existing report consumers can ignore `route_trace.json`.

## Gate B Trace Result

All 10 final clean rerun prompts have `route_trace.json`.

The three previously route-blocked prompts now show:

- standalone artifact signals present
- no real-repo signals
- behavior contract probe id present
- `normalized_intent_after_route: disposable_small_file_bundle`
- `route_decision: GO`
- preview path selected

## Remaining NOT_RECORDED

No required Gate B route-trace fields are intentionally omitted in the new sidecar. Some values can still be empty when a prompt has no blocking reason or preview is selected; that is expected.
