# Cartographer Live Operation Step 9.2: Soak Drift Review Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only drift review contract for a future live shadow soak.

Drift review compares observed state to expected policy and reports mismatches for human review. It does not write reports, evidence, receipts, queue items, events, or runtime state.

Limited unattended operation is not granted. Full auto is not granted.

## Drift Categories

Future drift review may classify:

- HEAD drift.
- Dirty-tree drift.
- Protected lane drift.
- Approval scope drift.
- Queue preview drift.
- Event summary drift.
- Kill switch state drift.
- Trust tier drift.
- Blocked action class drift.
- Manual verification drift.

## Drift Response Rules

Any drift must produce a blocked recommendation for human review.

Drift must not trigger:

- Automatic repair.
- File writes.
- Evidence writes.
- Receipt writes.
- Queue execution.
- Command execution.
- Approval generation.
- Self-approval.
- Branch/worktree creation.
- Git mutation.
- Protected-lane mutation.

## Drift Report Boundary

A future drift report may be planned as a human-readable summary only after explicit approval.

This document does not write a drift report. If later approved, drift reporting must remain exact-scoped, non-secret, non-mutating, and safe with unrelated dirty files present.

## Manual Checks

After Step 9.2, manually verify:

- `git diff --check` passes.
- The Step 9.2 doc exists.
- Drift categories include HEAD, dirty-tree, protected lane, approval scope, queue preview, event summary, kill switch, trust tier, blocked action class, and manual verification drift.
- Drift response rules block automatic repair, writes, evidence/receipt writes, queue execution, command execution, approval generation, self-approval, branch/worktree creation, git mutation, and protected-lane mutation.
- The doc does not write a drift report.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only soak drift review contract.

No runtime code, tests, scheduled jobs, monitors, automations, soak reports, evidence files, receipt files, command runners, queue execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-9-2-soak-drift-review-contract.md`

## Stop Conditions

Stop immediately if:

- Step 9.2 writes drift reports.
- Step 9.2 implements drift detection runtime.
- Step 9.2 triggers automatic repair.
- Step 9.2 grants command execution, queue execution, write authority, self-approval, limited unattended operation, or full auto.
- Step 9.2 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 9.3: Soak Stop Conditions And Escalation Plan
