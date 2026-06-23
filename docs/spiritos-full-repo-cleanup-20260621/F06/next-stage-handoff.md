# F06 -> F07 Handoff

**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW

## F06 hands to F07
- Long-running state/readback helpers are split into `source_proxy/tasks/engine/state.py`.
- Core transition, apply, recovery, persistence, and route behavior remain in `long_running.py`.
- Full long-running apply-suite failures are documented as pre-existing and not counted as PASS.

## F07 can begin once
- F06 commit is created and the worktree is clean.

## Carry-forward for F07
- Do not delete alternate coding shells.
- Do not replace canonical `/coding`.
- Keep UI shell cleanup reversible and metadata-oriented.
