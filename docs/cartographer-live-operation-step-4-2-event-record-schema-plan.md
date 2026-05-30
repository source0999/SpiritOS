# Cartographer Live Operation Step 4.2: Event Record Schema Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines a conceptual event record schema for future durable event storage.

The schema is planning-only. It is not a runtime model, not persisted state, not evidence, not a receipt, not an approval token, and not a command or queue executor.

Limited unattended operation is not granted. Full auto is not granted.

## Conceptual Event Fields

Future inert event records may include:

| Field | Required | Meaning |
| --- | --- | --- |
| `event_id` | yes | Stable identifier for the inert event record. |
| `event_type` | yes | Observation, recommendation, blocked action, or operator review snapshot. |
| `status_date` | yes | Date the event was formed. |
| `head` | yes | HEAD observed at event formation. |
| `dirty_tree_summary` | yes | Dirty tree summary captured as data only. |
| `source_scope` | yes | Allowed observation sources used. |
| `protected_lane_matches` | yes | Protected path matches, if any. |
| `blocked_action_classes` | yes | Forbidden action classes detected, if any. |
| `trust_tier` | yes | Tier 0, Tier 1, or future Tier 2 preview only. |
| `operator_review_required` | yes | Always true for Step 4 planning. |

## Forbidden Event Fields

Future event records must not contain:

- Secrets.
- Environment values.
- Approval token secrets.
- Executable command payloads.
- Queue execution flags.
- Evidence write payloads.
- Receipt write payloads.
- Auto-selected tasks.
- Branch/worktree instructions.
- Commit/push/merge instructions.
- Stash/checkout/clean/delete instructions.

## Event Type Boundaries

Allowed conceptual event types:

- `observation_recorded`.
- `recommendation_recorded`.
- `blocked_action_recorded`.
- `operator_review_snapshot_recorded`.

Forbidden event types:

- `queue_item_executed`.
- `command_executed`.
- `approval_generated`.
- `self_approved`.
- `evidence_written`.
- `receipt_written`.
- `branch_created`.
- `worktree_created`.
- `committed`.
- `pushed`.
- `merged`.

## Manual Checks

After Step 4.2, manually verify:

- `git diff --check` passes.
- The Step 4.2 doc exists.
- The event schema is conceptual only.
- The doc says event records are not evidence, not receipts, not approvals, not commands, and not queue executors.
- Forbidden event fields block secrets, command payloads, queue execution flags, approval token secrets, evidence writes, receipt writes, and git mutation instructions.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only event record schema plan.

No runtime code, tests, durable storage files, event records, queue execution, command execution, approval token flow, live autonomy, `/coding` mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-4-2-event-record-schema-plan.md`

## Stop Conditions

Stop immediately if:

- Step 4.2 implements event storage.
- Step 4.2 writes event records.
- Step 4.2 treats events as evidence, receipts, approvals, commands, or queue execution.
- Step 4.2 touches `/coding`, runtime, or test files.
- Step 4.2 grants limited unattended operation or full auto.

## Next Recommended Increment

Step 4.3: Queue Preview Record Schema Plan
