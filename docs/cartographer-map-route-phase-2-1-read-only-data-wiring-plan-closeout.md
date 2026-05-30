# Cartographer Map Route Phase 2.1 Read-Only Data Wiring Plan Closeout

Status date: 2026-05-22

## Files Changed

- `docs/cartographer-map-route-phase-2-1-read-only-data-wiring-plan-closeout.md`

## What Changed

- Inventoried existing Cartographer route methods by reading `src/app/v1/cartographer/**/route.ts`.
- Confirmed Phase 2 remains planning-only and display-only.
- Identified candidate GET routes that may later feed read-only `/map` views.
- Identified POST routes that must remain action-forbidden from `/map`.

## Candidate Read-Only GET Sources

- `/v1/cartographer/status`
- `/v1/cartographer/v1-closeout-dashboard`
- `/v1/cartographer/repo-map`
- `/v1/cartographer/blueprints`
- `/v1/cartographer/proposals`
- `/v1/cartographer/commit-proposals`
- `/v1/cartographer/level-3-commit-proposals`
- `/v1/cartographer/level-3-closeout-readiness`
- `/v1/cartographer/v1-evidence`
- `/v1/cartographer/codex-evidence`
- `/v1/cartographer/audit-trail`
- `/v1/cartographer/docs-autopilot/dry-run`

## Action-Forbidden POST Routes

- `/v1/cartographer/proposals/[proposalId]/review`
- `/v1/cartographer/proposals/[proposalId]/apply-approved`
- `/v1/cartographer/docs-autopilot/apply`
- `/v1/cartographer/branch-recommendations/[recommendationId]/approve`
- `/v1/cartographer/commit-proposals/[commitProposalId]/approve`
- `/v1/cartographer/push-queue/[pushId]/approve`
- `/v1/cartographer/clutter-proposals/[proposalId]/approve`
- `/v1/cartographer/starter-blueprints/[proposalId]/approve`

## What It Does Not Do

- Does not wire data into `/map`.
- Does not edit Cartographer API routes.
- Does not call backend endpoints.
- Does not create data helpers.
- Does not add approval, apply, commit, push, command execution, queue execution, or kill switch mutation controls.
- Does not grant full auto or limited unattended operation.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

grep -R "export async function \\(GET\\|POST\\|PUT\\|DELETE\\|PATCH\\)" -n src/app/v1/cartographer | sort

grep -n "Candidate Read-Only GET Sources\|Action-Forbidden POST Routes\|Does not wire data into /map\|Does not grant full auto or limited unattended operation" \
  docs/cartographer-map-route-phase-2-1-read-only-data-wiring-plan-closeout.md

git status --short -- \
  docs/cartographer-map-route-phase-2-1-read-only-data-wiring-plan-closeout.md \
  src/app/map/page.tsx \
  src/app/v1/cartographer \
  src/app/coding/page.tsx \
  src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx \
  package.json \
  src/app/v1/decisions/prompt-packet/route.ts
```

## Expected Output

- `git diff --check` prints nothing.
- Method inventory shows GET candidates and POST mutation routes.
- Closeout grep shows the read-only and action-forbidden boundaries.
- `git status --short -- ...` shows this new doc and prior `/map` lane files, with existing forbidden-lane dirty files unchanged.

## Rollback Notes

- Remove this closeout document.

## Stop Conditions

- A backend route must be edited.
- `/map` needs a real fetch to complete this phase.
- Any POST route is wired into UI.
- Any action authority is granted.

## Next Recommended Increment Title

Map Route Phase 2.2: Add Static Read-Only Source Inventory
