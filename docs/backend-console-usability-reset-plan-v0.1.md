# Backend Console Usability Reset v0.1

- status: planning-only
- implementation: not started
- target page: /proxy-backend
- priority: usability first
- design priority: plain, understandable, low-scroll, low-widget
- autonomy: not enabled
- execution controls: not added
- /coding lane: protected
- /map lane: protected
- Cartographer full-auto roadmap lane: protected

## Problem Statement

The backend page is hard to use today because it asks the operator to sort through too many widgets, repeated cards, abstract status words, and long scrolling sections. It feels like a mix of dashboard, coding console, modal language, safety warnings, and backend checks instead of one plain operator page.

The page does not need to look final right now. It needs to help the user quickly understand whether the backend is alive, what matters, what is blocked, and where to go next.

## Product Boundary

`/proxy-backend` should answer:

- Is the backend alive?
- What services matter right now?
- What is healthy, degraded, or blocked?
- What can I safely check?
- What should I do next?
- Where do I go for coding?
- Where do I go for Cartographer/manual control?
- What is intentionally not wired?

`/coding` should remain:

- coding command center
- coding agent workflow
- task prompt, plan, preview, approval, verify

`/map` should remain:

- Cartographer manual control center
- manual review
- evidence
- approval packets
- future operator controls

Dashboard should remain:

- overview-only

## Usability Principles

- One screen should tell the user what is going on.
- Fewer cards.
- Fewer widgets.
- No endless repeated sections.
- No fake controls.
- No modal-style wording unless there is actually a modal.
- No "autonomy" language unless needed for a blocked state.
- Plain labels.
- Short explanations.
- Clear next action.
- Mobile usable.
- Desktop readable.
- No glass overload.
- Status first, controls second, detail last.

## Proposed New Information Architecture

### Top Area

- Page title: Backend Console
- One sentence: "Check backend health, proxy status, and safe next actions."
- Status strip:
  - Backend API
  - Source Proxy
  - Ollama/local model
  - Scout
  - /coding link
  - /map link

### Main Sections

1. System Status
   - Simple health rows.
   - Labels: healthy, degraded, blocked, offline.
   - Last checked placeholder if not wired.

2. Safe Checks
   - Show what checks are available later.
   - No executable buttons yet unless a future approved implementation allows them.
   - Placeholder copy should say "planned, not wired".

3. Current Workflows
   - Coding command center link.
   - Cartographer map link.
   - Scout/intelligence link if useful.
   - Short explanation for each.

4. Blocked Or Not Wired
   - List what is intentionally disabled.
   - No scary wall of text.
   - No giant red modal energy.
   - Short, clear reasons.

5. Debug Notes
   - Small collapsible or lower-page area later.
   - Not a giant visible wall by default.

## Things To Remove Or Simplify

- Repeated glass widgets.
- Big nested cards inside cards.
- Abstract "operator" wording where plain wording works.
- Long safety paragraphs on the main view.
- Repeated blocked cards.
- Fake interactive controls.
- Modals that do not help.
- Excessive vertical scroll.
- Overly pretty design that makes the page harder to use.

## Phase Plan

### Phase 0: Baseline And Lane Boundary

Objective: Record the current page state and protect `/coding`, `/map`, dashboard, backend runtime, and full-auto roadmap lanes.

Likely files later:

- `docs/backend-console-usability-reset-plan-v0.1.md`
- `src/app/proxy-backend/page.tsx` only after a later implementation approval

Forbidden files:

- `src/app/coding/page.tsx`
- `src/app/map/page.tsx`
- `src/components/coding/**`
- `src/components/dashboard/**`
- `source_proxy/**`
- package, config, env, generated, Scout, and test files

Manual checks:

- `git status --branch --short`
- `git diff --name-only`
- Confirm existing dirty files are not touched.

Expected output: A written baseline that states the reset is isolated to `/proxy-backend` planning.

Debug path if failed: Stop and compare `git diff --name-only` against the allowed file list.

Stop conditions:

- Any forbidden file changes.
- Any implementation work begins before approval.
- Any autonomy or execution control is introduced.

Next increment title: Backend Console Reset Phase 1: Current Backend Page Inventory

### Phase 1: Current Backend Page Inventory

Objective: Inventory the current `/proxy-backend` page, imports, visible sections, confusing widgets, repeated areas, and unclear flows.

Likely files later:

- `docs/backend-console-usability-reset-plan-v0.1.md`
- Possible future notes doc if approved

Forbidden files:

- React components
- `/coding`
- `/map`
- dashboard widgets
- backend runtime

Manual checks:

- `sed -n '1,260p' src/app/proxy-backend/page.tsx`
- `find src/components -maxdepth 3 -type f | sort | grep -E 'coding|backend|proxy|dashboard|system' || true`
- `find src/app -maxdepth 3 -type f | sort | grep -E 'proxy-backend|coding|map|dashboard' || true`

Expected output: A short inventory of what the page currently depends on and what makes it confusing.

Debug path if failed: Re-run the inventory commands and capture only the relevant page/import facts.

Stop conditions:

- Inventory turns into refactor work.
- Any coding, map, dashboard, or runtime file is edited.

Next increment title: Backend Console Reset Phase 2: Plain Page Flow Design

### Phase 2: Plain Page Flow Design

Objective: Define the simple page structure and exact user journey.

Likely files later:

- `docs/backend-console-usability-reset-plan-v0.1.md`
- Future `/proxy-backend` implementation prompt

Forbidden files:

- Current implementation files until explicit approval
- `/coding`
- `/map`
- dashboard widgets
- runtime files

Manual checks:

- Review the planned top area and main sections.
- Confirm the first screen answers status, next action, and lane routing.

Expected output: A plain page flow: status strip, system status, safe checks, workflows, blocked/not wired, debug notes.

Debug path if failed: Remove sections until the first screen is understandable without scrolling.

Stop conditions:

- The page becomes a dashboard clone.
- The page becomes a coding console.
- The page becomes a Cartographer control center.

Next increment title: Backend Console Reset Phase 3: Static Usability Shell Plan

### Phase 3: Static Usability Shell Plan

Objective: Plan a static replacement shell for `/proxy-backend` with no data wiring and no executable controls.

Likely files later:

- `src/app/proxy-backend/page.tsx` after explicit implementation approval

Forbidden files:

- `src/app/coding/page.tsx`
- `src/app/map/page.tsx`
- `src/components/coding/**`
- `src/components/dashboard/**`
- `source_proxy/**`
- package and config files

Manual checks:

- Confirm labels are static or clearly marked "planned, not wired".
- Confirm no `onClick` execution behavior is introduced.
- Confirm no backend action endpoint is called.

Expected output: A future static shell that is readable before any live data exists.

Debug path if failed: Replace controls with plain text status rows and links only.

Stop conditions:

- New executable buttons appear.
- Start, stop, restart, apply, commit, push, merge, branch, worktree, stash, checkout, clean, or delete controls appear.
- Autonomy is enabled or implied.

Next increment title: Backend Console Reset Phase 4: Copy And Label Simplification

### Phase 4: Copy And Label Simplification

Objective: Replace confusing language with simple labels and short explanations.

Likely files later:

- `src/app/proxy-backend/page.tsx` after explicit implementation approval

Forbidden files:

- `/coding`
- `/map`
- dashboard widgets
- runtime files

Manual checks:

- Search visible copy for modal-like wording.
- Search visible copy for unnecessary autonomy language.
- Confirm each section has one clear job.

Expected output: The page uses plain words like Backend API, Source Proxy, Healthy, Blocked, Not wired, and Next step.

Debug path if failed: Rewrite each label as a sentence a tired operator would understand in five seconds.

Stop conditions:

- Labels become abstract again.
- Safety copy expands into a wall of text.
- The page hides important blocked states behind decorative language.

Next increment title: Backend Console Reset Phase 5: Section Reduction And Scroll Control

### Phase 5: Section Reduction And Scroll Control

Objective: Reduce the page to a few clear sections and move long debug details lower or behind a simple details section.

Likely files later:

- `src/app/proxy-backend/page.tsx` after explicit implementation approval

Forbidden files:

- Shared dashboard layouts
- `/coding`
- `/map`
- backend runtime

Manual checks:

- Desktop route check.
- Mobile viewport check.
- Confirm the first screen shows status and next action.
- Confirm there are no repeated cards that say the same thing.

Expected output: A lower-scroll backend page with one visible status summary and a small number of focused sections.

Debug path if failed: Collapse or remove duplicate sections before adding any styling.

Stop conditions:

- Endless scrolling remains.
- Nested cards dominate the layout.
- Debug details occupy the top of the page.

Next increment title: Backend Console Reset Phase 6: Safe Navigation Links

### Phase 6: Safe Navigation Links

Objective: Add clear navigation paths to `/coding`, `/map`, dashboard, and possibly Scout/intelligence without mixing responsibilities.

Likely files later:

- `src/app/proxy-backend/page.tsx` after explicit implementation approval

Forbidden files:

- `/coding` implementation
- `/map` implementation
- dashboard implementation
- Scout runtime

Manual checks:

- Confirm `/coding` link is described as coding command center.
- Confirm `/map` link is described as Cartographer manual control.
- Confirm dashboard link is overview-only.
- Confirm links do not trigger execution.

Expected output: The backend page routes the user to the right lane instead of blending all lanes into one surface.

Debug path if failed: Replace workflow widgets with short text and normal navigation links.

Stop conditions:

- `/proxy-backend` starts owning coding workflow.
- `/proxy-backend` starts owning Cartographer manual controls.
- Any unsafe control appears as a navigation item.

Next increment title: Backend Console Reset Phase 7: Read-Only Data Wiring Decision Gate

### Phase 7: Read-Only Data Wiring Decision Gate

Objective: Decide later whether safe GET-only health data can be wired. Do not wire it in this plan.

Likely files later:

- Future decision doc
- Future `/proxy-backend` implementation only if approved

Forbidden files:

- Backend runtime until a separate approved wiring plan exists
- Mutation endpoints
- Package and config files

Manual checks:

- List proposed read-only endpoints.
- Confirm each endpoint is GET-only.
- Confirm failure states are visible and harmless.
- Confirm no execution controls are bundled with read-only wiring.

Expected output: A go/no-go decision for read-only health wiring, separate from the static usability reset.

Debug path if failed: Keep the page static and mark live values "planned, not wired".

Stop conditions:

- Any mutation endpoint is proposed.
- Any start/stop/restart or apply-style action is bundled into wiring.
- Approval is unclear.

Next increment title: Backend Console Reset Phase 8: Future Implementation Sequence

### Phase 8: Future Implementation Sequence

Objective: Break the actual page reset into tiny future implementation increments.

Likely files later:

- `src/app/proxy-backend/page.tsx` after explicit implementation approval

Forbidden files:

- `/coding`
- `/map`
- dashboard widgets
- backend runtime
- package/config/env files
- generated files

Manual checks:

- Run checks after each tiny increment.
- Confirm each diff remains limited to approved files.

Expected output:

- Create static shell.
- Simplify copy.
- Reduce sections.
- Add safe nav links.
- Add no-wiring banner.
- Run lint.
- Browser check.
- Mobile check.
- Stop for read-only wiring approval.

Debug path if failed: Revert only the current approved increment by making a new corrective patch; do not touch unrelated dirty files.

Stop conditions:

- Scope expands beyond `/proxy-backend`.
- New dependencies are required.
- Unsafe controls appear.
- The implementation starts changing Cartographer full-auto, `/coding`, `/map`, dashboard, or runtime behavior.

Next increment title: Backend Console Reset Phase 9: Final Verification And Closeout

### Phase 9: Final Verification And Closeout

Objective: Define success checks before the reset is considered done.

Likely files later:

- Final closeout doc if requested
- `src/app/proxy-backend/page.tsx` after approved implementation

Forbidden files:

- Any unrelated lane or runtime file

Manual checks:

- `git diff --check`
- `npx eslint src/app/proxy-backend/page.tsx`
- Browser route check for `/proxy-backend`
- Mobile viewport check for `/proxy-backend`
- Grep for forbidden controls and unsafe language.

Expected output: The reset is complete only when the page is understandable, lower-scroll, lane-safe, and free of unsafe controls.

Debug path if failed: Identify the failing section and fix the smallest approved surface only.

Stop conditions:

- The page cannot be understood quickly.
- `/coding`, `/map`, dashboard, runtime, or full-auto roadmap boundaries are crossed.
- Any execution or autonomy control appears without separate approval.

Next increment title: Backend Console Reset Phase 0.1: Baseline And Lane Boundary

## Acceptance Criteria

The future implemented page should:

- Be understandable in under 30 seconds.
- Have no endless widget scrolling.
- Not use glass cards everywhere.
- Not look like a modal maze.
- Clearly show what is healthy, blocked, or not wired.
- Clearly route the user to `/coding` or `/map`.
- Not expose unsafe controls.
- Not enable autonomy.
- Not mix with full-auto roadmap work.

## Explicit Non-Goals

- Not making the page visually final.
- Not building a beautiful design system.
- Not wiring new backend actions.
- Not enabling start/stop/restart unless separately approved.
- Not editing `/coding`.
- Not editing `/map`.
- Not editing dashboard.
- Not enabling full auto.
- Not enabling limited unattended operation.

## Manual Check Commands For Future Implementation

```bash
git diff --check
npx eslint src/app/proxy-backend/page.tsx
grep -RIn "start\\|stop\\|restart\\|apply\\|commit\\|push\\|merge\\|branch\\|worktree\\|stash\\|checkout\\|clean\\|delete" src/app/proxy-backend/page.tsx
grep -RIn "autonomy\\|unattended\\|execute\\|execution" src/app/proxy-backend/page.tsx
```

Browser route check:

- Open `/proxy-backend`.
- Confirm the page loads.
- Confirm the first viewport shows status and next action.
- Confirm `/coding` and `/map` links are visible and clear.
- Confirm no executable backend controls are present.

Mobile viewport check:

- Check a narrow viewport around 390px wide.
- Confirm status rows wrap cleanly.
- Confirm no text overlaps.
- Confirm the main flow remains readable without horizontal scrolling.

Stop here. Do not implement. Ask operator approval before writing the first implementation prompt.

## Next Recommended Increment

Backend Console Reset Phase 0.1: Baseline And Lane Boundary
