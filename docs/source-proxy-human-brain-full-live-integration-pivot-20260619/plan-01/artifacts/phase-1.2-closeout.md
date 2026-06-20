# Phase 1.2 Closeout

Delivered:

- `execute_approved_long_running_task` now creates an `invocation` event before the apply gate executes.
- Invocation events include `trace_id`, `invocation_event_id`, `task_id`, `approval_id`, `run_id`, `status_before`, and subsystem `source_proxy_long_running`.
- Central-gate failure creates a `failure` event with the same trace and marks the task `failed_needs_human`.
- Status changes create `status_transition` events.
- Task readback exposes bounded `causal_events` and summary `causal_trace`.

Guardrails:

- `/v1/decisions/route` remains advisory.
- `central_gate_check` remains fail-closed.
- No advisory route was merged into apply.

Verdict: GO
