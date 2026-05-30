# Coding Command Center VoidCore Master Plan v0.1

Status: planning only
Status date: 2026-05-21
Scope: replace the current `/coding` visual experience with a VoidCore-inspired coding command center foundation while preserving the Source Proxy coding engine and safety contracts underneath.

## A. Current-State Summary

Clear direction: the current `/coding` design is not being polished. It is being replaced visually. The existing `/coding` implementation is a backend/wiring reference for safe coding workflow contracts, route payloads, approval gates, and stress-tested Source Proxy behavior.

Preserve these backend and wiring pieces:

- `/coding` route entry: `src/app/coding/page.tsx`.
- Current cockpit wiring reference: `src/components/coding/CodingCockpitShell.tsx`.
- Older deep Source Proxy UI/wiring reference: `src/components/coding/CodingAgentInterface.tsx`.
- Approval derivation: `src/components/coding/approval-gate-binding.ts`.
- Proxy route payload guards: `src/lib/coding/proxy-route-payload.ts`.
- Proposal handoff, target parsing, diff path checks, workflow copy: `src/lib/coding/*`.
- Source Proxy origin fallback and stream handling: `src/lib/source-proxy-origin.ts`.
- BFF routes to Source Proxy: `src/app/v1/decisions/prompt-packet/route.ts`, `src/app/v1/verification/diff-preview/route.ts`, `src/app/v1/actions/execute-approved/route.ts`, `src/app/v1/tasks/long-running/*`, `src/app/v1/coding/codex/route.ts`.
- Source Proxy engine routes and tests in `source_proxy/api/*`, `source_proxy/codex/*`, `source_proxy/tasks/*`, `source_proxy/verification/*`, and `source_proxy/tests/*`.
- Chat persistence contracts in `src/lib/chat-db.ts`, `src/lib/chat-db.types.ts`, and `src/lib/chat-persistence.ts`.
- Model profile UI and runtime contracts in `src/components/chat/ModelProfileSelector.tsx`, `src/lib/spirit/model-profiles.ts`, `src/lib/spirit/model-runtime.ts`, and `src/lib/server/model-routing.ts`.
- Workspace and Windows bridge read/list tooling in `src/lib/spirit/tools/workspace-tools.ts` and `src/lib/spirit/tools/windows-workspace-tools.ts`.

Replace these visual pieces:

- The current stacked safety/process dashboard feel.
- The current task rail, status card stack, review pane composition, and composer layout as the target visual foundation.
- The current `DashboardDemoV4` cockpit styling as the final target. It may remain as a temporary reference, but the new foundation should follow the VoidCore command-center direction.

Inspected during this planning pass:

- `/coding` route and components: `src/app/coding/page.tsx`, `src/components/coding/CodingCockpitShell.tsx`, `src/components/coding/CodingAgentInterface.tsx`.
- Coding safety helpers: `src/components/coding/approval-gate-binding.ts`, `src/lib/coding/proxy-route-payload.ts`, `src/lib/coding/proposal-task-handoff.ts`, `src/lib/coding/unified-diff-paths.ts`, `src/lib/coding/workflow-progress-copy.ts`.
- Source Proxy bridge and routes: `src/lib/source-proxy-origin.ts`, `src/app/v1/decisions/prompt-packet/route.ts`, `src/app/v1/verification/diff-preview/route.ts`, `src/app/v1/actions/execute-approved/route.ts`, `src/app/v1/tasks/long-running/*`, `src/app/v1/coding/codex/route.ts`.
- Chat persistence/thread code: `src/lib/chat-db.ts`, `src/lib/chat-db.types.ts`, `src/lib/chat-persistence.ts`, `src/components/chat/SpiritTrinityChatShell.tsx`, `src/app/chat/page.tsx`.
- Model/profile routing: `src/components/chat/ModelProfileSelector.tsx`, `src/lib/spirit/model-profiles.ts`, `src/lib/spirit/model-runtime.ts`, `src/lib/server/model-routing.ts`, `src/app/api/spirit/route.ts`.
- Workspace/project tooling: `src/lib/spirit/tools/workspace-tools.ts`, `src/lib/spirit/tools/windows-workspace-tools.ts`, related tests under `src/lib/spirit/tools/__tests__`.
- Tests: `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, `src/components/coding/__tests__/approval-gate-binding.test.ts`, `src/lib/coding/__tests__/*`, `src/app/v1/coding/*/__tests__`, `src/app/v1/actions/execute-approved/__tests__/route.test.ts`, `tests/e2e/coding-ui.spec.mjs`.
- Docs: `docs/codingUI.md`, `docs/source-proxy-coding-agent-a-plus-stress-gauntlet.md`, `docs/source-proxy-regression-matrix.md`, `docs/source-proxy-daily-use-runbook.md`.
- Demo/reference files: `src/app/coding/design-demo/page.tsx`, `src/app/design-demo/coding/page.tsx`, `src/app/design-demo/page.tsx`, `_reference/dashboardDemo/src/App.tsx`, `chatDesign/*`.

Known:

- The Source Proxy safety loop is `Draft -> Preview -> Approval -> Apply -> Verify`.
- The current cockpit already calls preview routes before approval and applies only after an explicit approved state.
- The chat system already has local Dexie thread/message persistence.
- Spirit chat routing is local LLM/Ollama oriented by default where configured, with model/profile metadata separated from UI.
- Windows project access is deliberately gated by `SPIRIT_WINDOWS_FS_ENABLED`, base URL, bearer token, and allowlist.
- `package.json` includes `lint`, `typecheck`, `test`, and `test:coding-frontend-regression`.
- `playwright.config.mjs` exists, but `package.json` does not list `@playwright/test`; browser smoke checks must verify tooling before use.

Unknown:

- Whether the exact uploaded coding demo assets are present. The repo contains design/demo references, but no folder literally named `voidcore-agent-shell`.
- Whether the Windows bridge is currently configured to allow `C:\Projects` on the main PC.
- Whether GPT/cloud coding route credentials are configured in this environment.
- Whether safe project creation exists. Until proven, “Start new project” must be disabled, dry-run, or explicitly marked unwired.

Blocked until later approval:

- Code implementation.
- Source Proxy backend contract edits.
- Project creation.
- Windows writes.
- Autonomous coding, hidden mutation, self-approval, commits, pushes, merges, branch/worktree creation, cleanup, or stash.

## B. Target Product Definition

The target is a Coding Command Center: a focused command shell for coding work where the user can open `/coding`, start chats, switch between chats, choose the current workspace/project, see local or cloud model availability honestly, and enter coding mode without weakening Source Proxy safety.

Base shell in plain language:

- Left rail: chat list, new chat button, current workspace/project, compact task buckets.
- Center: active chat/task area with a centered composer, model/context chips, and a clear coding-mode entry point.
- Top or near-composer controls: workspace/project selector, local/GPT provider selector, context chips, availability status.
- Right or lower area: active task/status, compact safety state, preview/diff/review evidence when coding mode is active.
- Mobile-first: rail collapses into a drawer, composer remains primary, status stays compact and honest.

MVP base:

- `/coding` shell renders.
- User can start a new chat.
- User can create at least two chats and visibly swap between them.
- Empty per-chat state is preserved.
- Default workspace is the current SpiritOS repo.
- User can choose to work in the repo by default.
- Project selector shows a future path toward `C:\Projects` when Windows bridge tooling supports it.
- “Start new project” is visible but honest: disabled, dry-run, or explicitly unwired until safe project creation exists.
- Local LLM/local AI coding is the default where supported.
- GPT/cloud route is selectable only when configured or clearly shown as unavailable.
- UI shows model/provider availability and never claims local or GPT was used unless that route was actually used.
- Coding mode has an entry point from a chat.
- Coding preview uses existing Source Proxy safety flow.
- Safety workflow remains intact: draft, preview, approval gate, apply after approval only, verify, honest errors.

Intentionally not in MVP:

- Full autonomous coding.
- Hidden write actions.
- Auto project creation.
- Unsafe Windows mutation.
- Apply wiring before preview and approval are proven in the new shell.
- Final animation/polish before shell, chat switching, workspace selector, model selector, and coding preview work.
- Commit, push, merge, branch creation, worktree creation, cleanup, stash, or self-approval.

## C. Sequential Phases And Small Increments

Each increment below is intentionally small. Do not advance until the manual check passes and the operator can visually or terminal-check the expected outcome.

Manual check format rule:

- Each increment gets exactly one copy-paste terminal block.
- The expected outcome comes immediately after that block.
- The next increment title comes immediately after the expected outcome.
- Rollback notes come after the next increment title.

### Phase 0: Discovery, Boundary, And Baseline

#### Increment 0.1: Inventory `/coding` Backend Contracts

Purpose: Identify current safe coding contracts without changing them.

Files likely touched: none.

Allowed changes: none; notes only in this plan.

Forbidden changes: component rewrites, route edits, Source Proxy edits, styling changes.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git status --branch --short
grep -n "fetch(\"/v1/decisions/prompt-packet\"" src/components/coding/CodingCockpitShell.tsx
grep -n "fetch(\"/v1/verification/diff-preview\"" src/components/coding/CodingCockpitShell.tsx
grep -n "fetch(\"/v1/actions/execute-approved\"" src/components/coding/CodingCockpitShell.tsx
```

Expected outcome: current cockpit shows preview, diff-preview, and execute-approved call sites; no files changed.

Next increment title: Increment 0.2: Inventory Chat Persistence

Rollback notes: no rollback; discovery only.

#### Increment 0.2: Inventory Chat Persistence

Purpose: Confirm whether thread creation, message persistence, and model profile fields can be reused.

Files likely touched: none.

Allowed changes: none.

Forbidden changes: Dexie migrations, message schema edits, deleting or renaming stored keys.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
grep -n "function createThread" src/lib/chat-persistence.ts
grep -n "function listThreads" src/lib/chat-persistence.ts
grep -n "modelProfileId" src/lib/chat-db.types.ts
git status --branch --short
```

Expected outcome: existing thread CRUD and optional `modelProfileId` are visible; no files changed.

Next increment title: Increment 0.3: Inventory Model Routing

Rollback notes: no rollback; discovery only.

#### Increment 0.3: Inventory Model Routing

Purpose: Map local LLM defaults, model profiles, and cloud availability labels before UI work.

Files likely touched: none.

Allowed changes: none.

Forbidden changes: changing provider routing, changing default model env, inventing provider labels.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
grep -n "resolveOllamaModelId" src/app/api/spirit/route.ts src/lib/server/model-routing.ts
grep -n "MODEL_PROFILE_ORDER" src/lib/spirit/model-profiles.ts
grep -n "ModelProfileSelector" src/components/chat/ModelProfileSelector.tsx
git status --branch --short
```

Expected outcome: local model/profile code is identified; provider availability remains unchanged.

Next increment title: Increment 0.4: Inventory Workspace And Tests

Rollback notes: no rollback; discovery only.

#### Increment 0.4: Inventory Workspace And Tests

Purpose: Identify repo workspace defaults, Windows bridge constraints, demo references, and available test commands.

Files likely touched: none.

Allowed changes: none.

Forbidden changes: enabling Windows FS, changing allowlists, adding packages, editing tests.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
grep -n "SPIRIT_WINDOWS_FS_ENABLED" src/lib/spirit/tools/windows-workspace-tools.ts
grep -n "\"test:coding-frontend-regression\"" package.json
find src/app/coding src/app/design-demo _reference/dashboardDemo chatDesign -maxdepth 3 -type f | sort
git status --branch --short
```

Expected outcome: Windows bridge is env-gated; repo demo/reference files are identified; no files changed.

Next increment title: Increment 1.1: Route To New Shell Skeleton

Rollback notes: no rollback; discovery only.

### Phase 1: New Shell Foundation

#### Increment 1.1: Route To New Shell Skeleton

Purpose: Introduce the new VoidCore command-center shell as the visual foundation without deep wiring.

Files likely touched: `src/app/coding/page.tsx`, new `src/components/coding/CodingCommandCenterShell.tsx`, optional new focused test.

Allowed changes: route `/coding` to the new shell; keep `CodingCockpitShell` and `CodingAgentInterface` available as references; render left rail, active area, centered composer, compact status, workspace chip, model chip.

Forbidden changes: deleting old wiring, changing BFF routes, changing Source Proxy contracts, wiring apply, final polish.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
npm run lint
npm run typecheck
```

Expected outcome: `/coding` builds with a new shell skeleton; existing backend files remain untouched.

Next increment title: Increment 1.2: Shell Smoke Test

Rollback notes: revert only the route pointer and new shell/test files from this increment.

#### Increment 1.2: Shell Smoke Test

Purpose: Prove the route renders and no backend contract broke while the shell is still static.

Files likely touched: focused component test under `src/components/coding/__tests__`.

Allowed changes: add assertions for shell landmarks, new chat button placeholder, workspace chip, provider chip, compact safety state.

Forbidden changes: broad snapshot tests, visual polish assertions, Source Proxy route mocks beyond render safety.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
cat package.json | grep -n "\"test\"\\|\"typecheck\"\\|\"lint\""
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: focused shell test passes or, if file is not created yet, the implementer stops and creates the smallest relevant test before moving on.

Next increment title: Increment 2.1: Local Chat State

Rollback notes: remove only the new test and shell skeleton from this increment.

### Phase 2: Chat Creation And Chat Switching

#### Increment 2.1: Local Chat State

Purpose: Allow the user to start a new chat inside `/coding` without coding actions.

Files likely touched: `CodingCommandCenterShell.tsx`, optional small chat state helper.

Allowed changes: create in-memory chat records first if Dexie reuse needs a separate step; show chat title and empty state.

Forbidden changes: calling coding routes, invoking `/api/spirit`, writing files, background model calls.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: clicking “New chat” creates a visible active chat with an empty composer state.

Next increment title: Increment 2.2: Two Chat Switching

Rollback notes: remove local chat state additions only.

#### Increment 2.2: Two Chat Switching

Purpose: Make two chats visible and swappable.

Files likely touched: `CodingCommandCenterShell.tsx`, focused test.

Allowed changes: create at least two chat records, update active chat id, preserve per-chat empty state label or draft text.

Forbidden changes: coding actions, backend writes, automatic model responses.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: Chat A and Chat B can both exist; selecting each visibly changes active state and does not merge their UI state.

Next increment title: Increment 2.3: Optional Dexie Persistence Reuse

Rollback notes: revert chat switching state and test changes from this increment.

#### Increment 2.3: Optional Dexie Persistence Reuse

Purpose: Reuse existing chat persistence only after visible local switching works.

Files likely touched: `CodingCommandCenterShell.tsx`, maybe a narrow adapter around `src/lib/chat-persistence.ts`.

Allowed changes: use `createThread`, `listThreads`, `listMessages`, and `saveMessage` if browser availability and tests are stable.

Forbidden changes: Dexie schema migration, destructive thread cleanup, importing unrelated `/chat` shell UI wholesale.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npx vitest run src/lib/chat-persistence.buildTitle.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: chat switching still works; persistence failure degrades honestly instead of crashing.

Next increment title: Increment 3.1: SpiritOS Workspace Default

Rollback notes: remove the persistence adapter and return to local state.

### Phase 3: Workspace/Project Selector

#### Increment 3.1: SpiritOS Workspace Default

Purpose: Show the current SpiritOS repo as the default workspace/project.

Files likely touched: `CodingCommandCenterShell.tsx`, focused test.

Allowed changes: add selector state with SpiritOS selected by default; show repo-local status.

Forbidden changes: filesystem writes, Windows bridge calls, project creation.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: UI clearly says the active workspace is SpiritOS/current repo and that repo work is the default.

Next increment title: Increment 3.2: Windows Project Option

Rollback notes: remove workspace selector state and test assertions.

#### Increment 3.2: Windows Project Option

Purpose: Add a visible future path toward `C:\Projects` without unsafe writes.

Files likely touched: `CodingCommandCenterShell.tsx`, maybe a read-only availability helper.

Allowed changes: show `C:\Projects` option as unavailable, bridge-gated, or read/list-only depending on existing env-backed support.

Forbidden changes: enabling Windows FS, changing allowlist, writing to Windows paths, pretending access is configured.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npx vitest run src/lib/spirit/tools/__tests__/windows-workspace-tools.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: selector can move toward `C:\Projects`; status honestly says unavailable, bridge-gated, or read/list-only.

Next increment title: Increment 3.3: Start New Project Placeholder

Rollback notes: remove Windows option UI/helper only.

#### Increment 3.3: Start New Project Placeholder

Purpose: Expose “Start new project” honestly without creating anything.

Files likely touched: `CodingCommandCenterShell.tsx`, focused test.

Allowed changes: add disabled or dry-run option with clear status text.

Forbidden changes: directory creation, template writes, package installs, Windows mutation.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: user can see “Start new project”; UI states it is not wired for real creation yet.

Next increment title: Increment 4.1: Provider Availability Model

Rollback notes: remove placeholder option.

### Phase 4: Model/Provider Selector

#### Increment 4.1: Provider Availability Model

Purpose: Add honest local/GPT availability state before any coding route depends on it.

Files likely touched: `CodingCommandCenterShell.tsx`, possible `src/lib/coding/model-provider-status.ts`.

Allowed changes: local default label; GPT/cloud option marked configured, unavailable, or needs configuration based on existing env/status contracts.

Forbidden changes: changing model routing, claiming cloud use without a call, hardcoding fake availability.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npx vitest run src/lib/server/__tests__/model-routing.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: local LLM is default where supported; GPT/cloud can be selected only with honest availability messaging.

Next increment title: Increment 4.2: Payload Intent Visibility

Rollback notes: remove provider state/helper and selector assertions.

#### Increment 4.2: Payload Intent Visibility

Purpose: Make selected provider intent visible without running coding actions.

Files likely touched: `CodingCommandCenterShell.tsx`, focused test.

Allowed changes: show compact “will request local” or “will request GPT/cloud when configured” intent chip; store selected provider per active chat if chat state exists.

Forbidden changes: invoking GPT/cloud, changing `/api/spirit`, changing Source Proxy route fields without contract proof.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: switching provider changes visible intent and never says a route was used before it was actually used.

Next increment title: Increment 5.1: Coding Mode Flag

Rollback notes: remove provider intent chip/state only.

### Phase 5: Coding Mode Entry Point

#### Increment 5.1: Coding Mode Flag

Purpose: Turn one chat into a coding task context without calling apply.

Files likely touched: `CodingCommandCenterShell.tsx`, focused test.

Allowed changes: add “Coding mode” entry; show task fields or scoped composer state for the active chat.

Forbidden changes: applying diffs, executing approved actions, hidden mutation, coding route calls on mount.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: one chat can enter coding mode; other chats can remain normal empty chats.

Next increment title: Increment 5.2: Preview-Only Route Wiring

Rollback notes: remove coding-mode state and UI.

#### Increment 5.2: Preview-Only Route Wiring

Purpose: Wire composer to the existing preview/draft path only.

Files likely touched: `CodingCommandCenterShell.tsx`, focused test, maybe extraction from `CodingCockpitShell`.

Allowed changes: call `/v1/decisions/prompt-packet` and `/v1/verification/diff-preview` with existing safe payload shape; show blocked/unavailable state honestly.

Forbidden changes: `/v1/actions/execute-approved`, apply buttons, approval bypass, backend route edits, fake successful preview.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx src/lib/coding/__tests__/proxy-route-payload.test.ts
```

Expected outcome: coding preview request is possible or honestly blocked; no apply action appears.

Next increment title: Increment 6.1: Approval Gate Display

Rollback notes: remove preview wiring and return to coding-mode placeholder.

### Phase 6: Approval/Safety Workflow Wiring

#### Increment 6.1: Approval Gate Display

Purpose: Show preview, blocker, approval-available, and safety status in the new shell.

Files likely touched: `CodingCommandCenterShell.tsx`, possible safety status component, tests.

Allowed changes: reuse `approval-gate-binding` logic and existing preview payload parsing.

Forbidden changes: enabling apply from failed gates, changing gate criteria, broad backend edits.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npx vitest run src/components/coding/__tests__/approval-gate-binding.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: unsafe or blocked preview remains blocked; approval state is visible but does not apply.

Next increment title: Increment 6.2: Apply After Proven Approval

Rollback notes: remove safety status component/state from this increment.

#### Increment 6.2: Apply After Proven Approval

Purpose: Connect apply only after preview and approval state are proven in the new shell.

Files likely touched: `CodingCommandCenterShell.tsx`, tests.

Allowed changes: call existing `/v1/actions/execute-approved` only when an approved diff, task id or approved route contract, target, and approval state exist.

Forbidden changes: apply without approval, self-approval, commit/push, branch/worktree creation, Source Proxy authority changes.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npx vitest run src/app/v1/actions/execute-approved/__tests__/route.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: approved safe action still requires approval; unsafe action remains blocked; apply copy says verification is required after apply.

Next increment title: Increment 6.3: Verification Status

Rollback notes: remove apply button and handler; keep preview wiring.

#### Increment 6.3: Verification Status

Purpose: Surface verify status after apply without hiding errors.

Files likely touched: `CodingCommandCenterShell.tsx`, tests.

Allowed changes: show verification required, passed, failed, or unavailable based on existing long-running task verification responses.

Forbidden changes: treating apply as verified, auto-running destructive checks, fake green statuses.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: verification status is separate from approval and apply.

Next increment title: Increment 7.1: Focused Component Tests

Rollback notes: remove verification display wiring.

### Phase 7: Testing Harness And Manual Terminal Checks

#### Increment 7.1: Focused Component Tests

Purpose: Lock down chat switching, workspace selector, model selector, and safety status.

Files likely touched: `src/components/coding/__tests__/coding-command-center-shell.test.tsx` and any split component tests.

Allowed changes: add focused tests for one behavior at a time.

Forbidden changes: broad brittle snapshots, installing packages, changing production behavior only to satisfy tests.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
npm run typecheck
```

Expected outcome: tests prove chat switching, workspace selector, model selector, and safety status independently.

Next increment title: Increment 7.2: Coding Regression Checks

Rollback notes: revert only the tests from this increment if unstable.

#### Increment 7.2: Coding Regression Checks

Purpose: Re-run existing safe coding frontend regression after the new shell consumes preview/apply contracts.

Files likely touched: none unless tests reveal a scoped fix.

Allowed changes: update command docs or targeted tests only if route labels changed intentionally.

Forbidden changes: weakening safety tests, skipping failed assertions without a replacement.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run test:coding-frontend-regression
```

Expected outcome: existing approval, payload, client fallback, and proxy safety tests pass or failures are triaged before polish.

Next increment title: Increment 7.3: Route Smoke Check

Rollback notes: revert the shell wiring increment that caused regression.

#### Increment 7.3: Route Smoke Check

Purpose: Check `/coding` route only after the route is stable.

Files likely touched: none unless smoke reveals a scoped route/render fix.

Allowed changes: run browser/manual checks when tooling exists.

Forbidden changes: installing Playwright or browsers in this plan without approval, treating screenshots as passed when tooling is absent.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
cat package.json | grep -n "\"dev\"\\|\"test\""
npm run lint
npm run typecheck
# Optional only if available in the environment:
# npx playwright test tests/e2e/coding-ui.spec.mjs --project=chromium
```

Expected outcome: lint/typecheck pass; browser route smoke is either run and recorded or explicitly blocked by missing tooling.

Next increment title: Increment 8.1: Mobile Structure Pass

Rollback notes: revert the smallest route/render change that caused failure.

### Phase 8: Mobile-First And Final Polish

#### Increment 8.1: Mobile Structure Pass

Purpose: Make the working shell usable on small screens after wiring passes.

Files likely touched: `CodingCommandCenterShell.tsx`, CSS/module/style file if introduced, focused tests.

Allowed changes: mobile rail drawer, centered composer constraints, compact status layout, no-overlap fixes.

Forbidden changes: backend features, model routing changes, final animation pass.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run lint
npm run typecheck
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: mobile layout preserves chat switching, workspace/model selectors, and safety status without adding backend behavior.

Next increment title: Increment 8.2: VoidCore Visual Pass

Rollback notes: revert style/layout changes only.

#### Increment 8.2: VoidCore Visual Pass

Purpose: Apply the VoidCore glass/bubble visual language only after shell and wiring pass.

Files likely touched: shell component and local styles.

Allowed changes: spacing, glass surfaces, chips, transitions, density, icons, active states.

Forbidden changes: new backend features, new route authority, hiding safety status, changing workflow logic.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
npm run lint
npm run typecheck
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Expected outcome: base shell still works; polish does not change safety behavior or hide provider/workspace honesty.

Next increment title: Increment 8.3: Browser Viewport Proof

Rollback notes: revert visual styles only.

#### Increment 8.3: Browser Viewport Proof

Purpose: Confirm final desktop/mobile usability with real route rendering.

Files likely touched: e2e test only if labels intentionally changed.

Allowed changes: update smoke tests to match the new command-center labels if the app behavior is correct.

Forbidden changes: installing packages without approval, accepting viewport proof without a real browser run, changing product behavior to satisfy stale text.

Manual check copy-paste block:

```bash
cd /home/source/SpiritOS
cat package.json | grep -n "playwright\\|test"
# Optional only if @playwright/test and browser binaries are available:
# npx playwright test tests/e2e/coding-ui.spec.mjs
git diff --check
```

Expected outcome: viewport proof is either recorded with real tooling or marked blocked; no fake pass.

Next increment title: Stop for operator review

Rollback notes: revert only e2e label updates or the final visual pass that broke route usability.

## D. Strict Sequencing Rule

- Do not polish before shell, chat switching, workspace selector, model selector, and coding preview are wired.
- Do not wire coding apply before preview and approval state are proven.
- Do not add project creation until project selection is honest and safe.
- Do not add autonomous behavior in this plan.
- Do not weaken or bypass Source Proxy safety gates.
- Do not move hidden mutation, background writes, self-approval, commit, push, merge, branch/worktree creation, cleanup, or stash into the UI.

## E. Manual Checks

Reusable manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git status --branch --short
git diff --check
cat package.json | grep -n "\"lint\"\\|\"typecheck\"\\|\"test\""
npm run lint
npm run typecheck
# Pick the focused command or commands that match the current increment:
npx vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
npx vitest run src/components/coding/__tests__/approval-gate-binding.test.ts
npx vitest run src/lib/coding/__tests__/proxy-route-payload.test.ts
npx vitest run src/lib/spirit/tools/__tests__/windows-workspace-tools.test.ts
npx vitest run src/lib/server/__tests__/model-routing.test.ts
# Use this broader regression only after preview/apply contracts are wired:
npm run test:coding-frontend-regression
# Use browser checks only after route stability and tooling verification:
cat package.json | grep -n "playwright\\|@playwright/test"
# If @playwright/test and browser binaries are available:
# npx playwright test tests/e2e/coding-ui.spec.mjs
```

Expected outcome: the selected increment has one runnable check block, the result is recorded honestly, and missing optional tooling is marked blocked instead of treated as a pass.

Next increment title: the next named increment in this plan.

## F. Expected Output Style

Every implementation increment should leave the repo in a manually checkable state. Before moving to the next increment, the operator should be able to say exactly one of these:

- The route renders.
- A new chat can be created.
- Two chats can be created and swapped.
- SpiritOS is the selected workspace.
- `C:\Projects` is honestly unavailable, bridge-gated, or read/list-only.
- “Start new project” is visible but not pretending to create anything.
- Local model is default where supported.
- GPT/cloud is selectable only with honest availability.
- Coding mode exists for one chat.
- Preview is possible or honestly blocked.
- Approval remains separate from apply.
- Apply, when later wired, requires approval and verification remains separate.

Avoid vague output such as “improve UX” or “enhance shell.” Each increment must produce one observable behavior and one small test/manual check.

## G. Closeout And Stop Point

Current docs-only planning update manual check copy-paste block:

```bash
cd /home/source/SpiritOS
git diff --check
git status --branch --short
```

Expected outcome: only the requested plan documentation is changed by this increment; whitespace validation passes; no code implementation, commit, push, merge, branch/worktree creation, cleanup, stash, or Source Proxy contract edit occurred.

Next increment title: Increment 1.1: Route To New Shell Skeleton

Recommended first implementation increment title:

Increment 1.1: Route To New Shell Skeleton

Clear stop point:

Stop after this planning document is reviewed. Do not start implementation until the operator explicitly approves the first implementation increment.

Operator approval required:

Please approve `Increment 1.1: Route To New Shell Skeleton` before Codex starts code implementation.
