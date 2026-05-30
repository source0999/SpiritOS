# Cartographer Map Route Phase 12.1 Read-Only Wiring Go/No-Go Operator Decision

Status date: 2026-05-22

## Operator Decision

No-go.

Read-only data wiring is not approved in this phase.

## Reason

The current lane is still preserving an inert `/map` manual-control surface. A future go decision must name the exact GET endpoints, fallback behavior, timeout policy, cache policy, rollback scope, and verification commands.

## What Remains Allowed

- Static `/map` route display.
- Static manual-control planning sections.
- Static read-only candidate inventory.
- Static mutation boundary inventory.
- Main SpiritOS navbar access to `/map`.
- Documentation-only planning for future read-only wiring.

## What Remains Forbidden

- Real endpoint calls.
- `fetch`, `sourceProxyFetch`, or `proxyCartographer` usage in `/map`.
- POST endpoints.
- Buttons or click handlers in `/map`.
- Approval, apply, commit, push, branch, queue execution, command execution, or kill switch mutation.
- Full auto.
- Limited unattended operation.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

grep -n "Operator Decision\|No-go\|Read-only data wiring is not approved\|What Remains Forbidden\|Limited unattended operation" \
  docs/cartographer-map-route-phase-12-1-read-only-wiring-go-no-go-operator-decision.md

grep -n "fetch(\|sourceProxyFetch\|proxyCartographer\|onClick\|<button" src/app/map/page.tsx || true

git status --short -- \
  docs/cartographer-map-route-phase-12-1-read-only-wiring-go-no-go-operator-decision.md \
  src/app/map/page.tsx \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx \
  package.json \
  src/app/coding/page.tsx \
  src/app/v1/decisions/prompt-packet/route.ts
```

## Expected Output

- `git diff --check` prints nothing.
- Decision grep shows no-go, data wiring not approved, forbidden scope, and limited unattended operation denial.
- Fetch/button/click grep prints nothing.
- `git status --short -- ...` shows this decision doc plus existing `/map` lane files and already-dirty untouched files.

## Rollback Notes

- Remove this decision document.

## Stop Conditions

- Any live data wiring is implemented.
- Any mutation-capable action becomes available.
- Any forbidden lane file must be edited.

## Next Recommended Increment Title

Map Route Phase 12.2: Add Static No-Go Decision Record
