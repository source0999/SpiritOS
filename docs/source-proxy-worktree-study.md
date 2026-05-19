# Source Proxy Worktree Study

Status date: 2026-05-18
Status: study only

## Purpose

This study records whether Codex-style git worktrees are safe to introduce for Source Proxy work.

No worktree was created for this study. No branch was switched. No cleanup command was run.

## Current Observed State

Commands:

```bash
git worktree list
git branch --show-current
git status -sb
```

Observed state on 2026-05-18:

- Worktrees: one active worktree at `/home/source/SpiritOS`
- Branch: `main`
- Upstream: `origin/main`
- Dirty tree: yes
- New worktree experiment allowed now: no

The working tree contains many active modified and untracked files from the current Source Proxy hardening run. Creating a worktree from this state would make review, cleanup, and ownership harder.

## Recommendation

Do not introduce worktree automation yet.

Reassess only after the current Source Proxy hardening branch is reviewed, committed, or otherwise reduced to a clean and understandable state.

## Risks

- Dirty source tree can hide which changes belong to which increment.
- Multiple worktrees can obscure which branch owns evidence snapshots.
- Generated files and soak logs can be mistaken for source changes.
- Branch deletion can fail when another worktree has the branch checked out.
- A worker could appear isolated while still sharing external services, logs, caches, and env state.
- Worktree cleanup can accidentally delete unreviewed files if ownership is unclear.

## Required Rules Before Any Future Worktree

Future worktree use requires a separate explicit approval gate and must satisfy all of these:

- clean or deliberately checkpointed source tree
- named owner branch
- unique worktree path outside the active checkout
- scoped files and rollback command before creation
- no secrets copied into the worktree
- no automatic apply, commit, push, or cleanup
- evidence directory identified before tests run
- cleanup command documented before creation

## Safe Future Creation Pattern

Example only. Do not run without explicit approval.

```bash
cd /home/source/SpiritOS
git status -sb
git worktree add ../SpiritOS-worktree-example -b source-proxy/example-study main
```

Expected future approval packet:

```text
WORKTREE:
BRANCH:
OWNER:
SCOPE:
EXPECTED FILES:
CHECKS:
CLEANUP:
ROLLBACK:
```

## Cleanup Policy

Before removing a worktree:

1. Run `git status -sb` inside the worktree.
2. Save or discard only files explicitly owned by that worktree.
3. Confirm no branch contains unpushed or unreviewed commits.
4. Run `git worktree remove <path>` only after review.
5. Run `git worktree prune` only after confirming stale metadata.

Do not use broad delete commands for worktree cleanup.

## Manual Check

```bash
cd /home/source/SpiritOS
git worktree list
git branch --show-current
git status -sb
git diff -- docs/source-proxy-worktree-study.md
git diff --check
```

Expected output:

- one active worktree is listed
- current branch is `main`
- dirty state is visible
- doc diff only for this study
- no new worktree is created
- no branch changes
- `git diff --check` has no output

## Rollback

```bash
git restore docs/source-proxy-worktree-study.md docs/source-proxy-production-hardening-plan.md
```
