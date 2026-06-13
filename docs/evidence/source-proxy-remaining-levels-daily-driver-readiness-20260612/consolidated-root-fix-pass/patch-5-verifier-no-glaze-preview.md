# Patch 5: Verifier Preview Packet And No-Glaze Harness

Status: PASS_SUBCHECK

## Changed Files

- `source_proxy/decision/verifier_lane.py`
- `source_proxy/tests/test_verifier_lane.py`

## What Changed

- Verifier packets remain preview-only, advisory-only, and `model_calls_enabled: false`.
- Packets now include task spec, planner criteria, transcript path, workspace diff path, behavior probe evidence, repair packet, and repair result.
- Missing planner criteria, receipt, transcript, diff, probe, or browser evidence are reported as missing evidence.
- Failed browser behavior blocks PASS and returns a non-PASS advisory status.
- Verifier still cannot edit files, repair artifacts, override failed browser behavior, or convert UNVERIFIED into PASS.

## Sample Verifier Preview Packet

```json
{
  "preview_only": true,
  "advisory_only": true,
  "model_calls_enabled": false,
  "original_user_prompt": "make a theme toggle",
  "normalized_intent": "theme toggle",
  "task_spec": {"task_type": "create_file_bundle"},
  "planner_criteria": [{"criterion_id": "theme-computed-color-change"}],
  "selected_coder_lane": "qwen_local_coder",
  "generated_preview_path": "workspace/index.html",
  "browser_observation": {"verdict": "FAIL", "passed": false, "opened": true},
  "receipt_path": "receipt.json",
  "transcript_path": "transcript.txt",
  "workspace_diff_path": "workspace.diff",
  "behavior_probe_evidence": {"verdict": "FAIL"},
  "retest_result_path": "retest.json"
}
```

## Sample Downgrade / Block Output

```json
{
  "advisory_only": true,
  "model_calls_enabled": false,
  "verdict": "NEEDS_FIX",
  "reasons": ["browser_behavior_failed", "preview_contract_only_no_model_call"],
  "cannot_override_browser_behavior": true,
  "cannot_turn_unverified_into_pass": true
}
```

## Tests Run

```text
python -m pytest source_proxy/tests/test_verifier_lane.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_cartographer_routing.py source_proxy/tests/test_artifact_final_verdict.py
24 passed

python -m py_compile source_proxy/decision/verifier_lane.py source_proxy/tests/test_verifier_lane.py
PASS

git diff --check -- source_proxy/decision/verifier_lane.py source_proxy/tests/test_verifier_lane.py
PASS
```

## Remaining Risks

- This is still a preview harness. No live verifier model was called or promoted.
- The verifier cannot prove Level 3 GREEN; it only helps prevent evidence glazing once random-set reruns exist.
