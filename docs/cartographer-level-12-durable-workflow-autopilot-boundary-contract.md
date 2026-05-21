# Cartographer Level 12 Durable Workflow Autopilot Boundary Contract

status: planning-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 12.1 defines the boundary contract for future Durable Workflow Autopilot.

This increment is docs-only. It does not implement durable workflows, workflow runs, pause/resume, cancellation, retries, timers, approval interruptions, persistence, API routes, service builders, tests, UI, local execution, writes, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture until future increments explicitly unlock scoped workflow behavior.

## Starting Point

Level 11.9 closed the Level 11 Controlled Action Authority planning sequence and locked the Level 12 gate.

The operator has explicitly requested the next increment after Level 11.9. That request opens Level 12.1 planning only. It does not authorize Level 12 implementation, durable workflow runtime behavior, action authority, local execution, receipt writing, evidence writing, docs-only apply actions, rollback execution, Source Proxy stress-lane work, `/coding` UI work, Scout work, proxy memory writes, blueprint writes, branch creation, worktree creation, commit, push, merge, or cleanup.

## Scope

This contract defines what Level 12 may eventually implement, what remains forbidden, and what proof is required before durable workflow autopilot can be added.

Allowed in this increment:

- create this Level 12.1 boundary contract document.
- define future durable workflow concepts.
- define future workflow state and ledger requirements.
- define future pause, resume, cancel, retry, timeout, and approval interruption rules.
- define future implementation and test expectations.
- run doc-only verification commands.
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
- durable workflow implementation.
- workflow persistence implementation.
- workflow runner implementation.
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

## Non-Negotiable Boundary

Level 12.1 grants no workflow authority. It is a planning boundary only.

Future Level 12 workflow behavior must be unlocked by exact increment, exact workflow type, exact step type, exact file scope, explicit operator approval, focused tests, manual checks, rollback metadata, verification requirements, durable event trail, and fail-closed policy.

No roadmap, previous approval, passing check, Level 11 closeout, UI affordance, operator trust, successful dry run, or generated planning document may be interpreted as workflow execution authority.

## Durable Workflow Autopilot Definition

Durable Workflow Autopilot is future workflow coordination that is:

- run-bound.
- step-bound.
- approval-interruptible.
- pauseable.
- resumable.
- cancellable.
- retry-bounded.
- timeout-bounded.
- event-ledger-recorded.
- rollback-aware.
- verification-aware.
- fail-closed by default.

Durable Workflow Autopilot never means broad autonomy, hidden background execution, unbounded loops, automatic promotion, self-approval, branch/worktree authority, commit/push/merge authority, or cross-lane mutation.

## Workflow Authority Placement

Level 12 may design the path from isolated approved actions toward durable workflow runs.

Level 12 does not automatically add new write authority. It may eventually coordinate only action classes that were separately approved, scoped, ledgered, verified, and rollback-aware.

Level 12.1 grants no workflow execution authority, no write authority, and no local execution authority.

## Workflow State Requirements

Future durable workflow state must include:

- workflow_id.
- run_id.
- workflow_type.
- workflow_status.
- current_step_id.
- step_ids.
- step_statuses.
- allowed_files.
- forbidden_files.
- approval_requirements.
- approval_token_references.
- event_ledger_references.
- retry_policy.
- timeout_policy.
- cancellation_policy.
- pause_resume_policy.
- verification_commands.
- rollback_references.
- created_at.
- updated_at.
- closed_at.

Workflow state must be derived from durable state and append-only events, not inferred from chat history.

## Required Future Workflow Controls

Future Level 12 workflow controls must include:

- workflow dry run before live workflow.
- explicit approval interruption before sensitive steps.
- visible paused state.
- visible resumed state.
- visible cancelled state.
- bounded retry policy.
- bounded timeout policy.
- step-level failure reporting.
- step-level rollback references.
- step-level verification requirements.
- durable closeout state.

If any control is missing, future workflow execution must fail closed.

## Allowed Future Level 12 Workflow Classes

The following are future possible workflow classes only:

1. approved docs-only maintenance workflow.
2. approved receipt and evidence closeout workflow.
3. approved verification-only workflow.
4. approved rollback-aware closeout workflow.
5. approved metadata-only workflow packet.
6. approved paused approval-interruption workflow.
7. approved cancelled workflow closeout.

Each workflow class requires a future focused implementation increment and focused tests. None are implemented by Level 12.1.

## Forbidden Workflow Behavior

The following remain forbidden:

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

## Approval Interruption Requirements

Future workflows must pause for explicit operator approval before any sensitive step.

Sensitive steps include:

- file writes.
- receipt writes.
- evidence writes.
- docs-only apply actions.
- local verification command execution.
- rollback command execution.
- closeout receipt writing.
- any step touching protected or lane-sensitive paths.

Approval interruptions must be durable events. A workflow may resume only from known durable state after approval or rejection.

Approval for one step cannot approve future unrelated steps.

## Event Ledger Requirements

Future durable workflows must use the append-only event ledger as the source of truth.

Future workflow events must include at least:

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

No workflow event may be silently rewritten. No workflow counts as complete without an event trail. The UI may render workflow state, but the UI is not the source of truth.

Future implementation must prove no hidden mutation occurred.

## Retry And Timeout Rules

Future retries must be bounded, visible, ledgered, and covered by policy.

Retries are forbidden when:

- max attempts is missing.
- retry reason is missing.
- approval is expired or revoked.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- forbidden files are touched.
- protected paths are touched.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Future timeouts must be explicit per workflow and per step. Timed-out workflows must stop future steps unless a future explicit approval resumes from known durable state.

## Cancel And Stop Rules

Future cancellation must stop future workflow steps.

A cancelled workflow must not continue in the background, retry silently, promote itself, write closeout artifacts, or execute rollback unless a separate explicit approved rollback action exists.

Cancellation must be ledgered and visible.

## Fail-Closed Rules

Future workflows must fail closed when:

- workflow state is missing.
- event ledger storage is unavailable.
- workflow ordering cannot be proven.
- approval is absent.
- approval is expired or revoked.
- approval scope and step scope do not match.
- allowed files do not match target files.
- forbidden files are touched.
- protected paths are touched.
- Source Proxy stress files are touched.
- `/coding` UI files are touched without a future separate lane.
- HEAD changed unexpectedly.
- git status changed unexpectedly.
- retry policy is missing.
- timeout policy is missing.
- cancellation policy is missing.
- rollback metadata is missing when required.
- verification metadata is missing when required.
- lane ownership is ambiguous.
- hidden mutation is suspected.

Failure must be honest, visible, and explainable.

## Dirty Worktree And Lane Isolation Rules

Cartographer may observe dirty worktree state and report it as unrelated pre-existing state.

Observation does not authorize cleanup, stash, checkout, overwrite, branch creation, worktree creation, commit, push, merge, or mutation of those files.

Dirty files in Source Proxy stress testing, `/coding` UI, source code, tests, package files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, or dashboard lanes must remain untouched unless a separate explicit future lane authorizes them.

Cross-lane mutation is blocked by default.

## Required Future Implementation Shape

Future Level 12 implementation must proceed in small increments.

A conservative future path may include:

- Level 12.2: Workflow State Schema Preview
- Level 12.3: Workflow Event Ledger Contract
- Level 12.4: Workflow Dry Run Packet Boundary
- Level 12.5: Pause Resume And Approval Interruption Boundary
- Level 12.6: Cancellation And Timeout Boundary
- Level 12.7: Retry Policy Boundary
- Level 12.8: Workflow Closeout Boundary
- Level 12.9: Level 12 Closeout And Level 13 Gate

Do not implement any of these in Level 12.1.

## Required Future Tests

Future source-code increments must test both allowed and forbidden behavior.

Future tests must prove:

- workflow is blocked without explicit approval.
- workflow step is blocked without step approval.
- workflow is blocked with expired approval.
- workflow is blocked with revoked approval.
- workflow is blocked when allowed_files mismatch.
- workflow is blocked when forbidden_files match.
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
- cancellation stops future steps.
- retries are bounded and ledgered.
- timeouts stop or pause workflow honestly.
- approval interruptions are durable.
- rollback metadata exists before live action.
- verification metadata exists before live action.
- event ledger records every workflow step.
- failures are honest and explainable.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-12-durable-workflow-autopilot-boundary-contract.md

grep -n "Durable Workflow Autopilot Boundary Contract\|Workflow State Requirements\|Required Future Workflow Controls\|Approval Interruption Requirements\|Level 12.2: Workflow State Schema Preview" docs/cartographer-level-12-durable-workflow-autopilot-boundary-contract.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-12-durable-workflow-autopilot-boundary-contract.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 12.1 creates the Durable Workflow Autopilot Boundary Contract only.

Expected result:

- no durable workflow implementation enabled.
- no workflow runner enabled.
- no workflow persistence enabled.
- no approval interruption runtime enabled.
- no retry runtime enabled.
- no timeout runtime enabled.
- no cancellation runtime enabled.
- no approval token runtime authority enabled.
- no event ledger runtime authority enabled.
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

Level 12.2: Workflow State Schema Preview
