# Cartographer Level 10 Scout And Blueprint Handoff Preview

status: implemented-preview-only

Status date: 2026-05-21

## Purpose

Level 10.5 previews Scout and blueprint handoff context for operator decisions without writing to Scout, proxy memory, coding context, or blueprint files.

The handoff is preview-only. It may summarize source references, blockers, blueprint inventory, and provenance for human review, but it must not write Scout files, proxy memory, coding context, blueprints, evidence, receipts, or run history.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 10.0 boundary: `docs/cartographer-level-10-production-operator-boundary-contract.md`.
- Level 10.4 run history and evidence browser: `docs/cartographer-level-10-run-history-evidence-browser.md`.
- Service surface: `build_cartographer_level_10_scout_blueprint_handoff_preview` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-10-scout-blueprint-handoff-preview` in `source_proxy/api/cartographer.py`.
- Tests: `test_level_10_scout_blueprint_handoff_preview_does_not_write_context` and `test_level_10_scout_blueprint_handoff_preview_blocks_empty_sources_without_writes` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 10.5 payload reports:

- `status: observing`.
- `level: 10`.
- `mode: scout_blueprint_handoff_preview`.
- `contract_version: cartographer.level_10.scout_blueprint_handoff_preview.v1`.
- `handoff_preview_available: true`.
- `preview_only: true`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `scout_writes_allowed: false`.
- `proxy_memory_writes_allowed: false`.
- `coding_context_writes_allowed: false`.
- `blueprint_writes_allowed: false`.
- `evidence_writes_allowed: false`.
- `receipt_creation_allowed: false`.
- `run_history_mutation_allowed: false`.
- `background_mutation_allowed: false`.
- `cleanup_allowed: false`.
- `push_allowed: false`.
- `merge_allowed: false`.
- `stash_allowed: false`.
- `branch_creation_allowed: false`.
- `worktree_creation_allowed: false`.
- `automatic_execution_allowed: false`.
- `automatic_promotion_allowed: false`.
- `self_approval_allowed: false`.

## Handoff Preview Shape

Handoff preview entries may include:

- handoff id and target.
- source references.
- source count.
- blockers.
- provenance from the run history browser and blueprint inventory.
- `preview_only: true`.
- `writes_allowed: false`.
- `actions_taken: false`.

## Forbidden Actions

- No Scout writes.
- No proxy memory writes.
- No coding context writes.
- No blueprint writes.
- No evidence writes.
- No receipt creation.
- No run history mutation.
- No background mutation.
- No cleanup.
- No push.
- No merge.
- No stash.
- No branch creation.
- No worktree creation.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 10.6 work without explicit approval.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_scout_blueprint_handoff_preview or level_10_run_history_evidence_browser"
git status -sb
```

## Expected Outcome

- diff check has no output.
- focused Level 10.5 and Level 10.4 tests pass.
- tests prove handoff output is preview-only and does not write to Scout, proxy memory, coding context, blueprints, evidence, receipts, or run history.
- payload keeps Scout writes, proxy memory writes, coding context writes, blueprint writes, background mutation, cleanup, push, merge, automatic execution, and automatic promotion disabled.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no Scout write, blueprint write, context write, evidence write, cleanup, push, merge, background mutation, automatic execution, or automatic promotion occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-10-scout-blueprint-handoff-preview.md`.
- revert `build_cartographer_level_10_scout_blueprint_handoff_preview` in `source_proxy/cartographer/service.py`.
- revert the Level 10.5 route in `source_proxy/api/cartographer.py`.
- revert the Level 10.5 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, evidence cleanup, receipt cleanup, run history cleanup, Scout cleanup, or blueprint cleanup should be needed because Level 10.5 is preview-only.

## Next Increment

Level 10.6: Level 10 Production Readiness Checklist.

Do not implement Level 10.6 until Level 10.5 is manually checked and explicitly approved.
