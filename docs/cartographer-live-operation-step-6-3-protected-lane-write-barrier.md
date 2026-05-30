# Cartographer Live Operation Step 6.3: Protected Lane Write Barrier

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only protected lane write barrier for the first future safe write class.

The barrier keeps future write planning away from `/coding`, runtime, tests, package/config files, generated files, and other protected lanes. It does not implement enforcement code or write authority.

Limited unattended operation is not granted. Full auto is not granted.

## Protected Lane Barrier

Future first safe write class planning must block writes to:

- `/coding` shell files.
- `/coding` UI implementation files.
- `src/app/coding/`
- `src/components/coding/`
- `src/lib/coding/`
- `source_proxy/cartographer/`
- `source_proxy/tests/`
- `source_proxy/api/`
- Package files.
- Config files.
- Environment files.
- Generated files.
- Scout files.
- Dashboard components.
- Secrets and protected paths.

## Dirty Tree Handling

Existing dirty work in protected lanes must be treated as pre-existing and intentionally untouched.

Protected dirty files must not be normalized, reverted, staged, cleaned, checked out, stashed, deleted, moved, reformatted, or edited by Cartographer live-operation planning.

## Barrier Output

Future barrier output may say:

- Protected lane matched.
- Write blocked.
- Manual operator review required.
- Narrower exact scope required.
- Step must stop before implementation.

Barrier output must not write files, execute commands, generate approvals, self-approve, queue work, or mutate state.

## Manual Checks

After Step 6.3, manually verify:

- `git diff --check` passes.
- The Step 6.3 doc exists.
- Protected lane barrier blocks `/coding`, runtime, tests, API, package, config, env, generated, Scout, dashboard, secrets, and protected paths.
- Dirty tree handling says protected dirty files must not be normalized, reverted, staged, cleaned, checked out, stashed, deleted, moved, reformatted, or edited.
- Barrier output is inert.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only protected lane write barrier.

No runtime code, tests, write files, evidence files, receipt files, command execution, queue execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-6-3-protected-lane-write-barrier.md`

## Stop Conditions

Stop immediately if:

- Step 6.3 allows writes to protected lanes.
- Step 6.3 edits protected dirty files.
- Step 6.3 implements enforcement code.
- Step 6.3 grants command execution, queue execution, self-approval, limited unattended operation, or full auto.
- Step 6.3 touches `/coding`, runtime, test, package, or config files.

## Next Recommended Increment

Step 6.4: First Safe Write Class Closeout And Step 7 Gate
