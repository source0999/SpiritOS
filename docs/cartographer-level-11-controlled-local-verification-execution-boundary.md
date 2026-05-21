# Cartographer Level 11.7 Controlled Local Verification Execution Boundary

status: local-verification-execution-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 11.7 defines the future boundary for controlled local verification command execution.

This increment is docs-only. It does not execute verification commands, create approval tokens, validate approval tokens, implement an event ledger, add API routes, add service builders, add tests, change runtime behavior, write receipts, write evidence, apply documentation changes, create branches, create worktrees, commit, push, merge, clean up, or mutate files outside this document.

Cartographer remains in observe, recommend, preview, and dry-run posture. No local execution authority, write authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 11.1 created the Controlled Action Authority boundary contract.

Level 11.2 created the Approval Token Schema Preview.

Level 11.3 created the Event Ledger Preview Contract.

Level 11.4 created the Approved Receipt Write Dry Run contract.

Level 11.5 created the Approved Evidence Write Dry Run contract.

Level 11.6 created the Approved Docs-Only Apply Boundary.

Level 11.7 narrows the next design artifact to controlled local verification execution. It does not grant live local execution authority.

## Scope

Allowed in this increment:

- create this controlled local verification execution boundary document.
- define future verification command eligibility.
- define future command packet shape.
- define future approval, token, ledger, rollback, and output requirements.
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
- local command execution authority.
- verification command execution beyond manual doc checks.
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

This boundary is not local execution authority.

A future controlled local verification command may run only after a focused implementation increment, explicit approval token, exact command scope, exact file scope, event ledger trail, timeout policy, output capture policy, rollback metadata when applicable, and focused tests.

Level 11.7 does not create that implementation and does not run verification commands beyond doc-only manual checks.

## Controlled Verification Execution Definition

A future controlled local verification execution is a single approved local command used to verify an approved action.

It must be:

- single-command.
- approval-bound.
- command-scope-bound.
- file-scope-bound.
- run-bound.
- time-limited.
- output-captured.
- event-ledger-recorded.
- fail-closed by default.

Verification execution may inspect approved state and report results. It must not mutate source code, tests, package files, runtime files, Source Proxy stress files, `/coding` UI files, receipts, evidence, run history, branches, worktrees, or protected paths.

## Allowed Future Verification Command Classes

Future implementation may consider narrow verification command classes only:

- git status inspection.
- git diff inspection.
- git diff whitespace checking.
- grep or text presence checks against approved docs files.
- checksum or file existence checks against approved docs, receipt, or evidence files.
- focused read-only validation scripts after explicit future implementation and tests.

Each command class requires a future focused implementation increment and focused tests before it can run as controlled local execution.

## Forbidden Command Classes

Future verification execution must never authorize:

- package installs.
- dependency updates.
- test suite execution without a future explicit boundary.
- Playwright execution.
- proxy stress suites.
- frontend tests.
- Source Proxy stress testing.
- Codex adapter execution.
- long-running task execution.
- code generation.
- file writes.
- receipt writes.
- evidence writes.
- deletion commands.
- cleanup commands.
- checkout.
- stash.
- branch creation.
- worktree creation.
- commit.
- push.
- merge.
- network mutation.
- secret reads or writes.
- background commands.
- hidden retries.

## Command Packet Preview

Future verification command packets must include:

- packet_id: stable command packet identifier.
- run_id: stable run identifier.
- action_type: controlled_local_verification_execution.
- mode: dry_run or approved_execution.
- command: exact command string or structured command array.
- working_directory: exact approved working directory.
- allowed_files: exact file scope the command may inspect.
- forbidden_files: exact blocked file scope.
- approval_token_id: token expected before live execution.
- ledger_event_plan: ordered events expected before and after live execution.
- timeout_seconds: maximum runtime.
- max_attempts: maximum attempts.
- output_capture_policy: stdout and stderr capture rules.
- redaction_policy: output redaction rules for sensitive material.
- rollback_reference: rollback note when the verification command is tied to a live action.
- head_expected: HEAD value expected before live execution.
- git_status_expected: git status expectation before live execution.
- blocked: boolean result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Approval Requirements

Future local verification execution requires an explicit approval token scoped to:

- one run.
- one action type: controlled_local_verification_execution.
- one exact command.
- one exact working directory.
- exact allowed files.
- exact forbidden files.
- expiration.
- maximum attempts.
- timeout.
- output capture policy.
- external operator id.

Approval for a preview or dry run is not approval for live execution. A future live verification command must require its own valid token and ledger trail.

## Event Ledger Requirements

Future controlled local verification execution must emit ledger events before and after command execution.

Expected future live event trail:

- action_packet_created.
- approval_requested.
- approval_granted.
- approval_token_created.
- command_requested.
- verification_started.
- command_completed.
- verification_passed or verification_failed.
- action_closed_out.

Blocked attempts must emit command_blocked and must explain the blocked reason.

Level 11.7 does not implement ledger storage or emit runtime ledger events.

## Output And Evidence Rules

Future verification output must be captured, bounded, and explainable.

Output capture must not write receipts, evidence, run history, proxy memory, blueprints, source code, tests, package files, Source Proxy stress files, or `/coding` UI files unless a separate future action explicitly approves that write.

Sensitive output must be redacted or blocked. Secret path reads or writes remain forbidden.

Verification output is not proof of authority. It is evidence for the operator and future event ledger only after a future implementation exists.

## Rollback Relationship

Verification commands should be read-only. If a future verification command could mutate state, it must be forbidden until a separate explicit implementation boundary exists.

When verification is tied to a live approved action, rollback metadata for the live action must exist before verification execution is allowed.

Level 11.7 does not create rollback artifacts and does not perform cleanup.

## Fail-Closed Rules

Future controlled local verification execution must block when:

- approval token is missing.
- approval token is expired or revoked.
- action type is not controlled_local_verification_execution.
- command is missing.
- command differs from the approved command.
- working directory differs from the approved working directory.
- command is not in an allowed command class.
- command is in a forbidden command class.
- timeout is missing.
- output capture policy is missing.
- redaction policy is missing when sensitive output is possible.
- any target file is outside allowed files.
- any target file intersects forbidden files.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- source code, API routes, service builders, tests, package files, or runtime files are in scope without a future separate boundary.
- HEAD expectation is missing or changed unexpectedly.
- git status expectation is missing or changed unexpectedly.
- expected ledger events are missing.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Actions

The future controlled local verification execution boundary must never authorize:

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
- receipt writing.
- evidence writing.
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
- deletion of evidence.
- deletion of receipts.
- deletion of run history.
- deletion of branches or worktrees.

## Dirty Worktree And Lane Isolation Rules

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit approval.

Future verification execution must treat unexpected HEAD or git status changes as blocking conditions for live execution.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 11.8: Rollback And Closeout Receipt Boundary
- Level 11.9: Level 11 Closeout And Level 12 Gate

Do not implement any of these in Level 11.7.

## Required Future Tests

Future source-code increments must prove:

- local verification execution is blocked without approval.
- local verification execution is blocked with expired approval.
- local verification execution is blocked with revoked approval.
- local verification execution is blocked when action_type is not controlled_local_verification_execution.
- local verification execution is blocked when command differs from approval.
- local verification execution is blocked when working directory differs from approval.
- local verification execution is blocked when command class is forbidden.
- local verification execution is blocked when timeout is missing.
- local verification execution is blocked when output capture policy is missing.
- local verification execution is blocked when allowed_files mismatch.
- local verification execution is blocked when forbidden_files match.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- source code, API routes, service builders, tests, package files, and runtime files remain blocked unless a future separate boundary allows inspection.
- execution is blocked when HEAD changed unexpectedly.
- execution is blocked when git status changed unexpectedly.
- event ledger records command_requested, verification_started, command_completed, and verification_passed or verification_failed in future implementation.
- no write authority exists.
- no receipt writing authority exists.
- no evidence writing authority exists.
- no docs-only apply authority exists.
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

git diff --check -- docs/cartographer-level-11-controlled-local-verification-execution-boundary.md

grep -n "Controlled Local Verification Execution Boundary\|Allowed Future Verification Command Classes\|Command Packet Preview\|Output And Evidence Rules\|Level 11.8: Rollback And Closeout Receipt Boundary" docs/cartographer-level-11-controlled-local-verification-execution-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-11-controlled-local-verification-execution-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 11.7 creates the Controlled Local Verification Execution Boundary only.

Expected result:

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

Level 11.8: Rollback And Closeout Receipt Boundary
