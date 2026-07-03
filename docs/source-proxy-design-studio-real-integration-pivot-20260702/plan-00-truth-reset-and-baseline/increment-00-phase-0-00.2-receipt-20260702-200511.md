# Increment Receipt: Plan 00.2 Inherited Red-Test Baseline

increment_id: `00.2-inherited-red-writeback-test-baseline`
plan_id: `00`
phase_id: `0`
started_at: `2026-07-02T20:00:53-04:00`
completed_at: `2026-07-02T20:05:11-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 00.2 records the inherited red writeback baseline only. No implementation fix was performed in this increment.

Exact files changed by this increment:

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline/increment-00-phase-0-00.2-receipt-20260702-200511.md`

Forbidden files checked and not modified by this increment:

- `src/lib/coding/design-studio-obsidian-writeback.ts`
- `src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts`
- `src/app/v1/coding/design-studio/preview/route.ts`
- `src/components/coding/DesignStudioShell.tsx`
- `src/app/v1/actions/execute-approved/route.ts`

## Dirty Tree Before

Scoped status before this receipt:

```text
?? docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline/
```

No scoped runtime files were reported as modified.

Note: branch readback changed from `integration/cleanup-plan3-debug-20260623` during Plan 00.1 to `bench/glm4-9b-model-lanes` before Plan 00.2. Codex did not change branches.

## Dirty Tree After

Expected delta from this increment is one additional receipt file under the Plan 00 folder. No runtime file is intentionally changed.

## Commands Run

Windows baseline command:

```text
$env:CI='1'; npx.cmd vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism
```

Result on `Z:\` / Windows:

```text
Test Files  1 failed (1)
Tests       2 failed | 8 passed (10)
```

Failing cases:

- `creates a valid design memory note payload for an approved verified run`
- `does not overwrite an existing note`

Failure signature:

```text
expected 'rejected' to be 'written'
```

Relevant assertion locations:

- `src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts:55`
- `src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts:145`

Initial Windows attempt:

```text
$env:CI='1'; npx.cmd vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism
```

Result: timed out after 120 seconds before final verdict. A longer rerun produced the inherited 8/10 baseline above.

Dell comparison command:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && CI=1 npx vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism"
```

Result on `/home/source/SpiritOS` / Linux:

```text
Test Files  1 passed (1)
Tests       10 passed (10)
```

This confirms the failure is Windows path-separator specific, matching the pivot's inherited baseline.

## Browser Actions Run

None. Plan 00.2 is test-baseline only.

## Test Results

Required inherited baseline test:

- test file: `src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts`
- Windows result: 8 pass / 2 fail
- Linux/Dell comparison result: 10 pass / 0 fail
- blocker label: `INHERITED_RED_WRITEBACK_PATH_SEPARATOR`

## Root Cause

Current implementation in `src/lib/coding/design-studio-obsidian-writeback.ts` uses:

```text
path.startsWith(`${allowedRoot}/`)
```

On Windows, `resolve()` returns paths with backslashes. The slash-only prefix check rejects valid destinations under the approved `design-memory` folder, so write attempts return `destination_escape` and the two write-path tests fail before a note can be written.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 00.2 because this increment performs no route call, prompt generation, model invocation, sandbox apply, screenshot capture, critic pass, acceptance, or writeback:

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

The inherited Windows baseline failed exactly as expected:

`INHERITED_RED_WRITEBACK_PATH_SEPARATOR`

The red state was not introduced by Plan 00.2.

## What Changed To Fix It

Nothing. Fixing this defect is reserved for Plan 00.3 and must be limited to path-separator normalization in `src/lib/coding/design-studio-obsidian-writeback.ts`.

## Blockers

No Plan 00.2 blocker. The inherited red baseline was reproduced and recorded.

## Receipt Conclusion

Plan 00.2 is complete:

- inherited Windows result recorded as 8 pass / 2 fail
- failing cases recorded
- root cause recorded
- no runtime files touched
- no fix performed early

`INCREMENT_GO_PROVEN`
