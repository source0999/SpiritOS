# Cartographer Live Operation Step 6.1: Exact Write Scope Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only exact write scope contract for the first future safe write class.

The contract describes how a future write could be constrained to exact approved files. It does not implement writes, create files through Cartographer, write evidence, write receipts, or grant authority.

Limited unattended operation is not granted. Full auto is not granted.

## Exact Scope Rules

Future write scope must obey:

- Allowed files must be exact paths.
- Forbidden files must be exact paths or protected path families.
- Wildcards are not sufficient for write authority.
- Directory-wide write authority is not sufficient.
- Empty allowed file scope blocks writes.
- Missing forbidden file scope blocks writes.
- Any requested file outside exact allowed files blocks writes.
- Any requested file matching forbidden files blocks writes.
- Any protected lane match blocks writes.

## Candidate Allowed File Families

Future first safe write class may only consider exact approved files within:

- `docs/` for approved documentation writes.
- A future exact evidence docs path, only if separately approved.
- A future exact receipt docs path, only if separately approved.

This document does not approve any actual file write.

## Always Forbidden File Families

Always forbidden for the first safe write class:

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

## Scope Mismatch Handling

Any mismatch must fail closed:

- Requested file absent from allowed files.
- Requested file present in forbidden files.
- Requested file under protected lane.
- Approval names a directory but request names a file.
- Approval names a file but request expands to adjacent files.
- Approval omits HEAD or dirty-tree expectation.
- Approval is stale, expired, ambiguous, or self-approved.

Fail closed means no write, no evidence, no receipt, no queue execution, no command execution, and no git mutation.

## Manual Checks

After Step 6.1, manually verify:

- `git diff --check` passes.
- The Step 6.1 doc exists.
- Exact scope rules require exact paths and block wildcards, directory-wide authority, empty allowed scope, missing forbidden scope, and protected lane matches.
- Always forbidden families include `/coding`, runtime, tests, API, package, config, env, generated, Scout, dashboard, secrets, and protected paths.
- Scope mismatch fails closed.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only exact write scope contract.

No runtime code, tests, write files, evidence files, receipt files, queue execution, command execution, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-6-1-exact-write-scope-contract.md`

## Stop Conditions

Stop immediately if:

- Step 6.1 grants wildcard or directory-wide write authority.
- Step 6.1 implements writes.
- Step 6.1 touches `/coding`, runtime, test, package, or config files.
- Step 6.1 grants queue execution, command execution, self-approval, limited unattended operation, or full auto.

## Next Recommended Increment

Step 6.2: Rollback And Verification Contract
