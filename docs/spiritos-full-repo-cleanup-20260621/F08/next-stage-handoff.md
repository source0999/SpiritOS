# F08 → F09 Handoff

**Status:** NOT_STARTED (finalized when F08 verdict set).

## F08 hands to F09
- Port/config/start scripts for context/memory/Headroom/repomix are internally
  consistent; Cursor/8797 collision documented.
- Honest `headroom_status` probe in place; Headroom correctly BLOCKED_ENV;
  tree-sitter fallback correctly labeled `fallback_used=true`.
- Context pack shape unchanged.

## F09 can begin once
- F08 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- **F01 + F05 also GO** (F9 hard-depends on F1 taxonomy + F5 lane modules —
  adapters live in the lanes F5 creates).

## Carry-forward for F09
- F9 moves direct `subprocess`/`urllib` behavior in `decision.py` (browser/qwen/
  ollama) behind typed lane adapters; mac-worker contract cleanup.
- Each adapter: request/result types, timeout, attempt count, F1 failure
  classification, evidence reference, redacted logs, ownership metadata.
- Preserve output/timing before retiring direct paths. No new engine.
