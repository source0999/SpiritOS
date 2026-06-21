# Harness Selection

## Selected harness path

Selected canonical harness for future 3x10 execution:

```text
decision intake -> Plan 3 durable long-running task -> task readback/grading record

source_proxy.decision.router.decide_route
source_proxy.decision.task_spec_intake.build_task_spec_intake
source_proxy.tasks.durable_execution.create_plan3_durable_task
source_proxy.tasks.long_running.get_long_running_task / get_long_running_task_snapshot
source_proxy.tasks.durable_execution.apply_plan3_policy / recover_plan3_task / run_plan3_verifier_driven_repair when required
source_proxy.tasks.durable_execution.record_plan3_consumer_evidence / require_plan3_acceptance_evidence
```

The API-facing task entry is:

```text
POST /v1/tasks/long-running
GET /v1/tasks/long-running/{task_id}
GET /v1/tasks/long-running/{task_id}/stream
POST /v1/tasks/long-running/{task_id}/advance
POST /v1/tasks/long-running/{task_id}/verification
```

The Plan 3 durable wrapper is selected for Stage 4+ battery accounting because the plain task create path alone does not guarantee `trace_id`, `invocation_event_id`, same-trace `consumer_event_id`, or Plan 3 policy/recovery/repair evidence.

## Why it is canonical enough

This harness reuses the existing decision router, task-spec intake, long-running task store, causal trace event append/readback, and Plan 3 durable policy/recovery/repair gates. It does not create a new task engine, fake lane engine, fake evaluator, or local grep-only scorer.

## Real paths called

- Routing/lane classification: `source_proxy/decision/router.py`
- Task-spec normalization: `source_proxy/decision/task_spec_intake.py`
- Durable task creation and task ID: `source_proxy/tasks/long_running.py`
- Plan 3 state and causal evidence: `source_proxy/tasks/durable_execution.py`
- Task readback: `source_proxy/tasks/long_running.py`
- FastAPI route surface: `source_proxy/api/long_running_tasks.py`
- Next proxy surface: `src/app/v1/tasks/long-running/**`

## Evidence fields it can produce

Directly available from selected path:

```text
task_id
trace_id
final_status
invocation_event_id
latest_consumer_event_id
consumer_subsystem
downstream_consumed
same_trace_consumer_evidence
policy_event_present
recovery_event_present
repair_applied
reverified
auto_fix_attempts
max_auto_fix_attempts
fake_go_detected
patch_required
patch_bucket
notes
```

Available by combining decision/task-spec/lane readback:

```text
work_product_type
required_lanes
lanes_invoked
lanes_not_required
internet_required
live_search_used
local_fallback_used
research_materially_changed_output
mac_required
mac_invoked
qwen_required
qwen_activated
verifier_required
verification_result
limitations_stated
handoff_or_context_prompt_created_when_useful
recommendation_pack_created_when_useful
failure_changed_outcome
safety_violation_detected
jellyfin_or_media_mutation_detected
```

## Missing fields and limits

No single existing route emits the whole 3x10 grading schema as one normalized JSON record. Stage 3 therefore selects the existing canonical workflow and records a readback-normalized grading record outside the runtime path.

Future Stage 4+ still must prove prompt-specific lanes honestly:

- Live-search prompts must use real current research or mark `BLOCKED_ENV`.
- Mac-required prompts must invoke Mac worker or mark `BLOCKED_ENV`; Dell fallback cannot count as Mac.
- Code prompts must activate Qwen/coder/verifier as required or mark failure/blocker.
- Preview/advisory verifier output cannot be counted as PASS.

## Adaptation needed

No source code adaptation is needed in Stage 3. The only adaptation is a documentation-level harness selection and a grading-record normalization recipe based on real task readback.

## Explicitly not used

- No route preview as PASS.
- No advisory-only Mac route as PASS.
- No local repo grep as internet proof.
- No fabricated task IDs, trace IDs, lane outputs, or consumer events.
- No Set A/B/C prompt.
- No new dry-run engine or parallel event/state framework.
