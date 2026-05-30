# Cartographer Daily Driver Autonomy Plan 6 Phase 3 Run-Next One-Task-Only Endpoint Closeout

## Scope

Plan 6 Phase 3 added a request-scoped `run-next` endpoint that selects at most one eligible approved safe task per invocation.

Allowed files touched:

- `source_proxy/cartographer/safe_task_queue.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_safe_task_queue.py`
- `source_proxy/tests/test_cartographer_safe_task_queue_api.py`
- `docs/cartographer-daily-driver-autonomy-plan-6-phase-3-run-next-one-task-only-endpoint-closeout.md`

## Implemented

- Added `select_next_safe_task` as a data-only selector.
- Added `SafeTaskRunNextSelection` to report selected task data, selected count, eligible count, rejected count, evaluated count, validation results, and authority flags.
- Added `GET /v1/cartographer/queue/run-next` as a route/status check.
- Added `POST /v1/cartographer/queue/run-next` to evaluate supplied queue records and select at most one eligible pending task.
- Kept selection request-scoped because no durable queue storage path has been approved.
- Added direct FastAPI `TestClient` coverage for route existence, one-task-only selection, exact approval token blocking, and kill-switch blocking.

## Boundaries Preserved

- No task execution.
- No safe writes.
- No durable queue storage.
- No queue worker.
- No background loop.
- No auto-selection outside an explicit request.
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

- `source_proxy/tests/test_cartographer_safe_task_queue.py`: 12 passed.
- `source_proxy/tests/test_cartographer_safe_task_queue_api.py`: 3 passed.
