# Cartographer Level 12.7 Retry Policy Boundary

status: retry-policy-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 12.7 defines the future boundary for workflow retry policy.

This increment is docs-only. It does not implement retry runtime behavior, workflow persistence, workflow runners, workflow APIs, timers, cancellation, timeout handling, approval tokens, event ledgers, tests, UI, local execution, writes, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No workflow runtime authority, retry runtime authority, write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 12.1 created the Durable Workflow Autopilot Boundary Contract.

Level 12.2 created the Workflow State Schema Preview.

Level 12.3 created the Workflow Event Ledger Contract.

Level 12.4 created the Workflow Dry Run Packet Boundary.

Level 12.5 created the Pause Resume And Approval Interruption Boundary.

Level 12.6 created the Cancellation And Timeout Boundary.

Level 12.7 narrows the next design artifact to retry policy rules only. It does not advance to workflow closeout or runtime workflow execution.

## Scope

Allowed in this increment:

- create this retry policy boundary document.
- define future retry packet fields.
- define future retry eligibility rules.
- define future retry block rules.
- define future retry ledger requirements.
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
- retry implementation.
- timer implementation.
- cancellation implementation.
- timeout implementation.
- workflow persistence implementation.
- workflow runner implementation.
- workflow API implementation.
- approval token implementation.
- event ledger implementation.
- local command execution.
- write actions.
- receipt or evidence writing.
- docs-only apply implementation.
- rollback command execution.
- run history mutation.
- Scout writes.
- proxy memory writes.
- blueprint writes.
- branch, worktree, checkout, stash, cleanup, commit, push, or merge operations.

## Non-Authority Statement

This boundary is not retry authority.

Future retry policy may describe when a workflow step may be attempted again. It must not start workflows, resume workflows, execute commands, write files, execute rollback, write closeout artifacts, mutate files, or choose alternate work without separate approval.

Level 12.7 does not create runtime retry behavior.

## Retry Definition

A future workflow retry is a bounded, visible, ledgered repeat attempt for an approved workflow step.

Retry must be:

- workflow-bound.
- run-bound.
- step-bound.
- reason-bound.
- max-attempts-bound.
- approval-aware.
- timeout-aware.
- cancellation-aware.
- event-ledger-recorded.
- fail-closed by default.

Retries must never be hidden, unbounded, background-only, self-approved, or used to bypass approval, file scope, command scope, rollback, verification, timeout, cancellation, or lane isolation.

## Retry Packet Preview

Future retry packets must include:

- retry_id: stable retry identifier.
- workflow_id: stable workflow identifier.
- run_id: stable run identifier.
- step_id: retried step identifier.
- step_type: exact retried step class.
- retry_reason: human-readable retry reason.
- retry_count_before: attempts already used.
- max_attempts: maximum attempts allowed.
- next_attempt_number: next attempt number.
- retry_allowed: boolean policy result.
- approval_token_reference: token reference when approval is required.
- allowed_files: exact step file scope.
- forbidden_files: exact blocked file scope.
- command_preview: exact command when retrying a command step.
- write_preview: exact write when retrying a write step.
- rollback_reference: rollback note or rollback packet reference.
- verification_reference: verification command preview.
- timeout_policy_reference: timeout policy for the retry.
- cancellation_policy_reference: cancellation policy for the workflow.
- event_ledger_plan: required retry events.
- head_expected: HEAD value expected before retry.
- git_status_expected: git status expectation before retry.
- blocked: boolean retry result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Retry Eligibility Rules

Future retry may be eligible only when:

- retry policy exists.
- retry reason is recorded.
- retry_count_before is below max_attempts.
- workflow is not cancelled.
- workflow is not closed out.
- timeout policy allows another attempt.
- approval is valid when approval is required.
- step action type matches approval when approval is required.
- command or write preview matches approval when approval is required.
- allowed_files match step scope.
- forbidden_files do not match target files.
- rollback reference exists when retrying live write or execution.
- verification reference exists when retrying live write or execution.
- event ledger continuity is intact.
- HEAD expectation is present and unchanged.
- git status expectation is present and unchanged.

Eligibility is advisory until a future focused implementation and tests exist.

## Retry Block Rules

Future retry must be blocked when:

- retry policy is missing.
- retry reason is missing.
- max_attempts is missing.
- retry_count_before is greater than or equal to max_attempts.
- workflow is cancelled.
- workflow is closed out.
- timeout policy blocks another attempt.
- approval is required but absent.
- approval is expired.
- approval is revoked.
- approval scope and retry scope do not match.
- command differs from approval.
- write target differs from approval.
- allowed_files mismatch.
- forbidden_files match.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- rollback reference is missing when required.
- verification reference is missing when required.
- event ledger continuity is missing.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Blocked retries must be honest, visible, and explainable.

## Event Ledger Requirements

Future retry behavior must be ledger-visible.

Expected future retry event trail:

- workflow_step_failed or workflow_step_blocked before retry.
- workflow_step_started for retry attempt.
- command_requested or file_write_requested when applicable.
- command_completed, command_blocked, file_write_completed, or file_write_blocked when applicable.
- verification_started when verification applies.
- verification_passed or verification_failed when verification applies.
- workflow_step_completed, workflow_step_failed, or workflow_step_blocked according to outcome.

Retry count and retry reason must be included in the event trail.

Level 12.7 does not implement ledger storage or emit runtime ledger events.

## Timeout And Cancellation Relationship

Retries must obey timeout and cancellation policy.

A cancelled workflow cannot retry.

A timed-out workflow cannot retry unless a future explicit policy and approval allow a known next attempt from durable state.

Retry policy must not override cancellation, timeout, approval rejection, stale approval, or closeout.

## Fail-Closed Rules

Future retry behavior must fail closed when:

- workflow state is missing.
- retry packet is missing.
- retry policy is missing.
- retry reason is missing.
- max_attempts is missing.
- max_attempts is exceeded.
- approval is absent when required.
- approval is expired or revoked.
- workflow is cancelled.
- workflow is closed out.
- timeout policy blocks retry.
- event ledger continuity is missing.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- protected paths are touched.
- Source Proxy stress files are touched.
- `/coding` UI files are touched without a future separate lane.
- rollback would execute without separate approval.
- closeout artifact would be written without separate approval.
- cleanup would occur.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Retry Uses

Future retry behavior must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- hidden background workflows.
- hidden retries.
- unbounded loops.
- autonomous task selection.
- automatic promotion.
- retry after cancellation without separate explicit approval.
- retry after closeout.
- rollback execution without approval.
- closeout receipt writing without approval.
- receipt writing.
- evidence writing.
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
- force overwrite.
- deletion of evidence.
- deletion of receipts.
- deletion of run history.
- deletion of branches or worktrees.

## Dirty Worktree And Lane Isolation Rules

Dirty worktree state may be observed and reported. It must not be cleaned, stashed, checked out, overwritten, staged, committed, pushed, merged, or used as implicit approval.

Future retry must treat unexpected HEAD or git status changes as blocking conditions.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 12.8: Workflow Closeout Boundary
- Level 12.9: Level 12 Closeout And Level 13 Gate

Do not implement any of these in Level 12.7.

## Required Future Tests

Future source-code increments must prove:

- retry is blocked when retry policy is missing.
- retry is blocked when retry reason is missing.
- retry is blocked when max_attempts is missing.
- retry is blocked when max_attempts is exceeded.
- retry is blocked after workflow cancellation.
- retry is blocked after workflow closeout.
- retry is blocked when timeout policy blocks retry.
- retry is blocked without approval when approval is required.
- retry is blocked with expired approval.
- retry is blocked with revoked approval.
- retry is blocked when command differs from approval.
- retry is blocked when write target differs from approval.
- retry is blocked when allowed_files mismatch.
- retry is blocked when forbidden_files match.
- retry is blocked when HEAD changed unexpectedly.
- retry is blocked when git status changed unexpectedly.
- event ledger records retry count and retry reason.
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

git diff --check -- docs/cartographer-level-12-retry-policy-boundary.md

grep -n "Retry Policy Boundary\|Retry Packet Preview\|Retry Eligibility Rules\|Retry Block Rules\|Level 12.8: Workflow Closeout Boundary" docs/cartographer-level-12-retry-policy-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-12-retry-policy-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 12.7 creates the Retry Policy Boundary only.

Expected result:

- no retry runtime enabled.
- no cancellation runtime enabled.
- no timeout runtime enabled.
- no timer runtime enabled.
- no pause/resume runtime enabled.
- no approval interruption runtime enabled.
- no workflow dry-run runtime enabled.
- no workflow packet runtime enabled.
- no workflow event ledger runtime enabled.
- no workflow state persistence enabled.
- no workflow runner enabled.
- no workflow API enabled.
- no approval token runtime authority enabled.
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

Level 12.8: Workflow Closeout Boundary
