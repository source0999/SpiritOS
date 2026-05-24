# Backend Console Reset Phase 1: Current Backend Page Inventory

- status: planning-only
- implementation: not started
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- previous increment: `docs/backend-console-reset-phase-0-1-baseline-and-lane-boundary.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document records the current `/proxy-backend` page inventory before any usability implementation begins.

This is a docs-only increment. No React components, route implementations, runtime files, dashboard files, `/coding`, `/map`, `source_proxy`, package/config/env/generated/test files, or Cartographer full-auto roadmap files are changed.

## Current Route Inventory

Inspected command:

```bash
sed -n '1,260p' src/app/proxy-backend/page.tsx
```

Current file contents:

```tsx
import CodingAgentInterface from "@/components/coding/CodingAgentInterface";

export default function ProxyBackendPage() {
  return (
    <main className="min-h-dvh bg-slate-950">
      <CodingAgentInterface layoutMode="backend-console" />
    </main>
  );
}
```

Route-level findings:

- `/proxy-backend` has no standalone backend-console shell today.
- `/proxy-backend` imports `CodingAgentInterface` from the protected coding component lane.
- `/proxy-backend` passes `layoutMode="backend-console"` into that coding component.
- The route-level wrapper only sets `min-h-dvh` and `bg-slate-950`.
- Any visible page sections, widgets, status labels, controls, or repeated areas are currently hidden behind the imported coding component.

## Dependency And Boundary Inventory

Inspected command:

```bash
find src/components -maxdepth 3 -type f | sort | grep -E 'coding|backend|proxy|dashboard|system' || true
```

Relevant component paths found:

```text
src/components/coding/CodingAgentInterface.tsx
src/components/coding/CodingCockpitShell.tsx
src/components/coding/CodingCommandCenterShell.tsx
src/components/coding/__tests__/approval-gate-binding.test.ts
src/components/coding/__tests__/client-fallback.test.ts
src/components/coding/__tests__/coding-cockpit-shell.test.tsx
src/components/coding/__tests__/coding-command-center-shell.test.tsx
src/components/coding/__tests__/coding-workflow-step.test.ts
src/components/coding/__tests__/proxy-safety-smoke.test.ts
src/components/coding/approval-gate-binding.ts
src/components/dashboard/DashboardClient.tsx
src/components/dashboard/DashboardWidgetCard.tsx
src/components/dashboard/HomelabBackendHealthCard.tsx
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/components/dashboard/HomelabStatusBadge.tsx
src/components/dashboard/HomelabSystemStatsCard.tsx
src/components/dashboard/HomelabTestRunnerWidget.tsx
src/components/dashboard/ScoutIntelligenceCenter.tsx
src/components/dashboard/demo-v4/DashboardDemoV4.tsx
src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx
src/components/system/ClientFailSafe.tsx
```

Boundary findings:

- The current backend page directly depends on a coding component.
- Several dashboard/backend/status-adjacent components exist, but they are outside the allowed implementation surface for this reset unless separately approved.
- The dirty worktree already includes protected coding, dashboard, and `source_proxy` work. This increment does not inspect their internals or change them.
- A future `/proxy-backend` implementation should avoid pulling more behavior from `/coding`, `/map`, dashboard, or runtime lanes unless a later plan explicitly allows it.

## App Route Inventory

Inspected command:

```bash
find src/app -maxdepth 3 -type f | sort | grep -E 'proxy-backend|coding|map|dashboard' || true
```

Relevant app paths found:

```text
src/app/(dashboard)/error.tsx
src/app/(dashboard)/layout.tsx
src/app/(dashboard)/loading.tsx
src/app/(dashboard)/page.tsx
src/app/coding/__tests__/page.test.tsx
src/app/coding/design-demo/page.tsx
src/app/coding/page.tsx
src/app/design-demo/coding/page.tsx
src/app/map/page.tsx
src/app/map/read-only-map-data.ts
src/app/proxy-backend/page.tsx
```

Route-boundary findings:

- `/proxy-backend`, `/coding`, `/map`, and dashboard routes exist as separate lanes.
- `/proxy-backend` currently crosses into the `/coding` component lane through its import.
- `/map` has its own route and read-only map data file; those are protected from this reset.
- Dashboard routes are separate and remain overview-only for this reset.

## Visible Page Inventory Status

The visible backend console cannot be fully inventoried from `src/app/proxy-backend/page.tsx` alone because the page delegates rendering to `CodingAgentInterface`.

To keep Phase 1 docs-only and lane-safe:

- No coding component internals were edited.
- No dashboard component internals were edited.
- No `/map` internals were edited.
- No backend runtime internals were edited.
- This document records the route-level dependency as the main inventory finding.

Future implementation should either:

- replace the route-level wrapper with a plain static `/proxy-backend` shell after explicit approval, or
- create a separately approved deeper inventory of `CodingAgentInterface` before changing shared coding behavior.

## Current Usability Risks

- The target backend page is not independent at the route level.
- The backend-console experience is coupled to a coding workflow component.
- Backend status, safe checks, lane routing, blocked states, and debug notes are not visible in the route file.
- Any implementation that changes the imported coding component could accidentally affect `/coding`.
- Any reuse of dashboard widgets could accidentally turn `/proxy-backend` into a dashboard clone.
- Any runtime wiring before a decision gate could accidentally introduce unsafe controls.

## Allowed Future Implementation Surface

After explicit approval, the preferred implementation surface is:

```text
src/app/proxy-backend/page.tsx
```

The future page should be a plain, static or read-only backend console shell unless later increments explicitly approve more.

Allowed future concepts:

- Backend Console title and one-sentence purpose.
- Simple status strip.
- System status rows.
- Safe Checks section marked `planned, not wired`.
- Current Workflows section with normal links to `/coding`, `/map`, dashboard, and possibly Scout/intelligence if approved.
- Blocked Or Not Wired section.
- Small lower-page Debug Notes area.

## Forbidden Files And Actions

Forbidden files and directories:

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

- Editing implementation files during this docs-only increment.
- Reading deeper protected internals as a substitute for implementation approval.
- Adding executable backend controls.
- Adding autonomy controls.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if:

- Inventory turns into refactor work.
- Any `/coding`, `/map`, dashboard, runtime, `source_proxy`, package/config/env/generated/test, or Cartographer full-auto roadmap file is edited.
- Any executable control is introduced.
- Any autonomy behavior is enabled or implied.
- The current dirty worktree makes it impossible to identify this docs-only increment.

## Manual Verification Commands

```bash
git diff --check
grep -n "Backend Console Reset Phase 1\|planning-only\|/proxy-backend\|CodingAgentInterface\|/coding\|/map\|Stop" docs/backend-console-reset-phase-1-current-backend-page-inventory.md
git status --branch --short
git diff --stat
```

Expected output:

- `git diff --check` has no output.
- `grep` prints matching lines for the Phase 1 title, planning status, `/proxy-backend`, `CodingAgentInterface`, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new docs file plus pre-existing dirty files.
- `git diff --stat` shows no implementation-file changes from this increment.

## Next Recommended Increment

Backend Console Reset Phase 2: Plain Page Flow Design
