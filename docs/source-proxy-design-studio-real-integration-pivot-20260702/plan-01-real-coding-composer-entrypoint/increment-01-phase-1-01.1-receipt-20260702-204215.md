# Increment Receipt: Plan 01.1 Seam Discovery and Decision

increment_id: `01.1-seam-discovery-and-decision`
plan_id: `01`
phase_id: `1`
started_at: `2026-07-02T20:31:00-04:00`
completed_at: `2026-07-02T20:42:15-04:00`
head_before: `ec422564a3131ad4ecbd9f9626d1af421741019e`
head_after: `ec422564a3131ad4ecbd9f9626d1af421741019e`
branch: `bench/glm4-9b-model-lanes`
network_proof_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-network-20260702-2044.json`
dom_snapshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-dom-20260702-2044.html`
desktop_screenshot_path: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-viewport-20260702-2044.png`
desktop_screenshot_hash: `cc7f5daf0920d01ab31cc1b98d4e56a1883f1a59ffed3684469cab9ccff6f42e`
final_increment_verdict: `INCREMENT_GO_PROVEN`

## Scope

Plan 01.1 is seam discovery only. No UI wiring, route wiring, model wiring, sandbox apply, screenshot verifier, critic, repair, acceptance, or writeback implementation was performed.

Exact files changed by this increment:

- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-dom-20260702-2044.html`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-network-20260702-2044.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-page-info-20260702-2044.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-viewport-20260702-2044.png`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/increment-01-phase-1-01.1-receipt-20260702-204215.md`

Forbidden files checked and not modified by this increment:

- `src/app/coding/page.tsx`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/app/v1/coding/design-studio/preview/route.ts`
- `src/app/v1/actions/execute-approved/route.ts`
- `src/lib/coding/design-studio-obsidian-writeback.ts`

## Dirty Tree Before

Plan 00 left the expected scoped changes:

```text
 M src/lib/coding/design-studio-obsidian-writeback.ts
?? docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-00-truth-reset-and-baseline/
?? docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/
?? scripts/coding/
```

Plan 01.1 added only evidence and this receipt under the Plan 01 docs folder.

## Browser Proof

A separate local Next dev server was started on:

```text
http://localhost:3015
```

Why: port 3000 on Windows was already owned by another process and returned `401 Unauthorized`; the Dell-hosted server was not reliably reachable from Windows by browser URL. The first Windows dev start reached ready then crashed on stale generated `.next/dev/logs`; the generated log folder was cleared and the server restarted successfully.

In-app browser attempts:

- `http://127.0.0.1:3000/coding`: blocked before render.
- `http://localhost:3000/coding`: blocked before render.
- `http://localhost:3015/coding`: the in-app browser control timed out during navigation even after reconnecting the browser session.

Fallback browser proof:

A real Playwright Chromium browser opened:

```text
http://localhost:3015/coding
```

Verified visible/runtime page facts:

```json
{
  "url": "http://localhost:3015/coding",
  "title": "Spirit OS • Dark Node",
  "shellId": "coding-cockpit-shell",
  "hasCodingHeading": true,
  "hasTaskComposerHeading": true,
  "textareaPlaceholder": "Describe what you want SpiritOS to change.",
  "startButtonText": "Start coding",
  "hasReviewPane": true,
  "hasPromptComposer": true
}
```

Evidence artifacts:

- DOM: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-dom-20260702-2044.html`
- DOM sha256: `93f8c15ff54862e4d2b3c3c9150d36c75705387dbc98b0441079bd83c56d68be`
- screenshot: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-viewport-20260702-2044.png`
- screenshot sha256: `cc7f5daf0920d01ab31cc1b98d4e56a1883f1a59ffed3684469cab9ccff6f42e`
- network log: `docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-01-real-coding-composer-entrypoint/evidence/plan-01.1-coding-network-20260702-2044.json`
- network log sha256: `b79d0d4b45b16beda9f44152d41f17d5ba95eec7094eedf1f2294ca07cf8d19d`

## Source Seam Discovery

Current canonical `/coding` page:

- file: `src/app/coding/page.tsx`
- renders: `CodingCockpitShell`
- shell registry ID: `coding-cockpit-shell`
- registry source: `src/lib/coding/shell-registry.ts`

Do not use as canonical seam:

- `src/components/coding/CodingCommandCenterShell.tsx`
- reason: registry marks it `experimental`, route `null`, owner decision `undecided`

Exact current composer/control component:

- `src/components/coding/CodingCockpitShell.tsx`

Exact current composer UI:

- heading: `Task Composer`
- textarea bound to `task`
- placeholder: `Describe what you want SpiritOS to change.`
- primary button: `Start coding`
- review/status surface: existing review pane and `previewState`

Exact current state/store/hook/event path:

- `task` state feeds the manual composer
- `handleTaskChange(event.target.value)` updates task text and resets preview state
- `handleDraftPreview()` starts the current manual composer flow
- `previewState` carries pending/running/blocked/ready/apply status
- `manualEvent(...)` entries populate the visible progress/event list
- `composerTiming` records route timing

Exact current route payload path:

- current manual composer calls `/v1/decisions/prompt-packet`
- current manual composer then calls `/v1/verification/diff-preview`
- current manual composer may call `/v1/actions/execute-approved` for live apply

Design Studio constraint:

- `execute-approved` is out of scope for Design Studio
- Design Studio must use one canonical future sandbox apply path to `/coding/design-demo` only

## Seam Decision

Decision: `SEAM_SAFE_USE_EXISTING_CODING_COCKPIT_COMPOSER`

Plan 01.2 should attach Design Studio mode to the existing `CodingCockpitShell` task composer seam, not build a parallel Design Studio page and not mount the experimental command center shell.

Recommended Plan 01.2 seam:

- add a visible Design Studio mode/control near the existing Task Composer
- preserve the current manual coding mode as default
- route Design Studio submissions through a new Design Studio-specific frontend/backend path, not `/v1/actions/execute-approved`
- reuse `task` as the prompt input, or introduce a mode-scoped prompt state only if preserving existing coding behavior requires it
- reuse `previewState`-style visible running/blocked/result display or add a mode-scoped peer state in the same review pane
- surface trace/request/status in the existing `/coding` UI
- preserve selected-prompt clearing and failure state by calling the same reset/rewind patterns used by `handleTaskChange`, without clearing unrelated trial state

Unsafe seam avoided:

- a separate `/coding/design-studio` page as the tested entrypoint
- `DesignStudioShell` as the product entrypoint
- `CodingCommandCenterShell` as canonical
- `execute-approved` reuse for Design Studio apply

Required Britton decision:

- none for seam safety; the existing composer seam is safe enough for Plan 01.2 implementation
- Britton approval is still required before any separate future change that would reuse `execute-approved`

## Commands Run

Source discovery:

```text
rg --files src/app src/components/coding src/lib/coding | rg "coding|Coding|agent|prompt|composer|cockpit|command"
rg -n "<textarea|<input|<button|draftText|setDraft|handle.*Submit|fetch\(|taskSubmitted|previewStatus|DesignProposal|design-studio|mac-worker|prompt-packet|execute-approved" src/components/coding/CodingCockpitShell.tsx src/components/coding/CodingCommandCenterShell.tsx src/app/coding/page.tsx
```

Local server proof:

```text
npm run dev -- -p 3015
```

Browser proof:

```text
node <inline Playwright Chromium proof script>
```

Result: PASS, `/coding` opened and the canonical task composer controls were visible.

## Test Results

No unit tests were run in 01.1. This increment is source seam discovery plus browser proof only.

## Required Receipt Fields Not Applicable

The following fields are not applicable to Plan 01.1 because no prompt was submitted and no Design Studio runtime route, model invocation, sandbox apply, critic pass, acceptance, or writeback occurred:

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
- `mobile_screenshot_path`
- `mobile_screenshot_hash`
- `anti_template_verdict_id`
- `critic_verdict_id`
- `repair_attempt_ids`
- `retest_receipt_id`
- `acceptance_id`

## What Failed Before Fix

Before this increment, the active pivot had no approved seam decision for attaching Design Studio to the real `/coding` composer.

Environment/browser issues encountered:

- existing Windows port 3000 returned 401 from another process
- Dell port 3000 was not stable through direct Windows/browser access
- first Windows 3015 dev start crashed on generated `.next/dev/logs`
- in-app browser control timed out on local navigation after the server was ready

## What Changed To Fix It

No product code was changed. A generated Next dev log folder was cleared to start a local dev server, and evidence artifacts were written under this Plan 01 docs folder.

## Blockers

No seam blocker. Browser proof was completed with Playwright Chromium after in-app browser control failed.

## Receipt Conclusion

Plan 01.1 seam discovery is complete:

- real `/coding` browser proof captured
- canonical shell identified as `CodingCockpitShell`
- actual composer/control seam identified
- current route path identified
- `execute-approved` excluded from Design Studio apply
- seam marked safe for Plan 01.2
- no implementation started

`INCREMENT_GO_PROVEN`
