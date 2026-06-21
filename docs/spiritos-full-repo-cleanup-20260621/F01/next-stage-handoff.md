# F01 → F02 Handoff

**Status:** NOT_STARTED (handoff finalized when F01 verdict is set).

## F01 must hand to F02 (and F03/F05/F06/F09 downstream)
- The 19-code enum is live in `source_proxy/diagnostics/status_codes.py`.
- `classify_failure()` is the single entry point for mapping shapes → code.
- Lanes emit `reason_code`; receipts carry additive `failure_classification`;
  traces carry additive `failure` events.
- Legacy free strings preserved.

## F02 can begin once
- F01 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- F01 commit landed; worktree clean; HEAD advanced.
- `classify_failure()` importable (F02's anti-cheat detectors reference it for
  failure-honesty checks, though F02 has no hard upstream dep — it may also run
  before F01; the recommended order runs it after).

## Carry-forward invariants for F02
- F02 copies (not moves) existing selftests; runs legacy + new in parallel.
- F02's negative corpus is frozen in its own holdout-manifest before edits.
- F02 must not retire legacy behavior in its first increment.

## Downstream note
F03/F05/F06/F09 all depend on F1's taxonomy. They must not start before F01 GO.
