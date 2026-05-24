# Cartographer Daily Driver Autonomy Roadmap Plan 4 Phase 3 Closeout

## Phase

Plan 4 Phase 3: Verification API

## Result

Complete. This phase adds the controlled verification runner and API for exact
allowlisted argv only.

## Implemented Scope

- Added `run_verification_command` with:
  - exact argv preview gate
  - `shell=False`
  - timeout capped at 30 seconds
  - workspace-root cwd containment
  - stdout capture
  - stderr capture
  - exit code capture
  - blocked reasons for rejected commands
- Added `GET /v1/cartographer/verification/run` for runner status.
- Added `POST /v1/cartographer/verification/run` for exact allowlisted
  verification commands.
- The API uses `SPIRIT_PROJECT_PATH` allowlisted workspace discovery.
- The API does not accept arbitrary absolute cwd paths.
- Tests prove:
  - exact `git diff --check` can execute without shell
  - forbidden `git reset --hard` blocks without execution
  - missing workspace root blocks
  - nonzero command results capture exit code and stderr

## Authority Boundary

This phase allows only exact allowlisted verification commands. It does not add
shell execution, workflow execution, queue execution, staging, commit, push,
branch, worktree, stash, clean, reset, checkout, package installation, network
commands, hidden background workers, or receipt attachment.

Plan 4 Phase 4 must explicitly approve attaching verification results to safe
write receipts.

## Files Changed

- `source_proxy/cartographer/verification_runner.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_verification_runner.py`
- `source_proxy/tests/test_cartographer_api.py`
- `docs/cartographer-daily-driver-autonomy-plan-4-phase-3-verification-api-closeout.md`

## Manual Check

```bash
cd /home/source/SpiritOS

git status --branch --short
git diff --check
git diff --stat -- \
  source_proxy/cartographer/verification_runner.py \
  source_proxy/api/cartographer.py \
  source_proxy/tests/test_cartographer_verification_runner.py \
  source_proxy/tests/test_cartographer_api.py \
  docs/cartographer-daily-driver-autonomy-plan-4-phase-3-verification-api-closeout.md

git diff --name-only

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_cartographer_verification_runner.py \
  source_proxy/tests/test_cartographer_api.py -k "verification_run or safe_write or approval_token"

grep -nE "Plan 4|Phase 3|Verification API|/v1/cartographer/verification/run|run_verification_command|exact allowlisted|argv|shell=False|timeout|cwd|stdout|stderr|exit code|blocked|git diff --check|git reset --hard|command|workflow|queue|commit|push|branch|worktree|stash|clean|reset|checkout|manual check|next permission" \
  docs/cartographer-daily-driver-autonomy-plan-4-phase-3-verification-api-closeout.md
```

## Next Permission

Plan 4 Phase 4: Verification Receipt Attached To Safe Write

Required approval before continuing:

Approve Cartographer Daily Driver Roadmap Plan 4 Phase 4 Verification Receipt Attached To Safe Write
