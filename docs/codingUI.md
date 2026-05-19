# codingUI.md

## 1. Purpose

`/coding` becomes the clean user-facing coding cockpit for everyday Source Proxy work. It should help Britton draft a task, preview a bounded proposal, review the diff, approve only when gates pass, apply only after approval, verify the result, and understand the next safe action.

`/proxy-backend` remains the advanced diagnostic/proxy backend console. It continues to own verbose safety details, bounded proposal internals, diff/approval/verification evidence, replay logs, task history, debug JSON, legacy workflow diagnostics, and backend troubleshooting.

The goal is basic usable UI first, not polished final design. The first version should be calm, readable, and hard to misuse. It should clear diagnostic clutter from `/coding` while preserving the safety system already working behind Source Proxy.

Mobile-first matters because Britton needs comfortable iPhone/Android homelab control. The cockpit must be readable and usable on a phone before complex behavior is added.

Manual Playwright commands must be comfortable for desktop, iPhone, Android, and tablet validation. Device checks should prove that the cockpit loads, primary controls are visible, debug clutter is absent, and illegal actions are not shown.

## 2. Current State

`/proxy-backend` is working as the diagnostics/operator console. It is the right home for backend evidence, replayable logs, detailed task history, raw route/debug output, and troubleshooting.

`/coding` currently still shares or inherits backend-console style and clutter because both `/coding` and `/proxy-backend` render `CodingAgentInterface` with different layout modes. That kept the system useful while Source Proxy was being stabilized, but it now makes the user-facing coding surface too busy.

The old 1/2/3 workflow, debug panes, task history, replay logs, tester proposals, documenter proposals, blueprinter proposals, recent agent runs, and backend troubleshooting should not be the main `/coding` experience.

Source Proxy safety is already the system of record. The new `/coding` UI should simplify the control surface around existing gates instead of creating new authority.

## 3. Authority Boundary

Hard rules:

- `/coding` is a client/control surface only.
- `/proxy-backend` is the diagnostic console.
- Source Proxy APIs enforce safety.
- Source Proxy remains the execution boundary.
- TaskSpec first.
- `allowed_files` required.
- diff preview required.
- verifier/reviewer required.
- human approval required before apply.
- apply is separate from approval.
- commit requires separate approval.
- push requires separate approval.
- no approval bypass.
- no apply without approval.
- no commit or push in first `/coding` UI.
- no secret/path editing.
- no `.env` edits.
- no hidden writes.
- no scheduled/autonomous writes.
- no provider marketplace.
- `/coding` must not bypass `/proxy-backend` or Source Proxy gates.
- `/coding` must not create new backend authority.
- `/coding` must not add autopilot.

## 4. UX Principles

- Mobile-first single-column layout.
- Desktop/tablet two-column layout only when there is room.
- Big touch targets.
- Avoid tiny adjacent dangerous buttons.
- Sticky bottom action bar on mobile.
- Use iOS/mobile tap target and readable touch UI principles.
- Use Android/Material adaptive layout basics where useful.
- Use Playwright device emulation for iPhone, Android, tablet, and desktop.
- Mention AionUi, Cline, Goose, and OpenCode only as UX/reference vocabulary, not as authority.

Plain state language:

- Draft
- Preview ready
- Needs approval
- Approved, not applied
- Applied, verification required
- Verified
- Blocked

Every state must answer:

1. What is happening?
2. What changed?
3. What is the next safe action?
4. Has anything been applied?

## 5. /coding Target Layout

### Header

- Title: `Coding`
- proxy connection status
- current route/model status
- workspace/repo label
- link: `Advanced diagnostics -> /proxy-backend`

### Task Composer

- task textarea
- target file input
- allowed files input or simple summary
- optional expected checks
- route/model selector, minimal
- primary button: `Preview safely`
- no commit/push controls
- copy: `No files will be changed during preview.`

### Current Task Timeline

Stages:

- Draft
- Plan
- Diff
- Approval
- Apply
- Verification
- Done

### Diff Review

- changed files list
- target match
- allowed files result
- protected path result
- diff body
- reviewer/verifier summary
- link to full diagnostics in `/proxy-backend`

### Action Bar

Mobile sticky bottom:

- Reject
- Approve
- Apply approved diff
- Verify

Buttons appear only when legal. Dangerous actions must never be adjacent without clear state text explaining what will happen and whether anything has already been applied.

### Receipt / Result

- last action
- files changed
- checks run
- next safe action
- rollback hint
- link to `/proxy-backend` task evidence

## 6. What to Remove/Clear From /coding

Remove or hide from the `/coding` main surface:

- proxy safety smoke proposals
- tester agent proposals
- documenter/blueprinter proposals
- replayable logs
- workflow memory
- raw debug JSON
- old 1/2/3/4/5/6/7 workflow labels as the main structure
- recent agent runs wall
- advanced task queues
- local model debug internals
- backend route troubleshooting

These remain available in `/proxy-backend`.

## 7. Implementation Phases

Each increment must include:

- Goal
- Files likely changed
- What to implement
- Safety invariants
- Automated checks
- Manual browser checks
- Manual Playwright checks
- Expected output
- Britton's next step

# Phase 0: Documentation and Baseline

## Increment 0.1 — Create docs/codingUI.md only

Goal:
Write this plan only.

Files:

- `docs/codingUI.md`

What to implement:

- Create this planning document.
- Do not implement `/coding`.
- Do not modify `/coding` source code.
- Do not modify `/proxy-backend`.
- Do not modify Source Proxy backend behavior.
- Do not apply, commit, or push.

Safety invariants:

- Documentation-only change.
- No source code changed.
- No backend behavior changed.
- No apply/commit/push.

Automated checks:

```bash
git diff --check
```

Manual checks:

```bash
sed -n '1,260p' docs/codingUI.md
grep -n "Source Proxy remains" docs/codingUI.md
grep -n "/proxy-backend" docs/codingUI.md
grep -n "Manual Playwright" docs/codingUI.md
```

Expected output:

- file exists
- no source code changed
- safety boundaries documented
- implementation phases present

Britton's next step:
Review plan and approve Increment 1.1.

# Phase 1: Clear /coding Into a Shell

## Increment 1.1 — Add CodingCockpitShell placeholder

Goal:
Replace `/coding`'s diagnostic-heavy main view with a clean shell while keeping `/proxy-backend` unchanged.

Files likely changed:

- `src/app/coding/page.tsx`
- `src/components/coding/CodingCockpitShell.tsx` or similar
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

What to implement:

- `/coding` renders a new lightweight shell.
- Header says `Coding`.
- Show proxy status placeholder or basic fetched status if safe.
- Link to `/proxy-backend`.
- Show empty task composer placeholder.
- Show `No active task` state.
- Do not wire apply/approval yet unless existing safe components can be reused read-only.
- Keep `/proxy-backend` rendering the existing diagnostic console.

Safety invariants:

- `/proxy-backend` unchanged.
- no backend behavior change.
- no apply/commit/push controls.
- no hidden writes.
- no approval or apply action added.

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
git diff --check
```

Manual browser checks:

- open `https://10.0.0.186:3000/coding`
- open `https://10.0.0.186:3000/proxy-backend`
- confirm `/coding` is clean shell
- confirm `/proxy-backend` still has diagnostics
- confirm no console crash

Manual Playwright checks:

- desktop load `/coding`
- iPhone viewport load `/coding`
- Android viewport load `/coding`
- assert header visible
- assert Advanced diagnostics link visible
- assert no debug JSON visible

Expected output:

- `/coding` is cleared and simple
- `/proxy-backend` remains diagnostic
- no safety behavior changed

Britton's next step:
Approve Increment 1.2 if `/coding` shell is stable.

## Increment 1.2 — Mobile-first responsive layout

Goal:
Make `/coding` readable and usable on phone before adding complex behavior.

Files likely changed:

- `src/components/coding/CodingCockpitShell.tsx`
- optional CSS/module or Tailwind classes
- tests

What to implement:

- single-column mobile layout
- comfortable spacing
- sticky or fixed bottom action region placeholder
- no horizontal scroll
- large touch areas
- desktop/tablet layout can use two columns

Safety invariants:

- no backend changes
- no apply/commit/push
- no hidden writes

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
git diff --check
```

Manual browser checks:

- phone browser or responsive mode
- desktop browser
- no horizontal scrolling
- fields readable

Manual Playwright commands:

```bash
npx playwright test tests/e2e/coding-ui.spec.ts --project=chromium
npx playwright test tests/e2e/coding-ui.spec.ts --project="Mobile Safari"
npx playwright test tests/e2e/coding-ui.spec.ts --project="Pixel 5"
npx playwright test tests/e2e/coding-ui.spec.ts --project="iPad"
```

Expected output:

- `/coding` basic shell fits mobile
- Advanced diagnostics link is reachable
- no debug clutter

Britton's next step:
Approve wiring the task composer.

# Phase 2: Task Composer and Safe Preview

## Increment 2.1 — Add basic task composer

Goal:
Let user enter task, target file, allowed files, expected checks.

Files likely changed:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/lib/coding/proposal-task-handoff.ts` reuse if appropriate
- tests

What to implement:

- task textarea
- target file input
- allowed files input
- expected checks input
- button: `Preview safely`
- validation:
  - task required
  - target required
  - allowed files required
  - protected targets blocked in UI but backend remains final authority
- copy: `No files will be changed during preview.`

Safety invariants:

- preview only
- no approval/apply yet
- no commit/push
- backend remains final authority

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
# Python proxy tests if any route wiring changes
git diff --check
```

Manual browser checks:

- empty form blocks
- docs target enables preview
- `.env` target blocks visibly
- `/proxy-backend` still works

Manual Playwright checks:

- desktop and mobile form render
- empty form shows validation
- `.env` target shows protected-target block
- approve/apply controls are absent

Expected output:

- user can compose safe proposal
- no file writes

Britton's next step:
Run a preview-only docs test.

## Increment 2.2 — Wire preview safely

Goal:
Preview a bounded proposal through existing Source Proxy preview flow.

Files likely changed:

- `src/components/coding/CodingCockpitShell.tsx`
- possibly a small client hook
- existing `/v1` routes only; do not create new backend authority

What to implement:

- Submit to existing safe preview/proposal route.
- Show target.
- Show changed files.
- Show `Preview ready. No files changed yet.`
- If backend returns blocker, show blocker and next safe action.
- Link to `/proxy-backend` details for current task.

Safety invariants:

- preview only
- approval not yet exposed unless gates pass
- no apply
- no commit/push
- no new backend authority

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
# relevant Python tests if backend touched
git diff --check
```

Manual safe test:

Task:
Append exact sentence to `docs/phase-8-manual-check.md`:

```text
Coding cockpit preview smoke test passed.
```

Target:

```text
docs/phase-8-manual-check.md
```

Allowed:

```text
docs/phase-8-manual-check.md
```

Expected:

- diff preview ready
- no file changed before approval
- grep returns nothing before apply

Expected terminal output:

```bash
grep -n "Coding cockpit preview smoke test passed." docs/phase-8-manual-check.md || true
```

Should return nothing before apply.

Manual Playwright checks:

- preview request can be mocked or run against idle backend
- preview result shows changed files and no-applied state
- apply control is absent

Expected output:

- preview evidence is visible
- no file writes

Britton's next step:
Approve adding approval display.

# Phase 3: Approval and Apply Controls

## Increment 3.1 — Show approval state without apply

Goal:
Show approval gates clearly but do not apply yet.

Files likely changed:

- `src/components/coding/CodingCockpitShell.tsx`
- tests

What to implement:

- approval availability
- target match
- allowed files
- protected path
- requirement coverage
- reviewer/verifier summary
- no apply button yet

Safety invariants:

- no apply button
- no commit/push
- approval display does not mutate state beyond existing preview/session state
- backend remains final authority

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
git diff --check
```

Manual browser checks:

- safe docs diff shows approval available
- protected target shows approval unavailable
- no apply button exists
- `/proxy-backend` still shows full diagnostics

Manual Playwright checks:

- approval status renders on desktop/mobile
- protected state blocks approval display
- no apply button before Increment 3.2

Expected output:

- user can tell why approval is or is not available
- no files changed

Britton's next step:
Approve adding apply control.

## Increment 3.2 — Add approve/apply flow

Goal:
Expose human approval and apply approved diff using existing protected execution layer.

Files likely changed:

- `src/components/coding/CodingCockpitShell.tsx`
- possibly existing approval binding helpers
- tests

What to implement:

- Approve button only when backend says approval is available.
- Apply approved diff button only after approval.
- Clear state copy:
  - `Preview ready: no files changed`
  - `Approved: files still unchanged`
  - `Applied: verification required`

Safety invariants:

- no apply without approval
- apply uses existing protected execution layer
- approval ID/task binding is preserved
- no commit/push
- no hidden writes

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_source_proxy_end_to_end.py source_proxy/tests/test_long_running_tasks.py
git diff --check
```

Manual positive test:

- docs append task
- preview
- confirm grep returns nothing before apply
- approve
- apply
- confirm grep finds sentence after apply
- git diff only shows docs file

Manual Playwright checks:

- approve appears only when legal
- apply appears only after approval
- mobile sticky action bar does not place dangerous controls without state copy

Expected output:

- apply writes only allowed file
- verification required

Britton's next step:
Approve verification UI.

# Phase 4: Verification UI

## Increment 4.1 — Add verification status and manual verification

Goal:
After apply, show verification checklist.

Files likely changed:

- `src/components/coding/CodingCockpitShell.tsx`
- tests

What to implement:

- changed file summary
- rollback hint
- checks run/pending
- manual verification checklist for docs-only
- mark verification complete only via existing backend verification flow if available

Safety invariants:

- verification state does not imply commit approval
- no commit/push buttons
- no hidden writes
- backend remains final authority

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
git diff --check
```

Manual browser checks:

- after docs apply, verification required appears
- checking file and unintended changes works
- mark complete updates state only through allowed verification flow
- commit still unavailable from `/coding`

Manual Playwright checks:

- applied state shows verification required
- receipt remains unavailable until verification state is clear
- commit/push controls are absent

Expected output:

- task reaches verified/done
- commit still not available from `/coding`

Britton's next step:
Approve task receipt.

## Increment 4.2 — Add task receipt

Goal:
Show final result.

Files likely changed:

- `src/components/coding/CodingCockpitShell.tsx`
- tests

What to implement:

- what happened
- files changed
- checks passed
- next safe action
- link to `/proxy-backend` evidence

Safety invariants:

- no commit/push buttons
- receipt is evidence display only
- no hidden writes

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
git diff --check
```

Manual browser checks:

- completed docs task shows clear receipt
- receipt links to diagnostics
- no commit/push visible

Manual Playwright checks:

- receipt renders on desktop/mobile
- diagnostics link visible
- no debug JSON visible by default

Expected output:

- clear final receipt
- link to diagnostics

Britton's next step:
Approve mobile/Playwright pass.

# Phase 5: Mobile and Playwright Validation

## Increment 5.1 — Add Playwright smoke tests

Goal:
Manual Playwright commands for desktop/iPhone/Android/tablet.

Files likely changed:

- `playwright.config.ts` if existing
- `tests/e2e/coding-ui.spec.ts`
- do not add heavy dependency if Playwright is not installed unless approved

What to implement:

- `/coding` loads desktop
- `/coding` loads Mobile Safari emulation
- `/coding` loads Pixel emulation
- `/coding` loads tablet emulation
- no debug JSON by default
- advanced diagnostics link visible
- composer visible
- action bar visible on mobile
- approve/apply not visible before preview

Safety invariants:

- tests do not apply changes
- tests use mock/idle state unless safe preview test is explicitly approved
- no commit/push
- no backend authority changes

Automated checks:

```bash
npm run typecheck
npx vitest run src/components/coding
git diff --check
```

Manual Playwright commands:

```bash
npx playwright test tests/e2e/coding-ui.spec.ts --project=chromium
npx playwright test tests/e2e/coding-ui.spec.ts --project="Mobile Safari"
npx playwright test tests/e2e/coding-ui.spec.ts --project="Pixel 5"
npx playwright test tests/e2e/coding-ui.spec.ts --project="iPad"
```

Expected Playwright output:

- desktop test passes
- Mobile Safari emulation passes
- Pixel emulation passes
- iPad/tablet emulation passes
- failures include screenshot/trace path if enabled

Manual browser checks:

- inspect `/coding` in responsive browser mode
- confirm no horizontal scroll
- confirm debug JSON is absent
- confirm action bar is visible on mobile

Expected output:

- all device smoke checks pass or documented if Playwright not installed

Britton's next step:
Approve real mobile manual check.

## Increment 5.2 — Real device manual checks

Goal:
Validate on iPhone/Android browser via LAN.

Files likely changed:

- none expected unless minor UI fixes are approved

What to implement:

- Manual validation only unless defects are found and separately scoped.

Safety invariants:

- no backend changes
- no apply unless a separate approved safe docs test is active
- no commit/push

Automated checks:

```bash
git diff --check
```

Manual browser checks:

- open `https://10.0.0.186:3000/coding`
- no horizontal scroll
- fields usable
- keyboard does not hide primary action completely
- action bar reachable
- `/proxy-backend` link works
- no accidental apply

Manual Playwright checks:

- rerun Increment 5.1 commands if any responsive fix was made

Expected output:

- phone usable enough
- no final polish required yet

Britton's next step:
Approve closeout.

# Phase 6: Closeout

## Increment 6.1 — Regression and closeout audit

Goal:
Confirm `/coding` cockpit is stable enough for daily use.

Files likely changed:

- none expected unless closeout reveals a scoped fix

What to implement:

- Run regression checks.
- Perform manual positive and protected-target checks.
- Record blockers, if any.

Safety invariants:

- no commit/push from `/coding`
- apply only through approved Source Proxy flow
- protected targets block
- `/proxy-backend` remains diagnostic

Run:

```bash
npm run typecheck
npx vitest run src/components/coding
PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_source_proxy_end_to_end.py \
  source_proxy/tests/test_coding_regression_pack.py \
  source_proxy/tests/test_proxy_agent_routing.py
git diff --check
```

Manual browser checks:

- `/coding` loads
- `/proxy-backend` loads
- positive docs preview/apply/verify works
- protected target blocks
- no commit/push

Manual Playwright checks:

```bash
npx playwright test tests/e2e/coding-ui.spec.ts --project=chromium
npx playwright test tests/e2e/coding-ui.spec.ts --project="Mobile Safari"
npx playwright test tests/e2e/coding-ui.spec.ts --project="Pixel 5"
npx playwright test tests/e2e/coding-ui.spec.ts --project="iPad"
```

Expected output:

- clean test pass
- ready for commit-readiness audit

Britton's next step:
Ask for commit-readiness audit only.

## 8. Non-goals

- no final visual polish
- no native mobile app
- no AionUi bridge
- no provider marketplace
- no commit/push controls in `/coding` first version
- no autonomous writes
- no scheduled tasks
- no production deploy work
- no Source Proxy backend behavior changes unless a later approved increment explicitly requires them
- no `/proxy-backend` simplification or redesign in this plan

## 9. First Cursor Implementation Prompt

```text
Implement only Increment 1.1. Clear /coding into a clean shell and keep /proxy-backend untouched. Do not implement later phases. Do not commit. Do not push.

Scope:
- Replace /coding's diagnostic-heavy main view with a clean CodingCockpitShell placeholder.
- Keep /proxy-backend rendering the existing diagnostic console.
- Do not modify Source Proxy backend behavior.
- Do not add approval, apply, commit, or push controls.
- Do not implement later phases.

Validation:
- npm run typecheck
- npx vitest run src/components/coding
- git diff --check
- manual load /coding and /proxy-backend

Output required:
- files changed
- test results
- screenshots/manual notes
- confirmation /proxy-backend unchanged
- no commit/push
```
