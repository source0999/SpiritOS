# F03 → F04 Handoff

**Status:** NOT_STARTED (finalized when F03 verdict set).

## F03 hands to F04
- `source_proxy/decision/escalation_contract.py` is live and recommendation-only.
- The `LOCAL_DECOMPOSITION_RECOMMENDED` verdict exists and is emitted for
  locally-tractable-but-large tasks — this is the trigger F4 acts on.
- model_lanes + litellm_router consult the contract read-only; no API enabled.

## F04 can begin once
- F03 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- F01 also GO (F4 sub-packets expose F1 failure classification).

## Carry-forward for F04
- F4 decomposition must be **generic** (task shapes), not benchmark-keyed.
- Sub-packets validate independently and use evidence IDs.
- F4 must not supply script-authored substance (constitution §B/§D).
- Historical A2/A5/A9 are regression references only.
