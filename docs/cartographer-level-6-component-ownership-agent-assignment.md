# Cartographer Level 6 Component Ownership And Agent Assignment

## Status
- status date: 2026-05-20
- increment: Level 6.3, Component Ownership And Agent Assignment
- current authority: read-only ownership and agent assignment preview
- assignment write status: disabled
- autonomous reassignment status: disabled

## Purpose
This increment surfaces component ownership and agent assignment metadata without writing assignments. It shows owner placeholders, assigned agent placeholders, changed-component conflicts, and recommended next action while preventing automatic reassignment and repo mutation.

## Contract
- mode: `component_ownership_agent_assignment`
- contract version: `cartographer.level_6.component_ownership_agent_assignment.v1`
- actions taken: false
- assignment write allowed: false
- automatic reassignment allowed: false
- cross-repo mutation allowed: false
- repo mutation allowed: false
- branch creation allowed: false
- worktree creation allowed: false
- push allowed: false
- merge allowed: false
- cleanup allowed: false

## Forbidden Actions
- repo mutation
- branch creation
- worktree creation
- push
- merge
- cleanup
- autonomous reassignment
- promotion beyond Level 6.3

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-6-component-ownership-agent-assignment.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_6_component_ownership or level_6_cross_project_status_board or level_6_project_registry"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_6_component_ownership_assignment

payload = build_cartographer_level_6_component_ownership_assignment()
print(payload["contract_version"])
print(payload["assignment_write_allowed"], payload["automatic_reassignment_allowed"], payload["repo_mutation_allowed"])
print(payload["branch_creation_allowed"], payload["worktree_creation_allowed"], payload["push_allowed"])
print(payload["merge_allowed"], payload["cleanup_allowed"], payload["actions_taken"])
print(payload["component_count"], payload["changed_component_count"], payload["conflict_count"])
PY
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 6.3 ownership contract with assignment and mutation flags false.

## Debug Path
Compare ownership items against component mapping and the Level 6.2 status board. Investigate duplicate owner conflicts, missing owners for changed components, and stale agent state.

## Rollback Path
Revert the Level 6.3 service, API, tests, and this document. No assignment cleanup should be needed because the increment is read-only.

## Next Increment
Level 6.4: Cross-Repo Dirty Tree Classifier
