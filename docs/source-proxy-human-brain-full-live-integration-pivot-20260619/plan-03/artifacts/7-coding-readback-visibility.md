# Stage 7 Coding And Task Readback Visibility

Result: `INTEGRATED_LIVE` through task readback.

Surface:
- `GET /v1/tasks/long-running/{task_id}`
- payload field: `task.plan_3_durable_state`

Visible fields:
- `current_status`
- `previous_status`
- `attempt_count`
- `policy_decision`
- `blocked_reason`
- `last_error`
- `recovery_marker`
- `repair_attempt_count`
- `trace_id`
- `latest_invocation_event_id`
- `latest_consumer_event_id`
- `verification_result`
- `repair_result`
- `causal_events_json`

Frontend note:
- `CodingCockpitShell` was not patched because backend task readback now surfaces all required Plan 3 fields without replacing or forking the canonical `/coding` route.
