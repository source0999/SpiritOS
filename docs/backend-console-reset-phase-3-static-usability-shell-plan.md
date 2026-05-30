# Backend Console Reset Phase 3: Static Usability Shell Plan

- status: planning-only
- implementation: not started
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- previous increment: `docs/backend-console-reset-phase-2-plain-page-flow-design.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document plans a future static replacement shell for `/proxy-backend` with no data wiring and no executable controls.

This is a docs-only increment. It does not edit `src/app/proxy-backend/page.tsx`, `/coding`, `/map`, dashboard files, backend runtime files, `source_proxy`, package/config/env/generated/test files, or Cartographer full-auto roadmap implementation files.

## Static Shell Goal

The future shell should be readable before live data exists.

It should:

- answer what the Backend Console is for
- show backend-facing status areas as static or `planned, not wired`
- route the user to the correct lane
- identify blocked and intentionally unavailable capabilities
- keep debug detail lower on the page
- avoid fake controls
- avoid runtime calls

It should not:

- call a backend action endpoint
- add `onClick` execution behavior
- add start, stop, restart, apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete controls
- imply autonomy is enabled
- become a dashboard clone
- become a coding console
- become a Cartographer control center

## Proposed Static Shell Structure

### Top Area

Content:

- title: `Backend Console`
- description: `Check backend health, proxy status, and safe next actions.`
- compact status strip:
  - `Backend API` with `Planned, not wired`
  - `Source Proxy` with `Planned, not wired`
  - `Ollama/local model` with `Planned, not wired`
  - `Scout` with `Planned, not wired`
  - `/coding` as a normal navigation link
  - `/map` as a normal navigation link

First-screen rule:

- The user should understand that this page is safe, static, and not running checks yet.
- The user should see where to go for coding and Cartographer/manual control.

### System Status

Static rows:

- `Backend API`: `Planned, not wired`
- `Source Proxy`: `Planned, not wired`
- `Ollama/local model`: `Planned, not wired`
- `Scout`: `Planned, not wired`

Row explanation pattern:

```text
Live status is planned for a later read-only wiring decision.
```

Allowed status labels:

- `Healthy`
- `Degraded`
- `Blocked`
- `Offline`
- `Not wired`
- `Planned, not wired`

Phase 3 default label:

```text
Planned, not wired
```

### Safe Checks

Static rows:

- `Backend health check`
- `Proxy reachability check`
- `Local model availability check`
- `Scout/intelligence status check`

Each row should say:

```text
Planned, not wired.
```

Interaction rule:

- Use text rows only.
- Do not use executable buttons.
- Do not add click handlers.
- Do not call endpoints.

### Current Workflows

Static navigation rows:

- `/coding`: coding command center.
- `/map`: Cartographer manual control center.
- dashboard: overview-only.
- Scout/intelligence: optional future route only if approved.

Navigation rule:

- Links are allowed only as lane routing.
- Links must not trigger backend work.
- Links must not make `/proxy-backend` own coding, map, dashboard, or Scout behavior.

### Blocked Or Not Wired

Static rows:

- `Live backend health`: `Planned, not wired`
- `Execution controls`: `Not added`
- `Autonomy controls`: `Not enabled`
- `Read-only data wiring`: `Requires later decision gate`
- `Backend runtime changes`: `Out of scope`

Copy rule:

- Use short labels.
- Keep explanations to one line.
- Do not create a warning wall.

### Debug Notes

Lower-page notes may include:

- current route delegates to `CodingAgentInterface`
- future preferred implementation surface is `src/app/proxy-backend/page.tsx`
- no backend runtime wiring is approved
- protected lanes remain protected

Debug notes should not appear as the main content of the first viewport.

## Implementation Constraints For Later Approval

If a later implementation increment is approved, the first implementation should prefer:

```text
src/app/proxy-backend/page.tsx
```

The future implementation should not edit:

- `src/components/coding/**`
- `src/components/dashboard/**`
- `src/app/coding/**`
- `src/app/map/**`
- `source_proxy/**`
- package/config/env/generated/test files

No new dependency should be required for the static shell.

## Static Content Checklist

Before future implementation begins, confirm:

- all labels are static or clearly marked `Planned, not wired`
- every apparent control is either plain text or a normal navigation link
- no action endpoint is named as callable by the page
- no execution verbs appear as controls
- `/coding` remains only a navigation destination
- `/map` remains only a navigation destination
- dashboard remains overview-only
- backend runtime remains untouched
- autonomy remains disabled and not implied

## Forbidden Files And Actions

Forbidden files and directories:

- `src/app/proxy-backend/page.tsx` during this docs-only increment
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

- Implementing the shell in this increment.
- Adding `onClick` execution behavior.
- Calling backend action endpoints.
- Adding executable buttons.
- Adding start, stop, restart, apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete controls.
- Adding autonomy controls.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if:

- This docs-only plan turns into implementation.
- Any forbidden file changes.
- Any executable button appears in the plan as approved Phase 3 behavior.
- Any backend action endpoint is introduced.
- Any `onClick` execution behavior is introduced.
- Start, stop, restart, apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete controls appear.
- Autonomy is enabled or implied.
- The current dirty worktree can no longer be distinguished from this docs-only increment.

## Manual Verification Commands

```bash
git diff --check
grep -n "Backend Console Reset Phase 3\|planning-only\|/proxy-backend\|Static Shell\|Planned, not wired\|onClick\|action endpoint\|/coding\|/map\|Stop" docs/backend-console-reset-phase-3-static-usability-shell-plan.md
git status --branch --short
git diff --stat
git diff --name-only
```

Expected output:

- `git diff --check` has no output.
- `grep` prints matching lines for the Phase 3 title, planning status, `/proxy-backend`, static shell, `Planned, not wired`, forbidden execution behavior, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new Phase 3 docs file plus pre-existing dirty files and earlier docs-only increments.
- `git diff --stat` shows no implementation-file changes from this increment.
- `git diff --name-only` still lists only tracked pre-existing dirty files, because the docs-only increment files are untracked.

## Next Recommended Increment

Backend Console Reset Phase 4: Copy And Label Simplification
