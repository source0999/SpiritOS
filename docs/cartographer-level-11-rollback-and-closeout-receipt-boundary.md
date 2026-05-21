# Cartographer Level 11.8 Rollback And Closeout Receipt Boundary

status: rollback-closeout-receipt-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 11.8 defines the future boundary for rollback metadata and closeout receipt handling in Controlled Action Authority.

This increment is docs-only. It does not execute rollback commands, write closeout receipts, write receipts, write evidence, apply documentation changes, execute verification commands, create approval tokens, validate approval tokens, implement an event ledger, add API routes, add service builders, add tests, change runtime behavior, create branches, create worktrees, commit, push, merge, clean up, or mutate files outside this document.

Cartographer remains in observe, recommend, preview, and dry-run posture. No rollback execution authority, closeout receipt write authority, local execution authority, write authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 11.1 created the Controlled Action Authority boundary contract.

Level 11.2 created the Approval Token Schema Preview.

Level 11.3 created the Event Ledger Preview Contract.

Level 11.4 created the Approved Receipt Write Dry Run contract.

Level 11.5 created the Approved Evidence Write Dry Run contract.

Level 11.6 created the Approved Docs-Only Apply Boundary.

Level 11.7 created the Controlled Local Verification Execution Boundary.

Level 11.8 narrows the next design artifact to rollback metadata and closeout receipt handling. It does not grant live rollback execution or closeout receipt writing authority.

## Scope

Allowed in this increment:

- create this rollback and closeout receipt boundary document.
- define future rollback metadata requirements.
- define future closeout receipt packet shape.
- define future approval, token, ledger, verification, and output requirements.
- define future blocked cases.
- define future tests.
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
- rollback command execution.
- closeout receipt writing.
- receipt writing.
- evidence writing.
- docs-only apply implementation.
- live documentation apply actions.
- local verification command execution.
- event ledger implementation.
- approval token implementation.
- action execution.
- run history mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- branch, worktree, checkout, stash, cleanup, commit, push, or merge operations.

## Non-Authority Statement

This boundary is not rollback execution authority and not closeout receipt write authority.

A future rollback command or closeout receipt write may occur only after a focused implementation increment, explicit approval token, exact command or file scope, event ledger trail, verification requirements, rollback metadata, and focused tests.

Level 11.8 does not create that implementation, does not run rollback commands, and does not write closeout receipts.

## Rollback Metadata Definition

Future rollback metadata describes how to reverse or supersede one approved action without mutating unrelated work.

Rollback metadata must be:

- single-action.
- approval-bound before execution.
- file-scope-bound.
- command-scope-bound when a command is involved.
- run-bound.
- time-limited.
- verification-required.
- event-ledger-recorded.
- fail-closed by default.

Rollback metadata is required before future live write or execution authority. Missing rollback metadata must block the action.

## Closeout Receipt Definition

A future closeout receipt is a single approved record that summarizes an approved action after verification and rollback availability are established.

It must capture:

- run id.
- action packet id.
- action type.
- approval token id.
- target files.
- allowed files.
- forbidden files.
- HEAD before and after when applicable.
- git status before and after when applicable.
- ledger event references.
- verification result.
- rollback reference.
- blocked or completed result.
- operator id.
- closeout timestamp.

Level 11.8 does not write closeout receipts.

## Rollback Packet Preview

Future rollback packets must include:

- packet_id: stable rollback packet identifier.
- run_id: stable run identifier.
- action_type: approved_rollback_execution.
- mode: dry_run or approved_execution.
- rollback_command: exact command or documented manual rollback step.
- rollback_target_files: exact files rollback may affect.
- original_action_id: action packet being rolled back.
- original_approval_token_id: approval token for the original action.
- approval_token_id: token expected before rollback execution.
- allowed_files: exact future allowed file scope.
- forbidden_files: exact blocked file scope.
- ledger_event_plan: ordered events expected before and after rollback.
- verification_command: command expected to verify rollback.
- timeout_seconds: maximum runtime when command execution is involved.
- max_attempts: maximum attempts.
- head_expected: HEAD value expected before rollback.
- git_status_expected: git status expectation before rollback.
- blocked: boolean result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Closeout Receipt Packet Preview

Future closeout receipt packets must include:

- packet_id: stable closeout packet identifier.
- run_id: stable run identifier.
- action_type: approved_closeout_receipt_write.
- mode: dry_run or approved_write.
- closeout_receipt_file: exact future closeout receipt path.
- action_summary: concise summary of the approved action.
- verification_summary: concise summary of verification result.
- rollback_summary: concise summary of rollback availability.
- allowed_files: exact future allowed file scope.
- forbidden_files: exact blocked file scope.
- approval_token_id: token expected before live closeout write.
- ledger_event_plan: ordered events expected before and after closeout.
- verification_command: command expected to verify the closeout receipt.
- head_expected: HEAD value expected before live closeout.
- git_status_expected: git status expectation before live closeout.
- blocked: boolean result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Approval Requirements

Future rollback execution requires an explicit approval token scoped to:

- one run.
- one action type: approved_rollback_execution.
- one exact rollback command or manual rollback step.
- exact rollback target files.
- exact allowed files.
- exact forbidden files.
- expiration.
- maximum attempts.
- timeout when command execution is involved.
- verification command.
- external operator id.

Future closeout receipt writing requires an explicit approval token scoped to:

- one run.
- one action type: approved_closeout_receipt_write.
- one exact closeout receipt file.
- exact allowed files.
- exact forbidden files.
- expiration.
- maximum attempts.
- verification command.
- external operator id.

Approval for a preview or dry run is not approval for live rollback execution or closeout receipt writing.

## Event Ledger Requirements

Future rollback execution must emit ledger events before and after rollback.

Expected future rollback event trail:

- action_packet_created.
- approval_requested.
- approval_granted.
- approval_token_created.
- rollback_available.
- rollback_requested.
- command_requested.
- command_completed.
- rollback_completed.
- verification_started.
- verification_passed or verification_failed.
- action_closed_out.

Future closeout receipt writing must emit ledger events before and after the write.

Expected future closeout event trail:

- action_packet_created.
- approval_requested.
- approval_granted.
- approval_token_created.
- file_write_requested.
- file_write_completed.
- verification_started.
- verification_passed.
- action_closed_out.

Blocked attempts must emit rollback_requested with command_blocked, file_write_blocked, or command_blocked where applicable and must explain the blocked reason.

Level 11.8 does not implement ledger storage or emit runtime ledger events.

## Verification Requirements

Future rollback execution must define verification before action.

Future rollback verification must prove:

- rollback affected only approved target files.
- rollback did not touch forbidden files.
- rollback did not touch protected paths.
- rollback did not touch Source Proxy stress files.
- rollback did not touch `/coding` UI files.
- rollback did not delete evidence, receipts, or run history.
- HEAD and git status expectations were respected or explicitly explained.
- event ledger contains the required rollback event trail.

Future closeout receipt verification must prove:

- expected closeout receipt file exists.
- closeout receipt path is inside allowed files.
- closeout receipt path is outside forbidden files.
- closeout receipt content matches the approved closeout packet.
- verification result is recorded.
- rollback reference is recorded.
- event ledger contains the required closeout event trail.

Level 11.8 does not run verification commands except doc-only manual checks.

## Fail-Closed Rules

Future rollback and closeout handling must block when:

- approval token is missing.
- approval token is expired or revoked.
- action type does not match the approved rollback or closeout action.
- rollback metadata is missing.
- rollback command differs from approval.
- rollback target files are outside allowed files.
- closeout receipt file is outside allowed files.
- any target file intersects forbidden files.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- evidence, receipts, or run history would be deleted.
- source code, API routes, service builders, tests, package files, or runtime files are in scope without a future separate boundary.
- HEAD expectation is missing or changed unexpectedly.
- git status expectation is missing or changed unexpectedly.
- verification command is missing.
- expected ledger events are missing.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Actions

The future rollback and closeout receipt boundary must never authorize:

- automatic rollback execution.
- rollback execution without approval.
- closeout receipt writing without approval.
- deletion of evidence.
- deletion of receipts.
- deletion of run history.
- automatic execution without approval.
- global approval.
- self-approval.
- source code edits.
- API route edits.
- service builder edits.
- tests.
- package changes.
- runtime behavior changes.
- UI mutation.
- Source Proxy stress testing mutation.
- docs-only apply actions.
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
- Scout writes.
- proxy memory writes.
- blueprint writes.
- background mutation.
- hidden retries.
- autonomous task selection.
- automatic promotion.
- force overwrite.
- deletion of branches or worktrees.

## Dirty Worktree And Lane Isolation Rules

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit approval.

Future rollback execution and closeout receipt writing must treat unexpected HEAD or git status changes as blocking conditions for live authority.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 11.9: Level 11 Closeout And Level 12 Gate

Do not implement Level 11.9 in Level 11.8.

## Required Future Tests

Future source-code increments must prove:

- rollback execution is blocked without approval.
- rollback execution is blocked with expired approval.
- rollback execution is blocked with revoked approval.
- rollback execution is blocked when action_type is not approved_rollback_execution.
- rollback execution is blocked when rollback command differs from approval.
- rollback execution is blocked when rollback target files are outside allowed_files.
- rollback execution is blocked when forbidden_files match.
- closeout receipt writing is blocked without approval.
- closeout receipt writing is blocked when action_type is not approved_closeout_receipt_write.
- closeout receipt writing is blocked when closeout receipt file is outside allowed_files.
- closeout receipt writing is blocked when forbidden_files match.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- deletion of evidence remains blocked.
- deletion of receipts remains blocked.
- deletion of run history remains blocked.
- source code, API routes, service builders, tests, package files, and runtime files remain blocked unless a future separate boundary allows inspection.
- rollback or closeout is blocked when HEAD changed unexpectedly.
- rollback or closeout is blocked when git status changed unexpectedly.
- event ledger records rollback_requested, rollback_completed, file_write_requested, file_write_completed, verification_started, and verification_passed or verification_failed in future implementation.
- no docs-only apply authority exists.
- no general local execution authority exists.
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

git diff --check -- docs/cartographer-level-11-rollback-and-closeout-receipt-boundary.md

grep -n "Rollback And Closeout Receipt Boundary\|Rollback Packet Preview\|Closeout Receipt Packet Preview\|Verification Requirements\|Level 11.9: Level 11 Closeout And Level 12 Gate" docs/cartographer-level-11-rollback-and-closeout-receipt-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-11-rollback-and-closeout-receipt-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 11.8 creates the Rollback And Closeout Receipt Boundary only.

Expected result:

- no rollback execution authority enabled.
- no closeout receipt write authority enabled.
- no local verification execution authority enabled.
- no docs-only apply authority enabled.
- no receipt writing enabled.
- no evidence writing enabled.
- no event ledger implementation enabled.
- no token creation enabled.
- no token validation enabled.
- no write authority enabled.
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

Level 11.9: Level 11 Closeout And Level 12 Gate
