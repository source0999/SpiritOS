# Cartographer Level 12.4 Workflow Dry Run Packet Boundary

status: dry-run-packet-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 12.4 defines the future workflow dry-run packet boundary for Durable Workflow Autopilot.

This increment is docs-only. It does not create workflow packets at runtime, implement workflow dry runs, implement workflow persistence, implement workflow runners, implement workflow APIs, pause or resume workflows, cancel workflows, retry workflows, execute commands, write files, write receipts, write evidence, add tests, change runtime behavior, create branches, create worktrees, commit, push, merge, clean up, or mutate files outside this document.

Cartographer remains in observe, recommend, preview, and dry-run posture. No workflow runtime authority, write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 12.1 created the Durable Workflow Autopilot Boundary Contract.

Level 12.2 created the Workflow State Schema Preview.

Level 12.3 created the Workflow Event Ledger Contract.

Level 12.4 narrows the next design artifact to workflow dry-run packet shape and safety rules only. It does not advance to pause/resume, cancellation, timeout, retry, closeout, or runtime workflow execution.

## Scope

Allowed in this increment:

- create this workflow dry-run packet boundary document.
- define future workflow dry-run packet fields.
- define future step dry-run packet fields.
- define future eligibility, blocked-result, and proof requirements.
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
- workflow dry-run implementation.
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

This dry-run packet boundary is not workflow authority.

A workflow dry-run packet described here is a future preview object. It must not be treated as permission to start, resume, retry, cancel, execute, write, verify, rollback, close out, or mutate anything.

Future implementation must prove that dry-run eligibility does not equal live workflow approval.

## Workflow Dry Run Packet Definition

A future workflow dry-run packet is a simulated workflow plan for a single workflow run.

It must be:

- workflow-bound.
- run-bound.
- step-bound.
- approval-preview-bound.
- file-scope-preview-bound.
- command-scope-preview-bound when commands are involved.
- rollback-preview-aware.
- verification-preview-aware.
- event-ledger-preview-aware.
- fail-closed by default.

The dry run may say whether a future live workflow appears eligible. It must not perform the workflow.

## Workflow Dry Run Packet Preview

Future workflow dry-run packets must include:

- packet_id: stable dry-run packet identifier.
- workflow_id: stable future workflow identifier.
- run_id: stable run identifier.
- workflow_type: exact future workflow class.
- mode: dry_run.
- proposed_goal: concise future workflow goal.
- step_packets: ordered step dry-run packet references.
- allowed_files: exact future workflow file scope.
- forbidden_files: exact blocked file scope.
- approval_requirements: approval requirements for workflow and steps.
- approval_token_previews: token fields expected before live authority.
- event_ledger_plan: ordered events expected before and after live workflow execution.
- retry_policy_preview: bounded retry rules.
- timeout_policy_preview: workflow and step timeout rules.
- cancellation_policy_preview: cancellation and stop rules.
- pause_resume_policy_preview: approval interruption and resume rules.
- rollback_references: rollback notes or rollback packet previews.
- verification_references: verification command previews.
- head_expected: HEAD value expected before live workflow execution.
- git_status_expected: git status expectation before live workflow execution.
- blocked: boolean dry-run result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Step Dry Run Packet Preview

Future step dry-run packets must include:

- step_packet_id: stable step dry-run packet identifier.
- workflow_id: parent workflow identifier.
- run_id: parent run identifier.
- step_id: stable future step identifier.
- step_type: exact future step class.
- depends_on: prior step ids required before this step may start.
- target_files: files the step may inspect or touch.
- allowed_files: exact approved file scope for this step.
- forbidden_files: exact blocked file scope for this step.
- approval_required: boolean approval requirement.
- approval_token_preview: token fields expected before live step authority.
- command_preview: exact command when a command is involved.
- write_preview: exact file write when a write is involved.
- verification_reference: verification command preview.
- rollback_reference: rollback note or rollback packet preview.
- retry_policy_preview: bounded step retry rules.
- timeout_seconds: step timeout preview.
- event_ledger_plan: ordered step events expected before and after live execution.
- blocked: boolean step dry-run result.
- blocked_reason: human-readable reason when blocked.

Step dry-run packets must be scoped more narrowly than or equal to the workflow dry-run packet.

## Eligibility Rules

A future workflow dry run may be eligible only when:

- workflow_type is exact and known.
- every step_type is exact and known.
- every step is ordered and dependency-safe.
- workflow allowed_files are present.
- workflow forbidden_files are present.
- step scopes are within workflow allowed_files.
- no step target intersects forbidden_files.
- approval requirements are explicit.
- retry policy is bounded.
- timeout policy is bounded.
- cancellation policy is explicit.
- rollback references exist before future live write or execution steps.
- verification references exist before future live write or execution steps.
- expected event ledger plan is complete.
- HEAD expectation is present.
- git status expectation is present.

Eligibility is advisory only. It is not approval for live workflow execution.

## Blocked Result Rules

Future workflow dry runs must return blocked when:

- workflow_type is missing or unknown.
- step_type is missing or unknown.
- step dependencies are invalid.
- allowed_files are missing.
- forbidden_files are missing.
- target files exceed allowed_files.
- target files intersect forbidden_files.
- protected paths are in scope.
- Source Proxy stress files are in scope.
- `/coding` UI files are in scope without a future separate lane.
- approval requirements are missing.
- retry policy is missing or unbounded.
- timeout policy is missing or unbounded.
- cancellation policy is missing.
- rollback references are missing for future live write or execution steps.
- verification references are missing for future live write or execution steps.
- event ledger plan is missing.
- HEAD expectation is missing.
- git status expectation is missing.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Blocked dry runs must explain the blocked reason honestly.

## Approval Relationship

A dry-run packet may preview approval requirements, but it does not create approval.

Future live workflow execution must require explicit operator approval at the workflow and sensitive-step boundaries. Approval for a dry run cannot approve a live workflow.

Approval for one step cannot approve later unrelated steps.

## Event Ledger Relationship

A dry-run packet may preview expected ledger events, but Level 12.4 does not implement ledger storage.

Future workflow dry-run creation must be ledger-visible before live workflow execution exists.

No future workflow counts as complete unless the actual event trail matches the approved workflow and step scopes.

## Retry Timeout And Cancellation Relationship

Workflow dry-run packets must preview retry, timeout, and cancellation policy before live execution is possible.

Retries must be bounded, visible, ledgered, and policy-covered.

Timeouts must stop or pause workflow honestly.

Cancellation must stop future steps and must not allow hidden background continuation.

## Forbidden Dry Run Uses

Future workflow dry-run packets must never authorize:

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

Future workflow dry-run packets must treat unexpected HEAD or git status changes as blocking conditions for live authority.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 12.5: Pause Resume And Approval Interruption Boundary
- Level 12.6: Cancellation And Timeout Boundary
- Level 12.7: Retry Policy Boundary
- Level 12.8: Workflow Closeout Boundary
- Level 12.9: Level 12 Closeout And Level 13 Gate

Do not implement any of these in Level 12.4.

## Required Future Tests

Future source-code increments must prove:

- dry-run packet creation does not start a workflow.
- dry-run packet creation does not write files.
- dry-run packet creation does not execute commands.
- dry-run packet creation does not mutate run history.
- dry run is blocked when workflow_type is missing or unknown.
- dry run is blocked when step_type is missing or unknown.
- dry run is blocked when step dependencies are invalid.
- dry run is blocked when allowed_files are missing.
- dry run is blocked when forbidden_files are missing.
- dry run is blocked when target files exceed allowed_files.
- dry run is blocked when target files intersect forbidden_files.
- dry run is blocked when protected paths are in scope.
- Source Proxy stress files remain blocked.
- `/coding` UI files remain blocked unless explicitly allowed in a future separate lane.
- dry run is blocked when retry policy is missing or unbounded.
- dry run is blocked when timeout policy is missing or unbounded.
- dry run is blocked when cancellation policy is missing.
- dry run is blocked when approval requirements are missing.
- dry run is blocked when rollback references are missing for live write or execution steps.
- dry run is blocked when verification references are missing for live write or execution steps.
- dry run is blocked when event ledger plan is missing.
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

git diff --check -- docs/cartographer-level-12-workflow-dry-run-packet-boundary.md

grep -n "Workflow Dry Run Packet Boundary\|Workflow Dry Run Packet Preview\|Step Dry Run Packet Preview\|Eligibility Rules\|Level 12.5: Pause Resume And Approval Interruption Boundary" docs/cartographer-level-12-workflow-dry-run-packet-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-12-workflow-dry-run-packet-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 12.4 creates the Workflow Dry Run Packet Boundary only.

Expected result:

- no workflow dry-run runtime enabled.
- no workflow packet runtime enabled.
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

Level 12.5: Pause Resume And Approval Interruption Boundary
