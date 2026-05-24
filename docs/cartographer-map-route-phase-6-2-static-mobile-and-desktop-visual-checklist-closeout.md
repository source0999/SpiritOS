# Cartographer Map Route Phase 6.2 Static Mobile And Desktop Visual Checklist Closeout

Status date: 2026-05-22

## Files Changed

- `docs/cartographer-map-route-phase-6-2-static-mobile-and-desktop-visual-checklist-closeout.md`

## What Changed

- Added a manual visual checklist for `/map` with the main OS navbar.
- Captured desktop and mobile expectations without adding automated browser checks.
- Kept this increment documentation-only.

## Desktop Visual Checklist

- Main SpiritOS desktop rail is visible on `/map`.
- `Map` nav item is active on `/map`.
- `/map` content is offset from the desktop rail and does not sit underneath it.
- Static section navigation remains visible and usable.
- Cards and chips do not overlap.
- No executable controls are visible in the `/map` content.

## Mobile Visual Checklist

- Main SpiritOS mobile pill nav is visible on `/map`.
- `Map` icon entry is present.
- Fixed mobile nav does not cover the final `/map` content.
- Section cards stack in a readable single-column flow.
- Long endpoint text wraps instead of overflowing.
- No approval, apply, commit, push, or command controls are visible.

## What It Does Not Do

- Does not start a dev server.
- Does not add Playwright or screenshot tests.
- Does not edit CSS.
- Does not edit dashboard widgets.
- Does not wire live data.
- Does not grant full auto or limited unattended operation.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx

grep -n "Desktop Visual Checklist\|Mobile Visual Checklist\|Map.*active\|does not cover the final /map content\|No executable controls" \
  docs/cartographer-map-route-phase-6-2-static-mobile-and-desktop-visual-checklist-closeout.md

grep -n "DashboardDemoV4FloatingNav\|dashboard-demo-v4-route-shell\|dashboard-demo-v4-route-main\|pb-28" \
  src/app/map/page.tsx

grep -n "fetch(\|sourceProxyFetch\|proxyCartographer\|onClick\|<button" src/app/map/page.tsx || true

git status --short -- \
  src/app/map/page.tsx \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx \
  docs/cartographer-map-route-phase-6-1-static-visual-polish-and-navbar-shell-closeout.md \
  docs/cartographer-map-route-phase-6-2-static-mobile-and-desktop-visual-checklist-closeout.md \
  package.json \
  src/app/coding/page.tsx \
  src/app/v1/decisions/prompt-packet/route.ts
```

## Expected Output

- `git diff --check` prints nothing.
- Focused ESLint prints nothing.
- Visual checklist grep shows desktop and mobile manual expectations.
- `/map` grep shows the navbar wrapper and mobile bottom padding.
- Fetch/button/click grep prints nothing.
- `git status --short -- ...` shows Phase 6 files plus already-dirty untouched files.

## Rollback Notes

- Remove this closeout document.

## Stop Conditions

- Visual verification requires CSS changes.
- Visual verification requires dashboard widget changes.
- `/map` needs live data or executable controls.

## Next Recommended Increment Title

Map Route Phase 7.1: Read-Only Data Wiring Scope Decision
