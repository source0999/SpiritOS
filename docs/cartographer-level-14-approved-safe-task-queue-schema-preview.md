# Cartographer Level 14.2 Approved Safe Task Queue Schema Preview

status: safe-task-queue-schema-preview-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 14.2 previews the future approved safe-task queue schema.

This increment is docs-only. It does not implement queues, schedulers, workers, autonomy, APIs, services, tests, UI, runtime execution, writes, receipts, evidence, commits, pushes, merges, cleanup, or background mutation.

## Starting Point

Level 14.1 created the Autonomous Operator Experience Boundary Contract.

Level 14.2 defines queue shape only and grants no queue authority.

## Scope

Allowed:

- define future queue fields.
- define queue eligibility and block rules.
- run doc-only verification commands.

Forbidden:

- queue runtime.
- automatic selection.
- automatic execution.
- runtime mutation.
- Source Proxy stress mutation.
- `/coding` UI mutation.

## Approved Safe Task Queue Schema Preview

Future queue records must include:

- queue_item_id.
- run_id.
- task_class.
- trust_tier.
- lane.
- requested_by.
- approved_by.
- allowed_files.
- forbidden_files.
- required_approval_mode.
- max_attempts.
- rollback_required.
- verification_required.
- kill_switch_scope.
- status.
- created_at.
- expires_at.
- blocked_reason.

## Queue Eligibility Rules

A future queue item may be eligible only when the task class is approved, trust tier is explicit, allowed and forbidden files are explicit, rollback and verification requirements are known, and lane isolation is clear.

Eligibility does not mean execution.

## Queue Block Rules

Future queue items must be blocked when approval is missing, scope is broad, task class is unknown, trust tier is missing, protected paths are included, Source Proxy stress files are included, `/coding` UI files are included without a separate lane, HEAD changed unexpectedly, git status changed unexpectedly, or hidden mutation is suspected.

## Required Future Implementation Shape

Future Level 14 work must remain incremental:

- Level 14.3: Safe Task Class And Trust Tier Boundary
- Level 14.4: Kill Switch And Stop Control Boundary
- Level 14.5: Recurring Health Check Boundary
- Level 14.6: Blueprint Refresh Proposal Boundary
- Level 14.7: Safe Docs Evidence Maintenance Boundary
- Level 14.8: Autonomous Escalation And Closeout Proposal Boundary
- Level 14.9: Level 14 Closeout And Final Review Gate

Do not implement any of these in Level 14.2.

## Required Future Tests

Future tests must prove queue items do not execute by being created, unknown task classes are blocked, broad file scope is blocked, protected paths remain blocked, Source Proxy stress files remain blocked, `/coding` UI files remain blocked unless separately allowed, no self-approval exists, and failures are honest.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-14-approved-safe-task-queue-schema-preview.md

grep -n "Approved Safe Task Queue Schema Preview\|Queue Eligibility Rules\|Queue Block Rules\|Required Future Tests\|Level 14.3: Safe Task Class And Trust Tier Boundary" docs/cartographer-level-14-approved-safe-task-queue-schema-preview.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-14-approved-safe-task-queue-schema-preview.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 14.2 creates the Approved Safe Task Queue Schema Preview only.

No queue runtime, automatic selection, automatic execution, write authority, local execution authority, commit/push/merge authority, self-approval, cleanup, Source Proxy stress mutation, or `/coding` UI mutation is enabled.

## Next Increment

Level 14.3: Safe Task Class And Trust Tier Boundary
