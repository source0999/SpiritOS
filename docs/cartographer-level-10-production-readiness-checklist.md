# Cartographer Level 10 Production Readiness Checklist

status: implemented-fail-closed-checklist

Status date: 2026-05-21

## Purpose

Level 10.6 verifies operator-mode readiness, explainability, rollback, audit path, safety gates, and known limitations.

The checklist is read-only and fail-closed. It may report readiness from existing Level 10 preview surfaces, but it must block production operator readiness when any safety, audit, rollback, explainability, or known-limitation requirement is missing.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 10.0 boundary: `docs/cartographer-level-10-production-operator-boundary-contract.md`.
- Level 10.5 handoff preview: `docs/cartographer-level-10-scout-blueprint-handoff-preview.md`.
- Service surface: `build_cartographer_level_10_production_readiness_checklist` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-10-production-readiness-checklist` in `source_proxy/api/cartographer.py`.
- Tests: `test_level_10_production_readiness_checklist_fails_closed_with_blockers` and `test_level_10_production_readiness_checklist_remains_explainable_when_ready` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 10.6 payload reports:

- `status: observing`.
- `level: 10`.
- `mode: production_readiness_checklist`.
- `contract_version: cartographer.level_10.production_readiness_checklist.v1`.
- `readiness_checklist_available: true`.
- `production_operator_ready`.
- `fail_closed: true`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `hidden_autonomy_allowed: false`.
- `background_mutation_allowed: false`.
- `cleanup_allowed: false`.
- `push_allowed: false`.
- `merge_allowed: false`.
- `automatic_execution_allowed: false`.
- `automatic_promotion_allowed: false`.
- `new_levels_allowed: false`.

## Checklist Shape

Checklist entries include:

- check id.
- status.
- passed flag.
- evidence.
- `operator_explainable: true`.
- `rollback_path_required: true`.
- `audit_path_required: true`.
- `actions_taken: false`.

The checklist must fail closed when blockers are present and must remain explainable to a human operator when all checks are ready.

## Forbidden Actions

- No hidden autonomy.
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
- No new levels.
- No Level 10.7 work without explicit approval.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_production_readiness_checklist or level_10_scout_blueprint_handoff_preview"
git status -sb
```

## Expected Outcome

- diff check has no output.
- focused Level 10.6 and Level 10.5 tests pass.
- tests prove readiness fails closed when blockers exist.
- tests prove readiness remains explainable when checks are ready.
- payload keeps hidden autonomy, background mutation, cleanup, push, merge, automatic execution, automatic promotion, and new levels disabled.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no cleanup, push, merge, branch creation, worktree creation, automatic execution, automatic promotion, self-approval, or new level creation occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-10-production-readiness-checklist.md`.
- revert `build_cartographer_level_10_production_readiness_checklist` and `_level_10_readiness_check` in `source_proxy/cartographer/service.py`.
- revert the Level 10.6 route in `source_proxy/api/cartographer.py`.
- revert the Level 10.6 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, evidence cleanup, receipt cleanup, run history cleanup, Scout cleanup, or blueprint cleanup should be needed because Level 10.6 is read-only.

## Next Increment

Level 10.7: Level 10 Closeout And Next-Roadmap Gate.

Do not implement Level 10.7 until Level 10.6 is manually checked and explicitly approved.
