# F06 — Split Long-Running Responsibilities

## Goal
`source_proxy/tasks/long_running.py` (6,513 lines, confirmed) → an engine module
plus cohesive `apply/`, `trace/`, `recovery/`, `regression/` responsibility
modules. **Do not rewrite the state machine.**

## Why
A 6,513-line file mixing engine, apply, trace, recovery, and regression is the
second concentration risk (after decision.py). Cohesive split makes apply
authority and recovery idempotence independently testable.

## Dependencies
**F1** (hard): long-running failure events in traces must use F1 classes.
**F5** (preferred): F5 stabilizes the decision/receipt surface F6 consumes.

## Responsibilities (split by these, not line count)
- **engine** — state transitions, task lifecycle
- **apply/** — git-apply + next-router helpers
- **trace/** — causal event emission
- **recovery/** — idempotent recovery, duplicate-action protection
- **regression/** — regression guards

## Increments (≤12 source files each)
1. **6.1** — extract `apply/` (git-apply + next-router helpers) with parity proof;
   `test_long_running_tasks` + `test_diff_verification` stay green.
2. **6.2** — extract `trace/` + `recovery/` (idempotence + duplicate-action
   protection preserved).
3. **6.3** — extract `regression/`; slim engine to pure state-machine.

## Preserve (compatibility — immutable)
transitions; apply authority; recovery idempotence; duplicate-action protection;
causal ordering; consumer semantics; operator readback.

## Invariants
- No state-machine rewrite — behavior identical.
- Apply behavior (what applies, how it reports, how it fails) unchanged; timing
  tolerances documented, material regressions = NEEDS_FIX.
- Same copy→parity→switch→retire discipline as F5.

## Stop conditions
- Apply behavior changes → NEEDS_FIX.
- Recovery idempotence or duplicate-action protection regresses → NEEDS_FIX.
- Parity fails after ≤3 repairs → NEEDS_FIX.

## Rollback
Re-import from long_running.py (or re-point). Each increment independently
reversible.

## Approval
Britton. Codex reviews apply/recovery parity.
