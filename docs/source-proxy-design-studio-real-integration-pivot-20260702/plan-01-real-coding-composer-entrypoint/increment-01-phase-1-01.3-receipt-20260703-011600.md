# Increment Receipt: Plan 01.3 Existing `/coding` Regression

increment_id: `01.3-existing-coding-regression`
plan_id: `01`
phase_id: `1`
started_at: `2026-07-02T21:12:00-04:00`
completed_at: `2026-07-02T21:16:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
network_proof_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-network.json`
dom_snapshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-dom.html`
desktop_screenshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-failure.png`
desktop_screenshot_hash: `2f98c8a325329637f968148638a96201483efedc4cacc50c5a4843db7d3217fb`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 01.3 is regression proof only. It verifies that the existing ordinary `/coding` flow still works as an ordinary coding flow after Plan 01.2 added Design Studio mode.

Exact files changed by this increment:

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-dom.html`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-failure.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-network.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-page-info.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/increment-01-phase-1-01.3-receipt-20260703-011600.md`

Forbidden files checked and not modified by this increment:

- `src/app/v1/actions/execute-approved/route.ts`
- `src/app/v1/coding/design-studio/preview/route.ts`
- `src/components/coding/DesignStudioShell.tsx`
- `src/components/coding/CodingCommandCenterShell.tsx`
- model/provider/subagent lanes
- sandbox apply, critic, acceptance, repair, screenshot verifier, and writeback runtime paths

## Browser Proof

A real Playwright Chromium browser opened:

```text
http://localhost:3015/coding
```

User-like browser actions performed:

1. Clicked `Reverse trial edits and clear results`.
2. Verified selected-prompt/trial clearing was visible.
3. Clicked the ordinary `Coding` composer mode.
4. Filled the existing task composer textarea.
5. Clicked `Start coding`.
6. Captured the ordinary coding failure state.

The browser test intercepted only `/v1/decisions/prompt-packet` and returned a controlled `503` to force the ordinary failure UI without risking `execute-approved` or file mutation. This is frontend regression proof, not a backend/provider success claim.

Browser proof result:

```json
{
  "url": "http://localhost:3015/coding",
  "promptPacketResponseStatus": 503,
  "ordinaryCodingModeSelected": true,
  "ordinaryPromptPacketSubmitted": true,
  "designStudioPreviewNotCalled": true,
  "executeApprovedNotCalled": true,
  "failureStateVisible": true,
  "forcedFailureDetailCapturedInDom": true,
  "selectedPromptClearActionClicked": true,
  "selectedPromptClearEvidenceVisible": true
}
```

Visible failure text included:

```text
Task could not start. Copy diagnostics for details.
FAIL: THE RUN FAILED BEFORE A USEFUL RESULT.
ROUTE
/v1/decisions/prompt-packet
TECHNICAL_DETAIL
Plan 01.3 controlled prompt-packet failure for ordinary coding regression proof.
```

Visible selected-prompt/trial clearing text included:

```text
Cleared trial suite results. Run again when ready.
No applied selected-prompt edits to reverse. Results cleared.
```

Evidence artifacts:

- network log: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-network.json`
- network log sha256: `ca0adc99664b82e0a5e2def974146930186284252ce8feb1a4809e0cd3c74a99`
- DOM snapshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-dom.html`
- DOM snapshot sha256: `0673e64aee204db8eb45bf1cea34d762f6f61813ec60b50cf3bcbd831209180b`
- screenshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-failure.png`
- screenshot sha256: `2f98c8a325329637f968148638a96201483efedc4cacc50c5a4843db7d3217fb`
- page info: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.3-coding-regression-20260703T011409Z-page-info.json`
- page info sha256: `6dccfa552066240502fd1799628fca26f873b2caf0496efd24ff7723fa2cbb45`

## Commands Run

Browser proof:

```text
node <inline Playwright Chromium proof script>
```

Result: PASS.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 01.3 because this increment does not invoke a model, apply a sandbox diff, run a screenshot verifier, run an anti-template critic, repair, accept, or write back:

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

No product defect was found in this increment. A first 01.3 proof run expected the forced failure detail to be visible outside diagnostics. The app rendered the main failure state visibly and kept the technical detail in diagnostics. The assertion was corrected to require visible failure state and DOM-captured technical detail.

## What Changed To Fix It

No product code was changed during Plan 01.3. Evidence and this receipt were added only.

## Blockers

No Plan 01.3 blocker.

## Receipt Conclusion

Plan 01.3 is complete:

- ordinary coding prompt path still submits to `/v1/decisions/prompt-packet`
- selected-prompt/trial clearing still works
- failure state is visible
- Design Studio preview was not called during ordinary coding regression
- `execute-approved` was not called
- no unrelated `/coding` UI regression was observed in the proof surface

`INCREMENT_GO_PROVEN`
