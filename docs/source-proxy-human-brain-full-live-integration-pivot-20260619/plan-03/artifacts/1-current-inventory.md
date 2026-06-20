# Stage 1 Current Inventory

Durable task store: `PARTIAL` before Plan 3, now extended. Existing `source_proxy/tasks/long_running.py` already persisted task records and causal events to SQLite.

Policy gate: `PARTIAL` before Plan 3. Existing `source_proxy/approval/external_gate.py` guarded model/apply paths, but Plan 3 needed action-class policy decisions persisted on task state.

Retry system: `PARTIAL` before Plan 3. Existing task loop bounded swarm cycles; Plan 3 added explicit failure classes and attempt readback.

Timeout handling: `PARTIAL` before Plan 3. Existing lanes had timeout diagnostics; Plan 3 added `model_timeout` as a persisted failure class.

Recovery/resume: `MISSING` before Plan 3. Plan 3 added recovery markers and causal recovery events on persisted in-flight state.

Repair loop: `PARTIAL` before Plan 3. Existing artifact repair loop could apply safe workspace changes; Plan 3 added verifier-triggered repair proof into durable task state.

Verifier integration: `PARTIAL` before Plan 3. Existing verifier lanes existed; Plan 3 added repair re-verification state and causal verification events.

Rollback/cleanup: `PARTIAL`. Plan 3 proof uses a disposable temp workspace and records no production mutation.

Operator visibility: `PARTIAL` before Plan 3, now `LIVE_AND_TESTED` for task readback. `/v1/tasks/long-running/{task_id}` exposes `plan_3_durable_state`.

Active `/coding` visibility: `STATUS_ONLY` for direct UI labels in this increment. Backend task readback exposes required fields without replacing the canonical `/coding` route.
