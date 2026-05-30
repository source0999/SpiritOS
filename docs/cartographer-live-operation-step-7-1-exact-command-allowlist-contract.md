# Cartographer Live Operation Step 7.1: Exact Command Allowlist Contract

status: documentation-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the planning-only exact command allowlist contract for future controlled command execution.

The contract describes how future verification commands must be matched exactly before execution can be considered. It does not implement a runner, execute commands, create allowlist files, or grant command authority.

Limited unattended operation is not granted. Full auto is not granted.

## Exact Allowlist Rules

Future command approval must obey:

- Commands must match an exact approved form.
- Arguments must match exact approved arguments.
- Working directory must match exact approved working directory.
- Environment must be explicitly approved or empty.
- Timeout must be explicit.
- Output capture policy must be explicit.
- Exit-code expectations must be explicit.
- Shell expansion must be blocked unless explicitly represented in the approved command form.
- Any mismatch fails closed.

## Forbidden Allowlist Patterns

Future allowlists must not include:

- Wildcard commands.
- Broad shell strings.
- Command prefixes that allow arbitrary suffixes.
- Unbounded environment inheritance.
- Unbounded working directories.
- Background execution.
- Recurring execution.
- Destructive commands.
- Git mutation commands.
- Package/config/env mutation commands.
- `/coding` mutation commands.
- Runtime/test mutation commands.

## Approval Requirements

Each future command entry must require:

- Valid human approval token.
- Exact command.
- Exact arguments.
- Exact working directory.
- Exact timeout.
- Exact output capture policy.
- Exact expected exit code.
- Current HEAD match.
- Dirty-tree expectation match.
- Kill switch clear.
- Trust tier allowing controlled verification command execution.

Missing or ambiguous approval fails closed.

## Manual Checks

After Step 7.1, manually verify:

- `git diff --check` passes.
- The Step 7.1 doc exists.
- Exact allowlist rules require exact command, arguments, working directory, environment, timeout, output capture, and exit-code expectations.
- Forbidden allowlist patterns block wildcards, broad shell strings, arbitrary suffixes, unbounded env/workdirs, background/recurring execution, destructive commands, git mutation, package/config/env mutation, `/coding` mutation, and runtime/test mutation.
- Limited unattended operation is not granted.
- Full auto is not granted.

## Expected Output

Expected output is this docs-only exact command allowlist contract.

No runtime code, tests, allowlist files, command runners, command execution, queue execution, write files, approval generation, live autonomy, `/coding` mutation, package/config mutation, staging, commit, push, merge, stash, checkout, clean, branch, or worktree operation is expected.

## Rollback Notes

Rollback is limited to removing:

- `docs/cartographer-live-operation-step-7-1-exact-command-allowlist-contract.md`

## Stop Conditions

Stop immediately if:

- Step 7.1 implements allowlist files or runtime command matching.
- Step 7.1 runs commands.
- Step 7.1 allows wildcards, arbitrary suffixes, broad shell access, limited unattended operation, or full auto.
- Step 7.1 touches `/coding`, runtime, test, package, or config files.

## Next Recommended Increment

Step 7.2: No Shell Expansion Barrier
