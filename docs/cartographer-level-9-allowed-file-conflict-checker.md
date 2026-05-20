# Cartographer Level 9 Allowed-File Conflict Checker

status: implemented-conflict-preview

Status date: 2026-05-20

## Purpose

Level 9.3 adds allowed-file conflict checking before suggesting parallel work. Cartographer may detect overlapping allowed-file scopes and block parallel-work suggestions, but it cannot overwrite files, reassign workers, create branches, create worktrees, commit, push, or merge.

This increment does not implement Level 9.4 branch/worktree proposal queues, Level 9.5 stale worker detection, Level 9.6 dashboard work, or any Level 10 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 9.0 boundary: `docs/cartographer-level-9-multi-worker-boundary-contract.md`.
- Level 9.1 worker registry: `docs/cartographer-level-9-worker-registry-assignment-model.md`.
- Level 9.2 one worker rule: `docs/cartographer-level-9-one-worker-one-task-one-branch-rule.md`.
- Service surface: `build_cartographer_level_9_allowed_file_conflict_checker` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-9-allowed-file-conflicts` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_9_allowed_file_conflict_checker_blocks_parallel_suggestion_without_overwrite` and `test_level_9_allowed_file_conflict_checker_preserves_rule_payload` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 9.3 payload reports:

- `status: observing`.
- `level: 9`.
- `mode: allowed_file_conflict_checker`.
- `contract_version: cartographer.level_9.allowed_file_conflict_checker.v1`.
- `conflict_checker_available: true`.
- `recommendation_only: true`.
- `parallel_work_suggestion_allowed` based on conflict state.
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

- No force overwrite.
- No automatic reassignment.
- No branch creation.
- No worktree creation.
- No checkout.
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
git diff --check -- docs/cartographer-level-9-allowed-file-conflict-checker.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "implemented-conflict-preview\|No force overwrite\|No automatic reassignment\|parallel_work_suggestion_allowed" docs/cartographer-level-9-allowed-file-conflict-checker.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_allowed_file_conflict_checker or level_9_one_worker_one_task_one_branch"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 9.3 safety terms.
- focused Level 9.3 and Level 9.2 tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no force overwrite, reassignment, branch creation, worktree creation, checkout, commit, push, merge, cleanup, stash, automatic execution, promotion, self-approval, or Level 10 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-9-allowed-file-conflict-checker.md`.
- revert `build_cartographer_level_9_allowed_file_conflict_checker` and `_level_9_allowed_file_conflicts` in `source_proxy/cartographer/service.py`.
- revert the Level 9.3 route in `source_proxy/api/cartographer.py`.
- revert the Level 9.3 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 9.4: Branch And Worktree Proposal Queue.

Do not implement Level 9.4 until Level 9.3 is complete, manually checked, and explicitly approved.
