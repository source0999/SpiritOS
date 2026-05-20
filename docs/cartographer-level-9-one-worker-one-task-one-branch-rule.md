# Cartographer Level 9 One Worker One Task One Branch Rule

status: implemented-rule-preview

Status date: 2026-05-20

## Purpose

Level 9.2 adds a read-only one worker, one task, one branch rule model. Cartographer may evaluate whether each observed worker has a single task and branch, but it cannot create branches, checkout branches, reassign work, overwrite files, commit, push, or merge.

This increment does not implement Level 9.3 allowed-file conflict checking, Level 9.4 branch/worktree proposal queues, Level 9.5 stale worker detection, Level 9.6 dashboard work, or any Level 10 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 9.0 boundary: `docs/cartographer-level-9-multi-worker-boundary-contract.md`.
- Level 9.1 worker registry: `docs/cartographer-level-9-worker-registry-assignment-model.md`.
- Service surface: `build_cartographer_level_9_one_worker_rule` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-9-one-worker-rule` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_9_one_worker_one_task_one_branch_rule_reports_without_topology_changes` and `test_level_9_one_worker_one_task_one_branch_rule_preserves_registry_safety` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 9.2 payload reports:

- `status: observing`.
- `level: 9`.
- `mode: one_worker_one_task_one_branch_rule`.
- `contract_version: cartographer.level_9.one_worker_one_task_one_branch_rule.v1`.
- `rule_model_available: true`.
- `recommendation_only: true`.
- `assignment_write_allowed: false`.
- `automatic_reassignment_allowed: false`.
- `force_overwrite_allowed: false`.
- `branch_creation_allowed: false`.
- `worktree_creation_allowed: false`.
- `checkout_allowed: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

## Forbidden Actions

- No branch creation.
- No branch checkout.
- No worktree creation.
- No assignment writes.
- No automatic reassignment.
- No force overwrite.
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
git diff --check -- docs/cartographer-level-9-one-worker-one-task-one-branch-rule.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "implemented-rule-preview\|No branch checkout\|No force overwrite\|checkout_allowed: false" docs/cartographer-level-9-one-worker-one-task-one-branch-rule.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_one_worker_one_task_one_branch or level_9_worker_registry"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 9.2 safety terms.
- focused Level 9.2 and Level 9.1 tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no branch creation, branch checkout, worktree creation, assignment write, reassignment, force overwrite, commit, push, merge, cleanup, stash, automatic execution, promotion, self-approval, or Level 10 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-9-one-worker-one-task-one-branch-rule.md`.
- revert `build_cartographer_level_9_one_worker_rule` and `_level_9_one_worker_rule_item` in `source_proxy/cartographer/service.py`.
- revert the Level 9.2 route in `source_proxy/api/cartographer.py`.
- revert the Level 9.2 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 9.3: Allowed-File Conflict Checker.

Do not implement Level 9.3 until Level 9.2 is complete, manually checked, and explicitly approved.
