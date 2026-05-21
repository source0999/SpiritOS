# Cartographer Level 11.2 Approval Token Schema Preview

status: schema-preview-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 11.2 defines the future approval token schema for Controlled Action Authority.

This increment is docs-only. It does not implement token creation, token validation, API routes, service builders, tests, runtime writes, command execution, receipts, evidence, event ledgers, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 11.1 created the Controlled Action Authority boundary contract. That contract defined future authority as single-action, approval-bound, file-scope-bound, run-bound, time-limited, rollback-required, verification-required, event-ledger-recorded, and fail-closed by default.

Level 11.2 narrows the next design artifact to approval token shape only. It does not advance to the event ledger, receipt writes, evidence writes, docs-only apply actions, local verification execution, rollback execution, or closeout authority.

## Scope

Allowed in this increment:

- create this approval token schema preview document.
- define future token fields.
- define future token lifecycle states.
- define future validation and invalidation rules.
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
- token creation at runtime.
- token validation at runtime.
- action execution.
- receipt or evidence writing.
- event ledger implementation.
- run history mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- branch, worktree, checkout, stash, cleanup, commit, push, or merge operations.

## Non-Authority Statement

This schema is not permission.

An approval token described here is a future control object that must later be implemented behind fail-closed checks. No operator approval token exists because of this document, and no future action may treat this document as a standing approval.

Future implementation must prove that schema presence does not equal authority. A token is valid only when a future implementation creates it for one run, one action type, exact file scope, explicit operator approval, expiration, rollback metadata, verification metadata, and event-ledger tracking.

## Approval Token Schema Preview

Future approval tokens must include:

- token_id: stable unique token identifier.
- run_id: stable run identifier the token belongs to.
- action_type: exact approved action class.
- target_files: exact files requested by the action.
- allowed_files: exact files the action may touch.
- forbidden_files: files or path patterns the action must not touch.
- expires_at: timestamp after which the token is invalid.
- max_attempts: maximum attempts allowed for the approved action.
- rollback_command: command or documented rollback step required before live action.
- verification_command: command required to verify the action after completion.
- operator_id: identifier for the approving operator.
- created_at: timestamp when the token was created.
- used_at: timestamp when the token was consumed, initially null.
- revoked: boolean revocation flag.

Future implementation may add derived display fields, but it must not remove or weaken these required fields.

## Field Rules

token_id must be unique, stable, and non-empty.

run_id must match the active run. A token from one run cannot approve another run.

action_type must match the exact future action class being attempted. A token for receipt writing cannot approve evidence writing, docs-only apply actions, local verification execution, rollback execution, branch creation, worktree creation, commit, push, merge, cleanup, or any unrelated action.

target_files and allowed_files must be compared as normalized repository-relative paths. The action must be blocked unless every target file is inside allowed_files and outside forbidden_files.

forbidden_files must block protected paths, secret paths, Source Proxy stress files, `/coding` UI files, Scout writes, proxy memory writes, blueprint writes, branches, worktrees, package files, tests, source code, API routes, service builders, runtime files, and any operator-declared isolated lane unless a future separate lane explicitly allows them.

expires_at must be enforced. Expired tokens are invalid.

max_attempts must be enforced. Hidden retries are forbidden.

rollback_command must exist before live write or execution authority is possible. Missing rollback metadata blocks the action.

verification_command must exist before live write or execution authority is possible. Missing verification metadata blocks the action.

operator_id must identify an external operator. Self-approval is forbidden.

used_at must prevent accidental token reuse unless a future implementation explicitly models attempts within max_attempts.

revoked true means blocked, even if every other field appears valid.

## Token Lifecycle

Future token lifecycle states:

- previewed.
- approval_requested.
- approved.
- active.
- used.
- expired.
- revoked.
- rejected.
- blocked.
- closed_out.

Level 11.2 does not create lifecycle storage or transitions. These states define future behavior only.

## Invalidation Rules

Future approval tokens must be invalid when:

- approval is missing.
- approval is self-issued.
- token is expired.
- token is revoked.
- token was already used outside the allowed attempt model.
- run_id does not match the active run.
- action_type does not match the requested action.
- target_files and allowed_files do not match.
- requested files intersect forbidden_files.
- approval scope and action scope do not match.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- protected paths are touched.
- secret paths are read or written.
- Source Proxy stress files are touched.
- `/coding` UI files are touched without a future separate lane.
- rollback metadata is missing.
- verification metadata is missing.
- event ledger recording is unavailable in a future live-action increment.

Invalid tokens must fail closed with an honest, explainable blocked result.

## Allowed Future Action Types

Future tokens may be designed for these Level 11 action classes only after focused implementation increments and focused tests:

1. approved receipt writing.
2. approved evidence writing.
3. approved closeout packet finalization.
4. approved docs-only apply actions.
5. approved metadata-only action packets.
6. approved local verification command execution.
7. approved rollback command execution.

Level 11.2 implements none of these actions.

## Forbidden Token Uses

Future approval tokens must never authorize:

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

## Event Ledger Relationship

Level 11.2 does not implement the event ledger.

Future token behavior must be recorded in an append-only event ledger. At minimum, token preview, approval request, approval grant, approval rejection, token creation, token revocation, token use, blocked action, completed action, verification, rollback availability, and closeout must become ledger-visible before live authority exists.

The UI may render token and ledger state, but the UI is not the source of truth.

## Dirty Worktree And Lane Isolation Rules

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit approval.

Future tokens are invalid if git status changes unexpectedly after approval. Dirty files in unrelated lanes remain unrelated and untouched.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 11.3: Event Ledger Preview Contract
- Level 11.4: Approved Receipt Write Dry Run
- Level 11.5: Approved Evidence Write Dry Run
- Level 11.6: Approved Docs-Only Apply Boundary
- Level 11.7: Controlled Local Verification Execution Boundary
- Level 11.8: Rollback And Closeout Receipt Boundary
- Level 11.9: Level 11 Closeout And Level 12 Gate

Do not implement any of these in Level 11.2.

## Required Future Tests

Future source-code increments must prove:

- action is blocked without approval.
- action is blocked with expired approval.
- action is blocked with revoked approval.
- action is blocked after token reuse outside the allowed attempt model.
- action is blocked when run_id does not match.
- action is blocked when action_type does not match.
- action is blocked when allowed_files mismatch.
- action is blocked when forbidden_files match.
- action is blocked when HEAD changed unexpectedly.
- action is blocked when git status changed unexpectedly.
- protected paths remain blocked.
- secret paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- no branch/worktree authority exists.
- no checkout/stash/cleanup authority exists.
- no commit/push/merge authority exists.
- no self-approval exists.
- no hidden background mutation exists.
- rollback metadata exists before live action.
- verification metadata exists before live action.
- event ledger records every future token step.
- failures are honest and explainable.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-11-approval-token-schema-preview.md

grep -n "Approval Token Schema Preview\|Field Rules\|Invalidation Rules\|Required Future Tests\|Level 11.3: Event Ledger Preview Contract" docs/cartographer-level-11-approval-token-schema-preview.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-11-approval-token-schema-preview.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 11.2 creates the Approval Token Schema Preview only.

Expected result:

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

Level 11.3: Event Ledger Preview Contract
