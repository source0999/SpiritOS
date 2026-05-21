# Cartographer Level 13.4 Ownership Zone And File Lock Preview

status: ownership-zone-file-lock-preview-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 13.4 defines the future ownership zone and file lock preview for multi-agent and multi-worker orchestration.

This increment is docs-only. It does not implement ownership locks, file locks, worker leases, worker registry runtime, task dispatch, conflict detection, branch/worktree proposals, branch creation, worktree creation, APIs, service builders, tests, UI, workflow runtime, local execution, writes, receipts, evidence, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No ownership lock runtime, file lock runtime, orchestration authority, worker authority, branch/worktree authority, write authority, local execution authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 13.1 created the Multi-Agent Worker Orchestration Boundary Contract.

Level 13.2 created the Worker Identity And Registry Schema Preview.

Level 13.3 created the Worker Lease Boundary.

Level 13.4 narrows the next design artifact to ownership zones and file lock previews only. It does not advance to conflict detection, handoff packets, branch/worktree proposals, worker closeout, or runtime orchestration.

## Scope

Allowed in this increment:

- create this ownership zone and file lock preview document.
- define future ownership zone fields.
- define future file lock fields.
- define future lock grant, conflict, stale, and release rules.
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
- ownership lock implementation.
- file lock implementation.
- worker lease implementation.
- worker registry implementation.
- task dispatch implementation.
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

This preview is not ownership or file lock authority.

Future ownership zones and file locks may describe coordination scope. They must not dispatch work, execute commands, write files, create branches, create worktrees, reassign workers, close out workers, or mutate anything by themselves.

Level 13.4 does not create runtime ownership or lock behavior.

## Ownership Zone Preview

Future ownership zones must include:

- ownership_zone_id.
- lane.
- owning_worker_id.
- task_id.
- run_id.
- owned_files.
- allowed_files.
- forbidden_files.
- protected_paths.
- active_lock_ids.
- conflicting_worker_ids.
- stale_policy.
- handoff_policy.
- closeout_policy.
- event_ledger_plan.
- created_at.
- updated_at.

Ownership zones must be explicit before dispatch. Ambiguous ownership must block orchestration.

## File Lock Preview

Future file locks must include:

- file_lock_id.
- ownership_zone_id.
- worker_id.
- task_id.
- run_id.
- locked_file.
- lock_mode: observe, preview, dry_run, or approved_mutation.
- allowed_operations.
- forbidden_operations.
- expires_at.
- stale_after.
- released_at.
- release_reason.
- conflict_references.
- event_ledger_plan.

Future file locks must not grant mutation authority unless a separate future boundary explicitly approves the exact operation.

## Lock Grant Rules

Future lock grant may be eligible only when:

- worker exists.
- lease exists when dispatch is involved.
- ownership zone exists.
- locked files are within allowed_files.
- locked files are outside forbidden_files.
- protected paths are not in scope.
- Source Proxy stress files are not in scope without a future separate lane.
- `/coding` UI files are not in scope without a future separate lane.
- no active conflict exists.
- expiration exists.
- stale policy exists.
- event ledger plan exists.

Lock grant is advisory until future focused implementation and tests exist.

## Lock Conflict Rules

Future lock conflict must be reported when:

- another active worker owns the same file.
- another active lock overlaps the same file.
- forbidden files match.
- protected paths are requested.
- dirty worktree state conflicts with requested ownership.
- Source Proxy stress lane conflicts.
- `/coding` UI lane conflicts.
- Scout, proxy memory, or blueprint lane conflicts.

Conflicts must block mutation dispatch by default.

## Stale And Release Rules

Future stale locks must block unsafe dispatch and reassignment.

Lock release must be ledgered and visible.

Lock release must not clean up files, stash work, checkout files, delete branches, delete worktrees, execute rollback, write receipts, write evidence, or reassign work unless a future separate approved action exists.

## Event Ledger Requirements

Future ownership and lock behavior must be ledger-visible.

Expected future events may include:

- ownership_zone_created.
- ownership_zone_blocked.
- file_lock_requested.
- file_lock_granted.
- file_lock_blocked.
- file_lock_marked_stale.
- file_lock_released.

Level 13.4 does not implement ledger storage or emit runtime ledger events.

## Fail-Closed Rules

Future ownership zones and file locks must fail closed when:

- ownership zone is missing.
- worker id is missing.
- task id is missing.
- allowed_files are missing.
- forbidden_files are missing.
- locked file is outside allowed_files.
- locked file intersects forbidden_files.
- protected paths are in scope.
- Source Proxy stress files are in scope without a future separate lane.
- `/coding` UI files are in scope without a future separate lane.
- active lock conflict exists.
- dirty worktree conflict exists.
- expiration is missing.
- stale policy is missing.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Lock Uses

Future ownership zones and file locks must never authorize:

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

Future locks must treat unexpected HEAD or git status changes as blocking conditions for grant, dispatch, reassignment, handoff, branch/worktree proposal escalation, or closeout.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 13.5: Conflict Detection Dry Run Boundary
- Level 13.6: Handoff Packet Boundary
- Level 13.7: Branch Worktree Proposal Boundary
- Level 13.8: Worker Closeout Boundary
- Level 13.9: Level 13 Closeout And Level 14 Gate

Do not implement any of these in Level 13.4.

## Required Future Tests

Future source-code increments must prove:

- ownership zone state does not dispatch work by itself.
- file lock state does not mutate files by itself.
- lock grant is blocked when ownership zone is missing.
- lock grant is blocked when worker id is missing.
- lock grant is blocked when allowed_files are missing.
- lock grant is blocked when forbidden_files are missing.
- lock grant is blocked when locked file is outside allowed_files.
- lock grant is blocked when forbidden_files match.
- active lock conflict blocks mutation dispatch.
- dirty worktree conflict blocks dispatch.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
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

git diff --check -- docs/cartographer-level-13-ownership-zone-file-lock-preview.md

grep -n "Ownership Zone And File Lock Preview\|Ownership Zone Preview\|File Lock Preview\|Lock Conflict Rules\|Level 13.5: Conflict Detection Dry Run Boundary" docs/cartographer-level-13-ownership-zone-file-lock-preview.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-13-ownership-zone-file-lock-preview.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 13.4 creates the Ownership Zone And File Lock Preview only.

Expected result:

- no ownership lock runtime enabled.
- no file lock runtime enabled.
- no worker lease runtime enabled.
- no worker registry runtime enabled.
- no task dispatch enabled.
- no conflict detection runtime enabled.
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

Level 13.5: Conflict Detection Dry Run Boundary
