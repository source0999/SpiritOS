# Source Proxy Tool Action Runtime v1 Plan 6 Closeout

Plan completed: Plan 6/8: /coding UI Integration For TaskSpec, Actions, Diffs, And Receipts.

## Files Changed

- `src/lib/coding/tool-runtime-surface.ts`
- `src/lib/coding/__tests__/tool-runtime-surface.test.ts`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-6/plan-6-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-6/plan-6-closeout.md`

## Evidence Created

- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-6/plan-6-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-6/plan-6-closeout.md`

## Increment Results

- Increment 6.1.1 TaskSpec field display: GO. `/coding` shows task kind, clarification state, model lane, workspace mode, and allowed files.
- Increment 6.1.2 Tool capability truth display: GO. `/coding` shows exposed tools, disposable workspace write scope, Mac/subagent advisory-only truth, and Source Proxy final-gate truth.
- Increment 6.2.1 Action transcript display: GO. `/coding` shows parsed model-authored action rows with validation/execution status, target, adapter, and blocked reason.
- Increment 6.2.2 Check output display: GO. `/coding` shows check output from the runtime surface.
- Increment 6.3.1 Diff and files display: GO. `/coding` shows disposable workspace diff summary and files touched.
- Increment 6.3.2 Apply remains blocked: GO. Runtime panel and copy diagnostics state safe apply is blocked unless separately approved.
- Increment 6.4.1 Copy diagnostics: GO. Receipt proof text includes TaskSpec, exposed tools, actions attempted, blocked reasons, diff summary, checks, Mac/subagent advisory truth, and Source Proxy final gate.

## Checks Run

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm exec vitest -- run src/lib/coding/__tests__/tool-runtime-surface.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm exec tsc -- --noEmit --pretty false"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or bounded_agent_loop or advisory'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_actions.py source_proxy/decision/tool_action_executor.py source_proxy/decision/tool_action_loop.py source_proxy/decision/advisory_broker.py"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal"
```

Outputs:

- Plan 6 frontend/runtime suite: `78 passed`.
- `tsc --noEmit`: passed on Dell.
- Plan 1-5 backend regression selected slice: `26 passed, 63 deselected`.
- `py_compile`: passed on Dell.
- `git diff --check`: final result recorded by manual verification.
- `git status`: expected dirty tree with previous plan work plus Plan 6 runtime/UI/evidence files.

## Live UI Smoke

NO-GO for live browser smoke only:

- In-app Browser control was not exposed in this thread.
- Existing Next dev server PID `2426036` on port `3000` returned `Empty reply from server` for `/coding`.
- A temporary verification server on port `3016` could not start because Next detected the existing repo dev server.
- The temporary verification PID `2447045` exited and was not left running.
- The existing server PID `2426036` was not killed or interrupted.

## Expected Output

- `/coding` exposes a visible Source Proxy Tool Runtime panel.
- The panel shows TaskSpec intake, action transcript, disposable diff/check output, and tool/advisory truth.
- Receipt copy text includes Source Proxy tool runtime diagnostics.
- Safe apply remains blocked unless separately approved.
- Mac/subagents remain advisory-only and Source Proxy remains the final gate.

## Manual Verification

Copy-paste terminal verification block:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm exec vitest -- run src/lib/coding/__tests__/tool-runtime-surface.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm exec tsc -- --noEmit --pretty false"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or bounded_agent_loop or advisory'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_actions.py source_proxy/decision/tool_action_executor.py source_proxy/decision/tool_action_loop.py source_proxy/decision/advisory_broker.py"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && curl -i --max-time 10 http://127.0.0.1:3000/coding | sed -n '1,80p'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal"
```

## Forbidden Scope Avoided

- No Plan 7 trap suite or golden tasks.
- No safe apply to the real repo.
- No new unsafe apply control.
- No provider/model calls.
- No benchmark or stress tests.
- No Cartographer mutation.
- No Mac/subagent write authority.
- No hidden workers left running.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.

## Blockers

- Live browser smoke is blocked by this thread lacking Browser control and by the pre-existing Next dev server on port `3000` returning an empty reply for `/coding`.

## Rollback Guidance

Rollback by removing only the Plan 6 files listed above and the Plan 6 test additions. Preserve unrelated dirty tree work and Plan 0/1/2/3/4/5 artifacts.

## GO/NO-GO

GO for Plan 6 automated UI/runtime closeout.

NO-GO for live browser smoke until the existing dev server is restarted or made healthy by an explicitly approved follow-up.

NO-GO for Plan 7 start in this turn.

Next plan title only:

`Plan 7/8: Trap Suite, Golden Tasks, And Safety Verification`
