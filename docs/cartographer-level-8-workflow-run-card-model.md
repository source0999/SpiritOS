# Cartographer Level 8 Workflow Run Card Model

status: implemented-model-only

Status date: 2026-05-20

## Purpose

Level 8.1 adds a workflow run card model. Cartographer may show a proposed sequence of visible steps, but it cannot approve, execute, retry, or write receipts for those steps.

This increment does not implement Level 8.2 step approval UI/API, Level 8.3 receipt journal, Level 8.4 stop/failure handling, Level 8.5 closeout smoke, or any Level 9 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 8.0 boundary: `docs/cartographer-level-8-workflow-runner-boundary-contract.md`.
- Level 7 closeout: `docs/cartographer-level-7-closeout-dashboard.md`.
- Service surface: `build_cartographer_level_8_workflow_run_card` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-8-workflow-run-card` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_8_workflow_run_card_models_steps_without_execution` and `test_level_8_workflow_run_card_stays_model_only_when_level_7_disabled` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 8.1 payload reports:

- `status: observing`.
- `level: 8`.
- `mode: workflow_run_card_model`.
- `contract_version: cartographer.level_8.workflow_run_card_model.v1`.
- `workflow_run_card_available: true`.
- `step_approval_contract_available: false`.
- `receipt_journal_available: false`.
- `background_execution_allowed: false`.
- `autonomous_retry_allowed: false`.
- `cross_project_mutation_allowed: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

Each workflow step must report:

- human approval required.
- not approved.
- `cartographer_may_execute: false`.
- actions taken false.
- receipt required before future execution.
- retry not allowed.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-8-workflow-run-card-model.md`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

## Forbidden Actions

- No execution.
- No background execution.
- No autonomous retry loops.
- No hidden receipt writes.
- No cross-project mutation.
- No push.
- No merge.
- No push queue creation.
- No branch creation.
- No worktree creation.
- No cleanup.
- No stash.
- No automatic commit.
- No automatic promotion.
- No self-approval.
- No Level 9 work.

## Expected Output

The workflow run card should show:

- a stable workflow id.
- visible step cards.
- per-step human approval requirement.
- per-step blocked or pending status.
- blockers for future unapproved increments.
- all mutation, execution, retry, and promotion flags false.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-8-workflow-run-card-model.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "model-only\|No background execution\|No autonomous retry loops\|cartographer_may_execute" docs/cartographer-level-8-workflow-run-card-model.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_workflow_run_card or level_7_closeout_dashboard or level_6_multi_project_closeout"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 8.1 safety terms.
- focused Level 8.1, Level 7 closeout, and Level 6 closeout tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no execution, background execution, retry loop, receipt write, push, branch, worktree, cleanup, stash, merge, automatic commit, promotion, self-approval, or Level 9 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-8-workflow-run-card-model.md`.
- revert `build_cartographer_level_8_workflow_run_card` and `_level_8_workflow_step_card` in `source_proxy/cartographer/service.py`.
- revert the Level 8.1 route in `source_proxy/api/cartographer.py`.
- revert the Level 8.1 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, receipts, or approval records.

## Next Increment

Level 8.2: Step Approval UI/API Contract.

Do not implement Level 8.2 until Level 8.1 is complete, manually checked, and explicitly approved.
