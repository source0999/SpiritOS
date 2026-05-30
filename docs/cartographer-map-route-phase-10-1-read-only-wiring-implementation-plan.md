# Cartographer Map Route Phase 10.1 Read-Only Wiring Implementation Plan

Status date: 2026-05-22

## Status

Planning-only. Read-only wiring is still not implemented.

## Purpose

Define the smallest future implementation shape for read-only `/map` data wiring without approving the wiring in this increment.

## Proposed Future File Scope

- `src/app/map/page.tsx`
- Optionally one read-only helper under `src/lib/cartographer-map/` if explicitly approved later
- Focused tests only after behavior exists

## Proposed Future Data Scope

- `/v1/cartographer/status`
- `/v1/cartographer/repo-map`
- `/v1/cartographer/blueprints`
- `/v1/cartographer/proposals`
- `/v1/cartographer/v1-evidence`
- `/v1/cartographer/audit-trail`

## Required Implementation Rules

- Use GET-only display reads.
- Keep `/map` renderable when every read fails.
- Preserve the existing static placeholders as fallbacks.
- Treat unavailable data as an empty, unavailable, or not wired state.
- Do not call POST routes.
- Do not add approval, apply, commit, push, queue execution, command execution, or kill switch controls.
- Do not edit backend/API routes.
- Do not grant full auto or limited unattended operation.

## Verification Plan For Future Wiring

- `git diff --check`
- Focused lint for `/map` and any new helper
- Grep for forbidden action controls
- Grep for POST-capable endpoint strings in executable code
- Browser check that `/map` renders with backend unavailable

## What This Increment Does Not Do

- Does not wire data.
- Does not call endpoints.
- Does not edit `/map`.
- Does not edit backend/API routes.
- Does not add tests, dependencies, package scripts, or generated files.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

grep -n "Planning-only\|Read-only wiring is still not implemented\|Required Implementation Rules\|Do not call POST routes\|Do not grant full auto or limited unattended operation" \
  docs/cartographer-map-route-phase-10-1-read-only-wiring-implementation-plan.md

grep -n "fetch(\|sourceProxyFetch\|proxyCartographer\|onClick\|<button" src/app/map/page.tsx || true

git status --short -- \
  docs/cartographer-map-route-phase-10-1-read-only-wiring-implementation-plan.md \
  src/app/map/page.tsx \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx \
  package.json \
  src/app/coding/page.tsx \
  src/app/v1/decisions/prompt-packet/route.ts
```

## Expected Output

- `git diff --check` prints nothing.
- Plan grep shows planning-only status, implementation rules, POST denial, and autonomy denial.
- Fetch/button/click grep prints nothing.
- `git status --short -- ...` shows this plan plus existing `/map` lane files and already-dirty untouched files.

## Rollback Notes

- Remove this plan document.

## Stop Conditions

- Any actual data wiring is required.
- Any backend/API route must be edited.
- Any mutation control is introduced.

## Next Recommended Increment Title

Map Route Phase 10.2: Add Static Implementation Plan Summary
