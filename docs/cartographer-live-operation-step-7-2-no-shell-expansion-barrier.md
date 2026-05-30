# Cartographer Live Operation Step 7.2: No Shell Expansion Barrier

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only no shell expansion barrier for future controlled command execution.

The barrier prevents future command approval from becoming broad shell access. It does not implement parsing, command execution, or runtime enforcement.

Limited unattended operation is not granted. Full auto is not granted.

## Barrier Rules

Future controlled command execution must block:

- Shell glob expansion.
- Command substitution.
- Variable expansion unless explicitly approved.
- Pipes.
- Redirects.
- Chained commands.
- Background operators.
- Subshells.
- Interactive prompts.
- Heredocs.
- Unquoted broad shell fragments.
- Any shell behavior not represented in the exact approved command form.

## Safer Command Shape

Future command shape should prefer:

- Executable path or command name as a discrete field.
- Arguments as an exact array.
- Working directory as an exact field.
- Environment as an exact allowlist.
- Timeout as an exact field.
- Output policy as an exact field.

This is a planning shape only. No parser or runner is implemented here.

## Failure Handling

Any detected shell expansion risk must fail closed:

- No command execution.
- No queue execution.
- No write.
- No evidence or receipt write.
- No approval generation.
- No self-approval.
- No git mutation.
- No protected-lane mutation.

## Manual Checks

After Step 7.2, manually verify:

- `git diff --check` passes.
- The Step 7.2 doc exists.
- Barrier rules block glob expansion, command substitution, variable expansion, pipes, redirects, chained commands, background operators, subshells, interactive prompts, heredocs, and broad shell fragments.
- Failure handling says no command execution, queue execution, write, evidence/receipt write, approval generation, self-approval, git mutation, or protected-lane mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only no shell expansion barrier.

No runtime code, tests, parsers, runners, command execution, queue execution, write files, approval generation, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-7-2-no-shell-expansion-barrier.md`

## Stop Conditions

Stop immediately if:

- Step 7.2 implements command parsing or execution.
- Step 7.2 permits broad shell behavior.
- Step 7.2 grants queue execution, write authority, limited unattended operation, or full auto.
- Step 7.2 touches `/coding`, runtime, test, package, or config files.

## Next Recommended Increment

Step 7.3: Verification-Only Command Boundary
