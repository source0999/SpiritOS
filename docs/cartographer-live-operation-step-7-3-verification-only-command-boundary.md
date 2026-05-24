# Cartographer Live Operation Step 7.3: Verification-Only Command Boundary

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only verification-only command boundary for future controlled command execution.

Verification-only commands are future candidates for checking known state. They are not task execution, not mutation authority, not queue execution, not approval generation, and not unattended operation.

Limited unattended operation is not granted. Full auto is not granted.

## Verification-Only Rules

Future verification commands must:

- Be exact approved commands.
- Be linked to a specific approved verification need.
- Have exact expected output or exit-code expectations.
- Be safe with unrelated dirty files.
- Avoid mutation.
- Avoid package/config/env changes.
- Avoid protected-lane writes.
- Avoid branch/worktree or git mutation.
- Avoid background or recurring behavior.

## Forbidden Verification Uses

Verification commands must not be used to:

- Execute queue items.
- Select tasks automatically.
- Generate approvals.
- Self-approve.
- Write evidence or receipts unless separately approved.
- Mutate app code.
- Mutate `/coding` shell or UI files.
- Mutate runtime modules.
- Mutate tests.
- Mutate package/config/env/generated files.
- Create branches or worktrees.
- Commit, push, merge, stash, checkout, clean, or delete.

## Output Handling

Future output handling must:

- Capture only the approved output.
- Avoid secrets and environment values.
- Avoid writing output to files unless separately approved.
- Report failures as blocked recommendations.
- Preserve fail-closed behavior.

## Manual Checks

After Step 7.3, manually verify:

- `git diff --check` passes.
- The Step 7.3 doc exists.
- Verification-only rules require exact approved commands, exact expected output or exit-code expectations, safety with unrelated dirty files, and no mutation.
- Forbidden uses block queue execution, task selection, approval generation, self-approval, evidence/receipt writes, app code mutation, `/coding` mutation, runtime/test mutation, package/config/env mutation, and git mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only verification-only command boundary.

No runtime code, tests, command runners, command execution, queue execution, write files, approval generation, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-7-3-verification-only-command-boundary.md`

## Stop Conditions

Stop immediately if:

- Step 7.3 implements command execution.
- Step 7.3 treats verification as task execution or mutation authority.
- Step 7.3 grants queue execution, write authority, self-approval, limited unattended operation, or full auto.
- Step 7.3 touches `/coding`, runtime, test, package, or config files.

## Next Recommended Increment

Step 7.4: Controlled Command Execution Closeout And Step 8 Gate
