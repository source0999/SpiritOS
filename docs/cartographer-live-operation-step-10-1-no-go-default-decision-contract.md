# Cartographer Live Operation Step 10.1: No-Go Default Decision Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the Step 10.1 no-go default decision contract.

No-go default means absence of exact proof, exact approval, or exact operator grant blocks progression. It does not implement any runtime decision gate.

Limited unattended operation is not granted. Full auto is not granted.

## No-Go Rules

The decision must remain no-go when:

- Any required proof is missing.
- Any required approval is missing.
- Any approval is stale, expired, ambiguous, or self-approved.
- HEAD does not match expectation.
- Dirty tree state does not match expectation.
- Kill switch is active, missing, or ambiguous.
- Protected lane drift is present.
- Queue execution is requested.
- Command execution is requested without exact approval.
- Write authority is requested without exact approval.
- Dashboard controls imply authority.
- Operator signoff is missing.

## No-Go Output

A no-go output may say:

- Readiness not granted.
- Limited unattended operation is not granted.
- Full auto is not granted.
- Missing proof list.
- Blocked action list.
- Manual operator next step.

No-go output must not write evidence, receipts, queue items, event records, approvals, dashboard state, runtime state, or files through Cartographer.

## Manual Checks

After Step 10.1, manually verify:

- `git diff --check` passes.
- The Step 10.1 doc exists.
- No-go rules block missing proof, missing approval, stale/expired/ambiguous/self-approved approval, stale HEAD, dirty-tree mismatch, kill switch problems, protected lane drift, queue execution, command execution without exact approval, write authority without exact approval, dashboard authority, and missing operator signoff.
- No-go output does not write evidence, receipts, queue items, event records, approvals, dashboard state, runtime state, or files through Cartographer.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only no-go default decision contract.

No runtime code, tests, scheduled jobs, monitors, automations, evidence files, receipt files, command runners, queue execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-10-1-no-go-default-decision-contract.md`

## Stop Conditions

Stop immediately if:

- Step 10.1 grants readiness by default.
- Step 10.1 treats missing proof or missing approval as acceptable.
- Step 10.1 grants limited unattended operation or full auto.
- Step 10.1 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 10.2: Required Proof Package Checklist
