# Backend Console Reset Phase 8: Future Implementation Sequence

- status: planning-only
- implementation: not started
- parent plan: `docs/backend-console-usability-reset-plan-v0.1.md`
- previous increment: `docs/backend-console-reset-phase-7-read-only-data-wiring-decision-gate.md`
- target page: `/proxy-backend`
- current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This document breaks the future Backend Console page reset into tiny implementation increments.

This is a docs-only increment. It does not edit `src/app/proxy-backend/page.tsx`, `/coding`, `/map`, dashboard files, backend runtime files, `source_proxy`, package/config/env/generated/test files, or Cartographer full-auto roadmap implementation files.

## Implementation Gate

Implementation is not approved by this document.

Before any implementation begins, require explicit approval for:

```text
Backend Console Reset implementation Phase A: Static Shell
```

No explicit approval means no implementation.

## Preferred Future Implementation Surface

The preferred future implementation surface is:

```text
src/app/proxy-backend/page.tsx
```

The first implementation sequence should avoid:

- shared coding components
- shared dashboard widgets
- `/map` files
- backend runtime files
- package/config/env/generated/test files
- new dependencies

## Future Increment A: Static Shell

Objective:

- Replace the current route-level backend page with a static backend console shell after explicit approval.

Allowed file after approval:

```text
src/app/proxy-backend/page.tsx
```

Expected result:

- page title
- short purpose sentence
- compact static status strip
- `Planned, not wired` labels
- no data wiring
- no executable controls

Manual checks:

```bash
git diff --check
npx eslint src/app/proxy-backend/page.tsx
grep -RIn "onClick\|fetch\|POST\|PUT\|PATCH\|DELETE" src/app/proxy-backend/page.tsx || true
git diff --name-only
```

Stop if:

- any file outside the approved surface changes
- any endpoint call appears
- any executable control appears

## Future Increment B: Copy Simplification

Objective:

- Apply Phase 4 copy rules to the static shell.

Allowed file after approval:

```text
src/app/proxy-backend/page.tsx
```

Expected result:

- plain labels
- short explanations
- no modal-like copy
- autonomy appears only as `Autonomy controls: not enabled`

Manual checks:

```bash
git diff --check
npx eslint src/app/proxy-backend/page.tsx
grep -RIn "operator runtime\|execution plane\|control authority\|autonomous backend\|full-auto controls\|unattended operation" src/app/proxy-backend/page.tsx || true
git diff --name-only
```

Stop if:

- labels become abstract
- safety copy becomes a wall of text
- implementation crosses into `/coding`, `/map`, dashboard, or runtime files

## Future Increment C: Section Reduction

Objective:

- Keep the page to a small number of focused sections.

Allowed file after approval:

```text
src/app/proxy-backend/page.tsx
```

Expected result:

- first viewport shows status and next action
- no repeated status cards
- no nested cards
- debug notes are lower on the page

Manual checks:

```bash
git diff --check
npx eslint src/app/proxy-backend/page.tsx
grep -RIn "Debug Notes\|Backend API\|Source Proxy\|Ollama/local model\|Scout" src/app/proxy-backend/page.tsx
git diff --name-only
```

Stop if:

- endless scrolling remains accepted
- nested cards dominate the layout
- debug notes occupy the top of the page

## Future Increment D: Safe Navigation Links

Objective:

- Add safe normal links to the appropriate lanes.

Allowed file after approval:

```text
src/app/proxy-backend/page.tsx
```

Expected result:

- `/coding` link is described as coding command center
- `/map` link is described as Cartographer manual control
- dashboard link is overview-only if included
- links do not trigger execution

Manual checks:

```bash
git diff --check
npx eslint src/app/proxy-backend/page.tsx
grep -RIn "Open coding\|Open map\|Open dashboard\|href=\"/coding\"\|href=\"/map\"" src/app/proxy-backend/page.tsx
grep -RIn "onClick\|start\|stop\|restart\|apply\|commit\|push\|merge\|branch\|worktree\|stash\|checkout\|clean\|delete" src/app/proxy-backend/page.tsx || true
git diff --name-only
```

Stop if:

- any link triggers execution
- `/proxy-backend` starts owning coding workflow
- `/proxy-backend` starts owning Cartographer manual controls

## Future Increment E: No-Wiring Banner

Objective:

- Add a clear no-wiring or static-data explanation.

Allowed file after approval:

```text
src/app/proxy-backend/page.tsx
```

Expected result:

- live data remains `Planned, not wired`
- read-only wiring remains blocked behind the Phase 7 decision gate
- no endpoint calls

Manual checks:

```bash
git diff --check
npx eslint src/app/proxy-backend/page.tsx
grep -RIn "Planned, not wired\|No explicit go means no wiring\|read-only wiring" src/app/proxy-backend/page.tsx
grep -RIn "fetch\|POST\|PUT\|PATCH\|DELETE" src/app/proxy-backend/page.tsx || true
git diff --name-only
```

Stop if:

- wiring is implied as approved
- endpoint calls appear
- failure states are hidden

## Future Increment F: Browser And Mobile Verification

Objective:

- Verify the implemented static reset manually.

Allowed files after approval:

```text
src/app/proxy-backend/page.tsx
```

Expected result:

- `/proxy-backend` loads
- first viewport shows status and next action
- `/coding` and `/map` links are visible and clear
- no executable backend controls are present
- mobile viewport has no horizontal overflow

Manual checks:

```bash
git diff --check
npx eslint src/app/proxy-backend/page.tsx
git diff --name-only
```

Browser checks:

- Open `/proxy-backend`.
- Confirm the page loads.
- Confirm the first viewport shows status and next action.
- Confirm `/coding` and `/map` links are visible and clear.
- Confirm no executable backend controls are present.
- Confirm mobile viewport is readable and not horizontally overflowing.

Stop if:

- page cannot be understood quickly
- first viewport does not show status and next action
- unsafe controls appear

## Stop Before Read-Only Wiring

After static implementation and verification, stop.

Do not wire read-only data unless a separate future decision explicitly approves it.

Read-only wiring must remain governed by:

```text
docs/backend-console-reset-phase-7-read-only-data-wiring-decision-gate.md
```

## Rollback And Correction Rule

If a future implementation increment fails:

- make a new corrective patch limited to the approved surface
- do not revert unrelated dirty files
- do not touch protected lanes
- do not use staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or worktrees

## Forbidden Files And Actions

Forbidden files and directories for this docs-only increment:

- `src/app/proxy-backend/page.tsx`
- `/coding`
- `/map`
- dashboard widgets
- backend runtime
- package files
- config files
- env files
- generated files
- test files
- `src/app/coding/**`
- `src/app/map/**`
- `src/components/coding/**`
- `src/components/dashboard/**`
- `source_proxy/**`
- Cartographer full-auto roadmap implementation files

Forbidden actions:

- Implementing any future increment now.
- Editing React components.
- Adding dependencies.
- Adding endpoint calls.
- Adding executable controls.
- Adding autonomy controls.
- Staging, committing, pushing, merging, stashing, checking out, cleaning, branching, or using worktrees.

## Stop Conditions

Stop immediately if:

- This implementation sequence turns into implementation.
- Any forbidden file changes.
- Scope expands beyond `/proxy-backend`.
- New dependencies are required.
- Unsafe controls appear.
- Read-only wiring is bundled into static implementation.
- Implementation starts changing Cartographer full-auto, `/coding`, `/map`, dashboard, or runtime behavior.
- The current dirty worktree can no longer be distinguished from this docs-only increment.

## Manual Verification Commands

```bash
git diff --check
grep -n "Backend Console Reset Phase 8\|planning-only\|Implementation Gate\|Static Shell\|Copy Simplification\|Section Reduction\|Safe Navigation Links\|No-Wiring Banner\|Browser And Mobile Verification\|/proxy-backend\|/coding\|/map\|Stop" docs/backend-console-reset-phase-8-future-implementation-sequence.md
git status --branch --short
git diff --stat
git diff --name-only
```

Expected output:

- `git diff --check` has no output.
- `grep` prints matching lines for the Phase 8 title, planning status, implementation gate, future increments, `/proxy-backend`, protected lanes, and Stop conditions.
- `git status --branch --short` shows this new Phase 8 docs file plus pre-existing dirty files and earlier docs-only increments.
- `git diff --stat` shows no implementation-file changes from this increment.
- `git diff --name-only` still lists only tracked pre-existing dirty files, because the docs-only increment files are untracked.

## Next Recommended Increment

Backend Console Reset Phase 9: Final Verification And Closeout
