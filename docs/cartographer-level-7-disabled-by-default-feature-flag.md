# Cartographer Level 7 Disabled By Default Feature Flag

status: implemented-disabled

Status date: 2026-05-20

## Purpose

Level 7.1 adds a disabled-by-default feature flag surface for future limited autopilot work. The flag makes Level 7 state visible, but it does not grant action authority, execution authority, write authority, self-approval, or promotion.

This increment exists so later Level 7 work can check an explicit flag state before recommendations or dry-run packets are designed. It does not implement Level 7.2 recommendations, Level 7.3 dry-run action packets, Level 7.4 approval handshakes, or Level 7.5 closeout.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Boundary contract: `docs/cartographer-level-7-autopilot-boundary-contract.md`.
- Level 6 closeout baseline: `docs/cartographer-level-3-to-6-closeout-summary.md`.
- Service surface: `build_cartographer_level_7_disabled_by_default` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-7-disabled-by-default` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_7_disabled_by_default_feature_flag_is_locked_when_unset` and `test_level_7_feature_flag_does_not_create_action_authority_when_configured` in `source_proxy/tests/test_cartographer_api.py`.

## Feature Flag Contract

Flag names:

- `CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED`
- `CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH`

Default state:

- `CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED` defaults to false.
- `CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH` defaults to true.
- Level 7 action availability is always false in this increment.
- write actions are always false in this increment.
- actions taken are always false in this increment.

Configured state:

- tests may set `CARTOGRAPHER_LEVEL_7_AUTOPILOT_ENABLED=true`.
- tests may set `CARTOGRAPHER_LEVEL_7_AUTOPILOT_KILL_SWITCH=false`.
- configured state may report `level_7_autopilot_enabled: true`.
- configured state still reports `level_7_autopilot_action_available: false`.
- configured state still cannot execute, mutate, promote, or self-approve.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-7-disabled-by-default-feature-flag.md`
- `source_proxy/cartographer/autopilot_config.py`
- `source_proxy/cartographer/safety.py`
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
- No Level 7.2 recommendations.
- No Level 7.3 dry-run action packets.
- No Level 7.4 approval handshake execution.
- No Level 8 work.

## Expected Output

The Level 7.1 payload reports:

- `status: observing`.
- `level: 7`.
- `mode: disabled_by_default_feature_flag`.
- `contract_version: cartographer.level_7.disabled_by_default_feature_flag.v1`.
- default flag state is disabled.
- kill switch default is active.
- `level_7_autopilot_action_available: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- all mutation, promotion, and execution flags false.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-7-disabled-by-default-feature-flag.md source_proxy/cartographer/autopilot_config.py source_proxy/cartographer/safety.py source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "disabled-by-default\|No automatic execution\|No self-approval\|level_7_autopilot_action_available" docs/cartographer-level-7-disabled-by-default-feature-flag.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 7.1 safety terms.
- focused Level 7.1 and Level 6 baseline tests pass.
- git status shows this docs file and the approved minimal service/API/test/config files, plus unrelated pre-existing worktree changes.
- no push, branch, worktree, cleanup, stash, merge, automatic commit, automatic execution, automatic promotion, or self-approval occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-7-disabled-by-default-feature-flag.md`.
- revert the Level 7.1 additions in `source_proxy/cartographer/autopilot_config.py`.
- revert the Level 7.1 safety manifest keys in `source_proxy/cartographer/safety.py`.
- revert `build_cartographer_level_7_disabled_by_default` in `source_proxy/cartographer/service.py`.
- revert the Level 7.1 route in `source_proxy/api/cartographer.py`.
- revert the Level 7.1 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, or generated evidence.

## Next Increment

Level 7.2: Next Safe Action Recommendation Contract.

Do not implement Level 7.2 until Level 7.1 is complete, manually checked, and explicitly approved.
