# Cartographer Level 8 Step Approval UI API Contract

status: implemented-preview-only

Status date: 2026-05-20

## Purpose

Level 8.2 adds a per-step approval preview contract for the Level 8 workflow run card. Cartographer may validate that a human supplied the exact workflow id, step id, step title, manual check commands, approval id, approver, and approval timestamp.

This increment does not execute approved steps. It does not add the Level 8.3 receipt journal, Level 8.4 stop/failure handling, Level 8.5 closeout smoke, or any Level 9 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 8.0 boundary: `docs/cartographer-level-8-workflow-runner-boundary-contract.md`.
- Level 8.1 workflow run card: `docs/cartographer-level-8-workflow-run-card-model.md`.
- Service surface: `build_cartographer_level_8_step_approval_preview` in `source_proxy/cartographer/service.py`.
- API surface: `POST /v1/cartographer/level-8-workflow-run-card/{workflow_id}/steps/{step_id}/approval-preview` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_8_step_approval_preview_validates_one_step_without_execution` and `test_level_8_step_approval_preview_blocks_self_approval_and_mismatches` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 8.2 payload reports:

- `status: approval_preview`.
- `level: 8`.
- `mode: step_approval_contract_preview`.
- `approval_version: cartographer.level_8.step_approval_contract_preview.v1`.
- `step_approval_contract_available: true`.
- `receipt_journal_available: false`.
- `execution_available: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `background_execution_allowed: false`.
- `autonomous_retry_allowed: false`.
- `cross_project_mutation_allowed: false`.

Even when `approval_preview_valid` is true, the step does not execute and no receipt is written.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-8-step-approval-contract.md`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

## Forbidden Actions

- No step execution.
- No background execution.
- No autonomous retry loops.
- No receipt journal writes.
- No cross-project mutation.
- No push.
- No merge.
- No branch creation.
- No worktree creation.
- No cleanup.
- No stash.
- No automatic commit.
- No automatic promotion.
- No self-approval.
- No Level 9 work.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-8-step-approval-contract.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "preview-only\|No background execution\|No autonomous retry loops\|execution_available: false" docs/cartographer-level-8-step-approval-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_step_approval or level_8_workflow_run_card or level_7_closeout_dashboard"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 8.2 safety terms.
- focused Level 8.2, Level 8.1, and Level 7 closeout tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no step execution, background execution, retry loop, receipt write, push, branch, worktree, cleanup, stash, merge, automatic commit, promotion, self-approval, or Level 9 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-8-step-approval-contract.md`.
- revert `build_cartographer_level_8_step_approval_preview` and `_level_8_step_approval_blockers` in `source_proxy/cartographer/service.py`.
- revert the Level 8.2 request model and route in `source_proxy/api/cartographer.py`.
- revert the Level 8.2 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, receipts, or approval records.

## Next Increment

Level 8.3: Receipt Journal And Evidence Trail.

Do not implement Level 8.3 until Level 8.2 is complete, manually checked, and explicitly approved.
