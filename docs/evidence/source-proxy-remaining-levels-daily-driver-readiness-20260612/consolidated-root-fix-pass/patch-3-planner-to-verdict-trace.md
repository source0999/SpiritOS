# Patch 3: Planner Criteria To Final Verdict Trace

Status: PASS_SUBCHECK

## Changed Files

- `source_proxy/decision/artifact_final_verdict.py`
- `source_proxy/decision/artifact_retest_result.py`
- `source_proxy/tests/test_artifact_final_verdict.py`
- `source_proxy/tests/test_artifact_retest_result.py`

## What Changed

- Added `build_artifact_final_verdict_row` to preserve one auditable row from original prompt through normalized intent, planner criterion, behavior contract, probe result, route/open status, repair status, evidence refs, anti-cheat flags, and final reason codes.
- Kept route GO, preview open, static DOM, and model self-report as non-pass signals when behavior proof is required.
- Failed browser probes now carry `behavior_failed_verified` and behavior-probe failure codes into the row.
- Added `post_behavior_repair_pass` and `post_behavior_repair_failed` aliases while preserving existing `post_repair_behavior_*` reason codes.

## Sample Final Verdict Row

```json
{
  "original_prompt": "make a calculator app",
  "normalized_intent": "create static calculator UI",
  "planner_criterion_id": "criterion-calc-result",
  "behavior_criterion_id": "criterion-calc-result",
  "behavior_contract_id": "source-proxy-artifact-behavior-contract-v0.2.phase-3",
  "probe_id": "calculator-basic-arithmetic",
  "selected_preview_path": "workspace/index.html",
  "route_status": "GO",
  "open_status": "PASS",
  "observed_before": "0",
  "observed_after": "5",
  "repair_attempt_count": 1,
  "repair_status": "READY_FOR_RETEST",
  "evidence_refs": {"receipt": "receipt.json", "probe": "behavior.json"},
  "anti_cheat_flags": {"fallback_used": false},
  "canonical_final_verdict": "PASS",
  "product_pass": true,
  "final_reason_codes": ["behavior_pass_verified", "post_behavior_repair_pass", "repair_attempts_1"],
  "passed_stage": "passed_after_repair"
}
```

## Tests Run

```text
python -m pytest source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_verifier_lane.py source_proxy/tests/test_coding_regression_pack.py -k "artifact or final_verdict or verifier"
28 passed, 112 deselected

python -m py_compile source_proxy/decision/artifact_final_verdict.py source_proxy/decision/artifact_retest_result.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py
PASS

git diff --check -- source_proxy/decision/artifact_final_verdict.py source_proxy/decision/artifact_retest_result.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py
PASS
```

## Remaining Risks

- The helper is additive. Existing report scripts still need to consume it for full HTML/JSON trace coverage.
- This subcheck proves reason-code and row construction behavior, not random-set threshold performance.
