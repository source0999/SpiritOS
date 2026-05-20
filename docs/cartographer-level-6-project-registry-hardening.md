# Cartographer Level 6 Project Registry Hardening

## Status
- status date: 2026-05-20
- increment: Level 6.1, Project Registry Hardening
- current authority: read-only multi-project registry preview
- project enrollment status: disabled
- cross-repo mutation status: disabled

## Purpose
This increment defines the read-only project registry Cartographer can observe. It records project id, path, owner placeholder, agent placeholder, repo type, allowed observation mode, and mutation-disabled flags without enrolling projects automatically or mutating any repo.

## Contract
- mode: `project_registry_hardening`
- contract version: `cartographer.level_6.project_registry_hardening.v1`
- actions taken: false
- cross-repo mutation allowed: false
- project enrollment allowed: false
- auto enrollment allowed: false
- commit allowed: false
- push allowed: false
- branch creation allowed: false
- worktree creation allowed: false
- cleanup allowed: false
- merge allowed: false
- stash allowed: false

## Registry Blockers
- blocked roots present
- configured root blockers present
- project entry blockers present
- duplicate project ids
- duplicate project roots
- unsafe mutation flag enabled

## Forbidden Actions
- cross-repo mutation
- commits
- pushes
- branch creation
- worktree creation
- cleanup
- merge
- stash
- automatic project enrollment
- promotion beyond Level 6.1

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-6-project-registry-hardening.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_project_registry"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_6_project_registry_hardening

payload = build_cartographer_level_6_project_registry_hardening()
print(payload["contract_version"])
print(payload["cross_repo_mutation_allowed"], payload["project_enrollment_allowed"], payload["auto_enrollment_allowed"])
print(payload["commit_allowed"], payload["push_allowed"], payload["branch_creation_allowed"], payload["worktree_creation_allowed"])
print(payload["cleanup_allowed"], payload["merge_allowed"], payload["stash_allowed"], payload["actions_taken"])
print(payload["project_count"], payload["candidate_count"], payload["blockers"])
PY
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 6.1 registry contract with all mutation and enrollment flags false.

## Debug Path
Compare registry entries against `/v1/cartographer/projects`, configured roots, and project discovery. Investigate missing paths, duplicate ids, duplicate roots, and any unsafe mutation flag.

## Rollback Path
Revert the Level 6.1 service, API, tests, and this document. No project cleanup should be needed because the increment is read-only.

## Next Increment
Level 6.2: Cross-Project Status Board
