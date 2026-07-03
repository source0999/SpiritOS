# Increment Receipt: Plan 03.2 Generated Design Packet

increment_id: `03.2-generated-design-packet`
plan_id: `03`
phase_id: `3`
started_at: `2026-07-02T21:52:00-04:00`
completed_at: `2026-07-02T22:00:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
design_packet_hash: `f638eb656cbdd51da57576e8ceb34c8ab3ab608f7f985e5fabf9323a87f21d76`
trace_id: `design-studio-trace-2ab6bbac5728-equest-a`
request_id: `plan-03-2-request-a`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 03.2 replaces the fixed design packet literal with prompt-derived structured packet fields and a real `design_packet_hash`.

Exact files changed by this increment:

- `src/app/v1/coding/design-studio/preview/route.ts`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-03-real-packet-generation/evidence/plan-03.2-generated-design-packet-20260703T015802Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-03-real-packet-generation/increment-03-phase-3-03.2-receipt-20260703-020000.md`

## Implementation

The route now derives a structured design packet from the prompt:

- `intent`
- `audience`
- `page_app_target`
- `constraints`
- `reference_inputs`
- `visual_direction`
- `accessibility_notes`
- `risk_flags`

The packet includes `design_packet_hash`, `design_packet_id`, `derivation_source`, bounded coder packet fields, and the route trace id.

## Runtime Proof

Live route:

```text
http://localhost:3018/v1/coding/design-studio/preview
```

Proof result:

```json
{
  "designPacketHashA": "f638eb656cbdd51da57576e8ceb34c8ab3ab608f7f985e5fabf9323a87f21d76",
  "designPacketHashB": "97df7cfd1bae7f493d5a862cdd4e0625c41b4919aa50473fbabb83b9a1c851c8",
  "hashesDifferent": true,
  "fieldsPresent": true,
  "packetAIsNotRawPromptOnly": true,
  "packetBIsNotRawPromptOnly": true
}
```

Prompt A derived:

```text
intent: increase perceived product quality; tighten operator workflow clarity; make interaction keyboard-first
audience: operators reviewing Source Proxy evidence; keyboard-heavy power users; design reviewers
visual_direction: premium restrained product surface; dense console workbench; precise technical evidence surface
```

Prompt B derived:

```text
intent: improve mobile usability; create editorial scanning rhythm
audience: mobile reviewers; design reviewers
visual_direction: editorial spacious hierarchy; mobile-first stacked controls
```

Evidence artifact:

- route proof JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-03-real-packet-generation/evidence/plan-03.2-generated-design-packet-20260703T015802Z.json`
- route proof JSON sha256: `a4c882ad3fe2910f4064c877144c8430752367dfe5a47a66c8fa367d7708469f`

## Commands Run

Runtime proof:

```text
node <inline route POST proof script>
```

Result: PASS.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 03.2 because this increment does not invoke a model, apply a sandbox diff, run a screenshot verifier, run an anti-template critic, repair, accept, or write back:

- `model_invocation_event_id`
- `provider_model_name`
- `input_hash`
- `output_hash`
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

Before this increment, the route returned a fixed `messy-prompt-preview-local` design packet with fixed motif/style fields. Different prompts could not produce different design packet hashes.

## What Changed To Fix It

Prompt-derived packet structuring and stable JSON hashing were added to the route.

## Blockers

No Plan 03.2 blocker.

## Receipt Conclusion

Plan 03.2 is complete:

- two messy prompts produced different `design_packet_hash` values
- required structured packet fields are present
- packet is not a raw prompt re-serialization
- fixed default packet no longer counts as product proof

`INCREMENT_GO_PROVEN`
