# Cartographer Level 9 Coordination Dashboard

status: implemented-dashboard-preview

Status date: 2026-05-20

## Purpose

Level 9.6 adds a coordination dashboard for multi-worker safety. Cartographer may summarize workers, tasks, file conflicts, branch/worktree proposals, stale worker packets, and Level 10 gating, but it cannot mutate assignments, create topology, clean up, commit, push, or merge.

This increment does not implement Level 10 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 9.0 boundary: `docs/cartographer-level-9-multi-worker-boundary-contract.md`.
- Level 9.1 worker registry: `docs/cartographer-level-9-worker-registry-assignment-model.md`.
- Level 9.2 one worker rule: `docs/cartographer-level-9-one-worker-one-task-one-branch-rule.md`.
- Level 9.3 conflict checker: `docs/cartographer-level-9-allowed-file-conflict-checker.md`.
- Level 9.4 proposal queue: `docs/cartographer-level-9-branch-worktree-proposal-queue.md`.
- Level 9.5 stale worker packet: `docs/cartographer-level-9-stale-worker-closeout-packet.md`.
- Service surface: `build_cartographer_level_9_coordination_dashboard` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-9-coordination-dashboard` in `source_proxy/api/cartographer.py`.

## Contract

The Level 9.6 payload reports:

- `status: observing`.
- `level: 9`.
- `mode: coordination_dashboard`.
- `contract_version: cartographer.level_9.coordination_dashboard.v1`.
- `coordination_dashboard_available: true`.
- `recommendation_only: true`.
- `level_9_closed_out`.
- `level_10_gated: true`.
- `level_10_may_begin: false`.
- `operator_approval_required_for_level_10: true`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `assignment_write_allowed: false`.
- `automatic_reassignment_allowed: false`.
- `force_overwrite_allowed: false`.
- `branch_creation_allowed: false`.
- `worktree_creation_allowed: false`.
- `checkout_allowed: false`.

## Forbidden Actions

- No Level 10 work without explicit approval.
- No assignment writes.
- No automatic reassignment.
- No force overwrite.
- No branch creation.
- No worktree creation.
- No checkout.
- No branch deletion.
- No worktree deletion.
- No cleanup.
- No stash.
- No commit.
- No push.
- No merge.
- No automatic execution.
- No automatic promotion.
- No self-approval.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-9-coordination-dashboard.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "implemented-dashboard-preview\|No Level 10 work\|No automatic reassignment\|level_10_may_begin: false" docs/cartographer-level-9-coordination-dashboard.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_coordination_dashboard or level_9_stale_worker_closeout_packet or level_9_allowed_file_conflict_checker"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 9.6 safety terms.
- focused Level 9.6, Level 9.5, and Level 9.3 tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no Level 10 work, assignment write, reassignment, force overwrite, branch creation, worktree creation, checkout, branch deletion, worktree deletion, cleanup, stash, commit, push, merge, automatic execution, promotion, or self-approval occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-9-coordination-dashboard.md`.
- revert `build_cartographer_level_9_coordination_dashboard` and `_level_9_coordination_dashboard_item` in `source_proxy/cartographer/service.py`.
- revert the Level 9.6 route in `source_proxy/api/cartographer.py`.
- revert the Level 9.6 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 10.0: Production Operator Boundary Contract.

Do not implement Level 10.0 until Level 9.6 is complete, manually checked, and explicitly approved.
