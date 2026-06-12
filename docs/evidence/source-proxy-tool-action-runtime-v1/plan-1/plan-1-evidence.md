# Source Proxy Tool Action Runtime v1 Plan 1 Evidence

Plan: Plan 1/8: Natural Prompt To TaskSpec Intake.

Status: implemented and verified.

## Phase 1.1 TaskSpec Schema

Implemented:

- `source_proxy/decision/task_spec_intake.py`
  - Adds `TaskSpecIntake` with fields for `task_kind`, `intent`, `user_prompt`, `target_paths`, `allowed_files`, `forbidden_files`, `protected_paths`, `workspace_mode`, `approval_level`, `model_lane`, `context_sources`, `verification_policy`, `risk_level`, `clarification_state`, reason codes, and summary.
  - Adds `build_task_spec_intake(...)` for pre-model prompt intake.
  - Adds `intake_as_legacy_task_spec(...)` so existing prompt-packet consumers receive compatible `task_spec` payloads.
- `source_proxy/api/decision.py`
  - Adds `task_spec_intake` and `taskSpecIntake` to prompt-packet responses.
  - Extends camelCase task-spec diagnostics with clarification/workspace/approval fields.
- `source_proxy/tests/test_coding_regression_pack.py`
  - Adds schema and serialization coverage.

Evidence:

- Existing explicit target prompt serializes to `modify_existing_file`.
- Allowed files are locked to the target for existing-file implementation.
- Verification policy includes `git diff --check`.
- Approval remains `preview_only_no_apply`.

GO/NO-GO: GO.

## Phase 1.2 Creation-Intent Route

Implemented:

- Bounded `Proposal task` JSON can form `create_new_file` only when:
  - `mode` is `proposal`;
  - `target_file` is present;
  - `target_file` is inside `allowed_files`;
  - target does not intersect forbidden/protected paths;
  - target does not escape the workspace.
- Unbounded/vague create prompts become `target_unresolved` with `clarification_state: required`.
- Missing real-repo target paths require clarification instead of silent advisory fallthrough.

Evidence:

- `src/app/agent-lab/demo/page.tsx` bounded create intake becomes `workspace_mode: disposable_workspace`.
- Vague create prompt with no target becomes `target_unresolved`, no allowed files, no workspace mode.

GO/NO-GO: GO.

## Phase 1.3 Scope Clarification UI/Diagnostics

Implemented:

- Existing `/coding` UI already shows inferred scope review and scope clarification from local `plain-english-scope` logic.
- Backend prompt-packet responses now include `task_spec_intake` / `taskSpecIntake` so UI/API clients can show exactly what Source Proxy understood before model execution.
- Blocked prompt-packet responses reuse the intake-derived legacy `task_spec`, preserving compatibility while exposing clarification details.

Evidence:

- Vague prompt-packet request returns `task_spec_intake.task_kind: target_unresolved`.
- Coder/architect model paths are not called for unresolved prompt-packet requests.
- Protected path intake returns `protected_path`, no allowed files, `clarification_state: blocked`, and high risk.

GO/NO-GO: GO.

## Checks

Executed on `/home/source/SpiritOS` via SSH:

```bash
.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or prompt_packet_exposes_task_spec_intake or explicit_target_controls_allowed_files or no_target_documentation_request'
.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_proxy_agent_routing.py -k 'target_unresolved or env_local or path_traversal or bounded_proposal'
git diff --check
```

Results:

- `7 passed, 60 deselected`
- `5 passed, 18 deselected`
- Linux `git diff --check`: clean

Windows note:

- Local PowerShell `git diff --check` was clean but printed LF-to-CRLF warnings for pre-existing/edited files.
- Local `.venv-source-proxy\Scripts\python.exe` shim was not usable from the mapped-drive shell, so tests were run on the authoritative Dell path.

## Forbidden Scope Avoided

- No tool/action parser or executor implementation.
- No model/provider calls.
- No trial prompts or benchmark reruns.
- No safe apply or real app mutation from prompts.
- No Cartographer, queue, worker, branch/worktree, commit, push, stash, reset, checkout, clean, package, config, or CSS edits.
