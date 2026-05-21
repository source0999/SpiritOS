# Cartographer Level 11.6 Approved Docs-Only Apply Boundary

status: docs-only-apply-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 11.6 defines the future boundary for approved docs-only apply actions.

This increment is docs-only. It does not apply documentation changes, create approval tokens, validate approval tokens, implement an event ledger, add API routes, add service builders, add tests, change runtime behavior, execute commands, write receipts, write evidence, create branches, create worktrees, commit, push, merge, clean up, or mutate files outside this document.

Cartographer remains in observe, recommend, preview, and dry-run posture. No write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 11.1 created the Controlled Action Authority boundary contract.

Level 11.2 created the Approval Token Schema Preview.

Level 11.3 created the Event Ledger Preview Contract.

Level 11.4 created the Approved Receipt Write Dry Run contract.

Level 11.5 created the Approved Evidence Write Dry Run contract.

Level 11.6 narrows the next design artifact to a future docs-only apply boundary. It does not grant live docs apply authority.

## Scope

Allowed in this increment:

- create this approved docs-only apply boundary document.
- define future docs-only target rules.
- define future apply packet shape.
- define future approval, token, ledger, rollback, and verification requirements.
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
- docs-only apply implementation.
- live documentation apply actions.
- receipt writing.
- evidence writing.
- event ledger implementation.
- approval token implementation.
- action execution.
- run history mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- branch, worktree, checkout, stash, cleanup, commit, push, or merge operations.

## Non-Authority Statement

This boundary is not docs apply authority.

A future approved docs-only apply action may modify exact approved documentation files only after a focused implementation increment, explicit approval token, exact file scope, event ledger trail, rollback metadata, verification command, and focused tests.

Level 11.6 does not create that implementation and does not perform any docs-only apply action.

## Docs-Only Apply Definition

A future docs-only apply action is a single approved file mutation limited to documentation files.

It must be:

- single-action.
- approval-bound.
- docs-file-scope-bound.
- run-bound.
- time-limited.
- rollback-required.
- verification-required.
- event-ledger-recorded.
- fail-closed by default.

Docs-only does not mean all docs are allowed. It means only the exact documentation files listed in the valid future approval token may be touched.

## Docs Target Rules

Future docs-only apply actions must identify:

- target documentation files.
- action type.
- run id.
- action packet id.
- approval token id.
- allowed files.
- forbidden files.
- protected path check result.
- lane isolation check result.
- HEAD expectation.
- git status expectation.
- rollback command or rollback note.
- verification command.
- expected ledger events.
- blocked reason when blocked.

The action must block if any target file is outside allowed files, intersects forbidden files, is not a documentation file, or belongs to a separately isolated lane.

## Apply Packet Preview

Future docs-only apply packets must include:

- packet_id: stable action packet identifier.
- run_id: stable run identifier.
- action_type: approved_docs_only_apply.
- mode: dry_run or approved_apply.
- target_docs_files: exact future documentation paths.
- proposed_change_summary: concise summary of the future docs changes.
- allowed_files: exact future allowed file scope.
- forbidden_files: exact blocked file scope.
- approval_token_id: token expected before live authority.
- ledger_event_plan: ordered events expected before and after live authority.
- rollback_command: command or note to reverse only the approved docs change.
- verification_command: command expected to verify the docs-only apply.
- head_expected: HEAD value expected before live action.
- git_status_expected: git status expectation before live action.
- blocked: boolean result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Approval Requirements

Future docs-only apply authority requires an explicit approval token scoped to:

- one run.
- one action type: approved_docs_only_apply.
- exact target documentation files.
- exact allowed files.
- exact forbidden files.
- expiration.
- maximum attempts.
- rollback command or rollback note.
- verification command.
- external operator id.

Approval for a preview or dry run is not approval for a live apply. A future live docs-only apply must require its own valid token and ledger trail.

## Event Ledger Requirements

Future docs-only apply actions must emit ledger events before and after the write.

Expected future live event trail:

- action_packet_created.
- approval_requested.
- approval_granted.
- approval_token_created.
- file_write_requested.
- file_write_completed.
- verification_started.
- verification_passed.
- rollback_available.
- action_closed_out.

Blocked attempts must emit file_write_blocked or command_blocked where applicable and must explain the blocked reason.

Level 11.6 does not implement ledger storage or emit runtime ledger events.

## Verification Requirements

Future live docs-only apply must define a verification command before action.

For docs-only apply, future verification must prove:

- every changed file is an approved documentation file.
- every changed file is inside allowed files.
- no changed file intersects forbidden files.
- no source code files changed.
- no API routes changed.
- no service builders changed.
- no tests changed.
- no package files changed.
- no runtime files changed.
- protected paths were not touched.
- Source Proxy stress files were not touched.
- `/coding` UI files were not touched unless explicitly allowed in a future separate lane.
- HEAD and git status expectations were respected or explicitly explained.
- event ledger contains the required event trail.

Level 11.6 does not run verification commands except doc-only manual checks.

## Rollback Requirements

Future live docs-only apply must define rollback before action.

Rollback metadata must explain how to reverse only the approved documentation change without touching unrelated docs, receipts, evidence, run history, branches, worktrees, source code, tests, package files, Source Proxy stress files, or `/coding` UI files.

Level 11.6 does not create rollback artifacts and does not perform cleanup.

## Fail-Closed Rules

Future docs-only apply actions must block when:

- approval token is missing.
- approval token is expired or revoked.
- action type is not approved_docs_only_apply.
- target docs files are missing.
- any target file is outside allowed files.
- any target file intersects forbidden files.
- any target file is not a documentation file.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- source code, API routes, service builders, tests, package files, or runtime files are in scope.
- HEAD expectation is missing or changed unexpectedly.
- git status expectation is missing or changed unexpectedly.
- rollback command or rollback note is missing.
- verification command is missing.
- expected ledger events are missing.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Actions

The future docs-only apply boundary must never authorize:

- source code edits.
- API route edits.
- service builder edits.
- tests.
- package changes.
- runtime behavior changes.
- UI mutation.
- Source Proxy stress testing mutation.
- receipt writing.
- evidence writing.
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

Future docs-only apply actions must treat unexpected HEAD or git status changes as blocking conditions for live authority.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 11.7: Controlled Local Verification Execution Boundary
- Level 11.8: Rollback And Closeout Receipt Boundary
- Level 11.9: Level 11 Closeout And Level 12 Gate

Do not implement any of these in Level 11.6.

## Required Future Tests

Future source-code increments must prove:

- docs-only apply is blocked without approval.
- docs-only apply is blocked with expired approval.
- docs-only apply is blocked with revoked approval.
- docs-only apply is blocked when action_type is not approved_docs_only_apply.
- docs-only apply is blocked when target docs files are outside allowed_files.
- docs-only apply is blocked when forbidden_files match.
- docs-only apply is blocked when target files are not documentation files.
- docs-only apply is blocked when protected paths are in scope.
- docs-only apply is blocked when Source Proxy stress files are in scope.
- docs-only apply is blocked when `/coding` UI files are in scope without a future separate lane.
- source code, API routes, service builders, tests, package files, and runtime files remain blocked.
- docs-only apply is blocked when HEAD changed unexpectedly.
- docs-only apply is blocked when git status changed unexpectedly.
- docs-only apply is blocked when rollback metadata is missing.
- docs-only apply is blocked when verification command is missing.
- docs-only apply records required ledger events in future implementation.
- no receipt writing authority exists.
- no evidence writing authority exists.
- no local execution authority exists.
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

git diff --check -- docs/cartographer-level-11-approved-docs-only-apply-boundary.md

grep -n "Approved Docs-Only Apply Boundary\|Docs Target Rules\|Apply Packet Preview\|Verification Requirements\|Level 11.7: Controlled Local Verification Execution Boundary" docs/cartographer-level-11-approved-docs-only-apply-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-11-approved-docs-only-apply-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 11.6 creates the Approved Docs-Only Apply Boundary only.

Expected result:

- no docs-only apply authority enabled.
- no receipt writing enabled.
- no evidence writing enabled.
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

Level 11.7: Controlled Local Verification Execution Boundary
