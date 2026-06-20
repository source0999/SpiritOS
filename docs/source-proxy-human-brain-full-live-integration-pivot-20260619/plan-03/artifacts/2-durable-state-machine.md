# Stage 2 Durable State Machine

Result: `INTEGRATED_LIVE`.

Implementation:
- added `source_proxy/tasks/durable_execution.py`
- reused the existing SQLite-backed long-running task store
- exposed Plan 3 readback through `plan_3_durable_state` on task payloads
- fixed trace allocation so persisted state and causal events share the same `trace_id`

Persisted fields include:
- `task_id`
- `trace_id`
- `run_id`
- `approval_id`
- `current_status`
- `previous_status`
- `attempt_count`
- `max_attempts`
- `last_error`
- `blocked_reason`
- `policy_decision`
- `recovery_marker`
- `repair_attempt_count`
- `causal_events_json`
- `created_at`
- `updated_at`

Test proof:
- `python -m pytest -q source_proxy\tests\test_plan3_durable_execution.py`
- result: `6 passed`

Covered assertions:
- status transitions persist
- invalid transition rejected
- terminal status cannot silently revert
- causal event emitted for status transition
- task readback exposes durable state
