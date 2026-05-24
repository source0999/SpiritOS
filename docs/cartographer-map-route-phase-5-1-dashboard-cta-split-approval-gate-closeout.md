# Cartographer Map Route Phase 5.1 Dashboard CTA Split Approval Gate Closeout

Status date: 2026-05-22

## Files Changed

- `src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx`
- `docs/cartographer-map-route-phase-5-1-dashboard-cta-split-approval-gate-closeout.md`

## What Changed

- Added `/map` to the main SpiritOS navbar.
- Used a static `Map` nav item that routes to the inert Cartographer Manual Control Center.
- Preserved the existing dirty `showMobile` navbar changes.
- Kept dashboard widget CTA work behind a future approval gate.

## What It Does Not Do

- Does not edit dashboard widgets.
- Does not add a dashboard card CTA.
- Does not wire real Cartographer data.
- Does not call backend endpoints.
- Does not add apply, commit, push, approval, command execution, queue execution, or kill switch controls.
- Does not grant full auto or limited unattended operation.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx

grep -n "href: \"/map\"\|label: \"Map\"\|p === \"/map\"\|startsWith(\"/map/\")" \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx

grep -n "Read-only wiring approval gate\|Mutation boundary inventory\|Static verification checklist\|Full auto is not granted" \
  src/app/map/page.tsx

grep -n "fetch(\|sourceProxyFetch\|proxyCartographer\|onClick\|<button" src/app/map/page.tsx || true

git status --short -- \
  src/app/map/page.tsx \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx \
  docs/cartographer-map-route-phase-5-1-dashboard-cta-split-approval-gate-closeout.md \
  package.json \
  src/app/coding/page.tsx \
  src/app/v1/decisions/prompt-packet/route.ts
```

## Expected Output

- `git diff --check` prints nothing.
- Focused ESLint prints nothing.
- Navbar grep shows the `/map` nav entry and active-route matcher.
- `/map` grep shows the inert guardrail sections remain present.
- Fetch/button/click grep prints nothing.
- `git status --short -- ...` shows the navbar file, `/map`, this doc, and already-dirty untouched files.

## Rollback Notes

- Remove the `Map` import and `/map` entry from `NAV`.
- Remove this closeout document.

## Stop Conditions

- Dashboard widgets need to change.
- Adding navigation requires data wiring or backend changes.
- Any live control becomes executable.

## Next Recommended Increment Title

Map Route Phase 5.2: Main Navbar Manual Verification Closeout
