# Cartographer Level 6 Multi Project Closeout Dashboard

## Status
- status date: 2026-05-20
- increment: Level 6.5, Multi-Project Closeout Dashboard
- current authority: read-only multi-project closeout view
- automatic promotion status: disabled
- automatic execution status: disabled

## Purpose
This increment summarizes project readiness, blockers, ownership, and next safe action across registered projects. It shows per-project level, allowed authority, blockers, next approved increment, and mutation-disabled state.

## Contract
- mode: `multi_project_closeout_dashboard`
- contract version: `cartographer.level_6.multi_project_closeout_dashboard.v1`
- actions taken: false
- commit allowed: false
- push allowed: false
- push queue creation allowed: false
- branch creation allowed: false
- worktree creation allowed: false
- cleanup allowed: false
- merge allowed: false
- stash allowed: false
- automatic promotion allowed: false
- automatic execution allowed: false

## Forbidden Actions
- commits
- pushes
- queue creation
- branch creation
- worktree creation
- cleanup
- merge
- stash
- automatic promotion
- automatic execution

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-6-multi-project-closeout-dashboard.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_multi_project_closeout or level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_6_multi_project_closeout_dashboard

payload = build_cartographer_level_6_multi_project_closeout_dashboard()
print(payload["contract_version"])
print(payload["commit_allowed"], payload["push_allowed"], payload["push_queue_creation_allowed"])
print(payload["branch_creation_allowed"], payload["worktree_creation_allowed"], payload["cleanup_allowed"])
print(payload["merge_allowed"], payload["stash_allowed"], payload["automatic_promotion_allowed"], payload["automatic_execution_allowed"], payload["actions_taken"])
print(payload["project_count"], payload["ready_project_count"], payload["blocked_project_count"])
PY
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 6.5 closeout dashboard contract with all mutation, promotion, and execution flags false.

## Debug Path
Compare closeout items against the Level 6.1 registry, Level 6.2 status board, Level 6.3 ownership preview, and Level 6.4 dirty tree classifier. Investigate mismatched project status and stale ownership data.

## Rollback Path
Revert the Level 6.5 service, API, tests, and this document. No repo cleanup should be needed because the increment is read-only.

## Next Increment
Level 7+: Future Limited Autopilot, disabled by default
