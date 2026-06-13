# Checks

Date: 2026-06-13

## Passed

- `python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_repair_loop.py`
  - 46 passed.
- `python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or final_verdict or retest or repair or score_integrity or failure_bucket or fake or fallback or backend_authored"`
  - 20 passed, 99 deselected.
- `python -m py_compile source_proxy/decision/artifact_final_verdict.py source_proxy/decision/artifact_behavior_contract.py docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_post_behavior_repair.py`
- `node --check docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`
- `git diff --check -- <changed scoped files>`
- JSON validation for `anti-tailoring-random-10d-results.json`, `anti-tailoring-random-10e-results.json`, and `anti-tailoring-random-10e.json`.
- HTML existence checks for 10d and 10e returned true.

## Batch Runs

- 10d rerun command completed with 5/10 PASS, NO-GO.
- 10e fresh run command completed with 6/10 PASS, NO-GO.
