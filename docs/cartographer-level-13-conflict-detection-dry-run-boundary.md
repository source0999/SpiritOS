# Cartographer Level 13.5 Conflict Detection Dry Run Boundary

status: conflict-detection-dry-run-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 13.5 defines the future dry-run boundary for worker conflict detection.

This increment is docs-only. It does not implement conflict detection runtime, worker registry runtime, worker leases, ownership locks, task dispatch, branch/worktree proposals, branch creation, worktree creation, APIs, service builders, tests, UI, workflow runtime, local execution, writes, receipts, evidence, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No conflict detection runtime, orchestration authority, worker authority, branch/worktree authority, write authority, local execution authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 13.1 created the Multi-Agent Worker Orchestration Boundary Contract.

Level 13.2 created the Worker Identity And Registry Schema Preview.

Level 13.3 created the Worker Lease Boundary.

Level 13.4 created the Ownership Zone And File Lock Preview.

Level 13.5 narrows the next design artifact to conflict detection dry-run rules only. It does not advance to handoff packets, branch/worktree proposals, worker closeout, or runtime orchestration.

## Scope

Allowed in this increment:

- create this conflict detection dry-run boundary document.
- define future conflict report fields.
- define future conflict classes.
- define future blocked conflict rules.
- define future test expectations.
- run doc-only verification commands.

Not allowed in this increment:

- source code edits.
- API route edits.
- service builder edits.
- tests.
- package changes.
- dependency installs.
- runtime behavior changes.
- UI work.
- Source Proxy stress testing mutation.
- `/coding` UI mutation.
- conflict detection implementation.
- worker lease implementation.
- worker registry implementation.
- task dispatch implementation.
- ownership lock implementation.
- branch/worktree proposal implementation.
- branch/worktree creation.
- local command execution.
- write actions.
- receipt or evidence writing.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- checkout, stash, cleanup, commit, push, or merge operations.

## Non-Authority Statement

This dry run is not conflict resolution authority.

Future conflict detection may report conflicts and block unsafe orchestration. It must not resolve conflicts, reassign work, overwrite files, clean up, create branches, create worktrees, execute commands, or mutate anything by itself.

Level 13.5 does not create runtime conflict detection behavior.

## Conflict Detection Dry Run Definition

A future conflict detection dry run is a simulated report over workers, ownership zones, locks, dirty worktree state, and lane boundaries.

It must be:

- read-only.
- worker-bound.
- task-bound when task context exists.
- lane-bound.
- file-scope-bound.
- event-ledger-preview-aware.
- fail-closed by default.

Conflict detection should block risky dispatch by default.

## Conflict Report Preview

Future conflict reports must include:

- conflict_report_id.
- run_id.
- checked_worker_ids.
- checked_task_ids.
- checked_lanes.
- checked_files.
- allowed_files.
- forbidden_files.
- conflict_classes.
- active_worker_conflicts.
- stale_worker_conflicts.
- ownership_zone_conflicts.
- file_lock_conflicts.
- dirty_worktree_conflicts.
- protected_path_conflicts.
- Source Proxy stress lane conflicts.
- `/coding` UI lane conflicts.
- Scout, proxy memory, or blueprint lane conflicts.
- branch_worktree_name_conflicts.
- blocked: boolean conflict result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Conflict Classes

Future conflict classes must include:

- overlapping_allowed_files.
- forbidden_file_match.
- active_worker_overlap.
- stale_worker_overlap.
- ownership_zone_overlap.
- file_lock_overlap.
- dirty_worktree_overlap.
- protected_path_scope.
- Source Proxy stress lane scope.
- `/coding` UI lane scope.
- Scout lane scope.
- proxy memory lane scope.
- blueprint lane scope.
- branch_name_collision.
- worktree_name_collision.

Each conflict class must block mutation dispatch unless a future separate policy explicitly allows a non-mutating observation.

## Blocked Conflict Rules

Future conflict detection must block when:

- checked files are missing.
- allowed_files are missing.
- forbidden_files are missing.
- active worker overlap exists.
- stale worker overlap exists and no handoff policy exists.
- ownership zone overlap exists.
- file lock overlap exists.
- dirty worktree overlap exists.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- Scout, proxy memory, or blueprint lanes are in scope without separate approval.
- branch or worktree name collision exists.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Blocked conflicts must be honest, visible, and explainable.

## Event Ledger Requirements

Future conflict detection dry runs must be ledger-visible before dispatch authority exists.

Expected future events may include:

- conflict_detection_requested.
- conflict_detection_completed.
- conflict_detection_blocked.
- registry_conflict_detected.

Level 13.5 does not implement ledger storage or emit runtime ledger events.

## Forbidden Conflict Uses

Future conflict detection must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- conflict auto-resolution.
- automatic reassignment without policy.
- force overwrite.
- branch creation.
- worktree creation.
- checkout.
- stash.
- cleanup.
- commit.
- push.
- merge.
- deletion of branches or worktrees.
- protected path writes.
- secret path reads or writes.
- cross-lane mutation.
- Source Proxy stress testing mutation.
- `/coding` UI mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- deletion of evidence.
- deletion of receipts.
- deletion of run history.

## Dirty Worktree And Lane Isolation Rules

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit approval.

Future conflict detection must treat unexpected HEAD or git status changes as blocking conditions for dispatch, reassignment, handoff, branch/worktree proposal escalation, or closeout.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 13.6: Handoff Packet Boundary
- Level 13.7: Branch Worktree Proposal Boundary
- Level 13.8: Worker Closeout Boundary
- Level 13.9: Level 13 Closeout And Level 14 Gate

Do not implement any of these in Level 13.5.

## Required Future Tests

Future source-code increments must prove:

- conflict detection dry run does not dispatch work.
- conflict detection dry run does not mutate files.
- conflict detection blocks active worker overlap.
- conflict detection blocks stale worker overlap without policy.
- conflict detection blocks ownership zone overlap.
- conflict detection blocks file lock overlap.
- conflict detection blocks dirty worktree overlap.
- conflict detection blocks protected paths.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- branch/worktree name collision blocks proposal escalation.
- no branch/worktree creation authority exists.
- no checkout/stash/cleanup authority exists.
- no commit/push/merge authority exists.
- no self-approval exists.
- no force overwrite exists.
- failures are honest and explainable.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-13-conflict-detection-dry-run-boundary.md

grep -n "Conflict Detection Dry Run Boundary\|Conflict Report Preview\|Conflict Classes\|Blocked Conflict Rules\|Level 13.6: Handoff Packet Boundary" docs/cartographer-level-13-conflict-detection-dry-run-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-13-conflict-detection-dry-run-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 13.5 creates the Conflict Detection Dry Run Boundary only.

Expected result:

- no conflict detection runtime enabled.
- no conflict resolution enabled.
- no worker lease runtime enabled.
- no worker registry runtime enabled.
- no task dispatch enabled.
- no ownership locks enabled.
- no branch/worktree creation enabled.
- no write authority enabled.
- no local execution authority enabled.
- no commit/push/merge authority enabled.
- no automatic execution enabled.
- no automatic promotion enabled.
- no self-approval enabled.
- no cleanup occurred.
- no Source Proxy stress files touched.
- no `/coding` UI files touched.
- no source code, API routes, tests, package files, or runtime files touched.

## Next Increment

Level 13.6: Handoff Packet Boundary
