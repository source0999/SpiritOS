# Cartographer Level 8 Closeout Smoke

status: implemented-closeout-preview

Status date: 2026-05-20

## Purpose

Level 8.5 adds a closeout smoke for the approved workflow runner. Cartographer may summarize the workflow run card, step approval preview, receipt journal preview, and fail-closed stop handling, but it cannot execute steps or start Level 9.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 8.0 boundary: `docs/cartographer-level-8-workflow-runner-boundary-contract.md`.
- Level 8.1 workflow run card: `docs/cartographer-level-8-workflow-run-card-model.md`.
- Level 8.2 step approval: `docs/cartographer-level-8-step-approval-contract.md`.
- Level 8.3 receipt journal: `docs/cartographer-level-8-receipt-journal-evidence-trail.md`.
- Level 8.4 stop handling: `docs/cartographer-level-8-cancel-stop-failed-step-handling.md`.
- Service surface: `build_cartographer_level_8_closeout_smoke` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-8-closeout-smoke` in `source_proxy/api/cartographer.py`.

## Contract

The Level 8.5 payload reports:

- `status: observing`.
- `level: 8`.
- `mode: level_8_closeout_smoke`.
- `contract_version: cartographer.level_8.closeout_smoke.v1`.
- `level_8_closed_out`.
- `level_9_gated: true`.
- `level_9_may_begin: false`.
- `operator_approval_required_for_level_9: true`.
- `execution_available: false`.
- `background_execution_allowed: false`.
- `autonomous_retry_allowed: false`.
- `cross_project_mutation_allowed: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

## Forbidden Actions

- No Level 9 work without explicit approval.
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

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-8-closeout-smoke.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "closeout-preview\|No background execution\|No autonomous retry loops\|level_9_may_begin: false" docs/cartographer-level-8-closeout-smoke.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_closeout_smoke or level_8_cancel_stop_failed_step or level_8_receipt_journal or level_8_step_approval or level_8_workflow_run_card"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 8.5 safety terms.
- focused Level 8.5 through Level 8.1 tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no Level 9 work, step execution, background execution, retry loop, receipt write, push, branch, worktree, cleanup, stash, merge, automatic commit, promotion, or self-approval occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-8-closeout-smoke.md`.
- revert `build_cartographer_level_8_closeout_smoke` and `_level_8_closeout_item` in `source_proxy/cartographer/service.py`.
- revert the Level 8.5 route in `source_proxy/api/cartographer.py`.
- revert the Level 8.5 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 9.0: Multi-Worker Boundary Contract.

Do not implement Level 9.0 until Level 8.5 is complete, manually checked, and explicitly approved.
