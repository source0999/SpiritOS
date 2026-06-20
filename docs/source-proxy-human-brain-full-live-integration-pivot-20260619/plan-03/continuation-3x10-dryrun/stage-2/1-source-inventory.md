# Source Inventory

## Policy Events

- Emitted by `apply_plan3_policy` in `source_proxy/tasks/durable_execution.py` using the existing `_append_causal_event(..., event_type="policy")` long-running task trace.
- Stage 2 now stores `blocked_action`, `mutation_prevented`, `latest_policy_event_id`, then records a same-trace consumer event for blocked policy proofs.

## Recovery Events

- Emitted by `recover_plan3_task` using existing `event_type="recovery"`.
- Stage 2 preserves `duplicate_action_prevented=true`, `latest_recovery_event_id`, and records a same-trace consumer event.

## Repair Events

- Emitted by `run_plan3_verifier_driven_repair`.
- Stage 2 changes the pre-repair verifier miss into an explicit `event_type="failure"` with `latest_repair_failure_event_id`, then records repair, reverify, final status, and same-trace consumer evidence.

## Consumer Fields

- `latest_consumer_event_id`: now populated by `record_plan3_consumer_evidence`.
- `consumer_event_id`: mirrors the latest consumer event required by operator checks.
- `consumer_subsystem`: populated with the proof-specific Plan 3 acceptance consumer.

## Previously Missing Evidence

- Policy and recovery proofs previously passed without consumer events.
- Repair proof previously had repair/reverify but no explicit failure event and no consumer event.
- The operator previously accepted artifact booleans/statuses without checking same-trace consumer evidence.
