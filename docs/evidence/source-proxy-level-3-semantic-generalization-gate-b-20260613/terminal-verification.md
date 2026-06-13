# Terminal Verification

Status: complete.

## Commands Run And Results

Preflight:

- `git status --branch --short --untracked-files=normal`: PASS, repo already dirty.
- Gate A folder listing: PASS.
- Final clean prompt set existence check: PASS.

Focused intake tests:

- `python -m pytest source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- Baseline after adding tests: FAIL as expected, 1 failed/12 passed, first failing prompt `make a cost sharer`.
- After route repair: PASS, 13 passed.
- Final rerun after later patches: PASS, 13 passed.

Behavior/final/retest/repair tests:

- `python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_repair_loop.py`
- First run after repair prompt upgrade: FAIL, 1 failed/46 passed due expected old `Primary failure bucket` label.
- After compatibility line restored: PASS, 47 passed.

Selected regression tests:

- `python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or final_verdict or retest or repair or score_integrity or failure_bucket or fake or fallback or backend_authored"`
- PASS, 20 passed, 99 deselected.

Syntax checks:

- `python -m py_compile source_proxy/decision/task_spec_intake.py source_proxy/decision/artifact_behavior_contract.py source_proxy/decision/human_messy_homepage.py source_proxy/decision/artifact_repair_contract.py docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py`
- PASS.

Final clean similar 10 rerun:

- Relative-path command: FAIL before prompt execution due runner resolving paths under its own script folder.
- Absolute `Z:/...` command: PASS.
- Output: first browser pass count 8/10, final post-repair pass count 9/10, overall `GREEN_READY_FOR_BRITTON_REVIEW`.

Anti-tailoring:

- Broad initial grep: timed out on large share scope.
- Narrow fixed-string runtime/source searches: PASS, no exact failed prompt strings or failed prompt ids found.

Final validation:

- `python -m json.tool docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/mini-context-pack.json`
  - PASS.
- `python -c "import xml.etree.ElementTree as ET; ET.parse('docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/mini-context-pack.xml')"`
  - PASS.
- `git diff --check -- <touched files>`
  - PASS. Git printed existing LF-to-CRLF warnings for `human_messy_homepage.py` and `task_spec_intake.py`; no whitespace errors.
- `git status --branch --short --untracked-files=normal`
  - PASS. Repo remains dirty as recorded in preflight; Gate B did not clean/reset/stash/stage/commit/push.
