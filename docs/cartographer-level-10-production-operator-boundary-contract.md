# Cartographer Level 10 Production Operator Boundary Contract

status: planning-only

Status date: 2026-05-20

## Purpose

Level 10 defines Cartographer production operator mode as a daily command center for SpiritOS repo operations, closeouts, evidence review, and next-step planning while preserving every safety gate from Levels 7 through 9.

This contract is the Level 10.0 stop point. It does not authorize Level 10.1 dashboard polish, project health timelines, closeout packet generation, run history browsing, Scout or Blueprint handoff work, production readiness implementation, runtime behavior changes, tests, service endpoints, UI changes, or any roadmap beyond Level 10.7.

## Source Of Truth

The current roadmap is `docs/cartographer-level-7-to-10-autopilot-plan.md`.

The completed Level 9 closeout surface is `docs/cartographer-level-9-coordination-dashboard.md`. Its latest focused manual check passed with:

```text
6 passed, 231 deselected, 2 warnings
```

Level 10 must preserve all Level 9 constraints:

- recommendations only unless explicitly approved.
- no automatic branch creation.
- no automatic worktree creation.
- no automatic reassignment.
- no force overwrite.
- no commit, push, merge, cleanup, stash, automatic execution, automatic promotion, or self-approval.
- conflicts must be detected before suggesting parallel work.

## Level 10.0 Boundary

Level 10.0 is a docs-only boundary contract.

Allowed behavior:

- Define production operator mode as command-center visibility and gated planning.
- Define the human operator as the final authority for every action.
- Define audit, rollback, and evidence expectations for future Level 10 increments.
- Preserve Level 9 coordination gates.
- Preserve Level 8 workflow runner gates.
- Preserve Level 7 disabled-by-default autopilot gates.
- Preserve Level 6 read-only coordination and approved local stewardship baselines.

Forbidden behavior:

- No implementation changes.
- No test changes.
- No runtime behavior changes.
- No UI changes.
- No API changes.
- No service changes.
- No hidden autonomy.
- No background mutation.
- No background execution.
- No push.
- No merge.
- No cleanup.
- No stash.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 11 roadmap or invented extra levels.

## Production Operator Rules

Level 10 must follow these rules:

- Still no hidden autonomy.
- Still no background mutation.
- Still no push, merge, or cleanup unless future approved executor gates exist.
- Every operator-facing recommendation must be explainable to a human operator.
- Every future action path must have a clear rollback and audit path.
- Every future execution path must begin as a proposal, preview, or dry-run before execution is considered.
- Every future increment must preserve explicit permission gates.
- Level 10 must stop at Level 10.7 unless the user explicitly asks for a new roadmap.

Production operator mode may make repo state easier to understand. It must not make repo state easier to mutate without a specific lower-level approved executor gate.

## Future Increment Boundary

Future Level 10 increments may plan or preview:

- operator dashboard polish.
- project health timelines.
- closeout packet generation.
- run history and evidence browsing.
- Scout and Blueprint handoff previews.
- production readiness checklists.
- Level 10 closeout and next-roadmap gates.

Future Level 10 increments must not silently introduce:

- write-side authority.
- background mutation.
- push or merge authority.
- cleanup authority.
- hidden retries.
- automatic promotion.
- autonomous task selection.
- roadmap continuation beyond Level 10.7.

## Required Human Gates

Level 10.0 only authorizes this boundary document.

Separate explicit approval is required before:

- Level 10.1 operator dashboard polish planning or implementation.
- any service change.
- any API change.
- any UI change.
- any test change.
- any runtime behavior change.
- any implementation prompt for Level 10.1 or later.
- any new roadmap after Level 10.7.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-10-production-operator-boundary-contract.md docs/cartographer-level-7-to-10-autopilot-plan.md
grep -n "no hidden autonomy\|no background mutation\|rollback and audit\|stop at Level 10.7" docs/cartographer-level-10-production-operator-boundary-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_9_coordination_dashboard or level_8_closeout_smoke or level_7_closeout_dashboard"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 10.0 boundary terms.
- Level 9, Level 8, and Level 7 closeout baselines remain green.
- git status shows this docs-only increment, plus unrelated pre-existing worktree changes.
- no implementation files changed by this increment.

## Rollback Notes

Rollback is docs-only:

- remove `docs/cartographer-level-10-production-operator-boundary-contract.md`.
- revert any correction made to `docs/cartographer-level-7-to-10-autopilot-plan.md`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, receipt cleanup, worker cleanup, or evidence cleanup should be needed because Level 10.0 is docs-only.

## Next Increment

Level 10.1: Operator Dashboard Polish Plan.

Do not implement Level 10.1 until Level 10.0 is manually checked and explicitly approved.
