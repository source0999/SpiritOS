# Cartographer Level 7 Autopilot Boundary Contract

status: planning-only

Status date: 2026-05-20

## Purpose

Level 7 defines the first limited-autopilot boundary for Cartographer. It allows Cartographer to recommend a next safe action and describe dry-run action packets, but it does not allow Cartographer to execute actions by itself.

This contract is the Level 7.0 stop point. It does not authorize Level 7.1, implementation work, tests, runtime behavior changes, UI changes, feature flags, service endpoints, automatic execution, or mutation.

## Source Of Truth

The current baseline is `docs/cartographer-level-3-to-6-closeout-summary.md`.

That closeout records:

- status date: 2026-05-20.
- current completed roadmap cap: Level 6.5 closeout dashboard.
- next possible scope: Level 7+ future limited autopilot, disabled by default.
- authority status: read-only unless a specific lower-level approved executor gate explicitly allows otherwise.
- focused Level 6.5 baseline: `10 passed, 195 deselected, 2 warnings`.
- all mutation, promotion, and execution flags remained false.

The next roadmap is `docs/cartographer-level-7-to-10-autopilot-plan.md`. It names this increment as Level 7.0 and states that Level 7 starts disabled by default.

## Level 7.0 Boundary

Level 7.0 is a docs-only boundary contract.

Allowed behavior:

- Read the Level 6.5 closeout state.
- Describe future Level 7 authority as disabled by default.
- Define recommendation-only behavior for later increments.
- Define dry-run action packet boundaries for later increments.
- Define exact approval requirements for later increments.
- Preserve all current Level 6 safety restrictions.

Forbidden behavior:

- No implementation changes.
- No test changes.
- No runtime behavior changes.
- No UI changes.
- No API changes.
- No service changes.
- No feature flag implementation.
- No push.
- No push queue creation.
- No branch creation.
- No branch automation.
- No worktree creation.
- No worktree automation.
- No cleanup.
- No stash.
- No merge.
- No automatic commit.
- No automatic promotion.
- No automatic execution.
- No self-approval.

## Disabled By Default Rule

Level 7 must be disabled by default.

Disabled by default means:

- no Level 7 action authority exists when no explicit future flag or gate is approved.
- no action packet can execute.
- no recommendation can become execution by implication.
- no approval preview can be treated as execution approval.
- no service, API, UI, or worker can self-enable Level 7.
- no lower-level executor gate is widened by this contract.

This document does not create the Level 7.1 disabled-by-default feature flag. Level 7.1 requires separate explicit approval.

## Recommendation Boundary

Future Level 7 recommendation behavior may only answer what a safe next human action could be.

Recommendations must:

- be explainable to a human operator.
- cite the blocker or evidence that shaped the recommendation.
- return a blocked or unavailable state when safety cannot be proven.
- keep all mutation and execution flags false.
- avoid implying that Cartographer can perform the action.

Recommendations must not:

- stage files.
- edit files.
- create commits.
- create branches.
- create worktrees.
- create push queue items.
- push.
- merge.
- stash.
- clean up files.
- retry automatically.
- promote themselves into execution.

## Dry-Run Action Packet Boundary

Future Level 7 dry-run action packets may only describe a proposed action. They must not execute that action.

A dry-run packet should include:

- packet id.
- proposed action title.
- purpose.
- allowed files.
- forbidden actions.
- required approvals.
- expected output.
- manual check commands.
- expected manual check result.
- rollback notes.
- blockers.
- evidence references.
- `actions_taken: false`.

A dry-run packet must not:

- write implementation files.
- write tests.
- change runtime behavior.
- create branches.
- create worktrees.
- create commits.
- create push queue items.
- push.
- merge.
- stash.
- clean up files.
- execute shell commands on behalf of the packet.
- treat human review as execution approval.

## Exact Approval Boundary

Future Level 7 approval behavior must be exact and non-transferable.

Any future approval contract must require:

- the exact increment title.
- the exact packet id.
- the exact allowed file list.
- the exact forbidden action list.
- the exact command list to be run.
- the human approver identity or operator label.
- a timestamp or run context.
- an explicit statement that approval is not self-approval.

Approval previews must not execute. Self-approval is forbidden.

## Required Human Gates

Level 7.0 only authorizes this boundary document.

Separate explicit approval is required before:

- Level 7.1 feature flag planning or implementation.
- any service change.
- any API change.
- any UI change.
- any test change.
- any runtime behavior change.
- any implementation prompt for Level 7.1 or later.

No Level 8 work may begin until Level 7 is closed out, manually checked, and explicitly approved.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-7-autopilot-boundary-contract.md docs/cartographer-level-7-to-10-autopilot-plan.md
grep -n "disabled by default\|No automatic execution\|No self-approval\|dry-run" docs/cartographer-level-7-autopilot-boundary-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required boundary terms.
- focused Level 6 baseline still passes.
- git status shows docs-only changes for this increment, plus any unrelated pre-existing worktree changes.
- no implementation files changed by this increment.

## Rollback Notes

Rollback is docs-only:

- remove `docs/cartographer-level-7-autopilot-boundary-contract.md`.
- revert any correction made to `docs/cartographer-level-7-to-10-autopilot-plan.md`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or evidence cleanup should be needed because Level 7.0 is docs-only.

## Next Increment

Level 7.1: Disabled-By-Default Feature Flag.

Do not implement Level 7.1 until Level 7.0 is manually checked and explicitly approved.
