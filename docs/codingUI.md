# Source Proxy Command Center v0.1: Codex/AionUi-Like Basic UX Before Final Polish

status: active planning

Status date: 2026-05-20

## Planning Lock

This is the active master plan for getting Source Proxy `/coding` back on track as an everyday coding command center.

The recent UI-Closeout-Repair pass was a docs/status and terminal-health repair pass. It confirmed safety and route health, but it did not solve the product problem: `/coding` still reads like stacked safety/process panels instead of a project command center for organizing and doing coding work.

Implementation comes before final visual polish. The first goal is the basic Codex/AionUi-like command-center UX shape, then functionality confirmation, then bug cleanup, and only then final visual polish.

Reference direction:

- Borrow Codex-like and AionUi-like UX/layout ideas only.
- Do not integrate AionUi.
- Do not add an AionUi bridge.
- Do not copy AionUi authority.
- Do not grant Codex CLI or any worker new trust by default.
- Do not add commit, push, apply, or approval bypasses.

Preserved Source Proxy safety loop:

```text
Draft -> Preview -> Approval -> Apply -> Verify
```

`/coding` is the everyday command center. `/proxy-backend` is the deep diagnostics surface.

## Current Closeout Baseline

Current confirmed closeout evidence from 2026-05-20:

- `git status` was `main...origin/main [ahead 30]`.
- Only `docs/codingUI.md` was modified during closeout.
- `git diff --check` passed.
- `npm run lint` passed with 7 existing warnings and 0 errors.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed, 6 tests.
- `global-safety-regression` passed.
- `/coding` returned `200 OK`.
- `/proxy-backend` returned `200 OK`.
- Screenshot/viewport review was blocked because the prior environment had no Playwright package and no local browser binary.
- No commit or push was performed.

Do not claim desktop/mobile viewport review is cleared until a real browser or runnable Playwright setup proves it.

## v0.3 Stress Testing Gate Redirect

PLAN STOP: v0.3 Controlled Frontend Usage / UI Polish Lane Paused

The old v0.3 stress plan remains archived evidence. The active next step is not frontend proof, viewport proof, mobile proof, controlled frontend usage, final visual polish, or Codex-wrapper implementation.

PLAN START: Source Proxy Coding Agent A+ Stress Gauntlet

The Source Proxy Coding Agent A+ Stress Gauntlet reached its decision gate in `docs/source-proxy-coding-agent-a-plus-stress-gauntlet.md`. Any future Codex-wrapper work must start only after explicit operator permission and must consume the engine contracts, receipts, traces, task states, and verification outputs instead of becoming the source of truth.

The preserved safety loop remains `Draft -> Preview -> Approval -> Apply -> Verify`.

Next increment title:
No next gauntlet increment: A+ decision gate reached; await explicit operator permission for wrapper work

## Current UI Problem

The current `/coding` page is logically safe, but it still has a safety/process-dashboard feel:

- Draft, Preview, Approval, Apply, Verify stepper.
- Proxy, Route, Workspace strip.
- Current State section.
- Task, Target, Safe Next Action cards.
- Evidence trail.
- Task Composer panel.

This must become a work command center where the operator can organize projects, pick active tasks, compose work, review diff/evidence, and keep diagnostics out of the way unless needed.

## Command Center Target Layout

### Left rail

- Workspaces/projects.
- Active tasks.
- Waiting approval.
- Blocked.
- Verified/done.
- Recent tasks.

### Center

- Active task thread/workspace.
- Task composer at bottom or as the primary action area.
- Target/allowed files selector.
- Model/route/permission strip.
- Task status header.
- Simple current state summary.

### Right

- Review pane.
- Changed files.
- Diff summary.
- Verifier/reviewer result.
- Safe next action.
- Collapsed evidence/artifacts drawer.

### Bottom/Drawer

- Terminal output.
- Receipts.
- Raw logs.
- Backend diagnostics.
- Hidden unless failed or explicitly opened.

## Reuse And Boundary Notes

Reusable existing pieces:

- `src/app/coding/page.tsx` already routes `/coding` to `CodingCockpitShell`.
- `src/components/coding/CodingCockpitShell.tsx` already contains the composer, preview, approval, apply-gated state, diff summary, route/model selector, protected target UI block, collapsed evidence details, mobile action bar, and `/proxy-backend` links.
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx` already covers the safe preview, protected target block, approval/apply separation, no commit/push copy, and diagnostics links.
- `src/components/coding/CodingAgentInterface.tsx` contains many older Source Proxy helper surfaces and derived state helpers, but it is over 500KB and should not be broadly rewritten during the basic shell increment.
- `src/lib/coding/*` contains reusable parsing, route payload, proposal handoff, unified diff path, and workflow progress helpers.

Known tooling state:

- `playwright.config.mjs` exists and defines desktop/mobile projects.
- `package.json` does not list `@playwright/test`, so screenshot/viewport checks are not cleared unless local tooling is installed or otherwise runnable in a later approved increment.

Authority boundary:

- `/coding` remains UI/client orchestration over existing Source Proxy contracts.
- `/proxy-backend` remains the diagnostic console.
- No backend authority changes are allowed unless a missing existing contract is proven and separately approved.
- No model/provider routing behavior changes are allowed in this v0.1 plan.
- No autopilot, mobile execution authority, AionUi integration, commit, push, hidden write, broad cleanup, or secret/.env edits.
- Approval, apply, commit, and push remain separate concepts.

## Phase 0: Truth Lock and Closeout Baseline

Goal:
Verify the closeout status and prevent Codex from building on stale or contradictory plan state.

Small increments:

- 0.1 Inspect current docs and identify contradictions.
- 0.2 Update `docs/codingUI.md` with the new command-center direction.
- 0.3 Record that Playwright/real viewport review is not cleared yet unless actually runnable.
- 0.4 Confirm `/coding` remains UI-only and `/proxy-backend` remains diagnostics.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run lint
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
```

Expected output:

- Only intended docs files are modified.
- Lint has warnings only, no errors.
- Typecheck passes.
- Cockpit shell test passes.
- No commit or push.

Next increment title:
Phase 1.1: Command center information architecture map

## Phase 1: Command Center Information Architecture

Goal:
Convert `/coding` from stacked safety panels into a Codex/AionUi-like work command center layout.

Small increments:

- 1.1 Write an IA map from current UI sections to new command-center zones.
- 1.2 Identify components that can be reused without backend changes.
- 1.3 Identify any props/state already available for route/model/permission/task status.
- 1.4 Define the minimum v0.1 UI skeleton.
- 1.5 Define what moves to `/proxy-backend`.

IA map draft:

| Current `/coding` section | Command-center zone | v0.1 handling |
| --- | --- | --- |
| Top navigation | Left rail or compact workspace switcher | Keep global nav, but make command center organization the dominant structure. |
| Draft/Preview/Approval/Apply/Verify stepper | Center task status header | Preserve safety loop as compact state, not the page's main visual weight. |
| Proxy/Route/Workspace strip | Center route/model/permission strip | Keep visible and honest; do not alter routing behavior. |
| Current State | Center active task header | Collapse to task title, state, target, and concise current summary. |
| Task/Target/Safe Next Action cards | Center header plus right review pane | Move safe next action to right pane; target belongs near composer/header. |
| Evidence trail | Right drawer or bottom drawer | Collapsed by default unless failed or opened. |
| Terminal/Test Evidence | Bottom drawer | Hidden unless failed or explicitly opened. |
| Task Composer | Center primary action area | Keep primary and ergonomic. |
| Diff Review | Right review pane | Show changed files, diff summary, reviewer/verifier results. |
| Advanced diagnostics links | Right/bottom diagnostics affordance | Keep linking to `/proxy-backend`; do not reproduce diagnostics in `/coding`. |

Minimum v0.1 skeleton:

- Left rail with static/project-derived organization using existing data only.
- Center active task workspace with task status header, route/model/permission strip, composer, target/allowed files controls, and current summary.
- Right review pane with changed files, diff summary, reviewer/verifier status, safe next action, and collapsed evidence/artifacts.
- Bottom/drawer surface for terminal output, receipts, raw logs, and backend diagnostics.
- Empty states for no active task, select or create a task, preview safely before writes, and review changes before approval.

Manual checks:

```bash
grep -n "Command Center v0.1" docs/codingUI.md
grep -n "Left rail" docs/codingUI.md
grep -n "Right" docs/codingUI.md
git diff --check -- docs/codingUI.md
```

Expected output:

- Docs describe a command-center shell, not a panel stack.
- No code implementation yet.
- No backend authority changes.

Next increment title:
Phase 2.1: Build static command-center shell behind existing behavior

## Phase 1.1 Closeout: Command Center Information Architecture Map

Status: complete as docs-only IA alignment.

Purpose:
Convert the current vertical panel stack into an explicit command-center map that Phase 2 can implement without changing backend contracts or Source Proxy authority.

Observed current `/coding` stack:

- Global nav row.
- Hero/header with `Source Proxy cockpit`, `Coding`, helper copy, and `Advanced diagnostics`.
- `Coding status` section with the Draft, Preview, Approval, Apply, Verify stepper.
- Proxy/Route/Workspace metadata strip.
- `Current State` section.
- Task, Target, and Safe next action cards.
- Collapsed `Evidence trail` with role timeline and terminal/test evidence.
- `Task Composer` panel.
- Collapsed `Advanced options` for target, allowed files, expected checks, and route/model.
- Preview readiness status.
- `Diff Review` panel after preview.
- `Safe Next Action` panel after preview.
- `Review gates` details after preview.
- Mobile action bar and diagnostics link.

Command-center zone map:

| v0.1 zone | Current source | Target behavior |
| --- | --- | --- |
| Left rail: workspace switcher | Current global nav row plus hard-coded `Workspace: SpiritOS` | Show SpiritOS as the active workspace/project. Keep global navigation available but make workspace/task organization the main left-side affordance. |
| Left rail: task queues | No real queue in `CodingCockpitShell`; older `CodingAgentInterface` has task/history helpers | Add placeholders or derived buckets only from existing state: Active task, Waiting approval, Blocked, Verified/done, Recent. Do not invent backend task authority. |
| Center: active task header | `Current State`, Task card, Target card, current status label | Combine into one compact task header with title, state, target, and last safe state summary. |
| Center: safety loop | `Coding status` stepper | Keep `Draft -> Preview -> Approval -> Apply -> Verify` as a compact status header. It must remain visible but stop dominating the page. |
| Center: context strip | Proxy/Route/Workspace strip and Route/model field | Show route, model, permission/scope, workspace, target, and allowed files near the active task. Display only what is known; do not imply active routing changes. |
| Center: task workspace/thread | Currently missing as a distinct concept | Reserve the central area for the active task flow: prompt/task text, preview state, human decisions, and task messages when they exist. |
| Center: composer | `Task Composer` panel | Keep composer as the primary work input. Prefer bottom or lower-center placement so the page feels like a working task thread, not a form dashboard. |
| Right: review pane | `Diff Review`, `Review gates`, changed files, reviewer/verifier summaries | Move review facts to the right pane: changed files, diff summary, target/allowed/protected gates, reviewer/verifier state, and approval availability. |
| Right: safe next action | Safe next action card and `Safe Next Action` panel | Keep one visible next action in the right pane. Avoid duplicating it in multiple cards. |
| Right: artifacts/evidence drawer | Collapsed `Evidence trail` and review evidence | Keep collapsed by default unless failed or explicitly opened. Show concise evidence receipts before raw logs. |
| Bottom drawer: terminal/logs | `Terminal/Test Evidence` inside evidence details | Move terminal output, receipts, raw logs, and backend diagnostics to a bottom drawer. It should open automatically only for failed/blocked states if implementation later chooses that behavior. |
| Diagnostics escape hatch | `Advanced diagnostics`, `/proxy-backend` links | Keep explicit links to `/proxy-backend`; do not reproduce deep diagnostics inside `/coding`. |
| Mobile command surface | Current fixed mobile action bar | Preserve mobile monitoring and review affordances, but do not add new mobile execution authority. |

v0.1 information priority:

1. Active workspace/project and task list.
2. Active task state and safety loop.
3. Composer and task scope.
4. Route/model/permission honesty.
5. Review/diff/safe next action.
6. Evidence, logs, receipts, and diagnostics only when needed.

Explicit non-goals for Phase 2:

- No new backend task queue contract.
- No provider/model routing behavior changes.
- No AionUi integration or bridge.
- No new apply, approval, commit, push, or execute-approved authority.
- No broad extraction of `CodingAgentInterface.tsx`.
- No final visual polish before functionality and bug cleanup.

Recommended Phase 2 implementation shape:

- Refactor `CodingCockpitShell` layout first, because it already owns the active `/coding` shell and targeted tests.
- Keep existing state names and handlers where possible: `task`, `targetFile`, `allowedFiles`, `expectedChecks`, `routeModel`, `draftReady`, `previewState`, `handleDraftPreview`, `handleApprovePreview`, and `handleApplyApprovedDiff`.
- Introduce small presentational sections inside the same file or small sibling components only if they reduce layout risk.
- Update `coding-cockpit-shell.test.tsx` to assert the command-center zones and preserve the existing safety assertions.
- Leave `CodingAgentInterface.tsx` as a later extraction/cleanup target unless Phase 2 needs one specific helper.

Phase 1.1 manual check:

```bash
cd /home/source/SpiritOS
grep -n "Phase 1.1 Closeout" docs/codingUI.md
grep -n "Command-center zone map" docs/codingUI.md
grep -n "v0.1 information priority" docs/codingUI.md
git diff --check -- docs/codingUI.md
git status --branch --short
```

Phase 1.1 expected output:

- `docs/codingUI.md` contains the IA closeout, zone map, information priority, and Phase 2 implementation shape.
- Only intended docs files are modified.
- `git diff --check -- docs/codingUI.md` has no output.
- No UI code, backend code, tests, secrets, commits, pushes, applies, or execute-approved actions changed in this increment.

## Phase 2: Basic Command Center Shell

Goal:
Implement the initial shell shape without changing task authority.

Small increments:

- 2.1 Add or refactor a `/coding` shell layout with left rail, center workspace, and right review pane.
- 2.2 Move the existing stepper into a compact task status header.
- 2.3 Move Current State into a single concise active task header.
- 2.4 Move Evidence Trail into a collapsed drawer or right-pane section.
- 2.5 Keep Task Composer as the primary action area.
- 2.6 Add project/task list placeholders using existing data only, no fake backend authority.
- 2.7 Add empty states that feel like a coding workspace:
  - No active task.
  - Select or create a task.
  - Preview safely before writes.
  - Review changes before approval.

Manual checks:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
curl -k -sS -I https://localhost:3000/coding
```

Expected output:

- `/coding` route returns `200`.
- Cockpit shell test passes or is intentionally updated for new layout.
- `Draft -> Preview -> Approval -> Apply -> Verify` remains visible but no longer dominates the whole page.
- Evidence is collapsed by default.
- Task composer feels primary.
- No backend behavior changes.

Next increment title:
Phase 3.1: Preserve Source Proxy functionality contracts

## Phase 2.1 Closeout: Static Command-Center Shell

Status: implemented as the first basic shell refactor.

Scope completed:

- Added a left project/task rail to `CodingCockpitShell`.
- Added a center workspace wrapper around the existing status, current state, composer, preview, approval, and review-gate flow.
- Added a right review pane for changed files, preview status, verifier/reviewer state, next safe move, collapsed artifacts/logs, and diagnostics link.
- Preserved existing state variables and handlers for preview, approval, reject, and apply.
- Updated the focused cockpit shell test to assert the command-center regions while preserving existing safety checks.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Authority notes:

- No backend behavior changed.
- No Source Proxy route changed.
- No model/provider routing behavior changed.
- No new task queue backend contract was introduced.
- No apply, execute-approved, commit, push, secret edit, destructive cleanup, or AionUi integration was performed.
- Existing apply UI behavior remains gated by the same client state as before this shell refactor.

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.

Still to run when a local server/browser is available:

```bash
cd /home/source/SpiritOS
curl -k -sS -I https://localhost:3000/coding
```

Expected output:

- `/coding` returns `200`.
- The page presents a left rail, center workspace, and right review pane.
- `Draft -> Preview -> Approval -> Apply -> Verify` remains visible.
- Evidence/artifacts/logs remain collapsed by default.
- No backend authority changes.

Next increment title:
Phase 2.2: Move the existing stepper into a compact task status header

## Phase 2.2 Closeout: Compact Task Status Header

Status: implemented.

Scope completed:

- Moved the `Draft -> Preview -> Approval -> Apply -> Verify` stepper out of its own standalone status card.
- Folded the safety loop into the active task header as a compact `Coding status` strip.
- Kept route/model/workspace context visible directly under the compact status strip.
- Renamed the old `Current State` heading to `Task status` to make the center workspace feel like an active task header rather than a process panel.
- Preserved the existing preview, approval, apply, reject, evidence, diagnostics, and mobile action behavior.
- Updated the focused cockpit shell test for the new heading while preserving safety-loop assertions.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
npm run lint
curl -k -sS -I --max-time 10 https://localhost:3000/coding
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `/coding` returned `200 OK`.

Authority notes:

- No backend behavior changed.
- No Source Proxy route changed.
- No provider/model routing behavior changed.
- No new apply, execute-approved, approval, commit, push, or mobile execution authority was added.
- No secret, `.env`, destructive cleanup, or AionUi integration work occurred.

Next increment title:
Phase 2.3: Move Current State into a single concise active task header

## Phase 2.3 Closeout: SpiritOS Chrome And Theme Alignment

Status: implemented.

Scope completed:

- Removed the bespoke `/coding` horizontal navbar that duplicated app navigation.
- Mounted the shared SpiritOS `DashboardDemoV4FloatingNav` desktop and mobile navigation on `/coding`.
- Kept `Source` active in the shared nav for `/coding`.
- Wrapped `/coding` in the existing dashboard v4 route shell so it uses the SpiritOS route chrome.
- Shifted the command-center shell toward SpiritOS theme variables and shared glass surfaces instead of the isolated slate/emerald mini-theme.
- Kept the active task header concise as the single `Task status` surface with compact `Coding status` inside it.
- Moved the mobile action bar above the shared mobile pill nav to avoid overlap.
- Updated the focused cockpit shell test to use the shared SpiritOS nav assertions.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
npm run lint
curl -k -sS -I --max-time 10 https://localhost:3000/coding
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `/coding` returned `200 OK`.

Authority notes:

- No backend behavior changed.
- No Source Proxy route changed.
- No provider/model routing behavior changed.
- No new apply, execute-approved, approval, commit, push, or mobile execution authority was added.
- No secret, `.env`, destructive cleanup, or AionUi integration work occurred.

Remaining visual gap:

- Real screenshot/viewport review is still not cleared. The shared nav and theme alignment are implemented by code and route smoke, but desktop/mobile visual framing still needs actual browser review.

Next increment title:
Phase 2.4: Move Evidence Trail into a collapsed drawer or right-pane section

## Phase 2.4 Closeout: Remove Hero Copy And Move Evidence Right

Status: implemented.

Scope completed:

- Removed the visible explanatory `/coding` hero/header block.
- Kept a screen-reader `Coding` heading for accessibility without showing the operator a redundant page explanation.
- Replaced the oversized glass-pearl widget treatment with flatter SpiritOS-themed panels using shared route theme variables.
- Improved text contrast in task, target, safe-action, composer, evidence, and review widgets.
- Moved the Evidence Trail out of the center task header and into the right-side collapsed `Evidence trail and logs` drawer.
- Kept backend diagnostics available from the right review pane.
- Updated the focused cockpit shell test to assert the hero copy is gone and evidence remains available in the right pane.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
npm run lint
curl -k -sS -I --max-time 10 https://localhost:3000/coding
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `/coding` returned `200 OK`.

Authority notes:

- No backend behavior changed.
- No Source Proxy route changed.
- No provider/model routing behavior changed.
- No new apply, execute-approved, approval, commit, push, or mobile execution authority was added.
- No secret, `.env`, destructive cleanup, or AionUi integration work occurred.

Remaining visual gap:

- Real desktop/mobile viewport review is still not cleared.
- A screenshot/manual browser pass should verify the flattened panels are readable in the active SpiritOS theme.

Next increment title:
Phase 2.5: Keep Task Composer as the primary action area

## Phase 2.5 Closeout: Composer As Primary Work Surface

Status: implemented.

Scope completed:

- Made the Task Composer the first visible center-column work surface.
- Enlarged the task textarea and promoted the preview action to a full-width primary command.
- Kept `Task status` available as a compact secondary center panel rather than the first thing the operator sees.
- Removed the duplicate Safe Next Action card from the task status panel because the right review pane owns the next safe move.
- Preserved preview, approval, apply, reject, diagnostics, evidence drawer, route/model, and mobile action behavior.
- Updated the focused cockpit shell test to assert the composer safety copy instead of the removed duplicate status-card copy.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
npm run lint
curl -k -sS -I --max-time 10 https://localhost:3000/coding
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `/coding` returned `200 OK`.

Authority notes:

- No backend behavior changed.
- No Source Proxy route changed.
- No provider/model routing behavior changed.
- No new apply, execute-approved, approval, commit, push, or mobile execution authority was added.
- No secret, `.env`, destructive cleanup, or AionUi integration work occurred.

Next increment title:
Phase 2.6: Add project/task list placeholders using existing data only

## Phase 2.6 Closeout: Local Project And Task Placeholders

Status: implemented.

Scope completed:

- Added a `Current task` block to the left rail using only existing in-page state.
- Exposed current task title/state, target, allowed-file count, and expected checks in the rail.
- Marked the rail task summary as `Local state only` so it is not confused with a backend queue contract.
- Kept task queue buckets as local command-center placeholders: Active task, Waiting approval, Blocked, Verified/done, and Recent tasks.
- Preserved the center composer, compact task status header, right review pane, evidence drawer, backend diagnostics link, and shared SpiritOS navigation.
- Updated the cockpit shell test to allow repeated honest empty labels that now appear in both the rail and center workspace.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
npm run lint
curl -k -sS -I --max-time 10 https://localhost:3000/coding
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `/coding` returned `200 OK`.

Authority notes:

- No backend queue, project, workspace, or task-history contract was added.
- No backend behavior changed.
- No Source Proxy route changed.
- No provider/model routing behavior changed.
- No new apply, execute-approved, approval, commit, push, or mobile execution authority was added.
- No secret, `.env`, destructive cleanup, or AionUi integration work occurred.

Next increment title:
Phase 2.7: Add empty states that feel like a coding workspace

## Phase 2.7 Closeout: Workspace Empty States

Status: implemented.

Scope completed:

- Added an idle workspace empty state in the center column for the pre-preview state.
- Included the required v0.1 empty-state cues: No active task, Select or create a task, Preview safely before writes, and Review changes before approval.
- Kept the empty state inside the active workspace area, after the primary composer, so it supports coding work instead of becoming another dashboard stack.
- Preserved the compact Draft, Preview, Approval, Apply, Verify safety loop.
- Preserved the right review pane, collapsed evidence drawer, backend diagnostics link, shared SpiritOS navigation, mobile action bar, and all existing Source Proxy handlers.
- Updated the cockpit shell test to cover the new workspace empty-state labels.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
npm run lint
curl -k -sS -I --max-time 10 https://localhost:3000/coding
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `/coding` returned `200 OK`.

Authority notes:

- No backend behavior changed.
- No Source Proxy route changed.
- No provider/model routing behavior changed.
- No new apply, execute-approved, approval, commit, push, or mobile execution authority was added.
- No secret, `.env`, destructive cleanup, or AionUi integration work occurred.

Next increment title:
Phase 3.1: Verify Draft state renders

## Phase 3: Functionality Preservation

Goal:
Confirm the new shell did not break the Source Proxy task loop.

Small increments:

- 3.1 Verify Draft state renders.
- 3.2 Verify Preview state renders.
- 3.3 Verify Approval gate state renders.
- 3.4 Verify Apply state remains gated.
- 3.5 Verify Verify state remains separate.
- 3.6 Verify blocked/rejected state is clear.
- 3.7 Verify evidence and terminal details remain accessible but collapsed.
- 3.8 Verify route/model/permission information displays without changing routing logic.

Manual checks:

```bash
cd /home/source/SpiritOS
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Expected output:

- Frontend regression passes.
- Cockpit shell test passes.
- Proxy closeout passes.
- No hidden apply.
- No commit.
- No push.
- No source auto-approval.
- No unexpected dirty files.

Next increment title:
Phase 4.1: Real task gauntlet through the new shell

## Phase 3.1 Closeout: Draft State Renders

Status: implemented and verified.

Scope completed:

- Confirmed the initial `/coding` command-center shell renders Draft as the active safety-loop state.
- Confirmed the left rail reports the task queue as `Ready to draft` before a task is scoped.
- Confirmed the task status section keeps the compact Draft, Preview, Approval, Apply, Verify loop visible.
- Confirmed the center workspace shows the idle task state without exposing approval or apply as available actions.
- Tightened the cockpit shell test so Draft state visibility is asserted in both the rail and task status areas.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes from proxy closeout:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- `applied_anything` was false.
- The test run did not change files.
- Dirty files remained limited to `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 3.2: Verify Preview state renders

## Phase 3.2 Closeout: Preview State Renders

Status: implemented and verified.

Scope completed:

- Confirmed the safe preview path renders in the command-center shell after task, target, and allowed files are set.
- Confirmed the compact status loop includes Preview after the mocked safe preview completes.
- Confirmed the task status header moves from Draft to `Needs approval` when preview gates pass.
- Confirmed the left task rail shows an approval queue item after preview.
- Confirmed the diff review panel renders `Preview ready. No files changed yet.`
- Confirmed approval is available only after preview gates pass, while apply and verify remain unavailable.
- Tightened the cockpit shell test to assert Preview state in the status loop, task status header, and rail.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes from proxy closeout:

- No approve occurred during closeout.
- No apply occurred.
- No `execute-approved` occurred.
- `applied_anything` was false.
- The test run did not change files.
- Dirty files remained limited to `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 3.3: Verify Approval gate state renders

## Phase 3.3 Closeout: Approval Gate State Renders

Status: implemented and verified.

Scope completed:

- Confirmed the approval gate state renders after preview gates pass and the operator clicks Approve.
- Confirmed the compact safety loop includes Approval in the approved-but-not-applied state.
- Confirmed the task status header renders `Approved, not applied`.
- Confirmed the UI states that files are still unchanged after approval.
- Confirmed `Apply approved diff` appears only after approval is recorded.
- Confirmed clicking Approve does not call the backend and does not apply anything.
- Tightened the cockpit shell test to assert the approval-gate stop before apply is triggered.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes from proxy closeout:

- No approve occurred during closeout.
- No apply occurred.
- No `execute-approved` occurred.
- `applied_anything` was false.
- The test run did not change files.
- Dirty files remained limited to `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 3.4: Verify Apply state remains gated

## Phase 3.4 Closeout: Apply State Remains Gated

Status: implemented and verified.

Scope completed:

- Confirmed apply is not visible after preview alone.
- Confirmed apply is not visible before human approval is recorded.
- Confirmed clicking Approve does not call `/v1/actions/execute-approved`.
- Confirmed `Apply approved diff` appears only after the approved-but-not-applied gate is reached.
- Confirmed the mocked apply path calls `/v1/actions/execute-approved` only after the explicit `Apply approved diff` button is clicked.
- Confirmed verify remains unavailable immediately after apply in the current shell.
- Tightened the cockpit shell test to assert no execute-approved call occurs before the explicit apply action.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes from proxy closeout:

- No approve occurred during closeout.
- No apply occurred.
- No `execute-approved` occurred.
- `applied_anything` was false.
- The test run did not change files.
- Dirty files remained limited to `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 3.5: Verify Verify state remains separate

## Phase 3.5 Closeout: Verify State Remains Separate

Status: implemented and verified.

Scope completed:

- Confirmed the mocked apply path reaches `Applied, verification required`.
- Confirmed the compact safety loop includes Verify after the applied state is reached.
- Confirmed the task status header renders `Applied, verification required`.
- Confirmed the task rail moves the done bucket to `Verify next`.
- Confirmed the verification gate tells the operator that verification is required before treating the task as done.
- Confirmed no standalone Verify action button is exposed immediately after apply in the current shell.
- Tightened the cockpit shell test to assert Verify is a separate post-apply state, not folded into apply.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes from proxy closeout:

- No approve occurred during closeout.
- No apply occurred.
- No `execute-approved` occurred.
- `applied_anything` was false.
- The test run did not change files.
- Dirty files remained limited to `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 3.6: Verify blocked/rejected state is clear

## Phase 3.6 Closeout: Blocked And Rejected States Are Clear

Status: implemented and verified.

Scope completed:

- Confirmed backend-blocked preview renders `Preview blocked. No files changed.`
- Confirmed backend blocker text appears in the command-center shell.
- Confirmed backend-blocked state moves the task status header to `Blocked`.
- Confirmed backend-blocked state marks the left rail `Blocked` bucket with `1 task`.
- Confirmed human Reject after preview renders `Rejected by human reviewer. No files changed.`
- Confirmed rejected state moves the task status header to `Blocked`.
- Confirmed rejected state marks the left rail `Blocked` bucket with `1 task`.
- Confirmed approval and apply controls are unavailable in blocked and rejected states.
- Tightened the cockpit shell test to assert blocked/rejected state clarity in the command-center shell.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes from proxy closeout:

- No approve occurred during closeout.
- No apply occurred.
- No `execute-approved` occurred.
- `applied_anything` was false.
- The test run did not change files.
- Dirty files remained limited to `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 3.7: Verify evidence and terminal details remain accessible but collapsed

## Phase 3.7 Closeout: Evidence And Terminal Details Stay Collapsed

Status: implemented and verified.

Scope completed:

- Confirmed the `Evidence trail and logs` drawer remains accessible in the right review pane.
- Confirmed the evidence drawer is collapsed by default by asserting the backing `details` element has no `open` attribute.
- Confirmed role evidence remains available inside the drawer: Architect, Coder, Reviewer, Verifier, Approval Gate, and Apply Result.
- Confirmed terminal/test evidence remains accessible inside the drawer without becoming a default page panel.
- Confirmed raw debug JSON and replayable logs remain absent from the default `/coding` view.
- Tightened the cockpit shell test to distinguish accessible drawer content from default-open clutter.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes from proxy closeout:

- No approve occurred during closeout.
- No apply occurred.
- No `execute-approved` occurred.
- `applied_anything` was false.
- The test run did not change files.
- Dirty files remained limited to `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 3.8: Verify route/model/permission information displays without changing routing logic

## Phase 3.8 Closeout: Route Model And Permission Context Stay Honest

Status: implemented and verified.

Scope completed:

- Confirmed the compact task status area displays Proxy, Route, and Workspace context.
- Confirmed the default route/model selector displays `Source Proxy default`.
- Confirmed the route/model selector exposes the existing choices: Source Proxy default, Local planning only, and Codex proposal route.
- Confirmed allowed-file permission/scope remains visible in the local task rail without implying a backend queue or new authority.
- Confirmed a selected route/model value is passed only through the existing safe preview verification payload as `route_type`.
- Confirmed no provider routing behavior, backend authority, approval, apply, execute-approved, commit, or push behavior changed.
- Tightened the cockpit shell test to assert route/model context display and payload honesty.

Files changed:

- `docs/codingUI.md`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npm run lint
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `git diff --check` had no output.
- `npm run typecheck` passed.
- `npm run lint` passed with the existing 7 warnings and 0 errors.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes from proxy closeout:

- No approve occurred during closeout.
- No apply occurred.
- No `execute-approved` occurred.
- `applied_anything` was false.
- The test run did not change files.
- Dirty files remained limited to `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 4.1: Write the gauntlet checklist in docs/codingUI.md

## Phase 4: Real Task Gauntlet

Goal:
Prove the new UI works for real coding tasks before final polish.

Required task gauntlet:

- A. Docs-only task.
- B. Small UI copy task.
- C. Allowed component edit.
- D. Protected path rejection.
- E. Bad diff rejection.
- F. Verify-after-apply path.
- G. Local model route display.
- H. Cloud/Codex route display if already supported.
- I. Manual handoff route display if already supported.

Gauntlet checklist:

| ID | Path | Operator input | Required UI proof | Safety stop |
| --- | --- | --- | --- | --- |
| A | Docs-only task | Task targets a single docs file such as `docs/codingUI.md`; allowed files contains only that same docs path; expected checks include `git diff --check`. | Composer enables Preview safely, review pane shows changed files only inside the allowed docs path, evidence drawer remains collapsed but accessible, no apply appears before approval. | Stop before approval/apply unless the operator explicitly approves a later verify-after-apply path. |
| B | Small UI copy task | Task targets a known UI copy string in an allowed component file; allowed files contains only that component path; expected checks include `npm run typecheck` and cockpit shell test if relevant. | Review pane shows a small diff summary, task status reaches Preview/Needs approval, route/model/permission strip remains visible and honest. | Reject if diff touches files outside the allowed component or changes behavior instead of copy. |
| C | Allowed component edit | Task targets one approved component file; allowed files is the same file or a deliberately tiny set; expected checks include typecheck and the focused component test. | Changed files list stays inside allowed files, approval gate explains target match and allowed-file pass, apply remains hidden until approval. | Stop if route/model choice implies new backend authority or if changed files exceed the allowed list. |
| D | Protected path rejection | Task targets `.env`, secrets, config secrets, or another protected path. | Composer or preview clearly blocks the task, blocked rail bucket shows the blocked state, approval and apply controls remain unavailable. | No preview/apply attempt against protected paths; no secret or `.env` edits. |
| E | Bad diff rejection | Use a preview response or dry-run case where the proposed diff touches the wrong file, protected path, malformed diff, or misses the stated target. | Review pane and gates show the blocker, task status is Blocked, safe next move is revise/reject, evidence remains accessible. | Reject; do not approve or apply bad diff. |
| F | Verify-after-apply path | Only after normal preview and approval gates are explicitly approved by the operator for a bounded safe test. | Apply remains unavailable until approval; after apply, status becomes Applied, verification required; Verify remains a separate next step. | Do not run unless the operator explicitly approves the apply step for that exact bounded task. |
| G | Local model route display | Select the local/planning route option only if already supported by the existing UI/contract. | Route/model selector and preview payload display the selected route honestly; no provider routing behavior changes. | If the route is unsupported or unavailable, record the blocker instead of adding routing logic. |
| H | Cloud/Codex route display | Select the Codex/cloud route option only if already supported by the existing UI/contract. | Route/model selector displays the route, preview evidence says what happened, blocked/config-unavailable states are visible when applicable. | Do not add Codex trust, provider fallback, or new routing behavior. |
| I | Manual handoff route display | Use only if an existing manual handoff route/state is already supported. | UI labels the route/state honestly and keeps Source Proxy gates separate from manual instructions. | If unsupported, mark as not supported in v0.1; do not add a bridge or handoff authority. |

Gauntlet pass criteria:

- `/coding` remains the everyday command center and `/proxy-backend` remains the diagnostics surface.
- Draft, Preview, Approval, Apply, and Verify stay separate in both UI copy and available actions.
- Approval never means apply, apply never means verify, and verify never implies commit or push.
- Changed files, target, allowed files, blocker, reviewer/verifier result, and next safe move are visible or accessible in the command-center shell.
- Terminal/evidence/log detail remains collapsed unless opened or unless a future failed-state rule explicitly opens it.
- Route/model/permission display is honest and uses only existing contracts.
- Dry-run paths produce no unexpected mutation.
- No commit, push, hidden write, execute-approved, autopilot, provider routing change, AionUi integration, secret edit, or destructive cleanup occurs.

Gauntlet result log template:

```text
Path:
Date:
Operator:
Task:
Target:
Allowed files:
Route/model shown:
Expected checks:
Observed state:
Changed files shown:
Approval available:
Apply available:
Verify shown separately:
Evidence/logs collapsed by default:
Result:
Blockers:
Unexpected mutations:
Next safe action:
```

Small increments:

- 4.1 Write the gauntlet checklist in `docs/codingUI.md`.
- 4.2 Run docs-only dry-run path.
- 4.3 Run allowed component dry-run path.
- 4.4 Run protected path rejection path.
- 4.5 Run bad diff rejection path.
- 4.6 Run verify-after-apply path only if normal approval/apply gates are explicitly approved by the operator.
- 4.7 Record results and blockers.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Expected output:

- All dry-run safety paths pass.
- Blocked paths are visibly blocked.
- Route/model/permission display is honest.
- No unexpected mutation.
- No commit or push.

Next increment title:
Phase 5.1: Browser and mobile viewport review

## Phase 4.1 Closeout: Real Task Gauntlet Checklist

Status: implemented.

Scope completed:

- Added an operator-facing gauntlet checklist for paths A through I.
- Defined inputs, required UI proof, and safety stop conditions for each gauntlet path.
- Added pass criteria that preserve Draft, Preview, Approval, Apply, and Verify as separate states.
- Added explicit dry-run and no-mutation expectations.
- Added a result log template for recording each gauntlet run.
- Kept this increment docs-only; no UI code, backend code, route behavior, provider logic, approval/apply behavior, or authority changed.

Files changed:

- `docs/codingUI.md`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check -- docs/codingUI.md
grep -n "Gauntlet checklist" docs/codingUI.md
grep -n "Gauntlet pass criteria" docs/codingUI.md
grep -n "Gauntlet result log template" docs/codingUI.md
git status --branch --short
```

Observed output:

- `git diff --check -- docs/codingUI.md` had no output.
- `Gauntlet checklist` exists in `docs/codingUI.md`.
- `Gauntlet pass criteria` exists in `docs/codingUI.md`.
- `Gauntlet result log template` exists in `docs/codingUI.md`.
- Dirty files remain limited to the current command-center work: `docs/codingUI.md`, `src/components/coding/CodingCockpitShell.tsx`, and `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Authority notes:

- No backend behavior changed.
- No Source Proxy route changed.
- No provider/model routing behavior changed.
- No approval, apply, execute-approved, commit, push, autopilot, mobile execution, secret edit, destructive cleanup, or AionUi integration work occurred.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 4.2: Run docs-only dry-run path

## Phase 4.2 Closeout: Docs-Only Dry-Run Path

Status: implemented and verified.

Scope completed:

- Ran a docs-only dry-run preview against `docs/phase-8-manual-check.md`.
- Used the existing `/v1/verification/diff-preview` contract with a handcrafted docs-only unified diff.
- Kept target and allowed files limited to `docs/phase-8-manual-check.md`.
- Confirmed the preview result was `preview_ready`.
- Confirmed changed files were limited to `docs/phase-8-manual-check.md`.
- Confirmed `git_apply_check_ok` was `true`.
- Confirmed `task_spec_check.ok` was `true`.
- Confirmed `would_apply_diff` was `false`.
- Confirmed `would_execute` was `false`.
- Stopped before approval/apply.

Gauntlet result log:

```text
Path: A. Docs-only task
Date: 2026-05-20
Operator: Codex
Task: Docs-only dry-run preview for Source Proxy command center gauntlet.
Target: docs/phase-8-manual-check.md
Allowed files: docs/phase-8-manual-check.md
Route/model shown: source-proxy-default
Expected checks: git diff --check
Observed state: preview_ready
Changed files shown: docs/phase-8-manual-check.md
Approval available: not exercised
Apply available: no
Verify shown separately: not exercised
Evidence/logs collapsed by default: previously verified in Phase 3.7
Result: PASS
Blockers: none
Unexpected mutations: none
Next safe action: continue to allowed component dry-run path
```

Manual checks run:

```bash
cd /home/source/SpiritOS
curl -k -sS --max-time 20 -X POST https://localhost:3000/v1/verification/diff-preview ...
git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- Docs-only dry-run returned `preview_ready`.
- Dry-run changed files were limited to `docs/phase-8-manual-check.md`.
- Dry-run returned `would_apply_diff: false`.
- Dry-run returned `would_execute: false`.
- `git status --branch --short` remained limited to the current command-center dirty files.
- `git diff --check` had no output.
- `global-safety-regression` passed.
- `proxy-closeout` passed.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No source auto-approval occurred.
- No unexpected mutation occurred.
- HEAD did not change.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 4.3: Run allowed component dry-run path

## Phase 4.3 Closeout: Allowed Component Dry-Run Path

Status: implemented and verified.

Scope completed:

- Ran an allowed component dry-run preview against `src/components/coding/CodingCockpitShell.tsx`.
- Used the existing `/v1/verification/diff-preview` contract with a handcrafted copy-only TSX diff.
- Kept target and allowed files limited to `src/components/coding/CodingCockpitShell.tsx`.
- Confirmed the preview result was `preview_ready`.
- Confirmed changed files were limited to `src/components/coding/CodingCockpitShell.tsx`.
- Confirmed `git_apply_check_ok` was `true`.
- Confirmed `task_spec_check.ok` was `true`.
- Confirmed `would_apply_diff` was `false`.
- Confirmed `would_execute` was `false`.
- Stopped before approval/apply.

Gauntlet result log:

```text
Path: C. Allowed component edit
Date: 2026-05-20
Operator: Codex
Task: Allowed component dry-run preview for Source Proxy command center gauntlet.
Target: src/components/coding/CodingCockpitShell.tsx
Allowed files: src/components/coding/CodingCockpitShell.tsx
Route/model shown: source-proxy-default
Expected checks: npm run typecheck; CI=1 npm run test -- coding-cockpit-shell
Observed state: preview_ready
Changed files shown: src/components/coding/CodingCockpitShell.tsx
Approval available: not exercised
Apply available: no
Verify shown separately: not exercised
Evidence/logs collapsed by default: previously verified in Phase 3.7
Result: PASS
Blockers: none
Unexpected mutations: none
Next safe action: continue to protected path rejection path
```

Manual checks run:

```bash
cd /home/source/SpiritOS
curl -k -sS --max-time 20 -X POST https://localhost:3000/v1/verification/diff-preview ...
git status --branch --short
git diff --check
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- Allowed component dry-run returned `preview_ready`.
- Dry-run changed files were limited to `src/components/coding/CodingCockpitShell.tsx`.
- Dry-run returned `would_apply_diff: false`.
- Dry-run returned `would_execute: false`.
- `git status --branch --short` remained limited to the current command-center dirty files.
- `git diff --check` had no output.
- `npm run typecheck` passed.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No unexpected mutation occurred.
- HEAD did not change.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 4.4: Run protected path rejection path

## Phase 4.4 Closeout: Protected Path Rejection Path

Status: implemented and verified.

Scope completed:

- Ran a protected-path rejection dry-run against `.env.local`.
- Used the existing `/v1/verification/diff-preview` contract with a handcrafted secret-shaped diff.
- Confirmed the preview result was `blocked`.
- Confirmed blocker reasons included `secret_shaped_path` and `protected_path`.
- Confirmed `limits.file_writes_allowed` was `false`.
- Confirmed `limits.terminal_execution_allowed` was `false`.
- Confirmed `limits.secret_shaped_paths_allowed` was `false`.
- Confirmed `would_apply_diff` was `false`.
- Confirmed `would_execute` was `false`.
- Stopped before approval/apply.

Gauntlet result log:

```text
Path: D. Protected path rejection
Date: 2026-05-20
Operator: Codex
Task: Protected path rejection gauntlet.
Target: .env.local
Allowed files: .env.local
Route/model shown: source-proxy-default
Expected checks: git diff --check
Observed state: blocked
Changed files shown: .env.local
Approval available: no
Apply available: no
Verify shown separately: not exercised
Evidence/logs collapsed by default: previously verified in Phase 3.7
Result: PASS
Blockers: secret_shaped_path; protected_path; diff_apply_check_failed
Unexpected mutations: none
Next safe action: continue to bad diff rejection path
```

Manual checks run:

```bash
cd /home/source/SpiritOS
curl -k -sS --max-time 20 -X POST https://localhost:3000/v1/verification/diff-preview ...
git status --branch --short
git diff --check
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- Protected path dry-run returned `blocked`.
- Blocker reasons included `secret_shaped_path` and `protected_path`.
- Dry-run returned `would_apply_diff: false`.
- Dry-run returned `would_execute: false`.
- `file_writes_allowed` was `false`.
- `terminal_execution_allowed` was `false`.
- `git status --branch --short` remained limited to the current command-center dirty files.
- `git diff --check` had no output.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No secret or `.env` edit occurred.
- No unexpected mutation occurred.
- HEAD did not change.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 4.5: Run bad diff rejection path

## Phase 4.5 Closeout: Bad Diff Rejection Path

Status: implemented and verified.

Scope completed:

- Ran a bad-diff rejection dry-run where the task target was `docs/phase-8-manual-check.md` but the diff touched `package.json`.
- Used the existing `/v1/verification/diff-preview` contract with a handcrafted wrong-file diff.
- Confirmed the preview result was `blocked`.
- Confirmed `task_spec_check.ok` was `false`.
- Confirmed reason codes included `task_spec_allowed_file_violation` and `task_spec_target_mismatch`.
- Confirmed blocker reasons included `task_spec_allowed_file_violation`, `task_spec_target_mismatch`, and `requirement_coverage_failed`.
- Confirmed `limits.file_writes_allowed` was `false`.
- Confirmed `limits.terminal_execution_allowed` was `false`.
- Confirmed `would_apply_diff` was `false`.
- Confirmed `would_execute` was `false`.
- Stopped before approval/apply.

Gauntlet result log:

```text
Path: E. Bad diff rejection
Date: 2026-05-20
Operator: Codex
Task: Bad diff rejection gauntlet.
Target: docs/phase-8-manual-check.md
Allowed files: docs/phase-8-manual-check.md
Route/model shown: source-proxy-default
Expected checks: git diff --check
Observed state: blocked
Changed files shown: package.json
Approval available: no
Apply available: no
Verify shown separately: not exercised
Evidence/logs collapsed by default: previously verified in Phase 3.7
Result: PASS
Blockers: task_spec_allowed_file_violation; task_spec_target_mismatch; requirement_coverage_failed
Unexpected mutations: none
Next safe action: continue to verify-after-apply path only if explicitly approved by the operator
```

Manual checks run:

```bash
cd /home/source/SpiritOS
curl -k -sS --max-time 20 -X POST https://localhost:3000/v1/verification/diff-preview ...
git status --branch --short
git diff --check
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- Bad diff dry-run returned `blocked`.
- Changed files showed `package.json`, outside allowed files.
- Dry-run returned `would_apply_diff: false`.
- Dry-run returned `would_execute: false`.
- `file_writes_allowed` was `false`.
- `terminal_execution_allowed` was `false`.
- `git status --branch --short` remained limited to the current command-center dirty files.
- `git diff --check` had no output.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No unexpected mutation occurred.
- HEAD did not change.

Remaining known issues:

- The same 7 lint warnings remain.
- Browser screenshot and real viewport review are still not cleared.
- Working tree is intentionally dirty for the current uncommitted command-center changes.

Next increment title:
Phase 4.6: Run verify-after-apply path only if explicitly approved by the operator

## Phase 4.6 Preflight: Verify-After-Apply Requires Explicit Approval

Status: blocked pending explicit operator approval.

Scope completed:

- Confirmed the previous checks are green enough to reach Phase 4.6.
- Confirmed this increment is the first gauntlet path that may require an actual approved apply.
- Did not treat "go next" as approval to approve or apply a diff.
- Did not run approval, apply, execute-approved, commit, push, or destructive cleanup.

Required operator approval before continuing:

```text
I explicitly approve running the bounded Phase 4.6 verify-after-apply path.
Target:
Allowed files:
Expected diff/task:
Expected checks:
```

Manual checks run:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
grep -n "Phase 4.6\\|verify-after-apply" docs/codingUI.md
```

Observed output:

- Dirty files remain limited to the current command-center work.
- `git diff --check` had no output.
- Phase 4.6 is documented as requiring explicit operator approval.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No unexpected mutation occurred.

Next increment title:
Phase 4.6: Await explicit operator approval or skip verify-after-apply path

## Phase 4.6 Closeout: Verify-After-Apply Skipped Without Approval

Status: skipped.

Reason:

- The operator asked to continue, but did not explicitly approve a bounded apply.
- Phase 4.6 is the only gauntlet path that can require an actual approved apply.
- Source Proxy safety requires explicit approval for the exact target, allowed files, expected diff/task, and expected checks before running this path.

Result:

- Verify-after-apply was not run.
- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No unexpected mutation occurred.

Next safe action:

- Continue to Phase 4.7 and record results/blockers.
- Return to Phase 4.6 later only with explicit operator approval for a bounded apply.

## Phase 4.7 Closeout: Gauntlet Results And Blockers

Status: implemented.

Gauntlet summary:

| Path | Result | Notes |
| --- | --- | --- |
| A. Docs-only task | PASS | Preview-ready dry-run against `docs/phase-8-manual-check.md`; no apply or execute. |
| B. Small UI copy task | Covered by C for v0.1 | The allowed component dry-run used a copy-only TSX diff. |
| C. Allowed component edit | PASS | Preview-ready dry-run against `src/components/coding/CodingCockpitShell.tsx`; no apply or execute. |
| D. Protected path rejection | PASS | `.env.local` dry-run blocked with protected/secret-shaped reasons. |
| E. Bad diff rejection | PASS | Wrong-file `package.json` diff blocked against docs target/allowed files. |
| F. Verify-after-apply path | SKIPPED | Requires explicit operator approval for a bounded apply. |
| G. Local model route display | Verified in Phase 3.8 | Route/model display and payload honesty verified without changing routing logic. |
| H. Cloud/Codex route display | Verified as existing selector only | No Codex trust, provider fallback, or routing behavior was added. |
| I. Manual handoff route display | Not supported in v0.1 | No manual handoff bridge or new authority was added. |

Phase 4 pass criteria:

- Dry-run safety paths passed without unexpected mutation.
- Blocked paths were visibly blocked by the verification contract.
- Route/model/permission display was verified without routing behavior changes.
- No commit or push occurred.
- No hidden write, autopilot, provider routing change, AionUi integration, secret edit, or destructive cleanup occurred.
- Verify-after-apply remains blocked until explicit operator approval.

Remaining blockers:

- Phase 4.6 verify-after-apply is intentionally skipped without explicit approval.
- Browser screenshot and real viewport review are still not cleared.
- The same 7 lint warnings remain.
- Working tree is intentionally dirty for current command-center changes.

Next increment title:
Phase 5.1: Check whether Playwright is available in this repo

## Phase 5: Browser and Mobile Review

Goal:
Clear the visual/viewport gap that the closeout could not prove.

Small increments:

- 5.1 Check whether Playwright is available in this repo.
- 5.2 If available, add or run screenshot checks for `/coding` desktop.
- 5.3 Add or run iPhone-sized viewport check.
- 5.4 Add or run Android-sized viewport check.
- 5.5 If Playwright is not available, write manual browser screenshot checklist instead.
- 5.6 Confirm Codex mobile or phone browser review is usable for monitoring and approval review only, not new mobile authority.

Manual checks:

```bash
cd /home/source/SpiritOS
npm run test -- --help | head -40
npx playwright --version || true
ls -la playwright.config.* || true
curl -k -sS -I https://localhost:3000/coding
```

Expected output:

- If Playwright exists, screenshot/viewport checks run.
- If Playwright does not exist, docs clearly state manual visual review required.
- Do not claim viewport cleared unless it was actually cleared.

Next increment title:
Phase 6.1: Bug cleanup before final polish

## Phase 5.1 Closeout: Playwright Availability Check

Status: partially available, viewport review still blocked.

Findings:

- `playwright.config.mjs` exists.
- `tests/e2e/coding-ui.spec.mjs` exists.
- `npx playwright --version` reported `Version 1.60.0`.
- `npm run test -- --help` shows the repo test script is Vitest, not Playwright.
- `package.json` does not currently expose a Playwright/e2e script or direct `@playwright/test` dependency.
- `npx playwright test --list` failed because `@playwright/test` could not be resolved from the project.
- No local Chromium/headless-shell browser binary was found in `~/.cache/ms-playwright`.
- `npx playwright install --dry-run chromium` showed the browser download/install locations, but no browser install was performed.
- Existing e2e expectations are stale relative to the new command-center shell because they still reference old navigation/diagnostics text.

Result:

- Do not claim browser or viewport review is cleared.
- Playwright config/spec scaffolding exists, but the repo is not currently ready to run the `/coding` viewport checks without dependency/browser setup and e2e spec cleanup.

Manual checks run:

```bash
cd /home/source/SpiritOS
npm run test -- --help | head -40
npx playwright --version || true
ls -la playwright.config.* 2>/dev/null || true
grep -n "playwright\\|@playwright" package.json package-lock.json 2>/dev/null | head -40
npx playwright install --dry-run chromium 2>&1 | head -80
find ~/.cache/ms-playwright -maxdepth 2 -type f -name chrome -o -name chromium -o -name headless_shell 2>/dev/null | head -20
npx playwright test --list
git diff --check
```

Observed output:

- Vitest help printed successfully.
- Playwright CLI reported `Version 1.60.0`.
- `playwright.config.mjs` exists.
- `tests/e2e/coding-ui.spec.mjs` exists.
- `npx playwright test --list` failed with `ERR_MODULE_NOT_FOUND` for `@playwright/test`.
- Browser cache search returned no local browser binary.
- `git diff --check` had no output.

Safety notes:

- No dependency install occurred.
- No browser install occurred.
- No screenshot or viewport result was claimed.
- No backend behavior changed.
- No approval, apply, execute-approved, commit, push, destructive cleanup, secret edit, or AionUi integration occurred.

Next increment title:
Phase 5.5: Write manual browser screenshot checklist and Playwright readiness notes

## Phase 5.5 Closeout: Manual Browser Checklist And Playwright Readiness Notes

Status: implemented as documentation.

Why manual review is required:

- Playwright config and e2e specs exist, but `@playwright/test` is not currently resolvable from the project.
- No local Chromium/headless-shell browser binary was found.
- Existing Playwright expectations are stale relative to the new command-center shell.
- Therefore, browser and viewport review is not cleared and must not be reported as passed.

Manual browser screenshot checklist:

```text
Route: /coding
Server: https://localhost:3000
Reviewer:
Date:

Desktop viewport:
- width/height:
- SpiritOS navigation visible and Source active:
- hero/explainer heading absent:
- left rail visible or sensibly stacked:
- composer is primary work surface:
- task status is compact:
- right review pane visible or stacked below without overlap:
- evidence/log drawer collapsed by default:
- /proxy-backend diagnostics link visible:
- no apply/approval ambiguity:
- text readable:
- widget borders clean:
- no incoherent overlap:
- result:

iPhone-sized viewport:
- width/height:
- mobile nav/action bar visible:
- composer usable:
- Preview disabled until required fields are set:
- diagnostics available for review only:
- no mobile-only apply/execute authority:
- text readable:
- no horizontal overflow:
- no incoherent overlap:
- result:

Android-sized viewport:
- width/height:
- mobile nav/action bar visible:
- composer usable:
- Preview disabled until required fields are set:
- diagnostics available for review only:
- no mobile-only apply/execute authority:
- text readable:
- no horizontal overflow:
- no incoherent overlap:
- result:

Screenshots captured:
- desktop:
- iPhone:
- Android:

Blockers:
Next safe action:
```

Playwright readiness notes:

- Add or restore a project-resolvable `@playwright/test` dependency before running e2e tests.
- Install the required browser binaries only when dependency setup is approved.
- Update `tests/e2e/coding-ui.spec.mjs` for the new command-center shell:
  - shared SpiritOS navigation, not the old route nav label.
  - no `Advanced diagnostics` hero link expectation.
  - `Backend diagnostics` link in the review pane.
  - left rail, center composer, right review pane.
  - collapsed `Evidence trail and logs` drawer.
  - no apply button before approval.
  - no commit/push controls.
- Run desktop, iPhone, and Android/Pixel projects only after the above is fixed.
- Do not claim viewport review cleared until screenshots or e2e browser runs actually pass.

Mobile authority note:

- Phone/mobile review is allowed for monitoring, reading evidence, and approval review only.
- No new mobile execution authority is granted.
- Mobile UI must not bypass Draft, Preview, Approval, Apply, or Verify.

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
grep -n "Manual browser screenshot checklist" docs/codingUI.md
grep -n "Playwright readiness notes" docs/codingUI.md
grep -n "Mobile authority note" docs/codingUI.md
```

Observed output:

- Manual screenshot checklist is documented.
- Playwright readiness notes are documented.
- Mobile authority note is documented.
- Viewport review remains blocked until manual screenshots or working Playwright runs exist.

Next increment title:
Phase 6.1: Categorize warnings into must-fix-now vs later refactor

## Phase 6: Bug Cleanup Before Final UI Polish

Goal:
Fix warnings and reliability issues before making it pretty.

Known cleanup targets:

- 7 lint warnings from latest closeout.
- React `act(...)` warning in tests.
- `CodingAgentInterface.tsx` is over 500KB and likely needs later component extraction.
- Any new command-center layout regressions.
- Any missing route/model/permission honesty.
- Any viewport issues.

Small increments:

- 6.1 Categorize warnings into must-fix-now vs later refactor.
- 6.2 Fix low-risk unused variables/imports.
- 6.3 Fix or document React `act(...)` warnings.
- 6.4 Decide whether `CodingAgentInterface.tsx` extraction is required now or deferred.
- 6.5 Rerun frontend regression and proxy closeout.

Manual checks:

```bash
cd /home/source/SpiritOS
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Expected output:

- Lint has fewer warnings, ideally 0 errors and fewer than current 7 warnings.
- Typecheck passes.
- Frontend regression passes.
- Proxy closeout passes.
- No unexpected mutations.

Next increment title:
Phase 7.1: Final visual polish only after functionality is intact

## Phase 6.1 Closeout: Warning Triage Before Polish

Status: implemented as triage.

Current lint baseline:

- 0 errors.
- 7 warnings.
- Babel deoptimization note for `src/components/coding/CodingAgentInterface.tsx` because the file exceeds 500KB.

Warning categories:

| File | Warning | Category | Decision |
| --- | --- | --- | --- |
| `src/app/v1/cartographer/audit-trail/route.ts` | unused `result` | Low-risk cleanup, but outside `/coding` command-center lane | Defer unless doing Cartographer cleanup. |
| `src/components/coding/CodingAgentInterface.tsx` | unused `WorkflowProgressCopy` import | Low-risk cleanup candidate | Candidate for Phase 6.2 if no behavior coupling is found. |
| `src/components/coding/CodingAgentInterface.tsx` | missing `previewDiffVerification` dependency | Shared hook behavior risk in large legacy file | Do not quick-fix blindly; investigate before changing. |
| `src/components/coding/CodingAgentInterface.tsx` | missing `approvalGate`, `diffVerification`, `longRunningTask`, `proxySafetySmoke` dependencies | Shared hook behavior risk in large legacy file | Do not quick-fix blindly; investigate before changing. |
| `src/components/coding/CodingAgentInterface.tsx` | unused `current` | Low-risk cleanup candidate | Candidate for Phase 6.2 if local scope is clear. |
| `src/components/coding/CodingAgentInterface.tsx` | unused `onPreviewManualResult` | Medium risk because it may be part of a public/internal component interface | Investigate before removing. |
| `src/components/dashboard/HomelabBlueprintReviewWidget.tsx` | unused `pendingProposalCount` | Low-risk cleanup, outside `/coding` command-center lane | Defer unless doing dashboard cleanup. |

Reliability categories:

| Issue | Category | Decision |
| --- | --- | --- |
| React `act(...)` warning in `coding-workflow-step` regression | Test reliability cleanup | Document in Phase 6.3; fix if localized and low-risk. |
| `CodingAgentInterface.tsx` over 500KB | Refactor/maintainability issue | Defer broad extraction until after v0.1 command-center shell is stable. |
| Playwright/e2e not runnable | Viewport validation blocker | Keep as Phase 5 blocker; do not claim viewport cleared. |
| Existing e2e spec stale | Test maintenance blocker | Update only after Playwright dependency/browser setup is approved. |

Must-fix-now:

- New command-center regressions.
- Typecheck failures.
- Lint errors.
- Any warning caused by current command-center edits.
- Any route/model/permission honesty issue.
- Any safety ambiguity between approval, apply, verify, commit, or push.

Defer:

- Broad `CodingAgentInterface.tsx` extraction.
- Hook dependency changes in the 500KB legacy file without focused investigation.
- Non-`/coding` unused variables unless explicitly entering that lane.
- Playwright browser installation or dependency changes without approval.

Manual checks run:

```bash
cd /home/source/SpiritOS
npm run lint
git status --branch --short
```

Observed output:

- `npm run lint` passed with 7 warnings and 0 errors.
- Dirty files remain limited to the current command-center work.

Next increment title:
Phase 6.2: Fix low-risk unused variables/imports

## Phase 6.2 Closeout: Low-Risk Unused Cleanup

Status: implemented and verified.

Scope completed:

- Removed the unused `WorkflowProgressCopy` type import from `src/components/coding/CodingAgentInterface.tsx`.
- Removed the unused `current` setter argument in a local `setLongRunningTask` call.
- Removed unused destructuring of `onPreviewManualResult` while preserving the component prop contract.
- Left hook dependency warnings untouched because they require focused behavior investigation.
- Left non-`/coding` warnings untouched.
- Did not perform broad `CodingAgentInterface.tsx` extraction.

Observed lint improvement:

- Before: 7 warnings, 0 errors.
- After: 4 warnings, 0 errors.

Remaining warnings:

- `src/app/v1/cartographer/audit-trail/route.ts`: unused `result`.
- `src/components/coding/CodingAgentInterface.tsx`: two hook dependency warnings.
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`: unused `pendingProposalCount`.

Manual checks run:

```bash
cd /home/source/SpiritOS
npm run lint
npm run typecheck
git diff --check
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `npm run lint` passed with 4 warnings and 0 errors.
- `npm run typecheck` passed.
- `git diff --check` had no output.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No backend behavior changed.
- No route/model/provider behavior changed.

Next increment title:
Phase 6.3: Fix or document React act warnings

## Phase 6.3 Closeout: React Act Warning Fixed

Status: implemented and verified.

Scope completed:

- Fixed the localized React `act(...)` warning in `src/components/coding/__tests__/coding-workflow-step.test.ts`.
- Imported `act` from `@testing-library/react`.
- Wrapped the fake timer advance in the browser-autofill sync test with `await act(async () => ...)`.
- Did not change production behavior.
- Did not broaden test scope or alter Source Proxy authority.

Manual checks run:

```bash
cd /home/source/SpiritOS
npm run test:coding-frontend-regression
npm run lint
npm run typecheck
git diff --check
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- The previous React `act(...)` stderr did not appear in the regression output.
- `npm run lint` passed with 4 warnings and 0 errors.
- `npm run typecheck` passed.
- `git diff --check` had no output.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No backend behavior changed.
- No route/model/provider behavior changed.

Next increment title:
Phase 6.4: Decide whether CodingAgentInterface.tsx extraction is required now or deferred

## Phase 6.4 Closeout: CodingAgentInterface Extraction Deferred

Status: deferred.

Decision:

- Do not extract `src/components/coding/CodingAgentInterface.tsx` during Source Proxy Command Center v0.1.

Reason:

- The file is over 500KB and still produces the Babel deoptimization note.
- It contains legacy Source Proxy surfaces, hook state, approval/apply logic, diagnostics, task history, and regression-covered behavior.
- Broad extraction now would add risk after the command-center shell and functionality preservation work has already stabilized.
- The v0.1 goal is command-center UX, functionality confirmation, bug cleanup, and then visual polish; broad component extraction belongs in a later hardening/refactor lane.

Allowed later extraction criteria:

- Dedicated refactor increment.
- Component ownership map.
- Focused tests before and after each extraction.
- No authority changes.
- No approval/apply/verify behavior changes.
- No provider/model routing changes.

Manual checks accepted from operator run:

```bash
cd /home/source/SpiritOS
npm run test:coding-frontend-regression
npm run lint
npm run typecheck
git diff --check
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Observed output:

- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `npm run lint` passed with 4 warnings and 0 errors.
- `npm run typecheck` passed.
- `git diff --check` had no output.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.

Next increment title:
Phase 6.5: Rerun frontend regression and proxy closeout

## Phase 6.5 Closeout: Bug Cleanup Verification

Status: implemented and verified from operator run.

Scope completed:

- Confirmed low-risk cleanup did not break frontend regression.
- Confirmed React `act(...)` warning no longer appeared in the frontend regression output.
- Confirmed lint remains at 4 warnings and 0 errors.
- Confirmed typecheck passes.
- Confirmed cockpit shell tests pass.
- Confirmed proxy closeout passes.
- Confirmed no approve, apply, execute-approved, commit, push, or unexpected mutation occurred.

Remaining warnings:

- `src/app/v1/cartographer/audit-trail/route.ts`: unused `result`.
- `src/components/coding/CodingAgentInterface.tsx`: two hook dependency warnings.
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`: unused `pendingProposalCount`.

Remaining blockers before claiming final polish complete:

- Browser screenshot and real viewport review are still not cleared.
- Playwright/e2e remains blocked by missing project-resolved `@playwright/test`, missing browser binary, and stale e2e expectations.
- `CodingAgentInterface.tsx` extraction is deferred.

Next increment title:
Phase 7.1: Final visual polish only after functionality is intact

## Phase 7: Final Visual Polish

Goal:
Only after the command-center shell and functionality are confirmed, polish the UI visually.

Allowed polish:

- Spacing.
- Responsive layout.
- Typography.
- Glass styling.
- Soft shadows.
- Icons.
- Motion.
- Pane resizing if simple and safe.
- Polished empty states.
- Codex/AionUi-inspired visual finish.

Forbidden polish:

- Adding new authority.
- Hiding important safety states.
- Making approval/apply ambiguous.
- Adding extra always-visible panels.
- Adding another dashboard inside `/coding`.
- Adding AionUi integration.
- Adding provider logic changes.

Manual checks:

```bash
cd /home/source/SpiritOS
git diff --check
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
curl -k -sS -I https://localhost:3000/coding
curl -k -sS -I https://localhost:3000/proxy-backend
```

Expected output:

- Layout looks closer to a coding command center.
- Task loop still works.
- Safety loop remains explicit.
- Diagnostics are available but not cluttering default view.
- No commit or push unless separately approved.

Next increment title:
Command Center v0.1 closeout

## Phase 7.1 Closeout: Final Visual Polish After Functionality

Status: implemented and verified, with viewport review still blocked.

Scope completed:

- Polished `/coding` command-center shell spacing and desktop column proportions.
- Added clearer focus-visible states to composer controls, selectors, summaries, links, and action buttons.
- Added subtle hover/transition affordances to safe interactive controls.
- Tightened drawer clipping with `overflow-hidden` on collapsed details surfaces.
- Kept composer primary, task status compact, left rail organized, and right review pane focused.
- Preserved Draft, Preview, Approval, Apply, and Verify as separate visible safety states.
- Preserved `/proxy-backend` as the diagnostics surface.

Files changed in this polish increment:

- `src/components/coding/CodingCockpitShell.tsx`
- `docs/codingUI.md`

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
curl -k -sS -I --max-time 10 https://localhost:3000/coding
curl -k -sS -I --max-time 10 https://localhost:3000/proxy-backend
```

Observed output:

- `git diff --check` had no output.
- `npm run lint` passed with 4 warnings and 0 errors.
- `npm run typecheck` passed.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.
- `global-safety-regression` passed.
- `/coding` returned `200 OK`.
- `/proxy-backend` returned `200 OK`.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No source auto-approval occurred.
- No hidden write occurred.
- No backend behavior changed.
- No route/model/provider behavior changed.
- No AionUi integration was added.
- No mobile execution authority was added.

Remaining blockers:

- Browser screenshot and real viewport review are still not cleared.
- Playwright/e2e remains blocked by missing project-resolved `@playwright/test`, missing browser binary, and stale e2e expectations.
- `CodingAgentInterface.tsx` extraction is deferred.
- 4 lint warnings remain.

Next increment title:
Command Center v0.1 closeout

## Command Center v0.1 Closeout

Status: complete for basic command-center UX, functionality preservation, safety gauntlet dry-runs, bug cleanup, and limited final polish.

Closeout date: 2026-05-21

What changed:

- `/coding` now presents as a Source Proxy command center instead of a stacked safety/process dashboard.
- The default layout has a left project/task rail, center task workspace and composer, compact task status header, right review pane, and collapsed evidence/log drawer.
- The old explanatory hero/header was removed.
- The shared SpiritOS navigation is used.
- The visual styling now matches the SpiritOS theme more closely.
- The composer is the primary work surface.
- Evidence, terminal details, and diagnostics are available without cluttering the default view.
- `/proxy-backend` remains the deeper diagnostics surface.
- Draft, Preview, Approval, Apply, and Verify remain explicit and separate.

Files changed during v0.1:

- `docs/codingUI.md`
- `src/components/coding/CodingAgentInterface.tsx`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `src/components/coding/__tests__/coding-workflow-step.test.ts`

Final checks accepted from operator run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
curl -k -sS -I --max-time 10 https://localhost:3000/coding
curl -k -sS -I --max-time 10 https://localhost:3000/proxy-backend
```

Final observed output:

- `git diff --check` passed.
- `npm run lint` passed with 4 warnings and 0 errors.
- `npm run typecheck` passed.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.
- `global-safety-regression` passed.
- `/coding` returned `200 OK`.
- `/proxy-backend` returned `200 OK`.

Safety closeout:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No source auto-approval occurred.
- No memory writes occurred.
- No backend authority changed.
- No provider/model routing behavior changed.
- No AionUi integration was added.
- No new mobile execution authority was added.
- Test runs did not change files.
- HEAD did not change during safety checks.

Known remaining blockers:

- Browser screenshot and real viewport review are still not cleared.
- Playwright/e2e remains blocked by missing project-resolved `@playwright/test`, missing browser binary, and stale e2e expectations.
- 4 lint warnings remain.
- `CodingAgentInterface.tsx` extraction is deferred.
- Phase 4.6 verify-after-apply remains skipped until explicit operator approval for a bounded apply.

Recommended next increment title:
Source Proxy Command Center v0.2: Browser viewport clearance and remaining warning cleanup

# Source Proxy Command Center v0.2: Browser Viewport Clearance And Remaining Warning Cleanup

Status: active plan.

Start date: 2026-05-21

Goal:
Clear the remaining proof gaps after v0.1 without weakening Source Proxy authority. v0.2 focuses on real browser/viewport evidence, stale Playwright setup, remaining lint warnings, and a small final readiness closeout.

Safety boundaries:

- No commit.
- No push.
- No approve/apply/execute-approved unless the operator explicitly approves a bounded apply task.
- No backend authority changes.
- No provider/model routing behavior changes.
- No AionUi integration.
- No new mobile execution authority.
- No dependency install or browser install unless explicitly approved.
- Do not claim browser/viewport review passed until screenshots or real Playwright/browser runs actually pass.

## v0.2 Phase 0: Baseline Lock

Goal:
Confirm v0.1 is the starting point and prevent the v0.2 lane from inheriting stale or unrelated dirty state.

Small increments:

- 0.1 Confirm expected dirty files.
- 0.2 Confirm v0.1 closeout exists.
- 0.3 Confirm lint baseline is 4 warnings, 0 errors.
- 0.4 Confirm typecheck, frontend regression, cockpit shell, proxy closeout, and global safety remain green.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
grep -n "Command Center v0.1 Closeout" docs/codingUI.md
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
```

Expected output:

- Dirty files are expected v0.1 files unless the operator has added new work.
- `git diff --check` passes.
- v0.1 closeout exists.
- Lint remains 4 warnings, 0 errors.
- Typecheck and regression checks pass.
- Proxy closeout and global safety pass.

Next increment title:
v0.2 Phase 1.1: Playwright dependency and e2e readiness map

## v0.2 Phase 1: Browser And Viewport Clearance

Goal:
Turn the current viewport blocker into either passing browser evidence or an explicit manual screenshot record.

Small increments:

- 1.1 Map Playwright dependency state, scripts, config, browser cache, and stale e2e expectations.
- 1.2 Decide whether to request approval for installing project Playwright dependency/browser binaries or use manual screenshots only.
- 1.3 If approved, update stale `/coding` e2e expectations for the command-center shell.
- 1.4 If approved and tooling is ready, run desktop Chromium viewport check.
- 1.5 If approved and tooling is ready, run iPhone viewport check.
- 1.6 If approved and tooling is ready, run Android/Pixel viewport check.
- 1.7 If not approved or still blocked, complete the manual screenshot checklist from Phase 5.5.

Manual checks:

```bash
cd /home/source/SpiritOS
npm run test -- --help | head -40
npx playwright --version || true
npx playwright test --list || true
ls -la playwright.config.* tests/e2e 2>/dev/null || true
find ~/.cache/ms-playwright -maxdepth 2 -type f -name chrome -o -name chromium -o -name headless_shell 2>/dev/null | head -20
```

Expected output:

- Honest readiness map.
- No viewport clearance claimed unless a real browser run or manual screenshot review happens.

Next increment title:
v0.2 Phase 2.1: Remaining warning cleanup plan

## v0.2 Phase 1.1 Closeout: Playwright Dependency And E2E Readiness Map

Status: mapped, viewport clearance still blocked.

Findings:

- `playwright.config.mjs` exists and imports `@playwright/test`.
- `tests/e2e/coding-ui.spec.mjs` exists.
- `npm ls @playwright/test playwright --depth=0` shows no project-installed Playwright packages.
- `package-lock.json` references `@playwright/test` and `@vitest/browser-playwright`, but project resolution is not currently available from `node_modules`.
- `npx playwright --version` reports `Version 1.60.0` via npx.
- `npx playwright test --list` fails with `ERR_MODULE_NOT_FOUND` for `@playwright/test` imported from `playwright.config.mjs`.
- No local browser binary was found in `~/.cache/ms-playwright`.
- `npx playwright install --dry-run chromium` reports install locations but warns dependencies are not installed first.
- Existing `/coding` e2e expectations are stale:
  - expects `Spirit workspace navigation`, but v0.1 uses shared SpiritOS navigation labels.
  - expects `Advanced diagnostics`, but v0.1 uses `Backend diagnostics`.
  - does not assert the current left rail / center composer / right review pane command-center structure.

Readiness decision needed:

- Option A: request explicit approval to install/restore project Playwright dependency and browser binaries, then update stale e2e expectations and run real viewport checks.
- Option B: do not install dependencies/browsers; use the manual screenshot checklist from Phase 5.5 and keep Playwright as blocked.

Manual checks run:

```bash
cd /home/source/SpiritOS
npm ls @playwright/test playwright --depth=0 || true
grep -n "playwright\\|@playwright\\|e2e" package.json package-lock.json 2>/dev/null | head -80
npx playwright --version || true
npx playwright test --list || true
ls -la playwright.config.* tests/e2e 2>/dev/null || true
find ~/.cache/ms-playwright -maxdepth 2 -type f \( -name chrome -o -name chromium -o -name headless_shell \) 2>/dev/null | head -20
npx playwright install --dry-run chromium 2>&1 | head -100
git status --branch --short
git diff --check
```

Observed output:

- Project-installed Playwright packages are absent.
- Playwright CLI via npx reports `Version 1.60.0`.
- `npx playwright test --list` fails on missing `@playwright/test`.
- Config and e2e spec files exist.
- Browser cache search found no local browser binary.
- `git diff --check` had no output.
- Dirty files remained the expected v0.1/v0.2 work files.

Safety notes:

- No dependency install occurred.
- No browser install occurred.
- No e2e spec was changed.
- No viewport clearance was claimed.
- No backend behavior changed.
- No approval, apply, execute-approved, commit, push, destructive cleanup, provider routing change, or AionUi integration occurred.

Next increment title:
v0.2 Phase 1.2: Decide Playwright install approval or manual screenshot path

## v0.2 Phase 1.2 Closeout: Manual Screenshot Path Selected By Default

Status: decided for now.

Decision:

- Use the manual screenshot checklist path unless the operator explicitly approves dependency and browser installation.
- Do not install `@playwright/test`.
- Do not install Playwright browser binaries.
- Do not update stale e2e specs yet.

Clarification:

- `npx playwright --version` works because npx can fetch/use a Playwright CLI.
- The project itself cannot resolve `@playwright/test`:
  - `node -p "require.resolve('@playwright/test')"` fails with `MODULE_NOT_FOUND`.
  - `node -p "require.resolve('playwright')"` fails with `MODULE_NOT_FOUND`.
  - `npm ls @playwright/test playwright --depth=0` shows `(empty)`.
  - `package.json` has no direct `@playwright/test` or `playwright` dependency.
  - `node_modules/@playwright/test` and `node_modules/playwright` are absent.

Manual checks run:

```bash
cd /home/source/SpiritOS
node -p "require.resolve('@playwright/test')" 2>&1 || true
node -p "require.resolve('playwright')" 2>&1 || true
npm ls @playwright/test playwright --depth=0 || true
ls -ld node_modules node_modules/@playwright node_modules/playwright node_modules/@playwright/test 2>/dev/null || true
cat package.json | sed -n '1,140p'
git status --branch --short
```

Observed output:

- `@playwright/test` is not project-resolvable.
- `playwright` is not project-resolvable.
- `npm ls` shows no project-installed Playwright packages.
- `package.json` has no Playwright dependency/script.
- Dirty files remain the expected v0.1/v0.2 work files.

Safety notes:

- No dependency install occurred.
- No browser install occurred.
- No e2e spec was changed.
- No viewport clearance was claimed.
- No backend behavior changed.
- No approval, apply, execute-approved, commit, push, destructive cleanup, provider routing change, or AionUi integration occurred.

Next increment title:
v0.2 Phase 1.7: Complete manual screenshot checklist or collect operator screenshots

## v0.2 Phase 1.7 Closeout: Manual Screenshot Checklist Pending

Status: pending operator screenshots.

Scope completed:

- Confirmed the manual browser screenshot checklist exists in `docs/codingUI.md`.
- Confirmed `/coding` route smoke returns `200 OK`.
- Confirmed `/proxy-backend` route smoke returns `200 OK`.
- Confirmed `git diff --check` remains clean.
- Did not claim desktop/mobile viewport review is cleared.

Manual checks run:

```bash
cd /home/source/SpiritOS
curl -k -sS -I --max-time 10 https://localhost:3000/coding
curl -k -sS -I --max-time 10 https://localhost:3000/proxy-backend
grep -n "Manual browser screenshot checklist\\|Route: /coding\\|Desktop viewport\\|iPhone-sized viewport\\|Android-sized viewport" docs/codingUI.md
git status --branch --short
git diff --check
```

Observed output:

- `/coding` returned `200 OK`.
- `/proxy-backend` returned `200 OK`.
- Manual screenshot checklist anchors exist.
- Dirty files remain the expected v0.1/v0.2 work files.
- `git diff --check` had no output.

Still needed for viewport clearance:

- Desktop screenshot review.
- iPhone-sized screenshot review.
- Android-sized screenshot review.
- Confirmation that mobile review does not add mobile execution authority.

Safety notes:

- No dependency install occurred.
- No browser install occurred.
- No e2e spec was changed.
- No viewport clearance was claimed.
- No backend behavior changed.
- No approval, apply, execute-approved, commit, push, destructive cleanup, provider routing change, mobile execution authority, or AionUi integration occurred.

Next increment title:
v0.2 Phase 2.1: Remaining warning cleanup plan

## v0.2 Phase 2: Remaining Warning Cleanup

Goal:
Reduce the 4-warning baseline without risky behavioral changes.

Remaining warning targets:

- `src/app/v1/cartographer/audit-trail/route.ts`: unused `result`.
- `src/components/coding/CodingAgentInterface.tsx`: missing `previewDiffVerification` hook dependency.
- `src/components/coding/CodingAgentInterface.tsx`: missing `approvalGate`, `diffVerification`, `longRunningTask`, and `proxySafetySmoke` hook dependencies.
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`: unused `pendingProposalCount`.

Small increments:

- 2.1 Classify warning ownership and risk one more time against the current dirty tree.
- 2.2 Fix non-`/coding` unused variables only if the operator wants the cleanup lane to touch those areas.
- 2.3 Investigate hook dependency warnings with focused tests before changing dependencies.
- 2.4 Leave hook warnings documented if behavior risk is higher than v0.2 benefit.
- 2.5 Rerun lint, typecheck, frontend regression, and proxy closeout.

Manual checks:

```bash
cd /home/source/SpiritOS
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
```

Expected output:

- Fewer warnings if low-risk fixes are made, or documented deferral if not.
- No behavior or authority changes.

Next increment title:
v0.2 Phase 3.1: Command Center v0.2 closeout

## v0.2 Phase 2.1 Closeout: Remaining Warning Ownership And Risk

Status: implemented as triage.

Current lint baseline:

- 4 warnings.
- 0 errors.
- Babel deoptimization note remains for `src/components/coding/CodingAgentInterface.tsx` because it exceeds 500KB.

Warning ownership and risk:

| Warning | Ownership | Risk | Decision |
| --- | --- | --- | --- |
| `src/app/v1/cartographer/audit-trail/route.ts` unused `result` | Cartographer route | Low code risk, outside `/coding` command-center lane | Fix only if operator approves touching Cartographer in this lane. |
| `src/components/dashboard/HomelabBlueprintReviewWidget.tsx` unused `pendingProposalCount` | Dashboard widget | Low code risk, outside `/coding` command-center lane | Fix only if operator approves touching dashboard in this lane. |
| `src/components/coding/CodingAgentInterface.tsx` missing `previewDiffVerification` dependency | Legacy coding interface | Medium/high behavior risk because hook timing may intentionally avoid repeated effects | Investigate with focused tests before changing. |
| `src/components/coding/CodingAgentInterface.tsx` missing `approvalGate`, `diffVerification`, `longRunningTask`, `proxySafetySmoke` dependencies | Legacy coding interface | Medium/high behavior risk because adding dependencies could retrigger safety/proxy effects | Investigate with focused tests before changing. |

Recommended warning plan:

- Do not change hook dependencies casually.
- Keep `CodingAgentInterface.tsx` extraction deferred.
- Ask before touching Cartographer or dashboard files from the Source Proxy command-center lane.
- If the operator approves cross-lane cleanup, fix only the two non-`/coding` unused variable warnings first.
- If the operator does not approve cross-lane cleanup, proceed to v0.2 closeout with 4 warnings documented.

Manual checks run:

```bash
cd /home/source/SpiritOS
npm run lint
git status --branch --short
```

Observed output:

- `npm run lint` passed with 4 warnings and 0 errors.
- Dirty files remain the expected v0.1/v0.2 work files.

Safety notes:

- No production code changed in this increment.
- No backend behavior changed.
- No approval, apply, execute-approved, commit, push, destructive cleanup, provider routing change, or AionUi integration occurred.

Next increment title:
v0.2 Phase 2.2: Optional cross-lane unused-variable cleanup or defer remaining warnings

## v0.2 Phase 2.2 Closeout: Cross-Lane Warning Cleanup Deferred

Status: deferred by default.

Decision:

- Do not touch Cartographer or dashboard files from the Source Proxy command-center lane without explicit operator approval.
- Do not change `CodingAgentInterface.tsx` hook dependencies during v0.2 without a focused behavior investigation and targeted tests.
- Carry the current 4-warning lint baseline into v0.2 closeout as documented residual cleanup.
- Treat the remaining warnings as cleanup work, not blockers for command-center v0.2 closeout.

Manual checks run:

```bash
cd /home/source/SpiritOS
npm run lint
git status --branch --short
```

Observed output:

- `npm run lint` still reports 4 warnings and 0 errors.
- The remaining warnings are the two non-`/coding` unused-variable warnings plus two deferred `CodingAgentInterface.tsx` hook dependency warnings.
- Dirty files remain limited to the Source Proxy command-center work files.

Safety notes:

- No Cartographer or dashboard edits were made in this increment.
- No hook dependency behavior was changed.
- No backend behavior, model routing, provider routing, approval, apply, execute-approved, commit, push, or destructive cleanup occurred.

Next increment title:
v0.2 Phase 3.1: Command Center v0.2 closeout

## v0.2 Phase 3: Closeout

Goal:
Record whether v0.2 cleared viewport proof and warning cleanup, or honestly preserve blockers.

Manual checks:

```bash
cd /home/source/SpiritOS
git diff --check
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
curl -k -sS -I --max-time 10 https://localhost:3000/coding
curl -k -sS -I --max-time 10 https://localhost:3000/proxy-backend
```

Expected output:

- Safety checks pass.
- `/coding` and `/proxy-backend` return 200.
- Browser/viewport status is accurately reported.
- Warning status is accurately reported.
- No commit or push unless separately approved.

Next increment title:
v0.2 Phase 0.1: Confirm expected dirty files and v0.1 baseline

## v0.2 Phase 0 Closeout: Baseline Lock

Status: complete.

Scope completed:

- Confirmed v0.1 closeout exists.
- Confirmed v0.2 plan exists.
- Confirmed current dirty files are the expected command-center work files.
- Confirmed lint baseline is 4 warnings and 0 errors.
- Confirmed typecheck passes.
- Confirmed frontend regression passes.
- Confirmed cockpit shell tests pass.
- Confirmed proxy closeout passes.
- Confirmed global safety regression passes.

Current expected dirty files:

- `docs/codingUI.md`
- `src/components/coding/CodingAgentInterface.tsx`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `src/components/coding/__tests__/coding-workflow-step.test.ts`

Manual checks run:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
grep -n "Command Center v0.1 Closeout\\|Source Proxy Command Center v0.2\\|v0.2 Phase 0" docs/codingUI.md
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
```

Observed output:

- `git status --branch --short` showed branch `main...origin/main [ahead 31]` and the five expected dirty files.
- `git diff --check` had no output.
- v0.1 closeout, v0.2 plan, and v0.2 Phase 0 markers exist in `docs/codingUI.md`.
- `npm run lint` passed with 4 warnings and 0 errors.
- `npm run typecheck` passed.
- `npm run test:coding-frontend-regression` passed: 7 test files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 test file, 6 tests.
- `proxy-closeout` passed.
- `global-safety-regression` passed.

Safety notes:

- No approve occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No source auto-approval occurred.
- No memory writes occurred.
- No unexpected mutation occurred.
- HEAD did not change during safety checks.

Next increment title:
v0.2 Phase 1.1: Playwright dependency and e2e readiness map

## v0.2 Phase 3.1 Closeout: Command Center v0.2 Status

Status: closed with documented residual blockers.

Scope completed:

- Confirmed the command-center shell remains the active `/coding` direction.
- Confirmed v0.2 browser/viewport work selected the manual screenshot path because repo-local Playwright dependencies and browser runtime are not ready.
- Confirmed remaining warning cleanup is triaged and intentionally deferred unless the operator approves cross-lane cleanup or focused hook investigation.
- Confirmed `/coding` remains the everyday command center and `/proxy-backend` remains the deep diagnostics surface.

Manual checks run:

```bash
cd /home/source/SpiritOS
git diff --check
npm run lint
npm run typecheck
npm run test:coding-frontend-regression
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
curl -k -sS -I --max-time 10 https://localhost:3000/coding
curl -k -sS -I --max-time 10 https://localhost:3000/proxy-backend
```

Observed output:

- `git diff --check` passed.
- `npm run lint` passed with 4 warnings and 0 errors.
- `npm run typecheck` passed.
- `npm run test:coding-frontend-regression` passed: 7 files, 157 tests.
- `CI=1 npm run test -- coding-cockpit-shell` passed: 1 file, 6 tests.
- `proxy-closeout` passed.
- `global-safety-regression` passed.
- `/coding` returned `HTTP/1.1 200 OK`.
- `/proxy-backend` returned `HTTP/1.1 200 OK`.

Residual blockers:

- Real desktop/mobile viewport clearance remains pending until manual screenshots are completed or Playwright dependencies/browser runtime are explicitly installed and checked.
- Lint remains at 4 warnings: two cross-lane unused-variable warnings and two deferred `CodingAgentInterface.tsx` hook dependency warnings.
- Branch remains ahead of origin with uncommitted command-center work; no commit or push was performed in this lane.

Safety notes:

- No approval occurred.
- No apply occurred.
- No `execute-approved` occurred.
- No commit occurred.
- No push occurred.
- No destructive cleanup occurred.
- No backend authority change occurred.
- No model or provider routing behavior changed.
- No AionUi integration or bridge was added.
- No new mobile execution authority was added.

Next increment title:
v0.3 Phase 0.1: Manual viewport review or Playwright dependency decision

## Historical Closeout-Repair Plan

Everything below this point is retained as historical closeout and prior cockpit-polish context. It is not the active implementation plan for the next `/coding` work.

# /coding UI Polish Plan

status: closeout-repair

Status date: 2026-05-20

## UI Closeout Repair Status

Repair date: 2026-05-20

Current verified status:

- UI-4 is verified implemented in code and tests. The default `/coding` flow now uses the task composer, one current state card, one safe next action surface, a compact diff/review summary when preview exists, and collapsed evidence.
- UI-5 is verified implemented in code and tests. Mobile support includes a sticky mobile action bar, diagnostic handoff link, and legal-state action buttons for preview, approve, and apply.
- UI-6 terminal closeout passed. Manual route smoke passed for `/coding` and `/proxy-backend`; true desktop/mobile screenshot review remains blocked in this environment because no Playwright package or local browser binary is installed.

Readiness decision:

- `/coding` is ready for the next Codex-like polish planning pass.
- `/coding` is not cleared for visual-polish implementation that depends on viewport judgment until a real desktop/mobile browser review is run.
- The next Codex-like polish plan must remain UI-only unless separately approved.
- `/proxy-backend` remains the diagnostic surface.
- No commit, push, provider, autopilot, AionUi, Cowork, native mobile, or backend authority expansion is active in this repair pass.

## Purpose

`/coding` is the clean, Codex-like everyday cockpit for Source Proxy coding work. It helps the operator draft a task, preview a bounded proposal, review evidence, approve only when legal, apply only after approval, verify afterward, and understand the next safe action.

`/proxy-backend` remains the raw diagnostic and backend surface for detailed route output, replay logs, task internals, safety evidence, and troubleshooting.

This plan is UI polish only. It uses existing Source Proxy contracts and gates. It does not create new authority, hidden writes, commit/push buttons, provider routing, autopilot, or any bypass around preview, approval, apply, or verification.

## Authority Boundary

- `/coding` is a client/control surface.
- `/proxy-backend` is the advanced diagnostic console.
- Source Proxy APIs remain the execution boundary.
- Task specs, target files, allowed files, diff preview, reviewer/verifier evidence, approval, apply, and verification remain separate.
- Buttons appear only when legal under existing backend state.
- Apply does not imply commit.
- Verify does not imply push.
- No commit or push controls belong in this UI polish phase.
- No backend authority changes are allowed unless UI work reveals a real missing contract and a separate approval authorizes it.
- Mobile-first support matters because Codex mobile and remote terminal workflows are part of daily operation.

## Status Language

The cockpit should use readable states:

- Draft
- Preview ready
- Needs approval
- Approved, not applied
- Applied, verification required
- Verified
- Blocked

Every state should make clear what happened, whether files changed, what evidence exists, and what the next safe action is.

## Simplification-First Direction

Default `/coding` must show one simple operator flow, not a wall of process evidence.

The default screen should contain:

- Task composer
- One current state card
- One safe next action bar
- Diff/review summary when available
- Collapsed evidence and receipts

Each screen should answer:

- What task is being worked on?
- What state is it in?
- What changed?
- What can I safely do next?
- What evidence exists if inspection is needed?

Keep the Source Proxy process visible as:

```text
Draft -> Preview -> Approval -> Apply -> Verify
```

Do not add new major UI sections unless they replace or simplify an existing section. UI polish should remove competition for attention before it adds new visible structure.

Collapse or hide by default:

- raw Architect/Coder/Reviewer/Verifier role timeline
- terminal/test evidence unless failed or explicitly opened
- receipts and verbose evidence packets
- backend route details
- raw task internals

Deep diagnostics belong in `/proxy-backend`. `/coding` may link there, but should not reproduce the diagnostic console.

## Phase UI-0: Green Baseline And Route Separation

Intent:
Record that the backend green gate passed and separate the next active UI track from backend diagnostics before feature work begins.

Allowed files or likely files:

- `docs/plan-index.md`
- `docs/source-proxy-production-hardening-plan.md`
- `docs/codingUI.md`

Forbidden actions:

- Source code changes
- backend contract changes
- deletion or cleanup without explicit permission
- recreating `proxyCLI.md`
- commit, push, autopilot, provider, AionUi, Cowork, or native mobile work

Manual checks:

```bash
git diff -- docs/plan-index.md docs/source-proxy-production-hardening-plan.md docs/codingUI.md
git diff --check -- docs/plan-index.md docs/source-proxy-production-hardening-plan.md docs/codingUI.md
```

Expected output:

- Green gate is recorded.
- `/coding` is named as the user cockpit.
- `/proxy-backend` is named as diagnostics.
- No feature implementation starts.

Next increment title:
UI-1: Clean `/coding` cockpit shell.

## Phase UI-1: Clean /coding Cockpit Shell

Intent:
Make `/coding` feel like a focused operator cockpit instead of a diagnostic wall, while keeping `/proxy-backend` unchanged.

Allowed files or likely files:

- `src/app/coding/page.tsx`
- `src/components/coding/*`
- `src/components/coding/__tests__/*`
- targeted styling files already used by the coding surface
- targeted Playwright coverage if an e2e pattern already exists

Forbidden actions:

- Backend execution changes
- commit or push buttons
- approval/apply bypasses
- hidden writes
- provider marketplace or provider expansion
- new autonomy or autopilot controls

Manual checks:

- Open `/coding` on desktop and mobile viewport.
- Open `/proxy-backend` and confirm diagnostic detail remains available there.
- Confirm the default `/coding` view shows a header/status strip, task composer, current task card, safe action rail, mobile-first stacked layout, and no debug clutter.
- Confirm any advanced details link to `/proxy-backend`.

Expected output:

- `/coding` has a calm cockpit shell.
- Debug-heavy panels are removed or hidden from the default view.
- `/proxy-backend` still carries diagnostics.
- No source files are changed by viewing or composing.

Next increment title:
UI-2: Collapsed evidence trail.

## Phase UI-2: Timeline And Evidence

Status: superseded by simplification direction.

Intent:
Keep evidence available without making role/process cards compete with the main operator flow.

Allowed files or likely files:

- `src/components/coding/*`
- existing Source Proxy client hooks or typed response adapters
- `src/components/coding/__tests__/*`
- targeted Playwright tests if present

Forbidden actions:

- New backend authority
- changing verifier/reviewer semantics
- applying files from the timeline
- commit or push affordances
- hiding blockers in order to make the UI look cleaner

Manual checks:

- Confirm raw role timeline is collapsed under `Evidence trail`.
- Confirm terminal/test evidence is collapsed unless failed or explicitly opened.
- Confirm the readable state renders in one current state card.
- Confirm a path to full diagnostics in `/proxy-backend` remains visible.

Expected output:

- The operator sees one main flow, not several competing process panels.
- Evidence exists but is collapsed by default.
- Failed evidence can surface enough detail to explain the blocker.

Next increment title:
UI-3: Diff/review summary.

## Phase UI-3: Diff And Review Pane

Status: superseded by simplification direction.

Intent:
Expose the review facts that make approval safe as a compact summary, not as another always-visible diagnostic pane.

Allowed files or likely files:

- `src/components/coding/*`
- existing diff/review rendering helpers
- `src/components/coding/__tests__/*`
- targeted Playwright tests if present

Forbidden actions:

- Diff application from this pane
- mutating allowed files, target files, or protected path results in the client
- treating reviewer advisory output as a hard pass unless the backend already says so
- commit/push controls

Manual checks:

- Confirm changed files, allowed-file result, protected-path result, target match, reviewer verdict, and verification result appear in one compact diff/review summary when preview exists.
- Confirm raw diff and role evidence are collapsed unless explicitly opened or failed.
- Confirm an `Open diagnostics in /proxy-backend` link is present.

Expected output:

- The operator can tell whether the preview is bounded and reviewable.
- Mismatches and protected-path blocks are obvious.
- Full diagnostic detail remains one click away instead of always visible.

Next increment title:
UI-4: Simplify default cockpit flow.

## Phase UI-4: Approval/Action Bar

Status: verified implemented in UI-Closeout-Repair.

Intent:
Replace competing visible panels with one default operator flow: task composer, current state card, safe next action bar, compact diff/review summary, and collapsed evidence trail.

Allowed files or likely files:

- `src/components/coding/*`
- existing approval/apply client integration already used by Source Proxy
- `src/components/coding/__tests__/*`
- targeted Playwright tests if present

Forbidden actions:

- Buttons that appear before backend state allows them
- apply without approval
- approval that mutates files
- apply implying commit
- verify implying push
- commit or push buttons
- hidden writes

Manual checks:

- Confirm the default `/coding` view does not show role cards, terminal evidence, receipts, or raw backend details as always-visible panels.
- Confirm the Source Proxy process remains clear: Draft -> Preview -> Approval -> Apply -> Verify.
- Confirm Preview appears for draft work only when required fields are valid.
- Confirm Approve appears only when preview gates pass and approval is legal.
- Confirm Apply appears only after approval and uses existing approval binding.
- Confirm Verify appears only after apply or when backend state says verification is needed.
- Confirm blocked state explains the blocker and the safe next action.

Expected output:

- `/coding` is simpler than before this increment.
- Preview, approve, apply, and verify are distinct.
- Illegal actions are absent or disabled with an explanation.
- Apply never implies commit; verify never implies push.

Next increment title:
UI-5: Mobile/manual remote checks after simplification.

## Phase UI-5: Mobile/Manual Remote Checks

Status: verified implemented in UI-Closeout-Repair.

Intent:
Make `/coding` usable for Codex mobile and remote workflows without requiring a full desktop visual session for basic review.

Allowed files or likely files:

- `src/components/coding/*`
- existing responsive styles
- targeted Playwright device checks
- docs updates for manual remote checks if needed

Forbidden actions:

- Native mobile app work
- RustDesk-only workflow assumptions
- mobile-only authority bypasses
- hidden writes or shortcuts around approval
- commit/push controls

Manual checks:

- Review on iPhone-sized viewport.
- Review on Android-sized viewport.
- Confirm mobile review cards show status, changed files, blockers, evidence, and next safe action.
- Confirm Codex mobile/manual terminal workflow notes remain accurate.
- Confirm basic checks do not require RustDesk when the cockpit exposes enough state.
- Confirm RustDesk remains useful only for full visual debugging.

Expected output:

- `/coding` can be reviewed comfortably on mobile.
- Remote operation can rely on cockpit state plus terminal checks for common cases.
- Visual debugging remains available without becoming required for every check.

Next increment title:
UI-6: Closeout.

## Phase UI-6: Closeout

Status: terminal closeout passed; visual viewport review blocked by missing browser tooling.

Intent:
Verify the UI polish did not weaken Source Proxy safety and record the finished state.

Allowed files or likely files:

- final touched UI files
- final touched tests
- docs touched by the approved UI polish increment

Forbidden actions:

- commit or push
- destructive cleanup
- broad refactors outside the UI polish scope
- new backend authority
- autopilot, provider marketplace, AionUi bridge, Cowork console, or native mobile activation

Manual checks:

```bash
git diff --check
git status --short
```

Run available checks only after inspecting scripts and local environment:

- typecheck
- lint if available
- targeted Vitest if available
- targeted Playwright if available
- global safety regression
- dashboard smoke
- no unexpected mutation check

Expected output:

- Typecheck passes.
- Lint passes if available.
- Targeted UI tests pass if available.
- Targeted Playwright checks pass if available.
- Global safety regression remains green.
- Dashboard smoke remains green.
- No unexpected mutation occurs.
- Docs are updated.
- No commit or push occurs.

Next increment title:
UI-Closeout-Repair: record terminal and desktop/mobile review results.

## UI-Closeout-Repair Record

Status: complete with visual-review blocker recorded.

Scope:

- Verify UI-4, UI-5, and UI-6 actual status.
- Fix contradictory planning status.
- Run terminal closeout pack.
- Run manual desktop and mobile cockpit review.
- Record whether `/coding` is ready for the next Codex-like polish plan.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run lint
npm run typecheck
CI=1 npm run test -- coding-cockpit-shell
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
curl -k -sS -I https://localhost:3000/coding
curl -k -sS -I https://localhost:3000/proxy-backend
curl -k -sS https://localhost:3000/coding | grep -Eo 'Coding|Source Proxy cockpit|Task Composer|Evidence trail|Advanced diagnostics' | sort | uniq -c
```

Observed output:

- Worktree showed only this closeout-repair docs update before recording results.
- Diff check had no output.
- Lint passed with 7 existing warnings and 0 errors.
- Typecheck passed.
- `coding-cockpit-shell` passed 6 tests.
- Global safety regression passed: Source Proxy safety, Scout backend, Cartographer safety, dashboard smoke, no unexpected mutation, no unexpected Level 2 evidence, no commit, and stable HEAD.
- HTTPS route smoke returned `200 OK` for `/coding` and `/proxy-backend` on the existing dev server at `https://localhost:3000`.
- `/coding` route HTML contained `Source Proxy cockpit`, `Task Composer`, `Evidence trail`, `Advanced diagnostics`, and `Coding`.
- Desktop/mobile screenshot review could not run because this environment has `playwright.config.mjs` but no Playwright package and no local browser binary.

Next increment title:
Next Codex-like `/coding` polish plan draft, then real desktop/mobile visual review before implementation.
