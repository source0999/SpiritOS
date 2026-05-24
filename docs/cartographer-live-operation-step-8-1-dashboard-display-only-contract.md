# Cartographer Live Operation Step 8.1: Dashboard Display-Only Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only display-only contract for future operator dashboard controls.

Display-only means dashboard state may inform a human operator but cannot execute, approve, write, command, queue, or mutate state by itself.

Limited unattended operation is not granted. Full auto is not granted.

## Display-Only Rules

Future dashboard display must obey:

- Status display is not approval.
- Recommendation display is not task selection.
- Queue preview display is not queue execution.
- Event display is not evidence or receipt writing.
- Kill switch status display is not kill switch mutation.
- Approval requirement display is not approval generation.
- Blocked-action display is not command execution.
- Control presence is not authority.

## Allowed Display Concepts

Future display concepts may include:

- Current HEAD.
- Dirty-tree summary.
- Protected lane warnings.
- Approval requirements.
- Queue preview summaries.
- Event summaries.
- Blocked action reasons.
- Kill switch status.
- Manual next-step recommendations.

These are concepts only and must not be implemented in this session.

## Forbidden Display-Driven Actions

Future display must not trigger:

- Queue execution.
- Command execution.
- File writes.
- Evidence writes.
- Receipt writes.
- Approval generation.
- Self-approval.
- Branch/worktree creation.
- Commit/push/merge.
- Stash/checkout/clean/delete.
- `/coding` mutation.
- Runtime/test mutation.
- Package/config mutation.

## Manual Checks

After Step 8.1, manually verify:

- `git diff --check` passes.
- The Step 8.1 doc exists.
- Display-only rules say dashboard display is not approval, task selection, queue execution, evidence/receipt writing, kill switch mutation, approval generation, command execution, or authority.
- Forbidden display-driven actions include queue execution, command execution, writes, approval generation, self-approval, git mutation, `/coding` mutation, runtime/test mutation, and package/config mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only dashboard display-only contract.

No UI, dashboard component, runtime code, tests, command runners, queue execution, write files, approval generation, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-8-1-dashboard-display-only-contract.md`

## Stop Conditions

Stop immediately if:

- Step 8.1 implements dashboard UI.
- Step 8.1 treats display state as authority.
- Step 8.1 grants approval, command execution, queue execution, write authority, limited unattended operation, or full auto.
- Step 8.1 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 8.2: Kill Switch Control Boundary
