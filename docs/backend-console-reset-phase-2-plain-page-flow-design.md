# Backend Console Reset Phase 2: Plain Page Flow Design

- status: planning-only
- implementation: not started
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- previous increment: `docs/backend-console-reset-phase-1-current-backend-page-inventory.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the plain page flow for the Backend Console usability reset before any implementation begins.

The goal is to make `/proxy-backend` understandable quickly: what is alive, what matters, what is blocked, what is not wired, and where the user should go next.

This is a docs-only increment. It does not edit `src/app/proxy-backend/page.tsx`, `/coding`, `/map`, dashboard files, backend runtime files, `source_proxy`, package/config/env/generated/test files, or Cartographer full-auto roadmap implementation files.

## Flow Principle

The page should read from top to bottom in this order:

1. What page am I on?
2. Is the backend okay enough to trust?
3. What services matter right now?
4. What can I safely check?
5. Where should I go for coding or manual control work?
6. What is blocked or intentionally not wired?
7. Where are the low-priority debug details?

If the first viewport does not answer status, next action, and lane routing, the flow is too complicated.

## First Viewport Design

The first viewport should include:

- Page title: `Backend Console`
- Short purpose sentence: `Check backend health, proxy status, and safe next actions.`
- One compact status strip:
  - `Backend API`
  - `Source Proxy`
  - `Ollama/local model`
  - `Scout`
  - `/coding`
  - `/map`
- One clear next-action line.

The first viewport should not include:

- Long safety paragraphs.
- Nested cards.
- Dashboard-style widget grids.
- Coding workflow controls.
- Cartographer manual-control panels.
- Execution buttons.
- Autonomy controls.

## Section Order

### 1. System Status

Job: show whether the backend-facing services are healthy, degraded, blocked, offline, or not wired.

Rows:

- `Backend API`
- `Source Proxy`
- `Ollama/local model`
- `Scout`

Allowed labels:

- `Healthy`
- `Degraded`
- `Blocked`
- `Offline`
- `Not wired`
- `Planned, not wired`

Each row should have one short explanation. If live data is not approved, the row should clearly say `planned, not wired`.

### 2. Safe Checks

Job: show what checks may exist later without pretending they work now.

Rows:

- `Backend health check`
- `Proxy reachability check`
- `Local model availability check`
- `Scout/intelligence status check`

Phase 2 rule: these are planned rows, not executable controls.

Copy rule:

- Use `Planned, not wired`.
- Do not use button language.
- Do not imply a command will run.

### 3. Current Workflows

Job: route the user to the right lane without blending lanes into `/proxy-backend`.

Rows:

- `/coding`: coding command center for coding agent workflow, task prompt, plan, preview, approval, and verify.
- `/map`: Cartographer manual control center for manual review, evidence, approval packets, and future operator controls.
- dashboard: overview-only.
- Scout/intelligence: optional future link only if approved.

Navigation should be normal links only. Links must not trigger backend actions.

### 4. Blocked Or Not Wired

Job: make intentional non-capabilities obvious without turning the page into a warning wall.

Rows:

- Live backend health data: `planned, not wired`.
- Execution controls: `not added`.
- Autonomy controls: `not enabled`.
- Read-only data wiring: `requires later decision gate`.
- Backend runtime changes: `out of scope`.

Copy should be short, plain, and specific.

### 5. Debug Notes

Job: keep low-priority implementation detail available without dominating the page.

Placement:

- lower page only, or
- future simple details section if implementation approval allows it.

Content:

- route currently delegates to `CodingAgentInterface`
- future implementation surface is expected to be `src/app/proxy-backend/page.tsx`
- protected lanes remain `/coding`, `/map`, dashboard, backend runtime, `source_proxy`, and Cartographer full-auto roadmap files

## User Journey

Expected operator path:

1. Open `/proxy-backend`.
2. Read the title and purpose sentence.
3. Scan the status strip for backend, proxy, model, and Scout state.
4. Read the next-action line.
5. Use `/coding` only for coding workflow.
6. Use `/map` only for Cartographer/manual control workflow.
7. Check `Blocked Or Not Wired` if something appears unavailable.
8. Ignore debug notes unless troubleshooting.

The page should not require the user to understand Cartographer full-auto planning, dashboard widget structure, or coding agent internals.

## Lane Boundary Rules

`/proxy-backend` owns:

- backend health overview
- proxy status overview
- safe next-action guidance
- lane routing
- not-wired explanations

`/proxy-backend` does not own:

- coding agent workflow
- Cartographer manual control workflow
- dashboard overview widgets
- backend runtime behavior
- command execution
- autonomy
- read-only data wiring before a later decision gate

## Failure Patterns To Avoid

- The page becomes a dashboard clone.
- The page becomes a coding console.
- The page becomes a Cartographer control center.
- The first viewport becomes decorative instead of useful.
- Status rows are repeated across multiple sections.
- Planned checks look like executable buttons.
- Debug notes dominate the main page.
- Copy uses abstract modal or autonomy language where plain labels work.

## Allowed Future Implementation Surface

After explicit implementation approval, the preferred future surface remains:

```text
src/app/proxy-backend/page.tsx
```

Phase 2 does not approve implementation. It only defines the planned flow.

## Forbidden Files And Actions

Forbidden files and directories:

- `src/app/proxy-backend/page.tsx` during this docs-only increment
- `src/app/coding/page.tsx`
- `src/app/coding/**`
- `src/app/map/page.tsx`
- `src/app/map/**`
- `src/components/coding/**`
- `src/components/dashboard/**`
- `source_proxy/**`
- package files
- config files
- env files
- generated files
- Scout files
- test files
- dashboard files
- backend runtime files
- Cartographer full-auto roadmap implementation files

Forbidden actions:

- Implementing the flow.
- Editing React components.
- Adding backend action endpoints.
- Adding executable controls.
- Adding autonomy controls.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if:

- This flow design turns into implementation.
- Any forbidden file changes.
- `/proxy-backend` is planned as a dashboard clone.
- `/proxy-backend` is planned as a coding console.
- `/proxy-backend` is planned as a Cartographer control center.
- Any executable backend control is introduced.
- Any autonomy control is introduced.
- The current dirty worktree can no longer be distinguished from this docs-only increment.

## Manual Verification Commands

```bash
git diff --check
grep -n "Backend Console Reset Phase 2\|planning-only\|/proxy-backend\|First Viewport\|System Status\|Safe Checks\|Current Workflows\|/coding\|/map\|Stop" docs/backend-console-reset-phase-2-plain-page-flow-design.md
git status --branch --short
git diff --stat
git diff --name-only
```

Expected output:

- `git diff --check` has no output.
- `grep` prints matching lines for the Phase 2 title, planning status, `/proxy-backend`, first viewport, main sections, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new Phase 2 docs file plus pre-existing dirty files and earlier docs-only increments.
- `git diff --stat` shows no implementation-file changes from this increment.
- `git diff --name-only` still lists only tracked pre-existing dirty files, because the new docs-only files are untracked.

## Next Recommended Increment

Backend Console Reset Phase 3: Static Usability Shell Plan
