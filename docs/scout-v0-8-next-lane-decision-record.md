# Scout v0.8 Phase 0.1 Next Scout Lane Decision Record

status: planning/manual-controlled

Status date: 2026-05-20

This document records the next Scout lane decision after Scout v0.7 review ergonomics was parked. It is documentation only. It does not implement a new Scout lane, change Scout authority, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, or push.

## Current Parked State

Scout remains parked as a manual-controlled intelligence center.

Latest gate before this record:

- packet backlog: `0`
- packets: `45`
- verdicts: `45`
- packet synthesis: ready
- Scout Level 1 soak: pass
- closeout: pass
- closeout mode: `dry_run_only`
- `read_only: true`
- `mutated: false`
- proxy memory writes: `false`
- coding context writes: `false`
- promotion finalization: `false`

## Decision

Choose **Option A: Stay Parked And Require A Fresh Operator Decision**.

Scout v0.8 does not open new implementation work yet. The correct next step is to choose a lane explicitly before code changes:

- keep Scout parked
- continue read-only review ergonomics
- improve diagnostics and test contracts
- design a future manual-controlled workflow
- defer Scout work and return to another active plan

No option is selected for implementation in this record.

## Options For A Later Decision

### Option A: Stay Parked

Keep Scout as-is.

Allowed:

- docs-only status records
- read-only diagnostics
- manual checks

Forbidden:

- new Scout behavior
- new routes
- UI behavior changes
- database writes
- background workers

### Option B: Read-Only Diagnostics Hardening

Improve test and runner diagnostics without changing Scout behavior.

Possible future increments:

- make closeout summaries easier to scan on mobile
- add stronger assertions for packet backlog and synthesis readiness
- add a compact dirty-tree classifier for Scout-only checks

Forbidden:

- source approval automation
- discovery execution
- candidate extraction
- packet promotion
- proxy memory writes
- coding context writes

### Option C: Read-Only Review Ergonomics

Continue UI clarity work only.

Possible future increments:

- group source candidate evidence more clearly
- group packet evidence more clearly
- improve manual gate labels or empty states

Forbidden:

- new automatic action
- hidden worker
- scheduled write
- promotion finalization
- proxy intake

### Option D: Manual-Controlled Workflow Design

Create a design doc for a future explicit workflow, without implementation.

Possible future increments:

- manual discovery proposal review design
- manual packet promotion review design
- manual import dry-run review design

Forbidden:

- route implementation
- database mutation
- proxy memory writes
- coding context writes

## Safety Boundary

This decision record does not authorize:

- auto-approval
- auto-rejection
- auto-blocking
- auto source activation
- automatic discovery execution
- automatic candidate extraction
- automatic packet promotion
- proxy intake calls
- proxy memory writes
- coding context writes
- active context writes
- append-only evidence writes
- real receipt emission
- promotion finalization
- apply actions
- commits
- pushes
- service changes
- hidden background workers
- scheduled writes
- self-promotion to a higher autonomy level

## Acceptance Criteria

- Scout remains manual-controlled.
- Scout v0.7 remains parked.
- No Scout v0.8 implementation is claimed.
- No source, candidate, discovery, packet, proxy memory, or coding context mutation is introduced.
- Closeout remains green.
- Any next increment requires explicit operator approval.

## Manual Check

`cd /home/source/SpiritOS && grep -n "Scout v0.8 Phase 0.1 Next Scout Lane Decision Record\|Option A: Stay Parked\|proxy memory writes: false\|coding context writes: false\|promotion finalization: false\|Next Permission Gate" docs/scout-v0-8-next-lane-decision-record.md docs/plan-index.md && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'`

Expected outcome:

- decision record exists and is indexed
- `git diff --check` prints nothing
- closeout returns `result: pass`
- `read_only: true`
- `mutated: false`
- `ready: true`
- `mode: dry_run_only`
- proxy memory, coding context, and finalization remain `false`
- `unexpected` is empty
- `head_changed` is `false`

## Rollback

```bash
git restore docs/plan-index.md
rm docs/scout-v0-8-next-lane-decision-record.md
```

## Next Permission Gate

Scout v0.8 is not open for implementation. Operator approval is required before selecting or implementing any next Scout lane. The recommended next increment is **Scout v0.8 Phase 0.2: Lane Selection**, docs-only, choosing Option A, B, C, or D.
