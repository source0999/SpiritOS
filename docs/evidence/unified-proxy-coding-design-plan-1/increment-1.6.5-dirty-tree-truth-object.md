# Increment 1.6.5: Define Dirty-Tree Truth Object

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.6, Shared task/project/context contract.

INCREMENT:
Increment 1.6.5, Define dirty-tree truth object.

Objective:
Define dirty-tree display contract without cleanup.

Isolated proxy lane scope:
Contract evidence plus read-only status snapshots.

Allowed files or file zones:
Plan 1 evidence files only; read-only git status/diff.

Forbidden files, paths, systems, and actions:
Cleanup, stash, reset, checkout, stage, commit, push, branch, worktree, provider calls, apply, execute-approved, Cartographer writes, queues, and hidden workers.

Exact work performed:
- Defined fields: state clean/dirty/unknown, trackedDiffNames, untrackedNames, ownedPaths, unownedPaths, unknownPaths, actionBlocked, lastSnapshotCommand, evidenceRef.
- Current status basis: untracked `docs/evidence/` and untracked source-of-truth plan file; tracked diff empty.
- Rule: dirty-tree chip can block action, but cannot clean or modify git state.

Required tests/checks:
- `git -C /home/source/SpiritOS status --short --branch --untracked-files=normal`
- `git -C /home/source/SpiritOS diff --name-status`

Manual validation performed by Codex:
Dirty state is display-only; no cleanup was performed.

Evidence artifact:
This file.

Stop conditions checked:
Cleanup required: no.

Rollback or recovery note:
Unknown dirty state blocks future action instead of cleaning.

GO/NO-GO exit:
GO for Increment 1.6.5.

Next authorized increment only:
Plan 1, Phase 1.7, Increment 1.7.1.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
