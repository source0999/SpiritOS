# Source Proxy Tool Action Runtime v1 Plan 3 Closeout

Plan completed: Plan 3/8: Disposable Workspace Executor And Safety Gates.

## Files Changed

- `source_proxy/decision/tool_action_executor.py`
- `source_proxy/tests/test_coding_regression_pack.py`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-3/plan-3-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-3/plan-3-closeout.md`

## Evidence Created

- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-3/plan-3-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-3/plan-3-closeout.md`

## Increment Results

- Increment 3.1.1 Workspace root contract: GO. `ToolActionWorkspaceContract` defines the explicit disposable workspace root and safety policy.
- Increment 3.1.2 Path traversal and symlink escapes: GO. Resolved targets must stay beneath the workspace root; symlink targets are blocked.
- Increment 3.1.3 Protected paths and forbidden files: GO. Protected/secret-shaped targets and forbidden files block before mutation.
- Increment 3.1.4 Before/after workspace status: GO. Receipts include before/after file status snapshots.
- Increment 3.2.1 WriteFile: GO. Writes model-authored content only to allowed workspace files.
- Increment 3.2.2 EditFile: GO. Applies one model-authored search/replace and fails if the old fragment is missing.
- Increment 3.2.3 MultiEdit: GO. Applies ordered model-authored edits and fails without partial hidden retry.
- Increment 3.2.4 Unified diff: GO. Write/edit/multiedit results include unified diffs and touched files.
- Increment 3.3.1 ReadFile: GO. Reads bounded workspace file content.
- Increment 3.3.2 ListFiles: GO. Lists bounded non-protected workspace files.
- Increment 3.3.3 SearchRepo with limits: GO. Search output obeys result and byte limits.
- Increment 3.4.1 Command allowlist: GO. RunCheck supports only approved check command shapes.
- Increment 3.4.2 Timeout and output limits: GO. RunCheck uses timeout and bounded stdout/stderr.
- Increment 3.4.3 Network blocked: GO. Network commands block with `network_blocked`.
- Increment 3.4.4 No hidden background jobs: GO. Shell/background syntax blocks with `unsafe_command`.
- Increment 3.5.1 Central authority gate: GO. Workspace contract, action allowed snapshot, forbidden/protected paths, and approval mode are checked before mutation.
- Increment 3.5.2 Existing safety helpers: GO. Uses existing path normalization and unsafe target checks.
- Increment 3.5.3 Unsafe commands report reason: GO. Unsafe commands produce blocked results instead of execution or retry.

## Checks Run

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'tool_action_executor'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_proxy_agent_routing.py source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or prompt_packet_exposes_task_spec_intake'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_actions.py source_proxy/decision/tool_action_executor.py"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal"
```

Outputs:

- Plan 3 executor slice: `5 passed, 76 deselected`.
- Plan 1-3 coding regression selected slice: `18 passed, 63 deselected`.
- Combined routing/regression selected slice: `18 passed, 86 deselected`.
- `py_compile`: passed on Dell.
- `git diff --check`: clean.
- `git status`: expected dirty tree with pre-existing roadmap/evidence artifacts plus Plan 1/2/3 runtime and evidence files.

## Expected Output

- Parsed write/edit actions can mutate only an approved disposable workspace.
- Wrong-file, traversal, symlink, protected path, unsafe command, background, and network traps block visibly.
- Read/search output is bounded and protected paths are not exposed.
- Results and receipts include status, blocked reason, touched files, diff summary, stdout/stderr, before/after workspace status, and adapter source.

## Manual Verification

Copy-paste terminal verification block:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'tool_action_executor'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_proxy_agent_routing.py source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or prompt_packet_exposes_task_spec_intake'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_actions.py source_proxy/decision/tool_action_executor.py"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal"
```

## Forbidden Scope Avoided

- No Plan 4 loop controller.
- No provider/model calls.
- No benchmark or stress tests.
- No safe apply to the real repo.
- No Cartographer mutation.
- No hidden workers.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.

## Blockers

None for Plan 3.

## Rollback Guidance

Rollback by removing only the Plan 3 files listed above and the Plan 3 test additions. Preserve unrelated dirty tree work and Plan 0/1/2 artifacts.

## GO/NO-GO

GO for Plan 3 closeout.

NO-GO for Plan 4 start in this turn.

Next plan title only:

`Plan 4/8: Bounded Agent Loop And Verification Receipts`
