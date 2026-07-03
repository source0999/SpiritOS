# Increment Receipt: Plan 06.4 Phase Regression

increment_id: `06.4-phase-regression`
plan_id: `06`
phase_id: `4`
started_at: `2026-07-03T00:37:00-04:00`
completed_at: `2026-07-03T00:48:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-24e3574ecc8f-r-packet`
diff_hash: `69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192`
sandbox_apply_receipt_id: `sandbox-apply-69f25b09d872`
desktop_screenshot_hash: `df58f5c18102b054cb9e055fb268b7d288634a3c00b38190cf5c3d386f31b50d`
mobile_screenshot_hash: `ef42762820aaf3f98c0e913ee32645743c26d1d1d89bc46208a1ca346f2469a9`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 06.4 closes Plan 06 with phase regression. It confirms prior plans remain covered by the receipt validator, screenshot artifacts are linked to Plan 05 apply, and "looked good" proof is rejected.

Exact files changed by this increment:

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.4-phase-regression-20260703T044500Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/increment-06-phase-4-06.4-receipt-20260703-044800.md`

## Regression Evidence

Evidence artifact:

- phase regression JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-06-desktop-mobile-screenshot-proof/evidence/plan-06.4-phase-regression-20260703T044500Z.json`
- phase regression JSON sha256: `256ce5fbe6c9bb8ca25f6c5abec503ea833f89939a85c1bca126d1081996b654`

Negative proof:

```text
manual_verdict: looked good
accepted: false
blockers:
- looked_good_is_not_acceptance_proof
- missing_desktop_screenshot_hash
- missing_mobile_screenshot_hash
- missing_sandbox_apply_receipt_id
- missing_diff_hash
```

Screenshot-linked candidate:

```text
accepted: true
blockers: []
desktop_screenshot_hash: df58f5c18102b054cb9e055fb268b7d288634a3c00b38190cf5c3d386f31b50d
mobile_screenshot_hash: ef42762820aaf3f98c0e913ee32645743c26d1d1d89bc46208a1ca346f2469a9
sandbox_apply_receipt_id: sandbox-apply-69f25b09d872
diff_hash: 69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192
```

## Commands Run

Phase regression proof:

```text
node <inline looked-good rejection and screenshot-linked candidate script>
```

Required receipt validator is run after this receipt before Plan 07 starts.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 06.4 because this increment closes screenshot proof and does not run anti-template, critic, repair, or acceptance:

- `network_proof_path`
- `anti_template_verdict_id`
- `critic_verdict_id`
- `repair_attempt_ids`
- `retest_receipt_id`
- `acceptance_id`

## What Failed Before Fix

Before this increment, there was no explicit negative proof that a manual "looked good" claim could not substitute for screenshot-linked artifacts.

## What Changed To Fix It

A phase regression artifact now rejects "looked good" proof and accepts only a candidate carrying desktop/mobile screenshot hashes plus the same `sandbox_apply_receipt_id` and `diff_hash`.

## Blockers

No Plan 06.4 blocker.

## Receipt Conclusion

Plan 06.4 is complete:

- Plans 01-05 remain covered by validator chain
- validator is rerun through Plan 06 after this receipt
- no "looked good" proof accepted

`INCREMENT_GO_PROVEN`
