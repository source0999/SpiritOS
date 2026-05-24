# Cartographer Live Operation Package A: Step 3 To Step 5 Sequencing

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Package A Overview

Package A is the future live-operation package covering:

- Step 3: Read-only live mode.
- Step 4: Durable queue and event storage.
- Step 5: Human approval token flow.

This document sequences those steps without implementing them.

Package A is not implemented now. Step 4 durable queue/event storage is not implemented now. Step 5 human approval token flow is not implemented now. Limited unattended operation is not granted. Full auto is not granted.

## Step 3: Read-Only Live Mode

Step 3 defines the read-only live observation and recommendation boundary.

Step 3 may plan how Cartographer later observes exact approved repo state, such as git status summary, current HEAD, changed file list, known Cartographer docs, existing proof closeout docs, existing plan docs, existing test names, and existing route names if later needed.

Step 3 may produce operator-facing recommendation plans only. It must not write files, execute commands through Cartographer, execute queue items, generate approvals, approve itself, create branches/worktrees, commit, push, merge, stash, checkout, clean, delete, touch `/coding` UI files, or mutate runtime state.

## Step 4: Durable Queue And Event Storage

Step 4 may later introduce durable queue and event storage as inert infrastructure.

Step 4 is not implemented now.

When separately approved later, Step 4 must prove that durable storage does not imply queue execution, action authority, command execution, unattended operation, approval generation, or protected-lane mutation.

## Step 5: Human Approval Token Flow

Step 5 may later introduce a human approval token flow.

Step 5 is not implemented now.

When separately approved later, Step 5 must bind operator id, token id, run id, action type, exact allowed files, exact forbidden files, expiry, rollback, verification, current HEAD, dirty-tree expectation, kill switch state, and trust tier.

Step 5 must fail closed on missing fields, expired approval, stale HEAD, dirty-tree mismatch, forbidden paths, forbidden action classes, ambiguous authority, and self-approval.

## Why Step 3 Must Stay Docs/Planning First In This Session

Step 3 must stay docs/planning first because the repo already has active parallel work and the first live-operation increment must not conflict with `/coding` shell work.

This session establishes the observation contract and lane boundary only. It does not implement runtime code, tests, storage, tokens, command execution, queue execution, live autonomy, limited unattended operation, or full auto.

Planning the read-only boundary first prevents later Step 4 storage or Step 5 approval work from being mistaken for action authority.

## What Step 3 Can Prepare For Step 4 Without Implementing Step 4

Step 3 can prepare:

- The allowed observation list that future storage may reference.
- The blocked action classes that future queue storage must preserve.
- The recommendation packet concept that future storage may preview.
- The requirement that any future queue/event entry remains inert unless separately approved.
- The requirement that missing or ambiguous approval data fails closed.

Step 3 must not create durable storage, event ledgers, queue files, queue runners, queue execution paths, database migrations, or runtime modules.

## What Step 3 Can Prepare For Step 5 Without Implementing Step 5

Step 3 can prepare:

- The authority boundary that future approval tokens must respect.
- The exact no-write/no-execute classes that tokens must not bypass.
- The future need for exact allowed files and exact forbidden files.
- The future need for HEAD and dirty-tree matching.
- The future need to block self-approval.
- The future need to preserve kill switch fail-closed behavior.

Step 3 must not create approval tokens, approval schemas, token stores, token validators, approver identities, approval generation paths, or self-approval paths.

## Boundaries For Future Implementation

Step 4 may introduce durable storage later, but not now.

Step 5 may introduce live approval token flow later, but not now.

Any future implementation must be separately approved, narrowly scoped, and reviewed against protected lanes before files are touched.

Future implementation must not treat Step 3 recommendations as authority to execute, write, approve, branch, worktree, commit, push, merge, stash, checkout, clean, delete, or mutate `/coding` shell work.

## Manual Checks

Before any future Package A implementation, manually verify:

- Step 3 remains read-only observation and recommendation only.
- Step 4 storage is separately approved before any durable queue/event files are created.
- Step 5 approval token flow is separately approved before any token files or validators are created.
- `/coding` shell and UI files remain protected.
- `source_proxy/cartographer` runtime files are not edited by this Step 3 docs pass.
- `source_proxy/tests` are not edited by this Step 3 docs pass.
- Limited unattended operation is not granted.
- Full auto is not granted.
- Queue execution is not implemented.
- Human approval token flow is not implemented.

## Expected Output

Expected output is sequencing clarity for Package A:

- Step 3 plans read-only live mode first.
- Step 4 remains a later durable queue/event storage step.
- Step 5 remains a later human approval token flow step.
- No live operation, runtime mutation, queue execution, durable storage, approval token flow, command execution, or unattended operation is implemented now.

## Rollback Notes

Rollback for this document is limited to removing:

- `docs/cartographer-live-operation-package-a-step-3-to-5-sequencing.md`

Rollback must not touch `/coding` shell files, Cartographer runtime modules, tests, queue storage, token storage, branches, worktrees, commits, stashes, generated files, or unrelated dirty files.

## Stop Conditions

Stop immediately if:

- Step 3 implementation attempts to create Step 4 durable queue/event storage.
- Step 3 implementation attempts to create Step 5 human approval token flow.
- Any write behavior is introduced.
- Any command execution through Cartographer is introduced.
- Any queue execution is introduced.
- Any limited unattended operation is granted.
- Any full auto is granted.
- Any `/coding` shell or UI file is touched.
- Any `source_proxy/cartographer` runtime module or `source_proxy/tests` file is touched.

## Next Recommended Increment

Step 3.1: Read-Only Live Observation Contract
