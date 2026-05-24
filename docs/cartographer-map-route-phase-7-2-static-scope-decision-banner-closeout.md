# Cartographer Map Route Phase 7.2 Static Scope Decision Banner Closeout

Status date: 2026-05-22

## Files Changed

- `src/app/map/page.tsx`
- `docs/cartographer-map-route-phase-7-2-static-scope-decision-banner-closeout.md`

## What Changed

- Added a static `Read-only scope decision` section to `/map`.
- Made the current decision visible: data wiring remains unapproved.
- Listed the future conditions for named GET endpoints, placeholder fallback, display-only rollback, and blocked mutation routes.

## What It Does Not Do

- Does not wire read-only data.
- Does not call GET endpoints.
- Does not call POST endpoints.
- Does not add buttons or click handlers.
- Does not edit backend routes, dashboard widgets, `/coding`, package files, runtime files, config, env, generated, or Scout files.
- Does not grant full auto or limited unattended operation.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx

grep -n "Read-only scope decision\|Data wiring remains unapproved\|Decision pending\|Future wiring needs named GET endpoints\|Mutation routes remain blocked" \
  src/app/map/page.tsx

grep -n "fetch(\|sourceProxyFetch\|proxyCartographer\|onClick\|<button" src/app/map/page.tsx || true

git status --short -- \
  src/app/map/page.tsx \
  docs/cartographer-map-route-phase-7-1-read-only-data-wiring-scope-decision-closeout.md \
  docs/cartographer-map-route-phase-7-2-static-scope-decision-banner-closeout.md \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx \
  package.json \
  src/app/coding/page.tsx \
  src/app/v1/decisions/prompt-packet/route.ts
```

## Expected Output

- `git diff --check` prints nothing.
- Focused ESLint prints nothing.
- Scope decision grep shows the static unapproved data-wiring banner.
- Fetch/button/click grep prints nothing.
- `git status --short -- ...` shows Phase 7 files plus already-dirty untouched files.

## Rollback Notes

- Remove `readOnlyScopeDecision`.
- Remove the static read-only scope decision section.
- Remove this closeout document.

## Stop Conditions

- Any actual data wiring is added.
- Any action endpoint becomes callable.
- Any forbidden lane file must be edited.

## Next Recommended Increment Title

Map Route Phase 8.1: Final Inert Route Closeout
