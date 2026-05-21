# Cartographer Level 13.8 Worker Closeout Boundary

status: worker-closeout-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 13.8 defines the future worker closeout boundary for multi-worker orchestration.

This increment is docs-only. It does not implement worker closeout runtime, closeout receipt writing, evidence writing, worker registry mutation, worker lease release, ownership lock release, branch/worktree creation, checkout, stash, cleanup, task dispatch, APIs, service builders, tests, UI, workflow runtime, local execution, writes, commits, pushes, merges, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No closeout authority, worker authority, branch/worktree authority, write authority, local execution authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 13.1 created the Multi-Agent Worker Orchestration Boundary Contract.

Level 13.2 created the Worker Identity And Registry Schema Preview.

Level 13.3 created the Worker Lease Boundary.

Level 13.4 created the Ownership Zone And File Lock Preview.

Level 13.5 created the Conflict Detection Dry Run Boundary.

Level 13.6 created the Handoff Packet Boundary.

Level 13.7 created the Branch Worktree Proposal Boundary.

Level 13.8 narrows the next design artifact to worker closeout rules only. It does not advance to Level 13 closeout, Level 14, or runtime orchestration.

## Scope

Allowed in this increment:

- create this worker closeout boundary document.
- define future worker closeout packet fields.
- define future closeout eligibility rules.
- define future closeout block rules.
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
- worker closeout implementation.
- closeout receipt writing.
- evidence writing.
- worker registry mutation.
- worker lease release.
- ownership lock release.
- task dispatch implementation.
- branch/worktree proposal implementation.
- branch/worktree creation.
- checkout.
- stash.
- cleanup.
- local command execution.
- write actions.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- commit, push, or merge operations.

## Non-Authority Statement

This boundary is closeout-preview-only.

Future worker closeout packets may describe whether a worker appears ready to close a task or hand work back to the operator. They must not close tasks, write receipts, write evidence, release leases, release locks, mutate registries, create branches, create worktrees, execute commands, commit, push, merge, or clean anything by themselves.

Level 13.8 does not create runtime worker closeout behavior.

## Worker Closeout Boundary Definition

A future worker closeout packet is a structured, non-mutating preview of worker completion state.

It must be:

- worker-bound.
- task-bound.
- lane-bound.
- file-scope-bound.
- lease-aware.
- lock-aware.
- conflict-report-aware.
- verification-aware.
- handoff-aware.
- fail-closed by default.

Closeout packets must separate completion claims from actual closeout authority.

## Worker Closeout Packet Preview

Future worker closeout packets must include:

- closeout_packet_id.
- run_id.
- worker_id.
- task_id.
- lane.
- worker_state.
- lease_id.
- ownership_zone_ids.
- file_lock_ids.
- allowed_files.
- forbidden_files.
- touched_files.
- unresolved_files.
- conflict_report_id.
- verification_summary.
- handoff_packet_id.
- branch_proposal_id.
- worktree_proposal_id.
- closeout_summary.
- blocked_reasons.
- required_operator_approval.
- created_at.
- expires_at.

Future implementation may add display fields, but display fields must not become authority.

## Closeout Eligibility Rules

Future worker closeout packets may be eligible only when:

- worker identity is known.
- task identity is known.
- lane is known.
- allowed_files are explicit.
- forbidden_files are explicit.
- lease state is visible.
- lock state is visible.
- conflict detection has completed.
- verification summary is present when verification was required.
- unresolved files are empty or explicitly explained.
- protected paths are excluded.
- Source Proxy stress files are excluded.
- `/coding` UI files are excluded unless a future separate lane allows them.
- no hidden mutation occurred.

Eligibility does not mean closeout. It only means a closeout proposal may be shown.

## Closeout Block Rules

Future worker closeout packets must be blocked when:

- worker identity is unknown.
- task identity is unknown.
- lane is ambiguous.
- allowed_files are missing.
- forbidden_files are missing.
- lease state is missing or expired without explanation.
- lock state is missing or conflicting.
- conflict detection reports a blocker.
- required verification summary is missing.
- unresolved files are unexplained.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- Scout, proxy memory, or blueprint lanes are in scope without separate approval.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- closeout would imply receipt or evidence writing without explicit future authority.
- closeout would imply checkout, stash, cleanup, commit, push, or merge.
- hidden mutation is suspected.

Blocked closeouts must be honest, visible, and explainable.

## Closeout Receipt Relationship

Future worker closeout packets may prepare information for a later receipt boundary, but they must not write receipts.

Receipt writing remains locked unless a future explicit increment grants approved, scoped, token-bound write authority with verification and rollback requirements.

## Event Ledger Requirements

Future worker closeout previews must be ledger-visible before runtime closeout authority exists.

Expected future events may include:

- worker_closeout_packet_created.
- worker_closeout_packet_blocked.
- worker_closeout_packet_expired.
- worker_closeout_packet_closed.

Level 13.8 does not implement ledger storage or emit runtime ledger events.

## Forbidden Closeout Uses

Future worker closeout packets must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- automatic worker reassignment.
- automatic task dispatch.
- automatic closeout.
- receipt writing.
- evidence writing.
- lease release.
- lock release.
- registry mutation.
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

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit closeout approval.

Future closeout logic must treat unexpected HEAD or git status changes as blocking conditions for closeout, proposal escalation, dispatch, or any future receipt boundary.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 13.9: Level 13 Closeout And Level 14 Gate

Do not implement this in Level 13.8.

## Required Future Tests

Future source-code increments must prove:

- closeout packet creation does not close work.
- closeout packet creation does not mutate files.
- closeout packet creation does not write receipts.
- closeout packet creation does not write evidence.
- closeout packet creation does not release leases.
- closeout packet creation does not release locks.
- closeout packet creation does not mutate registries.
- closeout is blocked without worker identity.
- closeout is blocked without task identity.
- closeout is blocked without explicit allowed_files.
- closeout is blocked when forbidden_files overlap.
- closeout is blocked when conflict detection reports a blocker.
- closeout is blocked when required verification summary is missing.
- closeout is blocked when HEAD changed unexpectedly.
- closeout is blocked when git status changed unexpectedly.
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

git diff --check -- docs/cartographer-level-13-worker-closeout-boundary.md

grep -n "Worker Closeout Boundary\|Worker Closeout Packet Preview\|Closeout Eligibility Rules\|Closeout Block Rules\|Level 13.9: Level 13 Closeout And Level 14 Gate" docs/cartographer-level-13-worker-closeout-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-13-worker-closeout-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 13.8 creates the Worker Closeout Boundary only.

Expected result:

- no worker closeout runtime enabled.
- no receipt writing enabled.
- no evidence writing enabled.
- no lease release enabled.
- no lock release enabled.
- no registry mutation enabled.
- no branch/worktree creation enabled.
- no checkout/stash/cleanup enabled.
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

Level 13.9: Level 13 Closeout And Level 14 Gate
