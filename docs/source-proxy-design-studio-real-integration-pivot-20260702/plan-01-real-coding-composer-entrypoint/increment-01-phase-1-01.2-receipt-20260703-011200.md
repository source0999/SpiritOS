# Increment Receipt: Plan 01.2 Real Composer Design Studio Entry

increment_id: `01.2-real-composer-design-studio-entry`
plan_id: `01`
phase_id: `1`
started_at: `2026-07-02T20:43:00-04:00`
completed_at: `2026-07-02T21:12:00-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
network_proof_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-network.json`
dom_snapshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-dom.html`
desktop_screenshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-final.png`
desktop_screenshot_hash: `d91378b30c75541ec0308952422dea7247495c1a51e8fd4b4d8eb6242a376a95`
request_id: `design-studio-8ec4ee98-7f82-4e88-881d-208910a7d42a`
trace_id: `preview-shell-trace`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 01.2 wires the approved Plan 01.1 seam into the real `/coding` composer only. It adds a Design Studio composer mode beside the existing coding mode and routes the Design Studio submission through `/v1/coding/design-studio/preview`.

Exact files changed by this increment:

- `src/components/coding/CodingCockpitShell.tsx`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-dom.html`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-final.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-network.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-page-info.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-pending.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/increment-01-phase-1-01.2-receipt-20260703-011200.md`

Forbidden files checked and not modified by this increment:

- `src/app/v1/actions/execute-approved/route.ts`
- `src/components/coding/DesignStudioShell.tsx`
- `src/components/coding/CodingCommandCenterShell.tsx`
- model/provider/subagent lanes
- sandbox apply, critic, acceptance, repair, screenshot verifier, and writeback runtime paths

## Dirty Tree Before

The worktree already contained Plan 00 changes, Plan 01.1 evidence, and unrelated pre-existing edits in `src/components/coding/CodingCockpitShell.tsx`. Those pre-existing edits were not reverted.

## Implementation

Design Studio entry was added inside the existing `CodingCockpitShell` task composer:

- composer mode state defaults to `coding`
- visible mode buttons: `Coding` and `Design Studio`
- Design Studio uses the same prompt textarea
- Design Studio submit calls `/v1/coding/design-studio/preview`
- request id is generated client-side and sent in the JSON body plus `x-design-studio-request-id`
- pending/running, endpoint status, outcome, reason, request id, and trace id render inside the existing `/coding` UI
- ordinary coding mode still points at `handleDraftPreview`
- no `execute-approved` call was added to Design Studio

## Browser Proof

A real Playwright Chromium browser opened:

```text
http://localhost:3015/coding
```

User-like browser actions performed:

1. Filled the existing task composer textarea.
2. Clicked the visible `Design Studio` composer mode button.
3. Clicked the visible `Start Design Studio` button.
4. Captured the visible pending/running state before the preview response completed.
5. Waited for the real `/v1/coding/design-studio/preview` response.
6. Verified visible request id and trace id in the `/coding` page.

Browser proof result:

```json
{
  "url": "http://localhost:3015/coding",
  "responseStatus": 200,
  "pendingStateVisible": true,
  "finalRequestIdVisible": true,
  "finalTraceIdVisible": true,
  "requestId": "design-studio-8ec4ee98-7f82-4e88-881d-208910a7d42a",
  "traceId": "preview-shell-trace"
}
```

Network proof includes a real request and response for:

```text
POST http://localhost:3015/v1/coding/design-studio/preview
```

Evidence artifacts:

- network log: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-network.json`
- network log sha256: `08efb4fe3a9658a2620de2d270c4fe139825780a7878740d1debdc88dd034ecb`
- DOM snapshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-dom.html`
- DOM snapshot sha256: `4e57ab258548e94187f982220c732b26f2d22baaca95762a2cfb3e1d57f02347`
- pending screenshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-pending.png`
- pending screenshot sha256: `ac6b6f766ad923bacf24712980aa85186ff086b03ad76215f673fabad88a7f0f`
- final screenshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-final.png`
- final screenshot sha256: `d91378b30c75541ec0308952422dea7247495c1a51e8fd4b4d8eb6242a376a95`
- page info: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.2-coding-design-studio-20260703T010947Z-page-info.json`
- page info sha256: `499d4b705dcb8e14347d543cc0ce53570d54490f4bf68a5522ef6ab698f56b47`

## Commands Run

Source and process inspection:

```text
rg -n "DesignStudioComposerState|handleDesignStudioPreview|Composer mode|Start Design Studio|Design Studio run" src/components/coding/CodingCockpitShell.tsx
rg -n "function asRecord|const asRecord|function stringValue|const stringValue|function messageFromPayload|function readJson" src/components/coding/CodingCockpitShell.tsx
Get-CimInstance Win32_Process -Filter "name = 'node.exe'" | Select-Object ProcessId,ParentProcessId,CommandLine
```

Attempted full TypeScript check:

```text
npx.cmd tsc --noEmit --pretty false --incremental false
```

Result: timed out after 304 seconds without compiler output. The stale `tsc` process was stopped by exact command-line match.

Attempted targeted component test:

```text
$env:CI='1'; npx.cmd vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx --reporter=verbose --testTimeout=20000 --hookTimeout=20000 --pool=threads
```

Result: timed out after 244 seconds without assertion output. The stale `vitest` process was stopped by exact command-line match.

Browser proof:

```text
node <inline Playwright Chromium proof script>
```

Result: PASS.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 01.2 because this increment does not invoke a model, apply a sandbox diff, run a screenshot verifier, run an anti-template critic, repair, accept, or write back:

- `original_user_prompt_hash`
- `model_invocation_event_id`
- `provider_model_name`
- `input_hash`
- `output_hash`
- `design_packet_hash`
- `designdna_hash`
- `coder_packet_hash`
- `diff_hash`
- `sandbox_apply_receipt_id`
- `mobile_screenshot_path`
- `mobile_screenshot_hash`
- `anti_template_verdict_id`
- `critic_verdict_id`
- `repair_attempt_ids`
- `retest_receipt_id`
- `acceptance_id`

## What Failed Before Fix

Before this increment, the real `/coding` task composer had no Design Studio mode and no visible browser path to submit a Design Studio preview request through `/v1/coding/design-studio/preview`.

During proof, an initial browser script clicked the mode button before the prompt-enabled state had settled and timed out waiting for `Start Design Studio`. The proof script was corrected to wait for the textarea value and mode pressed state before submission. A second proof run reached the final state but used an overly broad `trace_id` text assertion; the final proof scoped verification to the trace value.

## What Changed To Fix It

The real `CodingCockpitShell` composer now includes a Design Studio mode that submits to the Design Studio preview route and renders the pending/final run metadata in the `/coding` page.

## Blockers

No Plan 01.2 blocker.

The full TypeScript and targeted Vitest commands timed out without assertion or compiler output, so they are recorded as environment/check-run instability rather than green proof. The required frontend/browser proof for Plan 01.2 is green.

## Receipt Conclusion

Plan 01.2 is complete:

- user-like browser action selected Design Studio mode in real `/coding`
- prompt submitted through existing UI
- pending/running state visibly appeared
- network proof exists for `/v1/coding/design-studio/preview`
- request id and trace id are visible in the page
- no `execute-approved` Design Studio path was added

`INCREMENT_GO_PROVEN`
