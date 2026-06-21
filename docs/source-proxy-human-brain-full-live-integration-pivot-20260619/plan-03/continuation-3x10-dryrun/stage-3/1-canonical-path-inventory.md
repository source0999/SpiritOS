# Canonical Path Inventory

## Discovery notes

The requested `rg` inventory command could not run because `rg` was not on the remote PATH in the noninteractive SSH shell. Raw evidence was written to `/home/source/spiritos-evidence/plan-03-3x10-dryrun/stage-3/inventory-rg.txt` and contains the shell error. I used the requested `find` probes plus direct inspection of the likely files.

## Canonical intake and task paths

Canonical user/task intake path:

- FastAPI task API: `source_proxy/api/long_running_tasks.py`
- Next proxy route: `src/app/v1/tasks/long-running/route.ts`
- Internal task store: `source_proxy/tasks/long_running.py`
- Decision/task-spec intake: `source_proxy/decision/router.py` and `source_proxy/decision/task_spec_intake.py`
- Plan 3 durable state wrapper: `source_proxy/tasks/durable_execution.py`

Route that creates `task_id`:

- `POST /v1/tasks/long-running` calls `create_long_running_task`.
- `create_long_running_task` creates `LongRunningTask(id="task_<uuid>")`, persists it, and returns the task envelope.
- `create_plan3_durable_task` calls `create_long_running_task`, then adds Plan 3 durable state and causal invocation evidence.

Route/handler that performs routing/lane selection:

- `source_proxy/decision/router.py` performs route classification through `decide_route`.
- `source_proxy/decision/task_spec_intake.py` normalizes task kind, workspace mode, targets, protected paths, model lane, verification policy, and reason codes.
- Long-running task advancement uses `_run_architect_handoff`, `_run_coder_handoff`, and `_run_debugger_handoff`.
- Worker lane readback is exposed by `_worker_lanes_for_task`.

Path that produces `trace_id`:

- `source_proxy/tasks/long_running.py::_ensure_causal_trace_id`.
- Plan 3 wrapper calls this during `create_plan3_durable_task`.

Path that records `invocation_event_id`:

- `source_proxy/tasks/long_running.py::_append_causal_event` records causal events.
- `source_proxy/tasks/durable_execution.py::create_plan3_durable_task` records the Plan 3 invocation event and stores `latest_invocation_event_id`.

Path that records `consumer_event_id` and downstream consumption:

- `source_proxy/tasks/durable_execution.py::record_plan3_consumer_evidence` records a same-trace consumer event, sets `latest_consumer_event_id`, `consumer_event_id`, and `consumer_subsystem`, then revalidates the evidence.
- `source_proxy/tasks/long_running.py::_causal_trace_summary` exposes `consumer_event_id` and `consumer_subsystem` in task readback.

Research path:

- `source_proxy/decision/current_research.py::run_current_research_for_task`.
- `source_proxy/decision/research.py` for repo and SearxNG diagnostics.
- `source_proxy/decision/scout_research.py` for Scout research diagnostics.

Mac path:

- `source_proxy/decision/mac_integration.py::run_mac_worker_for_task`.
- Next API surface: `src/app/api/coding/mac-worker/route.ts`.
- Advisory-only path not sufficient for dry-run PASS: `src/app/v1/coding/mac-advisory/route.ts`.

Qwen/model lane path:

- `source_proxy/decision/model_lanes.py` defines Qwen as the primary local coder lane and exposes `run_qwen_coder_lane`.
- `source_proxy/decision/specialist_integration.py` records Qwen and verifier subsystem consumption.

Verifier path:

- `source_proxy/decision/verifier_lane.py`.
- `source_proxy/decision/specialist_integration.py::run_live_specialist_integration_for_task`.
- Long-running post-apply verification path: `record_post_apply_verification`.

Repair/recovery/policy path:

- `source_proxy/tasks/durable_execution.py` contains `apply_plan3_policy`, `recover_plan3_task`, `run_plan3_verifier_driven_repair`, `record_plan3_consumer_evidence`, `require_plan3_acceptance_evidence`, and `plan3_final_go_allowed`.

Existing tests/harnesses that use real paths:

- `source_proxy/tests/test_long_running_tasks.py`
- `source_proxy/tests/test_plan3_durable_execution.py`
- `source_proxy/tests/test_source_proxy_end_to_end.py`
- `source_proxy/tests/test_coding_regression_pack.py`
- Next route tests under `src/app/v1/tasks/long-running/**` and coding route tests.

Preview/advisory paths that must not be used as the canonical battery harness:

- `src/app/v1/actions/preview/route.ts`
- `src/app/v1/coding/*/preview/route.ts`
- `src/app/v1/coding/mac-advisory/route.ts`
- `src/app/v1/verification/*-preview/route.ts`
- Cartographer import/dry-run routes that do not create Source Proxy long-running task state.

Inventory conclusion: a canonical path exists, but it is a composed existing workflow rather than a single all-in-one dry-run command.
