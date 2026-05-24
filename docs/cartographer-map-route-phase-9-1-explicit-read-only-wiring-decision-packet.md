# Cartographer Map Route Phase 9.1 Explicit Read-Only Wiring Decision Packet

Status date: 2026-05-22

## Decision State

Read-only wiring is not approved yet.

This packet exists so a later operator decision can approve or reject an exact display-only wiring scope without mixing in mutation controls.

## Candidate Scope For Later Approval

- `/v1/cartographer/status`
- `/v1/cartographer/repo-map`
- `/v1/cartographer/blueprints`
- `/v1/cartographer/proposals`
- `/v1/cartographer/v1-evidence`
- `/v1/cartographer/audit-trail`

## Required Conditions Before Wiring

- The operator names the exact GET endpoints.
- The UI remains renderable when every endpoint is unavailable.
- Missing data displays placeholder, unavailable, or empty states.
- Data reads use display-only semantics.
- Rollback removes only read-only display wiring.
- No POST endpoint is called.

## Explicitly Excluded

- Approval recording.
- Apply approved changes.
- Commit approval or commit execution.
- Push approval or push execution.
- Branch approval.
- Queue execution.
- Command execution.
- Kill switch mutation.
- Durable queue storage.
- Approval token flows.
- Full auto.
- Limited unattended operation.

## What This Packet Does Not Do

- Does not approve read-only data wiring.
- Does not edit `/map`.
- Does not call backend endpoints.
- Does not edit API routes.
- Does not edit dashboard widgets, `/coding`, package, runtime, config, env, generated, or Scout files.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

grep -n "Read-only wiring is not approved yet\|Candidate Scope For Later Approval\|Required Conditions Before Wiring\|Explicitly Excluded\|Limited unattended operation" \
  docs/cartographer-map-route-phase-9-1-explicit-read-only-wiring-decision-packet.md

grep -n "fetch(\|sourceProxyFetch\|proxyCartographer\|onClick\|<button" src/app/map/page.tsx || true

git status --short -- \
  docs/cartographer-map-route-phase-9-1-explicit-read-only-wiring-decision-packet.md \
  src/app/map/page.tsx \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx \
  package.json \
  src/app/coding/page.tsx \
  src/app/v1/decisions/prompt-packet/route.ts
```

## Expected Output

- `git diff --check` prints nothing.
- Decision packet grep shows unapproved state, candidate scope, required conditions, excluded actions, and limited unattended operation denial.
- Fetch/button/click grep prints nothing.
- `git status --short -- ...` shows this doc, prior `/map` lane files, navbar, and already-dirty untouched files.

## Rollback Notes

- Remove this decision packet.

## Stop Conditions

- Any data wiring is implemented.
- Any mutation-capable route is approved or exposed.
- Any forbidden lane file must be edited.

## Next Recommended Increment Title

Map Route Phase 9.2: Add Static Decision Packet Summary
