# Cartographer Live Operation Step 4.3: Queue Preview Record Schema Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines a conceptual queue preview record schema for future durable queue storage.

The queue preview record is not executable. It is not an approval, not a command, not evidence, not a receipt, and not a task auto-selection mechanism.

Limited unattended operation is not granted. Full auto is not granted.

## Conceptual Queue Preview Fields

Future inert queue preview records may include:

| Field | Required | Meaning |
| --- | --- | --- |
| `preview_id` | yes | Stable identifier for the inert preview. |
| `status_date` | yes | Date the preview was formed. |
| `head` | yes | HEAD observed at preview formation. |
| `dirty_tree_summary` | yes | Dirty tree summary captured as data only. |
| `requested_action_class` | yes | Requested class, never executed by Step 4. |
| `allowed_file_scope` | yes | Exact future allowed scope, if any. |
| `forbidden_file_scope` | yes | Exact forbidden scope. |
| `blocked_action_classes` | yes | Classes that block the preview. |
| `approval_required` | yes | Always true for any later action. |
| `operator_review_required` | yes | Always true. |

## Queue Preview Rules

Future queue preview records must obey:

- Preview does not execute.
- Preview does not approve.
- Preview does not write.
- Preview does not run commands.
- Preview does not select tasks automatically.
- Preview does not bypass approval token requirements.
- Preview does not bypass protected-lane rules.
- Preview does not bypass HEAD or dirty-tree checks.

## Forbidden Queue Preview Fields

Queue preview records must not contain:

- Executable command payloads.
- Queue execution flags.
- Approval token material.
- Self-approval indicators.
- Evidence write payloads.
- Receipt write payloads.
- Branch/worktree creation instructions.
- Commit/push/merge instructions.
- Stash/checkout/clean/delete instructions.
- `/coding` mutation instructions.

## Manual Checks

After Step 4.3, manually verify:

- `git diff --check` passes.
- The Step 4.3 doc exists.
- The queue preview schema is conceptual only.
- The doc says queue preview records do not execute, approve, write, run commands, select tasks automatically, or bypass approvals.
- Forbidden queue preview fields block command payloads, execution flags, token material, self-approval, evidence/receipt writes, git mutation, and `/coding` mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only queue preview record schema plan.

No runtime code, tests, durable queue files, queue items, event records, queue execution, command execution, approval token flow, live autonomy, `/coding` mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-4-3-queue-preview-record-schema-plan.md`

## Stop Conditions

Stop immediately if:

- Step 4.3 implements queue storage.
- Step 4.3 writes queue items.
- Step 4.3 makes queue previews executable or approved.
- Step 4.3 touches `/coding`, runtime, or test files.
- Step 4.3 grants limited unattended operation or full auto.

## Next Recommended Increment

Step 4.4: Durable Queue/Event Storage Closeout And Step 5 Gate
