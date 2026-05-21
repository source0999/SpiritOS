# Cartographer Level 13.6 Handoff Packet Boundary

status: handoff-packet-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 13.6 defines the future handoff packet boundary for multi-worker coordination.

This increment is docs-only. It does not implement worker handoff runtime, worker reassignment, worker registry runtime, worker leases, ownership locks, conflict detection runtime, task dispatch, branch/worktree proposals, branch creation, worktree creation, APIs, service builders, tests, UI, workflow runtime, local execution, writes, receipts, evidence, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No handoff authority, orchestration authority, worker authority, branch/worktree authority, write authority, local execution authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 13.1 created the Multi-Agent Worker Orchestration Boundary Contract.

Level 13.2 created the Worker Identity And Registry Schema Preview.

Level 13.3 created the Worker Lease Boundary.

Level 13.4 created the Ownership Zone And File Lock Preview.

Level 13.5 created the Conflict Detection Dry Run Boundary.

Level 13.6 narrows the next design artifact to handoff packet rules only. It does not advance to branch/worktree proposals, worker closeout, Level 13 closeout, or runtime orchestration.

## Scope

Allowed in this increment:

- create this handoff packet boundary document.
- define future handoff packet fields.
- define future handoff eligibility rules.
- define future handoff block rules.
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
- worker handoff implementation.
- worker reassignment implementation.
- worker lease implementation.
- worker registry implementation.
- task dispatch implementation.
- conflict detection implementation.
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

This boundary is not handoff authority.

Future handoff packets may preview how one worker should transfer context, ownership, and unresolved risks to another worker. They must not transfer authority, mutate registry state, clear locks, reassign tasks, overwrite files, execute commands, create branches, create worktrees, or close work by themselves.

Level 13.6 does not create runtime handoff behavior.

## Handoff Packet Boundary Definition

A future handoff packet is a structured, non-mutating preview of a worker-to-worker transition.

It must be:

- worker-bound.
- task-bound.
- lane-bound.
- file-scope-bound.
- lease-aware.
- lock-aware.
- conflict-report-aware.
- approval-aware when authority is proposed.
- fail-closed by default.

Handoff packets must make uncertainty explicit instead of hiding gaps.

## Handoff Packet Preview

Future handoff packets must include:

- handoff_packet_id.
- run_id.
- source_worker_id.
- target_worker_id.
- task_id.
- lane.
- source_worker_state.
- target_worker_state.
- current_lease_id.
- ownership_zone_ids.
- file_lock_ids.
- allowed_files.
- forbidden_files.
- touched_files.
- unresolved_files.
- conflict_report_id.
- handoff_reason.
- handoff_summary.
- open_questions.
- blocked_reasons.
- required_operator_approval.
- created_at.
- expires_at.

Future implementation may add display fields, but display fields must not become authority.

## Handoff Eligibility Rules

Future handoff packets may be eligible only when:

- source worker identity is known.
- target worker identity is known.
- task identity is known.
- lane is known.
- allowed_files are explicit.
- forbidden_files are explicit.
- active leases are visible.
- active locks are visible.
- conflict detection has completed.
- protected paths are excluded.
- Source Proxy stress files are excluded.
- `/coding` UI files are excluded unless a future separate lane allows them.
- branch/worktree creation is not implied.
- no hidden mutation occurred.

Eligibility does not mean execution. It only means a handoff proposal may be shown.

## Handoff Block Rules

Future handoff packets must be blocked when:

- source worker is unknown.
- target worker is unknown.
- task is unknown.
- lane is ambiguous.
- allowed_files are missing.
- forbidden_files are missing.
- active conflict report blocks handoff.
- stale worker state cannot be explained.
- lease state is missing or expired.
- lock state is missing or conflicting.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- Scout, proxy memory, or blueprint lanes are in scope without separate approval.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- handoff would imply branch/worktree creation.
- handoff would imply checkout, stash, cleanup, commit, push, or merge.
- hidden mutation is suspected.

Blocked handoffs must be honest, visible, and explainable.

## Event Ledger Requirements

Future handoff packet previews must be ledger-visible before runtime orchestration exists.

Expected future events may include:

- handoff_packet_created.
- handoff_packet_blocked.
- handoff_packet_expired.
- handoff_packet_closed.

Level 13.6 does not implement ledger storage or emit runtime ledger events.

## Forbidden Handoff Uses

Future handoff packets must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- automatic worker reassignment.
- automatic task dispatch.
- conflict auto-resolution.
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

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit handoff approval.

Future handoff logic must treat unexpected HEAD or git status changes as blocking conditions for handoff proposal escalation, dispatch, branch/worktree proposal escalation, or closeout.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 13.7: Branch Worktree Proposal Boundary
- Level 13.8: Worker Closeout Boundary
- Level 13.9: Level 13 Closeout And Level 14 Gate

Do not implement any of these in Level 13.6.

## Required Future Tests

Future source-code increments must prove:

- handoff packet creation does not dispatch work.
- handoff packet creation does not mutate files.
- handoff is blocked without source worker identity.
- handoff is blocked without target worker identity.
- handoff is blocked without explicit allowed_files.
- handoff is blocked when forbidden_files overlap.
- handoff is blocked when conflict detection reports a blocker.
- handoff is blocked when lease state is expired.
- handoff is blocked when lock state conflicts.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- no branch/worktree creation authority exists.
- no checkout/stash/cleanup authority exists.
- no commit/push/merge authority exists.
- no self-approval exists.
- no hidden background mutation exists.
- failures are honest and explainable.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-13-handoff-packet-boundary.md

grep -n "Handoff Packet Boundary\|Handoff Packet Preview\|Handoff Eligibility Rules\|Handoff Block Rules\|Level 13.7: Branch Worktree Proposal Boundary" docs/cartographer-level-13-handoff-packet-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-13-handoff-packet-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 13.6 creates the Handoff Packet Boundary only.

Expected result:

- no handoff runtime enabled.
- no worker reassignment enabled.
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

Level 13.7: Branch Worktree Proposal Boundary
