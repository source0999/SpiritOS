# Cartographer Level 12.6 Cancellation And Timeout Boundary

status: cancellation-timeout-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 12.6 defines the future boundary for workflow cancellation and timeout behavior.

This increment is docs-only. It does not implement cancellation runtime behavior, timeout runtime behavior, timers, workflow persistence, workflow runners, workflow APIs, approval tokens, event ledgers, tests, UI, local execution, writes, receipts, evidence, branches, worktrees, commits, pushes, merges, cleanup, or background mutation.

Cartographer remains in observe, recommend, preview, and dry-run posture. No workflow runtime authority, cancellation runtime authority, timeout runtime authority, write authority, local execution authority, branch/worktree authority, commit/push/merge authority, automatic execution, automatic promotion, or self-approval is enabled.

## Starting Point

Level 12.1 created the Durable Workflow Autopilot Boundary Contract.

Level 12.2 created the Workflow State Schema Preview.

Level 12.3 created the Workflow Event Ledger Contract.

Level 12.4 created the Workflow Dry Run Packet Boundary.

Level 12.5 created the Pause Resume And Approval Interruption Boundary.

Level 12.6 narrows the next design artifact to cancellation and timeout rules only. It does not advance to retry policy, workflow closeout, or runtime workflow execution.

## Scope

Allowed in this increment:

- create this cancellation and timeout boundary document.
- define future cancellation packet fields.
- define future timeout packet fields.
- define future stop, closeout, and blocked continuation rules.
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
- cancellation implementation.
- timeout implementation.
- timer implementation.
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

Future cancellation and timeout behavior may stop, block, or close out workflows according to explicit policy. It must not start workflows, resume workflows, retry workflows, execute rollback, write closeout artifacts, mutate files, or choose alternate work without separate approval.

Level 12.6 does not create runtime cancellation, timeout, timer, or workflow stop behavior.

## Cancellation Definition

A future workflow cancellation is a durable request and outcome that stops future workflow steps.

Cancellation must be:

- workflow-bound.
- run-bound.
- reason-bound.
- operator-visible.
- event-ledger-recorded.
- stop-enforcing.
- closeout-aware.
- fail-closed by default.

Cancelled workflows must not continue in the background, retry silently, promote themselves, write artifacts, execute commands, execute rollback, or mutate files.

## Timeout Definition

A future workflow timeout is a bounded time policy that stops or pauses a workflow or step when time expires.

Timeout must be:

- workflow-bound.
- step-bound when applied to a step.
- duration-bound.
- reason-bound.
- event-ledger-recorded.
- stop-or-pause-enforcing.
- closeout-aware.
- fail-closed by default.

Timed-out workflows must not continue in the background, retry silently, promote themselves, write artifacts, execute commands, execute rollback, or mutate files unless a future explicit policy and approval allow a next step.

## Cancellation Packet Preview

Future cancellation packets must include:

- cancellation_id: stable cancellation identifier.
- workflow_id: stable workflow identifier.
- run_id: stable run identifier.
- requested_by: operator or system actor id.
- requested_at: cancellation request timestamp.
- cancellation_reason: human-readable cancellation reason.
- current_step_id: active step when cancellation was requested.
- workflow_status_before: workflow status before cancellation.
- step_statuses_before: step statuses before cancellation.
- allowed_files: exact workflow file scope.
- forbidden_files: exact blocked file scope.
- stop_future_steps: boolean that must be true.
- closeout_policy: allowed closeout behavior after cancellation.
- rollback_policy: rollback behavior, blocked unless separately approved.
- event_ledger_plan: required cancellation events.
- head_expected: HEAD value expected at cancellation.
- git_status_expected: git status expectation at cancellation.
- blocked: boolean cancellation result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Timeout Packet Preview

Future timeout packets must include:

- timeout_id: stable timeout identifier.
- workflow_id: stable workflow identifier.
- run_id: stable run identifier.
- step_id: step identifier when timeout is step-scoped.
- timeout_scope: workflow or step.
- timeout_seconds: approved timeout duration.
- timeout_started_at: timestamp when timeout began.
- timeout_expires_at: timestamp when timeout expires.
- timeout_reason: human-readable timeout reason.
- workflow_status_before: workflow status before timeout outcome.
- step_status_before: step status before timeout outcome when applicable.
- timeout_outcome: pause, block, cancel, or closeout.
- allowed_files: exact workflow file scope.
- forbidden_files: exact blocked file scope.
- event_ledger_plan: required timeout events.
- head_expected: HEAD value expected at timeout.
- git_status_expected: git status expectation at timeout.
- blocked: boolean timeout result.
- blocked_reason: human-readable reason when blocked.

Future implementation may add display fields, but display fields must not become authority.

## Stop Rules

Future cancellation must stop future steps.

Future timeout must stop, pause, block, cancel, or close out according to explicit timeout policy.

After cancellation or timeout:

- no new step may start unless policy and approval explicitly allow it.
- no hidden retry may occur.
- no automatic promotion may occur.
- no rollback may execute without separate explicit approval.
- no receipt, evidence, or closeout artifact may be written without separate explicit approval.
- no cleanup may occur.

## Closeout Relationship

Cancellation and timeout may require future closeout state, but they do not authorize closeout writes by themselves.

Future cancellation or timeout closeout must be ledgered, visible, and bounded to the workflow. It must not delete evidence, receipts, run history, branches, worktrees, dirty worktree changes, or unrelated files.

## Event Ledger Requirements

Future cancellation and timeout behavior must be ledger-visible.

Expected future cancellation event trail:

- workflow_cancel_requested.
- workflow_cancelled.
- workflow_closed_out when closeout is allowed.

Expected future timeout event trail:

- workflow_step_failed or workflow_step_blocked when step-scoped.
- workflow_paused, workflow_cancelled, or workflow_closed_out according to policy.
- verification_failed when timeout affects verification.
- workflow_closed_out when closeout is allowed.

Level 12.6 does not implement ledger storage or emit runtime ledger events.

## Fail-Closed Rules

Future cancellation and timeout behavior must fail closed when:

- workflow state is missing.
- cancellation packet is missing when cancellation is requested.
- timeout packet is missing when timeout is evaluated.
- cancellation policy is missing.
- timeout policy is missing.
- stop_future_steps is not true for cancellation.
- timeout outcome is missing or unknown.
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

## Forbidden Cancellation Timeout Uses

Future cancellation and timeout behavior must never authorize:

- automatic execution without approval.
- global approval.
- self-approval.
- hidden background workflows.
- hidden retries.
- unbounded loops.
- autonomous task selection.
- automatic promotion.
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

Future cancellation and timeout must treat unexpected HEAD or git status changes as blocking conditions for any later resume, retry, rollback, or closeout.

Source Proxy stress files, `/coding` UI files, source code, tests, package files, API routes, service builders, runtime files, Scout implementation, proxy memory, blueprint, safety, verification, Codex adapter, and dashboard lanes remain blocked unless a separate explicit future lane authorizes them.

## Required Future Implementation Shape

Future implementation must remain incremental:

- Level 12.7: Retry Policy Boundary
- Level 12.8: Workflow Closeout Boundary
- Level 12.9: Level 12 Closeout And Level 13 Gate

Do not implement any of these in Level 12.6.

## Required Future Tests

Future source-code increments must prove:

- cancellation stops future steps.
- cancelled workflow does not continue in the background.
- cancelled workflow does not retry silently.
- cancellation does not execute rollback without separate approval.
- cancellation does not write closeout artifacts without separate approval.
- cancellation does not clean up files.
- timeout stops, pauses, blocks, cancels, or closes out according to explicit policy.
- timed-out workflow does not continue in the background.
- timed-out workflow does not retry silently.
- timeout does not execute rollback without separate approval.
- timeout does not write closeout artifacts without separate approval.
- missing cancellation policy blocks cancellation handling.
- missing timeout policy blocks timeout handling.
- unknown timeout outcome blocks timeout handling.
- event ledger records workflow_cancel_requested and workflow_cancelled.
- event ledger records timeout outcomes.
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

git diff --check -- docs/cartographer-level-12-cancellation-and-timeout-boundary.md

grep -n "Cancellation And Timeout Boundary\|Cancellation Packet Preview\|Timeout Packet Preview\|Stop Rules\|Level 12.7: Retry Policy Boundary" docs/cartographer-level-12-cancellation-and-timeout-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-12-cancellation-and-timeout-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 12.6 creates the Cancellation And Timeout Boundary only.

Expected result:

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
- no retry runtime enabled.
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

Level 12.7: Retry Policy Boundary
