# Cartographer Level 10 Project Health Timeline

status: implemented-read-only-preview

Status date: 2026-05-20

## Purpose

Level 10.2 shows project health, blockers, evidence, and closeout history as an operator timeline.

The timeline is read-only. It may summarize repo health, dirty state, closeout history, evidence references, blockers, and the next approved planning gate, but it must not mutate evidence, alter repo state, clean up files, push, merge, execute actions, or promote any workflow.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 10.0 boundary: `docs/cartographer-level-10-production-operator-boundary-contract.md`.
- Level 10.1 polish plan: `docs/cartographer-level-10-operator-dashboard-polish-plan.md`.
- Level 9 closeout dashboard: `docs/cartographer-level-9-coordination-dashboard.md`.
- Service surface: `build_cartographer_level_10_project_health_timeline` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-10-project-health-timeline` in `source_proxy/api/cartographer.py`.
- Tests: `test_level_10_project_health_timeline_reports_read_only_evidence` and `test_level_10_project_health_timeline_clean_state_is_locked` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 10.2 payload reports:

- `status: observing`.
- `level: 10`.
- `mode: project_health_timeline`.
- `contract_version: cartographer.level_10.project_health_timeline.v1`.
- `timeline_available: true`.
- `read_only: true`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `background_mutation_allowed: false`.
- `hidden_writes_allowed: false`.
- `cleanup_allowed: false`.
- `push_allowed: false`.
- `merge_allowed: false`.
- `automatic_execution_allowed: false`.
- `automatic_promotion_allowed: false`.
- `evidence_mutation_allowed: false`.

Timeline entries may include:

- project id, name, root, status, and branch.
- dirty state, ahead count, behind count, and merge readiness.
- blockers and timeline state.
- blueprint health.
- evidence references.
- recommended next action.
- `mutation_allowed: false`.
- `actions_taken: false`.

Closeout history entries may include Level 9 closeout item titles, closeout status, blockers, and evidence references.

## Forbidden Actions

- No background mutation.
- No hidden writes.
- No evidence mutation.
- No cleanup.
- No push.
- No merge.
- No stash.
- No branch creation.
- No worktree creation.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 10.3 work without explicit approval.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_project_health_timeline or level_10_operator_dashboard_polish"
git status -sb
```

Expected outcome:

- diff check has no output.
- focused Level 10.2 timeline tests pass.
- timeline tests prove dirty and clean project states are reported without changing git status.
- timeline payload keeps write actions, authority, background mutation, hidden writes, cleanup, push, merge, automatic execution, automatic promotion, and evidence mutation disabled.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no cleanup, push, merge, automatic execution, automatic promotion, hidden write, or evidence mutation occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-10-project-health-timeline.md`.
- revert `build_cartographer_level_10_project_health_timeline` in `source_proxy/cartographer/service.py` if this increment's implementation needs to be backed out.
- revert the Level 10.2 route in `source_proxy/api/cartographer.py` if this increment's implementation needs to be backed out.
- revert the Level 10.2 focused tests in `source_proxy/tests/test_cartographer_api.py` if this increment's implementation needs to be backed out.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, evidence cleanup, or receipt cleanup should be needed because Level 10.2 is read-only.

## Next Increment

Level 10.3: Closeout Packet Generator.

Do not implement Level 10.3 until Level 10.2 is manually checked and explicitly approved.
