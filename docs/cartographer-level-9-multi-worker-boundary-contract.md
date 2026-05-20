# Cartographer Level 9 Multi-Worker Boundary Contract

status: planning-only

Status date: 2026-05-20

## Purpose

Level 9 defines the multi-worker coordination boundary for Cartographer. It may help coordinate multiple Codex workers safely so they do not collide across files, branches, tasks, or project ownership zones.

This contract is the Level 9.0 stop point. It does not authorize Level 9.1, worker registry implementation, assignment modeling, branch proposal queues, worktree proposal queues, file conflict checking, stale worker detection, dashboard work, runtime behavior changes, tests, service endpoints, UI changes, or Level 10 work.

## Source Of Truth

The current roadmap is `docs/cartographer-level-7-to-10-autopilot-plan.md`.

The completed Level 8 closeout surface is `docs/cartographer-level-8-closeout-smoke.md`. Its latest focused manual check passed with:

```text
10 passed, 215 deselected, 2 warnings
```

Level 9 must preserve all Level 8 constraints:

- no hidden autonomy.
- no background execution.
- no autonomous retry loops.
- no cross-project mutation.
- no receipt journal writes unless later explicitly approved.
- no push, merge, branch creation, worktree creation, cleanup, stash, automatic commit, automatic promotion, or self-approval.

## Level 9.0 Boundary

Level 9.0 is a docs-only boundary contract.

Allowed behavior:

- Define the Level 9 worker coordination safety boundary.
- Define recommendation-only behavior for worker coordination.
- Define conflict detection requirements before suggesting parallel work.
- Define branch and worktree proposal queue boundaries.
- Define stale worker closeout packet boundaries.
- Preserve Level 8 closeout gates.
- Preserve Level 7 and Level 6 safety baselines.

Forbidden behavior:

- No implementation changes.
- No test changes.
- No runtime behavior changes.
- No UI changes.
- No API changes.
- No service changes.
- No automatic branch creation.
- No automatic worktree creation.
- No automatic reassignment.
- No force overwrite.
- No commit.
- No push.
- No merge.
- No cleanup.
- No stash.
- No automatic execution.
- No automatic promotion.
- No self-approval.
- No Level 10 work.

## Multi-Worker Rules

Level 9 must follow these rules:

- Recommendations only unless explicitly approved.
- No automatic branch or worktree creation yet.
- No automatic reassignment.
- No force overwrite.
- No commit/push/merge without lower-level approved gates.
- Must detect conflicts before suggesting parallel work.

Worker coordination must never imply ownership transfer, file overwrite permission, branch creation, worktree creation, commit, push, merge, cleanup, or reassignment. Every unsafe or ambiguous state must become a blocker for human review.

## Conflict Detection Boundary

Future Level 9 conflict detection must happen before suggesting parallel work.

It may inspect and report:

- worker ids.
- task ids.
- assigned file scopes.
- proposed branches.
- proposed worktrees.
- ownership zones.
- stale worker indicators.
- overlapping allowed files.
- blocked or ambiguous assignments.

It must not:

- create branches.
- create worktrees.
- checkout branches.
- move files.
- overwrite files.
- reassign tasks.
- close workers.
- commit.
- push.
- merge.
- clean up.
- stash.

## Branch And Worktree Proposal Boundary

Future Level 9 branch and worktree outputs may be proposals only.

Proposal payloads may include:

- proposed branch name.
- proposed worktree path.
- owner.
- task.
- allowed files.
- blockers.
- required approvals.
- conflict status.

Proposal payloads must not create or checkout the branch or worktree.

## Required Human Gates

Level 9.0 only authorizes this boundary document.

Separate explicit approval is required before:

- Level 9.1 worker registry and assignment model work.
- any service change.
- any API change.
- any UI change.
- any test change.
- any runtime behavior change.
- any implementation prompt for Level 9.1 or later.

No Level 10 work may begin until Level 9 is closed out, manually checked, and explicitly approved.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-9-multi-worker-boundary-contract.md docs/cartographer-level-7-to-10-autopilot-plan.md
grep -n "Recommendations only\|No automatic branch\|No force overwrite\|detect conflicts" docs/cartographer-level-9-multi-worker-boundary-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_8_closeout_smoke or level_7_closeout_dashboard or level_6_multi_project_closeout"
git status -sb
```

Expected outcome:

- diff check has no output.
- grep finds the required Level 9.0 boundary terms.
- Level 8 closeout, Level 7 closeout, and Level 6 closeout baselines remain green.
- git status shows docs-only changes for this increment, plus unrelated pre-existing worktree changes.
- no implementation files changed by this increment.

## Rollback Notes

Rollback is docs-only:

- remove `docs/cartographer-level-9-multi-worker-boundary-contract.md`.
- revert any correction made to `docs/cartographer-level-7-to-10-autopilot-plan.md`.

No repo cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, receipt cleanup, worker cleanup, or evidence cleanup should be needed because Level 9.0 is docs-only.

## Next Increment

Level 9.1: Worker Registry And Assignment Model.

Do not implement Level 9.1 until Level 9.0 is manually checked and explicitly approved.
