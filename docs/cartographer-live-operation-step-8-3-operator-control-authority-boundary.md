# Cartographer Live Operation Step 8.3: Operator Control Authority Boundary

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only authority boundary for future operator controls.

Operator controls may guide a human review workflow, but control presence is not authority. This document does not implement controls, UI, runtime behavior, approval flows, command execution, queue execution, or writes.

Limited unattended operation is not granted. Full auto is not granted.

## Authority Rules

Future operator controls must obey:

- A button is not approval.
- A toggle is not approval.
- A selected row is not task selection authority.
- A visible queue item is not executable authority.
- A visible event is not receipt or evidence authority.
- A visible approval requirement is not approval generation.
- A visible command is not command execution authority.
- A visible write class is not write authority.

## Required Human Confirmation

Future control flows must require separate exact human confirmation before any future action class:

- Exact approval token for writes.
- Exact approval token for command execution.
- Exact approval token for queue execution if a later package ever permits it.
- Exact allowed files.
- Exact forbidden files.
- Exact action class.
- Current HEAD match.
- Dirty-tree expectation match.
- Kill switch clear.

## Forbidden Control Patterns

Forbidden patterns include:

- Full auto toggle.
- Limited unattended operation toggle.
- Self-approval button.
- Execute queue button without exact approval.
- Run command button without exact approval.
- Broad approve button.
- Broad write button.
- Protected-lane mutation button.
- Branch/worktree/git mutation control.
- Package/config mutation control.

## Manual Checks

After Step 8.3, manually verify:

- `git diff --check` passes.
- The Step 8.3 doc exists.
- Authority rules say visible controls do not grant approval, task selection, queue execution, evidence/receipt authority, approval generation, command execution, or write authority.
- Forbidden control patterns block full auto, limited unattended operation, self-approval, queue execution without exact approval, command execution without exact approval, broad approval/write controls, protected-lane mutation, git mutation, and package/config mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only operator control authority boundary.

No UI, dashboard component, runtime code, tests, command runners, queue execution, write files, approval generation, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-8-3-operator-control-authority-boundary.md`

## Stop Conditions

Stop immediately if:

- Step 8.3 implements controls or UI.
- Step 8.3 treats control presence as authority.
- Step 8.3 grants approval generation, command execution, queue execution, write authority, limited unattended operation, or full auto.
- Step 8.3 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 8.4: Operator Dashboard Controls Closeout And Step 9 Gate
