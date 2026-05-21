# Cartographer Level 12.3 Workflow Event Ledger Contract

status: ledger-contract-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 12.3 defines the future workflow event ledger contract for Durable Workflow Autopilot.

This increment is docs-only. It does not implement workflow event storage, workflow persistence, workflow runners, workflow APIs, pause/resume, cancellation, retries, timers, approval interruptions, tests, UI, local execution, writes, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No durable workflow runtime authority, event ledger runtime authority, write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 12.1 created the Durable Workflow Autopilot Boundary Contract.

Level 12.2 created the Workflow State Schema Preview.

Level 12.3 narrows the next design artifact to workflow event ledger shape and rules only. It does not advance to workflow dry-run packets, pause/resume, cancellation, timeout, retry, closeout, or runtime workflow execution.

## Scope

Allowed in this increment:

- create this workflow event ledger contract document.
- define future workflow event names.
- define future workflow event envelope fields.
- define future append-only rules.
- define future completion, pause, resume, cancellation, retry, and timeout event requirements.
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
- workflow event ledger implementation.
- workflow persistence implementation.
- workflow runner implementation.
- workflow API implementation.
- approval token implementation.
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

This ledger contract is not workflow authority.

A workflow event described here is a future audit and control record. It must not be treated as permission to start, resume, retry, cancel, execute, write, verify, rollback, close out, or mutate anything.

Future implementation must prove that event presence does not bypass approval, workflow state validity, file scope, command scope, rollback requirements, verification requirements, or lane isolation.

## Workflow Event Ledger Definition

The future workflow event ledger is an append-only record of Durable Workflow Autopilot state transitions.

It must record workflow creation, dry-run creation, start, pause, resume, cancellation request, cancellation completion, step start, step block, step completion, step failure, approvals, command requests, command blocks, command completions, file write requests, file write blocks, file write completions, verification, rollback availability, rollback requests, rollback completion, and workflow closeout.

The ledger is the source of truth for future workflow state. The UI may render ledger state, but the UI is not the source of truth.

## Required Workflow Event Names

Future workflow ledger implementations must support at least:

- workflow_created.
- workflow_dry_run_created.
- workflow_started.
- workflow_paused.
- workflow_resumed.
- workflow_cancel_requested.
- workflow_cancelled.
- workflow_step_started.
- workflow_step_blocked.
- workflow_step_completed.
- workflow_step_failed.
- approval_requested.
- approval_granted.
- approval_rejected.
- approval_token_created.
- approval_token_revoked.
- command_requested.
- command_blocked.
- command_completed.
- file_write_requested.
- file_write_blocked.
- file_write_completed.
- verification_started.
- verification_passed.
- verification_failed.
- rollback_available.
- rollback_requested.
- rollback_completed.
- workflow_closed_out.

Future implementation may add narrower event names, but it must not remove or weaken these required events.

## Workflow Event Envelope Preview

Future workflow ledger events must include:

- event_id: stable unique event identifier.
- event_type: one of the supported workflow event names.
- workflow_id: stable workflow identifier.
- run_id: stable run identifier.
- step_id: step identifier when applicable.
- action_id: action packet identifier when applicable.
- token_id: approval token identifier when applicable.
- sequence: monotonic sequence within the workflow.
- created_at: timestamp when the event was recorded.
- actor_type: operator, system, or tool.
- actor_id: identifier for the actor.
- status: observed, requested, granted, rejected, blocked, started, paused, resumed, completed, passed, failed, timed_out, cancelled, revoked, or closed_out.
- workflow_status_before: workflow status before the event.
- workflow_status_after: workflow status after the event.
- step_status_before: step status before the event when applicable.
- step_status_after: step status after the event when applicable.
- target_files: files involved in the event when applicable.
- allowed_files: approved file scope when applicable.
- forbidden_files: blocked file scope when applicable.
- command: command involved in the event when applicable.
- head_before: HEAD observed before the event when applicable.
- head_after: HEAD observed after the event when applicable.
- git_status_before: git status snapshot or reference before the event when applicable.
- git_status_after: git status snapshot or reference after the event when applicable.
- retry_count: retry attempt count when applicable.
- timeout_seconds: timeout value when applicable.
- rollback_reference: rollback command, note, or artifact reference when applicable.
- verification_reference: verification command or result reference when applicable.
- reason: human-readable explanation for blocked, rejected, failed, timed-out, cancelled, or revoked events.

Future implementation may add display fields, but it must not rely on display fields as authority.

## Append-Only Rules

No workflow event may be silently rewritten.

No workflow event may be deleted to hide a failed step, blocked step, rejected approval, revoked token, failed verification, timeout, cancellation, rollback, or workflow closeout.

Corrections must be represented as new events that point back to the original event.

Ledger ordering must be stable within a workflow. If ordering cannot be proven, future workflow behavior must fail closed.

## Completion Rules

No future workflow counts as complete without an event trail.

At minimum, a completed future workflow must have:

- workflow_created.
- workflow_dry_run_created.
- workflow_started.
- workflow_step_started for each executed step.
- workflow_step_completed for each completed step.
- verification_started when verification applies.
- verification_passed when verification applies.
- rollback_available when rollback applies.
- workflow_closed_out.

Blocked workflows and failed workflows must also be recorded. A blocked workflow is successful safety behavior, not an invisible non-event.

## Pause Resume And Approval Event Rules

Future approval interruptions must be represented by durable events.

A workflow that pauses for approval must record:

- approval_requested.
- workflow_paused.
- approval_granted or approval_rejected.
- workflow_resumed only after approval_granted when resumption is allowed.

Approval for one step cannot approve future unrelated steps. Resumption must occur from known durable state, not inferred conversation state.

## Cancellation Event Rules

Future cancellation must be durable and visible.

A cancelled workflow must record:

- workflow_cancel_requested.
- workflow_cancelled.
- workflow_closed_out when closeout is allowed.

Cancellation must stop future steps. Cancelled workflows must not continue in the background or retry silently.

## Retry And Timeout Event Rules

Future retries must be bounded, visible, and ledgered.

Retry events must record the retry count, retry reason, policy reference, and step affected.

Timeouts must be ledgered as workflow_step_failed or workflow_step_blocked with timed-out status, followed by workflow_paused, workflow_cancelled, or workflow_closed_out as policy requires.

Unbounded retries and hidden retries remain forbidden.

## Approval Token Relationship

Future approval tokens must be ledger-visible when workflows use them.

A token without matching approval_requested, approval_granted, approval_token_created, and step-scoped event trail is invalid for future live workflow authority.

A ledger event without a valid token must not authorize writes, command execution, rollback, receipt writing, evidence writing, or docs-only apply actions.

## Workflow State Relationship

Workflow state must be derived from durable state and append-only events.

The event ledger may reconstruct state, but reconstructed state must still obey workflow state invariants, approval requirements, file scope, retry policy, timeout policy, cancellation policy, rollback requirements, verification requirements, and lane isolation.

## Fail-Closed Rules

Future workflows must fail closed when:

- event ledger storage is unavailable.
- event ordering cannot be proven.
- event write fails.
- required workflow events are missing.
- required approval events are missing.
- required token events are missing.
- required step events are missing.
- required verification events are missing.
- required rollback events are missing.
- workflow state and event trail disagree.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- approval scope and step scope do not match.
- target files and allowed files do not match.
- forbidden files are touched.
- protected paths are touched.
- Source Proxy stress files are touched.
- `/coding` UI files are touched without a future separate lane.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Ledger Uses

The future workflow ledger must never be used to authorize:

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

Future workflow ledger events may record dirty-state observations, but observation does not authorize mutation.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 12.4: Workflow Dry Run Packet Boundary
- Level 12.5: Pause Resume And Approval Interruption Boundary
- Level 12.6: Cancellation And Timeout Boundary
- Level 12.7: Retry Policy Boundary
- Level 12.8: Workflow Closeout Boundary
- Level 12.9: Level 12 Closeout And Level 13 Gate

Do not implement any of these in Level 12.3.

## Required Future Tests

Future source-code increments must prove:

- no workflow completes without an event trail.
- workflow ledger records workflow_created.
- workflow ledger records workflow_dry_run_created.
- workflow ledger records workflow_started.
- workflow ledger records workflow_paused.
- workflow ledger records workflow_resumed.
- workflow ledger records workflow_cancel_requested.
- workflow ledger records workflow_cancelled.
- workflow ledger records workflow_step_started.
- workflow ledger records workflow_step_blocked.
- workflow ledger records workflow_step_completed.
- workflow ledger records workflow_step_failed.
- workflow ledger records approval events.
- workflow ledger records token events.
- workflow ledger records command events.
- workflow ledger records file write events.
- workflow ledger records verification events.
- workflow ledger records rollback events.
- workflow ledger records workflow_closed_out.
- events are append-only.
- corrections create new events rather than rewriting old events.
- workflow is blocked when ledger storage is unavailable.
- workflow is blocked when required events are missing.
- workflow is blocked when workflow state and event trail disagree.
- workflow is blocked when HEAD changed unexpectedly.
- workflow is blocked when git status changed unexpectedly.
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

git diff --check -- docs/cartographer-level-12-workflow-event-ledger-contract.md

grep -n "Workflow Event Ledger Contract\|Required Workflow Event Names\|Workflow Event Envelope Preview\|Append-Only Rules\|Level 12.4: Workflow Dry Run Packet Boundary" docs/cartographer-level-12-workflow-event-ledger-contract.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-12-workflow-event-ledger-contract.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 12.3 creates the Workflow Event Ledger Contract only.

Expected result:

- no workflow event ledger runtime enabled.
- no workflow state persistence enabled.
- no workflow runner enabled.
- no workflow API enabled.
- no approval interruption runtime enabled.
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

Level 12.4: Workflow Dry Run Packet Boundary
