# Cartographer Level 14.4 Kill Switch And Stop Control Boundary

status: kill-switch-stop-control-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 14.4 defines future kill switch and stop control boundaries.

This increment is docs-only and does not implement runtime stop controls.

## Starting Point

Level 14.3 defined safe task class and trust tier boundaries.

Level 14.4 defines stop-control contracts only.

## Scope

Allowed:

- define future kill switch scopes.
- define future stop packet shape.
- define stop conditions.
- run doc-only verification commands.

Forbidden:

- runtime kill switch implementation.
- process control.
- command execution.
- cleanup.
- Source Proxy stress mutation.
- `/coding` UI mutation.

## Kill Switch Scope Rules

Future kill switches must support global, lane, queue, task, worker, and run scopes.

The broadest active stop control must win. A stopped scope must block new autonomous selection, new execution, retries, handoffs, and closeouts until explicitly cleared by an authorized operator action.

## Stop Control Packet Preview

Future stop packets must include:

- stop_packet_id.
- scope_type.
- scope_id.
- reason.
- requested_by.
- created_at.
- expires_at.
- clears_allowed_by.
- affected_queue_items.
- affected_workers.
- blocked_actions.

## Stop Conditions

Future autonomy must stop on operator kill switch, expired approval, unexpected HEAD change, unexpected git status change, protected path touch, Source Proxy stress lane touch, `/coding` UI lane touch, verification failure, rollback failure, hidden mutation suspicion, or repeated failure.

## Required Future Implementation Shape

Future Level 14 work must remain incremental:

- Level 14.5: Recurring Health Check Boundary
- Level 14.6: Blueprint Refresh Proposal Boundary
- Level 14.7: Safe Docs Evidence Maintenance Boundary
- Level 14.8: Autonomous Escalation And Closeout Proposal Boundary
- Level 14.9: Level 14 Closeout And Final Review Gate

Do not implement any of these in Level 14.4.

## Required Future Tests

Future tests must prove kill switch state blocks new work, per-worker stops block worker activity, global stops override lower scopes, stopped queues do not execute, retries stop when blocked, protected paths remain blocked, and failures are honest.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-14-kill-switch-and-stop-control-boundary.md

grep -n "Kill Switch And Stop Control Boundary\|Kill Switch Scope Rules\|Stop Control Packet Preview\|Stop Conditions\|Level 14.5: Recurring Health Check Boundary" docs/cartographer-level-14-kill-switch-and-stop-control-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-14-kill-switch-and-stop-control-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 14.4 creates the Kill Switch And Stop Control Boundary only.

No kill switch runtime, process control, automatic execution, write authority, local execution authority, commit/push/merge authority, self-approval, cleanup, Source Proxy stress mutation, or `/coding` UI mutation is enabled.

## Next Increment

Level 14.5: Recurring Health Check Boundary
