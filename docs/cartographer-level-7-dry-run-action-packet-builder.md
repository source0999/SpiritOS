# Cartographer Level 7 Dry-Run Action Packet Builder

status: implemented-dry-run-only

Status date: 2026-05-20

## Purpose

Level 7.3 adds a dry-run action packet builder for the Level 7 next safe action recommendation. Cartographer may package the recommendation into a human-readable packet with allowed files, forbidden actions, required approvals, manual checks, expected output, rollback notes, blockers, and evidence references.

This increment does not execute the packet. It does not add the Level 7.4 exact approval handshake, Level 7.5 closeout dashboard, or any Level 8 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Boundary contract: `docs/cartographer-level-7-autopilot-boundary-contract.md`.
- Level 7.1 flag: `docs/cartographer-level-7-disabled-by-default-feature-flag.md`.
- Level 7.2 recommendation: `docs/cartographer-level-7-next-safe-action-recommendation-contract.md`.
- Service surface: `build_cartographer_level_7_dry_run_action_packet` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-7-dry-run-action-packet` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_7_dry_run_action_packet_builds_preview_without_execution` and `test_level_7_dry_run_action_packet_stays_non_executing_when_flag_configured` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 7.3 payload reports:

- `status: observing`.
- `level: 7`.
- `mode: dry_run_action_packet_builder`.
- `contract_version: cartographer.level_7.dry_run_action_packet_builder.v1`.
- `dry_run_action_packet_builder_available: true`.
- `exact_approval_handshake_available: false`.
- `level_7_autopilot_action_available: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

The packet reports:

- `packet_id: cartographer.level_7.dry_run.next_safe_action_review.v1`.
- `packet_type: dry_run_action_packet`.
- `actions_taken: false`.
- `cartographer_may_execute: false`.
- `cartographer_may_self_approve: false`.
- `approval_handshake_available: false`.
- `execution_available: false`.
- allowed files.
- forbidden actions.
- required approvals.
- expected output.
- manual check commands.
- expected manual check result.
- rollback notes.
- blockers.
- evidence references.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-7-dry-run-action-packet-builder.md`
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
- No exact approval handshake execution.
- No Level 8 work.

## Expected Output

When Level 7 remains disabled by default, the dry-run packet should include blockers such as:

- `level_7_autopilot_disabled_by_default`.
- `level_7_action_authority_unavailable`.

When the Level 7 flag is configured in test scope, the packet may reflect the configured flag through the recommendation payload, but it must still report:

- `level_7_autopilot_action_available: false`.
- `actions_taken: false`.
- `cartographer_may_execute: false`.
- `cartographer_may_self_approve: false`.
- `approval_handshake_available: false`.
- `execution_available: false`.
- all mutation, promotion, and execution flags false.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-7-dry-run-action-packet-builder.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "dry-run-only\|No automatic execution\|No self-approval\|cartographer_may_execute" docs/cartographer-level-7-dry-run-action-packet-builder.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_dry_run_action_packet or level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 7.3 safety terms.
- focused Level 7.3, Level 7.2, Level 7.1, and Level 6 baseline tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no push, branch, worktree, cleanup, stash, merge, automatic commit, automatic execution, automatic promotion, self-approval, approval handshake execution, or packet execution occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-7-dry-run-action-packet-builder.md`.
- revert `build_cartographer_level_7_dry_run_action_packet` and `_level_7_dry_run_action_packet` in `source_proxy/cartographer/service.py`.
- revert the Level 7.3 route in `source_proxy/api/cartographer.py`.
- revert the Level 7.3 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, execution receipts, or approval records.

## Next Increment

Level 7.4: Exact Approval Handshake Contract.

Do not implement Level 7.4 until Level 7.3 is complete, manually checked, and explicitly approved.
