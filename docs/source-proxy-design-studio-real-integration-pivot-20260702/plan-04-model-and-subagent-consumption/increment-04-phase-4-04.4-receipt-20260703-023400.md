# Increment Receipt: Plan 04.4 Failure Behavior

increment_id: `04.4-failure-behavior`
plan_id: `04`
phase_id: `4`
started_at: `2026-07-02T22:27:00-04:00`
completed_at: `2026-07-02T22:34:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 04.4 proves explicit model-probe failure behavior. Failed model probes must return blocked status and must not appear as successful fallback preview output.

Exact files changed by this increment:

- `src/app/v1/coding/design-studio/preview/route.ts`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.4-route-runtime-20260703T023200Z.cjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.4-failure-behavior-20260703T023200Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/increment-04-phase-4-04.4-receipt-20260703-023400.md`

## Failure Proof

Evidence artifact:

- failure behavior JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-04-model-and-subagent-consumption/evidence/plan-04.4-failure-behavior-20260703T023200Z.json`
- failure behavior JSON sha256: `ce43ff36c7937788511a48dd82864db5ddd267250d64fc445412d3875ed305a0`
- transpiled runtime harness sha256: `c8d316cdbd2b6bde54c3f4330ee674f34f7cc0641b1e0425ab132190d20f5028`
- route implementation sha256 after edit: `909deb44cd69ec635c82d2d294aea4437c8cae700e9711516b5ae20dcfdef34f`

Runtime negative cases:

```text
unavailable_model: 424 MODEL_PROBE_BLOCKED_ENV UNAVAILABLE_MODEL_BLOCKED_ENV
timeout: 424 MODEL_PROBE_BLOCKED_ENV TIMEOUT_RETRY_LIMITED_BLOCKED_ENV
missing_source: 424 MODEL_PROBE_BLOCKED_ENV MISSING_SOURCE_BLOCKED_ENV
```

For every negative case:

```text
model_call_made: false
provider_call_made: false
blocked_env: true
fake_fallback_success: false
```

## Commands Run

Runtime route proof:

```text
node <inline route transpile and negative POST invocation script>
```

The proof script executed the current route implementation with real `Request` objects for unavailable model, timeout, and missing-source cases.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 04.4 because this increment proves blocked failure behavior rather than successful model output or sandbox/browser proof:

- `model_invocation_event_id`
- `provider_model_name`
- `input_hash`
- `output_hash`
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

Before this increment, an explicit failed model probe could be recorded while the route still returned the normal preview envelope. That risked presenting fallback preview output as a successful model path.

## What Changed To Fix It

The route now:

- supports explicit model probe timeout and required-source options
- returns `MODEL_PROBE_BLOCKED_ENV` with HTTP 424 for missing source
- returns `MODEL_PROBE_BLOCKED_ENV` with HTTP 424 for unavailable model or timeout
- includes `fallback_success_for_model_failure: false`

## Blockers

No Plan 04.4 blocker. The negative cases are blocked honestly and no provider was manufactured.

## Receipt Conclusion

Plan 04.4 is complete:

- unavailable model returns `BLOCKED_ENV`
- timeout returns retry-limited `BLOCKED_ENV`
- missing source returns `BLOCKED_ENV`
- fake fallback success is explicitly false

`INCREMENT_GO_PROVEN`
