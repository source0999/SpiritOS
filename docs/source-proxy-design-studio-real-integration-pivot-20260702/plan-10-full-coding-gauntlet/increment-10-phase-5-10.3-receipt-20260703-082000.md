# Increment Receipt: Plan 10.3 Failure Path Gauntlet

increment_id: `10.3-failure-path-gauntlet`
plan_id: `10`
phase_id: `5`
started_at: `2026-07-03T04:05:00-04:00`
completed_at: `2026-07-03T04:20:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-c06527121a7b-7be9185f`
network_proof_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.3-blocked-env-network-proof-20260703T081500Z.json`
request_id: `design-studio-420ac561-5798-417f-9c42-ee267be9185f`
model_invocation_event_id: `ollama-phi4-mini-latest-blocked-env`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 10.3 proves the failure path from the real `/coding` UI. The unavailable provider was induced environmentally by starting the dev server with `SOURCE_PROXY_OLLAMA_BASE_URL=http://127.0.0.1:9`.

Exact files changed or created by this increment:

- `src/app/v1/coding/design-studio/preview/route.ts`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.3-failure-path-runner-20260703T081500Z.cjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10-devserver-3028-blocked-env.out.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10-devserver-3028-blocked-env.err.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10-devserver-3028-blocked-env-restart.out.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10-devserver-3028-blocked-env-restart.err.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.3-blocked-env-network-proof-20260703T081500Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.3-blocked-env-ui-final-20260703T081500Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.3-blocked-env-ui-final-dom-20260703T081500Z.txt`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.3-failure-path-gauntlet-20260703T081500Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/increment-10-phase-5-10.3-receipt-20260703-082000.md`

## Failure Path Proof

Evidence artifact:

- failure path gauntlet JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.3-failure-path-gauntlet-20260703T081500Z.json`
- failure path gauntlet JSON sha256: `4a16f6d1a68f71f02e00083df8562dc6d7fd3d434046d3cdda5f8eab4024d35e`
- network proof JSON sha256: `e78799db702a489ca865464d1a9f232800af116bbde01f7f8c65d0bee0ca7491`
- UI screenshot sha256: `b8d176fc60001af88f59a901fbef423c35e9206fb02b1d2eb5571ee497abaee3`
- UI DOM sha256: `309abe30dc6788a9eb4f86bd1845e53f7d6338476237280f828d6969b8cd95fb`

Required proof:

```text
unavailable_provider_safely_triggered_or_simulated_environmentally: true
environmental_induction: SOURCE_PROXY_OLLAMA_BASE_URL=http://127.0.0.1:9
endpoint_status: 424
ui_shows_blocked_env: true
outcome: MODEL_PROBE_BLOCKED_ENV
failure_mode: PROVIDER_UNREACHABLE_BLOCKED_ENV
no_fake_go: true
trace_records_failure_reason: true
```

## Commands Run

Real browser failure proof:

```text
SOURCE_PROXY_OLLAMA_BASE_URL=http://127.0.0.1:9 npm run dev -- -p 3028
node docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.3-failure-path-runner-20260703T081500Z.cjs
```

Receipt validator:

```text
node scripts/coding/validate-design-studio-receipts.mjs --pivot docs/source-proxy-design-studio-real-integration-pivot-20260702 --through-plan 10
```

## Non-GO Evidence Retained

The first blocked-env lane failed because another Next dev server was active. A later attempt exposed a corrupted generated `.next/dev` cache; the generated cache was cleared after resolving it under the workspace.

## Blockers

No Plan 10.3 blocker.

## Receipt Conclusion

Plan 10.3 is complete:

- provider unavailability was induced environmentally
- UI showed `MODEL_PROBE_BLOCKED_ENV`
- no fake GO path was accepted
- trace recorded the failure reason

`INCREMENT_GO_PROVEN`
