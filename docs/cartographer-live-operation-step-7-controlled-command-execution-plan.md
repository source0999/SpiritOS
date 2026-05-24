# Cartographer Live Operation Step 7: Controlled Command Execution Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document starts Step 7 as a docs-first plan for future controlled command execution.

Step 7 planning defines how a future command class could be limited to exact approved verification commands. It does not implement command execution, command runners, shell access, queue execution, write authority, live autonomy, limited unattended operation, or full auto.

Limited unattended operation is not granted. Full auto is not granted.

## Scope

Step 7 may plan:

- Exact command allowlist boundaries.
- Verification-only command class boundaries.
- No shell expansion rules.
- Human approval token prerequisites.
- Fail-closed command validation.
- Manual checks before any future implementation.

Step 7 may not implement runtime modules, tests, command runners, shell adapters, queue execution, dashboard UI, package changes, config changes, or `/coding` shell changes.

## Non-Scope

This Step 7 planning pass does not:

- Run commands through Cartographer.
- Implement command execution.
- Execute queue items.
- Write files.
- Write evidence.
- Write receipts.
- Modify app code.
- Modify `/coding` shell or UI files.
- Modify `source_proxy/cartographer` runtime modules.
- Modify `source_proxy/tests`.
- Modify `package.json` or config files.
- Generate approvals.
- Self-approve.
- Create branches or worktrees.
- Commit, push, merge, stash, checkout, clean, or delete.
- Enable limited unattended operation.
- Enable full auto.

## Controlled Command Definition

Future controlled command execution means exact approved verification commands only.

A controlled command is not broad shell access, not task execution, not queue execution, not write authority, not approval generation, and not unattended operation.

No command may run unless a later implementation separately proves exact command matching, approval-token validation, HEAD and dirty-tree checks, protected-lane checks, no shell expansion beyond the approved form, timeout handling, output capture boundaries, and fail-closed behavior.

## Candidate Command Class

The only candidate future command class is approval-bound verification command execution.

Candidate verification commands must be:

- Exact.
- Human-approved.
- Read-only or verification-only.
- Safe with unrelated dirty files present.
- Scoped to the approved write or review.
- Non-mutating unless a later exact package proves otherwise.

Step 7 does not approve or run any command.

## Forbidden Command Classes

Forbidden command classes include:

- Broad shell execution.
- Queue execution.
- Package installation or package mutation.
- Config mutation.
- Environment mutation.
- Branch/worktree creation.
- Commit/push/merge.
- Stash/checkout/clean/delete.
- Destructive filesystem commands.
- Background jobs.
- Recurring jobs.
- Network or deployment commands unless a later exact package separately approves them.
- `/coding` mutation commands.
- Runtime/test mutation commands.
- Commands inferred from recommendation packets, queue records, event records, or silence.

## Manual Checks

After Step 7 planning, manually verify:

- `git diff --check` passes.
- Step 7 docs exist.
- Step 7 says controlled command execution is not implemented now.
- Step 7 says candidate commands are exact approved verification commands only.
- Step 7 blocks broad shell execution, queue execution, package/config/env mutation, branch/worktree creation, git mutation, destructive filesystem commands, background/recurring jobs, `/coding` mutation, runtime/test mutation, and inferred commands.
- Step 7 requires human approval token validation, HEAD and dirty-tree checks, protected-lane checks, no shell expansion, timeout handling, output capture boundaries, and fail-closed behavior before any future implementation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is a docs-only controlled command execution plan.

No runtime code, tests, command runners, command execution, queue execution, write files, evidence files, receipt files, approval generation, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-7-controlled-command-execution-plan.md`

Rollback must not touch `/coding` work, runtime modules, tests, package/config files, branches, worktrees, commits, stashes, generated files, or unrelated dirty files.

## Stop Conditions

Stop immediately if:

- Step 7 runs commands through Cartographer.
- Step 7 implements command execution.
- Step 7 grants broad shell access.
- Step 7 grants queue execution, write authority, self-approval, limited unattended operation, or full auto.
- Step 7 touches `/coding`, runtime, test, package, or config files.

## Next Recommended Increment

Step 7.1: Exact Command Allowlist Contract
