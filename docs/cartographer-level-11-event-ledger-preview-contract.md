# Cartographer Level 11.3 Event Ledger Preview Contract

status: ledger-preview-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 11.3 defines the future event ledger contract for Controlled Action Authority.

This increment is docs-only. It does not implement an event ledger, token creation, token validation, API routes, service builders, tests, runtime writes, command execution, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 11.1 created the Controlled Action Authority boundary contract.

Level 11.2 created the Approval Token Schema Preview.

Level 11.3 narrows the next design artifact to the future append-only event ledger. It does not advance to receipt writes, evidence writes, docs-only apply actions, local verification execution, rollback execution, or closeout authority.

## Scope

Allowed in this increment:

- create this event ledger preview contract document.
- define future ledger principles.
- define future required event names.
- define future event envelope fields.
- define future ordering, source-of-truth, and fail-closed rules.
- define future test expectations.
- run doc-only verification commands.

Not allowed in this increment:

- source code edits.
- API route edits.
- service builder edits.
- tests.
- package changes.
- dependency installs.
- runtime behavior changes.
- UI work.
- Source Proxy stress testing mutation.
- `/coding` UI mutation.
- event ledger implementation.
- token creation at runtime.
- token validation at runtime.
- action execution.
- receipt or evidence writing.
- run history mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- branch, worktree, checkout, stash, cleanup, commit, push, or merge operations.

## Non-Authority Statement

This ledger preview is not authority.

The event ledger described here is a future audit and control requirement. It does not create a ledger, grant permission, approve an action, write a receipt, write evidence, execute commands, mutate files, or close out runs.

Future implementation must prove that no action counts as complete without an event trail and that event presence never bypasses approval, file scope, rollback, verification, or lane isolation.

## Event Ledger Definition

The future event ledger is an append-only record of Controlled Action Authority state transitions.

It must record approval requests, approvals, rejections, token creation, token revocation, write requests, blocked writes, completed writes, command requests, blocked commands, completed commands, verification, rollback availability, rollback requests, rollback completion, and action closeout.

The ledger is the source of truth for future authority state. The UI may render ledger state, but the UI is not the source of truth.

## Required Event Names

Future ledger implementations must support at least:

- action_packet_created.
- approval_requested.
- approval_granted.
- approval_rejected.
- approval_token_created.
- approval_token_revoked.
- file_write_requested.
- file_write_blocked.
- file_write_completed.
- command_requested.
- command_blocked.
- command_completed.
- verification_started.
- verification_passed.
- verification_failed.
- rollback_available.
- rollback_requested.
- rollback_completed.
- action_closed_out.

Future implementation may add narrower event names, but it must not remove or weaken these required events.

## Event Envelope Preview

Future ledger events must include:

- event_id: stable unique event identifier.
- event_type: one of the supported event names.
- run_id: stable run identifier.
- action_id: stable action packet identifier when applicable.
- token_id: approval token identifier when applicable.
- sequence: monotonic sequence within the run.
- created_at: timestamp when the event was recorded.
- actor_type: operator, system, or tool.
- actor_id: identifier for the actor.
- status: observed, requested, granted, rejected, blocked, started, completed, passed, failed, revoked, or closed_out.
- target_files: files involved in the event when applicable.
- allowed_files: approved file scope when applicable.
- forbidden_files: blocked file scope when applicable.
- command: command involved in the event when applicable.
- head_before: HEAD observed before the action when applicable.
- head_after: HEAD observed after the action when applicable.
- git_status_before: git status snapshot or reference before the action when applicable.
- git_status_after: git status snapshot or reference after the action when applicable.
- rollback_reference: rollback command, rollback note, or rollback artifact reference when applicable.
- verification_reference: verification command or verification result reference when applicable.
- reason: human-readable explanation for blocked, rejected, failed, or revoked events.

Future implementation may add display fields, but it must not rely on display fields as authority.

## Append-Only Rules

No event may be silently rewritten.

No event may be deleted to hide a failed action, blocked action, rejected approval, revoked token, failed verification, or rollback.

Corrections must be represented as new events that point back to the original event.

Ledger ordering must be stable within a run. If ordering cannot be proven, future action authority must fail closed.

## Completion Rules

No future action counts as complete without an event trail.

At minimum, a completed future action must have:

- action_packet_created.
- approval_requested.
- approval_granted.
- approval_token_created.
- file_write_requested or command_requested.
- file_write_completed or command_completed.
- verification_started.
- verification_passed.
- rollback_available when rollback applies.
- action_closed_out.

Blocked actions must also be recorded. A blocked action is successful safety behavior, not an invisible non-event.

## Approval Token Relationship

Future approval tokens must be ledger-visible.

The ledger must record approval_requested, approval_granted or approval_rejected, approval_token_created, approval_token_revoked when applicable, and any token-scoped blocked or completed action.

A token without a matching ledger trail is invalid for future live authority. A ledger event without a valid token must not authorize writes or execution.

## Receipt And Evidence Relationship

Level 11.3 does not write receipts or evidence.

Future receipt and evidence writes must emit ledger events before and after the write. A future receipt or evidence file must be traceable to the run, action packet, approval token, target files, verification result, and rollback reference.

Deletion of evidence, receipts, or run history remains forbidden.

## Fail-Closed Rules

Future authority must fail closed when:

- event ledger storage is unavailable.
- event ordering cannot be proven.
- event write fails.
- required approval events are missing.
- required token events are missing.
- required file write or command events are missing.
- required verification events are missing.
- required rollback events are missing.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- approval scope and action scope do not match.
- target files and allowed files do not match.
- forbidden files are touched.
- protected paths are touched.
- Source Proxy stress files are touched.
- `/coding` UI files are touched without a future separate lane.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Ledger Uses

The future ledger must never be used to authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- branch creation.
- worktree creation.
- checkout.
- stash.
- cleanup.
- commit.
- push.
- merge.
- protected path writes.
- secret path reads or writes.
- cross-lane mutation.
- Source Proxy stress testing mutation.
- `/coding` UI mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- background mutation.
- hidden retries.
- autonomous task selection.
- automatic promotion.
- force overwrite.
- deletion of evidence.
- deletion of receipts.
- deletion of run history.
- deletion of branches or worktrees.

## Dirty Worktree And Lane Isolation Rules

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit approval.

Future ledger events may record dirty-state observations, but observation does not authorize mutation.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 11.4: Approved Receipt Write Dry Run
- Level 11.5: Approved Evidence Write Dry Run
- Level 11.6: Approved Docs-Only Apply Boundary
- Level 11.7: Controlled Local Verification Execution Boundary
- Level 11.8: Rollback And Closeout Receipt Boundary
- Level 11.9: Level 11 Closeout And Level 12 Gate

Do not implement any of these in Level 11.3.

## Required Future Tests

Future source-code increments must prove:

- no action completes without an event trail.
- event ledger records every future approval step.
- event ledger records every future token step.
- event ledger records every future file write request.
- event ledger records blocked file writes.
- event ledger records completed file writes.
- event ledger records every future command request.
- event ledger records blocked commands.
- event ledger records completed commands.
- event ledger records verification started.
- event ledger records verification passed.
- event ledger records verification failed.
- event ledger records rollback availability before live action.
- event ledger records rollback requested and rollback completed when rollback is used.
- events are append-only.
- corrections create new events rather than rewriting old events.
- action is blocked when ledger storage is unavailable.
- action is blocked when required events are missing.
- action is blocked when HEAD changed unexpectedly.
- action is blocked when git status changed unexpectedly.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- no branch/worktree authority exists.
- no checkout/stash/cleanup authority exists.
- no commit/push/merge authority exists.
- no self-approval exists.
- no hidden background mutation exists.
- failures are honest and explainable.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-11-event-ledger-preview-contract.md

grep -n "Event Ledger Preview Contract\|Required Event Names\|Event Envelope Preview\|Append-Only Rules\|Level 11.4: Approved Receipt Write Dry Run" docs/cartographer-level-11-event-ledger-preview-contract.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-11-event-ledger-preview-contract.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 11.3 creates the Event Ledger Preview Contract only.

Expected result:

- no event ledger implementation enabled.
- no token creation enabled.
- no token validation enabled.
- no write authority enabled.
- no local execution authority enabled.
- no branch/worktree authority enabled.
- no commit/push/merge authority enabled.
- no automatic execution enabled.
- no automatic promotion enabled.
- no self-approval enabled.
- no cleanup occurred.
- no Source Proxy stress files touched.
- no `/coding` UI files touched.
- no source code, API routes, tests, package files, or runtime files touched.

## Next Increment

Level 11.4: Approved Receipt Write Dry Run
