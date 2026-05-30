# Backend Console Reset Phase 6: Safe Navigation Links

- status: planning-only
- implementation: not started
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- previous increment: `docs/backend-console-reset-phase-5-section-reduction-and-scroll-control.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document defines safe navigation-link rules for a future `/proxy-backend` usability reset.

The goal is for the backend page to route the user to the right lane instead of blending all lanes into one surface.

This is a docs-only increment. It does not edit `src/app/proxy-backend/page.tsx`, `/coding`, `/map`, dashboard files, Scout runtime files, backend runtime files, `source_proxy`, package/config/env/generated/test files, or Cartographer full-auto roadmap implementation files.

## Navigation Principle

Navigation links are allowed only when they are normal route links.

Links must:

- describe the destination lane clearly
- avoid execution language
- avoid runtime side effects
- keep `/proxy-backend` from owning destination workflows
- remain visually secondary to backend status and next action

Links must not:

- trigger backend checks
- start, stop, restart, apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete anything
- create approval, execution, or autonomy controls
- turn `/proxy-backend` into a coding console
- turn `/proxy-backend` into a Cartographer manual-control center
- turn `/proxy-backend` into a dashboard clone

## Required Navigation Rows

### `/coding`

Label:

```text
Open coding
```

Description:

```text
Coding command center for coding agent workflow.
```

Boundary:

- `/proxy-backend` may link to `/coding`.
- `/proxy-backend` must not own task prompts, plans, previews, approvals, verification, or coding-agent workflow.
- `/proxy-backend` must not import or edit coding components during this docs-only increment.

### `/map`

Label:

```text
Open map
```

Description:

```text
Cartographer manual control center.
```

Boundary:

- `/proxy-backend` may link to `/map`.
- `/proxy-backend` must not own manual review, evidence, approval packets, future operator controls, or Cartographer full-auto roadmap behavior.
- `/proxy-backend` must not import or edit map files during this docs-only increment.

### Dashboard

Label:

```text
Open dashboard
```

Description:

```text
Overview-only dashboard.
```

Boundary:

- `/proxy-backend` may link to the dashboard route after implementation approval.
- Dashboard remains overview-only.
- `/proxy-backend` must not reuse dashboard widgets in a way that turns the backend page into a dashboard clone.
- Dashboard implementation files remain protected.

## Optional Future Navigation Row

### Scout/intelligence

Label:

```text
Open Scout
```

Description:

```text
Intelligence view, if a safe route is approved later.
```

Boundary:

- Scout/intelligence navigation is optional.
- It requires an approved destination route.
- It must not touch Scout runtime.
- It must not trigger intelligence jobs or backend execution.

## Link Placement

Navigation should appear in two places at most:

- compact first-screen status/routing strip
- `Current Workflows` section

Avoid repeating the same link in multiple cards or widget grids.

If the page needs fewer links, prefer keeping:

- `/coding`
- `/map`

Dashboard and Scout/intelligence can remain lower-priority or future-only.

## Safe Link Copy

Allowed:

- `Open coding`
- `Open map`
- `Open dashboard`
- `Open Scout`
- `Coding command center`
- `Cartographer manual control center`
- `Overview-only dashboard`

Avoid:

- `Run coding`
- `Start map`
- `Launch autonomous control`
- `Execute dashboard check`
- `Apply Scout action`
- `Approve backend operation`

## Workflow Ownership Rules

`/proxy-backend` may say:

```text
Go to /coding for coding agent workflow.
Go to /map for Cartographer manual control.
Dashboard is overview-only.
```

`/proxy-backend` must not say:

```text
Create a coding plan here.
Approve Cartographer work here.
Run dashboard checks here.
Start autonomous operation here.
```

## Future Implementation Checklist

Before future implementation is accepted, confirm:

- `/coding` link is described as coding command center.
- `/map` link is described as Cartographer manual control.
- dashboard link is described as overview-only.
- optional Scout/intelligence link is clearly future-safe or approved.
- links are normal navigation only.
- links do not trigger execution.
- links do not include mutation verbs.
- no destination implementation files are changed.

## Allowed Future Implementation Surface

After explicit implementation approval, the preferred future surface remains:

```text
src/app/proxy-backend/page.tsx
```

Phase 6 does not approve implementation. It only defines safe navigation-link rules.

## Forbidden Files And Actions

Forbidden files and directories:

- `src/app/proxy-backend/page.tsx` during this docs-only increment
- `/coding` implementation files
- `/map` implementation files
- dashboard implementation files
- Scout runtime files
- backend runtime files
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
- test files
- Cartographer full-auto roadmap implementation files

Forbidden actions:

- Implementing navigation changes in this increment.
- Editing React components.
- Editing destination lane files.
- Adding backend action endpoints.
- Adding executable controls.
- Adding autonomy controls.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if:

- This safe-navigation plan turns into implementation.
- Any forbidden file changes.
- `/proxy-backend` starts owning coding workflow.
- `/proxy-backend` starts owning Cartographer manual controls.
- `/proxy-backend` starts owning dashboard behavior.
- Any unsafe control appears as a navigation item.
- Any link triggers execution instead of navigation.
- Any autonomy control is introduced.
- The current dirty worktree can no longer be distinguished from this docs-only increment.

## Manual Verification Commands

```bash
git diff --check
grep -n "Backend Console Reset Phase 6\|planning-only\|/proxy-backend\|Open coding\|Open map\|Open dashboard\|Overview-only dashboard\|normal navigation\|/coding\|/map\|Stop" docs/backend-console-reset-phase-6-safe-navigation-links.md
git status --branch --short
git diff --stat
git diff --name-only
```

Expected output:

- `git diff --check` has no output.
- `grep` prints matching lines for the Phase 6 title, planning status, `/proxy-backend`, safe link labels, overview-only dashboard, normal navigation, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new Phase 6 docs file plus pre-existing dirty files and earlier docs-only increments.
- `git diff --stat` shows no implementation-file changes from this increment.
- `git diff --name-only` still lists only tracked pre-existing dirty files, because the docs-only increment files are untracked.

## Next Recommended Increment

Backend Console Reset Phase 7: Read-Only Data Wiring Decision Gate
