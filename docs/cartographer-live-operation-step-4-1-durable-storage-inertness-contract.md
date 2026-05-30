# Cartographer Live Operation Step 4.1: Durable Storage Inertness Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the Step 4.1 inertness contract for future durable queue and event storage.

Inert storage means stored records may be reviewed by a human operator but cannot execute, approve, write, command, select tasks, or mutate repo state.

Limited unattended operation is not granted. Full auto is not granted.

## Inertness Rules

Future durable storage must obey these rules:

- A stored queue preview is not an executable queue item.
- A stored event is not approval.
- A stored recommendation is not authority.
- A stored blocked-action finding is not a command.
- A stored operator review snapshot is not evidence or a receipt.
- Storage presence does not bypass HEAD checks.
- Storage presence does not bypass dirty-tree checks.
- Storage presence does not bypass forbidden-path checks.
- Storage presence does not bypass trust-tier checks.
- Storage presence does not bypass human approval token requirements.

## Allowed Future Record Classes

Future Step 4 implementation may later define inert record classes for:

- Queue preview records.
- Observation event records.
- Recommendation event records.
- Blocked action event records.
- Operator review snapshot records.

This document does not create those records, persist those records, define runtime models, or write tests.

## Forbidden Record Classes

Future Step 4 storage must not create:

- Approval tokens.
- Evidence records.
- Receipt records.
- Executable command records.
- Auto-selected task records.
- Branch/worktree instruction records.
- Commit/push/merge instruction records.
- Stash/checkout/clean/delete instruction records.

If a record can directly cause mutation or execution, it is outside Step 4.

## Fail-Closed Requirements

Future storage consumers must fail closed when:

- Approval is missing.
- Approval is expired.
- Approval scope is ambiguous.
- HEAD is stale.
- Dirty-tree state mismatches expectation.
- A protected path is present.
- A forbidden action class is present.
- A trust tier above Tier 2 is requested.
- Self-approval is attempted.
- The kill switch is active.

Fail-closed means no execution, no write, no approval, and no queue advancement.

## Manual Checks

After Step 4.1, manually verify:

- `git diff --check` passes.
- The Step 4.1 doc exists.
- The inertness rules say storage does not execute, approve, write, command, select tasks, or mutate repo state.
- The doc says storage does not bypass HEAD, dirty-tree, forbidden-path, trust-tier, or approval-token requirements.
- The doc does not implement storage.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only durable storage inertness contract.

No runtime code, tests, durable storage files, queue items, event records, approval token flow, queue execution, command execution, live autonomy, `/coding` mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-4-1-durable-storage-inertness-contract.md`

## Stop Conditions

Stop immediately if:

- Step 4.1 implements storage.
- Step 4.1 treats stored records as executable or approved.
- Step 4.1 grants write authority, command authority, queue execution authority, approval authority, limited unattended operation, or full auto.
- Step 4.1 touches `/coding`, runtime, or test files.

## Next Recommended Increment

Step 4.2: Event Record Schema Plan
