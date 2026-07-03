# Increment Receipt: Plan 03.1 Prompt Hash and Request Identity

increment_id: `03.1-prompt-hash-and-request-identity`
plan_id: `03`
phase_id: `3`
started_at: `2026-07-02T21:46:00-04:00`
completed_at: `2026-07-02T21:52:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
original_user_prompt_hash: `ecef30fa47eb88570cb1e3618656f523bf38e48276231f423f8846be32eb3f03`
request_id: `plan-03-1-request-a`
trace_id: `design-studio-trace-ecef30fa47eb-equest-a`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 03.1 adds prompt hashing plus request/trace identity to the Design Studio preview route. It does not replace the hardcoded design packet yet; that begins in Plan 03.2.

Exact files changed by this increment:

- `src/app/v1/coding/design-studio/preview/route.ts`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-03-real-packet-generation/evidence/plan-03.1-prompt-identity-20260703T014829Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-03-real-packet-generation/increment-03-phase-3-03.1-receipt-20260703-015200.md`

## Implementation

The route now returns:

- top-level `original_user_prompt_hash`
- top-level `request_id`
- top-level `trace_id`
- the same identity fields inside `preview_packet`

Hashing uses SHA-256 of the original prompt string.

## Runtime Proof

Live route:

```text
http://localhost:3017/v1/coding/design-studio/preview
```

Proof result:

```json
{
  "original_user_prompt_hash": "ecef30fa47eb88570cb1e3618656f523bf38e48276231f423f8846be32eb3f03",
  "different_prompt_hash": "e710d3acd76f623c133eacd0b25efa6941b1a7afc45a70cfd911bdf344c9b6bb",
  "samePromptSameHash": true,
  "differentPromptDifferentHash": true,
  "requestIdsReturned": [
    "plan-03-1-request-a",
    "plan-03-1-request-b",
    "plan-03-1-request-c"
  ],
  "traceIdsReturned": [
    "design-studio-trace-ecef30fa47eb-equest-a",
    "design-studio-trace-ecef30fa47eb-equest-b",
    "design-studio-trace-e710d3acd76f-equest-c"
  ],
  "allStatus200": true
}
```

Evidence artifact:

- route proof JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-03-real-packet-generation/evidence/plan-03.1-prompt-identity-20260703T014829Z.json`
- route proof JSON sha256: `9749abd49fd08ff0429a4d587fade6c1baff26d4b403a17bbee4b8467be8134b`

## Commands Run

Source inspection:

```text
rg -n "original_user_prompt_hash|requestIdentity|promptHash|trace_id: identity|request_id: identity" src/app/v1/coding/design-studio/preview/route.ts
```

Runtime proof:

```text
node <inline route POST proof script>
```

Result: PASS.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 03.1 because this increment does not invoke a model, generate the full design packet, normalize DesignDNA, apply a sandbox diff, run a screenshot verifier, run an anti-template critic, repair, accept, or write back:

- `model_invocation_event_id`
- `provider_model_name`
- `input_hash`
- `output_hash`
- `design_packet_hash`
- `designdna_hash`
- `coder_packet_hash`
- `diff_hash`
- `sandbox_apply_receipt_id`
- `desktop_screenshot_path`
- `desktop_screenshot_hash`
- `mobile_screenshot_path`
- `mobile_screenshot_hash`
- `dom_snapshot_path`
- `network_proof_path`
- `anti_template_verdict_id`
- `critic_verdict_id`
- `repair_attempt_ids`
- `retest_receipt_id`
- `acceptance_id`

## What Failed Before Fix

Before this increment, the route returned no top-level prompt hash, request id, or route trace id, and `preview_packet.trace_id` was hardcoded.

The first runtime proof hit the still-running old dev server and correctly failed because the new identity fields were absent. The dev proof lane was restarted on port 3017, and the proof then passed.

## What Changed To Fix It

The route now derives identity from the request body and returns it in the response.

## Blockers

No Plan 03.1 blocker.

## Receipt Conclusion

Plan 03.1 is complete:

- `original_user_prompt_hash` returned
- `request_id` returned
- `trace_id` returned
- same prompt produces same prompt hash
- different prompt produces different prompt hash

`INCREMENT_GO_PROVEN`
