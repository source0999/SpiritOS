# Cartographer Live Operation Step 8: Operator Dashboard Controls Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document starts Step 8 as a docs-first plan for future operator dashboard controls.

Step 8 planning defines how a future dashboard or operator-control surface could display Cartographer state, approvals, blocked actions, and kill switch status. It does not implement dashboard UI, mutate dashboard components, write runtime code, execute commands, execute queue items, enable live autonomy, grant limited unattended operation, or grant full auto.

Limited unattended operation is not granted. Full auto is not granted.

## Scope

Step 8 may plan:

- Operator control concepts.
- Dashboard display boundaries.
- Kill switch control boundaries.
- Approval visibility boundaries.
- Protected lane dashboard barriers.
- Manual checks before any future implementation.

Step 8 may not implement UI, dashboard components, runtime modules, tests, command runners, queue execution, package changes, config changes, or `/coding` shell changes.

## Non-Scope

This Step 8 planning pass does not:

- Build dashboard UI.
- Mutate dashboard components.
- Mutate `/coding` shell or UI files.
- Mutate `source_proxy/cartographer` runtime modules.
- Mutate `source_proxy/tests`.
- Mutate `package.json` or config files.
- Create approvals.
- Self-approve.
- Execute queue items.
- Run commands through Cartographer.
- Write evidence.
- Write receipts.
- Create branches or worktrees.
- Commit, push, merge, stash, checkout, clean, or delete.
- Enable limited unattended operation.
- Enable full auto.

## Operator Dashboard Definition

A future operator dashboard is a human-facing control and review surface.

It may show state, warnings, recommendations, approval requirements, blocked actions, and kill switch status. It must not turn display state into action authority.

A dashboard button, indicator, card, toggle, or status row is not approval by itself. It cannot execute queue items, run commands, generate approvals, self-approve, or mutate protected lanes unless a later exact package separately implements and proves that behavior.

## Candidate Future Controls

Future operator controls may include conceptual plans for:

- Read-only state display.
- Blocked action display.
- Approval requirement display.
- Queue preview display.
- Event summary display.
- Kill switch status display.
- Manual operator next-step display.

These are concepts only. Step 8 does not implement them.

## Forbidden Dashboard Behaviors

Forbidden behaviors include:

- One-click live autonomy.
- Full auto toggle.
- Limited unattended operation toggle.
- Self-approval controls.
- Queue execution controls.
- Command execution controls.
- Broad write controls.
- Branch/worktree controls.
- Commit/push/merge controls.
- Stash/checkout/clean/delete controls.
- `/coding` mutation controls.
- Runtime/test mutation controls.
- Package/config mutation controls.

## Manual Checks

After Step 8 planning, manually verify:

- `git diff --check` passes.
- Step 8 docs exist.
- Step 8 says operator dashboard controls are not implemented now.
- Step 8 says dashboard display does not imply authority.
- Step 8 blocks full auto, limited unattended operation, self-approval, queue execution, command execution, broad writes, git mutation, `/coding` mutation, runtime/test mutation, and package/config mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is a docs-only operator dashboard controls plan.

No UI, dashboard component, runtime code, tests, command runners, queue execution, write files, approval generation, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-8-operator-dashboard-controls-plan.md`

Rollback must not touch `/coding` work, runtime modules, tests, dashboard components, package/config files, branches, worktrees, commits, stashes, generated files, or unrelated dirty files.

## Stop Conditions

Stop immediately if:

- Step 8 implements dashboard UI.
- Step 8 mutates dashboard components.
- Step 8 grants dashboard-driven approval, command execution, queue execution, write authority, self-approval, limited unattended operation, or full auto.
- Step 8 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 8.1: Dashboard Display-Only Contract
