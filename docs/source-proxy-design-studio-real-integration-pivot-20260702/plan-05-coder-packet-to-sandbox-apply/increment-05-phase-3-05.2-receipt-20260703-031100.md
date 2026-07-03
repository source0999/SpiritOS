# Increment Receipt: Plan 05.2 Apply Sandbox Diff

increment_id: `05.2-apply-sandbox-diff`
plan_id: `05`
phase_id: `3`
started_at: `2026-07-02T23:04:00-04:00`
completed_at: `2026-07-02T23:11:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-24e3574ecc8f-r-packet`
coder_packet_hash: `preview_bb110d8d`
diff_hash: `69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192`
sandbox_apply_receipt_id: `sandbox-apply-69f25b09d872`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 05.2 applies an actual sandbox page diff to `/coding/design-demo` only. It does not use `execute-approved`, does not touch production app routes, and does not touch protected files.

Exact files changed by this increment:

- `src/app/coding/design-demo/page.tsx`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.2-sandbox-diff-20260703T030900Z.patch`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.2-sandbox-apply-20260703T030900Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/increment-05-phase-3-05.2-receipt-20260703-031100.md`

## Sandbox Diff Proof

Evidence artifact:

- sandbox apply JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.2-sandbox-apply-20260703T030900Z.json`
- sandbox apply JSON sha256: `2844d32161104ae8875811af15c5833e1043af87705e7c34298ce5da466561b2`
- sandbox diff patch: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-05-coder-packet-to-sandbox-apply/evidence/plan-05.2-sandbox-diff-20260703T030900Z.patch`
- sandbox diff patch sha256: `69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192`
- sandbox page file sha256 after apply: `b788901d4fc6bfb8791b7d30247ef72ce3c73b1158104a9eb1fed6bcc0b34225`

Changed files:

```text
src/app/coding/design-demo/page.tsx
```

Guard proof:

```text
allowed_files: src/app/coding/design-demo/page.tsx
protected_paths_blocked: true
production_app_files_blocked: true
execute_approved_used: false
```

Blocked candidates:

```text
.env.local -> BLOCKED_OUTSIDE_DESIGN_DEMO_SANDBOX
src/app/page.tsx -> BLOCKED_OUTSIDE_DESIGN_DEMO_SANDBOX
src/app/coding/page.tsx -> BLOCKED_OUTSIDE_DESIGN_DEMO_SANDBOX
src/app/globals.css -> BLOCKED_OUTSIDE_DESIGN_DEMO_SANDBOX
src/components/coding/DesignStudioShell.tsx -> BLOCKED_OUTSIDE_DESIGN_DEMO_SANDBOX
```

## Commands Run

Sandbox diff and guard evidence:

```text
node <inline git diff, changed-file, and path-guard proof script>
```

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 05.2 because this increment applies the sandbox diff but does not yet perform browser-visible proof:

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

Before this increment, Plan 05 had a generated coder packet but no actual file diff applied to the sandbox page.

## What Changed To Fix It

The `/coding/design-demo` page now visibly reflects the Plan 05 sandbox apply, including:

- Plan 05 sandbox apply heading
- trace marker
- design packet hash
- coder packet hash
- visible proof rail for allowed-file and protected-path boundaries

## Blockers

No Plan 05.2 blocker. Browser proof is intentionally deferred to Plan 05.3.

## Receipt Conclusion

Plan 05.2 is complete:

- actual file diff generated
- changed files under allowed sandbox only
- `diff_hash` recorded
- protected paths blocked
- production app files blocked
- `execute-approved` not used

`INCREMENT_GO_PROVEN`
