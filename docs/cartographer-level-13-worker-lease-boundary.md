# Cartographer Level 13.3 Worker Lease Boundary

status: worker-lease-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 13.3 defines the future boundary for worker leases in multi-agent and multi-worker orchestration.

This increment is docs-only. It does not implement worker leases, worker registry runtime, task dispatch, ownership locks, conflict detection, branch/worktree proposals, branch creation, worktree creation, APIs, service builders, tests, UI, workflow runtime, local execution, writes, receipts, evidence, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No worker lease runtime, orchestration authority, worker authority, branch/worktree authority, write authority, local execution authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 13.1 created the Multi-Agent Worker Orchestration Boundary Contract.

Level 13.2 created the Worker Identity And Registry Schema Preview.

Level 13.3 narrows the next design artifact to worker lease rules only. It does not advance to ownership locks, conflict detection, handoff packets, branch/worktree proposals, worker closeout, or runtime orchestration.

## Scope

Allowed in this increment:

- create this worker lease boundary document.
- define future worker lease fields.
- define future lease grant, renewal, revocation, stale, and closeout rules.
- define future lease block rules.
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
- worker lease implementation.
- worker registry implementation.
- task dispatch implementation.
- ownership lock implementation.
- branch/worktree proposal implementation.
- branch/worktree creation.
- workflow runtime implementation.
- approval token implementation.
- event ledger implementation.
- local command execution.
- write actions.
- receipt or evidence writing.
- docs-only apply implementation.
- rollback command execution.
- run history mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- checkout, stash, cleanup, commit, push, or merge operations.

## Non-Authority Statement

This boundary is not worker lease authority.

A future worker lease may reserve a scoped task or file zone for a worker. It must not dispatch work, execute commands, write files, create branches, create worktrees, reassign workers, close out workers, or mutate anything by itself.

Level 13.3 does not create runtime lease behavior.

## Worker Lease Definition

A future worker lease is a bounded coordination record for one worker, one task, and one ownership scope.

It must be:

- worker-bound.
- task-bound.
- run-bound.
- lane-bound.
- file-scope-bound.
- time-limited.
- revocable.
- stale-detectable.
- event-ledger-recorded.
- fail-closed by default.

Leases must never authorize mutation outside exact scope.

## Worker Lease Packet Preview

Future worker lease packets must include:

- lease_id: stable lease identifier.
- worker_id: stable worker identifier.
- worker_type: exact worker class.
- task_id: exact task identifier.
- run_id: stable run identifier.
- lane: assigned lane.
- allowed_files: exact allowed file scope.
- forbidden_files: exact blocked file scope.
- ownership_zone_reference: ownership zone reference.
- lease_status: proposed, active, paused, revoked, stale, expired, or closed_out.
- granted_by: operator or system actor id.
- granted_at: lease grant timestamp.
- expires_at: lease expiration timestamp.
- stale_after: stale threshold.
- max_renewals: maximum renewal count.
- renewal_count: renewals used.
- event_ledger_plan: required lease events.
- verification_reference: verification requirement when lease is used for dispatch.
- rollback_reference: rollback note when lease is used for mutation.
- blocked: boolean lease result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Lease Grant Rules

Future lease grant may be eligible only when:

- worker_id exists.
- task_id exists.
- lane is exact.
- allowed_files are present.
- forbidden_files are present.
- ownership zone exists.
- no active worker conflict exists.
- no dirty worktree conflict exists.
- lease expiration exists.
- stale_after exists.
- event ledger plan exists.
- protected paths are not in scope.
- Source Proxy stress files are not in scope unless a future separate lane explicitly allows observation.
- `/coding` UI files are not in scope unless a future separate lane explicitly allows observation.

Lease grant is advisory until future focused implementation and tests exist.

## Lease Renewal Rules

Future lease renewal must be bounded and visible.

Renewal must be blocked when:

- max_renewals is missing.
- renewal_count has reached max_renewals.
- lease is revoked.
- lease is stale without operator review.
- lease is expired.
- worker state changed unexpectedly.
- allowed_files changed unexpectedly.
- forbidden_files changed unexpectedly.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- conflict detection reports a conflict.

Hidden lease renewal is forbidden.

## Lease Revocation Rules

Future lease revocation must stop future dispatch for that lease.

Revocation must be ledgered and visible.

Revocation must not clean up files, stash work, checkout files, delete branches, delete worktrees, execute rollback, write receipts, write evidence, or reassign work unless a future separate approved action exists.

## Stale Lease Rules

Future stale leases must block unsafe dispatch and reassignment.

Stale lease handling must require explicit policy before any handoff, closeout, or reassignment.

Stale status must not authorize force overwrite, cleanup, branch deletion, worktree deletion, or worker closure by itself.

## Event Ledger Requirements

Future worker lease behavior must be ledger-visible.

Expected future lease events may include:

- worker_lease_requested.
- worker_lease_granted.
- worker_lease_renewed.
- worker_lease_revoked.
- worker_lease_expired.
- worker_lease_marked_stale.
- worker_lease_closed_out.

Level 13.3 does not implement ledger storage or emit runtime ledger events.

## Fail-Closed Rules

Future worker leases must fail closed when:

- worker_id is missing.
- task_id is missing.
- lane is missing.
- allowed_files are missing.
- forbidden_files are missing.
- ownership zone is missing.
- lease expiration is missing.
- stale_after is missing.
- max_renewals is missing for renewals.
- worker conflict exists.
- dirty worktree conflict exists.
- protected paths are in scope.
- Source Proxy stress files are in scope without a future separate lane.
- `/coding` UI files are in scope without a future separate lane.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- event ledger continuity is missing.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Lease Uses

Future worker leases must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- hidden background workers.
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

Future leases must treat unexpected HEAD or git status changes as blocking conditions for grant, renewal, dispatch, reassignment, handoff, branch/worktree proposal escalation, or closeout.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 13.4: Ownership Zone And File Lock Preview
- Level 13.5: Conflict Detection Dry Run Boundary
- Level 13.6: Handoff Packet Boundary
- Level 13.7: Branch Worktree Proposal Boundary
- Level 13.8: Worker Closeout Boundary
- Level 13.9: Level 13 Closeout And Level 14 Gate

Do not implement any of these in Level 13.3.

## Required Future Tests

Future source-code increments must prove:

- lease state does not dispatch work by itself.
- lease grant is blocked when worker_id is missing.
- lease grant is blocked when task_id is missing.
- lease grant is blocked when allowed_files are missing.
- lease grant is blocked when forbidden_files are missing.
- lease grant is blocked when ownership zone is missing.
- lease grant is blocked when expiration is missing.
- lease renewal is bounded.
- lease renewal is blocked after max_renewals.
- revoked leases block dispatch.
- stale leases block unsafe reassignment.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- no branch/worktree creation authority exists.
- no checkout/stash/cleanup authority exists.
- no commit/push/merge authority exists.
- no self-approval exists.
- no force overwrite exists.
- no hidden background mutation exists.
- failures are honest and explainable.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-13-worker-lease-boundary.md

grep -n "Worker Lease Boundary\|Worker Lease Packet Preview\|Lease Grant Rules\|Lease Revocation Rules\|Level 13.4: Ownership Zone And File Lock Preview" docs/cartographer-level-13-worker-lease-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-13-worker-lease-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 13.3 creates the Worker Lease Boundary only.

Expected result:

- no worker lease runtime enabled.
- no worker registry runtime enabled.
- no task dispatch enabled.
- no ownership locks enabled.
- no conflict detection runtime enabled.
- no branch/worktree proposal runtime enabled.
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

Level 13.4: Ownership Zone And File Lock Preview
