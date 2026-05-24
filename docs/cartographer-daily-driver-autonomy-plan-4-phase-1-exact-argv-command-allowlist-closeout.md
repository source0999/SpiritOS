# Cartographer Daily Driver Autonomy Roadmap Plan 4 Phase 1 Closeout

## Phase

Plan 4 Phase 1: Exact Argv Command Allowlist

## Result

Complete. This phase defines a preview-only verification command allowlist using
exact argv arrays.

## Implemented Scope

- Added a pure allowlist module for verification command specs.
- Represented every allowed command as a tuple of argv parts, not a shell string.
- Added initial exact allowed command entries:
  - `["git", "diff", "--check"]`
  - `["git", "status", "--short"]`
  - `[".venv/bin/python", "-m", "pytest", "<exact approved test file>"]`
  - `["npm", "test", "--", "<exact approved test file>"]`
- Added preview-only matching that accepts only exact argv arrays.
- Shell strings, malformed argv, unapproved test files, absolute test paths,
  traversal-shaped test paths, wildcard test paths, and near-miss argv are
  blocked.

## Authority Boundary

This phase does not execute commands. It does not open a shell, run subprocesses,
execute workflows, execute queues, stage files, commit, push, branch, create
worktrees, stash, clean, reset, checkout, install packages, access the network,
or mutate repository files.

Plan 4 Phase 2 must add negative tests before any command runner can execute.

## Files Changed

- `source_proxy/cartographer/verification_runner.py`
- `source_proxy/tests/test_cartographer_verification_runner.py`
- `docs/cartographer-daily-driver-autonomy-plan-4-phase-1-exact-argv-command-allowlist-closeout.md`

## Manual Check

```bash
cd /home/source/SpiritOS

git status --branch --short
git diff --check
git diff --stat -- \
  source_proxy/cartographer/verification_runner.py \
  source_proxy/tests/test_cartographer_verification_runner.py \
  docs/cartographer-daily-driver-autonomy-plan-4-phase-1-exact-argv-command-allowlist-closeout.md

git diff --name-only

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_cartographer_verification_runner.py

grep -nE "Plan 4|Phase 1|Exact Argv Command Allowlist|argv|allowlist|git diff --check|git status --short|pytest|npm|approved test file|shell|string|malformed|blocked|command|workflow|queue|commit|push|branch|worktree|stash|clean|reset|checkout|manual check|next permission" \
  docs/cartographer-daily-driver-autonomy-plan-4-phase-1-exact-argv-command-allowlist-closeout.md
```

## Next Permission

Plan 4 Phase 2: Verification Runner Tests

Required approval before continuing:

Approve Cartographer Daily Driver Roadmap Plan 4 Phase 2 Verification Runner Tests
