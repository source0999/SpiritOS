# Cartographer Live Operation Step 5.1: Approval Token Field Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only field contract for future human approval tokens.

The field contract is not a schema implementation, not token storage, not validation code, not approval generation, and not runtime authority.

Limited unattended operation is not granted. Full auto is not granted.

## Required Fields

Future approval tokens must include:

| Field | Required | Meaning |
| --- | --- | --- |
| `operator_id` | yes | Human operator requesting or supervising the action. |
| `approver_id` | yes | Human approver granting exact-scope approval. |
| `token_id` | yes | Unique token identifier. |
| `run_id` | yes | Exact run or review identifier. |
| `action_type` | yes | Exact approved action class. |
| `exact_allowed_files` | yes | Exact file paths allowed for the action. |
| `exact_forbidden_files` | yes | Exact forbidden file paths and protected lanes. |
| `expires_at` | yes | Expiry timestamp. |
| `rollback` | yes | Manual rollback instructions. |
| `verification` | yes | Manual or future exact verification instructions. |
| `head` | yes | Current HEAD expected by the approval. |
| `dirty_tree_expectation` | yes | Expected dirty tree state. |
| `kill_switch_state` | yes | Expected kill switch state. |
| `trust_tier` | yes | Approved trust tier. |
| `human_approved_at` | yes | Human approval timestamp. |

## Field Rules

Field rules:

- `operator_id` and `approver_id` must not be the same actor.
- `action_type` must be exact and must not imply broad authority.
- `exact_allowed_files` must not be empty for write-capable future actions.
- `exact_forbidden_files` must include protected lanes.
- `expires_at` must be checked before any future action.
- `rollback` must be concrete enough for manual review.
- `verification` must be concrete and scoped.
- `head` must match current HEAD before any future action.
- `dirty_tree_expectation` must match current dirty tree before any future action.
- `kill_switch_state` must be clear before any future action.
- `trust_tier` must not exceed the approved package tier.

## Forbidden Fields

Future approval tokens must not include:

- Secrets.
- Environment values.
- Broad shell command strings.
- Auto-selected task instructions.
- Self-approval flags.
- Full auto flags.
- Limited unattended operation flags unless a later explicit package separately proves that authority.
- Wildcard file scopes.
- Ambiguous rollback instructions.
- Ambiguous verification instructions.

## Manual Checks

After Step 5.1, manually verify:

- `git diff --check` passes.
- The Step 5.1 doc exists.
- Required fields include operator id, approver id, token id, run id, action type, exact allowed files, exact forbidden files, expiry, rollback, verification, HEAD, dirty-tree expectation, kill switch state, trust tier, and human approval timestamp.
- Field rules block self-approval.
- Forbidden fields block secrets, broad command strings, auto-selected task instructions, full auto flags, limited unattended operation flags, wildcard scopes, and ambiguous rollback/verification.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only approval token field contract.

No runtime code, tests, token files, token storage, token validators, approval generation, queue execution, command execution, write authority, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-5-1-approval-token-field-contract.md`

## Stop Conditions

Stop immediately if:

- Step 5.1 implements a token schema in runtime code.
- Step 5.1 stores token data.
- Step 5.1 permits self-approval, wildcard scope, broad command authority, limited unattended operation, or full auto.
- Step 5.1 touches `/coding`, runtime, test, package, or config files.

## Next Recommended Increment

Step 5.2: Approval Validation Fail-Closed Contract
