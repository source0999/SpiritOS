# Cartographer Level 8 Receipt Journal And Evidence Trail

status: implemented-preview-only

Status date: 2026-05-20

## Purpose

Level 8.3 adds a visible receipt journal and evidence trail preview. Cartographer may model journal entries for proposed workflows and step approval previews, but it cannot write receipts, hide receipts, execute steps, retry steps, or mutate project state.

This increment does not implement Level 8.4 cancel/stop/failed-step handling, Level 8.5 closeout smoke, or any Level 9 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 8.0 boundary: `docs/cartographer-level-8-workflow-runner-boundary-contract.md`.
- Level 8.1 workflow run card: `docs/cartographer-level-8-workflow-run-card-model.md`.
- Level 8.2 step approval: `docs/cartographer-level-8-step-approval-contract.md`.
- Service surface: `build_cartographer_level_8_receipt_journal` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-8-receipt-journal` in `source_proxy/api/cartographer.py`.
- Focused tests: `test_level_8_receipt_journal_models_visible_evidence_without_writes` and `test_level_8_receipt_journal_stays_preview_when_step_approval_is_valid` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 8.3 payload reports:

- `status: observing`.
- `level: 8`.
- `mode: receipt_journal_evidence_trail`.
- `contract_version: cartographer.level_8.receipt_journal_evidence_trail.v1`.
- `receipt_journal_available: true`.
- `receipt_journal_write_allowed: false`.
- `hidden_receipt_writes_allowed: false`.
- `execution_available: false`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `background_execution_allowed: false`.
- `autonomous_retry_allowed: false`.
- `cross_project_mutation_allowed: false`.

Each journal entry must be visible to the operator, preview-only, not persisted, not hidden, non-executing, and backed by evidence references.

## Allowed Files

This increment is limited to:

- `docs/cartographer-level-8-receipt-journal-evidence-trail.md`
- `source_proxy/cartographer/service.py`
- `source_proxy/api/cartographer.py`
- `source_proxy/tests/test_cartographer_api.py`

## Forbidden Actions

- No receipt journal writes.
- No hidden receipt writes.
- No step execution.
- No background execution.
- No autonomous retry loops.
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
git diff --check -- docs/cartographer-level-8-receipt-journal-evidence-trail.md source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py
grep -n "preview-only\|No hidden receipt writes\|No background execution\|receipt_journal_write_allowed: false" docs/cartographer-level-8-receipt-journal-evidence-trail.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_receipt_journal or level_8_step_approval or level_8_workflow_run_card"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 8.3 safety terms.
- focused Level 8.3, Level 8.2, and Level 8.1 tests pass.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no receipt write, hidden receipt write, step execution, background execution, retry loop, push, branch, worktree, cleanup, stash, merge, automatic commit, promotion, self-approval, or Level 9 work occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-8-receipt-journal-evidence-trail.md`.
- revert `build_cartographer_level_8_receipt_journal` and `_level_8_receipt_journal_entry` in `source_proxy/cartographer/service.py`.
- revert the Level 8.3 route in `source_proxy/api/cartographer.py`.
- revert the Level 8.3 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup should be needed because this increment does not create branches, worktrees, commits, push queues, stashes, generated evidence, persisted receipts, or approval records.

## Next Increment

Level 8.4: Cancel, Stop, And Failed-Step Handling.

Do not implement Level 8.4 until Level 8.3 is complete, manually checked, and explicitly approved.
