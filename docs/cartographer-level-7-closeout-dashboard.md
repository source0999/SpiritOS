# Cartographer Level 7 Closeout Dashboard

status: implemented-closeout-preview

Status date: 2026-05-20

## Purpose

Level 7.5 adds a closeout dashboard for Level 7 limited autopilot. It summarizes the disabled-by-default flag, next-safe-action recommendation, dry-run action packet, and exact approval handshake preview.

This increment does not start Level 8. It keeps Level 8 gated until explicit human approval.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Boundary contract: `docs/cartographer-level-7-autopilot-boundary-contract.md`.
- Level 7.1 flag: `docs/cartographer-level-7-disabled-by-default-feature-flag.md`.
- Level 7.2 recommendation: `docs/cartographer-level-7-next-safe-action-recommendation-contract.md`.
- Level 7.3 dry-run packet: `docs/cartographer-level-7-dry-run-action-packet-builder.md`.
- Level 7.4 handshake preview: `docs/cartographer-level-7-exact-approval-handshake-contract.md`.
- Service surface: `build_cartographer_level_7_closeout_dashboard` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-7-closeout-dashboard` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_7_closeout_dashboard_summarizes_safe_preview_surfaces` and `test_level_7_closeout_dashboard_keeps_level_8_blocked_when_disabled` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 7.5 payload reports:

- `status: observing`.
- `level: 7`.
- `mode: level_7_closeout_dashboard`.
- `contract_version: cartographer.level_7.closeout_dashboard.v1`.
- `level_7_closed_out`.
- `level_8_gated: true`.
- `level_8_may_begin: false`.
- `operator_approval_required_for_level_8: true`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `automatic_execution_allowed: false`.
- `automatic_promotion_allowed: false`.
- `self_approval_allowed: false`.

The dashboard closes out Level 7 only as a human-reviewable preview stack. It does not authorize Level 8, execution, mutation, promotion, or self-approval.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-7-closeout-dashboard.md`
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
- No packet execution.
- No Level 8 work without explicit approval.

## Expected Output

The closeout dashboard should show:

- Level 7.1 is locked to disabled-by-default state and action availability remains false.
- Level 7.2 is recommendation-only.
- Level 7.3 is dry-run-only and packet `actions_taken` is false.
- Level 7.4 is approval-preview-only and execution remains unavailable.
- Level 8 is gated and may not begin without explicit human approval.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-7-closeout-dashboard.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "closeout-preview\|No automatic execution\|No self-approval\|level_8_may_begin: false" docs/cartographer-level-7-closeout-dashboard.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_closeout_dashboard or level_7_exact_approval_handshake or level_7_dry_run_action_packet or level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 7.5 safety terms.
- focused Level 7.5, Level 7.4, Level 7.3, Level 7.2, Level 7.1, and Level 6 baseline tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no push, branch, worktree, cleanup, stash, merge, automatic commit, automatic execution, automatic promotion, self-approval, packet execution, or Level 8 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-7-closeout-dashboard.md`.
- revert `build_cartographer_level_7_closeout_dashboard` and `_level_7_closeout_item` in `source_proxy/cartographer/service.py`.
- revert the Level 7.5 route in `source_proxy/api/cartographer.py`.
- revert the Level 7.5 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, execution receipts, or approval records.

## Next Increment

Level 8.0: Workflow Runner Boundary Contract.

Do not implement Level 8.0 until Level 7.5 is complete, manually checked, and explicitly approved.
