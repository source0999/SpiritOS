# Source Proxy Tool Action Runtime v1 Plan 3 Evidence

Plan: Plan 3/8: Disposable Workspace Executor And Safety Gates.

Status: implemented and verified.

## Phase 3.1 Workspace Containment

Implemented:

- `source_proxy/decision/tool_action_executor.py`
  - Adds `ToolActionWorkspaceContract` with explicit `workspace_root`, allowed files, forbidden/protected paths, approval level, network policy, output limits, search limits, and RunCheck timeout.
  - Resolves every file target beneath the approved workspace root.
  - Blocks path traversal, protected/secret-shaped targets, forbidden files, wrong-file writes, and symlink escapes.
  - Records before/after workspace file status in execution receipts.

Evidence:

- Wrong-file write blocks with `target_not_allowed`.
- `../outside.md` blocks with `path_escape`.
- `.env.local` blocks before write.
- Symlink target to outside the temp workspace blocks and leaves the outside file unchanged.
- Receipts include `before_status` and `after_status`.

GO/NO-GO: GO.

## Phase 3.2 Write/Edit Execution

Implemented:

- `WriteFile` writes model-authored content only to allowed workspace files.
- `EditFile` performs a single model-authored search/replace.
- `MultiEdit` applies ordered model-authored search/replace items.
- Each write/edit operation returns a unified diff and touched file list.

Evidence:

- `WriteFile` updates only `docs/phase-8-manual-check.md` in the disposable test workspace.
- `EditFile` and `MultiEdit` complete against the allowed docs target.
- Wrong-file and traversal traps do not create files.

GO/NO-GO: GO.

## Phase 3.3 Read/Search Execution

Implemented:

- `ReadFile` returns bounded file output.
- `ListFiles` returns bounded non-protected file listings.
- `SearchRepo` scans workspace files with result and byte limits.
- Protected paths are excluded from list/search output.

Evidence:

- `ReadFile` returns the edited docs content.
- `SearchRepo` honors `search_result_limit=1`.
- Search output does not expose protected `.env` paths.

GO/NO-GO: GO.

## Phase 3.4 RunCheck Execution

Implemented:

- `RunCheck` uses an allowlist:
  - `git diff --check`
  - `git status --short`
  - `python -m py_compile ...`
  - `python3 -m py_compile ...`
- Python commands run through the active interpreter for portable venv behavior.
- RunCheck uses `shell=False`, a timeout, output limits, and no background jobs.
- Network commands remain blocked unless policy later explicitly allows them.

Evidence:

- Allowlisted `python -m py_compile source_proxy/__init__.py` completes inside the temp workspace.
- `curl http://example.com` blocks with `network_blocked`.
- Background syntax blocks with `unsafe_command`.

GO/NO-GO: GO.

## Phase 3.5 Authority Validator

Implemented:

- Central target resolution checks the workspace contract, action allowed snapshot, forbidden/protected paths, and approval mode before file mutation.
- Contract-level allowed files win when supplied; action-level snapshots cannot expand authority beyond the workspace contract.
- Unsafe commands block instead of retrying or falling through.

Evidence:

- An action with its own allowed snapshot for `docs/not-approved.md` still blocks when the workspace contract allows only `docs/phase-8-manual-check.md`.
- Protected and traversal failures produce blocked results with explicit error codes.
- No real app file is touched by executor tests; all mutations happen inside `tempfile.TemporaryDirectory`.

GO/NO-GO: GO.

## Checks

Executed from `Z:\` PowerShell against `/home/source/SpiritOS`:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'tool_action_executor'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_action_executor.py"
```

Results:

- Plan 3 executor slice: `5 passed, 76 deselected`.
- `py_compile`: passed on Dell.

Final combined checks are recorded in the Plan 3 closeout.

## Forbidden Scope Avoided

- No Plan 4 loop controller.
- No provider/model calls.
- No benchmark or stress tests.
- No safe apply to the real repo.
- No Cartographer mutation.
- No hidden workers.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.
