# SpiritOS Worktree Policy

This repository has multiple active project streams. The manifest is the operational entry point: read `worktree-manifest.md` before editing, list worktrees, verify the active branch and HEAD, and choose the named project worktree.

## Ownership boundaries

- Source Proxy changes, its focused tests, and its authoritative receipt packet belong on a Source Proxy branch/worktree.
- SpiritFlix source belongs on its own branch/worktree. Mutable media queues, face reports, and generated library indexes are not source-commit payloads.
- Generated evidence may be retained as a named, authoritative receipt; routine run output stays local unless a plan explicitly names it as evidence.
- Local watchdog markers, backups, logs, build products, caches, and environment links are machine state, not a commit payload.
- Shared files need hunk-level attribution. A filename alone does not assign ownership.

## Service identity

Before runtime tests, record the backend and frontend process CWD, command line, worktree root, branch, and HEAD. Managed services normally run from the authoritative integration worktree. A feature worktree may host them only for an explicitly bounded verification, after equivalent health has been checked. Switch by building or validating the target first, changing one service at a time, and confirming both process CWD and health; never assume a port proves the edited checkout is serving.

## Safe Git operations

Use explicit paths, scoped patches, hashes, and independent checks. Do not run broad reset, restore, clean, force checkout/push, whole-tree stashes, rebases of mixed work, or `git add -A`. Keep unknown work in its current holding worktree until its owner and destination are proven.

## Completion discipline

Before ending a cleanup or feature increment, run `git worktree list --porcelain` and `git status --short` in every retained worktree. Commit verified source, archive bulk generated output outside active worktrees, and remove clean obsolete worktrees with `git worktree remove` followed by `git worktree prune`.

The Prompt 1 dummy storefront is generated lifecycle output. Archive acceptance output when needed, reset it after the run, and do not track generated fixture files. Media scan queues and bulk screenshots follow the same ignored-runtime policy; only a named final receipt may be deliberately added.
