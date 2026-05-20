# Cartographer Level 10 Operator Dashboard Polish Plan

status: planning-only

Status date: 2026-05-20

## Purpose

Level 10.1 plans operator dashboard polish for daily scanning, blocker review, evidence review, closeout awareness, and next-step planning.

This increment is planning-only. It does not implement UI changes, service changes, API changes, tests, runtime behavior, project health timelines, closeout packet generation, run history browsing, Scout or Blueprint handoff work, production readiness checks, or Level 10.2 work.

## Source Of Truth

- Roadmap: `docs/cartographer-level-7-to-10-autopilot-plan.md`.
- Level 10.0 boundary: `docs/cartographer-level-10-production-operator-boundary-contract.md`.
- Level 9 closeout dashboard: `docs/cartographer-level-9-coordination-dashboard.md`.
- Existing Level 9 service surface: `build_cartographer_level_9_coordination_dashboard` in `source_proxy/cartographer/service.py`.
- Existing Level 9 API surface: `GET /v1/cartographer/level-9-coordination-dashboard` in `source_proxy/api/cartographer.py`.

The Level 10.0 boundary defines production operator mode as command-center visibility and gated planning. Level 10.1 must preserve that boundary.

## Dashboard Polish Goals

The future operator dashboard should help a human operator answer five questions quickly:

- What is the current Cartographer level and closeout state?
- What blockers need attention before the next increment?
- What evidence or manual checks support the current state?
- What action is recommended next, and why is it safe?
- Which actions remain forbidden or gated?

The dashboard should make safety state visible before it makes next-step recommendations prominent.

## Proposed Operator Sections

Future UI polish may organize the dashboard into these sections:

- Level status: current level, current increment, closeout status, and next permission gate.
- Safety boundary: disabled autonomy, forbidden actions, and executor gate status.
- Blockers: unresolved blockers, stale worker indicators, dirty tree warnings, and conflict summaries.
- Evidence: latest focused checks, relevant docs, route names, service functions, and receipt previews.
- Next step: one recommended next increment or action preview, with required approval language.
- Rollback: concise rollback notes for the current increment.

These sections are display and planning surfaces. They do not imply write authority.

## Non-Mutating Interaction Rules

Future polish may add navigation, filtering, sorting, compact cards, status labels, or evidence links.

Future polish must not add:

- hidden autonomy.
- background mutation.
- automatic execution.
- automatic promotion.
- automatic retries.
- push.
- merge.
- cleanup.
- stash.
- branch creation.
- worktree creation.
- cross-project mutation.
- self-approval.

Every future operator control that could affect repo state must begin as a proposal, preview, or dry-run before execution is considered.

## Acceptance Criteria For Later Implementation

If Level 10.1 implementation is later approved, it should be considered acceptable only when:

- the dashboard remains explainable to a human operator.
- every visible recommendation includes its safety basis.
- every forbidden action remains visibly gated.
- no runtime mutation is introduced.
- no background execution is introduced.
- no push, merge, cleanup, stash, branch creation, or worktree creation is introduced.
- the Level 9 coordination dashboard baseline still passes.
- any UI tests prove display behavior only.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_operator_dashboard_polish or level_9_coordination_dashboard"
git status -sb
```

Expected outcome:

- diff check has no output.
- focused Level 9 coordination dashboard baseline remains green.
- no implementation, test, API, service, runtime, or UI files are changed by this planning-only increment.
- git status shows this docs file, plus unrelated pre-existing worktree changes.
- no hidden autonomy, background mutation, push, merge, cleanup, automatic execution, or automatic promotion occurred.

## Rollback Notes

Rollback is docs-only:

- remove `docs/cartographer-level-10-operator-dashboard-polish-plan.md`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, receipt cleanup, worker cleanup, or evidence cleanup should be needed because Level 10.1 is planning-only.

## Next Increment

Level 10.2: Project Health Timeline.

Do not implement Level 10.2 until Level 10.1 is manually checked and explicitly approved.
