# Increment Receipt: Plan 02.1 Real Design Studio Network Path

increment_id: `02.1-wire-shell-to-backend-route`
plan_id: `02`
phase_id: `2`
started_at: `2026-07-02T21:17:00-04:00`
completed_at: `2026-07-02T21:41:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
network_proof_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z-network.json`
dom_snapshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z-dom.html`
desktop_screenshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z.png`
desktop_screenshot_hash: `7a5149b24f8e4b65784e735c4722695d65a66fe8342ae11e65eb4b04baca2c98`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 02.1 wires `DesignStudioShell` to the existing backend preview route and proves the canonical `/coding` composer still starts the same real Design Studio network path.

Exact files changed by this increment:

- `src/components/coding/DesignStudioShell.tsx`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-helper-20260703T013810Z-dom.html`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-helper-20260703T013810Z-network.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-helper-20260703T013810Z-page-info.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-helper-20260703T013810Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z-dom.html`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z-network.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z-page-info.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/increment-02-phase-2-02.1-receipt-20260703-014100.md`

Forbidden files checked and not modified by this increment:

- `src/app/v1/actions/execute-approved/route.ts`
- model/provider/subagent lanes
- sandbox apply, critic, acceptance, repair, screenshot verifier, and writeback runtime paths
- external dependency manifests

## Implementation

`DesignStudioShell` now:

- keeps the preview-only guardrails visible
- exposes an editable prompt field
- posts to `/v1/coding/design-studio/preview`
- sends `prompt`, `request_id`, and `target_surface`
- sends `x-design-studio-request-id`
- renders returned outcome, reason, request id, design packet id, trace id, consumer event id, DesignDNA outcome, coder packet outcome, critic outcome, and bounded coder target files
- keeps apply, commit, push, memory write, and sandbox apply unavailable

Source inspection confirmed the shell route call and live-response rendering in `src/components/coding/DesignStudioShell.tsx`.

## Browser Proof

Local dev proof used:

```text
http://localhost:3016
```

Why: the earlier 3015 dev lane became socket-wedged after repeated browser probes. A fresh 3016 lane was started and warmed until both `/coding/design-studio` and `/coding` returned `200`.

### Helper Shell Proof

Browser opened:

```text
http://localhost:3016/coding/design-studio
```

Actions:

1. Filled the visible prompt textarea.
2. Clicked `Preview packet`.
3. Observed `POST /v1/coding/design-studio/preview`.
4. Verified request body included the original prompt.
5. Verified UI changed from waiting state to live response data.

Result:

```json
{
  "responseStatus": 200,
  "backendReceivedOriginalPrompt": true,
  "uiChangedFromLiveResponse": true,
  "visibleOutcome": "DESIGN_PACKET_PREVIEW",
  "visibleDesignPacketId": "preview-shell-local",
  "visibleTraceId": "preview-shell-trace"
}
```

Helper shell artifacts:

- network log: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-helper-20260703T013810Z-network.json`
- network log sha256: `fdf0a604e39eaf752b48263962e2a29a678be06a32e45f9fc4a0089c12f80d5d`
- DOM snapshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-helper-20260703T013810Z-dom.html`
- DOM snapshot sha256: `c1dc3226b5dbd1cdbd3b6cd253c651ff91c5ef892cc4941060aebf20155deccf`
- screenshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-helper-20260703T013810Z.png`
- screenshot sha256: `4433d04d72d9284349322fe0e6c43ffb5bc1dbf53b952deb4977bc0440f08173`
- page info: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-helper-20260703T013810Z-page-info.json`
- page info sha256: `dcf4070941936cc1ed493bfde1639c6e0b9071447dc685a2b23bed27e3a833ed`

### Real `/coding` Proof

Browser opened:

```text
http://localhost:3016/coding
```

Actions:

1. Filled the existing `/coding` task composer textarea.
2. Selected `Design Studio` mode.
3. Clicked `Start Design Studio`.
4. Observed `POST /v1/coding/design-studio/preview`.
5. Verified request body included the original prompt.
6. Verified the `/coding` UI rendered endpoint `:200`, request id, and trace id.

Result:

```json
{
  "responseStatus": 200,
  "backendReceivedOriginalPrompt": true,
  "uiChangedFromLiveResponse": true,
  "visibleEndpoint": "/v1/coding/design-studio/preview:200",
  "visibleTraceId": "preview-shell-trace"
}
```

Real `/coding` artifacts:

- network log: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z-network.json`
- network log sha256: `d008982d8df849139fb6d15604604dc7dbdb4a6b0449709b21068fe629160af1`
- DOM snapshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z-dom.html`
- DOM snapshot sha256: `9bd8475d10d4c22eaa0c262de38519d0650bcfaedf37511f1e02718fde34a353`
- screenshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z.png`
- screenshot sha256: `7a5149b24f8e4b65784e735c4722695d65a66fe8342ae11e65eb4b04baca2c98`
- page info: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-02-real-design-studio-network-path/evidence/plan-02.1-coding-20260703T013849Z-page-info.json`
- page info sha256: `febec3727ad820e4b417cad3b3dc757b938d8c4c5311d0690f55cfb29faabf3e`

## Commands Run

Source inspection:

```text
rg -n -F 'x-design-studio-request-id' src/components/coding/DesignStudioShell.tsx
rg -n -F 'Live preview response received' src/components/coding/DesignStudioShell.tsx
git diff -- src/components/coding/DesignStudioShell.tsx
```

Browser proof:

```text
node <inline Playwright helper shell proof script>
node <inline Playwright real /coding proof script>
```

Result: PASS.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 02.1 because this increment does not invoke a model, apply a sandbox diff, run a screenshot verifier, run an anti-template critic, repair, accept, or write back:

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

Before this increment, `DesignStudioShell` displayed static local packet rows and did not call the backend preview route.

During proof, the original 3015 dev lane became socket-wedged. A fresh 3016 lane was started. The helper shell also needed a warmed browser/hydration wait before the app button emitted the route request; once warmed, the real route request and live UI state were stable.

## What Changed To Fix It

`DesignStudioShell` was changed from static preview rows to a live preview-only backend client. The canonical `/coding` composer path from Plan 01 remained unchanged and still starts the Design Studio preview route.

## Blockers

No Plan 02.1 blocker.

## Receipt Conclusion

Plan 02.1 is complete:

- source inspection confirms real route call
- helper shell browser proof confirms backend route call
- real `/coding` browser proof confirms canonical route starts from `/coding`
- backend received original prompt/body in both proofs
- UI changed based on live response data
- no `execute-approved` path was added

`INCREMENT_GO_PROVEN`
