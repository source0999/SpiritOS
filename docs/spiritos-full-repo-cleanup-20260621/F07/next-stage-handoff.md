# F07 → F08 Handoff

**Status:** NOT_STARTED (finalized when F07 verdict set).

## F07 hands to F08
- Coding shells classified; shared types/components extracted; reversible feature
  metadata added. No shell deleted; `/coding` unchanged.
- The UI now consumes the stable receipt/trace/decision contracts (F1/F5/F6).

## F08 can begin once
- F07 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- (F08 has no hard upstream dep besides F10; it can run before/after F7 in
  principle, but the recommended order slots it here.)

## Carry-forward for F08
- F8 makes context/memory/Headroom/repomix scripts internally consistent.
- Preserve audited Headroom truth: Cursor on 8797; Headroom was a Linux venv;
  Windows Git Bash couldn't run it; Cursor must not be killed; tree-sitter is an
  honest fallback.
- Do NOT claim Headroom active without health + compressed=true + tokens_saved>0.
