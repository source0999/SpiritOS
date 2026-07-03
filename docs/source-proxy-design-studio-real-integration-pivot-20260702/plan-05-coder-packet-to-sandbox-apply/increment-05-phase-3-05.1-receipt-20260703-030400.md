# Increment Receipt: Plan 05.1 Generate Coder Packet

increment_id: `05.1-generate-coder-packet`
plan_id: `05`
phase_id: `3`
started_at: `2026-07-02T22:55:00-04:00`
completed_at: `2026-07-02T23:04:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-24e3574ecc8f-r-packet`
coder_packet_hash: `preview_bb110d8d`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 05.1 changes the generated coder packet target from the Design Studio preview shell to the canonical `/coding/design-demo` sandbox. It does not apply a diff and does not use `execute-approved`.

Exact files changed by this increment:

- `src/app/v1/coding/design-studio/preview/route.ts`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.1-route-runtime-20260703T030100Z.cjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.1-coder-packet-20260703T030100Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/increment-05-phase-3-05.1-receipt-20260703-030400.md`

## Runtime Proof

Evidence artifact:

- coder packet JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.1-coder-packet-20260703T030100Z.json`
- coder packet JSON sha256: `52105cebaa487a69904095f384ca23b6d95d44a5247729f7d85bd59ac4fd4b1d`
- runtime harness sha256: `c686b53baddcf8e765d51b8d177ba1d8962f85c4f8f7beedb5ea62faa7e85f44`
- route implementation sha256 after edit: `b00112d31bb22bac243ab327979339517de3bf4fb509657196855326045a92b6`

Runtime result:

```text
http_status: 200
trace_id: design-studio-trace-24e3574ecc8f-r-packet
model_invocation_event_id: ollama-phi4-mini-latest-67f088ad3d99
design_packet_hash: 999875b640e1270e38555d435c85a150573515c24d6e0a25d8f0022c039f6cf2
coder_packet_hash: preview_bb110d8d
```

Required proof:

```text
references_design_packet_hash: true
target_limited_to_design_demo_sandbox: true
no_production_route_apply: true
top_level_bounded_packet_matches: true
execute_approved_used: false
```

Generated coder packet target:

```text
allowed_files: src/app/coding/design-demo/page.tsx
target_files: src/app/coding/design-demo/page.tsx
sandbox_apply_target: /coding/design-demo
production_apply_authority: false
```

## Commands Run

Runtime route proof:

```text
node <inline route transpile and POST coder-packet proof script>
```

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 05.1 because this increment generates the coder packet only and does not apply a diff or perform browser proof:

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

Before this increment, the preview route's generated coder packet targeted Design Studio shell files and the preview route itself. That was not the canonical Plan 05 sandbox target.

## What Changed To Fix It

The generated coder packet now:

- references the originating `design_packet_hash`
- targets only `src/app/coding/design-demo/page.tsx`
- declares `sandbox_apply_target: /coding/design-demo`
- keeps `production_apply_authority: false`
- aligns the legacy top-level `bounded_coder_packet` with the canonical coder packet

## Blockers

No Plan 05.1 blocker. No sandbox diff was applied in this increment.

## Receipt Conclusion

Plan 05.1 is complete:

- `coder_packet_hash` generated
- coder packet references `design_packet_hash`
- target limited to design-demo sandbox
- no production route apply
- `execute-approved` not used

`INCREMENT_GO_PROVEN`
