# Codex Plan 3 Acceptance Review

Final verdict: NEEDS_FIX.

Commit reviewed:
- `4c553554 Implement Plan 3 durable execution and repair`

Scope:
- Source diff scope is clean for Plan 3.
- No Plan 4, media, Jellyfin, Mac, route, service, framework, stage, commit, or push action was performed during this review.

What passes:
- Commit scope is Plan 3-specific.
- Plan 3 focused tests pass.
- Plan 2 hardline and subsystem carryforward tests pass.
- Typecheck passes.
- Plan 3 operator passes.
- Retry/failure terminal path includes downstream consumer evidence.
- Durable state, retry, recovery, policy, and repair mechanisms are implemented as real code rather than documentation-only placeholders.

What blocks GO:
- Task A policy proof is persisted and blocked, but has no consumer event and no `latest_consumer_event_id`.
- Task B recovery proof is persisted, but has no consumer event and no `latest_consumer_event_id`.
- Task C repair proof shows verification failure reason, repair, and reverify, but has no explicit `failure` event and no consumer event.
- The Plan 3 operator passes despite those missing acceptance-critical events.
- The broad requested selector failed in the current environment due an ambient gate mismatch.

Acceptance rationale:
- The acceptance request requires live, durable, traced, consumed output.
- Persisted status and durable events are not enough when the output is not demonstrably consumed downstream.
- Repair cannot be accepted as the requested failure-repair-reverify-consumer trace when failure is not represented as a failure event and consumer evidence is absent.

Required fixes before GO:
- Add or invoke Plan 3 downstream consumer causal events for policy, recovery, and repair terminal outputs.
- Ensure `latest_consumer_event_id` is populated in raw proof for Task A, Task B, and Task C where consumption is required.
- Represent verifier failure before repair as an explicit failure/hardline-equivalent event in the Task C trace.
- Harden operator checks and tests so missing consumer/failure proof fails.
- Refresh raw proof and acceptance artifacts after fixes.

Plan 4 readiness:
- NOT READY. Stop at Plan 3 fixes.
