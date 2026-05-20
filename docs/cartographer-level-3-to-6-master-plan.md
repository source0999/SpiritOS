# Cartographer Level 3 To Level 6 Master Plan

## Status

- Status date: 2026-05-20.
- Current phase cap: Level 3 approved local commits only.
- Current authority: proposal preview and approval preview are complete; local commit execution remains unimplemented and hard-blocked.
- Current forbidden actions: push, push queue creation, branch automation, cleanup, merge, stash, autonomous commit, self-approval, self-promotion, and any file mutation outside an explicitly approved increment.
- Current manual readiness output:

```text
True
True []
True True []
True False
## main...origin/main
```

## Why This Plan Exists

Cartographer has outgrown one-off level docs. It now needs one forward roadmap so Codex stops inventing extra increments, skipping safety gates, or turning future-level notes into active implementation work.

This plan covers Levels 3 through 6, but Codex may only implement one small increment at a time after Britton approves that exact increment. Level 3 is the current implementation cap.

## Current Evidence Baseline

This roadmap starts from the current repo evidence:

- `docs/cartographer-level-2-apply-smoke.md`
- `docs/cartographer-level-3-autonomy-plan.md`
- `docs/cartographer-level-3-approval-gate-smoke.md`
- `docs/cartographer-level-3-execution-hard-block-smoke.md`
- `docs/cartographer-level-3-closeout-summary.md`

The baseline says Level 3 proposal preview and approval preview are complete. Level 3 commit execution remains unimplemented and hard-blocked.

## Current Phase Cap

- Current cap: Level 3 approved local commits only.
- No push.
- No push queue creation.
- No branch automation.
- No cleanup.
- No merge.
- No autonomous commit.

## Manual State Checks

Run this before editing this plan or before beginning a later approved increment:

```bash
cd /home/source/SpiritOS && PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import (
    build_cartographer_level_2_readiness,
    build_cartographer_level_3_closeout_readiness,
    build_cartographer_level_3_finalization_marker,
)

level2 = build_cartographer_level_2_readiness()
level3 = build_cartographer_level_3_closeout_readiness()
marker = build_cartographer_level_3_finalization_marker()

print(level2["level_1_accepted_by_britton"])
print(level2["docs_apply_enabled"], [blocker["code"] for blocker in level2["blockers"]])
print(level3["proposal_preview_ready"], level3["local_commit_ready"], [blocker["code"] for blocker in level3["blockers"]])
print(marker["level_3_complete_for_proposal_preview"], marker["level_3_complete_for_commit_execution"])
PY

git status -sb
```

Expected output before this plan:

```text
True
True []
True True []
True False
## main...origin/main
```

Run this after editing this plan:

```bash
cd /home/source/SpiritOS

git diff --check -- docs/cartographer-level-3-to-6-master-plan.md

grep -n "Current Phase Cap\|Do Not Let Codex Invent Increments\|Definition Of Done For Level 3\|Promotion Gate From Level 3 To Level 4\|Recommended Next Increment" docs/cartographer-level-3-to-6-master-plan.md

PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import (
    build_cartographer_level_2_readiness,
    build_cartographer_level_3_closeout_readiness,
    build_cartographer_level_3_finalization_marker,
)

level2 = build_cartographer_level_2_readiness()
level3 = build_cartographer_level_3_closeout_readiness()
marker = build_cartographer_level_3_finalization_marker()

print(level2["level_1_accepted_by_britton"])
print(level2["docs_apply_enabled"], [blocker["code"] for blocker in level2["blockers"]])
print(level3["proposal_preview_ready"], level3["local_commit_ready"], [blocker["code"] for blocker in level3["blockers"]])
print(marker["level_3_complete_for_proposal_preview"], marker["level_3_complete_for_commit_execution"])
PY

git status -sb
```

Expected output after this plan:

- `git diff --check` has no output.
- `grep` finds all required sections.
- Readiness still shows:

```text
True
True []
True True []
True False
```

- `git status -sb` shows only `docs/cartographer-level-3-to-6-master-plan.md` as new or modified.

## Level Map

- Level 3: Local Commit Steward.
- Level 4: Push Queue Steward.
- Level 5: Branch And Worktree Steward.
- Level 6: Multi-Project Cartographer.
- Level 7+: Future Limited Autopilot, disabled by default and not part of the current implementation scope.

## Level 3 Definition

Level 3 means approved local commit steward.

Level 3 may inspect the dirty tree, group files, recommend commit messages, list checks, preview approval metadata, and eventually create one local commit only after explicit human approval for an exact approved file bundle.

Level 3 must still forbid push, push queue creation, branch creation, merge, stash, cleanup, self-approval, self-promotion, secret files, unclassified files, unrelated dirty files, failed checks, stale HEAD, dirty tree mismatch, and unapproved deletions.

## Level 3 Phases And Increments

### Phase 3.1: Local Commit Execution Design Refresh

- Purpose: refresh the Level 3 execution contract before any executor code exists.
- Likely files to inspect or touch later: `docs/cartographer-level-3-autonomy-plan.md`, `docs/cartographer-level-3-closeout-summary.md`, future design docs only unless Britton approves code.
- Implementation notes: define exact approval payload, file bundle identity, HEAD validation, dirty tree fingerprint validation, required checks validation, receipt shape, and rollback contract.
- Forbidden actions: executor code, staging, committing, pushing, push queue creation, branch automation, cleanup, merge, stash, source edits, endpoint edits, UI edits, and tests unless separately approved.
- Manual checks: run the readiness check and `git status -sb`.
- Expected output: a design-only artifact or plan update showing commit execution remains disabled.
- Debug path: compare the design against the closeout summary and hard-block smoke if any authority appears wider than Level 3.
- Rollback path: revert only the design refresh document change.
- Permission gate: Britton must approve this named increment before any file is edited.
- Next increment title: Level 3.2: Level 3 Negative Tests Before Executor.

### Phase 3.2: Level 3 Negative Tests Before Executor

- Purpose: prove unsafe commit execution paths fail before any executor is implemented.
- Likely files to inspect or touch later: `source_proxy/tests/test_cartographer_api.py`, `source_proxy/tests/test_cartographer_safety_audit.py`, and Level 3 fixture files.
- Implementation notes: add failing-path coverage for no approval, self-approval, stale HEAD, fingerprint mismatch, failed checks, unclassified files, forbidden paths, secrets, unapproved deletions, unrelated dirty files, and attempted push queue creation.
- Forbidden actions: executor implementation, staging, committing, pushing, branch creation, cleanup, merge, stash, UI work, and broad refactors.
- Manual checks: run focused Cartographer tests and `git status -sb`.
- Expected output: tests prove the execution surface remains blocked or rejects unsafe inputs.
- Debug path: inspect failing assertions for accidental authority expansion.
- Rollback path: revert only the negative test changes.
- Permission gate: Britton must approve test implementation after the design refresh is accepted.
- Next increment title: Level 3.3: Approved Local Commit Executor, backend only.

### Phase 3.3: Approved Local Commit Executor, backend only

- Purpose: implement the smallest backend-only path that creates one local commit from one exact approved file bundle.
- Likely files to inspect or touch later: `source_proxy/cartographer/service.py`, `source_proxy/cartographer/commit_proposals.py`, `source_proxy/api/cartographer.py`, and focused Cartographer tests.
- Implementation notes: require exact approval, exact file list, HEAD match, dirty tree fingerprint match, passing checks, forbidden path filtering, deletion approval, and receipt generation; use explicit file paths only.
- Forbidden actions: `git add .`, `git commit -a`, push, push queue creation, branch creation, merge, stash, cleanup, self-approval, committing unclassified files, committing secrets, committing unrelated dirty files, and UI one-click commit.
- Manual checks: run focused tests, inspect the exact command path, perform a controlled local smoke only after Britton approves the exact bundle.
- Expected output: one local commit may be created only when all gates pass.
- Debug path: inspect receipt, HEAD before and after, status before and after, and rejected file classifications.
- Rollback path: use the receipt rollback command, normally `git reset --soft HEAD~1`, only after human approval.
- Permission gate: Britton must approve executor implementation and separately approve any exact file bundle used in a smoke.
- Next increment title: Level 3.4: Commit Receipt And Rollback Contract.

### Phase 3.4: Commit Receipt And Rollback Contract

- Purpose: make every approved local commit auditable and reversible.
- Likely files to inspect or touch later: Cartographer receipt builders, API response models, and focused tests.
- Implementation notes: include proposal id, approval id, approved files, rejected files, branch, old HEAD, new HEAD, command summary, checks, timestamp, actor, and rollback command.
- Forbidden actions: push, push queue creation, branch creation, merge, stash, cleanup, autonomous rollback, and receipt mutation after commit.
- Manual checks: inspect receipt fields after a controlled smoke and verify `git status -sb`.
- Expected output: receipt clearly explains what changed and how a human can roll it back.
- Debug path: compare receipt file list with `git show --name-status --oneline HEAD`.
- Rollback path: follow the receipt rollback command after human approval.
- Permission gate: Britton must approve receipt contract implementation.
- Next increment title: Level 3.5: UI Preview Only, no one-click commit yet.

### Phase 3.5: UI Preview Only, no one-click commit yet

- Purpose: expose Level 3 commit readiness and receipts without adding one-click commit execution.
- Likely files to inspect or touch later: Cartographer UI components, API client code, and UI tests.
- Implementation notes: show proposal, approval metadata, blockers, exact file bundle, checks, and receipts; keep execution outside the UI.
- Forbidden actions: one-click commit, push controls, push queue controls, branch controls, cleanup controls, merge controls, and hidden executor calls.
- Manual checks: load the UI, confirm execution remains unavailable, and verify `git status -sb`.
- Expected output: humans can review Level 3 state without triggering Git mutation from the UI.
- Debug path: inspect network calls and confirm no execution endpoint is called by preview.
- Rollback path: revert only the UI preview changes.
- Permission gate: Britton must approve UI preview work after backend safety is accepted.
- Next increment title: Level 3.6: Level 3 Closeout Smoke.

### Phase 3.6: Level 3 Closeout Smoke

- Purpose: prove Level 3 approved local commits are complete while push remains disabled.
- Likely files to inspect or touch later: Level 3 smoke docs, focused smoke scripts, and Cartographer tests.
- Implementation notes: run negative tests, readiness checks, one approved local commit smoke, receipt validation, rollback documentation, and final status inspection.
- Forbidden actions: push, push queue creation, branch automation, cleanup, merge, stash, autonomous commit, and promotion to Level 4.
- Manual checks: run the readiness check, focused tests, receipt inspection, and `git status -sb`.
- Expected output: Level 3 is done for approved local commits only.
- Debug path: investigate any changed HEAD, dirty tree mismatch, missing receipt, or push-related artifact.
- Rollback path: use the documented receipt rollback path after human approval.
- Permission gate: Britton must approve closeout smoke and separately approve promotion consideration.
- Next increment title: Level 4.1: Push Readiness Contract.

## Level 4 Definition

Level 4 is push queue steward only. It can prepare push queue proposals after local commits exist. It cannot push automatically and cannot merge.

Level 4 is not active until the promotion gate from Level 3 to Level 4 is satisfied and Britton explicitly approves promotion.

## Level 4 Phases And Increments

### Phase 4.1: Push Readiness Contract

- Purpose: define the safety contract for proposing pushes without executing them.
- Likely files to inspect or touch later: future push readiness service, API models, and tests.
- Implementation notes: require local commit receipts, clean status, branch identity, upstream identity, no secret findings, and explicit push-disabled flags.
- Forbidden actions: actual push, push queue item creation, merge, branch creation, cleanup, stash, and autonomous promotion.
- Manual checks: inspect branch/upstream state and `git status -sb`.
- Expected output: a read-only contract for push readiness.
- Debug path: compare readiness output with `git status -sb` and branch upstream data.
- Rollback path: revert only the readiness contract changes.
- Permission gate: Britton must approve Level 4.1 after Level 3 promotion.
- Next increment title: Level 4.2: Push Queue Proposal Preview.

### Phase 4.2: Push Queue Proposal Preview

- Purpose: preview a push queue proposal without creating a queue item.
- Likely files to inspect or touch later: future push proposal builder, API route, and tests.
- Implementation notes: include commits to push, upstream target, risk notes, checks, and approval requirements.
- Forbidden actions: push, queue item creation, merge, branch creation, cleanup, and executor behavior.
- Manual checks: inspect proposal output and confirm git state is unchanged.
- Expected output: a human-reviewable push proposal preview.
- Debug path: compare proposed commits with `git log @{u}..HEAD` where an upstream exists.
- Rollback path: disable the preview route or revert proposal changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 4.3: Push Queue Approval Gate.

### Phase 4.3: Push Queue Approval Gate

- Purpose: validate push queue approval metadata while still preventing push execution.
- Likely files to inspect or touch later: approval validator, API models, and negative tests.
- Implementation notes: validate actor, target branch, exact commits, checks, stale HEAD, and push-disabled state.
- Forbidden actions: push, queue item creation, merge, branch creation, cleanup, and self-approval.
- Manual checks: run focused approval tests and `git status -sb`.
- Expected output: approval preview can pass structurally while execution stays disabled.
- Debug path: inspect stale commit and mismatched target failures.
- Rollback path: revert approval gate changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 4.4: Push Execution Hard Block Smoke.

### Phase 4.4: Push Execution Hard Block Smoke

- Purpose: prove push attempts are hard-blocked.
- Likely files to inspect or touch later: smoke docs, tests, and hard-block service path.
- Implementation notes: attempt the execution path in a controlled test and assert no push, no queue item, no merge, and no branch mutation.
- Forbidden actions: real push, real queue item creation, merge, branch creation, cleanup, and stash.
- Manual checks: run focused tests and inspect git status.
- Expected output: push execution remains unavailable.
- Debug path: inspect any remote, queue, or branch side effect.
- Rollback path: revert smoke-only changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 4.5: Future approved push executor, separate permission only.

### Phase 4.5: Future approved push executor, separate permission only

- Purpose: reserve a future path for an approved push executor after queue safety is proven.
- Likely files to inspect or touch later: future push executor, queue persistence, audit receipts, and tests.
- Implementation notes: this is not auto-push; execution would require separate exact approval and durable receipts.
- Forbidden actions: auto-push, merge, branch mutation, cleanup, silent retries, and broad queue mutation.
- Manual checks: to be defined only if Britton approves this future increment.
- Expected output: no active implementation until separately approved.
- Debug path: stop if any implementation starts before approval.
- Rollback path: revert any unauthorized executor work.
- Permission gate: Britton must explicitly approve this future increment.
- Next increment title: Level 5.1: Parallel Work Risk Model.

## Level 5 Definition

Level 5 is branch and worktree steward for parallel Codex work. It is designed to prevent multiple Codex workers from dirtying the same branch.

Level 5 can recommend branch and worktree strategy. It can create branches or worktrees only after explicit approval in a future implementation. There is no auto branch creation in this plan.

## Level 5 Phases And Increments

### Phase 5.1: Parallel Work Risk Model

- Purpose: identify collision risks between multiple Codex workers.
- Likely files to inspect or touch later: future branch/worktree planner, status service, and tests.
- Implementation notes: model dirty files, ownership, branch identity, worker assignment, and conflicting paths.
- Forbidden actions: branch creation, worktree creation, merge, cleanup, stash, push, and autonomous reassignment.
- Manual checks: inspect current branch, worktrees, and dirty state.
- Expected output: a read-only risk report.
- Debug path: compare report with `git worktree list` and `git status -sb`.
- Rollback path: revert the risk model changes.
- Permission gate: Britton must approve Level 5 work after Level 4 is complete.
- Next increment title: Level 5.2: Branch Recommendation Refresh.

### Phase 5.2: Branch Recommendation Refresh

- Purpose: recommend branch strategy without creating branches.
- Likely files to inspect or touch later: branch recommendation service and tests.
- Implementation notes: recommend naming, base branch, owner, purpose, and collision notes.
- Forbidden actions: branch creation, checkout, merge, push, cleanup, stash, and executor behavior.
- Manual checks: compare recommendation to current branch and status.
- Expected output: a branch recommendation preview.
- Debug path: inspect stale base or wrong upstream assumptions.
- Rollback path: revert recommendation changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 5.3: Worktree Recommendation Contract.

### Phase 5.3: Worktree Recommendation Contract

- Purpose: recommend when a separate worktree is safer for parallel work.
- Likely files to inspect or touch later: worktree recommendation service, API models, and tests.
- Implementation notes: include path proposal, branch proposal, owner, conflicting dirty files, and approval requirements.
- Forbidden actions: worktree creation, branch creation, checkout, cleanup, stash, merge, and push.
- Manual checks: inspect `git worktree list` and `git status -sb`.
- Expected output: a worktree recommendation only.
- Debug path: compare recommendation with existing worktrees and path ownership.
- Rollback path: revert contract changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 5.4: Approval Gate For Branch/Worktree Creation.

### Phase 5.4: Approval Gate For Branch/Worktree Creation

- Purpose: validate future branch/worktree approval metadata without creating anything.
- Likely files to inspect or touch later: approval validator and negative tests.
- Implementation notes: validate branch name, base HEAD, target path, owner, exact command preview, and collision checks.
- Forbidden actions: branch creation, worktree creation, checkout, merge, cleanup, stash, and push.
- Manual checks: run focused approval tests and inspect git status.
- Expected output: approval preview only.
- Debug path: inspect stale HEAD, existing path, and branch collision failures.
- Rollback path: revert approval gate changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 5.5: Multi-Codex Worker Safety Smoke.

### Phase 5.5: Multi-Codex Worker Safety Smoke

- Purpose: prove parallel worker recommendations do not mutate Git state.
- Likely files to inspect or touch later: smoke docs and focused tests.
- Implementation notes: simulate multiple workers, conflicting paths, and recommended isolation.
- Forbidden actions: branch creation, worktree creation, checkout, merge, cleanup, stash, push, and autonomous task reassignment.
- Manual checks: run smoke tests, `git worktree list`, and `git status -sb`.
- Expected output: safe recommendations with no mutation.
- Debug path: inspect any branch, worktree, or dirty tree side effect.
- Rollback path: revert smoke-only changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 6.1: Project Registry Hardening.

## Level 6 Definition

Level 6 is multi-project Cartographer. It coordinates multiple projects, components, and repos. It can show status, blockers, owner or agent, recommended next action, and safe sequencing.

Level 6 cannot mutate other repos without explicit project-level approval.

## Level 6 Phases And Increments

### Phase 6.1: Project Registry Hardening

- Purpose: define the registry of projects/components Cartographer can observe.
- Likely files to inspect or touch later: future project registry, config schema, and tests.
- Implementation notes: record project id, path, owner, repo type, allowed observation mode, and mutation disabled flags.
- Forbidden actions: cross-repo mutation, commits, pushes, branch creation, cleanup, merge, stash, and automatic project enrollment.
- Manual checks: inspect registry output and confirm no repo status changes.
- Expected output: a durable read-only registry.
- Debug path: inspect missing paths, duplicate ids, and unsafe mutation flags.
- Rollback path: revert registry changes.
- Permission gate: Britton must approve Level 6 work after Level 5 is complete.
- Next increment title: Level 6.2: Cross-Project Status Board.

### Phase 6.2: Cross-Project Status Board

- Purpose: show status and blockers across projects without mutating them.
- Likely files to inspect or touch later: status aggregator, API route, UI board, and tests.
- Implementation notes: display clean/dirty state, blockers, owner, current level, and recommended next action.
- Forbidden actions: commits, pushes, queue creation, branch creation, cleanup, merge, stash, and automatic fixes.
- Manual checks: compare board output to each project status command.
- Expected output: read-only cross-project visibility.
- Debug path: inspect stale registry entries and failed project probes.
- Rollback path: revert board changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 6.3: Component Ownership And Agent Assignment.

### Phase 6.3: Component Ownership And Agent Assignment

- Purpose: track which human or Codex agent owns each component.
- Likely files to inspect or touch later: ownership model, assignment API, UI board, and tests.
- Implementation notes: support explicit assignment, no automatic reassignment, and visible conflicts.
- Forbidden actions: repo mutation, branch creation, worktree creation, push, merge, cleanup, and autonomous reassignment.
- Manual checks: inspect ownership display and audit output.
- Expected output: clear ownership and agent assignment metadata.
- Debug path: inspect duplicate owner conflicts and stale agent state.
- Rollback path: revert ownership changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 6.4: Cross-Repo Dirty Tree Classifier.

### Phase 6.4: Cross-Repo Dirty Tree Classifier

- Purpose: classify dirty trees across registered repos without staging or committing.
- Likely files to inspect or touch later: classifier, registry integration, API output, and tests.
- Implementation notes: identify project, dirty files, forbidden paths, unclassified files, and recommended sequencing.
- Forbidden actions: staging, committing, pushing, branch creation, cleanup, merge, stash, and cross-repo fixes.
- Manual checks: compare classifier output with each repo's `git status -sb`.
- Expected output: cross-repo dirty tree classification only.
- Debug path: inspect repo probe failures, path normalization, and classifier gaps.
- Rollback path: revert classifier integration.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 6.5: Multi-Project Closeout Dashboard.

### Phase 6.5: Multi-Project Closeout Dashboard

- Purpose: summarize project readiness, blockers, ownership, and next safe action.
- Likely files to inspect or touch later: dashboard UI, API aggregation, tests, and smoke docs.
- Implementation notes: show per-project level, allowed authority, blockers, next approved increment, and mutation-disabled state.
- Forbidden actions: commits, pushes, queue creation, branch creation, cleanup, merge, stash, automatic promotion, and automatic execution.
- Manual checks: inspect dashboard against registry and project status outputs.
- Expected output: a read-only multi-project closeout view.
- Debug path: inspect mismatched project status and stale ownership data.
- Rollback path: revert dashboard changes.
- Permission gate: Britton must approve this increment.
- Next increment title: Level 7+: Future Limited Autopilot, disabled by default.

## Do Not Let Codex Invent Increments

- Codex must only implement the next named increment.
- If Codex believes a new increment is needed, it must stop and propose it.
- Codex must not append new phases to the active plan without Britton approval.
- Codex must not skip from Level 3 to Level 4.
- Codex must not turn future-level notes into active work.
- Future increments must be selected from this plan or explicitly approved by Britton.

## Definition Of Done For Level 3

Level 3 is done only when all of these are true:

- Exact approved file bundle is required for every local commit.
- HEAD validation blocks stale proposals.
- Dirty tree fingerprint validation blocks mismatched trees.
- Required checks validation blocks missing or failed checks.
- Forbidden path block prevents secret, sensitive, generated, and disallowed files.
- Unclassified dirty file block prevents unknown files from being committed.
- No `git add .`.
- No `git commit -a`.
- No push.
- No push queue item.
- Commit receipt exists for every approved local commit.
- Rollback command is included in every receipt.
- Safety tests cover negative execution paths.
- Final git status is clean except intentional plan changes or explicitly approved local commit results.

## Promotion Gate From Level 3 To Level 4

Level 4 cannot start until:

- Level 3 local commit executor has passed negative tests.
- At least one approved local commit smoke has completed.
- Commit receipts are reliable.
- Rollback path is documented.
- Push remains disabled.
- Britton explicitly approves promotion.

## Recommended Next Increment

The next increment after this plan must be:

Level 3.1: Local Commit Execution Design Refresh

It must be planning and tests-first only. It must not implement commit execution yet.
