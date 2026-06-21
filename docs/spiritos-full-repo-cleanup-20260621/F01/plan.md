# F01 — Failure Taxonomy + Debug Receipts

## Goal
One canonical typed contract for all 19 failure classes; every lane emits a
stable `reason_code`; FIP0 receipt gains a top-level `failure_classification`;
failure event appears in causal traces; legacy string field retained.

## Why (from audit §17 + §risk)
Audit's #1 risk: the formatting-failure-vs-capability-failure ambiguity
misread A2/A5/A9. A typed taxonomy lets every downstream stage (F3 brain switch,
F4 decomposition, F9 adapters) reason about failures by class, not free string.

## Primary new file
`source_proxy/diagnostics/status_codes.py`
(`diagnostics/` exists with `gpu.py`; `status_codes.py` is absent → created here.)

## The 19 classes (frozen — see acceptance-contract.json)
TECHNICAL_FAILURE, ENVIRONMENT_FAILURE, SERVICE_UNAVAILABLE,
BRIDGE_INTEGRATION_FAILURE, ROUTING_FAILURE, TOOL_FAILURE,
SEARCH_PROVIDER_EMPTY, SEARCH_PROVIDER_FAILURE, MODEL_CAPABILITY_LIMIT,
MODEL_FORMATTING_FAILURE, LOCAL_MODEL_INSUFFICIENT,
API_ESCALATION_RECOMMENDED, POLICY_BLOCKED, HUMAN_APPROVAL_REQUIRED,
EVIDENCE_MISSING, VALIDATOR_FAILURE, PROMPT_AMBIGUITY,
RESOURCE_PRESSURE, UNKNOWN_NEEDS_INVESTIGATION.

## Increments (≤12 source files each)
1. **Increment 1.1 — taxonomy module + qwen lane only.**
   - Create `diagnostics/status_codes.py`: enum of 19 codes + `classify_failure()`
     helper mapping common exception/result shapes → code. Include a
     `legacy_compat_string` field so old callers still get their string.
   - Wire the **qwen lane** in `decision/model_lanes.py` (835 lines) to emit
     `reason_code` on failure. Keep old strings as the legacy field.
   - Add `failure_classification` to the FIP0 receipt serializer in
     `api/decision.py` as an **additive** top-level field (do not touch existing
     fields — compatibility contract §3).
   - Add `source_proxy/tests/test_status_codes.py`: every class constructible;
     classify() maps representative shapes; legacy string preserved.
   - Safe-first: nothing else changes. Old behavior intact.

2. **Increment 1.2 — expand to remaining lanes + trace event.**
   - Wire remaining lanes (research, coder, verifier, context) to emit codes.
   - Emit a `failure` event into causal traces (additive; existing trace fields
     unchanged — compatibility §5).
   - Extend tests to cover each lane's emission + trace event presence.

## Invariants (immutable once frozen)
- No change to final-status vocabulary.
- No change to `fake_go_detected` (compatibility §8).
- No benchmark-ID branches (constitution §A).
- `UNKNOWN_NEEDS_INVESTIGATION` may not absorb a known class merely to pass —
  classify() must map known shapes to their specific class.
- Receipt change is strictly additive.

## Stop conditions
- Existing tests red for non-new-field reasons → repair (≤3) then NEEDS_FIX.
- Any compatibility-contract field changed → NEEDS_FIX.

## Rollback
Revert `status_codes.py`; remove the additive `failure_classification` field;
old free strings still drive behavior. Exact, complete.

## Approval
Britton signs the 19-code list (frozen here). Codex reviews parity + coverage.
