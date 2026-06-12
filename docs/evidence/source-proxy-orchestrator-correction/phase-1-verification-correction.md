# Source Proxy Orchestrator Correction Phase 1 Verification Correction

## Status

Verification evidence repaired only.

No runtime feature work, provider/model calls, benchmark prompts, real app trial mutation, git staging, commit, push, branch, worktree, stash, reset, checkout, or clean were performed.

## Mismatched Claim

The Phase 1 closeout claimed:

```text
34 passed, 1 skipped, 69 deselected
```

That claim was not trustworthy for `source-server` because the active server Python reported:

```text
/home/source/.local/bin/python: No module named pytest
```

## Python/Test Setup

Host checked:

```text
source-server
```

Repo path checked:

```text
/home/source/SpiritOS
```

Actual active Python path checked:

```text
/home/source/.local/bin/python
```

Active Python version:

```text
3.12.3 (main, Mar 23 2026, 19:04:32) [GCC 13.3.0]
```

Pytest was missing from the active Python:

```powershell
ssh source@10.0.0.186 'cd /home/source/SpiritOS && /home/source/.local/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake"'
```

Result:

```text
/home/source/.local/bin/python: No module named pytest
```

Existing setup files/venvs found:

```text
./requirements.core.txt
./requirements.txt
./scout/pytest.ini
./scout/requirements.txt
./.venv-face-organizer/pyvenv.cfg
./.venv/pyvenv.cfg
./.venv-source-proxy/pyvenv.cfg
./.venv-source-proxy-windows/pyvenv.cfg
```

`requirements.txt` already includes:

```text
pytest>=8,<9
```

Existing repo venv used:

```text
/home/source/SpiritOS/.venv/bin/python
pytest 8.4.2
```

No new venv was created. No packages were installed. Pytest was made available by using the existing repo `.venv`.

## Commands Run

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && source .venv/bin/activate && command -v python && python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake'"
```

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
```

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal"
```

## Test Result

Exact test command output:

```text
/home/source/SpiritOS/.venv/bin/python
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/source/SpiritOS
plugins: anyio-4.13.0
collected 104 items / 69 deselected / 35 selected

source_proxy/tests/test_coding_regression_pack.py ...................... [ 62%]
.............                                                            [100%]

====================== 35 passed, 69 deselected in 8.48s =======================
```

Corrected Phase 1 verification result:

```text
35 passed, 69 deselected
```

## Diff Check

Initial `git diff --check` on `source-server` failed with trailing whitespace in:

```text
docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/latest-run.json
docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/preview-url.txt
```

Only those whitespace/check artifacts were normalized. No product logic was changed for this repair.

Exact final command:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
```

Exact final result:

```text

```

The command exited 0 with no output.

## Git Status

Exact command:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal"
```

Exact result:

```text
## master
 M docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/latest-run.json
 M docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/preview-url.txt
 M scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py
 M source_proxy/decision/human_messy_homepage.py
 M source_proxy/decision/task_spec_intake.py
 M source_proxy/decision/tool_action_executor.py
 M source_proxy/decision/tool_action_loop.py
 M source_proxy/tests/test_coding_regression_pack.py
?? docs/evidence/source-proxy-orchestrator-correction/
?? docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/
?? docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/runs/20260611-223358/
```

## GO/NO-GO For Phase 2 Planning

GO for Phase 2 planning based on corrected host-side verification.

NO-GO for starting Phase 2 in this task.

## Blockers

None for verification correction.
