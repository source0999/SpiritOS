# Cartographer Level 12.2 Workflow State Schema Preview

status: schema-preview-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 12.2 defines the future workflow state schema for Durable Workflow Autopilot.

This increment is docs-only. It does not implement workflow persistence, workflow runners, workflow APIs, pause/resume, cancellation, retries, timers, approval interruptions, event ledgers, tests, UI, local execution, writes, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No durable workflow runtime authority, write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 12.1 created the Durable Workflow Autopilot Boundary Contract.

Level 12.2 narrows the next design artifact to workflow state shape only. It does not advance to workflow event ledger implementation, workflow dry-run packets, pause/resume, cancellation, timeout, retry, closeout, or runtime workflow execution.

## Scope

Allowed in this increment:

- create this workflow state schema preview document.
- define future workflow state fields.
- define future workflow step state fields.
- define future workflow status values.
- define future invariants and invalid states.
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

This schema is not workflow authority.

A workflow state object described here is a future control record. It must not be treated as permission to start, resume, retry, cancel, execute, write, verify, rollback, close out, or mutate anything.

Future implementation must prove that workflow state presence does not equal workflow execution authority.

## Workflow State Schema Preview

Future workflow state must include:

- workflow_id: stable unique workflow identifier.
- run_id: stable run identifier.
- workflow_type: exact workflow class.
- workflow_status: current workflow status.
- current_step_id: active step identifier when applicable.
- step_ids: ordered step identifiers.
- step_statuses: status map for each step.
- allowed_files: exact file scope the workflow may inspect or touch.
- forbidden_files: exact file scope the workflow must not touch.
- approval_requirements: approval rules for workflow and steps.
- approval_token_references: approval tokens associated with approved steps.
- event_ledger_references: event ids associated with workflow state transitions.
- retry_policy: bounded retry policy.
- timeout_policy: workflow-level and step-level timeout policy.
- cancellation_policy: rules for stopping future steps.
- pause_resume_policy: rules for approval interruptions and resumed state.
- verification_commands: approved verification command previews.
- rollback_references: rollback notes or rollback packet references.
- created_at: workflow creation timestamp.
- updated_at: last state update timestamp.
- closed_at: closeout timestamp when applicable.

Future implementation may add derived display fields, but display fields must not become authority.

## Workflow Step State Schema Preview

Future workflow step state must include:

- step_id: stable unique step identifier within the workflow.
- workflow_id: parent workflow identifier.
- run_id: parent run identifier.
- step_type: exact step class.
- step_status: current step status.
- depends_on: prior step ids required before this step may start.
- target_files: files the step may inspect or touch.
- allowed_files: exact approved file scope for this step.
- forbidden_files: exact blocked file scope for this step.
- approval_required: boolean approval requirement.
- approval_token_reference: token reference when approved.
- command_preview: exact command when a command is involved.
- write_preview: exact file write when a write is involved.
- verification_reference: verification command or verification result reference.
- rollback_reference: rollback note or rollback packet reference.
- retry_count: attempts used.
- max_attempts: attempts allowed.
- timeout_seconds: step timeout.
- started_at: timestamp when step started.
- completed_at: timestamp when step completed.
- blocked_reason: human-readable reason when blocked.
- failure_reason: human-readable reason when failed.

Step state must be scoped more narrowly than or equal to workflow state.

## Workflow Status Values

Future workflow_status values may include:

- previewed.
- dry_run_created.
- pending_approval.
- approved.
- running.
- paused.
- resumed.
- blocked.
- failed.
- timed_out.
- cancel_requested.
- cancelled.
- completed.
- closed_out.

Level 12.2 does not create lifecycle storage or transitions. These values define future behavior only.

## Step Status Values

Future step_status values may include:

- pending.
- skipped.
- pending_approval.
- approved.
- running.
- paused.
- blocked.
- failed.
- timed_out.
- cancelled.
- completed.
- verified.
- rolled_back.

Step status must not imply authority beyond the exact step approval and scope.

## State Invariants

Future workflow state must satisfy:

- workflow_id is non-empty and stable.
- run_id is non-empty and stable.
- workflow_type is exact and known.
- workflow_status is exact and known.
- current_step_id must be in step_ids when present.
- every step_id has a matching step state.
- step scopes are within workflow allowed_files.
- forbidden_files cannot be overridden by step state.
- approval_token_references cannot broaden allowed_files.
- event_ledger_references must exist for state transitions in future live implementation.
- retry_count cannot exceed max_attempts.
- timeout policy must exist before running.
- cancellation policy must exist before running.
- rollback references must exist before live write or execution steps.
- verification references must exist before live write or execution steps.

If an invariant cannot be proven, future workflow behavior must fail closed.

## Invalid State Rules

Future workflow state is invalid when:

- workflow_id is missing.
- run_id is missing.
- workflow_type is unknown.
- workflow_status is unknown.
- current_step_id is not in step_ids.
- step state is missing.
- allowed_files are missing.
- forbidden_files are missing.
- approval scope and step scope do not match.
- target files exceed allowed_files.
- target files intersect forbidden_files.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- retry policy is missing for retryable workflows.
- timeout policy is missing for executable workflows.
- cancellation policy is missing.
- event ledger references are missing in future live implementation.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Invalid state must block future workflow execution with an honest, visible, explainable result.

## Approval Relationship

Workflow state may reference approvals, but it does not create approvals.

Future approval tokens must remain single-run, single-step or single-action, time-limited, file-scope-bound, and operator-issued. A workflow-level state record must not convert one approval into global permission for later steps.

Approval interruptions must be represented as durable workflow state and append-only ledger events.

## Event Ledger Relationship

Workflow state must be derived from durable state and append-only events, not inferred from chat history.

Future workflow state changes must be ledger-visible. The UI may render workflow state, but the UI is not the source of truth.

No workflow state may be silently rewritten to hide failed, blocked, cancelled, timed-out, or rejected steps.

## Retry Timeout And Cancellation Relationship

Retry policy, timeout policy, and cancellation policy must be explicit before any future live workflow execution.

Retries must be bounded, visible, ledgered, and policy-covered.

Timeouts must stop or pause workflow honestly.

Cancellation must stop future steps and must not allow hidden background continuation.

## Forbidden State Uses

Future workflow state must never authorize:

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

Future workflow state is invalid if git status changes unexpectedly after approval.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 12.3: Workflow Event Ledger Contract
- Level 12.4: Workflow Dry Run Packet Boundary
- Level 12.5: Pause Resume And Approval Interruption Boundary
- Level 12.6: Cancellation And Timeout Boundary
- Level 12.7: Retry Policy Boundary
- Level 12.8: Workflow Closeout Boundary
- Level 12.9: Level 12 Closeout And Level 13 Gate

Do not implement any of these in Level 12.2.

## Required Future Tests

Future source-code increments must prove:

- workflow state does not start a workflow by itself.
- workflow state is blocked when workflow_id is missing.
- workflow state is blocked when run_id is missing.
- workflow state is blocked when workflow_type is unknown.
- workflow state is blocked when workflow_status is unknown.
- workflow state is blocked when current_step_id is invalid.
- workflow state is blocked when step state is missing.
- workflow state is blocked when allowed_files are missing.
- workflow state is blocked when forbidden_files are missing.
- workflow state is blocked when target files exceed allowed_files.
- workflow state is blocked when target files intersect forbidden_files.
- workflow state is blocked when protected paths are in scope.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- workflow state is blocked when retry policy is missing for retryable workflows.
- workflow state is blocked when timeout policy is missing for executable workflows.
- workflow state is blocked when cancellation policy is missing.
- workflow state is blocked when HEAD changed unexpectedly.
- workflow state is blocked when git status changed unexpectedly.
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

git diff --check -- docs/cartographer-level-12-workflow-state-schema-preview.md

grep -n "Workflow State Schema Preview\|Workflow Step State Schema Preview\|State Invariants\|Invalid State Rules\|Level 12.3: Workflow Event Ledger Contract" docs/cartographer-level-12-workflow-state-schema-preview.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-12-workflow-state-schema-preview.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 12.2 creates the Workflow State Schema Preview only.

Expected result:

- no workflow state persistence enabled.
- no workflow runner enabled.
- no workflow API enabled.
- no workflow event ledger runtime enabled.
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

Level 12.3: Workflow Event Ledger Contract
