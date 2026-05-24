# Cartographer Live Operation Step 6.2: Rollback And Verification Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only rollback and verification contract for the first future safe write class.

Rollback and verification are required before any future write can be considered. This document does not implement rollback automation, verification command execution, write authority, command authority, or queue execution.

Limited unattended operation is not granted. Full auto is not granted.

## Rollback Requirements

Future approval-bound writes must include rollback instructions that are:

- Exact.
- Human-readable.
- Scoped to the exact approved files.
- Independent of stash, checkout, clean, delete, branch, or worktree operations.
- Safe with unrelated dirty files present.
- Clear about which generated or protected files must not be touched.

Rollback must not require mutating `/coding`, runtime, test, package, config, env, generated, Scout, dashboard, secret, or protected files.

## Verification Requirements

Future approval-bound writes must include verification instructions that are:

- Exact.
- Human-readable.
- Scoped to the approved write.
- Safe with unrelated dirty files present.
- Clear about expected output.
- Clear about stop conditions.

Step 6.2 does not approve command execution through Cartographer. Verification may be manual unless a later Step 7 controlled command execution plan separately approves exact commands.

## Rollback Failure Conditions

Rollback is invalid if it:

- Relies on stash, checkout, clean, delete, branch, or worktree operations.
- Requires touching protected lanes.
- Is broader than the exact approved files.
- Cannot be manually reviewed.
- Ignores unrelated dirty files.
- Omits expected final state.

## Verification Failure Conditions

Verification is invalid if it:

- Requires broad command execution through Cartographer.
- Requires queue execution.
- Requires writing evidence or receipts before those write classes are separately approved.
- Requires package/config mutation.
- Ignores protected lanes.
- Has ambiguous success criteria.
- Has no stop conditions.

## Manual Checks

After Step 6.2, manually verify:

- `git diff --check` passes.
- The Step 6.2 doc exists.
- Rollback requirements are exact, human-readable, scoped, and do not rely on stash, checkout, clean, delete, branch, or worktree operations.
- Verification requirements are exact, scoped, safe with unrelated dirty files, and do not approve command execution through Cartographer.
- Rollback and verification failure conditions are listed.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only rollback and verification contract.

No runtime code, tests, write files, evidence files, receipt files, rollback automation, command execution, queue execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-6-2-rollback-and-verification-contract.md`

## Stop Conditions

Stop immediately if:

- Step 6.2 implements rollback automation.
- Step 6.2 approves command execution through Cartographer.
- Step 6.2 relies on stash, checkout, clean, delete, branch, or worktree operations.
- Step 6.2 touches `/coding`, runtime, test, package, or config files.
- Step 6.2 grants limited unattended operation or full auto.

## Next Recommended Increment

Step 6.3: Protected Lane Write Barrier
