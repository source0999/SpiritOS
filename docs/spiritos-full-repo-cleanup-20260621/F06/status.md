# F06 Status

**Stage:** F06 - Split long-running task responsibilities
**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Verdict:** INTERNAL_GO_PENDING_SECONDARY_REVIEW

## Completed extraction
- Added `source_proxy/tasks/engine/state.py` for pure task state/readback predicates.
- Kept `source_proxy/tasks/long_running.py` transition, apply, recovery, persistence, and route behavior in place.
- Preserved private helper names through imports/wrappers.

## Manual findings
- State transition entry points (`create_long_running_task`, `get_long_running_task`, `advance_long_running_task`, `execute_approved_long_running_task`, `record_post_apply_verification`, `update_long_running_task`) remain in `long_running.py`.
- Apply/recovery code was inspected and not moved or rewritten.
- Extracted helpers cover terminal/waiting statuses, approved-execution detection, unique-step merge, coder-waiting predicate, blocker reason parsing, and queue title formatting.

## Caveat
- The full existing `test_long_running_tasks.py` apply subset has pre-existing `approved_diff_blocked` failures. A representative failing test also failed against archived pre-F6 HEAD `18f5a1a4`; it is not counted as F6 PASS.
