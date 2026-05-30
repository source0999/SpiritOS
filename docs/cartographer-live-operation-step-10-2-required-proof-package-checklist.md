# Cartographer Live Operation Step 10.2: Required Proof Package Checklist

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines a planning-only checklist for a future readiness proof package.

The checklist describes what proof would be required before any later consideration of limited unattended operation. It does not create proof, write evidence, run tests, execute commands, or grant authority.

Limited unattended operation is not granted. Full auto is not granted.

## Required Proof Categories

A future proof package would need:

- Read-only observation proof.
- Recommendation packet proof.
- Blocked action classifier proof.
- Operator review packet proof.
- Inert durable queue/event storage proof.
- Approval token field proof.
- Approval validation fail-closed proof.
- Self-approval barrier proof.
- Exact write scope proof.
- Rollback and verification proof.
- Protected lane write barrier proof.
- Exact command allowlist proof.
- No shell expansion proof.
- Verification-only command proof.
- Dashboard display-only proof.
- Kill switch fail-closed proof.
- Operator control authority proof.
- Live shadow rehearsal proof.
- Drift review proof.
- Stop condition and escalation proof.

## Proof Quality Rules

Future proof must be:

- Exact-scoped.
- Human-reviewable.
- Reproducible.
- Safe with unrelated dirty files present.
- Explicit about HEAD and dirty-tree state.
- Explicit about protected lanes.
- Explicit about rollback and verification.
- Explicit that self-approval is blocked.
- Explicit that limited unattended operation is not granted until separately approved.
- Explicit that full auto is not granted.

## Missing Proof Handling

Any missing proof keeps the decision no-go.

Missing proof must not trigger runtime changes, tests, command execution, queue execution, evidence writes, receipt writes, dashboard mutation, or automatic repair.

## Manual Checks

After Step 10.2, manually verify:

- `git diff --check` passes.
- The Step 10.2 doc exists.
- Required proof categories cover Steps 3 through 9 controls.
- Proof quality rules require exact scope, human review, reproducibility, dirty-tree safety, HEAD state, protected lanes, rollback, verification, self-approval barrier, no limited unattended operation, and no full auto.
- Missing proof keeps the decision no-go.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only required proof package checklist.

No runtime code, tests, scheduled jobs, monitors, automations, evidence files, receipt files, command runners, queue execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-10-2-required-proof-package-checklist.md`

## Stop Conditions

Stop immediately if:

- Step 10.2 treats missing proof as acceptable.
- Step 10.2 writes proof evidence.
- Step 10.2 runs tests or commands.
- Step 10.2 grants limited unattended operation or full auto.
- Step 10.2 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 10.3: Operator Decision Packet Plan
