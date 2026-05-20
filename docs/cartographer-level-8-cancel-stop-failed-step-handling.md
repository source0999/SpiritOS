# Cartographer Level 8 Cancel Stop And Failed-Step Handling

status: implemented-preview-only

Status date: 2026-05-20

## Purpose

Level 8.4 adds fail-closed cancel, stop, and failed-step handling previews. Cartographer may model canceled, failed, and blocked workflow states, but it cannot continue workflows, retry steps, execute steps, or write receipts.

This increment does not implement Level 8.5 closeout smoke or any Level 9 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 8.0 boundary: `docs/cartographer-level-8-workflow-runner-boundary-contract.md`.
- Level 8.1 workflow run card: `docs/cartographer-level-8-workflow-run-card-model.md`.
- Level 8.2 step approval: `docs/cartographer-level-8-step-approval-contract.md`.
- Level 8.3 receipt journal: `docs/cartographer-level-8-receipt-journal-evidence-trail.md`.
- Service surface: `build_cartographer_level_8_stop_failure_handling` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-8-stop-failure-handling` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_8_cancel_stop_failed_step_handling_fails_closed_without_execution` and `test_level_8_cancel_stop_failed_step_handling_does_not_write_receipts` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 8.4 payload reports:

- `status: observing`.
- `level: 8`.
- `mode: cancel_stop_failed_step_handling`.
- `contract_version: cartographer.level_8.cancel_stop_failed_step_handling.v1`.
- `stop_handling_available: true`.
- `execution_available: false`.
- `workflow_continuation_allowed: false`.
- `human_review_required_to_continue: true`.
- `background_execution_allowed: false`.
- `autonomous_retry_allowed: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.

Canceled, failed, and blocked step states must all report:

- workflow stopped.
- later steps unapproved.
- human review required.
- continuation not allowed.
- retry not allowed.
- autonomous retry not allowed.
- background execution not allowed.
- actions taken false.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-8-cancel-stop-failed-step-handling.md`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

## Forbidden Actions

- No workflow continuation without human review.
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
git diff --check -- docs/cartographer-level-8-cancel-stop-failed-step-handling.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "preview-only\|No background execution\|No autonomous retry loops\|workflow_continuation_allowed: false" docs/cartographer-level-8-cancel-stop-failed-step-handling.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_cancel_stop_failed_step or level_8_receipt_journal or level_8_step_approval"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 8.4 safety terms.
- focused Level 8.4, Level 8.3, and Level 8.2 tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no workflow continuation, step execution, background execution, retry loop, receipt write, push, branch, worktree, cleanup, stash, merge, automatic commit, promotion, self-approval, or Level 9 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-8-cancel-stop-failed-step-handling.md`.
- revert `build_cartographer_level_8_stop_failure_handling` and `_level_8_stopped_state` in `source_proxy/cartographer/service.py`.
- revert the Level 8.4 route in `source_proxy/api/cartographer.py`.
- revert the Level 8.4 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 8.5: Level 8 Closeout Smoke.

Do not implement Level 8.5 until Level 8.4 is complete, manually checked, and explicitly approved.
