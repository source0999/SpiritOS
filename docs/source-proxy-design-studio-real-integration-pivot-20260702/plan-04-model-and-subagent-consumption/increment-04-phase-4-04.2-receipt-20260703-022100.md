# Increment Receipt: Plan 04.2 Live Model Invocation

increment_id: `04.2-live-model-subagent-invocation`
plan_id: `04`
phase_id: `4`
started_at: `2026-07-02T22:12:00-04:00`
completed_at: `2026-07-02T22:21:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-5c4b6d484172--2-model`
model_invocation_event_id: `ollama-phi4-mini-latest-9f74f41c8397`
provider_model_name: `phi4-mini:latest`
input_hash: `8d1de6e235634307071d0933fc047dfeb7a0412ccd7aa8a4539735b45150d41a`
output_hash: `9f74f41c8397c725c793971934c1a4be4c5347fb7610f349a023b052c7759b3a`
design_packet_hash: `368d458498009ffba23485e6cdc2fa3c2a5d382883f3d4bff03c2be6e0b06f1d`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 04.2 wires and proves at least one live model invocation in the Design Studio preview route. The provider is local Ollama using `phi4-mini:latest`; no OpenAI, Anthropic, Mac worker, Scout, Cartographer, Graphify, memory graph, or new external dependency was added.

Exact files changed by this increment:

- `src/app/v1/coding/design-studio/preview/route.ts`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.2-route-runtime-20260703T021915Z.cjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.2-live-model-invocation-20260703T021915Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/increment-04-phase-4-04.2-receipt-20260703-022100.md`

## Live Invocation Proof

The actual route implementation was executed with real `Request` objects after transpiling the current route module for direct runtime proof. This is runtime route execution, not source-text proof.

Evidence artifact:

- runtime evidence JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.2-live-model-invocation-20260703T021915Z.json`
- runtime evidence JSON sha256: `8b235bd9b538f1d548bfef743e52077d8ae2a3f2f4441f4709050f709b76f15a`
- transpiled runtime harness sha256: `491dfbc507a15d1c264e29c3f8233adac4a6695f9fcd90986d165248f99118dc`
- route implementation sha256 after edit: `eff5de6a8efd8b31787b2ccdc64acce1e76a7f0bd4e2cb88a68949ee7817e71b`

Runtime result:

```text
model_call_made: true
provider_call_made: true
provider_model_name: phi4-mini:latest
model_invocation_event_id: ollama-phi4-mini-latest-9f74f41c8397
byte_count: 143
```

Short non-sensitive output excerpt:

```text
Incorporate tactile feedback elements into the high-quality materials to enhance user engagement and reinforce a seamless, intuitive interface.
```

## Material Change Rule

The same prompt was run once through the no-model fallback path and once with the live Ollama model probe enabled.

```text
no_model_design_packet_hash: 9c2d7b87e5db3cebba67800f16444bb5eb2c8bea9e30537b5dee81f4fd7ba521
model_design_packet_hash:    368d458498009ffba23485e6cdc2fa3c2a5d382883f3d4bff03c2be6e0b06f1d
materially_changed:          true
```

The hashes differ, so the R4 material-change requirement is satisfied.

## Commands Run

Runtime route proof:

```text
node <inline route transpile and POST invocation script>
```

The proof script invoked the exported route `POST` function twice with real `Request` objects and recorded both fallback and model-enriched results.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 04.2 because this increment proves model invocation only and does not perform sandbox apply or browser capture:

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

Before this increment, the Design Studio preview route only produced deterministic fallback packets. It had no proven live provider invocation and no route-level model output linked to a changed `design_packet_hash`.

## What Changed To Fix It

The preview route now accepts an explicit `model_probe` request field. When enabled, it calls local Ollama `/api/generate`, records invocation metadata, adds the returned guidance to the design packet, and recomputes the packet hash.

## Blockers

No Plan 04.2 blocker. OpenAI, Anthropic, Mac worker, Scout, Cartographer, Graphify, and memory graph remain unavailable or out of scope and are not counted as live.

## Receipt Conclusion

Plan 04.2 is complete:

- live Ollama invocation proved
- provider/model name recorded
- input and output hashes recorded
- non-sensitive output excerpt recorded
- model output materially changed the design packet hash
- no fake fallback success claimed

`INCREMENT_GO_PROVEN`
