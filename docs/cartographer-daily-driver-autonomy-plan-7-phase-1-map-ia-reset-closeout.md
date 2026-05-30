# Cartographer Daily Driver Autonomy Plan 7 Phase 1 Map IA Reset Closeout

## Scope

Plan 7 Phase 1 reset `/map` from a dense static wall into simple operational sections.

Allowed files touched:

- `src/app/map/page.tsx`
- `src/app/map/map-information-architecture.ts`
- `src/app/map/__tests__/map-information-architecture.test.ts`
- `docs/cartographer-daily-driver-autonomy-plan-7-phase-1-map-ia-reset-closeout.md`
- `docs/cartographer-daily-driver-autonomy-plan-7-new-chat-handoff.md`

## Implemented

- Replaced the prior long `/map` layout with a simpler Cartographer cockpit.
- Added operational sections:
  - Current State
  - Approvals
  - Queue
  - Workflows
  - Receipts And Evidence
  - What Britton Needs To Verify
  - Debug Source Health
- Kept live-state and approval-token display read-only.
- Kept queue/workflow/receipt panels as visible homes for later Plan 7 phases without adding new authority.
- Added a focused IA test for section order, operator questions, and no-authority messaging.

## Boundaries Preserved

- No backend changes.
- No new API clients beyond existing read-only `/map` modules.
- No approval minting.
- No self-approval.
- No queue execution controls.
- No safe writes.
- No command execution.
- No commit, push, branch, checkout, reset, clean, or stash controls.
- No hidden blocker reasons or source health state.

## Verification

```bash
cd /home/source/SpiritOS
npm test -- run src/app/map/__tests__/map-information-architecture.test.ts
npm run typecheck
git diff --check
git status --branch --short
```

Focused result:

- `src/app/map/__tests__/map-information-architecture.test.ts`: 3 passed.
