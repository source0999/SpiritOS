# Canonical State And Event Contract

Plan 0 must adapt existing state machinery before building anything new. Candidate reuse anchors: `source_proxy/tasks/long_running.py`, `source_proxy/cartographer/workflow_state.py`, `source_proxy/cartographer/workflow_event_ledger.py`, `src/lib/coding/durable-run-store.ts`, and receipt/trace routes under `src/app/v1/decisions/fip0-receipts`.

Minimum task state: `task_id`, `trace_id`, `user_prompt`, `task_class`, `risk_tier`, `approval_state`, `canonical_route`, `brain_stage_statuses`, `required_subsystems`, `subsystem_invocations`, `subsystem_outputs`, `downstream_consumptions`, `effects`, `verification`, `repair`, `productive_truth`, `memory_writeback`, `final_verdict`.

Minimum event: `event_id`, `task_id`, `trace_id`, `parent_event_id`, `brain_stage`, `subsystem`, `event_type`, `input_hash`, `output_hash`, `authority`, `status`, `consumer_event_id`, `state_fields_changed`, and `external_evidence_refs`.
