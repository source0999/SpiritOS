# Cartographer Live Operation Step 8.2: Kill Switch Control Boundary

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only kill switch control boundary for future operator dashboard controls.

The kill switch is a fail-closed operator safety concept. This document does not implement kill switch UI, dashboard controls, runtime state, storage, or automation.

Limited unattended operation is not granted. Full auto is not granted.

## Kill Switch Principles

Future kill switch behavior must:

- Fail closed when active.
- Fail closed when missing.
- Fail closed when ambiguous.
- Block writes.
- Block command execution.
- Block queue execution.
- Block approval acceptance.
- Block self-approval.
- Block branch/worktree creation and git mutation.
- Block protected-lane mutation.

## Dashboard Boundary

Future dashboard controls may display kill switch status only unless a later exact package separately approves mutation.

Displaying kill switch status does not implement kill switch control. A future toggle, button, or indicator must not imply live autonomy, queue execution, command execution, approval generation, or write authority.

## Forbidden Kill Switch Patterns

Forbidden patterns include:

- Kill switch defaults open.
- Missing kill switch permits action.
- Ambiguous kill switch permits action.
- Dashboard display bypasses kill switch.
- Queue storage bypasses kill switch.
- Approval token bypasses kill switch.
- Command allowlist bypasses kill switch.
- Self-approval bypasses kill switch.

## Manual Checks

After Step 8.2, manually verify:

- `git diff --check` passes.
- The Step 8.2 doc exists.
- Kill switch principles fail closed when active, missing, or ambiguous.
- Kill switch blocks writes, command execution, queue execution, approval acceptance, self-approval, git mutation, and protected-lane mutation.
- Dashboard boundary says display-only unless a later exact package separately approves mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only kill switch control boundary.

No UI, dashboard component, runtime code, tests, command runners, queue execution, write files, approval generation, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-8-2-kill-switch-control-boundary.md`

## Stop Conditions

Stop immediately if:

- Step 8.2 implements kill switch UI or runtime state.
- Step 8.2 allows missing or ambiguous kill switch state to permit action.
- Step 8.2 grants command execution, queue execution, write authority, limited unattended operation, or full auto.
- Step 8.2 touches `/coding`, runtime, test, dashboard, package, or config files.

## Next Recommended Increment

Step 8.3: Operator Control Authority Boundary
