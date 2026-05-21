# Cartographer Level 11.5 Approved Evidence Write Dry Run

status: evidence-write-dry-run-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 11.5 defines the future dry-run boundary for approved evidence writing.

This increment is docs-only. It does not write evidence, write receipts, create approval tokens, validate approval tokens, implement an event ledger, add API routes, add service builders, add tests, change runtime behavior, execute commands, create branches, create worktrees, commit, push, merge, clean up, or mutate files outside this document.

Cartographer remains in observe, recommend, preview, and dry-run posture. No write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 11.1 created the Controlled Action Authority boundary contract.

Level 11.2 created the Approval Token Schema Preview.

Level 11.3 created the Event Ledger Preview Contract.

Level 11.4 created the Approved Receipt Write Dry Run contract.

Level 11.5 narrows the next design artifact to approved evidence writing in dry-run form only. It does not grant live evidence-writing authority.

## Scope

Allowed in this increment:

- create this approved evidence write dry-run document.
- define future dry-run evidence write packet shape.
- define future evidence target rules.
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
- evidence writing.
- receipt writing.
- event ledger implementation.
- approval token implementation.
- action execution.
- run history mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- branch, worktree, checkout, stash, cleanup, commit, push, or merge operations.

## Non-Authority Statement

This dry-run contract is not evidence-writing authority.

An approved evidence write dry run may preview what a future evidence write would do, why it would be allowed or blocked, what file it would target, what approval token it would require, what ledger events it would emit, what verification would run, and what rollback note would exist.

The dry run must not create, modify, delete, stage, commit, push, or otherwise mutate any evidence file.

## Dry Run Definition

A future approved evidence write dry run is a simulated action packet for a single evidence write.

It must be:

- single-action.
- approval-preview-bound.
- file-scope-preview-bound.
- run-bound.
- time-limited in preview.
- rollback-preview-required.
- verification-preview-required.
- event-ledger-preview-recorded.
- fail-closed by default.

The dry run may say whether the future live action appears eligible. It must not perform the action.

## Evidence Target Rules

Future evidence write dry runs must identify:

- evidence target file.
- evidence action type.
- evidence purpose.
- run id.
- action packet id.
- approval token id or token preview reference.
- allowed files.
- forbidden files.
- protected path check result.
- lane isolation check result.
- HEAD expectation.
- git status expectation.
- rollback note.
- verification command.
- expected ledger events.
- blocked reason when blocked.

The dry run must block if the target file is outside allowed evidence scope or intersects forbidden files.

## Dry Run Packet Preview

Future dry-run packets must include:

- packet_id: stable dry-run packet identifier.
- run_id: stable run identifier.
- action_type: approved_evidence_write.
- mode: dry_run.
- target_evidence_file: exact future evidence path.
- proposed_evidence_summary: concise summary of the future evidence content.
- evidence_purpose: reason the future evidence artifact is needed.
- allowed_files: exact future allowed file scope.
- forbidden_files: exact blocked file scope.
- approval_token_preview: token fields expected before live authority.
- ledger_event_preview: ordered events expected before and after live authority.
- rollback_note: rollback plan for the future evidence write.
- verification_command: command expected to verify the future evidence write.
- head_expected: HEAD value expected before live action.
- git_status_expected: git status expectation before live action.
- blocked: boolean dry-run result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Approval Requirements

Future live evidence writing requires an explicit approval token scoped to:

- one run.
- one action type: approved_evidence_write.
- one target evidence file.
- exact allowed files.
- exact forbidden files.
- expiration.
- maximum attempts.
- rollback command or rollback note.
- verification command.
- external operator id.

Level 11.5 does not create or consume approval tokens.

Approval for a dry run is not approval for a live write. A future live evidence write must require its own valid token and ledger trail.

## Event Ledger Requirements

Future evidence write dry runs must preview the ledger events that a live evidence write would require.

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

Blocked dry runs must preview file_write_blocked or command_blocked where applicable and must explain the blocked reason.

Level 11.5 does not implement ledger storage or emit runtime ledger events.

## Verification Requirements

Future live evidence writing must define a verification command before action.

For evidence writes, future verification must prove:

- expected evidence file exists.
- evidence path is inside allowed files.
- evidence path is outside forbidden files.
- evidence content matches the approved action packet.
- evidence purpose is recorded.
- protected paths were not touched.
- Source Proxy stress files were not touched.
- `/coding` UI files were not touched.
- HEAD and git status expectations were respected or explicitly explained.
- event ledger contains the required event trail.

Level 11.5 does not run verification commands except doc-only manual checks.

## Rollback Requirements

Future live evidence writing must define rollback before action.

Rollback metadata must explain how to remove or supersede the future evidence write without touching unrelated files, receipts, run history, branches, worktrees, source code, tests, package files, Source Proxy stress files, or `/coding` UI files.

Level 11.5 does not create rollback artifacts and does not perform cleanup.

## Fail-Closed Rules

Future evidence write dry runs must block when:

- approval token preview is missing.
- action type is not approved_evidence_write.
- target evidence file is missing.
- evidence purpose is missing.
- target evidence file is outside allowed files.
- target evidence file intersects forbidden files.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope.
- HEAD expectation is missing.
- git status expectation is missing.
- rollback note is missing.
- verification command is missing.
- expected ledger events are missing.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Actions

The future evidence write dry run must never authorize:

- live evidence writing.
- receipt writing.
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

Future evidence write dry runs must treat unexpected HEAD or git status changes as blocking conditions for live authority.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 11.6: Approved Docs-Only Apply Boundary
- Level 11.7: Controlled Local Verification Execution Boundary
- Level 11.8: Rollback And Closeout Receipt Boundary
- Level 11.9: Level 11 Closeout And Level 12 Gate

Do not implement any of these in Level 11.5.

## Required Future Tests

Future source-code increments must prove:

- dry run does not write evidence.
- dry run does not write receipts.
- dry run does not mutate run history.
- dry run is blocked without approval token preview.
- dry run is blocked when action_type is not approved_evidence_write.
- dry run is blocked when evidence purpose is missing.
- dry run is blocked when target evidence file is outside allowed_files.
- dry run is blocked when forbidden_files match.
- dry run is blocked when protected paths are in scope.
- dry run is blocked when Source Proxy stress files are in scope.
- dry run is blocked when `/coding` UI files are in scope.
- dry run is blocked when HEAD expectation is missing.
- dry run is blocked when git status expectation is missing.
- dry run is blocked when rollback note is missing.
- dry run is blocked when verification command is missing.
- dry run previews required ledger events.
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

git diff --check -- docs/cartographer-level-11-approved-evidence-write-dry-run.md

grep -n "Approved Evidence Write Dry Run\|Dry Run Packet Preview\|Evidence Target Rules\|Verification Requirements\|Level 11.6: Approved Docs-Only Apply Boundary" docs/cartographer-level-11-approved-evidence-write-dry-run.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-11-approved-evidence-write-dry-run.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 11.5 creates the Approved Evidence Write Dry Run contract only.

Expected result:

- no evidence writing enabled.
- no receipt writing enabled.
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

Level 11.6: Approved Docs-Only Apply Boundary
