# Increment Receipt: Plan 10.1 Happy Path Gauntlet

increment_id: `10.1-happy-path-gauntlet`
plan_id: `10`
phase_id: `5`
started_at: `2026-07-03T03:14:00-04:00`
completed_at: `2026-07-03T03:50:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
trace_id: `design-studio-trace-fd3920ff1c60-943f12a2`
network_proof_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.1-network-proof-20260703T074700Z.json`
request_id: `design-studio-756f8090-5c9c-482d-b209-029f943f12a2`
model_invocation_event_id: `ollama-phi4-mini-latest-e810c8f6f72c`
design_packet_hash: `8a7c2a3d35d2210e56f15ddb932c29a6a7eb3c7ca5f635e55c82610ba473bb66`
designdna_hash: `56f51ad0ccb636c7d856302929b6c76a2d3658f51d17ec189c6924306ce9bc8e`
coder_packet_hash: `preview_c57ddf26`
diff_hash: `69f25b09d8727a8af3c742ebd86774604943b65fc2bcc44501ed3bd315a2b192`
sandbox_apply_receipt_id: `sandbox-apply-69f25b09d872`
desktop_screenshot_hash: `46127c072b2a517aeda8569b5ee391aca303b92d5d60b68c41946b20d5492647`
mobile_screenshot_hash: `3047bff06eda22828c1f2e6a1e6dda56c9c84a772632c27c184aa37b9b24bb65`
anti_template_verdict_id: `plan-08-repaired-verdict-20260703T061100Z`
critic_verdict_id: `critic-design-studio-trace-24e3574ecc8f-r-packet`
retest_receipt_id: `08.3-retest-after-repair`
acceptance_id: `accept-plan-09-3-human`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 10.1 proves the happy path starts from the real `/coding` UI. The browser selected Design Studio mode, entered a messy design prompt in the actual composer, submitted it, and captured a Playwright network log for `/v1/coding/design-studio/preview`.

Exact files changed or created by this increment:

- `src/components/coding/CodingCockpitShell.tsx`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10-devserver-3026.out.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10-devserver-3026.err.log`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.1-network-proof-20260703T074700Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.1-coding-ui-final-20260703T074700Z.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.1-coding-ui-final-dom-20260703T074700Z.txt`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.1-happy-path-gauntlet-20260703T074700Z.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/increment-10-phase-5-10.1-receipt-20260703-075000.md`

## Browser Gauntlet Proof

Evidence artifact:

- happy path gauntlet JSON: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence/plan-10.1-happy-path-gauntlet-20260703T074700Z.json`
- happy path gauntlet JSON sha256: `dd693005f8df0cb14cd8b4cfb039586b2cddd813a72aafef57f0a496eb175b8f`
- network proof JSON sha256: `fe128d13a0fbbc803654364f182d086a21179a4af10d080cd74873eb4c9b0de6`
- UI screenshot sha256: `fb0becb0eb62bda3df04d26a86d9f14e5ba2edc0feed327e50e662b14865ac22`
- UI DOM sha256: `f2e565d2f4719fee9efb4129e9e4663f309cb907b407e87bac639c783fba5bf0`

Required proof:

```text
browser_opens_coding: true
messy_design_prompt_submitted_through_actual_ui: true
network_proof_path_present: true
request_id_present: true
trace_id_present: true
model_invocation_event_or_honest_blocked_env_present: true
model_invocation_event_id: ollama-phi4-mini-latest-e810c8f6f72c
design_packet_hash_present: true
designdna_hash_present: true
coder_packet_hash_present: true
sandbox_diff_hash_present: true
sandbox_apply_receipt_id_present: true
desktop_screenshot_hash_present: true
mobile_screenshot_hash_present: true
anti_template_verdict_id_present: true
critic_verdict_id_present: true
repair_retest_id_present: true
acceptance_id_present: true
ui_displays_final_status: true
```

## Commands Run

Real browser proof:

```text
npm run dev -- -p 3026
node <inline Playwright /coding UI submit and network proof script>
```

Receipt validator:

```text
node scripts/coding/validate-design-studio-receipts.mjs --pivot docs/source-proxy-design-studio-real-integration-pivot-20260702 --through-plan 10
```

## Blockers

No Plan 10.1 blocker.

## Receipt Conclusion

Plan 10.1 is complete:

- `/coding` opened in a real browser
- messy Design Studio prompt was submitted through the actual UI
- network proof captured the preview request and response
- downstream hashes, critic, repair/retest, and acceptance are tied into the gauntlet receipt
- UI displayed the final Design Studio status

`INCREMENT_GO_PROVEN`
