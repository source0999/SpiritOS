# Cartographer Daily Driver Autonomy Plan 6 Phase 5 First Auto-Selected Safe Task Run Closeout

## Scope

Plan 6 Phase 5 added the first bounded auto-selected safe task run and receipt path.

Allowed files touched:

- `source_proxy/cartographer/safe_task_queue.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_safe_task_queue.py`
- `source_proxy/tests/test_cartographer_safe_task_queue_api.py`
- `docs/cartographer-daily-driver-autonomy-plan-6-phase-5-first-auto-selected-safe-task-run-closeout.md`

## Implemented

- Added `run_first_auto_selected_safe_task`.
- Added `SafeTaskRunReceipt` for one-task run results and receipt payloads.
- Extended `POST /v1/cartographer/queue/run-next` with explicit `run_selected_task`.
- Preserved Phase 6.3 selection-only behavior when `run_selected_task` is omitted or false.
- Completed one proposal-only task per explicit request and returned an in-memory receipt.
- Blocked safe-write-later classes with `task_class_requires_later_safe_write_phase`.
- Preserved exact trust tier, exact approval token, and kill-switch checks.

## Boundaries Preserved

- No source writes.
- No safe writes.
- No verification execution.
- No durable queue storage.
- No queue worker.
- No background loop.
- No command execution.
- No approval token minting or storage.
- No staging, commit, push, branch, worktree, stash, clean, reset, or checkout authority.

## Verification

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_safe_task_queue_api.py
git diff --check
git status --branch --short
```

Focused result:

- `source_proxy/tests/test_cartographer_safe_task_queue.py`: 16 passed.
- `source_proxy/tests/test_cartographer_safe_task_queue_api.py`: 4 passed.
