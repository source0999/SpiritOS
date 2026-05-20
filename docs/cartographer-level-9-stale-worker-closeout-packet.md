# Cartographer Level 9 Stale Worker Detection And Closeout Packet

status: implemented-closeout-packet-preview

Status date: 2026-05-20

## Purpose

Level 9.5 adds stale worker detection and closeout packet previews. Cartographer may flag a stale or blocked worker and propose a human-reviewed closeout packet, but it cannot close workers, reassign tasks, delete branches, delete worktrees, clean up, stash, commit, push, or merge.

This increment does not implement Level 9.6 coordination dashboard work or any Level 10 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 9.0 boundary: `docs/cartographer-level-9-multi-worker-boundary-contract.md`.
- Level 9.4 proposal queue: `docs/cartographer-level-9-branch-worktree-proposal-queue.md`.
- Service surface: `build_cartographer_level_9_stale_worker_closeout_packet` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-9-stale-worker-closeout` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_9_stale_worker_closeout_packet_is_review_only` and `test_level_9_stale_worker_closeout_packet_preserves_proposal_queue_safety` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 9.5 payload reports:

- `status: observing`.
- `level: 9`.
- `mode: stale_worker_detection_closeout_packet`.
- `contract_version: cartographer.level_9.stale_worker_detection_closeout_packet.v1`.
- `stale_worker_detection_available: true`.
- `closeout_packet_available: true`.
- `closeout_execution_allowed: false`.
- `automatic_reassignment_allowed: false`.
- `automatic_closeout_allowed: false`.
- `branch_deletion_allowed: false`.
- `worktree_deletion_allowed: false`.
- `cleanup_allowed: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

## Forbidden Actions

- No automatic reassignment.
- No automatic closeout.
- No branch deletion.
- No worktree deletion.
- No cleanup.
- No stash.
- No commit.
- No push.
- No merge.
- No force overwrite.
- No branch creation.
- No worktree creation.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 10 work.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-9-stale-worker-closeout-packet.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "implemented-closeout-packet-preview\|No automatic closeout\|No branch deletion\|closeout_execution_allowed: false" docs/cartographer-level-9-stale-worker-closeout-packet.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_stale_worker_closeout_packet or level_9_branch_worktree_proposal_queue"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 9.5 safety terms.
- focused Level 9.5 and Level 9.4 tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no reassignment, closeout, branch deletion, worktree deletion, cleanup, stash, commit, push, merge, force overwrite, branch creation, worktree creation, automatic execution, promotion, self-approval, or Level 10 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-9-stale-worker-closeout-packet.md`.
- revert `build_cartographer_level_9_stale_worker_closeout_packet` and `_level_9_stale_worker_packet` in `source_proxy/cartographer/service.py`.
- revert the Level 9.5 route in `source_proxy/api/cartographer.py`.
- revert the Level 9.5 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 9.6: Level 9 Coordination Dashboard.

Do not implement Level 9.6 until Level 9.5 is complete, manually checked, and explicitly approved.
