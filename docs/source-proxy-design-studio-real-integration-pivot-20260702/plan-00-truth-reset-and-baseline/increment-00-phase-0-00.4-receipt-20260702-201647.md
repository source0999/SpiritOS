# Increment Receipt: Plan 00.4 Receipt Validator Bootstrap Contract

increment_id: `00.4-receipt-validator-bootstrap-contract`
plan_id: `00`
phase_id: `0`
started_at: `2026-07-02T20:09:00-04:00`
completed_at: `2026-07-02T20:16:47-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Bootstrap Exemption

This is the single Plan 00.4 validator-bootstrap receipt. Per the master plan, this receipt is not validator-gated because the validator is created by this increment.

Every receipt after Plan 00.4 must be validator-gated.

## Scope

Plan 00.4 created the machine-checkable receipt validator, schema contract files, concrete negative fixtures, and a dependency-free negative test runner.

Exact files changed by this increment:

- `scripts/coding/validate-design-studio-receipts.mjs`
- `scripts/coding/test-validate-design-studio-receipts.mjs`
- `scripts/coding/__tests__/fixtures/artifact-chain/critic.txt`
- `scripts/coding/__tests__/fixtures/artifact-chain/design-packet.txt`
- `scripts/coding/__tests__/fixtures/artifact-chain/screenshot.txt`
- `scripts/coding/__tests__/fixtures/broken-trace-link-chain.json`
- `scripts/coding/__tests__/fixtures/critic-missing-screenshot-hash.json`
- `scripts/coding/__tests__/fixtures/forged-artifact-hash.json`
- `scripts/coding/__tests__/fixtures/missing-artifact-path.json`
- `scripts/coding/__tests__/fixtures/missing-required-field.json`
- `scripts/coding/__tests__/fixtures/screenshot-missing-diff-hash.json`
- `scripts/coding/__tests__/fixtures/screenshot-missing-sandbox-apply.json`
- `scripts/coding/__tests__/fixtures/writeback-missing-approval-hash.json`
- `scripts/coding/__tests__/fixtures/writeback-trace-mismatch.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/increment-receipt.schema.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/artifact-chain.schema.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline/increment-00-phase-0-00.4-receipt-20260702-201647.md`

Forbidden files checked and not modified by this increment:

- `src/app/v1/coding/design-studio/preview/route.ts`
- `src/components/coding/DesignStudioShell.tsx`
- `src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts`
- `src/app/v1/actions/execute-approved/route.ts`
- model/provider/subagent lanes
- screenshot/apply/critic/acceptance runtime paths
- Obsidian/vault paths

## Dirty Tree Before

Scoped status before this receipt:

```text
 M src/lib/coding/design-studio-obsidian-writeback.ts
?? docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline/
?? docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/
?? scripts/coding/
```

The modified writeback helper is the approved Plan 00.3 runtime change. Plan 00.4 did not add further runtime mutations.

## Dirty Tree After

Expected delta from this increment is this bootstrap receipt plus validator/schema/test files listed above.

## Validator Capabilities Created

`scripts/coding/validate-design-studio-receipts.mjs` now:

- parses JSON receipts and markdown receipts with top-level `field: value` lines
- validates required increment fields
- validates allowed increment verdicts
- confirms referenced artifact paths exist
- recomputes artifact `sha256` hashes
- checks chain-link expected hashes against actual artifact hashes
- checks same-trace artifact links when trace IDs are supplied
- rejects screenshot receipts missing `sandbox_apply_receipt_id`
- rejects screenshot receipts missing `diff_hash`
- rejects critic receipts missing screenshot hashes
- rejects writeback receipts missing `approval_id_hash`
- rejects writeback receipts with acceptance trace mismatch
- validates pivot receipts through a requested plan number
- skips only the Plan 00.4 bootstrap receipt by filename pattern

## Schema Files Created

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/increment-receipt.schema.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/artifact-chain.schema.json`

JSON parse check:

```text
node -e "const fs=require('fs'); for (const f of ['docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/increment-receipt.schema.json','docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/artifact-chain.schema.json']) JSON.parse(fs.readFileSync(f,'utf8')); console.log('schemas-json-parse-pass')"
```

Result:

```text
schemas-json-parse-pass
```

## Negative Test Fixtures Created

Required rejection cases and concrete fixture files:

- forged/incorrect artifact hash: `scripts/coding/__tests__/fixtures/forged-artifact-hash.json`
- broken trace-link chain: `scripts/coding/__tests__/fixtures/broken-trace-link-chain.json`
- screenshot missing `sandbox_apply_receipt_id`: `scripts/coding/__tests__/fixtures/screenshot-missing-sandbox-apply.json`
- screenshot missing `diff_hash`: `scripts/coding/__tests__/fixtures/screenshot-missing-diff-hash.json`
- critic verdict missing screenshot hash: `scripts/coding/__tests__/fixtures/critic-missing-screenshot-hash.json`
- writeback missing approval ID hash: `scripts/coding/__tests__/fixtures/writeback-missing-approval-hash.json`
- writeback trace mismatch: `scripts/coding/__tests__/fixtures/writeback-trace-mismatch.json`
- missing required field: `scripts/coding/__tests__/fixtures/missing-required-field.json`
- artifact path does not exist: `scripts/coding/__tests__/fixtures/missing-artifact-path.json`

Supporting artifact files:

- `scripts/coding/__tests__/fixtures/artifact-chain/design-packet.txt`
- `scripts/coding/__tests__/fixtures/artifact-chain/screenshot.txt`
- `scripts/coding/__tests__/fixtures/artifact-chain/critic.txt`

## Commands Run

Negative fixture test runner:

```text
node scripts/coding/test-validate-design-studio-receipts.mjs
```

Result:

```json
{
  "cases": 9,
  "ok": true,
  "suite": "design-studio-receipt-validator-negative-fixtures"
}
```

Current receipt validation:

```text
node scripts/coding/validate-design-studio-receipts.mjs --pivot docs/source-proxy-design-studio-real-integration-pivot-20260702 --through-plan 00
```

Result before this bootstrap receipt existed:

```json
{
  "errors": [],
  "filesChecked": 3,
  "ok": true
}
```

Scoped diff check:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check -- scripts/coding docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline"
```

Result: PASS, exit code 0, no whitespace errors reported.

Note: an initial Vitest run against a `.test.mjs` file did not discover tests because this repo's include pattern is `**/*.{test,spec}.{ts,tsx}`. A later `.test.ts` attempt hit a Windows `Z:\` Vitest ESM path issue before assertions ran. The final negative suite is a direct Node runner to avoid adding dependencies and to keep the validator executable on this Windows share.

## Browser Actions Run

None. Plan 00.4 is validator/bootstrap work and does not claim frontend behavior.

## Test Results

- Negative fixture suite: PASS, 9/9 rejection cases asserted.
- Schema JSON parse: PASS.
- Existing Plan 00 receipts through 00.3 validate: PASS.
- Scoped diff check: PASS.

## Manual Artifact-Path Review

The negative fixtures reference only files under `scripts/coding/__tests__/fixtures/`. Existing artifact fixtures are intentionally tiny local text files. The missing-path fixture intentionally references `artifact-chain/missing-screenshot.txt`, which does not exist and is asserted as rejected.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 00.4 because this increment performs no route call, prompt generation, model invocation, sandbox apply, screenshot capture, critic pass, acceptance, or writeback:

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

Before Plan 00.4, there was no machine-checkable Design Studio receipt validator in `scripts/coding/`, no schemas under the active pivot, and no concrete negative fixture suite.

## What Changed To Fix It

Plan 00.4 added the validator, schemas, fixture artifacts, nine bad receipt fixtures, and a Node negative test runner.

## Blockers

No Plan 00.4 blocker.

## Receipt Conclusion

Plan 00.4 is complete:

- validator script created
- schemas created and parseable
- required negative rejection cases implemented as concrete fixtures
- negative suite passes
- current Plan 00 receipts through 00.3 validate
- scoped diff check passes
- no new dependency added
- no runtime integration performed

`INCREMENT_GO_PROVEN`
