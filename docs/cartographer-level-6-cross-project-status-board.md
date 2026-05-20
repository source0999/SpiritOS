# Cartographer Level 6 Cross Project Status Board

## Status
- status date: 2026-05-20
- increment: Level 6.2, Cross-Project Status Board
- current authority: read-only cross-project visibility
- cross-repo mutation status: disabled
- automatic fixes status: disabled

## Purpose
This increment shows status and blockers across registered projects and project candidates without mutating them. It displays clean or dirty state, blockers, owner and agent placeholders, current level, safe sequencing, and recommended next action.

## Contract
- mode: `cross_project_status_board`
- contract version: `cartographer.level_6.cross_project_status_board.v1`
- actions taken: false
- cross-repo mutation allowed: false
- commit allowed: false
- push allowed: false
- push queue creation allowed: false
- branch creation allowed: false
- worktree creation allowed: false
- cleanup allowed: false
- merge allowed: false
- stash allowed: false
- automatic fixes allowed: false

## Forbidden Actions
- commits
- pushes
- push queue creation
- branch creation
- worktree creation
- cleanup
- merge
- stash
- automatic fixes
- promotion beyond Level 6.2

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-6-cross-project-status-board.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_cross_project_status_board or level_6_project_registry"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_6_cross_project_status_board

payload = build_cartographer_level_6_cross_project_status_board()
print(payload["contract_version"])
print(payload["cross_repo_mutation_allowed"], payload["commit_allowed"], payload["push_allowed"], payload["push_queue_creation_allowed"])
print(payload["branch_creation_allowed"], payload["worktree_creation_allowed"], payload["cleanup_allowed"])
print(payload["merge_allowed"], payload["stash_allowed"], payload["automatic_fixes_allowed"], payload["actions_taken"])
print(payload["project_count"], payload["candidate_count"], payload["dirty_project_count"], payload["blocked_project_count"])
PY
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 6.2 status board contract with all mutation and automatic-fix flags false.

## Debug Path
Compare board items against Level 6.1 registry output, project health output, and each project status command. Investigate stale registry entries, missing project health, and failed probes.

## Rollback Path
Revert the Level 6.2 service, API, tests, and this document. No repo cleanup should be needed because the increment is read-only.

## Next Increment
Level 6.3: Component Ownership And Agent Assignment
