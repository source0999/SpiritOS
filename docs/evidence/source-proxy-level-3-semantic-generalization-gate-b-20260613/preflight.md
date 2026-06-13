# Gate B Preflight

Date: 2026-06-13

Scope: Level 3 semantic intake and behavior generalization repair. No Level 4, no new prompt batch, no 25/50/100 run, no scorer green-padding, no exact prompt branches, no prompt-id branches, no cloud fallback, no backend-authored rescue content, no hidden deterministic scaffold, no branch/stash/reset/checkout/clean/stage/commit/push.

## Current Git Status

`git status --branch --short --untracked-files=normal` was run before Gate B source edits.

Branch:

```text
## master
```

Pre-existing modified tracked files:

```text
M docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T02-19-36-375Z-design-mobile-britton-realistic/design/design-design-002-mobile-overlap-detection/design-design-002-mobile-overlap-detection.png
M source_proxy/api/decision.py
M source_proxy/decision/human_messy_homepage.py
M source_proxy/decision/task_spec_intake.py
M source_proxy/decision/tool_action_executor.py
M source_proxy/decision/tool_action_loop.py
M source_proxy/tests/test_coding_regression_pack.py
```

Pre-existing untracked Source Proxy/evidence files and folders were present, including the Gate A evidence folder, Level 3 proof folders, Source Proxy decision modules, and Source Proxy tests. This Gate B pass will preserve that dirty-tree state and add only the focused source/test/evidence changes needed for the task.

## Evidence Freeze

- Gate A evidence folder exists: `docs/evidence/source-proxy-level-3-semantic-generalization-gate-a-20260613/`
- Gate A verdict: PACK_READY.
- Final clean similar 10 prompt set exists: `docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/final-proof-prompt-set.json`
- Prompt set file size observed: 241 bytes.
- No Level 4/new batch will be created.
- Existing final clean similar 10 prompt set will be reused only after focused tests pass.

## Expected Source/Test Files To Touch

Expected runtime/test files:

- `source_proxy/decision/task_spec_intake.py`
- `source_proxy/decision/artifact_behavior_contract.py`
- `source_proxy/decision/human_messy_homepage.py`
- `source_proxy/decision/artifact_repair_contract.py`
- `source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- `source_proxy/tests/test_artifact_behavior_contract.py`
- `source_proxy/tests/test_artifact_repair_contract.py`

Expected evidence/runner files if needed for non-breaking trace sidecars:

- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py`

Expected Gate B evidence files:

- `docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/index.md`
- `preflight.md`
- `changed-files.md`
- `unit-test-gate.md`
- `route-intake-repair.md`
- `behavior-generation-repair.md`
- `repair-loop-upgrade.md`
- `trace-instrumentation.md`
- `final-clean-10-rerun-summary.md`
- `anti-tailoring-audit.md`
- `anti-cheat-integrity.md`
- `remaining-failures.md`
- `terminal-verification.md`
- `mini-context-pack.md`
- `mini-context-pack.xml`
- `mini-context-pack.json`

## Expected Tests/Commands

Focused test gate:

```powershell
python -m pytest source_proxy/tests/test_task_spec_intake_unseen_artifacts.py
```

Behavior/final verdict/repair tests:

```powershell
python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_repair_loop.py
```

Selected regression tests:

```powershell
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or final_verdict or retest or repair or score_integrity or failure_bucket or fake or fallback or backend_authored"
```

Syntax checks:

```powershell
python -m py_compile <touched Python files>
node --check <touched JS files if any>
```

Final holdout rerun after tests pass:

```powershell
python docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py --prompt-file docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/final-proof-prompt-set.json --run-root docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-runs --title "Source Proxy Level 3 semantic generalization Gate B final clean similar 10 rerun" --results docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-results.json --html docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b.html --run-receipt docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-run-receipt.json --browser-results docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-browser-behavior-results.json --repair-summary docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/final-clean-10-gate-b-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b
```

Final validation:

```powershell
python -m json.tool docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/mini-context-pack.json
python -c "import xml.etree.ElementTree as ET; ET.parse('docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/mini-context-pack.xml')"
git diff --check -- <touched files>
git status --branch --short --untracked-files=normal
```
