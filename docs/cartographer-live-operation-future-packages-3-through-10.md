# Cartographer Live Operation Future Packages 3 Through 10

status: future-package-outline-only

Status date: 2026-05-22

This document groups future Cartographer live-operation work into loose implementation packages. It does not implement any package, enable autonomy, grant full auto, grant limited unattended operation, grant write authority, grant command execution authority, or grant queue execution authority.

## Package A

Title: Cartographer Live Operation Package A: Read-Only Live Mode, Durable Queue/Event Storage, Approval Token Flow

Do not implement package A.

### Step 3: Read-Only Live Mode

Objective:

- Define and implement a future read-only live shadow mode that can inspect exact approved repo state and produce recommendations only.
- Preserve fail-closed behavior for stale HEAD, dirty-tree mismatch, forbidden files, missing approval scope, and kill switch activation.

Likely files:

- Future docs under `docs/`.
- Future Cartographer read-only runtime proposal files under `source_proxy/cartographer/`, only if explicitly approved in that future package.
- Future focused tests under `source_proxy/tests/`, only if explicitly approved in that future package.

Forbidden files:

- `/coding` UI implementation files.
- Source Proxy stress testing files.
- Scout write paths and soak logs.
- proxy memory write paths.
- Codex adapter files.
- verifier files.
- package files.
- Next config.
- environment files.
- secrets.
- generated files.

Manual checks:

- Confirm read-only mode cannot write files, execute commands, execute queue items, select tasks automatically, or approve itself.
- Confirm exact allowed files and exact forbidden files are represented in the policy.
- Confirm kill switch and stale state checks fail closed.

Expected output:

- A read-only live mode plan and runtime proposal.
- Focused proof that the mode observes and recommends only.

Rollback notes:

- Remove the future Step 3 docs and any explicitly approved Step 3 read-only runtime/test files.
- No rollback may rely on stash, checkout, clean, or deleting unrelated files.

Stop conditions:

- Any write behavior appears.
- Any command execution appears.
- Any queue execution appears.
- Any unattended behavior appears.
- Any protected lane is touched.

Next increment title:

- Step 4: Durable Queue And Event Storage Plan

### Step 4: Durable Queue And Event Storage

Objective:

- Define and implement future durable queue and event ledger storage as preview and audit infrastructure only.
- Ensure queued actions cannot execute without a later explicit approval-token flow and operator authorization.

Likely files:

- Future docs under `docs/`.
- Future queue/event model files under `source_proxy/cartographer/`, only if explicitly approved in that future package.
- Future focused tests under `source_proxy/tests/`, only if explicitly approved in that future package.

Forbidden files:

- `/coding` UI implementation files.
- Source Proxy stress testing files.
- Scout write paths and soak logs.
- proxy memory write paths.
- Codex adapter files.
- verifier files.
- package files.
- Next config.
- environment files.
- secrets.
- generated files.

Manual checks:

- Confirm queue storage is inert and cannot execute actions.
- Confirm event storage records previews and decisions without granting authority.
- Confirm queue and ledger state fail closed when approval data is missing or expired.

Expected output:

- A durable queue and event storage plan.
- Future tests proving storage does not imply execution.

Rollback notes:

- Remove the future Step 4 docs and any explicitly approved queue/event model or test files.
- Preserve unrelated repo state and protected lanes.

Stop conditions:

- Queue items can execute.
- Queue items can self-promote.
- Event storage writes to forbidden paths.
- Any approval bypass exists.

Next increment title:

- Step 5: Human Approval Token Flow Plan

### Step 5: Human Approval Token Flow

Objective:

- Define and implement a future approval-token flow that binds operator id, token id, run id, action type, exact allowed files, exact forbidden files, expiry, rollback, verification, HEAD, dirty-tree expectation, and trust tier.
- Ensure approvals cannot be created or accepted by self-approval.

Likely files:

- Future docs under `docs/`.
- Future approval-token runtime files under `source_proxy/cartographer/`, only if explicitly approved in that future package.
- Future focused tests under `source_proxy/tests/`, only if explicitly approved in that future package.

Forbidden files:

- `/coding` UI implementation files.
- Source Proxy stress testing files.
- Scout write paths and soak logs.
- proxy memory write paths.
- Codex adapter files.
- verifier files.
- package files.
- Next config.
- environment files.
- secrets.
- generated files.

Manual checks:

- Confirm missing token fields fail closed.
- Confirm expired tokens fail closed.
- Confirm stale HEAD and dirty-tree mismatch fail closed.
- Confirm self-approval fails closed.

Expected output:

- A human approval token flow plan.
- Future tests proving token validation blocks ambiguous, stale, expired, or self-approved actions.

Rollback notes:

- Remove the future Step 5 docs and any explicitly approved approval-token model or test files.
- Do not mutate unrelated runtime, UI, package, config, or generated files.

Stop conditions:

- Token validation allows missing fields.
- Self-approval is possible.
- Expired approval is accepted.
- Forbidden paths are not enforced.

Next increment title:

- Step 6: First Safe Write Class Plan

## Package B

Title: Cartographer Live Operation Package B: First Safe Write Class, Controlled Command Execution, Operator Dashboard Controls

Do not implement package B.

### Step 6: First Safe Write Class

Objective:

- Define the first future safe write class, likely approval-bound docs/evidence/receipt writes only.
- Require exact allowed files, exact forbidden files, rollback, verification, token validation, and fail-closed behavior.

Likely files:

- Future docs under `docs/`.
- Future narrow write-class runtime files under `source_proxy/cartographer/`, only if explicitly approved in that future package.
- Future focused tests under `source_proxy/tests/`, only if explicitly approved in that future package.

Forbidden files:

- app code files.
- `/coding` UI implementation files.
- Source Proxy stress testing files.
- Scout write paths and soak logs.
- proxy memory write paths.
- Codex adapter files.
- verifier files.
- package files.
- Next config.
- environment files.
- secrets.
- generated files.

Manual checks:

- Confirm the first write class cannot modify app code.
- Confirm writes are limited to exact approved docs/evidence/receipt files.
- Confirm rollback is concrete and manual-verifiable.

Expected output:

- A first safe write class plan and proof proposal.
- Future tests proving forbidden paths and unapproved files are blocked.

Rollback notes:

- Remove the future Step 6 docs and any explicitly approved Step 6 runtime/test files.
- Revert only exact future Step 6 files through normal operator review.

Stop conditions:

- App code writes are possible.
- `/coding` UI mutation is possible.
- Approval scope is broad or ambiguous.
- Rollback is missing.

Next increment title:

- Step 7: Controlled Command Execution Plan

### Step 7: Controlled Command Execution

Objective:

- Define future controlled verification command execution for exact approved commands only.
- Keep command execution approval-bound, narrow, auditable, and separate from queue execution or unattended operation.

Likely files:

- Future docs under `docs/`.
- Future command-policy runtime files under `source_proxy/cartographer/`, only if explicitly approved in that future package.
- Future focused tests under `source_proxy/tests/`, only if explicitly approved in that future package.

Forbidden files:

- `/coding` UI implementation files.
- Source Proxy stress testing files.
- Scout write paths and soak logs.
- proxy memory write paths.
- Codex adapter files.
- verifier files.
- package files.
- Next config.
- environment files.
- secrets.
- generated files.

Manual checks:

- Confirm only exact approved verification commands can run.
- Confirm shell expansion, arbitrary arguments, and command composition are blocked unless explicitly approved.
- Confirm command execution cannot stage, commit, push, merge, stash, checkout, clean, delete, branch, or create worktrees.

Expected output:

- A controlled command execution plan.
- Future tests proving unapproved commands and destructive git commands are blocked.

Rollback notes:

- Remove the future Step 7 docs and any explicitly approved command-policy runtime/test files.
- Do not use command execution as its own rollback mechanism.

Stop conditions:

- Broad shell access appears.
- Destructive git commands are permitted.
- Command execution can run without an approval token.
- Command execution can run while kill switch is active.

Next increment title:

- Step 8: Dashboard And Operator Controls Plan

### Step 8: Dashboard/Operator Controls

Objective:

- Define future dashboard/operator controls for viewing mode, trust tier, queue previews, approval status, kill switch state, and stop conditions.
- Keep controls observational and approval-bound; dashboard visibility must not imply authority.

Likely files:

- Future docs under `docs/`.
- Future dashboard/operator-control files only if explicitly approved in that future package.
- Future focused tests only if explicitly approved in that future package.

Forbidden files:

- Existing `/coding` UI implementation files unless a future package explicitly names exact files and approval boundaries.
- Source Proxy stress testing files.
- Scout write paths and soak logs.
- proxy memory write paths.
- Codex adapter files.
- verifier files.
- package files.
- Next config.
- environment files.
- secrets.
- generated files.

Manual checks:

- Confirm dashboard controls cannot silently grant authority.
- Confirm kill switch status is visible and enforced.
- Confirm approval, expiry, HEAD, dirty-tree, and forbidden-path failures are visible to the operator.

Expected output:

- A dashboard/operator controls plan.
- Future tests or manual checks proving controls show state accurately and do not bypass approval.

Rollback notes:

- Remove the future Step 8 docs and any explicitly approved dashboard/operator-control files.
- Keep `/coding` UI and other protected lanes separate unless future approval explicitly says otherwise.

Stop conditions:

- Dashboard controls mutate protected lanes.
- Dashboard controls approve actions implicitly.
- Dashboard controls hide kill switch, expiry, stale HEAD, or dirty-tree mismatch.

Next increment title:

- Step 9: 24 To 72 Hour Live Shadow Soak Plan

## Package C

Title: Cartographer Live Operation Package C: Live Shadow Soak And Limited Unattended Mode

Do not implement package C.

### Step 9: 24 To 72 Hour Live Shadow Soak

Objective:

- Define a future 24 to 72 hour live shadow soak for read-only or tightly approval-bound behavior before any limited unattended mode is considered.
- Measure stability, blocked actions, kill switch behavior, stale state handling, dirty-tree mismatch handling, and operator review quality.

Likely files:

- Future docs under `docs/`.
- Future soak reporting files only if explicitly approved in that future package.
- Future focused tests or checks only if explicitly approved in that future package.

Forbidden files:

- `/coding` UI implementation files.
- Source Proxy stress testing files unless explicitly approved as read-only references.
- Scout write paths and soak logs unless explicitly approved as read-only references.
- proxy memory write paths.
- Codex adapter files.
- verifier files.
- package files.
- Next config.
- environment files.
- secrets.
- generated files.

Manual checks:

- Confirm soak is live shadow, not unattended execution.
- Confirm all blocked action classes remain blocked.
- Confirm operator review happens at defined intervals.
- Confirm kill switch behavior is exercised and documented.

Expected output:

- A live shadow soak plan.
- Future soak result summary after explicit execution approval.

Rollback notes:

- Remove the future Step 9 docs and any explicitly approved soak reporting files.
- Stop any future soak mechanism through the approved kill switch before removal.

Stop conditions:

- Any unattended write or command execution occurs.
- Any queue item executes without approval.
- Any protected lane is touched.
- Kill switch fails to block.

Next increment title:

- Step 10: Limited Unattended Mode Plan

### Step 10: Limited Unattended Mode

Objective:

- Define a future limited unattended mode only after earlier packages implement and prove read-only live mode, durable queue/event storage, approval tokens, first safe write class, controlled command execution, dashboard controls, and a successful live shadow soak.
- Keep scope low-risk, explicit, reversible, observable, and kill-switch controlled.

Likely files:

- Future docs under `docs/`.
- Future limited-unattended policy/runtime files under `source_proxy/cartographer/`, only if explicitly approved in that future package.
- Future focused tests under `source_proxy/tests/`, only if explicitly approved in that future package.

Forbidden files:

- `/coding` UI implementation files unless exact future approval explicitly names the files.
- Source Proxy stress testing mutation.
- Scout writes.
- proxy memory writes unless a future explicit package separately authorizes exact files.
- branch/worktree creation.
- commit/push/merge.
- cleanup/delete/stash/checkout.
- secret/protected path access.
- automatic promotion.
- self-approval.
- package files.
- Next config.
- environment files.
- secrets.
- generated files.

Manual checks:

- Confirm the preceding live shadow soak passed.
- Confirm allowed unattended actions are low-risk, exact, reversible, and time-limited.
- Confirm kill switch blocks immediately.
- Confirm operator review cadence is defined.
- Confirm rollback and verification are mandatory.
- Confirm full auto remains not granted.

Expected output:

- A limited unattended mode plan and proof proposal.
- Future proof that limited unattended behavior cannot expand its own authority.

Rollback notes:

- Remove the future Step 10 docs and any explicitly approved limited-unattended runtime/test files.
- Disable any future unattended mechanism through the kill switch before file removal.
- Do not use stash, checkout, clean, branch deletion, or unrelated file cleanup as rollback.

Stop conditions:

- Full auto is requested or implied.
- Limited unattended scope is broad, irreversible, or self-expanding.
- Self-approval is possible.
- Automatic promotion is possible.
- Protected lanes can be touched.
- Kill switch does not fail closed.

Next increment title:

- Future Closeout: Limited Autonomous Operator v0.1 Review Gate
