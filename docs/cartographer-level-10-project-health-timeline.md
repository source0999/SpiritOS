# Cartographer Level 10 Project Health Timeline

## Status
- status date: 2026-05-20
- increment: Level 10.2, Project Health Timeline
- current authority: read-only operator timeline
- background mutation status: disabled
- evidence mutation status: disabled

## Purpose
This increment shows project health, blockers, evidence references, and Level 9 closeout history as a read-only operator timeline. It helps the operator scan current project state before any closeout packet work begins.

## Contract
- mode: `project_health_timeline`
- contract version: `cartographer.level_10.project_health_timeline.v1`
- actions taken: false
- timeline available: true
- read only: true
- background mutation allowed: false
- hidden writes allowed: false
- cleanup allowed: false
- push allowed: false
- merge allowed: false
- automatic execution allowed: false
- automatic promotion allowed: false
- evidence mutation allowed: false

## Forbidden Actions
- background mutation
- hidden writes
- cleanup
- push
- merge
- automatic execution
- automatic promotion
- evidence mutation
- promotion beyond Level 10.2

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-10-project-health-timeline.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_10_project_health_timeline or level_10_operator_dashboard_polish"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_level_10_project_health_timeline

payload = build_cartographer_level_10_project_health_timeline()
print(payload["contract_version"])
print(payload["background_mutation_allowed"], payload["hidden_writes_allowed"], payload["evidence_mutation_allowed"])
print(payload["cleanup_allowed"], payload["push_allowed"], payload["merge_allowed"])
print(payload["automatic_execution_allowed"], payload["automatic_promotion_allowed"], payload["actions_taken"])
print(payload["project_count"], payload["dirty_project_count"], payload["blocked_project_count"])
PY
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; sanity output reports the Level 10.2 timeline contract with all mutation, execution, promotion, and evidence-write flags false.

## Debug Path
Compare timeline entries against `GET /v1/cartographer/project-health` and `GET /v1/cartographer/level-9-coordination-dashboard`. Investigate stale blockers, missing evidence refs, and mismatched dirty state before planning closeout packets.

## Rollback Path
Revert the Level 10.2 service, API, tests, and this document. No repo cleanup should be needed because this increment is read-only.

## Next Increment
Level 10.3: Closeout Packet Generator
