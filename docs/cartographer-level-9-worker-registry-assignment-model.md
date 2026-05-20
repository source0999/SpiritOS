# Cartographer Level 9 Worker Registry And Assignment Model

status: implemented-read-only

Status date: 2026-05-20

## Purpose

Level 9.1 adds a read-only worker registry and assignment model. Cartographer may report observed workers, task ids, branches, owners, allowed files, and assignment status, but it cannot assign, reassign, overwrite, create branches, create worktrees, commit, push, or merge.

This increment does not implement Level 9.2 one worker/one task/one branch rules, Level 9.3 conflict checking, Level 9.4 branch/worktree proposal queues, Level 9.5 stale worker detection, Level 9.6 dashboard work, or any Level 10 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 9.0 boundary: `docs/cartographer-level-9-multi-worker-boundary-contract.md`.
- Level 8 closeout: `docs/cartographer-level-8-closeout-smoke.md`.
- Service surface: `build_cartographer_level_9_worker_registry` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-9-worker-registry` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_9_worker_registry_reports_assignments_without_writes` and `test_level_9_worker_registry_keeps_level_8_closeout_and_no_topology_changes` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 9.1 payload reports:

- `status: observing`.
- `level: 9`.
- `mode: worker_registry_assignment_model`.
- `contract_version: cartographer.level_9.worker_registry_assignment_model.v1`.
- `worker_registry_available: true`.
- `assignment_model_available: true`.
- `assignment_write_allowed: false`.
- `automatic_reassignment_allowed: false`.
- `force_overwrite_allowed: false`.
- `branch_creation_allowed: false`.
- `worktree_creation_allowed: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

Each worker entry must remain recommendation-only and must not create or modify assignments.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-9-worker-registry-assignment-model.md`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

## Forbidden Actions

- No assignment writes.
- No automatic reassignment.
- No force overwrite.
- No branch creation.
- No worktree creation.
- No commit.
- No push.
- No merge.
- No cleanup.
- No stash.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 10 work.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-9-worker-registry-assignment-model.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "implemented-read-only\|No automatic reassignment\|No force overwrite\|branch_creation_allowed: false" docs/cartographer-level-9-worker-registry-assignment-model.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_worker_registry or level_8_closeout_smoke"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 9.1 safety terms.
- focused Level 9.1 and Level 8 closeout tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no assignment write, reassignment, force overwrite, branch creation, worktree creation, commit, push, merge, cleanup, stash, automatic execution, promotion, self-approval, or Level 10 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-9-worker-registry-assignment-model.md`.
- revert `build_cartographer_level_9_worker_registry` and `_level_9_worker_registry_entry` in `source_proxy/cartographer/service.py`.
- revert the Level 9.1 route in `source_proxy/api/cartographer.py`.
- revert the Level 9.1 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 9.2: One Worker, One Task, One Branch Rule.

Do not implement Level 9.2 until Level 9.1 is complete, manually checked, and explicitly approved.
