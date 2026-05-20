# Cartographer Level 5 Branch Worktree Approval Gate

## Status
- status date: 2026-05-20
- increment: Level 5.4, Approval Gate For Branch/Worktree Creation
- current authority: approval preview only
- branch creation status: disabled
- worktree creation status: disabled

## Purpose
This increment validates future branch and worktree approval metadata without creating anything. Approval preview may validate the exact worktree path, exact branch name, base HEAD, owner, purpose, and command preview, but it cannot create a branch, create a worktree, checkout, merge, clean up, stash, or push.

## Contract
- mode: `branch_worktree_approval_gate_preview`
- approval version: `cartographer.level_5.branch_worktree_approval_preview.v1`
- actions taken: false
- worktree creation allowed: false
- branch creation allowed: false
- checkout allowed: false
- cleanup allowed: false
- stash allowed: false
- merge allowed: false
- push allowed: false

## Forbidden Actions
- worktree creation
- branch creation
- checkout
- cleanup
- stash
- merge
- push
- executor behavior
- promotion beyond Level 5.4

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-5-branch-worktree-approval-gate.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_branch_worktree_approval or level_5_worktree_recommendation or level_5_branch_recommendation or level_5_parallel_work_risk"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_5_branch_worktree_approval_preview

payload = build_cartographer_level_5_branch_worktree_approval_preview(
    recommendation_id="missing-recommendation",
    approval_id="approval-demo",
    approved_by="Britton",
    exact_worktree_path="../demo",
    exact_branch_name="cartographer/demo",
    base_head="demo-head",
    owner="Britton",
    purpose="demo",
    command_preview="git worktree add ../demo -b cartographer/demo demo-head",
)
print(payload["approval_version"])
print(payload["approval_validated"], payload["blockers"])
print(payload["worktree_creation_allowed"], payload["branch_creation_allowed"], payload["checkout_allowed"])
print(payload["cleanup_allowed"], payload["stash_allowed"], payload["merge_allowed"], payload["push_allowed"])
print(payload["actions_taken"])
PY
git worktree list
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 5.4 approval preview with mutation flags false.

## Debug Path
Compare approval preview payloads against the Level 5.3 worktree recommendation. If any branch creation, worktree creation, checkout, cleanup, stash, merge, or push occurs, stop and revert the implementation.

## Rollback Path
Revert the Level 5.4 service, API, tests, and this document. No branch or worktree cleanup should be needed because this increment is preview-only.

## Next Increment
Level 5.5: Multi-Codex Worker Safety Smoke
