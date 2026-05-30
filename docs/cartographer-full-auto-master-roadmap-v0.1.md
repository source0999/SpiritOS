# Cartographer Full Auto Master Roadmap v0.1

status: planning-only

Status date: 2026-05-22

## Status Metadata

- current state: inert manual-control lane passed
- current `/map` state: static, unwired, no executable controls
- full auto: not granted
- limited unattended operation: not granted
- read-only wiring: denied until explicit future approval
- implementation: not started by this roadmap

## Purpose

This roadmap names the major plans required to move Cartographer from the current inert/manual-control state toward a possible future full-auto operating mode.

This file is a master roadmap only. It does not write the full detailed Plan 1, implement runtime behavior, wire `/map`, create approval token runtime, create durable queue storage, enable command execution, enable write authority, grant limited unattended operation, or grant full auto.

## Current Baseline

Cartographer currently has a dry-run proof stack and a static `/map` manual control surface. The `/map` route is navbar-accessible and Phase 13 final review passed, but the route remains inert, static, and unwired.

The current baseline is:

- Dry-run proof stack exists.
- `/map` manual control surface exists.
- Phase 13 final review passed.
- `/map` has no real data wiring.
- `/map` has no fetch calls.
- `/map` has no backend endpoint calls.
- `/map` has no executable controls.
- Read-only wiring remains denied.
- Cartographer has no execution authority.
- Cartographer has no autonomous action authority.
- Full auto is not granted.
- Limited unattended operation is not granted.

## Missing Or Unread Source Docs

None noted during this roadmap pass. The requested source docs were available for review.

## Full-Auto Principle

Full auto is not one implementation step. It requires staged promotion through smaller operator modes, with each mode proving a narrow increase in authority before any later mode can be planned, approved, or implemented.

Each mode must define:

- exact authority
- allowed files
- forbidden files
- data sources
- rollback
- stop conditions
- manual checks
- proof package
- operator approval

No plan promotes itself. No UI surface, roadmap, recommendation packet, dry-run proof, dashboard state, or previous success grants live authority by implication.

## Main Plans

### Plan 0: Baseline Freeze And Authority Reset

Purpose: confirm the current no-go state, dirty files, protected lanes, `/map` final review, and no full auto.

Must cover later:

- repo state snapshot
- protected lanes
- dirty file classification
- source docs
- current no-go authorities
- rollback baseline
- stop conditions

Plan 0 output should be a freeze packet only. It must not wire `/map`, touch runtime modules, edit tests, clean dirty files, stage changes, or promote any authority.

### Plan 1: Limited Operator v0.1

Purpose: first real read-only `/map` wiring and recommendation packets. No writes. No commands. No approval actions.

Must cover later:

- safe GET-only endpoint list
- timeout behavior
- fallback behavior
- static-to-live data transition
- recommendation packet shape
- blocked action classifier
- operator review packet
- UI display only
- no execution

Plan 1 must be written as a full plan only in a future increment. This roadmap does not write that full plan.

### Plan 2: Human-Approved Operator v0.2

Purpose: human approval queue and approval token validation. Still no self-action.

Must cover later:

- approval token fields
- operator id
- action id
- exact allowed files
- forbidden files
- expiry
- stale HEAD block
- dirty tree block
- self-approval block
- kill switch block
- approval queue display

Plan 2 must not treat an approval queue as execution authority. Approval display and approval validation are separate from action execution.

### Plan 3: Safe Write Operator v0.3

Purpose: first allowed write class only. Start with docs/evidence/receipt writes. No app code. No UI code. No package changes. No commits.

Must cover later:

- allowed write paths
- exact write scope
- preflight checks
- rollback instructions
- post-write verification
- receipt schema
- protected lane barrier

Plan 3 must preserve a narrow write boundary. It must not authorize source code edits, test edits, package/config edits, commits, pushes, merges, branches, worktrees, stash, checkout, clean, or delete operations.

### Plan 4: Verification Operator v0.4

Purpose: controlled verification commands only. No arbitrary shell.

Must cover later:

- command allowlist
- no shell expansion
- timeout boundaries
- output capture
- failure reporting
- command audit records
- examples such as `git diff --check`, focused `pytest`, and focused `eslint` if safe

Plan 4 must prove that verification commands cannot become general command execution.

### Plan 5: Operator Dashboard And Kill Switch v0.5

Purpose: real `/map` operator dashboard controls with clear manual authority and stop controls.

Must cover later:

- status cards
- kill switch display
- stop control display
- queue state
- approval state
- evidence/receipt browser
- manual checks
- no dangerous controls unless approved
- dashboard remains overview-only

Plan 5 must not treat dashboard presence as approval. Dashboard visibility is not live authority, write authority, command authority, unattended authority, or full-auto authority.

### Plan 6: Live Shadow Soak v0.6

Purpose: 24 to 72 hour "would have acted" mode. Cartographer observes, recommends, and logs what it would do. It does not act.

Must cover later:

- soak duration
- sample cadence
- drift checks
- hidden mutation checks
- operator comparison
- false positive review
- false negative review
- escalation rules
- closeout proof

Plan 6 must prove that recommendations remain recommendations. It must not treat dry-run success as live approval.

### Plan 7: Limited Unattended Operator v0.7

Purpose: first small low-risk unattended maintenance mode. Still not full auto.

Must cover later:

- low-risk task classes
- allowed unattended actions
- hard stop conditions
- kill switch
- max actions per window
- notification/receipt requirements
- rollback
- daily cap
- operator review after every run

Plan 7 is the first plan that may discuss limited unattended operation as a future target, but limited unattended operation remains not granted by this roadmap.

### Plan 8: Multi-Task Worker Autonomy v0.8

Purpose: bounded worker lanes for multiple tasks without cross-lane damage.

Must cover later:

- worker identity
- leases
- ownership zones
- file locks
- conflict detection
- task queue scheduling
- branch/worktree proposals only unless separately approved
- worker closeout packets

Plan 8 must preserve lane ownership and conflict detection before any worker action. Branches and worktrees remain proposals only unless a separate approval explicitly grants exact authority.

### Plan 9: Full Auto Readiness Gate v0.9

Purpose: final proof gate before full auto. Still no full auto until explicitly approved.

Must cover later:

- repeated real-task proof
- rollback proof
- kill-switch proof
- auditability proof
- self-approval barrier proof
- protected-lane proof
- security review
- soak proof
- operator decision packet

Plan 9 must produce a decision packet, not a promotion. Full auto remains not granted until a later explicit operator grant.

### Plan 10: Full Auto v1.0

Purpose: actual full-auto switch, only after explicit operator grant.

Must cover later:

- final authority contract
- activation criteria
- deactivation criteria
- allowed autonomous task classes
- forbidden task classes
- monitoring
- rollback
- audit trail
- emergency stop
- human override
- post-run review
- promotion/demotion process

Plan 10 can only exist as an activation plan after Plans 0 through 9 have been completed, proved, closed out, and explicitly approved. Full Auto v1.0 is not granted by this roadmap.

## Dependency Chain

The plans must happen in order:

- Plan 0 before Plan 1.
- Plan 1 before Plan 2.
- Plan 2 before Plan 3.
- Plan 3 before Plan 4.
- Plan 4 before Plan 5.
- Plan 5 before Plan 6.
- Plan 6 before Plan 7.
- Plan 7 before Plan 8.
- Plan 8 before Plan 9.
- Plan 9 before Plan 10.

## Promotion Rules

No plan promotes itself.

Every plan must end with:

- closeout doc
- verification commands
- manual checks
- no-go/go decision
- next plan permission gate

Any missing closeout, missing verification, missing manual check, ambiguous operator decision, stale HEAD, unexpected dirty tree, active kill switch, protected-lane conflict, or broadened authority is a no-go condition.

## Forbidden Shortcuts

The system must not:

- jump from `/map` inert shell to full auto
- skip read-only wiring
- skip approval tokens
- skip safe write class
- skip verification command boundaries
- skip live shadow soak
- treat dashboard presence as approval
- treat silence as approval
- treat dry-run success as live approval
- treat recommendation packets as execution approval

## Parallel Lane Rules

The following lanes remain protected and must not be mutated by this roadmap or by any future plan unless that future plan explicitly lists exact allowed files, exact forbidden files, rollback, verification, manual checks, and operator approval:

- `/coding` shell lane
- dashboard revamp lane
- Scout lane
- Source Proxy stress lane
- package/config lane
- runtime Cartographer lane until explicitly allowed
- tests lane until explicitly allowed

Parallel lane observation does not grant mutation. Dirty files in protected lanes must not be cleaned, staged, committed, overwritten, stashed, checked out, deleted, or absorbed into Cartographer authority without explicit approval.

## Explicit Non-Implementation Boundary

Do not implement anything from this roadmap.

This roadmap does not:

- write the full detailed Plan 1
- wire `/map`
- call backend endpoints
- add fetch calls
- expose executable controls
- expose apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete controls
- enable read-only wiring
- enable write authority
- enable command execution
- enable limited unattended operation
- grant full auto
- create approval token runtime
- create durable queue storage
- edit runtime modules
- edit tests

## Stop Point

Stop here. Do not implement. Do not write Plan 1 yet without explicit operator approval.

## Next Recommended Increment

Write Plan 1 Full Plan Only, No Implementation
