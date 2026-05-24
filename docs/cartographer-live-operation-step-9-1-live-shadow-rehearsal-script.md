# Cartographer Live Operation Step 9.1: Live Shadow Rehearsal Script

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines a planning-only live shadow rehearsal script.

The script is a human operator checklist, not automation. It does not run commands through Cartographer, schedule jobs, write reports, mutate state, or enable autonomy.

Limited unattended operation is not granted. Full auto is not granted.

## Rehearsal Steps

A future human-led rehearsal may ask the operator to review:

- Current HEAD.
- Dirty tree summary.
- Protected lane matches.
- Read-only observation contract.
- Recommendation packet shape.
- Queue preview inertness.
- Approval token requirements.
- First safe write class boundaries.
- Controlled command boundaries.
- Dashboard display-only boundaries.
- Kill switch status.
- Blocked action findings.
- Manual next-step recommendations.

## Rehearsal Rules

The rehearsal must:

- Remain human-led.
- Remain read-only unless a later exact package grants authority.
- Treat all recommendations as inert.
- Treat all queue previews as non-executable.
- Treat dashboard display as non-authoritative.
- Treat missing approval as blocked.
- Treat stale HEAD as blocked.
- Treat dirty-tree mismatch as blocked.
- Treat protected lane matches as blocked.
- Treat kill switch active, missing, or ambiguous as blocked.

## Forbidden Rehearsal Behavior

The rehearsal must not:

- Execute queue items.
- Run commands through Cartographer.
- Write files.
- Write evidence.
- Write receipts.
- Generate approvals.
- Self-approve.
- Schedule recurring jobs.
- Create monitors or automations.
- Select tasks automatically.
- Mutate dashboard UI.
- Mutate `/coding`, runtime, tests, package, or config files.

## Manual Checks

After Step 9.1, manually verify:

- `git diff --check` passes.
- The Step 9.1 doc exists.
- Rehearsal steps are human review steps only.
- Rehearsal rules treat recommendations, queue previews, dashboard display, missing approval, stale HEAD, dirty-tree mismatch, protected lane matches, and kill switch failures as inert or blocked.
- Forbidden rehearsal behavior blocks queue execution, command execution, writes, evidence/receipt writes, approval generation, self-approval, scheduled jobs, monitors, automations, automatic task selection, dashboard mutation, and protected-lane mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only live shadow rehearsal script.

No runtime code, tests, scheduled jobs, monitors, automations, soak reports, evidence files, receipt files, command runners, queue execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-9-1-live-shadow-rehearsal-script.md`

## Stop Conditions

Stop immediately if:

- Step 9.1 becomes automation instead of a human checklist.
- Step 9.1 schedules jobs, monitors, or automations.
- Step 9.1 grants command execution, queue execution, write authority, self-approval, limited unattended operation, or full auto.
- Step 9.1 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 9.2: Soak Drift Review Contract
