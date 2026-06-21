# Harness Evidence Validation

## Smoke input

```text
prompt_id: STAGE3_SMOKE_NOT_BATTERY
counts_toward_3x10: false
prompt: stage 3 harness smoke: create a harmless operator receipt for current source proxy status
```

This smoke was not Set A, Set B, Set C, or a 3x10 battery prompt.

## Smoke execution

Command class: Python harness readback using the repo source-proxy venv.

The first attempt with system `python3` failed because `httpx` was missing. The successful run used:

```text
.venv-source-proxy/bin/python
SOURCE_PROXY_LONG_RUNNING_TASKS_DB=/home/source/spiritos-evidence/plan-03-3x10-dryrun/stage-3/stage3-smoke-tasks.sqlite3
SPIRIT_PROJECT_PATH=/home/source/SpiritOS
```

Using an isolated evidence DB avoided polluting the live task queue while still calling real Source Proxy decision, task, durable-state, policy, and consumer-evidence code.

## Captured grading fields

Captured from the smoke record:

```text
task_id: task_853c5e83eeba
trace_id: trace_6643706c87744657
final_status: blocked_human
work_product_type: operator_receipt_smoke
required_lanes: decision_router, task_spec_intake, long_running_task_store, plan3_policy_gate, same_trace_consumer_readback
lanes_invoked: decision_router, task_spec_intake, long_running_task_store, plan3_policy_gate, same_trace_consumer_readback
lanes_not_required: live_search, mac_worker, qwen_coder, browser_functional_verifier, repair_loop
internet_required: false
live_search_used: false
local_fallback_used: false
research_materially_changed_output: false
mac_required: false
mac_invoked: false
qwen_required: false
qwen_activated: false
verifier_required: false
verification_result: not_required_for_smoke
repair_required: false
repair_applied: false
reverified: false
policy_event_required: true
policy_event_present: true
recovery_required: false
recovery_event_present: false
latest_consumer_event_id: consumer_bd9dce4bea844197
consumer_subsystem: source_proxy_plan3_policy_acceptance_consumer
downstream_consumed: true
same_trace_consumer_evidence: true
limitations_stated: true
handoff_or_context_prompt_created_when_useful: false
recommendation_pack_created_when_useful: false
failure_changed_outcome: false
fake_go_detected: false
safety_violation_detected: false
jellyfin_or_media_mutation_detected: false
patch_required: false
patch_bucket: none
auto_fix_attempts: 0
max_auto_fix_attempts: 3
```

Machine-readable record:

```text
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/stage-3/stage3-smoke-grading-record.json
```

Raw evidence copy:

```text
/home/source/spiritos-evidence/plan-03-3x10-dryrun/stage-3/stage3-smoke-grading-record.json
```

## Limitations

This smoke validated evidence capture and same-trace consumer readback only. It did not run live internet research, Mac worker, Qwen coder, verifier, or repair. Future Stage 4+ prompts must invoke those lanes when required by the battery expectations or mark an honest blocker/failure.
