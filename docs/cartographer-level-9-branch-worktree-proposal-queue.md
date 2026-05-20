# Cartographer Level 9 Branch And Worktree Proposal Queue

status: implemented-proposal-only

Status date: 2026-05-20

## Purpose

Level 9.4 adds a branch and worktree proposal queue. Cartographer may propose branch and worktree names for human review, but it cannot create branches, create worktrees, checkout branches, clean up, stash, commit, push, or merge.

This increment does not implement Level 9.5 stale worker detection, Level 9.6 dashboard work, or any Level 10 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 9.0 boundary: `docs/cartographer-level-9-multi-worker-boundary-contract.md`.
- Level 9.3 conflict checker: `docs/cartographer-level-9-allowed-file-conflict-checker.md`.
- Service surface: `build_cartographer_level_9_branch_worktree_proposal_queue` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-9-branch-worktree-proposals` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_9_branch_worktree_proposal_queue_is_preview_only` and `test_level_9_branch_worktree_proposal_queue_carries_conflict_blockers` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 9.4 payload reports:

- `status: observing`.
- `level: 9`.
- `mode: branch_worktree_proposal_queue`.
- `contract_version: cartographer.level_9.branch_worktree_proposal_queue.v1`.
- `proposal_queue_available: true`.
- `recommendation_only: true`.
- `branch_creation_allowed: false`.
- `worktree_creation_allowed: false`.
- `checkout_allowed: false`.
- `branch_created: false`.
- `worktree_created: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

## Forbidden Actions

- No automatic branch creation.
- No automatic worktree creation.
- No checkout.
- No cleanup.
- No stash.
- No commit.
- No push.
- No merge.
- No force overwrite.
- No automatic reassignment.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 10 work.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-9-branch-worktree-proposal-queue.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "implemented-proposal-only\|No automatic branch creation\|No automatic worktree creation\|branch_created: false" docs/cartographer-level-9-branch-worktree-proposal-queue.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_branch_worktree_proposal_queue or level_9_allowed_file_conflict_checker"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 9.4 safety terms.
- focused Level 9.4 and Level 9.3 tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no branch creation, worktree creation, checkout, cleanup, stash, commit, push, merge, force overwrite, reassignment, automatic execution, promotion, self-approval, or Level 10 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-9-branch-worktree-proposal-queue.md`.
- revert `build_cartographer_level_9_branch_worktree_proposal_queue` and `_level_9_branch_worktree_proposal` in `source_proxy/cartographer/service.py`.
- revert the Level 9.4 route in `source_proxy/api/cartographer.py`.
- revert the Level 9.4 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 9.5: Stale Worker Detection And Closeout Packet.

Do not implement Level 9.5 until Level 9.4 is complete, manually checked, and explicitly approved.
