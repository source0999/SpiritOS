# Checks

## Commands And Results

```text
python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_repair_contract.py source_proxy/tests/test_artifact_repair_loop.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_task_spec_intake_unseen_artifacts.py source_proxy/tests/test_verifier_lane.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_cartographer_routing.py source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or repair or final_verdict or task_spec_intake or tool_action or verifier or model_lane or protected or fallback or backend_authored or fake"
108 passed, 1 skipped, 75 deselected

python -m py_compile source_proxy/decision/artifact_behavior_contract.py source_proxy/decision/artifact_repair_contract.py source_proxy/decision/artifact_repair_loop.py source_proxy/decision/artifact_retest_result.py source_proxy/decision/artifact_final_verdict.py source_proxy/decision/tool_action_executor.py source_proxy/decision/verifier_lane.py docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_post_behavior_repair.py
PASS

node --check docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs
PASS

JSON parse check for 10d JSON outputs
JSON_PARSE_OK 5

HTML link scan for anti-tailoring-random-10d.html
HTML_LINKS 69 MISSING 0

git diff --check -- touched files
PASS; Git printed a line-ending warning for source_proxy/decision/tool_action_executor.py

git status --branch --short --untracked-files=normal
Dirty tree preserved. No staging/commit/reset/checkout/clean performed.
```

## Skipped Tests

One existing regression-pack test was skipped by its existing condition during the focused filtered run.

## JSON Parse Result

PASS for:

- `anti-tailoring-random-10d.json`
- `anti-tailoring-random-10d-results.json`
- `anti-tailoring-random-10d-run-receipt.json`
- `anti-tailoring-random-10d-browser-behavior-results.json`
- `anti-tailoring-random-10d-post-behavior-repair-summary.json`

## HTML Link Scan

PASS. `anti-tailoring-random-10d.html` had 69 links and 0 missing.

## Final Git Status

The repository remains dirty with pre-existing modified and untracked files plus this pass's edits. No git mutation commands were run.
