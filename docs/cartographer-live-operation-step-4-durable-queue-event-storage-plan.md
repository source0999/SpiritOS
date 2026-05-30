# Cartographer Live Operation Step 4: Durable Queue And Event Storage Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document starts Step 4 as a docs-first plan for future durable queue and event storage.

Step 4 planning defines how durable queue and event storage may later be introduced as inert audit and preview infrastructure. It does not implement storage, create storage files, write events, write queue items, execute queue items, run commands through Cartographer, generate approvals, approve itself, or enable live autonomy.

Limited unattended operation is not granted. Full auto is not granted.

## Scope

Step 4 may plan:

- Durable queue storage boundaries.
- Event storage boundaries.
- Inert queued action previews.
- Event record concepts.
- Fail-closed storage behavior.
- Manual checks before any future implementation.

Step 4 may not implement runtime modules, tests, database migrations, storage files, queue runners, event writers, approval tokens, command execution, queue execution, dashboard UI, or `/coding` shell changes.

## Non-Scope

This Step 4 planning pass does not:

- Create durable queue/event storage.
- Write queue items.
- Write event records.
- Execute queue items.
- Run commands through Cartographer.
- Write evidence.
- Write receipts.
- Generate approvals.
- Self-approve.
- Implement human approval token flow.
- Enable limited unattended operation.
- Enable full auto.
- Touch `/coding` shell or UI implementation files.
- Touch `source_proxy/cartographer` runtime modules.
- Touch `source_proxy/tests`.

## Durable Queue Definition

Future durable queue storage means an inert representation of proposed actions that may be reviewed by an operator.

Durable queue storage does not imply execution. A stored queue item is not permission to act, not approval, not evidence, not a receipt, not a command invocation, and not a task selection decision.

Future queue records must remain blocked until a later human approval token flow is separately planned, implemented, and proven.

## Event Storage Definition

Future event storage means an inert audit-style record of observations, recommendations, blocked decisions, and operator-visible state transitions.

Event storage does not grant authority. An event record is not approval, not execution, not evidence, not a receipt, and not a command invocation.

## Why Step 4 Follows Step 3

Step 3 established read-only observation, inert recommendation packets, blocked action classes, and operator review packets.

Step 4 may now plan durable storage around those inert concepts. It must preserve the Step 3 rule that observation and recommendation do not become action authority.

## Required Boundaries

Future durable queue/event storage must:

- Treat all queue items as preview-only until a later approval-token step.
- Treat all event records as audit/review data only.
- Fail closed when approval data is missing.
- Fail closed when HEAD is stale.
- Fail closed when dirty-tree expectations mismatch.
- Fail closed when protected paths are present.
- Fail closed when the requested action class is forbidden.
- Fail closed when the trust tier is above the approved tier.
- Fail closed on ambiguous authority.

## Forbidden Actions

Step 4 planning and any future Step 4 implementation must not:

- Execute queue items.
- Run local commands through Cartographer.
- Write evidence.
- Write receipts.
- Generate approvals.
- Self-approve.
- Select tasks automatically.
- Create branches.
- Create worktrees.
- Commit, push, or merge.
- Stash, checkout, clean, or delete.
- Mutate `/coding` shell or UI files.
- Mutate runtime modules without a later exact approval.
- Mutate tests without a later exact approval.

## Proposed Future Storage Shape

This is a proposal only and must not be implemented in this session.

Future storage could be separated into:

- Durable queue preview records.
- Event audit records.
- Blocked action records.
- Operator review snapshots.

Each record type must be inert unless a later approved step explicitly adds a separate execution or write class. Step 4 does not add execution or write authority.

## Manual Checks

After Step 4 planning, manually verify:

- `git diff --check` passes.
- Step 4 docs exist.
- Step 4 says durable queue/event storage is not implemented now.
- Step 4 says queue storage does not imply execution.
- Step 4 says event storage does not imply approval or authority.
- Step 4 does not grant command execution through Cartographer.
- Step 4 does not grant queue execution.
- Step 4 does not grant approval generation or self-approval.
- Step 4 does not grant limited unattended operation.
- Step 4 does not grant full auto.
- `/coding` files were not edited by Step 4.
- `source_proxy/cartographer` runtime modules were not edited by Step 4.
- `source_proxy/tests` were not edited by Step 4.

## Expected Output

Expected output is a docs-only durable queue and event storage plan.

No runtime code, tests, durable storage files, queue items, event records, approval token flow, queue execution, command execution, live autonomy, `/coding` mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-4-durable-queue-event-storage-plan.md`

Rollback must not touch `/coding` work, runtime modules, tests, branches, worktrees, commits, stashes, generated files, or unrelated dirty files.

## Stop Conditions

Stop immediately if:

- Step 4 creates storage files or runtime storage.
- Step 4 creates queue items or event records.
- Step 4 executes queue items.
- Step 4 runs commands through Cartographer.
- Step 4 creates approval tokens.
- Step 4 grants limited unattended operation or full auto.
- Step 4 touches `/coding`, runtime, or test files.

## Next Recommended Increment

Step 4.1: Durable Storage Inertness Contract
