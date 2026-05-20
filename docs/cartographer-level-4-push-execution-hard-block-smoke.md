# Cartographer Level 4 Push Execution Hard Block Smoke

## Status
- status date: 2026-05-20
- increment: Level 4.4, Push Execution Hard Block Smoke
- current authority: push queue steward preview only
- current cap: Level 4 hard-blocked push execution
- execution status: disabled

## Purpose
This smoke proves that the Level 4 push execution surface exists only as a hard block. It may receive a proposal id and approval metadata, but it must not push, create a push queue item, merge, create a branch, stash, clean up files, or promote Cartographer to an executor.

## Expected Contract
- mode: `push_execution_hard_block`
- status: `blocked`
- block version: `cartographer.level_4.push_execution_hard_block.v1`
- required blocker: `level_4_push_execution_not_implemented`
- execution blocker: `push_execution_not_implemented`
- push flags: false
- queue creation flags: false
- merge, branch, cleanup, and stash flags: false
- actions taken: false

## Forbidden Actions
- push
- auto-push
- push queue item creation
- merge
- branch creation
- stash
- cleanup
- self-approval
- promotion beyond Level 4.4

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- source_proxy/cartographer/service.py source_proxy/api/cartographer.py source_proxy/tests/test_cartographer_api.py docs/cartographer-level-4-push-execution-hard-block-smoke.md
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "level_4_push_execution or level_4_push_queue_approval or level_4_push_queue_proposal or level_4_push_readiness or push_queue"
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import block_cartographer_level_4_push_execution

payload = block_cartographer_level_4_push_execution(
    proposal_id="missing-proposal",
    approval_id="approval-demo",
    approved_by="Britton",
)
print(payload["mode"])
print(payload["status"], payload["blockers"])
print(payload["push_allowed"], payload["push_enabled"], payload["auto_push_allowed"])
print(payload["push_queue_creation_allowed"], payload["push_queue_item_created"])
print(payload["merge_allowed"], payload["actions_taken"])
PY
git status -sb
```

Expected outcome: diff check has no output; focused tests pass; the sanity payload reports `push_execution_hard_block`, `blocked`, and false push, queue, merge, and action flags.

Next increment title: `Level 4.5: Future approved push executor, separate permission only`
