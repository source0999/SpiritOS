# Increment 0.7.1: Define Rollback Without Stash/Reset/Clean/Checkout

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.7, Rollback Model

INCREMENT: Increment 0.7.1, Define Rollback Without Stash/Reset/Clean/Checkout

Objective:
Define a recovery model that does not use stash, reset, clean, checkout, branch, worktree, stage, commit, or push.

Isolated proxy lane scope:
unified-proxy-coding-design-plan-0

Allowed files or file zones:
- Evidence files inside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/
- Read-only inspection only when needed.

Forbidden files, paths, systems, and actions:
- Production source files.
- Source Proxy runtime files.
- Cartographer runtime files.
- Cartographer soak logs.
- Scout soak logs.
- Cartographer live evidence.
- Map state.
- Git mutations, including branch, worktree, stash, reset, clean, checkout, stage, commit, and push.
- Provider/model calls.
- Apply or execute-approved routes.
- Background worker or queue mutation.

Exact work performed:
- Defined a non-git-mutation rollback/recovery model for this isolated evidence lane.
- No rollback command was run.
- No files were deleted, moved, staged, committed, stashed, reset, cleaned, checked out, or pushed.

Required tests or inspections:
- Manual review of forbidden git operations and recovery path.

Rollback/recovery model:
- If a future increment would require forbidden mutation: stop immediately and report NEEDS OPERATOR REVIEW.
- If a boundary is unclear: stop immediately and report the unclear path or action.
- If a production/runtime/shared-state path appears in dirty status: classify it without cleanup and stop if ownership is unknown.
- If an evidence packet contains an error: write a follow-up correction packet inside the evidence root; do not rewrite history with git operations.
- If an evidence file must be superseded: create a new evidence file inside the evidence root that states the supersession; do not delete or move prior evidence unless explicitly authorized.
- If a forbidden action accidentally occurs: stop, report the command/action, affected path, observed status, and NEEDS OPERATOR REVIEW.

Explicitly forbidden recovery commands:
- `git stash`
- `git reset`
- `git clean`
- `git checkout`
- `git switch`
- `git branch`
- `git worktree`
- `git add`
- `git commit`
- `git push`
- Any deletion, move, or edit outside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/

Required manual validation:
- Recovery model does not rely on git mutation.
- Recovery model does not touch Cartographer soak, Scout soak, runtime state, map state, or production files.
- Evidence correction remains isolated to the evidence root.

Required evidence artifact:
This file.

Stop conditions:
- Any need for git mutation.
- Any need to delete, move, or edit outside the evidence root.
- Any need to touch forbidden shared state.

Rollback or recovery note:
This increment is the rollback/recovery note. The only authorized recovery is stop, document, and report, or write a correction packet inside the evidence root if no forbidden action is required.

GO / NO-GO exit rule:
GO only if rollback is defined without stash/reset/clean/checkout or any other git mutation.

GO / NO-GO:
GO for Increment 0.7.1.

Next authorized increment only:
Plan 0, Phase 0.8, Increment 0.8.1: Closeout Packet And GO/NO-GO.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
