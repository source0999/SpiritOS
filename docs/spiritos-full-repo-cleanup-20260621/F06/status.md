# F06 Status

**Stage:** F06 — Split long-running responsibilities
**Status:** NOT_STARTED · **Verdict:** (pending) · **Depends on:** F01 (F05 preferred)

## Frozen artifacts
- `acceptance-contract.json` — frozen (5 responsibilities, 7 gates, state-machine preserved).
- `holdout-manifest.json` — frozen (6 behavior-invariant checks).

## Baseline
`long_running.py` = 6,513 lines; `test_long_running_tasks` + `test_diff_verification` green set.

## Increments
- 6.1 — extract apply/ (git-apply + next-router) + parity
- 6.2 — extract trace/ + recovery/ (idempotence + dup protection)
- 6.3 — extract regression/ + slim engine

## Gate results / Caveats
(populated during execution)
