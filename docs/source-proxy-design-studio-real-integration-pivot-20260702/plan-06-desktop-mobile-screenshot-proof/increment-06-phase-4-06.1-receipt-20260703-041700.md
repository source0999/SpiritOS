# Increment Receipt: Plan 06.1 Desktop Screenshot

increment_id: `06.1-desktop-screenshot`
plan_id: `06`
phase_id: `4`
started_at: `2026-07-03T00:00:00-04:00`
completed_at: `2026-07-03T00:17:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-24e3574ecc8f-r-packet`
diff_hash: `69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192`
sandbox_apply_receipt_id: `sandbox-apply-69f25b09d872`
desktop_screenshot_hash: `df58f5c18102b054cb9e055fb268b7d288634a3c00b38190cf5c3d386f31b50d`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 06.1 captures a real desktop screenshot after the Plan 05 sandbox apply and ties it structurally to the same trace, `sandbox_apply_receipt_id`, and `diff_hash`.

Exact files changed by this increment:

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06-devserver-3023.out.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06-devserver-3023.err.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.1-desktop-1440x900-20260703T040800Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.1-desktop-screenshot-20260703T040800Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.1-desktop-default-20260703T041400Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.1-desktop-screenshot-20260703T041400Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/increment-06-phase-4-06.1-receipt-20260703-041700.md`

## Desktop Screenshot Proof

Final green evidence artifact:

- desktop screenshot JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.1-desktop-screenshot-20260703T041400Z.json`
- desktop screenshot JSON sha256: `2a3c2d5ea4d26c67f2ad487e2b5da842668054ecc93fe436725d13ae2ca7f2f5`
- desktop screenshot path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.1-desktop-default-20260703T041400Z.png`
- desktop screenshot sha256: `df58f5c18102b054cb9e055fb268b7d288634a3c00b38190cf5c3d386f31b50d`
- screenshot size bytes: `104475`

Required provenance:

```text
sandbox_apply_receipt_id: sandbox-apply-69f25b09d872
diff_hash: 69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192
trace_id: design-studio-trace-24e3574ecc8f-r-packet
rendered_route: /coding/design-demo
viewport: 1280x720 desktop-default
captured_after_apply: true
file_non_empty: true
```

Page proof:

```text
h1: Applied Design Studio sandbox packet
hasTrace: true
hasDesignHash: true
hasCoderHash: true
hasApplied: true
```

The first 1440x900 override capture is retained as non-GO evidence because the rendered layout collapsed into a narrow column despite the reported viewport. It is not used as desktop screenshot GO.

## Commands Run

Dev server:

```text
npm run dev -- -p 3023
```

Browser capture:

```text
in-app browser -> http://127.0.0.1:3023/coding/design-demo
```

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 06.1 because this increment captures desktop only:

- `mobile_screenshot_path`
- `mobile_screenshot_hash`
- `network_proof_path`
- `anti_template_verdict_id`
- `critic_verdict_id`
- `repair_attempt_ids`
- `retest_receipt_id`
- `acceptance_id`

## What Failed Before Fix

The first explicit 1440x900 viewport screenshot produced a non-empty file but not a credible desktop layout. It is retained as non-GO evidence.

## What Changed To Fix It

The browser viewport override was reset and the page was recaptured at the normal desktop viewport. The final screenshot has a 1280px browser width, visible desktop layout, trace markers, and a non-empty screenshot hash.

## Blockers

No Plan 06.1 blocker. The 3023 dev server remains active only to continue immediately into Plan 06.2 mobile capture.

## Receipt Conclusion

Plan 06.1 is complete:

- desktop screenshot path recorded
- sha256 hash recorded
- trace ID recorded
- `sandbox_apply_receipt_id` recorded
- `diff_hash` recorded
- screenshot file is non-empty

`INCREMENT_GO_PROVEN`
