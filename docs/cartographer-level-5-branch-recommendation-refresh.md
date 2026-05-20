# Cartographer Level 5 Branch Recommendation Refresh

## Status
- status date: 2026-05-20
- increment: Level 5.2, Branch Recommendation Refresh
- current authority: read-only branch strategy preview
- branch creation status: disabled
- checkout status: disabled

## Purpose
This increment refreshes branch recommendations for parallel Codex work. It recommends a branch name, base branch, base HEAD, owner requirement, purpose, and collision notes without creating a branch or checking out anything.

## Contract
- mode: `branch_recommendation_refresh`
- contract version: `cartographer.level_5.branch_recommendation_refresh.v1`
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
- checkout
- merge
- push
- cleanup
- stash
- executor behavior
- promotion beyond Level 5.2

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-5-branch-recommendation-refresh.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_branch_recommendation or level_5_parallel_work_risk"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_5_branch_recommendation_refresh

payload = build_cartographer_level_5_branch_recommendation_refresh()
print(payload["contract_version"])
print(payload["branch_creation_allowed"], payload["worktree_creation_allowed"], payload["checkout_allowed"])
print(payload["merge_allowed"], payload["cleanup_allowed"], payload["stash_allowed"], payload["push_allowed"])
print(payload["actions_taken"], payload["recommendation_count"])
PY
git branch --show-current
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 5.2 contract with all mutation flags false.

## Debug Path
Compare recommendations against `git status -sb`, `git branch --show-current`, and the Level 5.1 risk model. If branch creation, checkout, merge, push, stash, or cleanup occurs, stop and revert the implementation.

## Rollback Path
Revert the Level 5.2 service, API, tests, and this document. No branch cleanup should be needed because this increment is preview-only.

## Next Increment
Level 5.3: Worktree Recommendation Contract
