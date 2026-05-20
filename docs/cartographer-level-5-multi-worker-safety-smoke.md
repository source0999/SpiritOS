# Cartographer Level 5 Multi Worker Safety Smoke

## Status
- status date: 2026-05-20
- increment: Level 5.5, Multi-Codex Worker Safety Smoke
- current authority: read-only worker assignment and collision preview
- branch creation status: disabled
- worktree creation status: disabled

## Purpose
This smoke proves that Level 5 can report parallel Codex worker collision risks without mutating Git state. It combines the Level 5 risk model, branch recommendation refresh, worktree recommendation contract, and approval preview boundary into a read-only assignment report.

## Contract
- mode: `multi_codex_worker_safety_smoke`
- smoke version: `cartographer.level_5.multi_worker_safety_smoke.v1`
- actions taken: false
- branch creation allowed: false
- worktree creation allowed: false
- checkout allowed: false
- cleanup allowed: false
- stash allowed: false
- merge allowed: false
- push allowed: false

## Forbidden Actions
- branch creation
- worktree creation
- checkout
- merge
- cleanup
- stash
- push
- autonomous task reassignment
- promotion beyond Level 5.5

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-5-multi-worker-safety-smoke.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_5_multi_worker_safety or level_5_branch_worktree_approval or level_5_worktree_recommendation or level_5_branch_recommendation or level_5_parallel_work_risk"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_5_multi_worker_safety_smoke

payload = build_cartographer_level_5_multi_worker_safety_smoke()
print(payload["smoke_version"])
print(payload["branch_creation_allowed"], payload["worktree_creation_allowed"], payload["checkout_allowed"])
print(payload["merge_allowed"], payload["cleanup_allowed"], payload["stash_allowed"], payload["push_allowed"])
print(payload["actions_taken"], payload["worker_assignment_count"], payload["collision_count"])
PY
git worktree list
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 5.5 smoke version with all mutation flags false.

## Debug Path
Compare worker assignments against `git status -sb`, `git worktree list`, and the Level 5.1 through Level 5.4 previews. If any branch creation, worktree creation, checkout, merge, cleanup, stash, or push occurs, stop and revert the implementation.

## Rollback Path
Revert the Level 5.5 service, API, tests, and this document. No branch or worktree cleanup should be needed because this smoke is read-only.

## Next Increment
Level 6.1: Project Registry Hardening
