# Cartographer Level 10 Run History And Evidence Browser

status: implemented-read-only-browser

Status date: 2026-05-20

## Purpose

Level 10.4 browses prior manual checks, run results, closeout packet previews, and evidence links without changing them.

The browser is read-only. It may summarize run history, closeout packet previews, evidence artifacts, and provenance, but it must not edit evidence, create receipts, append run history, clean up files, push, merge, execute actions, or promote any workflow.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 10.0 boundary: `docs/cartographer-level-10-production-operator-boundary-contract.md`.
- Level 10.2 timeline: `docs/cartographer-level-10-project-health-timeline.md`.
- Level 10.3 closeout packet generator: `docs/cartographer-level-10-closeout-packet-generator.md`.
- Service surface: `build_cartographer_level_10_run_history_evidence_browser` in `source_proxy/cartographer/service.py`.
- API surface: `GET /v1/cartographer/level-10-run-history-evidence` in `source_proxy/api/cartographer.py`.
- Tests: `test_level_10_run_history_evidence_browser_reads_without_mutation` and `test_level_10_run_history_evidence_browser_handles_empty_evidence` in `source_proxy/tests/test_cartographer_api.py`.

## Contract

The Level 10.4 payload reports:

- `status: observing`.
- `level: 10`.
- `mode: run_history_evidence_browser`.
- `contract_version: cartographer.level_10.run_history_evidence_browser.v1`.
- `browser_available: true`.
- `read_only: true`.
- `write_actions_enabled: false`.
- `authority_granted: false`.
- `actions_taken: false`.
- `run_history_mutation_allowed: false`.
- `receipt_creation_allowed: false`.
- `evidence_mutation_allowed: false`.
- `hidden_writes_allowed: false`.
- `background_mutation_allowed: false`.
- `cleanup_allowed: false`.
- `push_allowed: false`.
- `merge_allowed: false`.
- `automatic_execution_allowed: false`.
- `automatic_promotion_allowed: false`.

Browser entries may include:

- run ids, source names, status, manual checks, packet counts, and project counts.
- evidence task ids, artifact paths, safety verdicts, recommendations, changed files, components, and risk.
- closeout packet previews from Level 10.3.
- provenance describing which local read-only builders supplied the data.

## Forbidden Actions

- No evidence mutation.
- No hidden writes.
- No receipt creation.
- No run history mutation.
- No cleanup.
- No push.
- No merge.
- No stash.
- No branch creation.
- No worktree creation.
- No background mutation.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 10.5 work without explicit approval.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_run_history_evidence_browser or level_10_closeout_packet_generator"
git status -sb
```

Expected outcome:

- diff check has no output.
- focused Level 10.4 and Level 10.3 tests pass.
- tests prove browsing does not edit evidence, create receipts, or alter run history.
- browser payload keeps evidence mutation, hidden writes, receipt creation, run history mutation, cleanup, push, merge, background mutation, automatic execution, and automatic promotion disabled.
- git status shows this docs file and the approved minimal service/API/test files, plus unrelated pre-existing worktree changes.
- no evidence mutation, receipt creation, cleanup, push, merge, background mutation, automatic execution, or automatic promotion occurred.

## Rollback Notes

Rollback is limited to this increment:

- remove `docs/cartographer-level-10-run-history-evidence-browser.md`.
- revert `build_cartographer_level_10_run_history_evidence_browser` in `source_proxy/cartographer/service.py`.
- revert the Level 10.4 route in `source_proxy/api/cartographer.py`.
- revert the Level 10.4 focused tests in `source_proxy/tests/test_cartographer_api.py`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, evidence cleanup, receipt cleanup, or run history cleanup should be needed because Level 10.4 is read-only.

## Next Increment

Level 10.5: Scout And Blueprint Handoff Preview.

Do not implement Level 10.5 until Level 10.4 is manually checked and explicitly approved.
