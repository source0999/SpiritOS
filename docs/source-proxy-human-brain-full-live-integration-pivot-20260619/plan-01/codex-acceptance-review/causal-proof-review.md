# Causal Proof Review

## Source Verification

Current source confirms the causal seam is on the decision-bearing long-running apply path:

- `source_proxy/tasks/long_running.py` defines `execute_approved_long_running_task`.
- The function creates an `invocation` event with `trace_id`, `approval_id`, `run_id`, and `status_before` before `central_gate_check("apply", run_id=...)`.
- `central_gate_check("apply", run_id=...)` still runs before approval-id validation, diff verification, and workspace apply.
- Central-gate failure records a `failure` event and marks the task `failed_needs_human`.
- Successful apply records `status_transition` events.
- `_record_long_running_status_observer_consumer` records a durable backend `consumer` event when task readback consumes applied or failed status.
- `causal_events_json` is persisted in the existing `long_running_tasks` table.

Current source confirms shell visibility:

- `CodingCockpitShell.tsx` parses `causal_trace` and execute-approved trace fields through `causalTraceFromPayload`.
- The review pane renders `trace_id`, `invocation_event_id`, `consumer_event_id`, `consumer_subsystem`, and `status_after` in a `Causal trace` block.

Current source confirms `/v1/decisions/route` remains advisory-only:

- `source_proxy/api/decision.py` `/route` returns route decision payload only.
- `src/app/v1/decisions/route/route.ts` proxies `/v1/decisions/route` and returns a response body.
- The route is not merged into `execute_approved_long_running_task`.

## Artifact Review

All required Plan 1 artifacts are present:

- `1.1.1-preflight.md`
- `1.1.2-event-storage-decision.md`
- `phase-1.1-closeout.md`
- `phase-1.2-closeout.md`
- `phase-1.3-closeout.md`
- `1.4.2-success-live-proof.md`
- `1.4.3-failure-live-proof.md`
- `1.4.4-causality-audit.md`
- `1.5.1-evidence-budget.md`
- `plan-closeout.md`
- `plan-closeout.json`

The storage decision matches source: existing SQLite task store plus `causal_events_json`.

## Raw Proof Review

External raw evidence exists under `/home/source/spiritos-evidence/plan-01`.

Success proof:

- task_id: `task_4a0815afebd5`
- trace_id: `trace_e7fe171a814143ce`
- invocation_event_id: `invocation_0e2beba826444584`
- consumer_event_id: `consumer_70853e8c04314135`
- consumer_subsystem: `long_running_status_observer`
- status_after: `applied_needs_verification`
- event chain: invocation -> status_transition(executing) -> status_transition(applied_needs_verification) -> consumer

Failure proof:

- task_id: `task_6bf52d9516c7`
- trace_id: `trace_12991e9d6e4c402c`
- invocation_event_id: `invocation_1f965cde5a924b5d`
- consumer_event_id: `consumer_320587cccb9643aa`
- consumer_subsystem: `long_running_status_observer`
- status_after: `failed_needs_human`
- event chain: invocation -> failure -> consumer
- blocked target created: false

The `/mnt/spirit-8tb/spiritos-evidence/plan-01/` permission issue is documented in artifacts and the evidence budget. The fallback raw evidence path is documented.

## Verdict

GO. The causal seam, durable backend consumer proof, and shell visibility are verified from source plus raw evidence.
