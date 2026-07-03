# Increment Receipt: Plan 02.2 Remove Hardcoded Success As Product Proof

increment_id: `02.2-remove-hardcoded-success-as-product-proof`
plan_id: `02`
phase_id: `2`
started_at: `2026-07-02T21:41:00-04:00`
completed_at: `2026-07-02T21:44:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
network_proof_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z-network.json`
dom_snapshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z-dom.html`
desktop_screenshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z.png`
desktop_screenshot_hash: `7bdde10335e0212e30573417d6dff7356af30ff3f948aa0e22e25b6fa08a4325`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 02.2 proves the Design Studio preview UI is not accepting hardcoded success. It uses live route responses for success and blocked states, then a controlled browser-level `503` to prove the UI changes to failure.

Exact files changed by this increment:

- `src/components/coding/DesignStudioShell.tsx`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z-dom.html`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z-network.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z-page-info.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/increment-02-phase-2-02.2-receipt-20260703-014400.md`

Forbidden files checked and not modified by this increment:

- `src/app/v1/actions/execute-approved/route.ts`
- model/provider/subagent lanes
- sandbox apply, critic, acceptance, repair, screenshot verifier, and writeback runtime paths
- external dependency manifests

## Implementation

`DesignStudioShell` now has an editable target field. It sends `target_surface` only when the field is non-empty, which lets the real backend return `ASK_CLARIFY_TARGET` for ambiguous prompts instead of the UI always succeeding through a fixed target.

## Browser Proof

Browser opened:

```text
http://localhost:3016/coding/design-studio
```

Actions:

1. Submitted successful prompt 1 with target `/coding/design-demo`.
2. Submitted successful prompt 2 with target `/coding/design-demo`.
3. Cleared the target and submitted `make it look premium`.
4. Verified blocked UI from the real backend response.
5. Intercepted the preview route with a controlled `503`.
6. Verified failure UI replaced the prior success state.

Result:

```json
{
  "requestId1": "design-studio-shell-6c829c66-ad73-4ba2-9dd4-05a7a409720e",
  "requestId2": "design-studio-shell-77945cd6-c506-4382-ae6b-0d17f5c47d34",
  "requestIdsDifferent": true,
  "blockedStatus": 200,
  "blockedUiVisible": true,
  "routeFailureStatus": 503,
  "routeFailureUiVisible": true,
  "noHardcodedSuccessAccepted": true
}
```

Visible final failure text included:

```text
Preview route failed. Apply remains locked.
Plan 02.2 forced route failure
```

Blocked response proof included:

```text
Preview route asked for a clearer target.
ASK_CLARIFY_TARGET
```

Evidence artifacts:

- network log: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z-network.json`
- network log sha256: `12591a2d214c63a8a0ab97a38a3196175373eab1a36c52d8d92455dd42338506`
- DOM snapshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z-dom.html`
- DOM snapshot sha256: `2ecd1cd86d3517283c7b7b0763136b65b805cb65ec0c3811f0130cf500426160`
- screenshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z.png`
- screenshot sha256: `7bdde10335e0212e30573417d6dff7356af30ff3f948aa0e22e25b6fa08a4325`
- page info: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.2-no-hardcoded-success-20260703T014236Z-page-info.json`
- page info sha256: `92d149773cbe762027520b389626b916a4807909654c755548a0f74e1ed39542`

## Commands Run

Browser proof:

```text
node <inline Playwright no-hardcoded-success proof script>
```

Result: PASS.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 02.2 because this increment does not invoke a model, apply a sandbox diff, run a screenshot verifier, run an anti-template critic, repair, accept, or write back:

- `original_user_prompt_hash`
- `request_id`
- `trace_id`
- `model_invocation_event_id`
- `provider_model_name`
- `input_hash`
- `output_hash`
- `design_packet_hash`
- `designdna_hash`
- `coder_packet_hash`
- `diff_hash`
- `sandbox_apply_receipt_id`
- `mobile_screenshot_path`
- `mobile_screenshot_hash`
- `anti_template_verdict_id`
- `critic_verdict_id`
- `repair_attempt_ids`
- `retest_receipt_id`
- `acceptance_id`

## What Failed Before Fix

Before this increment, the helper shell always sent a fixed target surface, so the UI could not demonstrate a backend blocked response for a missing target.

## What Changed To Fix It

An editable target field was added to the helper shell. Empty target values are omitted from the route request, allowing the real backend blocked response to surface in UI.

## Blockers

No Plan 02.2 blocker.

## Receipt Conclusion

Plan 02.2 is complete:

- two submissions produced different request IDs
- blocked backend response surfaced as blocked UI
- route failure changed the UI verdict
- hardcoded success was not accepted after blocked/failure responses

`INCREMENT_GO_PROVEN`
