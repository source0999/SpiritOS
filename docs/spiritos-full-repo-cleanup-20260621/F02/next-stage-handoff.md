# F02 → F03 Handoff

**Status:** NOT_STARTED (finalized when F02 verdict set).

## F02 hands to F03 (and F10 downstream)
- `source_proxy/verification/anticheat/` package is live and independent.
- Legacy detectors unchanged and still callable.
- Parity harness + 15 negative-corpus detectors established.
- Set A runner imports the package additively.

## F03 can begin once
- F02 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- F02 commit landed; worktree clean; HEAD advanced.
- F01 also GO (F03 depends on F1 taxonomy — `API_ESCALATION_RECOMMENDED` etc.
  are F1 codes the F3 contract emits).

## Carry-forward for F03
- F03 is recommendation-only; **no real API call**. The anti-cheat registry (F02)
  is the honesty backstop that proves no provider call occurred and no fallback
  was laundered as primary success.
- F03 must not escalate by task label; no A2/A5/A9 production branch.

## Downstream note
F10 reuses F02's negative corpus as a terminal gate.
