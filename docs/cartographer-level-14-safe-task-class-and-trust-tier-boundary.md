# Cartographer Level 14.3 Safe Task Class And Trust Tier Boundary

status: safe-task-class-trust-tier-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 14.3 defines the future boundary for safe task classes and trust tiers.

This increment is docs-only and grants no autonomy or execution authority.

## Starting Point

Level 14.2 previewed approved safe-task queue shape.

Level 14.3 defines classification rules only.

## Scope

Allowed:

- define future safe task class rules.
- define future trust tier rules.
- define blocked classes.
- run doc-only verification commands.

Forbidden:

- runtime classification.
- automatic approval.
- task execution.
- Source Proxy stress mutation.
- `/coding` UI mutation.

## Safe Task Class Rules

Future safe task classes must be named, narrow, reversible, lane-bound, file-scope-bound, verification-aware, rollback-aware, and kill-switch-controlled.

Safe task classes must not include secrets, protected paths, production deployment, irreversible cleanup, cross-repo mutation, push, merge, Source Proxy stress mutation, or `/coding` UI mutation unless a future separate lane explicitly opens that scope.

## Trust Tier Rules

Future trust tiers must define maximum autonomy, allowed task classes, approval mode, allowed files, forbidden files, verification requirements, rollback requirements, max attempts, and stop conditions.

Trust tiers must not be global permission.

## Blocked Class Rules

Future classification must block unknown classes, broad classes, classes without rollback, classes without verification, classes with protected paths, classes that imply commit/push/merge, classes that imply cleanup, and classes with ambiguous lane ownership.

## Required Future Implementation Shape

Future Level 14 work must remain incremental:

- Level 14.4: Kill Switch And Stop Control Boundary
- Level 14.5: Recurring Health Check Boundary
- Level 14.6: Blueprint Refresh Proposal Boundary
- Level 14.7: Safe Docs Evidence Maintenance Boundary
- Level 14.8: Autonomous Escalation And Closeout Proposal Boundary
- Level 14.9: Level 14 Closeout And Final Review Gate

Do not implement any of these in Level 14.3.

## Required Future Tests

Future tests must prove unknown task classes are blocked, trust tier scope is enforced, broad task classes are blocked, protected paths remain blocked, Source Proxy stress files remain blocked, `/coding` UI files remain blocked unless separately allowed, no commit/push/merge authority exists, and no self-approval exists.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-14-safe-task-class-and-trust-tier-boundary.md

grep -n "Safe Task Class And Trust Tier Boundary\|Safe Task Class Rules\|Trust Tier Rules\|Blocked Class Rules\|Level 14.4: Kill Switch And Stop Control Boundary" docs/cartographer-level-14-safe-task-class-and-trust-tier-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-14-safe-task-class-and-trust-tier-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 14.3 creates the Safe Task Class And Trust Tier Boundary only.

No autonomy, automatic approval, automatic execution, write authority, local execution authority, commit/push/merge authority, self-approval, cleanup, Source Proxy stress mutation, or `/coding` UI mutation is enabled.

## Next Increment

Level 14.4: Kill Switch And Stop Control Boundary
