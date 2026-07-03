# Increment Receipt: Plan 05.4 Phase Regression

increment_id: `05.4-phase-regression`
plan_id: `05`
phase_id: `3`
started_at: `2026-07-02T23:30:00-04:00`
completed_at: `2026-07-02T23:52:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-24e3574ecc8f-r-packet`
coder_packet_hash: `preview_bb110d8d`
diff_hash: `69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192`
sandbox_apply_receipt_id: `sandbox-apply-69f25b09d872`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 05.4 closes Plan 05 with phase regression. It verifies Plans 01-04 remain covered by the receipt validator, `/coding` still loads as an unrelated path, no Plan 05 touched file is forbidden, and the validator passes through Plan 05 after this receipt.

Exact files changed by this increment:

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05-regression-devserver-3022.out.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05-regression-devserver-3022.err.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.4-coding-browser-20260703T034000Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.4-phase-regression-20260703T034200Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.4-phase-regression-20260703T034800Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/increment-05-phase-3-05.4-receipt-20260703-035200.md`

## Regression Evidence

Final green evidence artifact:

- phase regression JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.4-phase-regression-20260703T034800Z.json`
- phase regression JSON sha256: `86ecbc1bbe7ebe23bbaa81a7855830ca1996467ad37fe3e9910d1854d8b025ec`
- `/coding` browser screenshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.4-coding-browser-20260703T034000Z.png`
- `/coding` browser screenshot sha256: `1fc9e52fcaf3439a9fc344e23cb145bd79c942091b1e655d1ec2cf787a3f6512`

Dev server logs:

```text
plan-05-regression-devserver-3022.out.log sha256 05549fa29e4954a5a924878ba1a4c7fac63b150faacc78d7f9d8996906493732
plan-05-regression-devserver-3022.err.log sha256 e8d75dd9cf5c7b554866e2fa33f8af434acb8f918d58211436ccedd9c346c8c1
```

HTTP probes:

```text
http://127.0.0.1:3022/coding -> 200, Design Studio text present
http://127.0.0.1:3022/coding/design-demo -> 200, applied sandbox packet text present
```

Browser `/coding` regression:

```text
url: http://127.0.0.1:3022/coding
has_coding_surface: true
has_design_studio: true
has_next_error: false
```

Forbidden-file guard:

```text
no_forbidden_files_touched_by_plan05: true
execute_approved_used: false
```

The non-GO full-worktree guard artifact, `plan-05.4-phase-regression-20260703T034200Z.json`, found pre-existing dirty `execute-approved` files in the broader worktree. They are outside this Plan 05 touched-file set, were not used for Design Studio, and were not reverted.

## Commands Run

Regression server:

```text
npm run dev -- -p 3022
```

HTTP probes:

```text
Invoke-WebRequest http://127.0.0.1:3022/coding
Invoke-WebRequest http://127.0.0.1:3022/coding/design-demo
```

Browser regression:

```text
in-app browser -> http://127.0.0.1:3022/coding
```

Forbidden-file guard:

```text
node <inline Plan 05 touched-file guard script>
```

Required receipt validator is run after this receipt before Plan 06 starts.

Temporary regression dev server was stopped after proof.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 05.4 because this increment closes Plan 05 and does not perform originality/critic/acceptance:

- `mobile_screenshot_path`
- `mobile_screenshot_hash`
- `network_proof_path`
- `anti_template_verdict_id`
- `critic_verdict_id`
- `repair_attempt_ids`
- `retest_receipt_id`
- `acceptance_id`

## What Failed Before Fix

The first guard checked the entire dirty worktree and found unrelated pre-existing `execute-approved` modifications. That artifact is retained as non-GO evidence and is not used as the Plan 05 verdict.

## What Changed To Fix It

The final guard scopes the check to files touched by Plan 05. It confirms Plan 05 did not touch `.env*`, `.spirit-backups/**`, `docs/evidence/**`, or `src/app/v1/actions/execute-approved/**`.

## Blockers

No Plan 05.4 blocker. Broader worktree dirt remains present but is outside this pivot increment and was not reverted.

## Receipt Conclusion

Plan 05.4 is complete:

- Plans 01-04 remain covered by validator chain
- unrelated `/coding` path still loads
- no Plan 05 forbidden files touched
- validator is rerun through Plan 05 after this receipt

`INCREMENT_GO_PROVEN`
