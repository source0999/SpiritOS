# Cartographer Daily Driver Autonomy Plan 6 Phase 1 Queue Model Closeout

## Scope

Plan 6 Phase 1 added a model-only safe task queue record contract for durable task records.

Allowed files touched:

- `source_proxy/cartographer/safe_task_queue.py`
- `source_proxy/tests/test_cartographer_safe_task_queue.py`
- `docs/cartographer-daily-driver-autonomy-plan-6-phase-1-queue-model-closeout.md`

## Implemented

- Added `SafeTaskRecord` with durable record fields for task id, task class, trust tier, approval token id, allowed files, forbidden files, status, attempts, created at, selected at, completed at, and blocked reason.
- Added explicit task statuses: `pending`, `selected`, `running`, `completed`, `blocked`, `failed`, and `cancelled`.
- Added model-only validation for exact trust tier and approval token reference.
- Added bounded attempts with `MAX_SAFE_TASK_ATTEMPTS = 3`.
- Added fail-closed validation for malformed records, missing required fields, unknown task classes, unknown statuses, invalid timestamps, missing allowed files, duplicate file scope entries, and allowed/forbidden overlap.
- Locked Phase 6.1 to a single model-only task class, `queue_model_validation_only`, leaving task class expansion to Phase 6.2.

## Boundaries Preserved

- No `run-next` endpoint.
- No auto-selection.
- No task execution.
- No background loop.
- No API or UI wiring.
- No safe writes.
- No queue worker.
- No durable storage implementation.
- No approval token minting or storage.
- No staging, commit, push, branch, worktree, stash, clean, reset, or checkout authority.

## Verification

```bash
cd /home/source/SpiritOS
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safe_task_queue.py
git diff --check
git status --branch --short
```

Focused result:

- `source_proxy/tests/test_cartographer_safe_task_queue.py`: 8 passed.
