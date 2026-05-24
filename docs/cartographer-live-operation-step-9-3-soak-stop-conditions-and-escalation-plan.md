# Cartographer Live Operation Step 9.3: Soak Stop Conditions And Escalation Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines planning-only stop conditions and escalation rules for a future live shadow soak.

Stop and escalation rules are human review guidance only. They do not implement alerts, monitors, automations, runtime checks, dashboard controls, command execution, queue execution, or write authority.

Limited unattended operation is not granted. Full auto is not granted.

## Stop Conditions

A future live shadow soak must stop if:

- HEAD is stale.
- Dirty-tree state mismatches expectation.
- Protected lane drift appears.
- `/coding` work appears in Cartographer diffs.
- Runtime or test files appear in live-operation diffs.
- `package.json` or config files appear in live-operation diffs.
- Kill switch is active, missing, or ambiguous.
- Approval scope is missing, expired, stale, ambiguous, or self-approved.
- Queue execution is requested.
- Command execution is requested without exact approval.
- Write authority is requested without exact approval.
- Limited unattended operation or full auto is implied.

## Escalation Rules

Escalation means reporting the stop condition to the human operator.

Escalation must not:

- Repair automatically.
- Execute queue items.
- Run commands through Cartographer.
- Write files.
- Write evidence.
- Write receipts.
- Generate approvals.
- Self-approve.
- Schedule jobs.
- Create branches or worktrees.
- Commit, push, merge, stash, checkout, clean, or delete.

## Operator Response

The human operator may decide to:

- Stop the soak.
- Reclassify dirty files manually.
- Narrow the observation scope.
- Update future docs.
- Decline further live-operation progression.
- Approve a later separate planning step.

Cartographer must not make that decision automatically.

## Manual Checks

After Step 9.3, manually verify:

- `git diff --check` passes.
- The Step 9.3 doc exists.
- Stop conditions include stale HEAD, dirty-tree mismatch, protected lane drift, `/coding` diffs, runtime/test diffs, package/config diffs, kill switch problems, approval problems, queue execution request, command execution request, write request, limited unattended operation, and full auto.
- Escalation rules block automatic repair, queue execution, command execution, writes, evidence/receipt writes, approval generation, self-approval, scheduled jobs, branches/worktrees, and git mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only soak stop conditions and escalation plan.

No runtime code, tests, scheduled jobs, monitors, automations, soak reports, evidence files, receipt files, command runners, queue execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-9-3-soak-stop-conditions-and-escalation-plan.md`

## Stop Conditions

Stop immediately if:

- Step 9.3 implements alerts, monitors, automations, or runtime checks.
- Step 9.3 turns escalation into automatic repair.
- Step 9.3 grants command execution, queue execution, write authority, self-approval, limited unattended operation, or full auto.
- Step 9.3 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 9.4: Live Shadow Soak Closeout And Step 10 Gate
