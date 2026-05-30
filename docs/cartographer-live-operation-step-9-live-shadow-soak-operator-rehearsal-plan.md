# Cartographer Live Operation Step 9: Live Shadow Soak And Operator Rehearsal Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document starts Step 9 as a docs-first plan for future live shadow soak and operator rehearsal.

Step 9 planning defines how a future operator-invoked live shadow rehearsal could observe, recommend, and report readiness without executing actions. It does not start a soak, schedule jobs, write soak reports, write evidence, mutate runtime, execute commands, execute queue items, enable live autonomy, grant limited unattended operation, or grant full auto.

Limited unattended operation is not granted. Full auto is not granted.

## Scope

Step 9 may plan:

- Live shadow soak objectives.
- Operator rehearsal boundaries.
- Observation-only rehearsal script.
- Drift and blocked-action review expectations.
- Stop conditions.
- Manual checks before any future implementation.

Step 9 may not implement runtime modules, tests, scheduled jobs, monitors, automations, dashboard UI, command runners, queue execution, package changes, config changes, or `/coding` shell changes.

## Non-Scope

This Step 9 planning pass does not:

- Start a live shadow soak.
- Schedule recurring jobs.
- Create monitors or automations.
- Write soak reports.
- Write evidence.
- Write receipts.
- Execute queue items.
- Run commands through Cartographer.
- Generate approvals.
- Self-approve.
- Mutate dashboard UI.
- Mutate `/coding` shell or UI files.
- Mutate `source_proxy/cartographer` runtime modules.
- Mutate `source_proxy/tests`.
- Mutate `package.json` or config files.
- Create branches or worktrees.
- Commit, push, merge, stash, checkout, clean, or delete.
- Enable limited unattended operation.
- Enable full auto.

## Live Shadow Soak Definition

A future live shadow soak is a time-boxed observation rehearsal.

It may compare live repo state to approved policies, produce recommendations, identify blocked action classes, and help a human operator practice review decisions. It must not execute actions, write state, approve actions, select tasks automatically, or mutate protected lanes.

## Operator Rehearsal Definition

An operator rehearsal is a human-led practice run.

The human operator reviews observation packets, queue previews, approval requirements, blocked actions, kill switch status, and manual next steps. Cartographer remains a read-only recommender unless a later exact package separately proves otherwise.

## Candidate Future Soak Window

A future soak may be planned for 24 to 72 hours only after explicit approval.

This document does not schedule that soak. The future soak must remain operator-invoked, observable, and non-mutating unless a later package grants exact authority.

## Manual Checks

After Step 9 planning, manually verify:

- `git diff --check` passes.
- Step 9 docs exist.
- Step 9 says live shadow soak is not started now.
- Step 9 says no recurring jobs, monitors, automations, evidence writes, receipt writes, command execution, queue execution, dashboard mutation, or runtime mutation are implemented.
- Step 9 keeps operator rehearsal human-led.
- Step 9 says limited unattended operation is not granted.
- Step 9 says full auto is not granted.

## Expected Output

Expected output is a docs-only live shadow soak and operator rehearsal plan.

No runtime code, tests, scheduled jobs, monitors, automations, soak reports, evidence files, receipt files, command runners, queue execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-9-live-shadow-soak-operator-rehearsal-plan.md`

Rollback must not touch `/coding` work, runtime modules, tests, dashboard components, package/config files, branches, worktrees, commits, stashes, generated files, or unrelated dirty files.

## Stop Conditions

Stop immediately if:

- Step 9 starts a soak.
- Step 9 schedules recurring jobs, monitors, or automations.
- Step 9 writes soak reports, evidence, or receipts.
- Step 9 enables command execution, queue execution, write authority, self-approval, limited unattended operation, or full auto.
- Step 9 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 9.1: Live Shadow Rehearsal Script
