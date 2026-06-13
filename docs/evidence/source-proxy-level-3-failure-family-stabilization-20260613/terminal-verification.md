# Terminal Verification

Date: 2026-06-13

## Commands Run

```powershell
python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_repair_loop.py
```

Result: 47 passed.

```powershell
python -m pytest source_proxy/tests/test_task_spec_intake_unseen_artifacts.py
```

Result: 11 passed.

```powershell
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or final_verdict or retest or repair or score_integrity or failure_bucket or fake or fallback or backend_authored"
```

Result: 20 passed, 99 deselected.

```powershell
python -m py_compile source_proxy/decision/task_spec_intake.py source_proxy/decision/artifact_behavior_contract.py source_proxy/decision/human_messy_homepage.py source_proxy/decision/artifact_repair_contract.py source_proxy/tests/test_task_spec_intake_unseen_artifacts.py source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_repair_loop.py
```

Result: passed.

```powershell
node --check docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs
```

Result: passed.

```powershell
git diff --check -- source_proxy/decision/task_spec_intake.py source_proxy/decision/artifact_behavior_contract.py source_proxy/decision/human_messy_homepage.py source_proxy/decision/artifact_repair_contract.py source_proxy/tests/test_task_spec_intake_unseen_artifacts.py source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_repair_loop.py docs/evidence/source-proxy-level-3-failure-family-stabilization-20260613
```

Result: passed. Git emitted only line-ending warnings for two preexisting working-copy text normalization cases.

```powershell
python anti_tailoring_run_batch.py --prompt-file anti-tailoring-random-10d.json --run-root anti-tailoring-random-10d-level3-stabilization-runs --title "Anti-tailoring random 10d Level 3 failure-family stabilization rerun" --results anti-tailoring-random-10d-level3-stabilization-results.json --html anti-tailoring-random-10d-level3-stabilization.html --run-receipt anti-tailoring-random-10d-level3-stabilization-run-receipt.json --browser-results anti-tailoring-random-10d-level3-stabilization-browser-behavior-results.json --repair-summary anti-tailoring-random-10d-level3-stabilization-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b
```

Result: 10/10 PASS, overall `GREEN_READY_FOR_BRITTON_REVIEW`.

```powershell
python anti_tailoring_run_batch.py --prompt-file anti-tailoring-random-10e.json --run-root anti-tailoring-random-10e-level3-stabilization-runs --title "Anti-tailoring random 10e Level 3 failure-family stabilization rerun" --results anti-tailoring-random-10e-level3-stabilization-results.json --html anti-tailoring-random-10e-level3-stabilization.html --run-receipt anti-tailoring-random-10e-level3-stabilization-run-receipt.json --browser-results anti-tailoring-random-10e-level3-stabilization-browser-behavior-results.json --repair-summary anti-tailoring-random-10e-level3-stabilization-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b
```

Result: 10/10 PASS, overall `GREEN_READY_FOR_BRITTON_REVIEW`.

```powershell
python -m json.tool docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization-results.json > $null
python -m json.tool docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization-results.json > $null
```

Result: passed.
