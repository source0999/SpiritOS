# Cartographer Level 13.7 Branch Worktree Proposal Boundary

status: branch-worktree-proposal-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 13.7 defines the future proposal boundary for branch and worktree planning in multi-worker orchestration.

This increment is docs-only. It does not implement branch creation, worktree creation, checkout, stash, cleanup, task dispatch, worker handoff runtime, worker registry runtime, worker leases, ownership locks, conflict detection runtime, APIs, service builders, tests, UI, workflow runtime, local execution, writes, receipts, evidence, commits, pushes, merges, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No branch/worktree authority, orchestration authority, worker authority, write authority, local execution authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 13.1 created the Multi-Agent Worker Orchestration Boundary Contract.

Level 13.2 created the Worker Identity And Registry Schema Preview.

Level 13.3 created the Worker Lease Boundary.

Level 13.4 created the Ownership Zone And File Lock Preview.

Level 13.5 created the Conflict Detection Dry Run Boundary.

Level 13.6 created the Handoff Packet Boundary.

Level 13.7 narrows the next design artifact to branch/worktree proposal rules only. It does not advance to worker closeout, Level 13 closeout, or runtime orchestration.

## Scope

Allowed in this increment:

- create this branch/worktree proposal boundary document.
- define future branch proposal fields.
- define future worktree proposal fields.
- define future proposal eligibility rules.
- define future proposal block rules.
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
- branch creation.
- worktree creation.
- checkout.
- stash.
- cleanup.
- worker handoff implementation.
- worker lease implementation.
- worker registry implementation.
- task dispatch implementation.
- conflict detection implementation.
- ownership lock implementation.
- local command execution.
- write actions.
- receipt or evidence writing.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- commit, push, or merge operations.

## Non-Authority Statement

This boundary is proposal-only.

Future branch/worktree proposal packets may describe a possible isolation plan for a worker or task. They must not create branches, create worktrees, checkout, stash, clean files, stage files, commit, push, merge, delete branches, delete worktrees, or mutate anything by themselves.

Level 13.7 does not create runtime branch or worktree behavior.

## Branch Worktree Proposal Boundary Definition

A future branch/worktree proposal is a structured, non-mutating preview of isolation intent.

It must be:

- worker-bound.
- task-bound.
- lane-bound.
- file-scope-bound.
- conflict-report-aware.
- dirty-worktree-aware.
- approval-aware if future authority is requested.
- fail-closed by default.

Proposal packets must be clearly separated from execution packets.

## Branch Proposal Preview

Future branch proposal packets must include:

- branch_proposal_id.
- run_id.
- worker_id.
- task_id.
- lane.
- proposed_branch_name.
- source_head.
- expected_base_branch.
- naming_reason.
- collision_check_result.
- protected_branch_check_result.
- allowed_files.
- forbidden_files.
- required_operator_approval.
- blocked_reasons.
- created_at.
- expires_at.

Future implementation may add display fields, but display fields must not become authority.

## Worktree Proposal Preview

Future worktree proposal packets must include:

- worktree_proposal_id.
- run_id.
- worker_id.
- task_id.
- lane.
- proposed_worktree_path.
- proposed_branch_name.
- source_head.
- expected_base_branch.
- path_collision_check_result.
- branch_collision_check_result.
- protected_path_check_result.
- allowed_files.
- forbidden_files.
- required_operator_approval.
- blocked_reasons.
- created_at.
- expires_at.

Future implementation may add display fields, but display fields must not become authority.

## Proposal Eligibility Rules

Future branch/worktree proposals may be eligible only when:

- worker identity is known.
- task identity is known.
- lane is known.
- source HEAD is known.
- expected base branch is known.
- allowed_files are explicit.
- forbidden_files are explicit.
- conflict detection has completed.
- dirty worktree state has been observed.
- proposed names do not collide.
- protected paths are excluded.
- Source Proxy stress files are excluded.
- `/coding` UI files are excluded unless a future separate lane allows them.
- no hidden mutation occurred.

Eligibility does not mean creation. It only means a proposal may be shown.

## Proposal Block Rules

Future branch/worktree proposals must be blocked when:

- worker identity is unknown.
- task identity is unknown.
- lane is ambiguous.
- source HEAD is missing or changed unexpectedly.
- expected base branch is missing.
- allowed_files are missing.
- forbidden_files are missing.
- conflict detection reports a blocker.
- dirty worktree state changed unexpectedly.
- proposed branch name collides.
- proposed worktree path collides.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- Scout, proxy memory, or blueprint lanes are in scope without separate approval.
- proposal would imply checkout, stash, cleanup, commit, push, or merge.
- hidden mutation is suspected.

Blocked proposals must be honest, visible, and explainable.

## Event Ledger Requirements

Future branch/worktree proposals must be ledger-visible before any creation authority exists.

Expected future events may include:

- branch_proposal_created.
- branch_proposal_blocked.
- worktree_proposal_created.
- worktree_proposal_blocked.

Level 13.7 does not implement ledger storage or emit runtime ledger events.

## Forbidden Proposal Uses

Future branch/worktree proposals must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
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

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit branch/worktree approval.

Future proposal logic must treat unexpected HEAD or git status changes as blocking conditions for proposal escalation, dispatch, or closeout.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 13.8: Worker Closeout Boundary
- Level 13.9: Level 13 Closeout And Level 14 Gate

Do not implement any of these in Level 13.7.

## Required Future Tests

Future source-code increments must prove:

- proposal creation does not create branches.
- proposal creation does not create worktrees.
- proposal creation does not checkout, stash, or clean files.
- proposal creation does not mutate files.
- proposal is blocked without worker identity.
- proposal is blocked without task identity.
- proposal is blocked without explicit allowed_files.
- proposal is blocked when forbidden_files overlap.
- proposal is blocked when conflict detection reports a blocker.
- proposal is blocked when branch name collides.
- proposal is blocked when worktree path collides.
- proposal is blocked when HEAD changed unexpectedly.
- proposal is blocked when git status changed unexpectedly.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
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

git diff --check -- docs/cartographer-level-13-branch-worktree-proposal-boundary.md

grep -n "Branch Worktree Proposal Boundary\|Branch Proposal Preview\|Worktree Proposal Preview\|Proposal Block Rules\|Level 13.8: Worker Closeout Boundary" docs/cartographer-level-13-branch-worktree-proposal-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-13-branch-worktree-proposal-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 13.7 creates the Branch Worktree Proposal Boundary only.

Expected result:

- no branch creation enabled.
- no worktree creation enabled.
- no checkout enabled.
- no stash enabled.
- no cleanup enabled.
- no worker handoff runtime enabled.
- no worker registry runtime enabled.
- no task dispatch enabled.
- no write authority enabled.
- no local execution authority enabled.
- no commit/push/merge authority enabled.
- no automatic execution enabled.
- no automatic promotion enabled.
- no self-approval enabled.
- no Source Proxy stress files touched.
- no `/coding` UI files touched.
- no source code, API routes, tests, package files, or runtime files touched.

## Next Increment

Level 13.8: Worker Closeout Boundary
