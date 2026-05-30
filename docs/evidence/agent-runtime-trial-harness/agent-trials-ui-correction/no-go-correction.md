# Agent Trials UI Correction NO-GO

Plan title: Agent Trials UI Honesty, Cleanup, And Realistic Coverage Correction

Status: NO-GO correction pass opened.

The prior Realistic /coding Prompt Trial Remediation closeout claimed GO. Britton's manual browser review disputes that GO. This correction pass treats the prior result as not acceptable until browser/manual UI evidence proves the screen is understandable.

## Britton-observed bugs

- There are still two trial prompt/progress areas.
- The old/legacy main-panel progress bar is the only place where visible progress moves.
- The new Agent Trials widget mostly just says "Running."
- The weird `operator_run_request` text is still visible in the UI.
- The pulled-out/sidebar widget is visually messy.
- It is unclear whether the system is actually testing the prompts Britton cares about.
- Scrolling feels odd.
- There is still leftover junk from earlier cleanup work.
- Hybrid/design realistic prompts are still polished PIVOT/design-packet prompts instead of Britton-realistic messy prompts.

## Acceptance gate

No GO may be claimed unless browser screenshot/manual UI proof shows:

- no visible `operator_run_request` by default;
- no duplicate legacy trial/progress system by default;
- submitted prompt preview uses the actual `submitted_prompt`;
- the running/progress state is honest about whether it is manual-terminal, UI-local, artifact-only, or live;
- scrolling is sane on desktop and mobile;
- hybrid/design realistic coverage is either truly messy/Britton-realistic or explicitly not claimed as realistic.

## Increment log

### Increment 0.1 - Write NO-GO correction note

Evidence: this file records the disputed prior GO, Britton's observed bugs, and the new browser/manual proof gate.

Check: pending.

Result: GO. File exists and mentions every Britton-observed bug.

### Increment 1.1 - Inventory all trial/progress surfaces

Command:

```bash
grep -R "Legacy Proxy Test\|Proof run controls\|Agent Trials\|Operator run request\|Actual prompts to be submitted\|Running diagnostic\|trial-explicit-context\|Generated command\|Last submitted prompt\|Last diagnostics" -n src tests docs | head -200
```

Inventory:

| File | Component/function | Surface | Current or legacy | First viewport/default visibility | Should remain visible by default |
| --- | --- | --- | --- | --- | --- |
| `src/components/coding/CodingCommandCenterShell.tsx` | sidebar `section[aria-label="Agent Trials sidebar"]` around lines 6258-6500 | Agent Trials control surface | Current | Header visible in left sidebar by default; body collapsed by `agentTrialsOpen=false` | Yes, as the single compact control surface |
| `src/components/coding/CodingCommandCenterShell.tsx` | Agent Trials expanded body around lines 6374-6380 | Generated command full `pre` block | Current but too dominant | Visible after opening current widget | Yes, but compact one-line by default with full command behind expansion |
| `src/components/coding/CodingCommandCenterShell.tsx` | Agent Trials expanded body around lines 6381-6387 | Operator run request | Debug/artifact-only data shown as normal UI | Visible after opening current widget | No; hidden behind Advanced/Debug only |
| `src/components/coding/CodingCommandCenterShell.tsx` | Agent Trials expanded body around lines 6389-6415 | Actual prompts to be submitted | Current but confusing/multi-panel | Visible after opening current widget | Yes, renamed/consolidated as submitted prompt preview |
| `src/components/coding/CodingCommandCenterShell.tsx` | Agent Trials expanded body around lines 6418-6423 | Last submitted prompt | Duplicate current prompt panel | Visible after opening current widget | No, unless it is contextual current trial text |
| `src/components/coding/CodingCommandCenterShell.tsx` | Agent Trials expanded body around lines 6439-6455 | Running button in current widget | Current label but not live runner truth | Visible after opening current widget | Yes as manual action, but must not say fake "Running..." |
| `src/components/coding/CodingCommandCenterShell.tsx` | Agent Trials expanded body around lines 6472-6488 | Last diagnostics block full `pre` | Current debug block too visible | Visible after opening current widget | Only when blocked/failed or in diagnostics/details |
| `src/components/coding/CodingCommandCenterShell.tsx` | main panel compact proxy diagnostic around lines 7620-7810 | Legacy Proxy Test, Proof run controls, active state/build marker, progress bar | Legacy | Visible by default because `trialWidgetEnabled=true`; likely in main scroll and can enter first viewport | No; collapse under Legacy diagnostics or remove from default |
| `src/components/coding/CodingCommandCenterShell.tsx` | expanded proxy diagnostic around lines 8313-8440 | old prompt browser/run buttons, multiple "Running diagnostic..." controls, run summaries | Legacy | Hidden unless proxy details opened, but still tied to default legacy widget | No by default; keep only behind Legacy diagnostics if needed |
| `src/components/coding/CodingCommandCenterShell.tsx` | constant line 226 and active run badge | `trial-explicit-context-safe-20260525-2250` build marker | Stale legacy marker | Visible in default legacy badge | No |
| `src/lib/coding/agent-trials-ui.ts` | `buildAgentTrialUiState`, helpers | Generated command, manual operator request, prompt previews, diagnostics block | Current data builder | Feeds current widget | Yes for data, but UI must separate artifact/debug from submitted prompt |
| `src/components/coding/__tests__/coding-command-center-shell.test.tsx` | Agent Trials and legacy tests | Tests assert old visible surfaces | Test expectations are stale | N/A | Update to enforce clean default UI |

Evidence: inventory found both the current Agent Trials sidebar and the default-enabled legacy proxy diagnostic/proof-run system. The legacy system owns the moving UI-local progress bar and exposes the stale `trial-explicit-context` marker.

Check: GO. No source edits were made in this increment; only this evidence document was updated.

### Increment 1.2 - Remove duplicate visible trial/progress systems

Edits:

- `src/components/coding/CodingCommandCenterShell.tsx`
  - Added a collapsed `Legacy diagnostics` details gate inside the Diagnostics drawer.
  - Rendered the legacy proxy trial diagnostic only when that gate is opened.
  - Changed the Agent Trials badge from ambiguous `Running`/`Ready` to `UI-local proof progress` or `Manual terminal`.
  - Added visible honesty copy: `Manual terminal run only - no live progress stream wired.` or `UI-local progress only; terminal/artifact is source of truth.`
  - Changed the safe preview button running label from `Running...` to `UI-local preview in progress`.
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - Updated helpers to open `Legacy diagnostics` explicitly before using legacy proxy controls.
  - Updated drawer expectations so the legacy proxy diagnostic and proof controls are not default-visible.

Checks:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials sidebar runner|renders the coding command center shell|drawer"
```

Result: PASS, 1 file, 2 tests passed, 71 skipped.

Browser/manual DOM evidence:

- Existing dev server was HTTPS on port 3000.
- Captured screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-1.2-default-desktop.png`
- Browser DOM at `https://localhost:3000/coding` reported:
  - Agent Trials buttons: 1
  - visible `Legacy Proxy Test`: false
  - visible `Proof run controls`: false
  - visible `Operator run request`: false
  - visible `Running...` buttons: 0
  - visible progress bars: 0

Result: GO. Normal `/coding` viewport now has one default trial status source, the Agent Trials sidebar, and the legacy proof/progress system is hidden behind explicit legacy diagnostics.

### Increment 2.1 - Make operator_run_request artifact-only by default

Edits:

- `src/components/coding/CodingCommandCenterShell.tsx`
  - Removed the normal visible `Operator run request` panel from the Agent Trials widget.
  - Moved `Operator run request`, `Last diagnostics block`, and raw execution details under collapsed `Advanced/debug`.
  - Renamed normal diagnostics surface to `Latest diagnostic` and only renders it when the active run state is blocked or failed.
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - Updated Agent Trials test to prove operator text is inside collapsed `Advanced/debug`, not the default widget body.

Checks:

```bash
grep -R "Operator run request" -n src/components/coding src/lib/coding tests/ui-agent-trials | head -50
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials sidebar runner"
```

Result: PASS. The label exists only in the component's collapsed advanced/debug details and in the test that verifies that placement.

Browser/manual evidence:

- Screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-2.1-agent-trials-open.png`
- Browser DOM with Agent Trials open reported:
  - visible `Operator run request`: false
  - visible `hey can you run the 25 agent trial`: false
  - `Advanced/debug` exists: true
  - operator details open: false
  - visible `Actual prompts to be submitted`: true
  - visible `Latest diagnostic`: false

Result: GO. The operator batch request is no longer visible in the normal/default Agent Trials view.

### Increment 2.2 - Rename and reduce Generated command

Edits:

- `src/components/coding/CodingCommandCenterShell.tsx`
  - Added `copyAgentTrialRunnerCommand()` so the normal command Copy button copies only the generated runner command.
  - Replaced the tall generated command block with a compact one-line command row and Copy button.
  - Moved the full command behind collapsed `Show command`.
  - Moved the debug copy action for operator request plus command into collapsed `Advanced/debug` as `Copy debug prompt + command`.
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - Updated Agent Trials expectations for compact command and hidden debug copy.

Checks:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials sidebar runner"
```

Result: PASS, 1 test.

Browser/manual evidence:

- Screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-2.2-agent-trials-command-compact.png`
- Browser DOM with Agent Trials open reported:
  - visible `Show command`: true
  - `Show command` details open: false
  - visible generated command occurrences: 1
  - generated command section height: 102px
  - visible `Copy debug prompt + command`: false
  - visible `Operator run request`: false

Result: GO. The generated command no longer dominates the widget by default.

### Increment 3.1 - Consolidate prompt preview

Edits:

- `src/components/coding/CodingCommandCenterShell.tsx`
  - Replaced `Actual prompts to be submitted` with one `Submitted prompt preview` section.
  - Shows selected count, e.g. `25 prompts selected`.
  - Shows first prompt as the exact submitted prompt card.
  - Shows next two prompts as compact rows.
  - Hides the remaining preview prompts behind `Show all prompts`.
  - Adds a `Current prompt: trial X of N` card during a UI-local running preview.
  - Removed the duplicate `Last submitted prompt` panel.
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - Updated Agent Trials assertions for the consolidated preview and removal of the duplicate panel.

Checks:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials sidebar runner"
grep -R "Actual prompts to be submitted\|Last submitted prompt" -n src/components/coding src/lib/coding tests/ui-agent-trials src/components/coding/__tests__ | head -100
```

Result: PASS. Old labels are absent from source except the test asserting `Last submitted prompt` is gone.

Browser/manual evidence:

- Collapsed screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-3.1-prompt-preview-collapsed.png`
- Expanded screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-3.1-prompt-preview-expanded.png`
- Browser DOM reported:
  - visible `Submitted prompt preview`: true
  - visible `25 prompts selected`: true
  - visible `Last submitted prompt`: false
  - visible old label `Actual prompts to be submitted`: false
  - visible `Operator run request`: false
  - textareas inside prompt preview: 0
  - `Show all prompts` expands normally

Result: GO. Prompt preview is now one section and uses submitted prompt content without operator request leakage.

### Increment 3.2 - Fix scrolling

Edits:

- `src/components/coding/CodingCommandCenterShell.tsx`
  - Prompt previews now render as normal cards/details, not textareas or nested `overflow-auto` prompt boxes.
  - Advanced/debug blocks use normal expanding details instead of trapped internal scroll regions.
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - Added regression coverage that the Agent Trials runner is collapsed by default and the default view does not show submitted preview, operator request, legacy proxy test, or proof controls.

Checks:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials compact|Agent Trials sidebar runner"
```

Result: PASS, 2 tests.

Browser/manual evidence:

- Desktop screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-3.2-desktop-scroll.png`
- Mobile screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-3.2-mobile-default.png`
- Desktop wheel check:
  - wheel over sidebar moved page from `window.scrollY=0` to `600`
  - wheel over main area moved page from `600` to `1180`
  - Agent Trials runner textareas: 0
  - nested scrollboxes inside Agent Trials runner: 0
  - visible `Submitted prompt preview`: true
  - visible `Operator run request`: false
- Mobile check:
  - `Agent Trials` visible: true
  - visible `Operator run request`: false
  - visible `Legacy Proxy Test`: false
  - page scroll height 2483 against viewport height 844, so page-level scrolling is available.

Result: GO. Desktop wheel behavior scrolls the page from sidebar and main task areas, and the Agent Trials prompt area has no tiny nested textarea/scroll trap.

### Increment 4.1 - Make Agent Trials running state truthful

Edits:

- `src/components/coding/CodingCommandCenterShell.tsx`
  - Running badge now uses the explicit label `UI-local demo/proof progress`.
  - Default/manual copy remains `Manual terminal run only - no live progress stream wired.`
  - Active UI-local copy remains `UI-local progress only; terminal/artifact is source of truth.`
  - The action button uses `UI-local preview in progress`, not `Running...`.

Checks:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials compact|Agent Trials sidebar runner"
```

Result: PASS, 2 tests.

Browser/manual evidence:

- Screenshot after triggering Agent Trials safe preview: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-4.1-running-ui-local.png`
- Browser DOM reported:
  - visible `UI-local demo/proof progress`: true
  - visible `UI-local progress only; terminal/artifact is source of truth.`: true
  - visible `Running...` buttons: 0
  - visible `UI-local preview in progress`: true
  - progress bars: none in the current Agent Trials surface
  - no visible language implying live streamed real runner progress

Result: GO. Triggering the widget makes the state read as UI-local proof progress, not a real streamed terminal/artifact runner.

### Increment 4.2 - Add latest artifact summary card

Edits:

- `src/components/coding/CodingCommandCenterShell.tsx`
  - Added a `Latest artifact summary` card to Agent Trials.
  - The card explicitly says browser artifact summary is unavailable instead of faking totals.
  - Shows the last known evidence path and a grep command for submitted prompt/meta-prompt/submitted-through-UI artifact checks.
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - Added assertions for the artifact summary card and unavailable-in-browser copy.

Checks:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials compact|Agent Trials sidebar runner"
```

Result: PASS, 2 tests.

Browser/manual evidence:

- Screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-4.2-artifact-summary.png`
- Browser DOM reported:
  - visible `Latest artifact summary`: true
  - visible unavailable truth copy: true
  - visible `artifact-only`: true
  - visible grep command: true
  - fake `total trials: <number>` summary: false

Result: GO. The browser now gives one honest artifact summary surface without inventing unread browser-side artifact totals.

### Increment 5.1 - Fix hybrid/design Britton-realistic prompts

Edits:

- `tests/ui-agent-trials/fixtures/design-agent-prompts.json`
  - Added messy `submitted_prompt` values to the first five design fixtures used by UI preview and small desktop runs.
- `scripts/agent-trials/run-ui-agent-trials.mjs`
  - Added Britton-realistic fallback generation for design fixtures that do not yet have a `submitted_prompt`.
  - Changed combined/hybrid handoff generation so `britton-realistic` coding handoff prompts are natural/messy and no longer start with `PIVOT:`.
  - Kept clean-control handoff prompts on the existing polished PIVOT packet path.

Checks:

```bash
node -e "JSON.parse(require('fs').readFileSync('tests/ui-agent-trials/fixtures/design-agent-prompts.json','utf8')); console.log('design fixtures json ok')"
node --check scripts/agent-trials/run-ui-agent-trials.mjs
node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 3 --profile britton-realistic
node scripts/agent-trials/run-ui-agent-trials.mjs --agent design --viewport desktop --limit 3 --profile britton-realistic
```

Result: PASS. Combined run passed 3/3 with artifacts at `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-31-00-823Z-combined-desktop-britton-realistic`. Design run passed 3/3 with artifacts at `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-31-29-698Z-design-desktop-britton-realistic`.

Artifact grep evidence:

- Combined `submitted_prompt` examples now start with natural handoff text such as `the design agent says this is the actual issue... can u turn that into the smallest safe coding proposal...`
- Design `submitted_prompt` examples now start with natural prompts such as `this mobile view is still doing that cramped overlap thing...`
- Grep found no `submitted_prompt` beginning with `PIVOT:` in either latest combined or design Britton-realistic run.

Result: GO. Hybrid/design Britton-realistic submitted prompts are now messy natural prompts instead of clean PIVOT packet prompts.

### Increment 5.2 - Add regression test for prompt realism by mode

Edits:

- `tests/ui-agent-trials/realistic-prompt-remediation.test.ts`
  - Added coverage that design Britton-realistic fixture prompts are messy and do not start with PIVOT packet language.
  - Added coverage that Agent Trials hybrid prompt preview uses submitted prompts, not the operator run request.
  - Added coverage that hybrid Britton-realistic previews do not start with PIVOT design packet language.
  - Added coverage that clean-control hybrid previews do not contain noisy Britton wording.

Checks:

```bash
npx --no-install vitest run tests/ui-agent-trials/realistic-prompt-remediation.test.ts src/lib/coding/__tests__/agent-trials-ui.test.ts
```

Result: PASS, 2 files, 16 tests.

Result: GO. Prompt realism now has regression coverage across coding, design, hybrid preview, operator separation, and clean-control separation.

### Increment 6.1 - Cleanup old trial/diagnostic clutter

Edits:

- `src/components/coding/CodingCommandCenterShell.tsx`
  - Removed the stale `trial-explicit-context-safe-20260525-2250` marker from the default active run state badge.
  - Left the build marker only in copyable diagnostic evidence / collapsed legacy diagnostics, not the normal default UI.

Checks:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials compact|Agent Trials sidebar runner|renders the coding command center shell"
```

Result: PASS, 2 tests.

Browser/manual evidence:

- Screenshot: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/increment-6.1-default-cleanliness.png`
- Browser DOM reported:
  - visible `Legacy Proxy Test`: false
  - visible `Proof run controls`: false
  - visible `trial-explicit-context`: false
  - visible `Running diagnostic`: false
  - visible full diagnostics wall: false
  - visible `Operator run request`: false
  - visible `Agent Trials`: true
  - composer exists: true
  - progress bars: 0

Result: GO. The default `/coding` viewport no longer exposes the stale legacy/proof/diagnostic clutter that caused the manual NO-GO.

### Increment 6.2 - Update tests for default UI cleanliness

Edits:

- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
  - Strengthened default Agent Trials cleanliness test to assert no default `Operator run request`, `Legacy Proxy Test`, `Proof run controls`, full diagnostics wall, stale `trial-explicit-context-safe-20260525-2250`, or `Running...` buttons.

Checks:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials compact"
```

Result: PASS, 1 test.

Result: GO. Default UI cleanliness is now guarded by a focused regression test.

### Increment 7.1 - Run checks

Checks:

```bash
npx --no-install vitest run src/lib/coding/__tests__/agent-trials-ui.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx tests/ui-agent-trials/realistic-prompt-remediation.test.ts tests/ui-agent-trials/trial-result-schema.test.ts
node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 3 --profile britton-realistic
node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 3 --profile britton-realistic
grep -R '"submitted_prompt"' -n docs/evidence/agent-runtime-trial-harness/plan-5/artifacts | tail -40
grep -R '"operator_run_request"' -n docs/evidence/agent-runtime-trial-harness/plan-5/artifacts | tail -20
npx --no-install tsc --noEmit --pretty false
git diff --check
git status --branch --short --untracked-files=normal
```

Results:

- Vitest: PASS, 4 files, 92 tests.
- Coding Britton-realistic run: PASS/GO, artifacts at `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-45-59-765Z-coding-desktop-britton-realistic`.
- Combined Britton-realistic run: PASS/GO, artifacts at `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-46-29-821Z-combined-desktop-britton-realistic`.
- Requested broad `submitted_prompt` grep showed latest corrected prompts plus older pre-correction PIVOT artifacts that remain in the historical artifact tree. Follow-up grep against the latest coding and combined artifact roots found no `submitted_prompt` beginning with `PIVOT:`.
- Requested `operator_run_request` grep confirmed operator requests still exist in artifact JSON, as intended.
- Typecheck: PASS.
- `git diff --check`: PASS.
- `git status --branch --short --untracked-files=normal`: dirty tree remains, including pre-existing unrelated changes outside this correction pass. No reset/stash/clean/checkout was run.

Result: GO. Required command checks pass, with the historical-artifact caveat recorded honestly.

### Increment 7.2 - Browser screenshots

Screenshots:

- Default desktop `/coding`: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-default-desktop.png`
- Agent Trials collapsed/default: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-agent-trials-collapsed-default.png`
- Agent Trials prompt preview expanded: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-agent-trials-prompt-preview-expanded.png`
- Running/UI-local state: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-running-ui-local-state.png`
- Mobile default viewport: `docs/evidence/agent-runtime-trial-harness/agent-trials-ui-correction/7.2-mobile-default.png`
- Blocked/failed diagnostics screenshot: not available without fabricating a blocked/failed run; not faked.

Browser/manual evidence:

- Desktop with Agent Trials open/running:
  - visible `Operator run request`: false
  - visible `Legacy Proxy Test`: false
  - visible `Proof run controls`: false
  - visible `Submitted prompt preview`: true
  - visible UI-local progress truth: true
  - `Running...` buttons: 0
  - progress bars in normal Agent Trials surface: 0
  - textareas in Agent Trials runner: 0
- Mobile default:
  - visible `Operator run request`: false
  - visible `Legacy Proxy Test`: false
  - visible `Proof run controls`: false
  - visible `Agent Trials`: true
  - page scroll height 2481 against viewport height 844.

Result: GO. Browser proof exists for default desktop, collapsed Agent Trials, expanded prompt preview, UI-local running state, and mobile default; no fake blocked/failed screenshot was manufactured.
