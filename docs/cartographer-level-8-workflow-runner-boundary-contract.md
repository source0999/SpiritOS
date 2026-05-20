# Cartographer Level 8 Workflow Runner Boundary Contract

status: planning-only

Status date: 2026-05-20

## Purpose

Level 8 defines the approved workflow runner boundary for Cartographer. It may model and display a sequence of safe approved steps, but the human must approve each step. The operator experience should be a controlled operations cockpit, not an autonomous agent.

This contract is the Level 8.0 stop point. It does not authorize Level 8.1, workflow run cards, step approval UI/API work, receipt journal implementation, cancel or failed-step handling, execution behavior, runtime behavior changes, UI changes, tests, service endpoints, or Level 9 work.

## Source Of Truth

The current roadmap is `docs/cartographer-level-7-to-10-autopilot-plan.md`.

The completed Level 7 closeout surfaces are:

- `docs/cartographer-level-7-autopilot-boundary-contract.md`.
- `docs/cartographer-level-7-disabled-by-default-feature-flag.md`.
- `docs/cartographer-level-7-next-safe-action-recommendation-contract.md`.
- `docs/cartographer-level-7-dry-run-action-packet-builder.md`.
- `docs/cartographer-level-7-exact-approval-handshake-contract.md`.
- `docs/cartographer-level-7-closeout-dashboard.md`.

The latest Level 7 closeout manual check passed with:

```text
20 passed, 195 deselected, 2 warnings
```

## Level 8.0 Boundary

Level 8.0 is a docs-only boundary contract.

Allowed behavior:

- Define the Level 8 workflow runner safety boundary.
- Define human approval per step as a hard requirement.
- Define receipt journal visibility requirements.
- Define cancel, stop, and failed-step handling expectations.
- Preserve Level 7 closeout gates.
- Preserve Level 6 read-only coordination baseline.

Forbidden behavior:

- No implementation changes.
- No test changes.
- No runtime behavior changes.
- No UI changes.
- No API changes.
- No service changes.
- No workflow runner execution.
- No background execution.
- No autonomous retry loops.
- No hidden receipt writes.
- No cross-project mutation.
- No push by default.
- No merge by default.
- No push queue creation.
- No branch creation.
- No worktree creation.
- No cleanup.
- No stash.
- No automatic commit.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 9 work.

## Workflow Runner Rules

Level 8 must follow these rules:

- Human approval required per step.
- No push or merge by default.
- No background execution.
- No cross-project mutation.
- No autonomous retry loops.
- All actions must be visible in a receipt journal.

Approval for one step must not approve later steps. A workflow may be modeled as a sequence, but every step must remain individually visible, reviewable, cancellable, and blocked until the human approves that exact step.

## Receipt Journal Boundary

Future Level 8 receipt journal behavior must be visible and auditable.

The journal may record:

- proposed steps.
- approved steps.
- skipped steps.
- canceled steps.
- failed steps.
- completed steps.
- evidence references.
- manual check results.
- operator labels.

The journal must not:

- hide actions.
- create background execution authority.
- retry failed steps automatically.
- mutate cross-project state.
- treat a visible receipt as execution approval.
- replace explicit human approval.

## Stop And Failure Boundary

Future Level 8 workflow handling must fail closed.

If a step is canceled, blocked, or failed:

- the workflow must stop.
- later steps must remain unapproved.
- no autonomous retry may occur.
- the receipt journal must show the stopped state.
- human review is required before any continuation.

## Required Human Gates

Level 8.0 only authorizes this boundary document.

Separate explicit approval is required before:

- Level 8.1 workflow run card model work.
- any service change.
- any API change.
- any UI change.
- any test change.
- any runtime behavior change.
- any implementation prompt for Level 8.1 or later.

No Level 9 work may begin until Level 8 is closed out, manually checked, and explicitly approved.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-8-workflow-runner-boundary-contract.md docs/cartographer-level-7-to-10-autopilot-plan.md
grep -n "Human approval required per step\|No background execution\|receipt journal" docs/cartographer-level-8-workflow-runner-boundary-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_7_closeout_dashboard or level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 8.0 boundary terms.
- Level 7 closeout and Level 6 baseline remain green.
- git status shows docs-only changes for this increment, plus unrelated pre-existing worktree changes.
- no implementation files changed by this increment.

## Rollback Notes

Rollback is docs-only:

- remove `docs/cartographer-level-8-workflow-runner-boundary-contract.md`.
- revert any correction made to `docs/cartographer-level-7-to-10-autopilot-plan.md`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, receipt cleanup, or evidence cleanup should be needed because Level 8.0 is docs-only.

## Next Increment

Level 8.1: Workflow Run Card Model.

Do not implement Level 8.1 until Level 8.0 is manually checked and explicitly approved.
