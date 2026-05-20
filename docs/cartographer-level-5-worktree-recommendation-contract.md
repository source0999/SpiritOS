# Cartographer Level 5 Worktree Recommendation Contract

## Status
- status date: 2026-05-20
- increment: Level 5.3, Worktree Recommendation Contract
- current authority: read-only worktree strategy preview
- worktree creation status: disabled
- branch creation status: disabled

## Purpose
This increment recommends when a separate worktree is safer for parallel Codex work. It previews a target path, branch proposal, owner requirement, purpose, conflicting dirty files, and command preview without creating a worktree or branch.

## Contract
- mode: `worktree_recommendation_contract`
- contract version: `cartographer.level_5.worktree_recommendation_contract.v1`
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
- promotion beyond Level 5.3

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-5-worktree-recommendation-contract.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_worktree_recommendation or level_5_branch_recommendation or level_5_parallel_work_risk"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_5_worktree_recommendation_contract

payload = build_cartographer_level_5_worktree_recommendation_contract()
print(payload["contract_version"])
print(payload["worktree_creation_allowed"], payload["branch_creation_allowed"], payload["checkout_allowed"])
print(payload["cleanup_allowed"], payload["stash_allowed"], payload["merge_allowed"], payload["push_allowed"])
print(payload["actions_taken"], payload["recommendation_count"])
PY
git worktree list
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 5.3 contract with all mutation flags false.

## Debug Path
Compare recommendations against `git worktree list`, `git status -sb`, and Level 5.2 branch recommendations. If any worktree creation, branch creation, checkout, cleanup, stash, merge, or push occurs, stop and revert the implementation.

## Rollback Path
Revert the Level 5.3 service, API, tests, and this document. No worktree cleanup should be needed because this increment is preview-only.

## Next Increment
Level 5.4: Approval Gate For Branch/Worktree Creation
