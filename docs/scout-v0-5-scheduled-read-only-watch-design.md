# Scout v0.5 Phase 2.1 Scheduled Read-Only Watch Design

status: design/manual-controlled

Status date: 2026-05-20

This document designs Level 2 scheduled read-only watch for Scout. It does not implement a scheduler, register a worker, add cron, change services, write snapshots automatically, run search, extract candidates, approve sources, reject sources, block sources, activate sources, promote packets, write proxy memory, write coding context, apply code, commit, or push.

## Current Gate

Level 1 Auto-Rank is live and visible:

- `scout-level-1-soak` result: `pass`
- `mutated`: `false`
- candidate rank field counts: `18, 18, 18`
- packet rank field counts: `42, 42, 42`
- `rank_fields_visible`: `true`
- warnings: none
- source count: `7`
- pollable sources: `5`
- stored-only sources: `2`
- candidate counts: `approved 4`, `recommended 10`, `needs_review 2`, `rejected 1`, `blocked 1`, `stored 0`
- discovery execution: `manual_controlled`
- `automatic_execution`: `false`
- `worker_registered`: `false`
- promotion queue: `0`
- backlog: `0`

Phase 2.1 may design scheduled watch only because Level 1 is visible and still read-only.

## Level 2 Boundary

Level 2 may do only scheduled diagnostics and evidence snapshots after explicit approval.

Forbidden in Level 2:

- automatic candidate extraction
- automatic discovery execution
- source activation
- source approval
- source rejection
- source blocking
- packet promotion
- proxy memory writes
- coding context writes
- apply actions
- commits
- pushes
- service changes without a named operator gate
- hidden background workers
- scheduled writes before approval
- self-promotion to Level 3 or higher

## Scheduler Shape

The future scheduler should be a disabled-by-default read-only observer.

- Default state: disabled.
- Registration: no worker is registered in Phase 2.1.
- Trigger: manual operator command first, then explicit scheduler approval in a later increment.
- Cadence proposal: every 30 minutes while enabled.
- Jitter proposal: 0 to 120 seconds to avoid sharp service edges.
- Timeout proposal: 30 seconds per endpoint group.
- Concurrency: one watch run at a time.
- Locking: skip a run if the previous read-only watch is still active.
- Kill switch: one environment flag must disable all scheduled watch execution.
- Output: evidence summary only.

No implementation is authorized by this document.

## Read Set

Scheduled watch may read only:

- `/health`
- `/v1/scout/overview?limit=5`
- `/v1/scout/sources`
- `/v1/scout/source-candidates?limit=200`
- `/v1/scout/discovery-jobs?limit=50`
- `/v1/scout/packets/explorer?limit=100`
- recent Scout container logs for diagnostics only
- Scout DB file size metadata

It must not call POST, PATCH, PUT, DELETE, approval, rejection, block, activation, extraction, promotion, memory, coding context, apply, commit, or push endpoints.

## Evidence Snapshot Shape

The future evidence payload should include:

- timestamp
- runner profile name
- health status
- packet synthesis state
- backlog counts
- source count
- pollable source count
- stored-only source count
- candidate counts
- discovery job count
- discovery execution state
- `automatic_execution`
- `worker_registered`
- promotion queue count
- candidate rank field count
- packet rank field count
- warning list
- mutation boundary verdict
- next recommended operator action

The evidence payload must not contain secrets, raw large packet bodies, or full logs.

## Retention

Proposed retention after implementation approval:

- Keep latest 48 snapshots by default.
- Keep only summaries, not raw packet payloads.
- Allow manual deletion of old evidence logs.
- Do not prune anything until retention behavior has its own test.

## Implementation Notes For Later

Likely files if approved later:

- `source_proxy/testing/runner.py` for a manual read-only profile extension.
- Scout docs for the operational contract.
- Optional UI readout only after the runner profile is stable.

Do not add a service worker, cron entry, background loop, compose change, or process supervisor in Phase 2.1.

## Acceptance Criteria For Future Implementation

Before Level 2 can be considered active:

- Level 1 soak still passes.
- Rank fields remain visible.
- A manual watch run reads only allowed endpoints.
- No source count changes.
- No candidate count changes unless caused by an explicit manual operator action.
- Discovery execution remains `manual_controlled`.
- `automatic_execution` remains `false`.
- `worker_registered` remains `false`.
- Promotion queue remains unchanged.
- Proxy memory writes remain off.
- Coding context writes remain off.
- The scheduler is disabled by default.
- The scheduler cannot self-enable.
- Tests prove no mutation endpoints are called.

## Rollback

This phase is docs-only. Roll back with:

```bash
git restore docs/scout-v0-5-scheduled-read-only-watch-design.md
```

If the file is untracked, use:

```bash
rm docs/scout-v0-5-scheduled-read-only-watch-design.md
```

## Next Permission Gate

Operator approval is required before implementing Phase 2.2. The recommended next increment is a manual evidence snapshot review design or runner extension that remains disabled by default and read-only.
