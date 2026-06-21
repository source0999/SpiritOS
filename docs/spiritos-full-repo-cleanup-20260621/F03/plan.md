# F03 — Brain-Switch Verdict Contract

## Goal
A **recommendation-only** contract that emits one of five verdicts **after**
bounded local failure, with full evidence — and makes **no real API call**.

Verdicts (frozen):
`LOCAL_RETRY_RECOMMENDED`, `LOCAL_DECOMPOSITION_RECOMMENDED`,
`LOCAL_MODEL_INSUFFICIENT`, `API_ESCALATION_RECOMMENDED`,
`HUMAN_DECISION_REQUIRED`.

## Why
Make the local→API brain switch explicit and auditable. This is the stage most
exposed to benchmark tailoring (A2/A5/A9 are exactly the tempting escalation
cases) and to unapproved API calls. Highest-stakes stage alongside F2.

## Primary new file
`source_proxy/decision/escalation_contract.py`
Touches: `decision/model_lanes.py` (835), `routing/litellm_router.py`.

## Dependencies
**F1** (taxonomy): verdicts reference F1 failure classes — e.g.
`MODEL_FORMATTING_FAILURE` must NOT imply `LOCAL_MODEL_INSUFFICIENT`;
`LOCAL_MODEL_INSUFFICIENT` after bounded retries can justify
`API_ESCALATION_RECOMMENDED`.

## Must record (per recommendation)
task shape; local attempts; formatting failures; validation failures;
reasoning/capability evidence; configured vs unconfigured lanes; privacy class;
cost class; authority required; evidence IDs.

## Increments (≤12 source files)
1. **3.1** — `escalation_contract.py`: the verdict enum + a `recommend()`
   function that takes an evidence record (attempt history + F1 classifications)
   and returns a recommendation. **No provider call anywhere.** Dry-run test
   prints the recommendation. Tests prove the five properties below.
2. **3.2** — wire `model_lanes.py` + `litellm_router.py` to *consult* the
   contract (read-only) before any escalation path; the contract's
   recommendation is advisory. No escalation by task label.

## Invariants (immutable)
- **No escalation by task label.** No A2/A5/A9 production branch.
- **No real API/cloud call** in this stage. The contract is recommendation-only.
- Final provider policy remains Britton's decision.
- Unavailable provider is never reported available.

## Prove (tests)
- formatting failure ≠ capability failure (does not auto-recommend escalation)
- retryable local failure ≠ API recommendation
- bounded repeated *validated* capability failure *can* recommend escalation
- unavailable provider never reported available
- **no provider call occurs** (assert no network/subprocess to a provider)

## Stop conditions
- Any unapproved API attempt → NEEDS_FIX (and likely BLOCKED_HUMAN review).
- Any task-label branch → NEEDS_FIX (constitution §A).

## Rollback
Disable the contract (recommend() returns the prior default); model_lanes +
litellm_router revert to pre-stage behavior. Exact.

## Approval
Britton (highest-stakes). Codex independently confirms no provider call.
