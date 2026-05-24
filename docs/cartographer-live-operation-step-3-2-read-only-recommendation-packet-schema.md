# Cartographer Live Operation Step 3.2: Read-Only Recommendation Packet Schema

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines a conceptual read-only recommendation packet schema for future Cartographer read-only live mode.

The packet is an operator-facing planning shape only. It is not a runtime data model, not durable storage, not an event ledger, not a queue item, not evidence, not a receipt, and not an approval token.

Limited unattended operation is not granted. Full auto is not granted.

## Scope

Step 3.2 may define:

- Packet sections.
- Required packet fields.
- Forbidden packet fields.
- Recommendation rules.
- Failure and blocked-state reporting.
- Manual verification expectations.

Step 3.2 may not implement the packet in code, write packet files, persist state, create event storage, create queue storage, create approval tokens, execute commands, execute queue items, or touch `/coding` shell or UI implementation files.

## Conceptual Packet Schema

A future read-only recommendation packet may include:

| Field | Required | Meaning |
| --- | --- | --- |
| `status_date` | yes | Date the observation was summarized. |
| `head` | yes | Current HEAD captured as read-only data. |
| `branch_summary` | yes | Git branch summary captured as read-only data. |
| `dirty_tree_summary` | yes | Human-readable dirty tree summary. |
| `changed_file_list` | yes | Changed or untracked file paths observed within allowed observation scope. |
| `allowed_sources_observed` | yes | Exact allowed sources consulted. |
| `forbidden_sources_blocked` | yes | Requested sources that were blocked. |
| `protected_lane_matches` | yes | Protected path matches such as `/coding`, `source_proxy/cartographer`, or `source_proxy/tests`. |
| `trust_tier` | yes | Tier 0 or Tier 1 only. |
| `blocked_action_classes` | yes | Any action classes that must not run. |
| `recommendations` | yes | Human-facing recommendations only. |
| `operator_next_step` | yes | Suggested manual next action. |

## Forbidden Packet Fields

The packet must not include:

- Approval token material.
- Secrets.
- Environment values.
- Durable queue state.
- Event ledger state.
- Evidence write paths.
- Receipt write paths.
- Command strings for execution through Cartographer.
- Self-approval indicators.
- Auto-selected tasks.
- Branch or worktree creation instructions.
- Commit, push, merge, stash, checkout, clean, or delete instructions.

If a field would imply authority to act, it is forbidden.

## Recommendation Rules

Recommendations must stay inert.

Allowed recommendation wording may identify:

- Stale HEAD risk.
- Dirty-tree mismatch risk.
- Protected lane drift.
- Missing approval scope.
- Forbidden action class.
- Need for manual operator review.
- Need to stop before Step 4.

Recommendations must not:

- Approve the action.
- Generate an approval.
- Execute the action.
- Select the next task automatically.
- Write evidence or receipts.
- Queue work.
- Persist event data.
- Run commands through Cartographer.

## No-Write/No-Execute Boundary

Step 3.2 preserves the no-write/no-execute boundary.

This schema does not grant file writes, evidence writes, receipt writes, durable queue writes, event writes, queue execution, command execution through Cartographer, automatic task selection, approval generation, self-approval, branch/worktree creation, commit/push/merge, stash/checkout/clean/delete, `/coding` mutation, runtime mutation, or test mutation.

## Manual Checks

After Step 3.2, manually verify:

- `git diff --check` passes.
- The Step 3.2 doc exists.
- The packet schema is conceptual only.
- The doc says the packet is not durable storage, not an event ledger, not a queue item, not evidence, not a receipt, and not an approval token.
- The doc blocks approval generation, self-approval, command execution, queue execution, file writes, runtime mutation, test mutation, and `/coding` mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only conceptual packet schema.

No runtime code, tests, durable storage, approval token flow, queue execution, command execution, live autonomy, `/coding` mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-3-2-read-only-recommendation-packet-schema.md`

## Stop Conditions

Stop immediately if:

- The packet is implemented in runtime code.
- The packet is persisted as durable state.
- The packet becomes a queue item, event entry, evidence file, receipt file, or approval token.
- Any live autonomy, limited unattended operation, full auto, write authority, command authority, queue execution authority, approval authority, or self-approval appears.
- Any `/coding`, runtime, or test file is touched.

## Next Recommended Increment

Step 3.3: Blocked Action Classifier Plan
