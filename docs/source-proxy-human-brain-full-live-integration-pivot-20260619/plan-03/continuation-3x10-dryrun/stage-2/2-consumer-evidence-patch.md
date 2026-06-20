# Consumer Evidence Patch

## Files Changed

- `source_proxy/tasks/durable_execution.py`
- `source_proxy/tests/test_plan3_durable_execution.py`
- `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/operator-check.sh`

## Event Fields Added Or Used

- `blocked_action`
- `mutation_prevented`
- `latest_policy_event_id`
- `latest_recovery_event_id`
- `latest_repair_failure_event_id`
- `latest_repair_event_id`
- `latest_reverify_event_id`
- `latest_consumer_event_id`
- `consumer_event_id`
- `consumer_subsystem`
- `max_repair_attempts`

## Same-Trace Guarantee

The patch appends consumer evidence through the existing long-running task `_append_causal_event` path, so the consumer event inherits the task causal trace ID. `require_plan3_acceptance_evidence` rejects a consumer event whose `trace_id` differs from the proof state's `trace_id`.

## Missing Evidence Failure

`require_plan3_acceptance_evidence` fails closed for missing policy/recovery/repair preconditions, missing `latest_consumer_event_id`, missing `consumer_event_id`, missing `consumer_subsystem`, different-trace consumers, missing repair failure events, missing repair/reverify events, and missing/unbounded repair attempts.
