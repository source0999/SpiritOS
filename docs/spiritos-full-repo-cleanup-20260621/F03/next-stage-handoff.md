# F03 -> F04 Handoff

**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW.

## F03 Hands To F04
- `source_proxy/decision/escalation_contract.py` is live and recommendation-only.
- The `LOCAL_DECOMPOSITION_RECOMMENDED` verdict exists and is emitted for locally tractable-but-large or repeated structured-output failure shapes; this is the trigger F04 can consult.
- `model_lanes.py` and `litellm_router.py` consult the contract read-only through advisory helpers; no API/provider lane is enabled by F03.
- Verdict payloads carry F1 `FailureClass` values for downstream evidence continuity.

## F04 Can Begin Once
- F03 commit is reviewed as `INTERNAL_GO_PENDING_SECONDARY_REVIEW`.
- F01 remains GO for failure classification dependencies.
- Secondary reviewer accepts that full `source_proxy/tests` timeout is a broad-suite caveat, not an F03 gate failure.

## Carry-Forward For F04
- F04 decomposition must be generic by task shape, not benchmark-keyed.
- Sub-packets validate independently and use evidence IDs.
- F04 must not supply script-authored substance or handholding.
- Historical A2/A5/A9 are regression labels only.
- F04 must preserve F03 dry-run/no-provider-call behavior.
