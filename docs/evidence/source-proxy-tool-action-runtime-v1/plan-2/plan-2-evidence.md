# Source Proxy Tool Action Runtime v1 Plan 2 Evidence

Plan: Plan 2/8: Tool/Action Contract And Parser.

Status: implemented and verified.

## Phase 2.1 Action Envelope

Implemented:

- `source_proxy/decision/tool_actions.py`
  - Adds `SourceProxyAction` with versioned action fields: `action_id`, `action_type`, `target`, `arguments`, `reason`, `requires_approval`, `model_id`, `source_message_id`, `allowed_files_snapshot`, `created_at`, `schema_version`, `authorship`, and parser-only execution state.
  - Adds `adapter_source` to the action envelope and parse result so adapter source lane is carried into receipts.
  - Adds `SourceProxyActionResult` with result fields: `action_id`, `status`, `blocked_reason`, `files_touched`, `diff_summary`, `stdout`, `stderr`, `observation`, `receipt_path`, `adapter_source`, `schema_version`, and `error_code`.
  - Adds stable parser and execution-boundary error codes.

Evidence:

- Strict JSON `WriteFile` action preserves the raw transcript and source metadata.
- Plan 2 write/run actions return `execution_blocked_until_plan_3` from the contract helper and touch no files.
- Backend-authored content is rejected with `backend_authorship_rejected`.

GO/NO-GO: GO.

## Phase 2.2 Initial Tool Set

Implemented:

- Initial generic tool catalog:
  - `ReadFile`
  - `ListFiles`
  - `SearchRepo`
  - `WriteFile`
  - `EditFile`
  - `MultiEdit`
  - `RunCheck`
  - `AskClarification`
  - `ReturnFinal`
- Read/write/execute/respond classifications.
- Write and execute tools are marked `blocked_until_plan_3`; no executor is attached.

Evidence:

- Regression test asserts all nine tools are present.
- Regression test asserts capability classifications.
- Regression test asserts `WriteFile` execution is blocked until Plan 3.

GO/NO-GO: GO.

## Phase 2.3 Parser Paths

Implemented:

- Strict JSON parser for one action or an `actions` array.
- Line-delimited JSON parser for multiple model-authored actions.
- Explicit `<file path="...">...</file>` path/content block parser for local-model fallback.
- Adapter compatibility aliases for model-authored path-bound output, including legacy `replace_file` to `WriteFile`.
- Continue-style `Bash` string arguments normalize to `RunCheck` command arguments; non-`Bash` string arguments reject with `bash_string_args_only_for_bash`.
- Aider-like search/replace chunks parse only when model-authored and path-bound.
- Path-bound write/edit adapter output respects the allowed file snapshot when one is supplied.
- Raw transcript and per-parser parse decisions are preserved.
- Free-floating code with no path/action is rejected with a visible repair prompt.

Evidence:

- Strict JSON `WriteFile` parses as a model-authored action and remains blocked for execution.
- Line-delimited `ReadFile` plus Continue `Bash` parses as two actions; string Bash args normalize to `{"command": "git diff --check"}`.
- Plain `RunCheck` string args reject with `bash_string_args_only_for_bash`.
- Aider-like path-bound edit chunks parse into `EditFile` actions when their target is in the allowed snapshot.
- Aider-like edit chunks outside the allowed snapshot reject with `target_not_allowed`.
- Path/content block parses into a path-bound `WriteFile` action with `content_source: path_content_block`.
- Free-floating TSX code fence with no path/action is rejected as `free_floating_code_no_path_action`.

GO/NO-GO: GO.

## Checks

Executed from `Z:\` PowerShell:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_proxy_agent_routing.py source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or prompt_packet_exposes_task_spec_intake'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_actions.py"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
```

Results:

- Coding regression parser/intake slice: `13 passed, 63 deselected`.
- Combined routing/regression selected slice: `13 passed, 86 deselected`.
- `py_compile`: passed on Dell.
- `git diff --check`: clean.

Environment note:

- Authoritative checks run over SSH on `/home/source/SpiritOS` with `.venv-source-proxy/bin/python`.
- No model/provider calls were made.

## Forbidden Scope Avoided

- No Plan 3 executor behavior.
- No write/edit/run execution.
- No provider/model calls.
- No benchmark or stress tests.
- No safe apply.
- No Cartographer mutation.
- No hidden workers.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.
