# Cartographer Daily Driver Autonomy Plan 8 Phase 1 Closeout

## Phase

Plan 8 Phase 1: Worker registry / worker contract model.

## Scope Completed

- Added an inert worker contract model in `source_proxy/cartographer/worker_contract.py`.
- Added focused tests in `source_proxy/tests/test_cartographer_worker_contract.py`.
- Modeled worker id, name, role, assigned task id, exact allowed and forbidden file scopes, trust tier, approval token reference, status, active/stale state, current step, heartbeat/check-in timestamps, blocked reason, and lifecycle timestamps.
- Locked worker roles to Codex, Scout, Proxy, Designer, Blueprinter, and sub-cartographer only.
- Required exact trust tier and approval token references during validation.
- Rejected broad file scopes, duplicate scope entries, empty scopes, and allowed/forbidden overlap.

## Authority Boundary

This phase is model and validation only. It does not spawn workers, dispatch workers, run queues, execute tasks, run commands, perform safe writes, mint or store approval tokens, use durable storage, stage, commit, push, branch, create worktrees, stash, clean, reset, or checkout.

## Verification

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_worker_contract.py
git diff --check
```

## Next Phase

Plan 8 Phase 2: File Ownership And Locks.
