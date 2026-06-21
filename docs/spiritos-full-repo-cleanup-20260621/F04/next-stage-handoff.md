# F04 → F05 Handoff

**Status:** NOT_STARTED (finalized when F04 verdict set).

## F04 hands to F05
- `source_proxy/decision/packet_templates/` generic decomposer is live.
- `prompt_packet.py` routes through it when F3 recommends decomposition.
- Sub-packets validate independently and expose F1 failure classes.

## F05 can begin once
- F04 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- **F01 also GO** (F5 hard-depends on F1 taxonomy — lanes must emit reason_code).
- Shared decision contracts (receipt shape, FIP semantics) are the surface F5
  splits; F1 has pinned failure classification on that surface.

## Carry-forward for F05
- F5 is a behavior-preserving split of `api/decision.py` (7,971 lines) into a
  thin router + cohesive `decision/lanes/*` modules.
- First extraction must be pure with parity proof before any canonical switch.
- F5 must not change receipt shape, FIP0–FIP6 semantics, trace/consumer behavior,
  final status, or `fake_go_detected`.
- No line-count-only refactor; no new parallel engine.
