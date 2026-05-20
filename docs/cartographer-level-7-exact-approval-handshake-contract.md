# Cartographer Level 7 Exact Approval Handshake Contract

status: implemented-preview-only

Status date: 2026-05-20

## Purpose

Level 7.4 adds an exact approval handshake preview for the Level 7 dry-run action packet. Cartographer may validate that a human supplied the exact packet id, allowed files, forbidden actions, manual check commands, approval id, approver, and approval timestamp.

This increment does not execute an approved packet. It does not allow self-approval, automatic execution, automatic promotion, commit, push, branch creation, worktree creation, cleanup, stash, merge, or Level 8 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Boundary contract: `docs/cartographer-level-7-autopilot-boundary-contract.md`.
- Level 7.1 flag: `docs/cartographer-level-7-disabled-by-default-feature-flag.md`.
- Level 7.2 recommendation: `docs/cartographer-level-7-next-safe-action-recommendation-contract.md`.
- Level 7.3 dry-run packet: `docs/cartographer-level-7-dry-run-action-packet-builder.md`.
- Service surface: `build_cartographer_level_7_exact_approval_handshake` in `source_proxy/cartographer/service.py`.
- API surface: `POST /v1/cartographer/level-7-dry-run-action-packet/{packet_id}/approval-preview` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_7_exact_approval_handshake_validates_preview_without_execution` and `test_level_7_exact_approval_handshake_blocks_self_approval_and_mismatches` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 7.4 payload reports:

- `status: approval_preview`.
- `level: 7`.
- `mode: exact_approval_handshake_preview`.
- `approval_version: cartographer.level_7.exact_approval_handshake_preview.v1`.
- `approval_handshake_available: true`.
- `execution_available: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `automatic_execution_allowed: false`.
- `self_approval_allowed: false`.

The preview validates:

- exact packet id.
- approval id is present.
- approved by is present.
- approved at is present.
- exact allowed files match the packet.
- exact forbidden actions match the packet.
- exact manual check commands match the packet.
- self-approval is blocked.

Even when `approval_preview_valid` is true, execution remains unavailable through `execution_available: false` and `execution_blockers: ["level_7_execution_not_implemented"]`.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-7-exact-approval-handshake-contract.md`
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
- No Level 8 work.

## Expected Output

For an exact non-self approval preview:

- approval shape can validate.
- execution still remains unavailable.
- all mutation, promotion, and execution flags remain false.

For a self-approval or mismatched preview:

- `approval_preview_valid` is false.
- blockers explain the missing or mismatched fields.
- `self_approval_blocked` is present when the approver is Cartographer, Codex, or `cartographer-ui`.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-7-exact-approval-handshake-contract.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "preview-only\|No automatic execution\|No self-approval\|execution_available: false" docs/cartographer-level-7-exact-approval-handshake-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_exact_approval_handshake or level_7_dry_run_action_packet or level_7_next_safe_action or level_7_disabled_by_default or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 7.4 safety terms.
- focused Level 7.4, Level 7.3, Level 7.2, Level 7.1, and Level 6 baseline tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no push, branch, worktree, cleanup, stash, merge, automatic commit, automatic execution, automatic promotion, self-approval, or packet execution occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-7-exact-approval-handshake-contract.md`.
- revert `build_cartographer_level_7_exact_approval_handshake`, `_level_7_exact_approval_blockers`, and `_level_7_is_self_approval` in `source_proxy/cartographer/service.py`.
- revert the Level 7.4 request model and route in `source_proxy/api/cartographer.py`.
- revert the Level 7.4 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, execution receipts, or approval records.

## Next Increment

Level 7.5: Level 7 Closeout Dashboard.

Do not implement Level 7.5 until Level 7.4 is complete, manually checked, and explicitly approved.
