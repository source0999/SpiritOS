# Cartographer Level 5 Parallel Work Risk Model

## Status
- status date: 2026-05-20
- increment: Level 5.1, Parallel Work Risk Model
- current authority: read-only branch and worktree steward preview
- branch creation status: disabled
- worktree creation status: disabled

## Purpose
This increment adds a read-only risk report for parallel Codex work. It identifies dirty tree, primary branch, unpushed commit, and existing worktree risks so Britton can decide when a future branch or worktree recommendation is needed.

## Contract
- mode: `parallel_work_risk_model`
- contract version: `cartographer.level_5.parallel_work_risk_model.v1`
- actions taken: false
- branch creation allowed: false
- worktree creation allowed: false
- checkout allowed: false
- merge allowed: false
- cleanup allowed: false
- stash allowed: false
- push allowed: false

## Forbidden Actions
- branch creation
- worktree creation
- checkout
- merge
- cleanup
- stash
- push
- autonomous worker reassignment
- promotion beyond Level 5.1

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-5-parallel-work-risk-model.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_parallel_work_risk"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_5_parallel_work_risk_model

payload = build_cartographer_level_5_parallel_work_risk_model()
print(payload["contract_version"])
print(payload["branch_creation_allowed"], payload["worktree_creation_allowed"], payload["checkout_allowed"])
print(payload["merge_allowed"], payload["cleanup_allowed"], payload["stash_allowed"], payload["push_allowed"])
print(payload["actions_taken"], payload["project_count"], payload["risk_count"])
PY
git worktree list
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 5.1 contract with all mutation flags false.

## Debug Path
Compare the report against `git status -sb` and `git worktree list`. If the report changes a branch, creates a worktree, checks out another ref, pushes, stashes, merges, or cleans files, stop and revert the implementation.

## Rollback Path
Revert the Level 5.1 service, API, tests, and this smoke document. No branch or worktree cleanup should be needed because the increment is read-only.

## Next Increment
Level 5.2: Branch Recommendation Refresh
