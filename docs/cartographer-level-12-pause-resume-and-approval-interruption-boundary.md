# Cartographer Level 12.5 Pause Resume And Approval Interruption Boundary

status: pause-resume-approval-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 12.5 defines the future boundary for workflow pause, resume, and approval interruption behavior.

This increment is docs-only. It does not implement pause/resume runtime behavior, approval interruption runtime behavior, workflow persistence, workflow runners, workflow APIs, approval tokens, event ledgers, tests, UI, local execution, writes, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No workflow runtime authority, approval interruption runtime authority, write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 12.1 created the Durable Workflow Autopilot Boundary Contract.

Level 12.2 created the Workflow State Schema Preview.

Level 12.3 created the Workflow Event Ledger Contract.

Level 12.4 created the Workflow Dry Run Packet Boundary.

Level 12.5 narrows the next design artifact to pause, resume, and approval interruption rules only. It does not advance to cancellation, timeout, retry, closeout, or runtime workflow execution.

## Scope

Allowed in this increment:

- create this pause resume and approval interruption boundary document.
- define future pause state rules.
- define future resume state rules.
- define future approval interruption packet fields.
- define future approval rejection and stale approval rules.
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
- pause/resume implementation.
- approval interruption implementation.
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

This boundary is not workflow execution authority.

A future paused workflow may wait for operator input. A future resumed workflow may continue only from known durable state after explicit approval and policy checks. Neither state may be inferred from chat messages alone.

Level 12.5 does not create runtime pause, resume, approval, rejection, or workflow continuation behavior.

## Pause Definition

A future workflow pause is a durable workflow state that stops future steps until a permitted resume, cancel, or closeout action occurs.

Pause must be:

- workflow-bound.
- run-bound.
- step-bound when a step caused the pause.
- reason-bound.
- approval-interruptible when approval is required.
- event-ledger-recorded.
- visible to the operator.
- fail-closed by default.

A paused workflow must not continue in the background, retry silently, promote itself, write artifacts, execute commands, or mutate files.

## Resume Definition

A future workflow resume is a controlled continuation from durable paused state.

Resume must be:

- workflow-bound.
- run-bound.
- step-bound when resuming a step.
- approval-bound when approval caused the pause.
- state-version-bound.
- event-ledger-recorded.
- verification-aware.
- fail-closed by default.

Resume must re-check workflow state, HEAD, git status, approval scope, allowed files, forbidden files, lane isolation, retry policy, timeout policy, cancellation policy, rollback requirements, verification requirements, and event ledger continuity.

## Approval Interruption Definition

A future approval interruption is a durable pause created before a sensitive workflow step.

Sensitive steps include:

- file writes.
- receipt writes.
- evidence writes.
- docs-only apply actions.
- local verification command execution.
- rollback command execution.
- closeout receipt writing.
- protected path inspection or mutation.
- lane-sensitive path inspection or mutation.

Approval interruption does not grant authority by itself. It only records that the workflow must wait.

## Approval Interruption Packet Preview

Future approval interruption packets must include:

- interruption_id: stable interruption identifier.
- workflow_id: stable workflow identifier.
- run_id: stable run identifier.
- step_id: interrupted step identifier.
- step_type: exact interrupted step class.
- requested_action_type: exact action requiring approval.
- reason: human-readable reason approval is required.
- target_files: files involved in the interrupted step.
- allowed_files: exact allowed file scope.
- forbidden_files: exact blocked file scope.
- command_preview: exact command when a command is involved.
- write_preview: exact file write when a write is involved.
- rollback_reference: rollback note or rollback packet reference.
- verification_reference: verification command preview.
- approval_token_preview: token fields required before resume.
- expires_at: approval interruption expiration.
- head_expected: HEAD value expected before resume.
- git_status_expected: git status expectation before resume.
- event_ledger_plan: required pause, approval, and resume events.
- blocked: boolean interruption result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Approval Grant Rules

Future approval grants must be:

- explicit.
- operator-issued.
- workflow-bound.
- run-bound.
- step-bound.
- action-type-bound.
- file-scope-bound.
- time-limited.
- ledger-recorded.
- non-transferable.

Approval for one paused step cannot approve future unrelated steps.

Approval for a dry run cannot approve live workflow execution.

Approval must be invalid if HEAD, git status, file scope, command scope, action type, or lane ownership changes unexpectedly.

## Approval Rejection Rules

Future approval rejection must keep the workflow paused, blocked, cancelled, or closed out according to explicit policy.

Rejected approval must be ledgered and visible.

Rejected approval must not trigger fallback execution, hidden retries, automatic promotion, cleanup, rollback execution, or alternate task selection.

## Stale Approval Rules

Future approval interruptions become stale when:

- approval expires.
- workflow state changes unexpectedly.
- HEAD changes unexpectedly.
- git status changes unexpectedly.
- target files change unexpectedly.
- approval scope no longer matches step scope.
- lane ownership becomes ambiguous.
- operator revokes approval.

Stale approvals must fail closed and require a new approval interruption or closeout policy.

## Event Ledger Requirements

Future pause, resume, and approval interruption behavior must be ledger-visible.

Expected future event trail:

- workflow_step_started or workflow_step_blocked.
- approval_requested.
- workflow_paused.
- approval_granted or approval_rejected.
- approval_token_created when approved.
- workflow_resumed only after valid approval when resumption is allowed.
- workflow_step_completed, workflow_step_blocked, workflow_step_failed, or workflow_closed_out according to outcome.

Level 12.5 does not implement ledger storage or emit runtime ledger events.

## Fail-Closed Rules

Future pause, resume, and approval interruption behavior must fail closed when:

- workflow state is missing.
- paused state is missing.
- approval interruption packet is missing.
- approval is absent.
- approval is expired.
- approval is revoked.
- approval was rejected.
- approval scope and step scope do not match.
- action type differs from approval.
- command differs from approval.
- write target differs from approval.
- allowed files do not match target files.
- forbidden files are touched.
- protected paths are touched.
- Source Proxy stress files are touched.
- `/coding` UI files are touched without a future separate lane.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- event ledger continuity is missing.
- rollback reference is missing when required.
- verification reference is missing when required.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Pause Resume Uses

Future pause, resume, and approval interruption must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- hidden background workflows.
- hidden retries.
- unbounded loops.
- autonomous task selection.
- automatic promotion.
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

Future resume must treat unexpected HEAD or git status changes as blocking conditions.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 12.6: Cancellation And Timeout Boundary
- Level 12.7: Retry Policy Boundary
- Level 12.8: Workflow Closeout Boundary
- Level 12.9: Level 12 Closeout And Level 13 Gate

Do not implement any of these in Level 12.5.

## Required Future Tests

Future source-code increments must prove:

- workflow pauses before sensitive steps.
- paused workflow does not continue in the background.
- resume is blocked without approval.
- resume is blocked with expired approval.
- resume is blocked with revoked approval.
- resume is blocked after approval rejection.
- resume is blocked when action type differs from approval.
- resume is blocked when command differs from approval.
- resume is blocked when write target differs from approval.
- resume is blocked when allowed_files mismatch.
- resume is blocked when forbidden_files match.
- resume is blocked when HEAD changed unexpectedly.
- resume is blocked when git status changed unexpectedly.
- protected paths remain blocked.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- approval for one step cannot approve unrelated future steps.
- approval rejection does not trigger fallback execution.
- stale approvals fail closed.
- event ledger records approval_requested, workflow_paused, approval_granted, approval_rejected, and workflow_resumed when applicable.
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

git diff --check -- docs/cartographer-level-12-pause-resume-and-approval-interruption-boundary.md

grep -n "Pause Resume And Approval Interruption Boundary\|Approval Interruption Packet Preview\|Approval Grant Rules\|Stale Approval Rules\|Level 12.6: Cancellation And Timeout Boundary" docs/cartographer-level-12-pause-resume-and-approval-interruption-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-12-pause-resume-and-approval-interruption-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 12.5 creates the Pause Resume And Approval Interruption Boundary only.

Expected result:

- no pause/resume runtime enabled.
- no approval interruption runtime enabled.
- no workflow dry-run runtime enabled.
- no workflow packet runtime enabled.
- no workflow event ledger runtime enabled.
- no workflow state persistence enabled.
- no workflow runner enabled.
- no workflow API enabled.
- no retry runtime enabled.
- no timeout runtime enabled.
- no cancellation runtime enabled.
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

Level 12.6: Cancellation And Timeout Boundary
