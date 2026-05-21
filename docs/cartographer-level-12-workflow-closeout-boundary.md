# Cartographer Level 12.8 Workflow Closeout Boundary

status: workflow-closeout-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 12.8 defines the future boundary for workflow closeout in Durable Workflow Autopilot.

This increment is docs-only. It does not implement workflow closeout runtime behavior, closeout receipt writing, workflow persistence, workflow runners, workflow APIs, approval tokens, event ledgers, tests, UI, local execution, writes, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No workflow runtime authority, closeout runtime authority, write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 12.1 created the Durable Workflow Autopilot Boundary Contract.

Level 12.2 created the Workflow State Schema Preview.

Level 12.3 created the Workflow Event Ledger Contract.

Level 12.4 created the Workflow Dry Run Packet Boundary.

Level 12.5 created the Pause Resume And Approval Interruption Boundary.

Level 12.6 created the Cancellation And Timeout Boundary.

Level 12.7 created the Retry Policy Boundary.

Level 12.8 narrows the next design artifact to workflow closeout rules only. It does not advance to Level 12 closeout gate or runtime workflow execution.

## Scope

Allowed in this increment:

- create this workflow closeout boundary document.
- define future workflow closeout packet fields.
- define future completed, blocked, failed, cancelled, and timed-out closeout rules.
- define future closeout ledger requirements.
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
- workflow closeout implementation.
- closeout receipt writing.
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

This boundary is not workflow closeout authority.

Future workflow closeout may summarize a workflow state and stop future steps. It must not write closeout artifacts, execute rollback, mutate files, clean up, commit, push, merge, delete evidence, delete receipts, delete run history, or choose alternate work without separate approval.

Level 12.8 does not create runtime closeout behavior.

## Workflow Closeout Definition

A future workflow closeout is a durable terminal or review state for one workflow.

Workflow closeout must be:

- workflow-bound.
- run-bound.
- status-bound.
- evidence-aware.
- rollback-aware.
- verification-aware.
- event-ledger-recorded.
- stop-enforcing.
- fail-closed by default.

Closed-out workflows must not continue in the background, retry silently, promote themselves, write artifacts, execute commands, execute rollback, or mutate files.

## Closeout Packet Preview

Future workflow closeout packets must include:

- closeout_id: stable closeout identifier.
- workflow_id: stable workflow identifier.
- run_id: stable run identifier.
- workflow_type: exact workflow class.
- closeout_status: completed, blocked, failed, cancelled, timed_out, or review_required.
- closeout_reason: human-readable closeout reason.
- final_step_id: final active or completed step.
- step_statuses: final step status map.
- completed_steps: completed step ids.
- blocked_steps: blocked step ids.
- failed_steps: failed step ids.
- cancelled_steps: cancelled step ids when applicable.
- timed_out_steps: timed-out step ids when applicable.
- allowed_files: exact workflow file scope.
- forbidden_files: exact blocked file scope.
- approval_references: approvals used or rejected.
- event_ledger_references: events required to prove closeout.
- verification_summary: verification result summary.
- rollback_summary: rollback availability summary.
- evidence_summary: evidence reference summary without writing new evidence.
- receipt_summary: receipt reference summary without writing new receipts.
- head_expected: HEAD value expected at closeout.
- git_status_expected: git status expectation at closeout.
- blocked: boolean closeout result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Completed Closeout Rules

Future completed workflow closeout may be eligible only when:

- all required steps are completed.
- required verification passed.
- required rollback references exist.
- required event ledger trail exists.
- no forbidden files were touched.
- protected paths remained blocked.
- Source Proxy stress files remained blocked.
- `/coding` UI files remained blocked unless explicitly allowed in a future separate lane.
- HEAD and git status expectations are satisfied or explicitly explained.

Completed closeout must not write a closeout receipt unless a separate approved closeout receipt action exists.

## Blocked Failed Cancelled Timeout Closeout Rules

Future non-completed closeout must preserve honest state.

Blocked, failed, cancelled, and timed-out workflows must record:

- final status.
- honest reason.
- last known step.
- event ledger references.
- approval state.
- verification state.
- rollback availability.
- whether future operator action is required.

Non-completed closeout must not hide failure, retry silently, promote itself, execute rollback, write artifacts, or clean up files.

## Event Ledger Requirements

Future workflow closeout must be ledger-visible.

Expected future closeout event trail:

- workflow_created.
- workflow_started or workflow_dry_run_created when applicable.
- workflow_step_completed, workflow_step_blocked, workflow_step_failed, workflow_cancelled, or timeout event according to outcome.
- verification_passed or verification_failed when verification applies.
- rollback_available when rollback applies.
- workflow_closed_out.

Level 12.8 does not implement ledger storage or emit runtime ledger events.

## Closeout Receipt Relationship

Workflow closeout and closeout receipt writing are separate authority classes.

Future workflow closeout may produce a closeout packet or state summary. It must not write a receipt file unless a separate explicit approved closeout receipt write authority exists.

Deletion of evidence, receipts, or run history remains forbidden.

## Fail-Closed Rules

Future workflow closeout must fail closed when:

- workflow state is missing.
- closeout packet is missing.
- closeout status is missing or unknown.
- closeout reason is missing.
- event ledger references are missing.
- workflow state and event trail disagree.
- required verification state is missing.
- required rollback state is missing.
- forbidden files are touched.
- protected paths are touched.
- Source Proxy stress files are touched.
- `/coding` UI files are touched without a future separate lane.
- closeout receipt would be written without separate approval.
- evidence would be written without separate approval.
- receipt would be written without separate approval.
- rollback would execute without separate approval.
- cleanup would occur.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Forbidden Closeout Uses

Future workflow closeout must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- hidden background workflows.
- hidden retries.
- unbounded loops.
- autonomous task selection.
- automatic promotion.
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

Future closeout must treat unexpected HEAD or git status changes as blocking conditions for closeout eligibility.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 12.9: Level 12 Closeout And Level 13 Gate

Do not implement Level 12.9 in Level 12.8.

## Required Future Tests

Future source-code increments must prove:

- closeout is blocked when workflow state is missing.
- closeout is blocked when closeout packet is missing.
- closeout is blocked when closeout status is missing or unknown.
- closeout is blocked when closeout reason is missing.
- closeout is blocked when event ledger references are missing.
- closeout is blocked when workflow state and event trail disagree.
- completed closeout requires completed required steps.
- completed closeout requires verification passed when verification applies.
- completed closeout requires rollback references when rollback applies.
- blocked, failed, cancelled, and timed-out closeouts preserve honest status.
- closeout does not retry workflow.
- closeout does not execute rollback without separate approval.
- closeout does not write closeout receipt without separate approval.
- closeout does not write evidence or receipts without separate approval.
- closeout does not clean up files.
- closeout is blocked when HEAD changed unexpectedly.
- closeout is blocked when git status changed unexpectedly.
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

git diff --check -- docs/cartographer-level-12-workflow-closeout-boundary.md

grep -n "Workflow Closeout Boundary\|Closeout Packet Preview\|Completed Closeout Rules\|Closeout Receipt Relationship\|Level 12.9: Level 12 Closeout And Level 13 Gate" docs/cartographer-level-12-workflow-closeout-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-12-workflow-closeout-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 12.8 creates the Workflow Closeout Boundary only.

Expected result:

- no workflow closeout runtime enabled.
- no closeout receipt writing enabled.
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

Level 12.9: Level 12 Closeout And Level 13 Gate
