# Source Proxy Tool Action Runtime v1 Plan 1 Closeout

Plan completed: Plan 1/8: Natural Prompt To TaskSpec Intake.

## Files Changed

- `source_proxy/decision/task_spec_intake.py`
- `source_proxy/api/decision.py`
- `source_proxy/tests/test_coding_regression_pack.py`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-1/plan-1-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-1/plan-1-closeout.md`

## Evidence Created

- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-1/plan-1-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-1/plan-1-closeout.md`

## Increment Results

- Increment 1.1.1 TaskSpec fields: GO. `TaskSpecIntake` captures task kind, intent, prompt, targets, allowed/forbidden/protected paths, workspace mode, approval level, model lane, context sources, verification policy, risk, and clarification state.
- Increment 1.1.2 Schema validation and readable errors: GO. Intake normalizes paths, blocks protected/path-escape targets, detects target/allowed mismatch, and emits reason codes plus clarification prompts.
- Increment 1.1.3 Serialization: GO. Responses expose snake_case and camelCase `task_spec_intake` payloads.
- Increment 1.2.1 Create/new-project/no-target detection: GO. Bounded proposals become disposable create specs; vague create prompts become clarification-required.
- Increment 1.2.2 Disposable target inference: GO. Create mode requires explicit bounded proposal target/allowed files and marks `workspace_mode: disposable_workspace`.
- Increment 1.2.3 Ambiguous real-repo target clarification: GO. Vague implementation prompts stay `target_unresolved` and do not call coder/architect paths.
- Increment 1.3.1 Show what Source Proxy understood: GO. Prompt-packet diagnostics now include `task_spec_intake`/`taskSpecIntake`.
- Increment 1.3.2 Show target/allowed/forbidden/protected paths: GO. Intake payload includes these fields.
- Increment 1.3.3 Show blocked/no-op/already-satisfied honestly: GO for Plan 1 scope. Blocked target and protected-path states are explicit; no no-op behavior was changed.

## Checks Run

```bash
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or prompt_packet_exposes_task_spec_intake or explicit_target_controls_allowed_files or no_target_documentation_request'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_proxy_agent_routing.py -k 'target_unresolved or env_local or path_traversal or bounded_proposal'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
git diff --check
git status --branch --short --untracked-files=normal
```

Outputs:

- Coding regression slice: `7 passed, 60 deselected`.
- Routing regression slice: `5 passed, 18 deselected`.
- Dell/Linux `git diff --check`: clean.
- Windows `git diff --check`: clean with LF-to-CRLF warnings.
- Status showed pre-existing dirty/untracked roadmap/evidence files plus Plan 1 changes.

## Expected Output

- Existing target implementation prompts produce a serialized TaskSpec intake before model execution.
- Bounded create prompts produce disposable-workspace create intake.
- Vague implementation/create prompts require clarification instead of advisory fallthrough.
- Protected paths are blocked before coder/model work and do not produce allowed files.
- Prompt-packet responses expose TaskSpec intake fields in both snake_case and camelCase.

## Forbidden Scope Avoided

- No Plan 2 tool/action contract parser.
- No Plan 3 executor.
- No provider/model calls.
- No benchmark/stress reruns.
- No safe apply.
- No real app mutation from trial prompts.
- No hidden scaffolding or backend-authored task files.
- No Cartographer mutation.
- No hidden workers.
- No package/config/CSS/provider-routing edits.
- No branch, worktree, stash, reset, checkout, clean, stage, commit, or push.

## Blockers

None for Plan 1. Plan 2 must not start until Britton approves it.

## Rollback Guidance

Rollback by reverting only the Plan 1 files listed above. Preserve unrelated dirty tree work and historical evidence.

## GO/NO-GO

GO for Plan 1 closeout.

NO-GO for Plan 2 start without Britton approval.

Next plan title only:

`Plan 2/8: Tool/Action Contract And Parser`
