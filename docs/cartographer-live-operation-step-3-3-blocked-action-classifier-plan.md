# Cartographer Live Operation Step 3.3: Blocked Action Classifier Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines a planning-only blocked action classifier for future Cartographer read-only live mode.

The classifier concept labels requested work as blocked when it requires authority outside Step 3. It does not execute actions, write files, create queue items, persist events, generate approvals, approve itself, or mutate state.

Limited unattended operation is not granted. Full auto is not granted.

## Scope

Step 3.3 may define:

- Blocked action classes.
- Protected lane matches.
- Fail-closed classifier behavior.
- Operator-facing blocked-action output.

Step 3.3 may not implement classifier runtime code, tests, storage, tokens, command execution, queue execution, or `/coding` UI changes.

## Blocked Action Classes

Future read-only mode must classify these actions as blocked:

- File writes.
- Evidence writes.
- Receipt writes.
- Durable queue writes.
- Event storage writes.
- Queue execution.
- Local command execution through Cartographer.
- Automatic task selection.
- Approval generation.
- Self-approval.
- Branch creation.
- Worktree creation.
- Commit, push, or merge.
- Stash, checkout, clean, or delete.
- `/coding` shell or UI mutation.
- `source_proxy/cartographer` runtime mutation.
- `source_proxy/tests` mutation.
- Package, config, environment, generated, Scout, dashboard, or API mutation.

## Protected Lane Matches

The classifier must treat these path families as protected during Step 3:

- `src/app/coding/`
- `src/components/coding/`
- `src/lib/coding/`
- `/coding` shell files.
- `/coding` UI implementation files.
- `source_proxy/cartographer/`
- `source_proxy/tests/`
- `source_proxy/api/`
- Package files.
- Config files.
- Environment files.
- Generated files.
- Scout files.
- Dashboard components.

Path matches produce blocked-action findings only. They do not authorize cleanup, checkout, stash, delete, or mutation.

## Fail-Closed Rules

The classifier must fail closed when:

- The requested action class is unknown.
- The requested file scope is ambiguous.
- The requested trust tier is above Tier 1.
- The request includes a protected lane.
- The request requires command execution through Cartographer.
- The request requires queue execution.
- The request requires a write.
- The request requires approval generation or self-approval.
- HEAD or dirty-tree expectations are missing when they are required by a future package.

Fail-closed means the output is a blocked recommendation for human review, not an automated action.

## Operator-Facing Output

A blocked-action finding may include:

- `blocked: true`.
- Blocked action class.
- Protected path match if present.
- Reason for block.
- Trust tier mismatch if present.
- Recommended manual operator next step.

This output is conceptual only and must not be written as evidence, receipt, event, queue item, or approval.

## No-Write/No-Execute Boundary

Step 3.3 does not grant file writes, queue execution, command execution through Cartographer, automatic task selection, approval generation, self-approval, branch/worktree creation, commit/push/merge, stash/checkout/clean/delete, `/coding` mutation, runtime mutation, or test mutation.

## Manual Checks

After Step 3.3, manually verify:

- `git diff --check` passes.
- The Step 3.3 doc exists.
- The blocked action classes include writes, evidence writes, receipt writes, queue execution, command execution through Cartographer, automatic task selection, approval generation, self-approval, git mutation, `/coding` mutation, runtime mutation, and test mutation.
- The classifier is conceptual only.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only blocked action classifier plan.

No runtime classifier, tests, durable storage, approval token flow, queue execution, command execution, live autonomy, `/coding` mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-3-3-blocked-action-classifier-plan.md`

## Stop Conditions

Stop immediately if:

- The classifier is implemented in runtime code.
- The classifier can execute or approve actions.
- Any blocked action class is treated as allowed.
- Any `/coding`, runtime, test, package, config, environment, generated, Scout, dashboard, or API file is touched.
- Any limited unattended operation or full auto is granted.

## Next Recommended Increment

Step 3.4: Operator Review Packet Plan
