# F05 → F06 Handoff

**Status:** NOT_STARTED (finalized when F05 verdict set).

## F05 hands to F06
- `api/decision.py` is a thin router; FIP0–FIP6 logic lives in cohesive
  `decision/lanes/*` modules with parity-proven behavior.
- The decision surface (receipts/lanes/trace) that F6's apply/trace/recovery
  modules consume is now stable.

## F06 can begin once
- F05 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- **F01 also GO** (F6 hard-depends on F1 taxonomy for trace failure events).

## Carry-forward for F06
- F6 splits `tasks/long_running.py` (6,513 lines) by responsibility into
  engine + apply/ + trace/ + recovery/ + regression/.
- **Do not rewrite the state machine.** Preserve transitions, apply authority,
  recovery idempotence, duplicate-action protection, causal ordering, consumer
  semantics, operator readback.
- Same safe-first cycle as F5 where applicable.
