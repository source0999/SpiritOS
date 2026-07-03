# Increment Receipt: Plan 04.5 Phase Regression

increment_id: `04.5-phase-regression`
plan_id: `04`
phase_id: `4`
started_at: `2026-07-02T22:34:00-04:00`
completed_at: `2026-07-02T22:53:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-24e3574ecc8f--5-model`
model_invocation_event_id: `ollama-phi4-mini-latest-67f088ad3d99`
provider_model_name: `phi4-mini:latest`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 04.5 closes Plan 04 with regression proof. It confirms the current route still produces Design Studio packets, DesignDNA, coder packet preview metadata, a live model invocation, and a linked model trace after the Plan 04.4 failure-behavior change.

Exact files changed by this increment:

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.5-route-runtime-20260703T024200Z.cjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.5-phase-regression-20260703T024200Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.5-route-runtime-20260703T024600Z.cjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.5-phase-regression-20260703T024600Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.5-route-runtime-20260703T025000Z.cjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.5-phase-regression-20260703T025000Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/increment-04-phase-4-04.5-receipt-20260703-025300.md`

## Regression Evidence

Final green evidence artifact:

- phase regression JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.5-phase-regression-20260703T025000Z.json`
- phase regression JSON sha256: `c64e5eedecfb10c7fadbd1b083ec770ba25b74e8606ae48d8ca777deb6eb18f6`
- final route runtime harness sha256: `c8d316cdbd2b6bde54c3f4330ee674f34f7cc0641b1e0425ab132190d20f5028`

Earlier checker attempts were retained as evidence and were not used as GO:

```text
plan-04.5-phase-regression-20260703T024200Z.json sha256 624139edae3db26d047e3ef9fd173676feac4b60b4db1b42fbb7c0366ac7b34e
plan-04.5-phase-regression-20260703T024600Z.json sha256 ab9ca9ac22b797b7e8a5c523f81f33d455f3aa4d32295545342d662c844feffc
```

Final route proof:

```text
fallback_status: 200
model_status: 200
fallback_outcome: DESIGN_PACKET_PREVIEW
model_outcome: DESIGN_PACKET_PREVIEW
fallback_design_packet_hash: 616f2f53ec75bd72f461ecc01a1caf53f39548186acdc690d6e541f1882ac734
model_design_packet_hash: 999875b640e1270e38555d435c85a150573515c24d6e0a25d8f0022c039f6cf2
designdna_hash: ca62309aa2854cf88790b6810a82e879fe56002aa4cc67a762f6398342805dbd
coder_packet_hash: preview_4bce3ce6
response_trace_id: design-studio-trace-24e3574ecc8f--5-model
model_invocation_trace_id: design-studio-trace-24e3574ecc8f--5-model
model_invocation_event_id: ollama-phi4-mini-latest-67f088ad3d99
model_call_made: true
provider_call_made: true
material_hash_changed: true
model_trace_linked_to_response: true
```

## Commands Run

Attempted focused Vitest regression:

```text
npx vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts src/app/v1/coding/design-studio/preview/__tests__/route.test.ts src/components/coding/__tests__/design-studio-shell.test.tsx src/components/coding/__tests__/coding-cockpit-shell.test.tsx --reporter=dot
```

Result:

```text
TIMED_OUT_124S_NO_PASS_CLAIMED
```

Attempted inherited writeback-only Vitest regression:

```text
npx vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=dot
```

Result:

```text
TIMED_OUT_64S_NO_PASS_CLAIMED
```

Final runtime route regression:

```text
node <inline route transpile and POST regression script>
```

Result:

```text
PASS
```

Required receipt validator is run after this receipt before Plan 05 starts.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 04.5 because this increment closes model/subagent consumption and does not perform sandbox apply or browser capture:

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

The first two 04.5 checker runs used incorrect assertions against the current route shape and were retained as non-GO evidence. Focused Vitest attempts also timed out and are not claimed as passing.

## What Changed To Fix It

The final runtime proof used the actual route contract:

- DesignDNA hash is at `design_dna_result.design_dna.designdna_hash`
- model invocation trace is linked to the response trace
- coder packet preview provides `coder_packet_hash` but does not currently expose its own `trace_id`

## Blockers

No Plan 04.5 blocker. Vitest did not return a usable pass signal in this environment, so it is not used as GO evidence.

## Receipt Conclusion

Plan 04.5 is complete:

- Plans 01-03 receipt chain is revalidated by the closeout validator
- current route runtime proof still produces packet, DesignDNA, and coder packet output
- live model invocation is linked to the same response trace
- validator is rerun through Plan 04 before moving to Plan 05

`INCREMENT_GO_PROVEN`
