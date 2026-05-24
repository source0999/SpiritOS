# Cartographer Live Operation Step 6: First Safe Write Class Plan

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document starts Step 6 as a docs-first plan for the first future safe write class.

Step 6 planning defines the narrowest possible future write class, likely approval-bound documentation/evidence/receipt writes only. It does not implement write authority, write runtime code, evidence writers, receipt writers, command execution, queue execution, live autonomy, limited unattended operation, or full auto.

Limited unattended operation is not granted. Full auto is not granted.

## Scope

Step 6 may plan:

- First safe write class boundaries.
- Exact allowed file requirements.
- Exact forbidden file requirements.
- Approval-token prerequisites.
- Rollback requirements.
- Verification requirements.
- Protected-lane barriers.
- Manual checks before any future implementation.

Step 6 may not implement runtime modules, tests, write functions, evidence writers, receipt writers, command execution, queue execution, dashboard UI, package changes, config changes, or `/coding` shell changes.

## Non-Scope

This Step 6 planning pass does not:

- Write files through Cartographer.
- Write evidence.
- Write receipts.
- Modify app code.
- Modify `/coding` shell or UI files.
- Modify `source_proxy/cartographer` runtime modules.
- Modify `source_proxy/tests`.
- Modify `package.json` or config files.
- Execute queue items.
- Run commands through Cartographer.
- Generate approvals.
- Self-approve.
- Create branches or worktrees.
- Commit, push, merge, stash, checkout, clean, or delete.
- Enable limited unattended operation.
- Enable full auto.

## First Safe Write Class Candidate

The first future safe write class should be documentation/evidence/receipt writes only, and only after exact human approval.

Candidate allowed write classes:

- Exact approved docs write.
- Exact approved evidence write.
- Exact approved receipt write.

These are candidates only. Step 6 does not grant them.

## Required Authority Before Any Future Write

Any future write must require:

- Valid human approval token.
- Distinct human approver.
- Exact action type.
- Exact allowed files.
- Exact forbidden files.
- Current HEAD match.
- Dirty-tree expectation match.
- Kill switch clear.
- Unexpired approval.
- Concrete rollback instructions.
- Concrete verification instructions.
- Trust tier allowing the exact write class.

Missing, stale, expired, ambiguous, or broader-than-approved authority must fail closed.

## Forbidden Write Classes

Forbidden write classes include:

- App code writes.
- `/coding` shell or UI mutation.
- `source_proxy/cartographer` runtime mutation unless a later exact package approves it.
- `source_proxy/tests` mutation unless a later exact package approves it.
- Package file mutation.
- Config file mutation.
- Environment file mutation.
- Generated file mutation.
- Scout file mutation.
- Dashboard component mutation.
- Secret/protected path mutation.
- Broad wildcard writes.
- Branch/worktree creation.
- Commit/push/merge.
- Stash/checkout/clean/delete.

## Manual Checks

After Step 6 planning, manually verify:

- `git diff --check` passes.
- Step 6 docs exist.
- Step 6 says first safe write class is not implemented now.
- Step 6 says candidate writes are docs/evidence/receipt only and exact approved only.
- Step 6 blocks app code, `/coding`, runtime, test, package, config, env, generated, Scout, dashboard, secret, branch/worktree, and git mutation writes.
- Step 6 requires valid human approval token, exact allowed files, exact forbidden files, HEAD match, dirty-tree match, kill switch clear, rollback, verification, and trust tier.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is a docs-only first safe write class plan.

No runtime code, tests, write files, evidence files, receipt files, token validators, approval generation, queue execution, command execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-6-first-safe-write-class-plan.md`

Rollback must not touch `/coding` work, runtime modules, tests, package/config files, branches, worktrees, commits, stashes, generated files, or unrelated dirty files.

## Stop Conditions

Stop immediately if:

- Step 6 writes files through Cartographer.
- Step 6 writes evidence or receipts.
- Step 6 implements runtime write authority.
- Step 6 grants broad write authority.
- Step 6 touches `/coding`, runtime, test, package, or config files.
- Step 6 grants queue execution, command execution, self-approval, limited unattended operation, or full auto.

## Next Recommended Increment

Step 6.1: Exact Write Scope Contract
