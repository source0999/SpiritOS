# Cartographer Map Route Phase 6.1 Static Visual Polish And Navbar Shell Closeout

Status date: 2026-05-22

## Files Changed

- `src/app/map/page.tsx`
- `docs/cartographer-map-route-phase-6-1-static-visual-polish-and-navbar-shell-closeout.md`

## What Changed

- Added the main SpiritOS navbar to `/map`.
- Imported the existing dashboard nav stylesheet so the desktop rail and mobile pill render correctly.
- Wrapped `/map` content in the existing route shell/main layout classes.
- Added mobile bottom padding so the fixed mobile nav does not cover content.

## What It Does Not Do

- Does not add new navigation components.
- Does not edit dashboard widgets.
- Does not wire live Cartographer data.
- Does not call backend endpoints.
- Does not add buttons or click handlers to `/map`.
- Does not add approval, apply, commit, push, queue execution, command execution, or kill switch mutation controls.
- Does not grant full auto or limited unattended operation.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx

grep -n "DashboardDemoV4FloatingNav\|dashboard-demo-v4.css\|dashboard-demo-v4-route-shell\|dashboard-demo-v4-route-main\|lg:pb-8" \
  src/app/map/page.tsx

grep -n "href: \"/map\"\|label: \"Map\"\|p === \"/map\"\|startsWith(\"/map/\")" \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx

grep -n "fetch(\|sourceProxyFetch\|proxyCartographer\|onClick\|<button" src/app/map/page.tsx || true

git status --short -- \
  src/app/map/page.tsx \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx \
  docs/cartographer-map-route-phase-6-1-static-visual-polish-and-navbar-shell-closeout.md \
  package.json \
  src/app/coding/page.tsx \
  src/app/v1/decisions/prompt-packet/route.ts
```

## Expected Output

- `git diff --check` prints nothing.
- Focused ESLint prints nothing.
- `/map` grep shows the existing navbar component, nav stylesheet, route shell, route main, and mobile padding.
- Navbar grep shows the `/map` nav entry and matcher.
- Fetch/button/click grep prints nothing.
- `git status --short -- ...` shows this phase's `/map` and doc changes plus already-dirty untouched files.

## Rollback Notes

- Remove the `DashboardDemoV4FloatingNav` import from `src/app/map/page.tsx`.
- Remove the dashboard nav stylesheet import from `src/app/map/page.tsx`.
- Remove the route shell/main wrapper and nav component render.
- Remove this closeout document.

## Stop Conditions

- Adding the navbar requires dashboard widget edits.
- `/map` starts requiring live data to render.
- Any action control becomes executable.

## Next Recommended Increment Title

Map Route Phase 6.2: Static Mobile And Desktop Visual Checklist
