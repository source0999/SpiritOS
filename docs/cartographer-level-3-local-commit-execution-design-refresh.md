# Cartographer Level 3 Local Commit Execution Design Refresh

Status date: 2026-05-20

Status: design-only, executor-not-implemented

Increment: Level 3.1: Local Commit Execution Design Refresh

Next increment: Level 3.2: Level 3 Negative Tests Before Executor

## Purpose

This document refreshes the Level 3 local commit execution design before any executor code is implemented.

Level 3 remains the current cap. Level 3 means approved local commit steward. It may eventually create one local commit only after explicit human approval for an exact approved file bundle.

This increment does not implement commit execution, tests, API routes, UI controls, push behavior, branch behavior, cleanup, merge, stash, or any autonomous Git behavior.

## Evidence Baseline

This design depends on the existing evidence:

- `docs/cartographer-level-2-apply-smoke.md`
- `docs/cartographer-level-3-autonomy-plan.md`
- `docs/cartographer-level-3-approval-gate-smoke.md`
- `docs/cartographer-level-3-execution-hard-block-smoke.md`
- `docs/cartographer-level-3-closeout-summary.md`
- `docs/cartographer-level-3-to-6-master-plan.md`

Current accepted state:

- Level 3 proposal preview is complete.
- Level 3 approval preview is complete.
- Level 3 commit execution is not implemented.
- Approval preview must not be treated as execution approval.

## Current Phase Cap

- Current cap: Level 3 approved local commits only.
- No push.
- No push queue creation.
- No branch automation.
- No cleanup.
- No merge.
- No autonomous commit.

## Execution Authority Contract

Future Level 3 execution may create a local commit only when all of these are true:

- Britton explicitly approves execution for the exact proposal.
- The approval names the exact file bundle.
- The current HEAD matches the proposal HEAD.
- The current dirty tree fingerprint matches the approved fingerprint.
- Required checks are present and passing.
- Every included file is classified.
- No included file is forbidden, secret, generated output, or otherwise sensitive.
- Every deletion is explicitly approved.
- No unrelated dirty file is staged or committed.
- The executor uses explicit file paths only.
- A commit receipt is returned.
- Push remains disabled.
- Push queue creation remains disabled.

## Required Approval Payload

A future execution approval must include:

- `approval_id`
- `approved_by`
- `approved_at`
- `proposal_id`
- `proposal_version`
- `approved_head`
- `approved_dirty_tree_fingerprint`
- `approved_file_bundle_id`
- `approved_files`
- `approved_deletions`
- `required_checks`
- `commit_title`
- `commit_body`
- `push_allowed: false`
- `push_queue_allowed: false`
- `branch_allowed: false`
- `cleanup_allowed: false`

Any missing, stale, or mismatched field must block execution.

## File Bundle Identity

The approved file bundle must be exact and reproducible.

The bundle identity should be derived from:

- proposal id and version
- repository root
- current branch
- proposal HEAD
- included files
- deleted files
- excluded dirty files
- forbidden files detected
- dirty tree fingerprint
- required checks

The executor must reject:

- unclassified dirty files
- unrelated dirty files
- files added after approval
- deleted files without deletion approval
- files outside the approved bundle
- file path normalization mismatches

## HEAD And Dirty Tree Validation

Before any future local commit, the executor must refresh and compare:

- current branch
- current HEAD
- dirty tree file list
- dirty tree fingerprint
- deleted files
- forbidden path findings
- sensitive file findings

Execution must block if the branch, HEAD, or dirty tree differs from the approved proposal.

## Required Checks Validation

Required checks must be explicit in the proposal and approval.

Execution must block when:

- required checks are missing
- any required check failed
- check output is stale
- checks were run against a different HEAD
- checks were run against a different dirty tree fingerprint

The future executor must not silently downgrade required checks.

## Forbidden Execution Commands

Future implementation must not use:

- `git add .`
- `git add -A`
- `git commit -a`
- `git push`
- branch creation commands
- merge commands
- stash commands
- cleanup commands
- reset or checkout commands except inside a separately approved rollback path

Future implementation may only stage explicit approved paths, and only after every validation gate passes.

## Commit Receipt Contract

Every future approved local commit must return a receipt with:

- receipt id
- proposal id
- approval id
- approved by
- executed by
- branch
- HEAD before commit
- HEAD after commit
- commit sha
- commit title
- committed files
- approved deletions
- excluded dirty files
- required checks and results
- validation summary
- push allowed: false
- push queue allowed: false
- rollback command

The receipt must be produced even when execution is blocked, with `commit_created: false` and blocker details.

## Rollback Contract

Rollback remains a human-approved operation.

The receipt may recommend a rollback command, normally:

```bash
git reset --soft HEAD~1
```

Cartographer must not automatically run rollback, cleanup, stash, merge, branch, or push commands.

## Negative Tests Required Before Executor

The next increment must add negative tests before executor implementation.

Required negative cases:

- no approval
- self-approval
- stale HEAD
- dirty tree fingerprint mismatch
- missing checks
- failed checks
- unclassified dirty files
- forbidden files
- sensitive files
- unrelated dirty files
- unapproved deletions
- path normalization mismatch
- attempted `git add .`
- attempted `git commit -a`
- attempted push
- attempted push queue item creation
- attempted branch, merge, stash, or cleanup behavior

## Debug Path

If future execution is blocked unexpectedly:

- inspect proposal id and version
- compare approved HEAD with current HEAD
- compare approved dirty tree fingerprint with current dirty tree fingerprint
- inspect classified, unclassified, forbidden, and sensitive file groups
- inspect required check names, timestamps, and results
- inspect deletion approval fields
- confirm push and push queue flags remain false

If future execution succeeds unexpectedly, treat it as a Level 3 safety bug.

## Rollback Path For This Increment

This increment is documentation only.

Rollback path:

```bash
rm docs/cartographer-level-3-local-commit-execution-design-refresh.md
```

Do not run that rollback through Cartographer automation. Do not stage, commit, push, clean, stash, merge, or create branches as part of this increment.

## Manual Checks

```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-3-local-commit-execution-design-refresh.md
grep -n "Execution Authority Contract\|Required Approval Payload\|Forbidden Execution Commands\|Commit Receipt Contract\|Negative Tests Required Before Executor" docs/cartographer-level-3-local-commit-execution-design-refresh.md
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

Expected outcome: diff check has no output, grep finds all required design sections, readiness remains blocked only by the current dirty tree state, and git status shows this design doc plus pre-existing unrelated dirty files.

Next increment title: Level 3.2: Level 3 Negative Tests Before Executor
