# Cartographer Level 14.5 Recurring Health Check Boundary

status: recurring-health-check-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 14.5 defines the future boundary for recurring project health checks.

This increment is docs-only and does not implement scheduling, monitors, commands, or runtime checks.

## Starting Point

Level 14.4 defined kill switch and stop control boundaries.

Level 14.5 defines recurring health check contracts only.

## Scope

Allowed:

- define future health check packet shape.
- define allowed future check classes.
- define block rules.
- run doc-only verification commands.

Forbidden:

- cron or scheduler changes.
- monitor runtime.
- command execution.
- source, test, UI, or runtime edits.
- Source Proxy stress mutation.
- `/coding` UI mutation.

## Health Check Packet Preview

Future health check packets must include:

- health_check_id.
- run_id.
- task_class.
- lane.
- schedule_hint.
- read_targets.
- forbidden_targets.
- command_preview.
- expected_outputs.
- kill_switch_scope.
- rollback_required.
- verification_required.
- status.
- blocked_reason.

## Allowed Future Check Classes

Future check classes may include docs freshness review, roadmap drift review, dirty worktree summary, open gate summary, and manual-check reminder proposals.

They must remain read-only unless a future approved safe-task class explicitly grants scoped write authority.

## Health Check Block Rules

Future health checks must block when they imply source mutation, Source Proxy stress mutation, `/coding` UI mutation, protected path access, secrets access, cleanup, commit, push, merge, broad command execution, or autonomous escalation without approval.

## Required Future Implementation Shape

Future Level 14 work must remain incremental:

- Level 14.6: Blueprint Refresh Proposal Boundary
- Level 14.7: Safe Docs Evidence Maintenance Boundary
- Level 14.8: Autonomous Escalation And Closeout Proposal Boundary
- Level 14.9: Level 14 Closeout And Final Review Gate

Do not implement any of these in Level 14.5.

## Required Future Tests

Future tests must prove recurring health checks do not mutate files, run only approved read classes, respect kill switches, block protected paths, block Source Proxy stress files, block `/coding` UI files unless separately allowed, and never commit, push, merge, or self-approve.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-14-recurring-health-check-boundary.md

grep -n "Recurring Health Check Boundary\|Health Check Packet Preview\|Allowed Future Check Classes\|Health Check Block Rules\|Level 14.6: Blueprint Refresh Proposal Boundary" docs/cartographer-level-14-recurring-health-check-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-14-recurring-health-check-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 14.5 creates the Recurring Health Check Boundary only.

No scheduler, monitor runtime, command execution, write authority, local execution authority, commit/push/merge authority, self-approval, cleanup, Source Proxy stress mutation, or `/coding` UI mutation is enabled.

## Next Increment

Level 14.6: Blueprint Refresh Proposal Boundary
