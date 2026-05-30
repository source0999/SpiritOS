# Backend Console Reset Phase 5: Section Reduction And Scroll Control

- status: planning-only
- implementation: not started
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- previous increment: `docs/backend-console-reset-phase-4-copy-and-label-simplification.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines the section reduction and scroll-control rules for a future `/proxy-backend` usability reset.

The goal is a lower-scroll backend page with one visible status summary and a small number of focused sections.

This is a docs-only increment. It does not edit `src/app/proxy-backend/page.tsx`, `/coding`, `/map`, dashboard files, backend runtime files, `source_proxy`, package/config/env/generated/test files, or Cartographer full-auto roadmap implementation files.

## Scroll-Control Goal

The future page should answer the main operator questions before the user scrolls:

- What page is this?
- Is anything clearly healthy, blocked, offline, or not wired?
- What should I do next?
- Where do I go for coding?
- Where do I go for Cartographer/manual control?

Long explanations, debug notes, and implementation detail should not occupy the top of the page.

## Section Budget

The future page should use five main sections at most:

1. Top status summary
2. System Status
3. Safe Checks
4. Current Workflows
5. Blocked Or Not Wired

Optional lower-page content:

- Debug Notes

No other top-level sections should be added unless a later plan removes or merges an existing section.

## First-Screen Requirements

The first screen should include:

- `Backend Console`
- one short purpose sentence
- compact status summary
- one `Next step` line
- visible `/coding` and `/map` routing

The first screen should not include:

- repeated status cards
- dashboard widget grids
- coding workflow panels
- Cartographer control panels
- long debug notes
- long safety paragraphs
- nested cards
- executable controls
- autonomy controls

## Section Reduction Rules

### Merge Duplicate Status

If two areas describe the same service state, keep only one.

Example:

- Keep: one `Backend API` row in `System Status`.
- Remove or merge: a second `Backend API` card elsewhere.

### Keep Safe Checks Static

`Safe Checks` should remain a short planned list until a later wiring decision.

Allowed rows:

- `Backend health check`
- `Proxy reachability check`
- `Local model availability check`
- `Scout/intelligence status check`

Each row should remain `Planned, not wired`.

### Keep Workflows Short

`Current Workflows` should route the user. It should not become a dashboard or command center.

Allowed rows:

- `/coding`: coding command center
- `/map`: Cartographer manual control center
- dashboard: overview-only
- Scout/intelligence: optional future route only if approved

### Move Debug Details Lower

Debug details belong after the main user-facing sections.

Allowed debug facts:

- current route delegates to `CodingAgentInterface`
- future preferred implementation surface is `src/app/proxy-backend/page.tsx`
- live data wiring requires a later decision gate
- protected lanes remain protected

Debug notes should not be the first or second section.

## Card And Layout Rules

Use restrained section blocks.

Avoid:

- cards inside cards
- large repeated card grids
- decorative widget clusters
- oversized warning panels
- dashboard-style tiles for every row
- long columns of similar-looking blocks

Prefer:

- one compact status strip
- simple rows
- short section headings
- small grouped lists
- lower-page debug notes

## Desktop Check Plan

Future implementation should be checked on desktop for:

- title and purpose visible without scrolling
- status summary visible without scrolling
- `Next step` visible without scrolling
- `/coding` and `/map` routing visible without scrolling
- no repeated cards saying the same thing
- debug notes lower on the page

## Mobile Check Plan

Future implementation should be checked on mobile for:

- title and purpose visible at the top
- status summary still readable
- `Next step` visible early
- `/coding` and `/map` routing visible before debug notes
- no horizontal overflow
- no oversized card stack before useful information appears

## Duplication Checklist

Before future implementation is accepted, confirm:

- `Backend API` appears as one status row or one summary item, not repeated across multiple cards.
- `Source Proxy` appears as one status row or one summary item, not repeated across multiple cards.
- `Ollama/local model` appears as one status row or one summary item, not repeated across multiple cards.
- `Scout` appears as one status row or one summary item, not repeated across multiple cards.
- `Planned, not wired` appears where needed but does not become a wall of identical cards.
- blocked states are visible once in a dedicated section.

## Allowed Future Implementation Surface

After explicit implementation approval, the preferred future surface remains:

```text
src/app/proxy-backend/page.tsx
```

Phase 5 does not approve implementation. It only defines section and scroll-control rules.

## Forbidden Files And Actions

Forbidden files and directories:

- `src/app/proxy-backend/page.tsx` during this docs-only increment
- shared dashboard layouts
- `src/app/coding/page.tsx`
- `src/app/coding/**`
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
- dashboard files
- backend runtime files
- Cartographer full-auto roadmap implementation files

Forbidden actions:

- Implementing layout changes in this increment.
- Editing React components.
- Adding dashboard layouts.
- Adding backend action endpoints.
- Adding executable controls.
- Adding autonomy controls.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if:

- This section plan turns into implementation.
- Any forbidden file changes.
- Endless scrolling remains accepted as the target design.
- Nested cards dominate the target layout.
- Debug details occupy the top of the target page.
- `/proxy-backend` becomes a dashboard clone.
- `/proxy-backend` becomes a coding console.
- `/proxy-backend` becomes a Cartographer control center.
- Any executable backend control is introduced.
- Any autonomy control is introduced.
- The current dirty worktree can no longer be distinguished from this docs-only increment.

## Manual Verification Commands

```bash
git diff --check
grep -n "Backend Console Reset Phase 5\|planning-only\|/proxy-backend\|Section Budget\|First-Screen Requirements\|Desktop Check\|Mobile Check\|nested cards\|Debug Notes\|/coding\|/map\|Stop" docs/backend-console-reset-phase-5-section-reduction-and-scroll-control.md
git status --branch --short
git diff --stat
git diff --name-only
```

Expected output:

- `git diff --check` has no output.
- `grep` prints matching lines for the Phase 5 title, planning status, `/proxy-backend`, section budget, first-screen requirements, desktop/mobile checks, nested-card warning, debug notes, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new Phase 5 docs file plus pre-existing dirty files and earlier docs-only increments.
- `git diff --stat` shows no implementation-file changes from this increment.
- `git diff --name-only` still lists only tracked pre-existing dirty files, because the docs-only increment files are untracked.

## Next Recommended Increment

Backend Console Reset Phase 6: Safe Navigation Links
