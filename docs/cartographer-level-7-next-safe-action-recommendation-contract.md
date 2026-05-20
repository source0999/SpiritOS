# Cartographer Level 7 Next Safe Action Recommendation Contract

status: implemented-recommendation-only

Status date: 2026-05-20

## Purpose

Level 7.2 adds a recommendation-only next safe action contract. Cartographer may explain the next safe human action based on the Level 7 disabled state and Level 6 closeout blockers, but it cannot execute the action, create dry-run packets, approve itself, promote itself, or mutate the repo.

This increment does not implement Level 7.3 dry-run action packets, Level 7.4 approval handshakes, Level 7.5 closeout, or any Level 8 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Boundary contract: `docs/cartographer-level-7-autopilot-boundary-contract.md`.
- Level 7.1 flag: `docs/cartographer-level-7-disabled-by-default-feature-flag.md`.
- Service surface: `build_cartographer_level_7_next_safe_action` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-7-next-safe-action` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_7_next_safe_action_recommends_human_review_without_execution` and `test_level_7_next_safe_action_stays_non_executing_when_flag_configured` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 7.2 payload reports:

- `status: observing`.
- `level: 7`.
- `mode: next_safe_action_recommendation`.
- `contract_version: cartographer.level_7.next_safe_action_recommendation.v1`.
- `recommendation_only: true`.
- `recommendation_contract_available: true`.
- `dry_run_action_packet_builder_available: false`.
- `exact_approval_handshake_available: false`.
- `level_7_autopilot_action_available: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

The recommendation must explain whether the next human action is blocked or available for human review. It must cite evidence and blockers. It must never imply that Cartographer can execute the action.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-7-next-safe-action-recommendation-contract.md`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

## Forbidden Actions

- No push.
- No push queue creation.
- No branch creation.
- No worktree creation.
- No cleanup.
- No stash.
- No merge.
- No automatic commit.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No dry-run action packet creation.
- No exact approval handshake execution.
- No Level 8 work.

## Expected Output

When Level 7 remains disabled by default, the payload should recommend human review and include blockers such as:

- `level_7_autopilot_disabled_by_default`.
- `level_7_action_authority_unavailable`.

When the Level 7 flag is configured in test scope, the payload may report `level_7_autopilot_enabled: true`, but it must still report:

- `level_7_autopilot_action_available: false`.
- `cartographer_may_execute: false`.
- `cartographer_may_create_dry_run_packet: false`.
- all mutation, promotion, and execution flags false.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-7-next-safe-action-recommendation-contract.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "recommendation-only\|No automatic execution\|No self-approval\|cartographer_may_execute" docs/cartographer-level-7-next-safe-action-recommendation-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 7.2 safety terms.
- focused Level 7.2, Level 7.1, and Level 6 baseline tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no push, branch, worktree, cleanup, stash, merge, automatic commit, automatic execution, automatic promotion, self-approval, or dry-run packet creation occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-7-next-safe-action-recommendation-contract.md`.
- revert `build_cartographer_level_7_next_safe_action` and its helpers in `source_proxy/cartographer/service.py`.
- revert the Level 7.2 route in `source_proxy/api/cartographer.py`.
- revert the Level 7.2 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, dry-run action packets, or execution receipts.

## Next Increment

Level 7.3: Dry-Run Action Packet Builder.

Do not implement Level 7.3 until Level 7.2 is complete, manually checked, and explicitly approved.
