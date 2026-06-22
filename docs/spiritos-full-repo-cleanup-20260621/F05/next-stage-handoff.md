# F05 -> F06 Handoff

**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW

## F05 hands to F06
- Decision lane status helpers now live in `source_proxy/decision/lanes/status_helpers.py`.
- `source_proxy/api/decision.py` keeps private aliases/wrappers so existing tests and callers continue to work.
- Receipt/failure classification semantics are covered by parity tests.

## F06 can begin once
- F05 commit is created and the worktree is clean.

## Carry-forward for F06
- Preserve task transitions, apply authority, recovery idempotence, duplicate-action prevention, causal ordering, consumer semantics, and operator readback.
- Do not rewrite the long-running state machine.
