# Source Proxy Tool Action Runtime v1 Plan 6 Evidence

Plan: Plan 6/8: /coding UI Integration For TaskSpec, Actions, Diffs, And Receipts.

Status: implemented and verified with automated UI, TypeScript, backend regression, and compile checks.

## Phase 6.1 Intake Panel

Implemented:

- `src/lib/coding/tool-runtime-surface.ts`
  - Builds a display-only Source Proxy tool runtime surface from TaskSpec intake data.
  - Exposes task kind, clarification state, model lane, workspace mode, allowed files, exposed tools, write scope, Mac/subagent advisory truth, and Source Proxy final-gate truth.
- `src/components/coding/CodingCommandCenterShell.tsx`
  - Adds a visible `Source Proxy Tool Runtime` section to `/coding`.
  - Shows TaskSpec fields and capability truth without adding execution controls.

Evidence:

- Unit test verifies TaskSpec display fields and tool truth.
- UI test verifies the runtime section renders and has no apply button.

GO/NO-GO: GO.

## Phase 6.2 Action Transcript Panel

Implemented:

- The runtime surface maps parsed actions and execution results into display rows.
- The `/coding` runtime section shows action type, status, target, adapter source, and blocked reason.
- Empty UI states explicitly say no model-authored tool actions are recorded.

Evidence:

- Unit test verifies action transcript data from parsed action and execution payloads.
- UI test verifies the Action Transcript panel is present while no unsafe controls appear.

GO/NO-GO: GO.

## Phase 6.3 Diff And Review Panel

Implemented:

- The runtime surface extracts files touched, diff summary, and check output.
- The `/coding` runtime section shows files touched, diff summary, check output, and safe-apply status.
- Safe apply remains display-only and blocked unless separately approved.

Evidence:

- Unit test verifies disposable diff, file list, and check output are surfaced.
- UI test verifies `Safe apply: blocked unless separately approved`.

GO/NO-GO: GO.

## Phase 6.4 Copy Diagnostics

Implemented:

- `toolRuntimeDiagnosticsText(...)` creates copyable diagnostics with:
  - TaskSpec fields.
  - Exposed tools.
  - Actions attempted.
  - Blocked reasons.
  - Files touched.
  - Diff summary.
  - Check output.
  - Safe apply blocked status.
  - Mac/subagent advisory truth.
  - Source Proxy final gate.
- `/coding` receipt text now includes the Source Proxy tool runtime diagnostics block.

Evidence:

- Unit test verifies diagnostics include blocked reasons and Mac/subagent references.
- Receipt-copy test verifies copied proof text includes `Source Proxy tool runtime diagnostics`, safe apply blocked status, and Mac/subagent advisory truth.

GO/NO-GO: GO.

## Live UI Smoke

Attempted:

```powershell
ssh source@10.0.0.186 'curl -fsS http://127.0.0.1:3000/coding >/tmp/plan6-coding-page.html && echo RUNNING || echo NOT_RUNNING'
ssh source@10.0.0.186 'cd /home/source/SpiritOS && (nohup npm run dev -- -H 0.0.0.0 -p 3016 >/tmp/spiritos-plan6-devserver.log 2>&1 & echo $!)'
ssh source@10.0.0.186 'for i in $(seq 1 30); do if curl -fsS http://127.0.0.1:3016/coding >/tmp/plan6-coding-page.html; then echo READY; exit 0; fi; sleep 1; done; echo NOT_READY; tail -80 /tmp/spiritos-plan6-devserver.log; exit 1'
ssh source@10.0.0.186 'curl -i --max-time 10 http://127.0.0.1:3000/coding | sed -n "1,80p"'
```

Result:

- In-app Browser control tool was not exposed in this thread.
- Existing Next dev server PID `2426036` was already registered on port `3000` but returned `Empty reply from server` for `/coding`.
- Temporary sidecar server on `3016` exited because Next reported another dev server already running for `/home/source/SpiritOS`.
- The temporary PID `2447045` was no longer running after the failed sidecar attempt.
- Existing PID `2426036` was not killed or interrupted.

GO/NO-GO: NO-GO for live browser smoke only. GO for Plan 6 automated UI/runtime verification.

## Checks

Executed from `Z:\` PowerShell against `/home/source/SpiritOS`:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm exec vitest -- run src/lib/coding/__tests__/tool-runtime-surface.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm exec tsc -- --noEmit --pretty false"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or bounded_agent_loop or advisory'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_actions.py source_proxy/decision/tool_action_executor.py source_proxy/decision/tool_action_loop.py source_proxy/decision/advisory_broker.py"
```

Results:

- Plan 6 frontend/runtime suite: `78 passed`.
- TypeScript: passed.
- Plan 1-5 backend regression selected slice: `26 passed, 63 deselected`.
- `py_compile`: passed on Dell.

Final combined checks are recorded in the Plan 6 closeout.

## Forbidden Scope Avoided

- No Plan 7 trap suite or golden tasks.
- No safe apply to the real repo.
- No apply button or new unsafe UI control.
- No provider/model calls.
- No benchmark or stress tests.
- No Cartographer mutation.
- No Mac/subagent write authority.
- No hidden workers left running from Plan 6 verification.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.
