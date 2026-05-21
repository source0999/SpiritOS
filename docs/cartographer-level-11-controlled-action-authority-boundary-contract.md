# Cartographer Level 11 Controlled Action Authority Boundary Contract

status: planning-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 11.1 defines the boundary contract for future Controlled Action Authority.

This increment is docs-only. It does not enable action authority, runtime writes, local execution, API routes, service builders, tests, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or any background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture until future increments explicitly unlock scoped authority.

## Starting Point

Level 10.7 is complete and remains the hard stop that required explicit operator permission before any new roadmap or Level 11 work.

The operator has explicitly requested Level 11.1 only. That request allows this boundary contract document and does not authorize Level 11.2, action authority, code implementation, tests, execution, receipts, evidence, run history mutation, Source Proxy stress-lane work, `/coding` UI work, Scout work, proxy memory writes, blueprint writes, branch creation, worktree creation, commit, push, merge, or cleanup.

## Scope

This contract defines what Level 11 may eventually implement, what remains forbidden, and what proof is required before actual write or execution authority can be added.

Allowed in this increment:

- create this Level 11.1 boundary contract document.
- run doc-only verification commands for this document.
- observe unrelated dirty worktree state without modifying it.

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
- action execution.
- receipt or evidence writing.
- run history mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- branch, worktree, checkout, stash, cleanup, commit, push, or merge operations.

## Non-Negotiable Boundary

Level 11.1 grants no authority. It is a planning boundary only.

Future Level 11 authority must be unlocked by exact increment, exact action type, exact file scope, explicit operator approval, focused tests, manual checks, rollback metadata, verification requirements, and fail-closed policy.

No roadmap, previous approval, passing test result, UI affordance, operator trust, or successful dry run may be interpreted as global permission.

## Controlled Action Authority Definition

Controlled Action Authority is future authority that is:

- single-action.
- approval-bound.
- file-scope-bound.
- run-bound.
- time-limited.
- rollback-required.
- verification-required.
- event-ledger-recorded.
- fail-closed by default.

Controlled Action Authority never means broad autonomy, global write permission, hidden execution, automatic promotion, self-approval, branch/worktree authority, or commit/push/merge authority.

## Authority Ladder Placement

Level 11 sits on this roadmap authority ladder:

- Authority 0: Observe
- Authority 1: Recommend
- Authority 2: Preview
- Authority 3: Dry Run
- Authority 4: Approved Write
- Authority 5: Approved Local Execution

Level 11 may design the path toward Authority 4 and narrow Authority 5. Level 11.1 grants neither.

Cartographer remains at observe, recommend, preview, and dry-run posture in this increment.

## Allowed Future Level 11 Action Classes

The following are future possible action classes only:

1. approved receipt writing.
2. approved evidence writing.
3. approved closeout packet finalization.
4. approved docs-only apply actions.
5. approved metadata-only action packets.
6. approved local verification command execution.
7. approved rollback command execution.

Each action class requires a future focused implementation increment and focused tests. None are implemented by Level 11.1.

## Forbidden Actions

The following remain forbidden:

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

## Approval Token Requirements

Future approval tokens must include:

- token id.
- run id.
- action type.
- target files.
- allowed files.
- forbidden files.
- expires at.
- max attempts.
- rollback command.
- verification command.
- operator id.
- created at.
- used at.
- revoked flag.

Tokens are not global permission. Tokens cannot approve future unrelated actions. Tokens cannot approve broader file scope than originally granted. Tokens expire.

Tokens are invalid if git status changes unexpectedly, HEAD changes unexpectedly, protected paths are touched, or approval scope and action scope do not match.

## Event Ledger Requirements

Future Controlled Action Authority must use an append-only event ledger with at least:

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

No event may be silently rewritten. No action counts as complete without an event trail. The UI may render the ledger, but the UI is not the source of truth.

Future implementation must prove no hidden mutation occurred.

## Receipt And Evidence Rules

Level 11.1 does not write receipts or evidence.

Future receipt and evidence writes must be explicitly approved, file-scope-bound, run-bound, rollback-described, verification-gated, event-ledger-recorded, and blocked outside the approved action class.

Evidence and receipts must not be deleted by Controlled Action Authority. If a future correction is needed, it must be represented as a new approved action with a new event trail, not silent deletion or overwrite.

## Fail-Closed Rules

Future authority must fail closed when:

- approval is absent.
- approval is expired.
- approval was revoked.
- approval scope and action scope do not match.
- allowed files do not match the requested target files.
- forbidden files are touched.
- protected paths are touched.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- rollback metadata is missing.
- verification command is missing when required.
- event ledger write fails.
- lane ownership is ambiguous.
- Source Proxy stress or `/coding` UI paths are in scope without a separate explicit lane.

Failure must be honest, visible, and explainable. Hidden retries and background mutation remain forbidden.

## Dirty Worktree And Lane Isolation Rules

Cartographer may observe dirty worktree state and report it as unrelated pre-existing state.

Observation does not authorize cleanup, stash, checkout, overwrite, branch creation, worktree creation, commit, push, merge, or mutation of those files.

Dirty files in Source Proxy stress testing, `/coding` UI, source code, tests, package files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, or dashboard lanes must remain untouched unless a separate explicit future lane authorizes them.

Cross-lane mutation is blocked by default.

## Required Future Implementation Shape

Future Level 11 implementation must proceed in small increments:

- Level 11.2: Approval Token Schema Preview
- Level 11.3: Event Ledger Preview Contract
- Level 11.4: Approved Receipt Write Dry Run
- Level 11.5: Approved Evidence Write Dry Run
- Level 11.6: Approved Docs-Only Apply Boundary
- Level 11.7: Controlled Local Verification Execution Boundary
- Level 11.8: Rollback And Closeout Receipt Boundary
- Level 11.9: Level 11 Closeout And Level 12 Gate

Do not implement any of these in Level 11.1.

## Required Future Tests

Future source-code increments must test both allowed and forbidden behavior.

Future tests must prove:

- action is blocked without approval.
- action is blocked with expired approval.
- action is blocked when allowed_files mismatch.
- action is blocked when HEAD changed unexpectedly.
- action is blocked when git status changed unexpectedly.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- no branch/worktree authority exists.
- no commit/push/merge authority exists.
- no self-approval exists.
- no hidden background mutation exists.
- rollback metadata exists before live action.
- event ledger records every step.
- failures are honest and explainable.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-11-controlled-action-authority-boundary-contract.md

grep -n "Controlled Action Authority Definition\|Approval Token Requirements\|Event Ledger Requirements\|Level 11.2: Approval Token Schema Preview" docs/cartographer-level-11-controlled-action-authority-boundary-contract.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-11-controlled-action-authority-boundary-contract.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 11.1 creates the Controlled Action Authority boundary contract only.

Expected result:

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

Level 11.2: Approval Token Schema Preview
