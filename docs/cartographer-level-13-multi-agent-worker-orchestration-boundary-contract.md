# Cartographer Level 13 Multi-Agent Worker Orchestration Boundary Contract

status: planning-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 13.1 defines the boundary contract for future multi-agent and multi-worker orchestration.

This increment is docs-only. It does not implement worker orchestration, worker registry, worker leases, task dispatch, branch proposals, worktree proposals, branch creation, worktree creation, ownership locks, conflict detection, APIs, service builders, tests, UI, workflow runtime, local execution, writes, receipts, evidence, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No orchestration authority, worker authority, branch/worktree authority, write authority, local execution authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 12.9 closed the Level 12 Durable Workflow Autopilot planning sequence and locked the Level 13 gate.

The operator has explicitly requested the next increment after Level 12.9. That request opens Level 13.1 planning only. It does not authorize Level 13 implementation, worker orchestration, task dispatch, branch/worktree proposals, branch/worktree creation, Source Proxy stress-lane work, `/coding` UI work, Scout writes, proxy memory writes, blueprint writes, commit, push, merge, cleanup, or background mutation.

## Scope

Allowed in this increment:

- create this Level 13.1 boundary contract document.
- define future worker orchestration concepts.
- define future worker identity, lease, ownership, and conflict rules.
- define future lane isolation and dispatch requirements.
- define future implementation and test expectations.
- run doc-only verification commands.
- observe unrelated dirty worktree state without modifying it.

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
- branch or worktree proposal implementation.
- branch or worktree creation.
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

## Non-Negotiable Boundary

Level 13.1 grants no orchestration authority. It is a planning boundary only.

Future Level 13 orchestration must be unlocked by exact increment, exact worker type, exact task type, exact ownership zone, exact file scope, explicit operator approval, focused tests, manual checks, rollback metadata, verification requirements, durable event trail, and fail-closed policy.

No roadmap, previous approval, passing check, Level 12 closeout, UI affordance, operator trust, successful dry run, or generated planning document may be interpreted as worker orchestration authority.

## Multi-Agent Worker Orchestration Definition

Multi-agent worker orchestration is future coordination across agents, workers, files, tasks, and ownership zones.

It must be:

- worker-bound.
- task-bound.
- lane-bound.
- file-scope-bound.
- lease-bound.
- approval-bound when dispatch or mutation is involved.
- conflict-checked.
- event-ledger-recorded.
- rollback-aware.
- verification-aware.
- fail-closed by default.

Multi-agent worker orchestration never means broad autonomy, hidden background execution, automatic reassignment, force overwrite, self-approval, branch/worktree authority by default, commit/push/merge authority, or cross-lane mutation.

## Worker Identity Requirements

Future worker identity must include:

- worker_id.
- worker_type.
- owner.
- assigned_task_id.
- assigned_run_id.
- assigned_lane.
- allowed_files.
- forbidden_files.
- status.
- lease_id.
- created_at.
- updated_at.
- stale_after.
- closeout_reference.

Worker identity must not grant authority by itself.

## Worker Lease Requirements

Future worker leases must be:

- worker-bound.
- task-bound.
- lane-bound.
- file-scope-bound.
- time-limited.
- revocable.
- event-ledger-recorded.
- fail-closed by default.

A lease must not authorize branch creation, worktree creation, commits, pushes, merges, cleanup, protected path mutation, Source Proxy stress mutation, `/coding` UI mutation, Scout writes, proxy memory writes, or blueprint writes unless a future separate boundary explicitly allows that exact authority.

## Ownership Zone Requirements

Future ownership zones must define:

- owned files.
- allowed files.
- forbidden files.
- protected paths.
- lane name.
- owning worker.
- conflicting workers.
- stale ownership policy.
- handoff policy.
- closeout policy.

Ownership zones must be explicit before dispatch. Ambiguous ownership must block orchestration.

## Dispatch Requirements

Future task dispatch must require:

- exact task id.
- exact worker id.
- exact worker type.
- exact lane.
- exact allowed files.
- exact forbidden files.
- exact command class when commands are involved.
- exact write class when writes are involved.
- approval requirement.
- verification requirement.
- rollback requirement.
- event ledger plan.

Level 13.1 does not implement dispatch.

## Conflict Detection Requirements

Future orchestration must detect:

- overlapping allowed files.
- conflicting forbidden files.
- active worker overlap.
- stale worker overlap.
- branch or worktree name collision.
- dirty worktree conflict.
- protected path conflict.
- Source Proxy stress lane conflict.
- `/coding` UI lane conflict.
- Scout, proxy memory, or blueprint lane conflict.

Conflict detection must block by default until explicit operator approval and a focused future implementation exist.

## Branch And Worktree Rules

Branch and worktree authority remains locked.

Future Level 13 may design branch or worktree proposals, but Level 13.1 grants no branch creation, no worktree creation, no checkout, no stash, no cleanup, no commit, no push, and no merge authority.

If branch or worktree authority is ever introduced, it must be approved branch/worktree authority only, with exact names, exact owner, exact allowed files, exact rollback notes, exact verification checks, and no push/merge authority.

## Allowed Future Level 13 Orchestration Classes

The following are future possible orchestration classes only:

1. approved worker registry preview.
2. approved worker lease preview.
3. approved ownership zone preview.
4. approved conflict detection dry run.
5. approved handoff packet preview.
6. approved branch/worktree proposal preview.
7. approved worker closeout preview.

Each orchestration class requires a future focused implementation increment and focused tests. None are implemented by Level 13.1.

## Forbidden Orchestration Behavior

The following remain forbidden:

- automatic execution without approval.
- global approval.
- self-approval.
- hidden background workers.
- hidden retries.
- unbounded loops.
- autonomous task selection.
- automatic promotion.
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

Cartographer may observe dirty worktree state and report it as unrelated pre-existing state.

Observation does not authorize cleanup, stash, checkout, overwrite, branch creation, worktree creation, commit, push, merge, reassignment, dispatch, or mutation of those files.

Dirty files in Source Proxy stress testing, `/coding` UI, source code, tests, package files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, or dashboard lanes must remain untouched unless a separate explicit future lane authorizes them.

Cross-lane mutation is blocked by default.

## Required Future Implementation Shape

Future Level 13 implementation must proceed in small increments.

A conservative future path may include:

- Level 13.2: Worker Identity And Registry Schema Preview
- Level 13.3: Worker Lease Boundary
- Level 13.4: Ownership Zone And File Lock Preview
- Level 13.5: Conflict Detection Dry Run Boundary
- Level 13.6: Handoff Packet Boundary
- Level 13.7: Branch Worktree Proposal Boundary
- Level 13.8: Worker Closeout Boundary
- Level 13.9: Level 13 Closeout And Level 14 Gate

Do not implement any of these in Level 13.1.

## Required Future Tests

Future source-code increments must test both allowed and forbidden behavior.

Future tests must prove:

- worker orchestration is blocked without explicit approval.
- task dispatch is blocked without exact worker assignment.
- task dispatch is blocked without exact allowed_files.
- task dispatch is blocked when forbidden_files match.
- ownership conflicts block dispatch.
- stale worker state blocks unsafe reassignment.
- dirty worktree conflicts block dispatch.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- Scout writes remain blocked unless separately approved.
- proxy memory writes remain blocked unless separately approved.
- blueprint writes remain blocked unless separately approved.
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

git diff --check -- docs/cartographer-level-13-multi-agent-worker-orchestration-boundary-contract.md

grep -n "Multi-Agent Worker Orchestration Boundary Contract\|Worker Identity Requirements\|Worker Lease Requirements\|Conflict Detection Requirements\|Level 13.2: Worker Identity And Registry Schema Preview" docs/cartographer-level-13-multi-agent-worker-orchestration-boundary-contract.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-13-multi-agent-worker-orchestration-boundary-contract.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 13.1 creates the Multi-Agent Worker Orchestration Boundary Contract only.

Expected result:

- no worker orchestration enabled.
- no worker registry enabled.
- no worker leases enabled.
- no ownership locks enabled.
- no conflict detection runtime enabled.
- no task dispatch enabled.
- no branch/worktree proposal runtime enabled.
- no branch/worktree creation enabled.
- no durable workflow runtime enabled.
- no approval token runtime authority enabled.
- no event ledger runtime authority enabled.
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

Level 13.2: Worker Identity And Registry Schema Preview
