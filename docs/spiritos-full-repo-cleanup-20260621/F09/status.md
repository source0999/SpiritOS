# F09 Status

**Stage:** F09 - Worker and tool adapters
**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Verdict:** INTERNAL_GO_PENDING_SECONDARY_REVIEW

## Completed
- Added typed `ProcessAdapterRequest`/`ProcessAdapterResult` contracts.
- Routed `_safe_dirty_tree_status()` through the typed process adapter.
- Preserved the existing dirty-tree payload shape and exception path.

## Manual findings
- No new engine was created.
- Output/timing contract for dirty-tree status remains unchanged.
- Adapter carries timeout, attempt, owner, evidence reference, and F1 failure class metadata.
