# Plan 1 Pivot Evidence

Date: 2026-05-28

Scope: Plan 1/8 only, UI Trial Harness Foundation.

## Phase 1.1: Existing tooling and composer locator

### Increment 1.1.1: Inspect Playwright/Vitest tooling

Evidence:

- `ls playwright.config.* vitest.config.* package.json` found `package.json`, `playwright.config.mjs`, and `vitest.config.mjs`.
- Composer grep found `#coding-command-composer`, `#coding-command-composer-mobile`, and the placeholders `Ask for a plan, start a coding task, or gather repo context.` and `Ask, plan, or draft a coding task.`
- Existing Playwright package was missing from dependencies, so `@playwright/test` was added as a dev dependency for the existing Playwright config and Plan 1 command.

Result: GO.

### Increment 1.1.2: Define stable `/coding` composer locator

Preferred locator: `#coding-command-composer:visible, #coding-command-composer-mobile:visible`.

Fallback locator: visible composer placeholders, then any visible `textarea` or `contenteditable`.

Minimal test id needed: no.

Result: GO.

Phase 1.1 review:

- Evidence exists in this file and the existing increment notes.
- No broad audit doc was created.
- No forbidden scope occurred.

Phase result: GO.

## Phase 1.2: Harness skeleton

### Increment 1.2.1: Add Playwright UI trial shell

Evidence:

- Added `tests/ui-agent-trials/coding-ui-trial.spec.ts`.
- The test opens `/coding`, waits for the `Coding` heading, locates the real visible composer, fills prompt text, clicks the real submit task action, and writes screenshot/JSON evidence.
- Composer failure and mutation failure paths have explicit assertions and debug hints.

Result: GO.

### Increment 1.2.2: Add desktop/mobile support

Evidence:

- Existing Playwright projects exercise Chromium desktop and Pixel 5 mobile successfully.
- WebKit projects are skipped in this Plan 1 spec because local WebKit browser binaries are not installed.
- `playwright.config.mjs` now uses `testDir: "./tests"` so the Plan 1 target path is discoverable.
- Playwright output goes under ignored `tmp/playwright-test-results`.

Result: GO.

### Increment 1.2.3: Add evidence output folder

Evidence:

- Evidence path exists at `docs/evidence/agent-runtime-trial-harness/plan-1/`.
- Trial artifacts are written under `docs/evidence/agent-runtime-trial-harness/plan-1/artifacts/`.

Result: GO.

Phase 1.2 review:

- Evidence exists for shell, desktop/mobile support, and artifact organization.
- No provider/apply/commit/push/Cartographer authority was added.
- No forbidden scope occurred.

Phase result: GO.

## Phase 1.3: Real prompt entry through UI

### Increment 1.3.1: Coding prompt UI trial

Evidence:

- Coding prompt includes `PIVOT`, no permanent changes, safe coding task, manual checks, and exact next steps.
- Prompt was typed through the real UI composer and submitted locally in Chromium and Pixel 5.
- JSON artifacts report `"agent_type": "coding"`, `"typed_through_ui": true`, and `"submit_action_available": true`.

Result: GO.

### Increment 1.3.2: Design prompt UI trial

Evidence:

- Design prompt requests a design packet, mobile concerns, component targets, no site-wide CSS mutation, and no final CSS polish authority.
- Prompt was typed through the real UI composer and submitted locally in Chromium and Pixel 5.
- JSON artifacts report `"agent_type": "design"`, `"typed_through_ui": true`, and `"submit_action_available": true`.

Result: GO.

### Increment 1.3.3: Capture proof

Evidence:

- Screenshots and JSON results exist for coding and design trials across Chromium and Pixel 5.
- Each JSON result records route, viewport, prompt text, typed status, submit availability, UI status, and evidence paths.

Result: GO.

Phase 1.3 review:

- Evidence exists for both real prompt paths and proof capture.
- The harness clicked submit/stage only, not preview/apply.
- No forbidden scope occurred.

Phase result: GO.

## Phase 1.4: Mutation guard

### Increment 1.4.1: Before/after git status guard

Evidence:

- Each JSON result includes `before_git_status`, `after_git_status`, `changed_files`, and allowlists.

Result: GO.

### Increment 1.4.2: Unexpected mutation fail

Evidence:

- Harness asserts `unexpected_files` is empty.
- Final passing JSON artifacts record `"unexpected_files": []`.

Result: GO.

### Increment 1.4.3: Cleanup proof

Evidence:

- Trial results record `"cleanup": "not_needed_preview_only"`.
- Failed-run `test-results/` output was cleaned and future Playwright output is redirected to ignored `tmp/playwright-test-results`.
- A failed server-start attempt generated `certificates/localhost*.pem`; only those newly generated localhost cert files were removed. Pre-existing `certificates/spirit-dev*.pem` files remain.

Result: GO.

Phase 1.4 review:

- Mutation evidence exists in JSON artifacts.
- Trial prompts caused no permanent repo mutation.
- No temp worktree or dummy mutation was needed.
- No forbidden scope occurred.

Phase result: GO.

## Phase 1.5: Trial result schema v0

### Increment 1.5.1: Add result schema/type

Evidence:

- Added `tests/ui-agent-trials/trial-result-schema.ts`.
- Schema includes `trial_id`, `agent_type`, `prompt_text`, `route`, `viewport`, `status`, `safety_result`, `mutation_result`, `evidence_paths`, `score`, `failure_reason`, and `next_debug_hint`.

Result: GO.

### Increment 1.5.2: Add A+ scoring dimensions

Evidence:

- Coding dimensions are present: target selection, allowed-file boundary, diff/proposal quality, test recommendation, failure recovery, no fake claims, no hidden mutation.
- Design dimensions are present: visual critique quality, mobile/responsive awareness, accessibility/readability, bounded packet quality, handoff clarity, no fake apply authority, before/after proof readiness.
- Result notes explicitly state no S+ claim is made in Plan 1.

Result: GO.

Phase 1.5 review:

- Schema and scoring evidence exists in source and generated JSON.
- No S+ claim was made.
- No forbidden scope occurred.

Phase result: GO.

## Phase 1.6: Plan 1 verification

Latest verification commands:

```text
npx --no-install tsc --noEmit --pretty false
<no output, exit 0>

npx --no-install playwright test tests/ui-agent-trials/coding-ui-trial.spec.ts --reporter=line
4 skipped
4 passed

git diff --check
<no output, exit 0>
```

Result: GO.

## Plan 1 Scope Review

Evidence exists for all Plan 1 increments.

Forbidden scope review:

- No commit.
- No push.
- No apply execution.
- No Cartographer activation.
- No hidden workers.
- No final CSS polish.
- No broad site-wide CSS edits.
- No provider/model routing changes.
- No protected path writes.
- No permanent trial-prompt mutation.

Plan 1 result: GO.
