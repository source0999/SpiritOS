# Cartographer Level 10 Closeout Packet Generator

status: implemented-preview-only

Status date: 2026-05-20

## Purpose

Level 10.3 generates human-reviewable closeout packet previews from existing status, evidence references, manual checks, blockers, and project health timeline data.

The generator is preview-only. It may assemble closeout packet candidates for human review, but it must not finalize records, promote workflows, write evidence, clean up files, push, merge, or mutate repo state.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 10.0 boundary: `docs/cartographer-level-10-production-operator-boundary-contract.md`.
- Level 10.1 polish plan: `docs/cartographer-level-10-operator-dashboard-polish-plan.md`.
- Level 10.2 timeline: `docs/cartographer-level-10-project-health-timeline.md`.
- Service surface: `build_cartographer_level_10_closeout_packet_generator` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-10-closeout-packets` in `source_proxy/api/cartographer.py`.
- Tests: `test_level_10_closeout_packet_generator_creates_previews_without_mutation` and `test_level_10_closeout_packet_generator_clean_state_still_does_not_finalize` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 10.3 payload reports:

- `status: observing`.
- `level: 10`.
- `mode: closeout_packet_generator`.
- `contract_version: cartographer.level_10.closeout_packet_generator.v1`.
- `closeout_packet_generator_available: true`.
- `preview_only: true`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `packet_finalization_allowed: false`.
- `automatic_closeout_allowed: false`.
- `automatic_promotion_allowed: false`.
- `hidden_evidence_writes_allowed: false`.
- `evidence_mutation_allowed: false`.
- `background_mutation_allowed: false`.
- `cleanup_allowed: false`.
- `push_allowed: false`.
- `merge_allowed: false`.

Packet previews may include:

- packet id and source.
- project id, name, root, branch, and timeline state.
- preview status.
- blockers.
- evidence references.
- recommended next action.
- `finalized: false`.
- `persisted: false`.
- `promoted: false`.
- `evidence_written: false`.
- `actions_taken: false`.

## Forbidden Actions

- No automatic closeout.
- No packet finalization.
- No automatic promotion.
- No hidden evidence writes.
- No evidence mutation.
- No cleanup.
- No push.
- No merge.
- No stash.
- No branch creation.
- No worktree creation.
- No background mutation.
- No automatic execution.
- No self-approval.
- No Level 10.4 work without explicit approval.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_closeout_packet_generator or level_10_project_health_timeline"
git status -sb
```

Expected outcome:

- diff check has no output.
- focused Level 10.3 and Level 10.2 tests pass.
- tests prove packet previews are generated without changing git status.
- packet previews remain unfinalized, unpersisted, unpromoted, and evidence-write disabled.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no automatic closeout, promotion, hidden evidence write, cleanup, push, merge, background mutation, or automatic execution occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-10-closeout-packet-generator.md`.
- revert `build_cartographer_level_10_closeout_packet_generator` and `_level_10_closeout_packet_preview` in `source_proxy/cartographer/service.py`.
- revert the Level 10.3 route in `source_proxy/api/cartographer.py`.
- revert the Level 10.3 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, evidence cleanup, receipt cleanup, or promotion cleanup should be needed because Level 10.3 is preview-only.

## Next Increment

Level 10.4: Run History And Evidence Browser.

Do not implement Level 10.4 until Level 10.3 is manually checked and explicitly approved.
