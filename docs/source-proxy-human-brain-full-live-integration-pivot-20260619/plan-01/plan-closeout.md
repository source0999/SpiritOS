# Plan 1 Closeout

Verdict: GO

Plan 1 adds a thin causal seam to the existing decision-bearing long-running apply path. It persists invocation, status, failure, and backend consumer events on the existing task record and displays the resulting trace in `CodingCockpitShell`.

Causal proof:

- task_id: `task_4a0815afebd5`
- approval_id: `approval-b58ce2a5f296fb97`
- run_id: `execute_approved_long_running_task:task_4a0815afebd5`
- trace_id: `trace_e7fe171a814143ce`
- invocation_event_id: `invocation_0e2beba826444584`
- consumer_event_id: `consumer_70853e8c04314135`
- consumer_subsystem: `long_running_status_observer`
- status_before: `queued`
- status_after: `applied_needs_verification`
- failure proof: `task_6bf52d9516c7`, `trace_12991e9d6e4c402c`, `failed_needs_human`, blocked target not created

Tests:

- `.venv-source-proxy/bin/python -m pytest -q source_proxy/tests -k "causal or long_running or consumer"`: passed
- `npm run typecheck`: passed
- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t "reads long-running causal trace proof"`: passed

Safety:

- no Obsidian write
- no Mac write
- no authority expansion
- no route replacement
- no new engine/framework
- no push
- no Plan 2 work
