# Cartographer Map Route Manual Control Plan v0.1

status: planning-only

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Purpose

This plan defines a future Cartographer UI split:

- Dashboard = overview-only.
- `/map` = Cartographer Manual Control Center.

The current dashboard makes Cartographer feel unavailable, cramped, and overblocked because status display, queue review, proposal review, evidence, manual checks, and execution boundaries are all visible in one small dashboard area. The future product structure should make the dashboard glanceable and move detailed manual control to a dedicated `/map` route.

This document is planning-only. It does not implement `/map`, edit dashboard widgets, edit React components, edit backend runtime, enable autonomy, expose execution controls, wire approval actions, add apply/commit/push controls, or change git state.

Limited unattended operation is not granted. Full auto is not granted. No full auto. No limited unattended operation.

## Repository Inventory Notes

Inspected before writing this plan:

- Dashboard components include `src/components/dashboard/HomelabCartographerWidget.tsx` and `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`.
- Dashboard route files live under `src/app/(dashboard)/`.
- No existing `src/app/map/page.tsx` route was found.
- Cartographer API route proxies exist under `src/app/v1/cartographer/`, including status, repo map, proposals, review, apply-approved, commit proposals, push queue, evidence, audit trail, blueprints, and safety-adjacent endpoints.
- Runtime support exists under `source_proxy/cartographer/`, but this plan does not modify it.
- Existing live-operation docs repeatedly preserve documentation-only, read-only, approval-token, command-boundary, dashboard-boundary, no full auto, and no limited unattended operation rules.
- `docs/codingUI.md` is relevant as a precedent for separating an everyday command center from deeper diagnostics, but this plan targets Cartographer and `/map`.

## Global Boundaries

Allowed now:

- Create this plan document.

Allowed later only when explicitly approved:

- Add inert `/map` route shell.
- Simplify dashboard widgets.
- Wire read-only Cartographer state into `/map`.
- Add focused UI tests and visual checks.

Forbidden now and by default:

- Edit `src/app/**`, `src/components/**`, `src/lib/**`, `source_proxy/**`, package/config/env/generated/test files, or dashboard implementation files.
- Enable live autonomy.
- Expose execution controls.
- Add apply, commit, push, merge, stash, checkout, clean, branch, or worktree controls.
- Wire real approval actions.
- Create self-approval paths.
- Grant limited unattended operation or full auto.

## Step 1: Current UI Inventory And Problem Statement

Objective:

Identify the current dashboard Cartographer and Blueprint widgets, describe the overcrowding, and define the dashboard as an overview-only surface.

Files likely to touch later:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`
- `src/components/dashboard/SpiritDashboardHome.tsx`
- Focused dashboard tests under `src/components/dashboard/__tests__/`

Files forbidden in that increment:

- `source_proxy/**`
- `src/app/v1/cartographer/**`
- `package.json`
- `next.config.ts`
- env files
- generated files
- unrelated dashboard, `/coding`, or backend files

Manual checks:

- Inspect the current dashboard at desktop and mobile widths.
- Confirm the Cartographer widget currently includes Level 1, Level 2, Level 3, blockers, manual checks, and execution-boundary messaging.
- Confirm the Blueprint Review widget currently includes queue items, proposal details, diff preview, decision buttons, manual checks, and apply-lane copy.
- Confirm the dashboard feels like a control panel instead of a high-level overview.

Expected output:

- A short UI inventory that names what exists and what is confusing.
- A product statement that dashboard = overview-only.
- A migration list for details that should not live on the dashboard: Level 2 docs apply details, Level 3 commit preview details, approval packet review, proposal queue, manual checks, rollback notes, evidence browser, kill switch details, and operator decision packets.

Debug path if the check fails:

- Re-open the named component files and capture the specific UI sections that contradict the inventory.
- Re-run `find src/components/dashboard -maxdepth 2 -type f | sort` to confirm no renamed widgets were missed.
- Delay design decisions until the inventory matches the actual files.

Stop conditions:

- Any implementation edit is required to complete the inventory.
- The inventory suggests enabling execution or approval actions from the dashboard.
- The dashboard is redefined as the control center.

Next increment title:

Step 2: Product Boundary

## Step 2: Product Boundary

Objective:

Define the split between the dashboard and `/map`.

Files likely to touch later:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`
- `src/components/dashboard/SpiritDashboardHome.tsx`
- `src/app/map/page.tsx`
- Future `/map` component files if an approved implementation plan creates them

Files forbidden in that increment:

- `source_proxy/**`
- `src/app/v1/cartographer/**`
- `src/lib/**`
- package/config/env/generated files
- tests outside the exact UI surface being implemented

Manual checks:

- Verify the dashboard can answer only: What is Cartographer's status? What autonomy level is visible? Is the kill switch on? How many reviews are queued? What was the last evidence or receipt state? Where do I open `/map`?
- Verify `/map` is the only future place for detailed manual control, queue review, evidence review, and operator decisions.
- Verify dashboard = overview appears in the implementation notes and review checklist.

Expected output:

- Dashboard cards show only:
  - Cartographer status.
  - Current autonomy level.
  - Kill switch state.
  - Review queue count.
  - Last evidence/receipt state.
  - Button/link to open `/map`.
- `/map` holds the detailed Cartographer Manual Control Center.

Debug path if the check fails:

- Remove any dashboard field that requires long explanation, manual verification text, packet review, or action-lane detail.
- Move any proposal/approval/evidence detail to the `/map` IA.
- Keep only compact labels and counts on the dashboard.

Stop conditions:

- Dashboard starts showing every Level 2 or Level 3 detail again.
- Dashboard exposes apply, commit, push, approval, or queue execution actions.
- `/map` becomes a route for autonomy instead of manual review.

Next increment title:

Step 3: `/map` Route Information Architecture

## Step 3: `/map` Route Information Architecture

Objective:

Plan `src/app/map/page.tsx` as the Cartographer Manual Control Center with a mobile-first information architecture.

Files likely to touch later:

- `src/app/map/page.tsx`
- Future `src/components/map/**` or `src/components/cartographer/**` files if separately approved
- Future focused tests for `/map`

Files forbidden in that increment:

- Existing dashboard widgets unless the increment is explicitly scoped to navigation only.
- `source_proxy/**`
- `src/app/v1/cartographer/**`
- package/config/env/generated files
- approval, apply, commit, push, or command runner files

Manual checks:

- Confirm `/map` renders as an inert route shell first.
- Confirm mobile viewport stacks sections in a useful order.
- Confirm details can be scanned without stacked cramped glass cards.
- Confirm no real approval/apply/commit/push action is wired.

Expected output:

- Planned `/map` sections:
  - Overview.
  - Repo map / blueprint map.
  - Manual review queue.
  - Approval packet review.
  - Evidence and receipts.
  - Kill switch and authority state.
  - Read-only observation packet.
  - Future safe write class area, hidden or disabled until safety docs allow it.
- Mobile-first layout requirements:
  - Single-column primary flow on small screens.
  - Sticky or easily reachable section navigation only if it does not obscure content.
  - Short section headings and clear status chips.
  - Long packet details behind expandable panels or tabs.
  - No text overlap, no dashboard-style cramped stacked cards.

Debug path if the check fails:

- Start from an inert static shell with only headings and placeholder empty states.
- Remove any action controls.
- Reduce each section to its minimum status, empty state, and next manual review note.

Stop conditions:

- `/map` needs backend mutation to render.
- `/map` includes execution controls.
- `/map` suggests full auto, limited unattended operation, or self-approval.

Next increment title:

Step 4: Manual Control Model

## Step 4: Manual Control Model

Objective:

Define what manual controls may appear and keep them review-first, blocked-by-default, and separate from execution.

Files likely to touch later:

- `src/app/map/page.tsx`
- Future `/map` UI component files
- Future focused tests verifying blocked/default-disabled states

Files forbidden in that increment:

- `source_proxy/cartographer/**`
- `src/app/v1/cartographer/**`
- command execution code
- approval token runtime code
- package/config/env/generated files

Manual checks:

- Confirm every manual control is a review or navigation affordance unless a later safety plan explicitly allows more.
- Confirm approval, apply, commit, and push remain separate concepts.
- Confirm dangerous actions display disabled or blocked states only.
- Confirm no full auto and no limited unattended operation copy exists except as denied capability.

Expected output:

- Allowed controls:
  - Open packet.
  - Expand evidence.
  - Copy/read manual check text.
  - Filter/sort review queue.
  - Navigate between map sections.
  - View blocked action reason.
  - View kill switch and authority state.
- Blocked unless separately approved later:
  - Approval recording.
  - Apply approved docs.
  - Commit.
  - Push.
  - Queue execution.
  - Command execution.
  - Kill switch mutation.
  - Any write class.

Debug path if the check fails:

- Convert unsafe controls to read-only status chips or disabled buttons with concise safety copy.
- Move action design into a future, separately approved safety package.
- Add tests that assert no live action button is enabled.

Stop conditions:

- A UI control can mutate runtime, write files, run commands, approve packets, apply docs, commit, or push.
- Approval and apply appear as one combined flow.
- Any unattended operation is implied.

Next increment title:

Step 5: Dashboard Widget Simplification Plan

## Step 5: Dashboard Widget Simplification Plan

Objective:

Replace the large crowded dashboard widgets with smaller summary widgets.

Files likely to touch later:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`
- `src/components/dashboard/SpiritDashboardHome.tsx`
- Focused dashboard tests

Files forbidden in that increment:

- `src/app/map/page.tsx` unless the `/map` route shell already exists and the increment only adds a link target.
- `source_proxy/**`
- `src/app/v1/cartographer/**`
- package/config/env/generated files
- unrelated dashboard widgets

Manual checks:

- Dashboard screenshot shows compact overview cards instead of detailed Level 2/Level 3 blocks.
- Widget copy uses short human-readable labels.
- The only CTA is `Open Map` or `Review in /map`.
- Giant blocked cards appear only for real critical blockers.
- Voidcore/glass styling remains visually consistent with the surrounding dashboard.

Expected output:

- Cartographer summary widget with compact status, blocker summary, queue count, latest evidence state, and `/map` CTA.
- Blueprint review dashboard surface reduced to high-level queue/review summary or merged into the Cartographer summary if product layout allows.
- No detailed approval/apply/commit/push messaging on the dashboard.

Debug path if the check fails:

- Count visible dashboard sections and remove any section that reads like a packet review.
- Replace repeated blocked copy with one blocker summary.
- Move manual checks and packet details to `/map`.

Stop conditions:

- Dashboard grows back into a control panel.
- Dashboard exposes approval/apply/commit/push controls.
- Visual density remains similar to the current cramped state.

Next increment title:

Step 6: `/map` Visual System Plan

## Step 6: `/map` Visual System Plan

Objective:

Plan `/map` as a spacious, readable control surface that can hold detail without inheriting the cramped dashboard layout.

Files likely to touch later:

- `src/app/map/page.tsx`
- Future `/map` components and style modules if separately approved
- Focused visual and accessibility tests

Files forbidden in that increment:

- Runtime/backend files
- Cartographer execution routes
- package/config/env/generated files
- unrelated dashboard widgets

Manual checks:

- Desktop screenshot has clear hierarchy and breathing room.
- Mobile screenshot has readable stacked sections with no overlap.
- Status chips are legible and concise.
- Manual actions are visually separated from status display.
- Empty states explain what to review next without overexplaining safety docs.

Expected output:

- `/map` visual plan:
  - Overview band with current state.
  - Section navigation or tabs for deep areas.
  - Cards for individual packets only, not cards inside cards.
  - Dedicated evidence and receipt browser area.
  - Dedicated authority/kill switch state area.
  - Disabled future write-class area kept visually subordinate.
  - Readable contrast over glass/Voidcore surfaces.

Debug path if the check fails:

- Remove nested card stacks.
- Increase section spacing and reduce duplicated safety text.
- Convert long warnings into a single blocked status plus details disclosure.

Stop conditions:

- `/map` recreates the dashboard's cramped stacked-card look.
- Status and manual decisions are mixed in one ambiguous control cluster.
- Text overlaps or becomes unreadable at mobile widths.

Next increment title:

Step 7: Data And API Readiness Review

## Step 7: Data And API Readiness Review

Objective:

Identify existing safe read-only endpoints/data sources for `/map`, what is missing, and what must remain fake or placeholder until runtime support exists.

Files likely to touch later:

- Future `/map` data helpers under `src/lib/**` only if separately approved.
- `src/app/map/page.tsx`
- Existing read-only API consumers in UI tests

Files forbidden in that increment:

- `source_proxy/**`
- `src/app/v1/cartographer/**`
- approval/apply/commit/push route implementation files
- package/config/env/generated files

Manual checks:

- List existing endpoints that can feed read-only views without mutation.
- Mark mutation-capable endpoints as display-only sources or forbidden until a future approved plan.
- Confirm missing data is represented as empty, unavailable, or placeholder state.
- Confirm no backend implementation is done.

Expected output:

- Candidate read-only data sources:
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
- Mutation-capable or safety-sensitive endpoints stay unwired for actions:
  - proposal review.
  - apply-approved.
  - docs-autopilot apply.
  - branch recommendation approval.
  - commit proposal approval.
  - push queue approval.
  - autonomy promotion.
- Missing or placeholder until runtime support exists:
  - Unified operator decision packet schema.
  - Durable queue/event ledger view if not already present.
  - Kill switch mutation authority.
  - Approval token detail view.
  - Safe write class runtime readiness.

Debug path if the check fails:

- Remove any endpoint that requires POST or mutation for the first `/map` version.
- Use static placeholder sections with "not wired" copy.
- Require a separate backend-readiness plan before adding new runtime support.

Stop conditions:

- Backend changes are needed.
- A POST endpoint is wired from `/map`.
- Data wiring implies approval, apply, commit, push, or command authority.

Next increment title:

Step 7.5: Dashboard Widget Fix And `/map` Control Split

## Step 7.5: Dashboard Widget Fix And `/map` Control Split

Objective:

Refactor the current dashboard widgets so they become overview-only while detailed manual control moves to `/map`.

Files likely to touch later:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`
- `src/components/dashboard/SpiritDashboardHome.tsx`
- `src/app/map/page.tsx`
- Focused dashboard and `/map` tests

Files forbidden in that increment:

- `source_proxy/**`
- `src/app/v1/cartographer/**`
- `src/lib/**` unless the later approved implementation explicitly scopes a read-only helper
- package/config/env/generated files
- unrelated dashboard, `/coding`, and backend files

Manual checks:

- Dashboard shows only compact status, blocker summary, queue count, latest evidence state, and open `/map` CTA.
- `/map` contains detailed packet, queue, evidence, kill switch, and operator decision surfaces.
- Dashboard screenshot remains useful without becoming the control panel again.
- No approval, apply, commit, push, command execution, or queue execution control is exposed.

Expected output:

- Exactly remains on dashboard:
  - Compact status.
  - Blocker summary.
  - Queue count.
  - Latest evidence state.
  - Open `/map` CTA.
- Exactly moves to `/map`:
  - Level 2 docs apply details.
  - Level 3 commit preview details.
  - Approval packet review.
  - Proposal queue.
  - Manual checks.
  - Rollback notes.
  - Evidence browser.
  - Kill switch details.
  - Operator decision packets.
- No-regression rule:
  - Dashboard must stay useful without becoming the control panel again.
  - New dashboard fields must pass an "overview-only" test: if a field requires a manual decision, a packet review, a long explanation, or an action boundary, it belongs in `/map`.

Debug path if the check fails:

- Remove detailed sections from dashboard until only the five allowed dashboard items remain.
- Add a failing UI test or screenshot checklist item for any reintroduced packet/control-panel content.
- Move the failed content to the appropriate `/map` section instead of deleting the concept.

Stop conditions:

- Dashboard still contains Level 2 or Level 3 detail blocks.
- Dashboard still exposes proposal selection, diff preview, manual check commands, rollback notes, approval decisions, or apply-lane controls.
- `/map` is not available as the home for moved details.

Next increment title:

Step 8: Implementation Sequencing

## Step 8: Implementation Sequencing

Objective:

Break the future implementation into small increments with manual checks and expected outputs.

Files likely to touch later:

- `src/app/map/page.tsx`
- Future `/map` components
- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`
- `src/components/dashboard/SpiritDashboardHome.tsx`
- Focused tests for dashboard and `/map`

Files forbidden in that increment:

- `source_proxy/**`
- `src/app/v1/cartographer/**`
- package/config/env/generated files
- git operation files or scripts
- unrelated UI surfaces

Manual checks:

- Each future implementation increment edits only its declared files.
- Each increment passes `git diff --check`.
- UI increments include screenshot checks.
- Tests are added only once behavior exists to test.
- No execution controls or autonomy appear.

Expected output:

- Future implementation increments:
  1. Create inert `/map` route shell.
  2. Add static `/map` sections.
  3. Add dashboard CTA to `/map`.
  4. Simplify dashboard widgets.
  5. Move detailed Cartographer status blocks into `/map`.
  6. Add read-only data wiring.
  7. Add tests.
  8. Add mobile polish.

Debug path if the check fails:

- Split the failing increment into smaller UI-only and data-only increments.
- Remove mutation-capable wiring.
- Return to static placeholders until route health and layout checks are green.

Stop conditions:

- An increment combines dashboard simplification, route creation, data wiring, and tests in one broad change without need.
- Any increment enables approval, apply, commit, push, command execution, queue execution, full auto, or limited unattended operation.
- Any implementation touches forbidden files.

Next increment title:

Step 9: Final Verification And Release Gate

### Future Increment 1: Create Inert `/map` Route Shell

Objective:

Create `src/app/map/page.tsx` with static, inert headings and empty states only.

Files likely to touch later:

- `src/app/map/page.tsx`

Files forbidden in that increment:

- Dashboard widgets
- `source_proxy/**`
- `src/app/v1/cartographer/**`
- package/config/env/generated files

Manual checks:

- Visit `/map`.
- Confirm the page renders.
- Confirm no fetch, POST, approval, apply, commit, push, or command controls exist.

Expected output:

- Inert route shell.

Debug path if the check fails:

- Remove dynamic imports, fetches, and control affordances.
- Keep only static route markup.

Stop conditions:

- Route shell requires backend changes.

Next increment title:

Future Increment 2: Add Static `/map` Sections

### Future Increment 2: Add Static `/map` Sections

Objective:

Add the planned `/map` sections with static placeholders and blocked empty states.

Files likely to touch later:

- `src/app/map/page.tsx`
- Future `/map` component files if needed

Files forbidden in that increment:

- Dashboard widgets except navigation if separately approved.
- Backend/runtime files.
- package/config/env/generated files.

Manual checks:

- Confirm all planned sections exist.
- Confirm visual hierarchy works on desktop and mobile.
- Confirm future write class area is hidden or disabled.

Expected output:

- Static Manual Control Center layout.

Debug path if the check fails:

- Collapse sections into simpler placeholders.
- Remove nested cards and excessive copy.

Stop conditions:

- Static layout includes live actions.

Next increment title:

Future Increment 3: Add Dashboard CTA To `/map`

### Future Increment 3: Add Dashboard CTA To `/map`

Objective:

Add one clear dashboard CTA: `Open Map` or `Review in /map`.

Files likely to touch later:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`
- Maybe `src/components/dashboard/SpiritDashboardHome.tsx`

Files forbidden in that increment:

- Backend/runtime files.
- Cartographer API routes.
- package/config/env/generated files.

Manual checks:

- Dashboard CTA navigates to `/map`.
- CTA is not styled as an execution button.
- Dashboard remains otherwise unchanged until the simplification increment.

Expected output:

- Safe navigation to `/map`.

Debug path if the check fails:

- Replace button behavior with a plain link.
- Remove any action wording that suggests execution.

Stop conditions:

- CTA triggers approval, apply, commit, push, command execution, or queue execution.

Next increment title:

Future Increment 4: Simplify Dashboard Widgets

### Future Increment 4: Simplify Dashboard Widgets

Objective:

Reduce dashboard widgets to overview-only content.

Files likely to touch later:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/HomelabBlueprintReviewWidget.tsx`
- Focused dashboard tests

Files forbidden in that increment:

- `/map` data wiring.
- Backend/runtime files.
- package/config/env/generated files.

Manual checks:

- Confirm dashboard contains only compact status, blocker summary, queue count, latest evidence state, and `/map` CTA.
- Confirm long Level 2/Level 3 blocks are gone from dashboard.
- Confirm dashboard screenshot is cleaner.

Expected output:

- Clean dashboard overview.

Debug path if the check fails:

- Remove every field not in the five allowed dashboard items.
- Move the removed content into `/map` placeholders.

Stop conditions:

- Dashboard remains visually cramped.

Next increment title:

Future Increment 5: Move Detailed Cartographer Status Blocks Into `/map`

### Future Increment 5: Move Detailed Cartographer Status Blocks Into `/map`

Objective:

Relocate detailed status, blocker, packet, queue, and manual-check views into `/map`.

Files likely to touch later:

- `src/app/map/page.tsx`
- Future `/map` components
- Focused `/map` tests

Files forbidden in that increment:

- Backend/runtime files.
- Mutation-capable API route implementation files.
- package/config/env/generated files.

Manual checks:

- `/map` contains Level 2 details, Level 3 details, approval packets, proposal queue, manual checks, rollback notes, evidence browser, kill switch details, and operator decision packet areas.
- All action controls remain inert, hidden, or disabled unless separately approved later.

Expected output:

- Detailed Cartographer control and review surface lives under `/map`.

Debug path if the check fails:

- Keep moved sections read-only.
- Split oversized sections into separate tabs or subsections.

Stop conditions:

- A moved section becomes an enabled action lane.

Next increment title:

Future Increment 6: Add Read-Only Data Wiring

### Future Increment 6: Add Read-Only Data Wiring

Objective:

Wire safe GET-only Cartographer data into `/map`.

Files likely to touch later:

- `src/app/map/page.tsx`
- Future `/map` components
- Future read-only UI helper files if explicitly approved

Files forbidden in that increment:

- `source_proxy/**`
- `src/app/v1/cartographer/**`
- POST action wiring.
- package/config/env/generated files.

Manual checks:

- Network review shows GET-only calls.
- Error states are readable.
- Missing data uses honest empty states.
- No POST endpoint is called.

Expected output:

- Read-only `/map` data display.

Debug path if the check fails:

- Disable the failing data source.
- Revert to placeholder copy for unsupported data.

Stop conditions:

- Data wiring requires backend changes or mutation calls.

Next increment title:

Future Increment 7: Add Tests

### Future Increment 7: Add Tests

Objective:

Add focused tests for dashboard overview boundaries and `/map` read-only/manual-control boundaries.

Files likely to touch later:

- Dashboard tests under `src/components/dashboard/__tests__/`
- Future `/map` route/component tests

Files forbidden in that increment:

- Runtime/backend files.
- package/config/env/generated files.
- unrelated tests.

Manual checks:

- Tests assert dashboard overview-only content.
- Tests assert `/map` contains manual-control sections without enabled execution controls.
- Tests assert apply/commit/push controls are absent or disabled.

Expected output:

- Focused regression coverage.

Debug path if the check fails:

- Narrow assertions to stable visible labels and safety-critical absences.
- Avoid snapshot-heavy tests for visual layout.

Stop conditions:

- Tests require implementation files outside the approved UI surface.

Next increment title:

Future Increment 8: Add Mobile Polish

### Future Increment 8: Add Mobile Polish

Objective:

Polish `/map` and dashboard behavior across mobile viewports.

Files likely to touch later:

- `/map` UI files
- Dashboard widget files
- Focused visual tests if tooling supports them

Files forbidden in that increment:

- Runtime/backend files.
- package/config/env/generated files.
- unrelated UI surfaces.

Manual checks:

- Mobile dashboard screenshot.
- Mobile `/map` screenshot.
- No overlapping text or controls.
- Section navigation remains reachable.

Expected output:

- Mobile-safe dashboard overview and `/map` manual-control center.

Debug path if the check fails:

- Reduce columns to one.
- Shorten labels.
- Move dense packet detail behind disclosure controls.

Stop conditions:

- Mobile layout hides safety-critical blocked state or creates accidental action affordances.

Next increment title:

Step 9: Final Verification And Release Gate

## Step 9: Final Verification And Release Gate

Objective:

Define readiness checks before future implementation is considered complete.

Files likely to touch later:

- Closeout doc under `docs/`
- Focused UI files and tests from approved implementation increments

Files forbidden in that increment:

- Runtime/backend files unless a separate approved implementation plan explicitly included them.
- package/config/env/generated files.
- unrelated dirty files.

Manual checks:

- Dashboard screenshot check:
  - Dashboard is overview-only.
  - It shows compact status, blocker summary, queue count, latest evidence state, and `/map` CTA.
  - It does not show full packet review or detailed action lanes.
- `/map` screenshot check:
  - `/map` is the Cartographer Manual Control Center.
  - It has overview, map, queue, packet, evidence, receipts, kill switch, authority, observation, and future disabled safe write sections.
- Mobile viewport check:
  - Dashboard and `/map` remain readable with no overlap.
- Safety check:
  - No execution controls exposed.
  - No autonomy enabled.
  - No apply/commit/push controls wired.
  - No queue execution or command execution wired.
  - No full auto.
  - No limited unattended operation.
- Code health checks:
  - `git diff --check`
  - TypeScript check.
  - Lint check.
  - Focused dashboard and `/map` tests.
- Manual visual QA:
  - Dashboard no longer feels unavailable or overblocked by default.
  - `/map` carries detail without becoming visually cramped.

Expected output:

- Implementation closeout doc records:
  - Files changed.
  - Screenshots reviewed.
  - Commands run.
  - Safety boundaries verified.
  - Any known placeholders.
  - Any missing runtime support.
  - Confirmation that no autonomy, execution controls, apply, commit, push, queue execution, or command execution were enabled.

Debug path if the check fails:

- If dashboard is too dense, remove detail until it returns to the five allowed overview items.
- If `/map` is too dense, split sections, add tabs, or collapse details.
- If any action appears enabled, disable/remove it and add a regression test.
- If tests fail because runtime support is missing, return that section to placeholder/read-only state.

Stop conditions:

- Any future implementation enables autonomy, execution controls, queue execution, command execution, apply, commit, or push.
- Any future implementation edits forbidden files without a separate approved plan.
- Screenshots show dashboard becoming the control panel again.

Next increment title:

Map Route Phase 1.1: Create Inert `/map` Route Shell
