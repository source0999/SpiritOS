# F06 → F07 Handoff

**Status:** NOT_STARTED (finalized when F06 verdict set).

## F06 hands to F07
- `tasks/long_running.py` split into cohesive engine + apply/ + trace/ +
  recovery/ + regression/, state-machine intact, behavior parity-proven.
- The apply/recovery/trace contracts F7's UI components render are now stable.

## F07 can begin once
- F06 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- Shared contracts stable (F1 taxonomy + F5 lanes/receipts + F6 apply/recovery).
  F7 only runs after shared contracts stabilize (dependency-map.md).

## Carry-forward for F07
- F7 cleans up coding UI shells: classify active/legacy/experimental; extract
  shared types / API adapters+hooks / timeline+receipt+debug components; add
  reversible feature metadata.
- **Provisional canonical** (from runtime import): `/coding` →
  `CodingCockpitShell`. Final canonical-shell decision is Britton's.
- **Do not delete any shell. Do not replace `/coding`.**
- If a structural move requires choosing between competing product behaviors →
  stop `BLOCKED_HUMAN`.
