# Cartographer Live Operation Step 5.2: Approval Validation Fail-Closed Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only fail-closed validation contract for future human approval tokens.

It does not implement validation code, token stores, queue execution, command execution, write authority, or live autonomy.

Limited unattended operation is not granted. Full auto is not granted.

## Fail-Closed Conditions

Future approval validation must fail closed when:

- `operator_id` is missing.
- `approver_id` is missing.
- `token_id` is missing.
- `run_id` is missing.
- `action_type` is missing.
- `exact_allowed_files` is missing when required.
- `exact_forbidden_files` is missing.
- `expires_at` is missing.
- `rollback` is missing.
- `verification` is missing.
- `head` is missing.
- `dirty_tree_expectation` is missing.
- `kill_switch_state` is missing.
- `trust_tier` is missing.
- `human_approved_at` is missing.
- Approval is expired.
- HEAD is stale.
- Dirty tree mismatches expectation.
- Kill switch is active.
- Operator and approver are the same actor.
- Requested files exceed exact allowed files.
- Requested files match forbidden files.
- Requested action class is forbidden.
- Trust tier exceeds approved package tier.
- Authority is ambiguous.

Fail-closed means no write, no command execution, no queue execution, no approval generation, no self-approval, no branch/worktree creation, no git mutation, and no protected-lane mutation.

## Validation Output

Future validation output may be:

- `approved: false`.
- Block reason.
- Missing fields list.
- Stale state reason.
- Forbidden path reason.
- Forbidden action class reason.
- Manual operator next step.

This output is conceptual only. It is not evidence, not a receipt, not an event record, not a queue item, and not runtime validation code.

## Manual Checks

After Step 5.2, manually verify:

- `git diff --check` passes.
- The Step 5.2 doc exists.
- Fail-closed conditions include missing fields, expired approval, stale HEAD, dirty-tree mismatch, kill switch active, self-approval, forbidden paths, forbidden action classes, trust tier mismatch, and ambiguous authority.
- Fail-closed means no write, command execution, queue execution, approval generation, self-approval, git mutation, or protected-lane mutation.
- The doc does not implement validation code.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only approval validation fail-closed contract.

No runtime code, tests, token files, token storage, token validators, approval generation, queue execution, command execution, write authority, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-5-2-approval-validation-fail-closed-contract.md`

## Stop Conditions

Stop immediately if:

- Step 5.2 implements validation code.
- Step 5.2 treats failed validation as approved.
- Step 5.2 permits self-approval.
- Step 5.2 grants write authority, command execution, queue execution, limited unattended operation, or full auto.
- Step 5.2 touches `/coding`, runtime, test, package, or config files.

## Next Recommended Increment

Step 5.3: Self-Approval Barrier Plan
