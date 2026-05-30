# Backend Console Reset Phase 0.1: Baseline And Lane Boundary

- status: planning-only
- implementation: not started
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document records the Phase 0.1 baseline for the Backend Console usability reset. It is intentionally docs-only and does not start implementation.

The reset is scoped to planning for `/proxy-backend`. It must not change `/coding`, `/map`, dashboard files, backend runtime files, `source_proxy`, package/config/env/generated/test files, or any Cartographer full-auto roadmap implementation lane.

## Lane Status

- `/coding`: protected. Existing dirty work is present and must not be touched by this increment.
- `/map`: protected. Existing untracked route work is present and must not be touched by this increment.
- dashboard: protected. Existing dirty dashboard work is present and must not be touched by this increment.
- backend runtime: protected. No runtime implementation, command execution, service wiring, or backend behavior changes are allowed in this increment.
- Cartographer full-auto roadmap: protected. Existing docs and `source_proxy` work are present and must not be touched by this increment.

## Current Dirty Worktree Summary

Baseline command results at the start of this increment:

```text
## main...origin/main [ahead 34]
 M docs/plan-index.md
 M package.json
 M src/app/coding/page.tsx
 M src/app/v1/decisions/prompt-packet/route.ts
 M src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx
?? docs/backend-console-usability-reset-plan-v0.1.md
?? docs/cartographer-*.md
?? docs/coding-command-center-voidcore-*.md
?? source_proxy/cartographer/*.py
?? source_proxy/tests/*.py
?? src/app/coding/__tests__/
?? src/app/map/
?? src/app/v1/decisions/prompt-packet/__tests__/
?? src/components/coding/CodingCommandCenterShell.tsx
?? src/components/coding/__tests__/coding-command-center-shell.test.tsx
?? src/lib/coding/__tests__/model-provider-status.test.ts
?? src/lib/coding/model-provider-status.ts
```

Tracked dirty-file stat at baseline:

```text
 docs/plan-index.md                                 |   1 +
 package.json                                       |   2 +-
 src/app/coding/page.tsx                            |   4 +-
 src/app/v1/decisions/prompt-packet/route.ts        | 148 ++++++++++++++++++++-
 .../demo-v4/DashboardDemoV4FloatingNav.tsx         |  70 +++++-----
 5 files changed, 191 insertions(+), 34 deletions(-)
```

Tracked dirty files at baseline:

```text
docs/plan-index.md
package.json
src/app/coding/page.tsx
src/app/v1/decisions/prompt-packet/route.ts
src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx
```

These dirty files were already present and are intentionally not touched by this Phase 0.1 increment.

## Current `/proxy-backend` Route Summary

Current file inspected:

```text
src/app/proxy-backend/page.tsx
```

Current route shape:

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

Summary:

- `/proxy-backend` currently imports `CodingAgentInterface` from the coding component lane.
- The page renders a full-height dark `<main>` wrapper.
- The visible backend console behavior is delegated to `CodingAgentInterface` through `layoutMode="backend-console"`.
- This Phase 0.1 document does not inspect or edit the imported component.
- No backend runtime behavior is changed.

## Allowed Future Implementation Surface

Future implementation may only begin after explicit approval in a later increment.

Likely future implementation surface:

- `src/app/proxy-backend/page.tsx`

Potential future work must stay focused on `/proxy-backend` usability:

- Plain backend status overview.
- Clear backend, proxy, local model, and workflow routing states.
- Static or read-only planned check descriptions unless later approved otherwise.
- Short blocked/not-wired explanations.
- No execution controls unless a later approved plan explicitly adds them.

## Forbidden Files And Actions

Forbidden files and directories:

- `src/app/coding/page.tsx`
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
- `/coding`
- `/map`
- dashboard files
- backend runtime files
- Cartographer full-auto roadmap implementation files

Forbidden actions:

- Implementing UI or runtime behavior in this increment.
- Editing `src/app/proxy-backend/page.tsx` in this increment.
- Adding backend execution controls.
- Adding autonomy controls or autonomy language beyond documenting blocked/protected lanes.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if any of the following occur:

- A forbidden file changes.
- Any implementation work begins before approval.
- Any `/coding`, `/map`, dashboard, backend runtime, `source_proxy`, package/config/env/generated/test, or Cartographer full-auto roadmap lane is edited.
- Any execution control is introduced.
- Any autonomy control is introduced.
- The dirty worktree cannot be distinguished from this docs-only increment.

Debug path if stopped:

```bash
git status --branch --short
git diff --name-only
git diff --stat
```

Compare changed files against the allowed file list and stop before making further edits.

## Manual Verification Commands

Run:

```bash
git diff --check
grep -n "Backend Console Reset Phase 0.1\|planning-only\|/proxy-backend\|/coding\|/map\|Stop" docs/backend-console-reset-phase-0-1-baseline-and-lane-boundary.md
git status --branch --short
git diff --stat
```

Expected verification result:

- `git diff --check` reports no whitespace errors.
- `grep` finds the title, planning status, `/proxy-backend`, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new docs file plus pre-existing dirty files.
- `git diff --stat` shows only tracked dirty files plus this new docs file if it is tracked by diff display after creation.

## Next Recommended Increment

Backend Console Reset Phase 1: Current Backend Page Inventory
