# Cartographer Level 4 Approved Push Executor Reservation

## Status
- status date: 2026-05-20
- increment: Level 4.5, Future approved push executor, separate permission only
- current authority: push queue steward preview and hard-block only
- executor status: reserved, not implemented
- push status: disabled

## Purpose
This document reserves the future approved push executor path without implementing it. Level 4 has enough preview and approval-gate structure to describe what a future executor would need, but Cartographer still has no authority to push, create push queue items, merge, mutate branches, stash, clean up files, or retry silently.

## Current Boundary
- Level 4 may preview push readiness.
- Level 4 may preview push queue proposals.
- Level 4 may validate approval metadata.
- Level 4 may expose a push execution hard block.
- Level 4 may not execute a push.
- Level 4 may not create a durable push queue item.
- Level 4 may not treat approval preview as execution approval.
- Level 4 may not promote itself to Level 5.

## Future Executor Requirements
A future executor would require a separate Britton-approved increment before any implementation starts. That future increment must define:
- exact commits approved for push
- exact remote, branch, and upstream
- required passing checks
- clean tree and HEAD validation
- no behind or drift state
- durable receipt format
- rollback and recovery guidance
- failure handling without silent retry
- audit trail for actor, approval id, command preview, and result

## Forbidden Actions
- auto-push
- push execution
- push queue item creation
- merge
- branch mutation
- worktree mutation
- stash
- cleanup
- silent retry
- broad queue mutation
- self-approval
- promotion beyond Level 4.5

## Manual Checks
```bash
cd /home/source/SpiritOS
git diff --check -- docs/cartographer-level-4-approved-push-executor-reservation.md
grep -n "Future Executor Requirements\|Forbidden Actions\|Manual Checks\|Next Increment" docs/cartographer-level-4-approved-push-executor-reservation.md
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

Expected outcome: diff check has no output; grep finds the required sections; the hard-block sanity payload still reports `push_execution_hard_block`, `blocked`, and false push, queue, merge, and action flags.

## Debug Path
If any future work starts implementing push behavior from this reservation alone, stop immediately. Re-read `docs/cartographer-level-3-to-6-master-plan.md`, confirm Phase 4.5 says separate permission only, and revert the unauthorized executor work.

## Rollback Path
This document is docs-only. Roll back by deleting this reservation doc if Britton decides Level 4.5 should be represented only in the master plan.

## Next Increment
Level 5.1: Parallel Work Risk Model
