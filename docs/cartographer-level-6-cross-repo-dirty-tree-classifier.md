# Cartographer Level 6 Cross Repo Dirty Tree Classifier

## Status
- status date: 2026-05-20
- increment: Level 6.4, Cross-Repo Dirty Tree Classifier
- current authority: read-only cross-repo dirty tree classification
- staging status: disabled
- cross-repo fixes status: disabled

## Purpose
This increment classifies dirty trees across registered projects without staging, committing, pushing, creating branches, cleaning up, merging, stashing, or applying cross-repo fixes. It identifies project, dirty files, component-mapped files, forbidden files, sensitive files, unclassified files, and recommended sequencing.

## Contract
- mode: `cross_repo_dirty_tree_classifier`
- contract version: `cartographer.level_6.cross_repo_dirty_tree_classifier.v1`
- actions taken: false
- staging allowed: false
- commit allowed: false
- push allowed: false
- branch creation allowed: false
- worktree creation allowed: false
- cleanup allowed: false
- merge allowed: false
- stash allowed: false
- cross-repo fixes allowed: false

## Forbidden Actions
- staging
- committing
- pushing
- branch creation
- worktree creation
- cleanup
- merge
- stash
- cross-repo fixes
- promotion beyond Level 6.4

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_cross_repo_dirty_tree or level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_6_cross_repo_dirty_tree_classifier

payload = build_cartographer_level_6_cross_repo_dirty_tree_classifier()
print(payload["contract_version"])
print(payload["staging_allowed"], payload["commit_allowed"], payload["push_allowed"])
print(payload["branch_creation_allowed"], payload["worktree_creation_allowed"], payload["cleanup_allowed"])
print(payload["merge_allowed"], payload["stash_allowed"], payload["cross_repo_fixes_allowed"], payload["actions_taken"])
print(payload["project_count"], payload["dirty_project_count"], payload["blocking_project_count"], payload["unclassified_file_count"])
PY
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 6.4 dirty tree classifier contract with all mutation and fix flags false.

## Debug Path
Compare classifier output with `git status -sb` for each registered repo, component mapping, and registry output. Investigate repo probe failures, path normalization, forbidden paths, sensitive paths, and unclassified files.

## Rollback Path
Revert the Level 6.4 service, API, tests, and this document. No repo cleanup should be needed because the increment is read-only.

## Next Increment
Level 6.5: Multi-Project Closeout Dashboard
