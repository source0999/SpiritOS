# Increment Receipt: Plan 06.2 Mobile Screenshot

increment_id: `06.2-mobile-screenshot`
plan_id: `06`
phase_id: `4`
started_at: `2026-07-03T00:17:00-04:00`
completed_at: `2026-07-03T00:28:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-24e3574ecc8f-r-packet`
diff_hash: `69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192`
sandbox_apply_receipt_id: `sandbox-apply-69f25b09d872`
mobile_screenshot_hash: `ef42762820aaf3f98c0e913ee32645743c26d1d1d89bc46208a1ca346f2469a9`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 06.2 captures a real mobile screenshot after the Plan 05 sandbox apply and ties it structurally to the same trace, `sandbox_apply_receipt_id`, and `diff_hash`. It also records measured horizontal overflow.

Exact files changed by this increment:

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.2-mobile-390x844-20260703T042100Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.2-mobile-screenshot-20260703T042100Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.2-mobile-viewport-390x844-20260703T042500Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.2-mobile-screenshot-20260703T042500Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/increment-06-phase-4-06.2-receipt-20260703-042800.md`

## Mobile Screenshot Proof

Final green evidence artifact:

- mobile screenshot JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.2-mobile-screenshot-20260703T042500Z.json`
- mobile screenshot JSON sha256: `8b483bd31675eae55125ff21984b8e0822413a5a62458dda9e83a77132f39c65`
- mobile screenshot path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.2-mobile-viewport-390x844-20260703T042500Z.png`
- mobile screenshot sha256: `ef42762820aaf3f98c0e913ee32645743c26d1d1d89bc46208a1ca346f2469a9`
- screenshot size bytes: `36788`

Required provenance:

```text
sandbox_apply_receipt_id: sandbox-apply-69f25b09d872
diff_hash: 69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192
trace_id: design-studio-trace-24e3574ecc8f-r-packet
rendered_route: /coding/design-demo
viewport: 390x844 mobile-viewport
captured_after_apply: true
file_non_empty: true
```

Overflow measurement:

```text
inner_width: 390
client_width: 390
scroll_width: 390
overflow_x: 0
no_horizontal_overflow: true
```

Page proof:

```text
h1: Applied Design Studio sandbox packet
hasTrace: true
hasDesignHash: true
hasCoderHash: true
hasApplied: true
```

The first mobile full-page capture is retained as non-GO evidence because browser screenshot stitching duplicated top content. The final GO artifact uses a viewport screenshot.

## Commands Run

Browser capture:

```text
in-app browser -> http://127.0.0.1:3023/coding/design-demo
```

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 06.2 because this increment captures mobile only:

- `network_proof_path`
- `anti_template_verdict_id`
- `critic_verdict_id`
- `repair_attempt_ids`
- `retest_receipt_id`
- `acceptance_id`

## What Failed Before Fix

The first mobile full-page screenshot was non-empty and overflow-free, but the browser's full-page stitching duplicated content vertically. It is retained as non-GO evidence.

## What Changed To Fix It

The final mobile screenshot uses a 390x844 viewport capture. It is non-empty, visually credible, linked to the same apply trace, and has `overflow_x: 0`.

## Blockers

No Plan 06.2 blocker. The 3023 dev server remains active only to continue immediately into Plan 06.3.

## Receipt Conclusion

Plan 06.2 is complete:

- mobile screenshot path recorded
- sha256 hash recorded
- trace ID recorded
- `sandbox_apply_receipt_id` recorded
- `diff_hash` recorded
- no measurable horizontal overflow

`INCREMENT_GO_PROVEN`
