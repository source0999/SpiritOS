# Cartographer Level 13.2 Worker Identity And Registry Schema Preview

status: schema-preview-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 13.2 defines the future worker identity and registry schema for multi-agent and multi-worker orchestration.

This increment is docs-only. It does not implement a worker registry, worker leases, task dispatch, ownership locks, conflict detection, branch/worktree proposals, branch creation, worktree creation, APIs, service builders, tests, UI, workflow runtime, local execution, writes, receipts, evidence, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No worker registry runtime, orchestration authority, worker authority, branch/worktree authority, write authority, local execution authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 13.1 created the Multi-Agent Worker Orchestration Boundary Contract.

Level 13.2 narrows the next design artifact to worker identity and registry schema only. It does not advance to leases, ownership locks, conflict detection, handoff packets, branch/worktree proposals, worker closeout, or runtime orchestration.

## Scope

Allowed in this increment:

- create this worker identity and registry schema preview document.
- define future worker identity fields.
- define future registry fields.
- define future worker status values.
- define future invariants and invalid states.
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
- worker registry implementation.
- worker lease implementation.
- task dispatch implementation.
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

This schema is not worker authority.

A worker identity or registry entry described here is a future coordination record. It must not be treated as permission to dispatch tasks, claim files, create branches, create worktrees, execute commands, write files, reassign work, close out work, or mutate anything.

Future implementation must prove that worker registry presence does not equal orchestration authority.

## Worker Identity Schema Preview

Future worker identity must include:

- worker_id: stable unique worker identifier.
- worker_type: exact worker class.
- worker_name: display name.
- owner: operator or agent owner.
- assigned_task_id: assigned task identifier when applicable.
- assigned_run_id: assigned run identifier when applicable.
- assigned_lane: lane name.
- allowed_files: exact file scope.
- forbidden_files: exact blocked file scope.
- status: current worker status.
- lease_id: active lease identifier when applicable.
- branch_proposal_id: branch proposal reference when applicable.
- worktree_proposal_id: worktree proposal reference when applicable.
- created_at: creation timestamp.
- updated_at: update timestamp.
- stale_after: stale threshold.
- closeout_reference: closeout reference when applicable.

Future implementation may add display fields, but display fields must not become authority.

## Worker Registry Schema Preview

Future worker registry state must include:

- registry_id: stable registry identifier.
- run_id: run identifier.
- active_workers: active worker ids.
- inactive_workers: inactive worker ids.
- stale_workers: stale worker ids.
- blocked_workers: blocked worker ids.
- ownership_zones: ownership zone references.
- lease_references: lease references.
- conflict_references: conflict report references.
- handoff_references: handoff packet references.
- branch_worktree_proposals: branch or worktree proposal references.
- event_ledger_references: event ids associated with registry changes.
- created_at: registry creation timestamp.
- updated_at: last registry update timestamp.

The registry must describe coordination state only. It must not dispatch or mutate by itself.

## Worker Status Values

Future worker status values may include:

- proposed.
- active.
- inactive.
- paused.
- blocked.
- stale.
- handoff_pending.
- closeout_pending.
- closed_out.

Status must not imply authority beyond exact approval and scope.

## Registry Invariants

Future worker registry state must satisfy:

- every worker_id is unique.
- every active worker has exact allowed_files and forbidden_files.
- every active worker has one assigned lane.
- every active worker has at most one active lease.
- worker allowed_files do not conflict unless conflict policy allows observation only.
- forbidden_files cannot be overridden by worker identity.
- stale_after must exist for active workers.
- closeout_reference must exist before closed_out status.
- branch/worktree proposals do not create branches or worktrees.
- event_ledger_references must exist for state transitions in future live implementation.

If an invariant cannot be proven, future orchestration must fail closed.

## Invalid Registry State Rules

Future worker registry state is invalid when:

- worker_id is missing.
- worker_type is unknown.
- status is unknown.
- assigned_lane is missing for active workers.
- allowed_files are missing for active workers.
- forbidden_files are missing for active workers.
- allowed_files overlap another active worker without an explicit non-mutating policy.
- forbidden_files match assigned files.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- stale_after is missing for active workers.
- closeout_reference is missing for closed_out workers.
- branch/worktree proposal is treated as creation authority.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Invalid registry state must block future orchestration with an honest, visible, explainable result.

## Event Ledger Relationship

Future worker registry changes must be ledger-visible.

Expected future registry events may include:

- worker_registered.
- worker_activated.
- worker_paused.
- worker_blocked.
- worker_marked_stale.
- worker_handoff_requested.
- worker_closeout_requested.
- worker_closed_out.
- registry_conflict_detected.

Level 13.2 does not implement ledger storage or emit runtime ledger events.

## Branch And Worktree Relationship

Worker identity may reference future branch or worktree proposals. Those references must not create branches or worktrees.

Branch and worktree authority remains locked unless a future separate boundary explicitly approves exact names, exact owner, exact allowed files, rollback notes, and verification checks.

## Forbidden Registry Uses

Future worker registry state must never authorize:

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
- deletion of branches or worktrees.

## Dirty Worktree And Lane Isolation Rules

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit approval.

Future registry state must treat unexpected HEAD or git status changes as blocking conditions for dispatch, reassignment, handoff, branch/worktree proposal escalation, or closeout.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 13.3: Worker Lease Boundary
- Level 13.4: Ownership Zone And File Lock Preview
- Level 13.5: Conflict Detection Dry Run Boundary
- Level 13.6: Handoff Packet Boundary
- Level 13.7: Branch Worktree Proposal Boundary
- Level 13.8: Worker Closeout Boundary
- Level 13.9: Level 13 Closeout And Level 14 Gate

Do not implement any of these in Level 13.2.

## Required Future Tests

Future source-code increments must prove:

- registry state does not dispatch work by itself.
- worker is blocked when worker_id is missing.
- worker is blocked when worker_type is unknown.
- worker is blocked when status is unknown.
- active worker is blocked without assigned_lane.
- active worker is blocked without allowed_files.
- active worker is blocked without forbidden_files.
- overlapping active workers block mutation dispatch.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- branch/worktree proposal references do not create branches or worktrees.
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

git diff --check -- docs/cartographer-level-13-worker-identity-registry-schema-preview.md

grep -n "Worker Identity And Registry Schema Preview\|Worker Identity Schema Preview\|Worker Registry Schema Preview\|Registry Invariants\|Level 13.3: Worker Lease Boundary" docs/cartographer-level-13-worker-identity-registry-schema-preview.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-13-worker-identity-registry-schema-preview.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 13.2 creates the Worker Identity And Registry Schema Preview only.

Expected result:

- no worker registry runtime enabled.
- no worker lease runtime enabled.
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

Level 13.3: Worker Lease Boundary
