# Terminal Verification

Date: 2026-06-13

Working tree note: the repo had pre-existing modified/untracked Source Proxy files and evidence folders before this task. This proof added `docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/` only.

## Prompt Lock Validation

Command:

```powershell
python -m json.tool docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\final-proof-prompt-set.json > $null
```

Result: PASS.

## Pre/Post Anti-Tailoring Grep

Command:

```powershell
rg -n -F -e "<new exact prompt strings and final-l3-clean-* ids>" source_proxy src apps scripts <runner scripts>
```

Result: no matches in runtime/source/runner scopes before or after the run.

Command:

```powershell
rg -n -F -e "<new exact prompt strings and final-l3-clean-* ids>" docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613
```

Result: matches present in prompt lock, run evidence, traces, reports, and dashboard as expected.

Command:

```powershell
rg -n -F -e "<old 10d/10e exact prompt strings>" source_proxy\decision src apps scripts <runner scripts>
```

Result: no matches in runtime decision/app/script scopes. Old strings are present in tests when searching all `source_proxy/`, as historical regression fixtures.

## Final Proof Run

Command:

```powershell
python docs\evidence\source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612\anti_tailoring_run_batch.py --prompt-file "<evidence>\final-proof-prompt-set.json" --run-root "<evidence>\final-clean-similar-10-runs" --title "Source Proxy Level 3 final clean similar 10 transparent proof" --results "<evidence>\final-proof-intermediate-results.json" --html "<evidence>\final-proof-intermediate.html" --run-receipt "<evidence>\final-proof-run-receipt.json" --browser-results "<evidence>\final-proof-browser-behavior-results.json" --repair-summary "<evidence>\final-proof-post-behavior-repair-summary.json" --model-id qwen2.5-coder:7b
```

Result:

```json
{
  "results": 10,
  "pass": 5
}
{
  "repairs": 2,
  "total": 10
}
{
  "results": 10,
  "pass": 5
}
{
  "total": 10,
  "pass": 5,
  "overall": "NO-GO"
}
```

## Report Generation

Command:

```powershell
python docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\generate_final_proof_reports.py
```

Result:

```json
{
  "verdict": "NO-GO",
  "pass": 5,
  "fail": 5
}
```

## Focused Tests

Command:

```powershell
python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_repair_loop.py
```

Result: 47 passed.

Command:

```powershell
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or final_verdict or retest or repair or score_integrity or failure_bucket or fake or fallback or backend_authored"
```

Result: 20 passed, 99 deselected.

Command:

```powershell
python -m pytest source_proxy/tests/test_task_spec_intake_unseen_artifacts.py
```

Result: 11 passed.

## Evidence Validation

Command:

```powershell
python -m py_compile docs\evidence\source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613\generate_final_proof_reports.py
```

Result: PASS.

Command:

```powershell
python -m json.tool final-proof-prompt-set.json > $null
python -m json.tool final-proof-results.json > $null
python -m json.tool per-prompt-traces\*.json > $null
python -c "import xml.etree.ElementTree as ET; ET.parse(r'mini-context-pack.xml')"
```

Result: json+xml validation ok.

Command:

```powershell
python <inline final-proof.html link audit>
```

Result:

```text
{'links': 91, 'missing': []}
```

Command:

```powershell
git diff --check -- docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613
```

Result: PASS.

## Git Status

Command:

```powershell
git status --branch --short --untracked-files=normal
```

Result summary:

```text
## master
pre-existing modified Source Proxy files remain
new evidence folder present:
?? docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/
```
