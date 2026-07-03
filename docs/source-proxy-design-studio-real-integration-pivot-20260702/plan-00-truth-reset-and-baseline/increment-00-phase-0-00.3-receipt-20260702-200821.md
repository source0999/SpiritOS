# Increment Receipt: Plan 00.3 Baseline-Only Writeback Path Normalization Fix

increment_id: `00.3-baseline-only-writeback-path-normalization-fix`
plan_id: `00`
phase_id: `0`
started_at: `2026-07-02T20:06:30-04:00`
completed_at: `2026-07-02T20:08:21-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 00.3 fixed only the inherited Windows path-separator normalization defect in the approved Design Studio writeback helper.

Exact files changed by this increment:

- `src/lib/coding/design-studio-obsidian-writeback.ts`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline/increment-00-phase-0-00.3-receipt-20260702-200821.md`

Forbidden files checked and not modified by this increment:

- `src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts`
- `src/app/v1/coding/design-studio/preview/route.ts`
- `src/components/coding/DesignStudioShell.tsx`
- `src/app/v1/actions/execute-approved/route.ts`
- model/provider/subagent lanes
- screenshot/apply/critic/acceptance paths
- Obsidian/vault paths

## Dirty Tree Before

Scoped status before this receipt:

```text
?? docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline/
```

The inherited red baseline from Plan 00.2 was:

```text
Test Files  1 failed (1)
Tests       2 failed | 8 passed (10)
```

with blocker label `INHERITED_RED_WRITEBACK_PATH_SEPARATOR`.

## Dirty Tree After

Scoped status after the code fix and before this receipt:

```text
 M src/lib/coding/design-studio-obsidian-writeback.ts
?? docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline/
```

No test file or Design Studio route/shell file was modified.

## Code Change Summary

Before:

```text
path.startsWith(`${allowedRoot}/`)
```

After:

```text
const relativeDestination = relative(allowedRoot, path);
```

The destination check now rejects escapes by using relative-path containment plus absolute-path detection, instead of assuming POSIX `/` separators. This preserves the same design-memory folder boundary while allowing valid Windows backslash paths.

## Commands Run

Required Windows verification:

```text
$env:CI='1'; npx.cmd vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism
```

Result on `Z:\` / Windows:

```text
Test Files  1 passed (1)
Tests       10 passed (10)
```

Scoped diff review:

```text
git diff -- src/lib/coding/design-studio-obsidian-writeback.ts
```

Result: only `node:path` imports and the destination containment check changed.

Dell scoped diff check and comparison test:

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check -- src/lib/coding/design-studio-obsidian-writeback.ts && CI=1 npx vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism"
```

Result:

```text
git diff --check: PASS
Test Files  1 passed (1)
Tests       10 passed (10)
```

## Browser Actions Run

None. Plan 00.3 is a focused writeback helper fix and does not claim frontend behavior.

## Test Results

- Before Plan 00.3: Windows writeback suite 8 passed / 2 failed.
- After Plan 00.3: Windows writeback suite 10 passed / 0 failed.
- Dell/Linux comparison remained 10 passed / 0 failed.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 00.3 because this increment performs no route call, prompt generation, model invocation, sandbox apply, screenshot capture, critic pass, acceptance, or writeback:

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

The writeback destination rejected valid Windows paths under the approved `design-memory` folder because the containment check used a hardcoded `/` separator.

## What Changed To Fix It

Only the destination containment check was changed to use `relative(allowedRoot, path)` and reject parent/absolute escapes. No behavior beyond path separator normalization was intentionally changed.

## Blockers

No Plan 00.3 blocker.

## Receipt Conclusion

Plan 00.3 is complete:

- inherited Windows writeback suite went from 8/10 to 10/10
- no unrelated writeback behavior changed
- no Design Studio route wiring performed
- no shell wiring performed
- no model/provider wiring performed
- no screenshot/apply/critic work performed
- no docs GO claim made

`INCREMENT_GO_PROVEN`
