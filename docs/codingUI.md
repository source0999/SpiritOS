# /coding UI Polish Plan

status: active

Status date: 2026-05-20

## Purpose

`/coding` is the clean, Codex-like everyday cockpit for Source Proxy coding work. It helps the operator draft a task, preview a bounded proposal, review evidence, approve only when legal, apply only after approval, verify afterward, and understand the next safe action.

`/proxy-backend` remains the raw diagnostic and backend surface for detailed route output, replay logs, task internals, safety evidence, and troubleshooting.

This plan is UI polish only. It uses existing Source Proxy contracts and gates. It does not create new authority, hidden writes, commit/push buttons, provider routing, autopilot, or any bypass around preview, approval, apply, or verification.

## Authority Boundary

- `/coding` is a client/control surface.
- `/proxy-backend` is the advanced diagnostic console.
- Source Proxy APIs remain the execution boundary.
- Task specs, target files, allowed files, diff preview, reviewer/verifier evidence, approval, apply, and verification remain separate.
- Buttons appear only when legal under existing backend state.
- Apply does not imply commit.
- Verify does not imply push.
- No commit or push controls belong in this UI polish phase.
- No backend authority changes are allowed unless UI work reveals a real missing contract and a separate approval authorizes it.
- Mobile-first support matters because Codex mobile and remote terminal workflows are part of daily operation.

## Status Language

The cockpit should use readable states:

- Draft
- Preview ready
- Needs approval
- Approved, not applied
- Applied, verification required
- Verified
- Blocked

Every state should make clear what happened, whether files changed, what evidence exists, and what the next safe action is.

## Simplification-First Direction

Default `/coding` must show one simple operator flow, not a wall of process evidence.

The default screen should contain:

- Task composer
- One current state card
- One safe next action bar
- Diff/review summary when available
- Collapsed evidence and receipts

Each screen should answer:

- What task is being worked on?
- What state is it in?
- What changed?
- What can I safely do next?
- What evidence exists if inspection is needed?

Keep the Source Proxy process visible as:

```text
Draft -> Preview -> Approval -> Apply -> Verify
```

Do not add new major UI sections unless they replace or simplify an existing section. UI polish should remove competition for attention before it adds new visible structure.

Collapse or hide by default:

- raw Architect/Coder/Reviewer/Verifier role timeline
- terminal/test evidence unless failed or explicitly opened
- receipts and verbose evidence packets
- backend route details
- raw task internals

Deep diagnostics belong in `/proxy-backend`. `/coding` may link there, but should not reproduce the diagnostic console.

## Phase UI-0: Green Baseline And Route Separation

Intent:
Record that the backend green gate passed and separate the next active UI track from backend diagnostics before feature work begins.

Allowed files or likely files:

- `docs/plan-index.md`
- `docs/source-proxy-production-hardening-plan.md`
- `docs/codingUI.md`

Forbidden actions:

- Source code changes
- backend contract changes
- deletion or cleanup without explicit permission
- recreating `proxyCLI.md`
- commit, push, autopilot, provider, AionUi, Cowork, or native mobile work

Manual checks:

```bash
git diff -- docs/plan-index.md docs/source-proxy-production-hardening-plan.md docs/codingUI.md
git diff --check -- docs/plan-index.md docs/source-proxy-production-hardening-plan.md docs/codingUI.md
```

Expected output:

- Green gate is recorded.
- `/coding` is named as the user cockpit.
- `/proxy-backend` is named as diagnostics.
- No feature implementation starts.

Next increment title:
UI-1: Clean `/coding` cockpit shell.

## Phase UI-1: Clean /coding Cockpit Shell

Intent:
Make `/coding` feel like a focused operator cockpit instead of a diagnostic wall, while keeping `/proxy-backend` unchanged.

Allowed files or likely files:

- `src/app/coding/page.tsx`
- `src/components/coding/*`
- `src/components/coding/__tests__/*`
- targeted styling files already used by the coding surface
- targeted Playwright coverage if an e2e pattern already exists

Forbidden actions:

- Backend execution changes
- commit or push buttons
- approval/apply bypasses
- hidden writes
- provider marketplace or provider expansion
- new autonomy or autopilot controls

Manual checks:

- Open `/coding` on desktop and mobile viewport.
- Open `/proxy-backend` and confirm diagnostic detail remains available there.
- Confirm the default `/coding` view shows a header/status strip, task composer, current task card, safe action rail, mobile-first stacked layout, and no debug clutter.
- Confirm any advanced details link to `/proxy-backend`.

Expected output:

- `/coding` has a calm cockpit shell.
- Debug-heavy panels are removed or hidden from the default view.
- `/proxy-backend` still carries diagnostics.
- No source files are changed by viewing or composing.

Next increment title:
UI-2: Collapsed evidence trail.

## Phase UI-2: Timeline And Evidence

Status: superseded by simplification direction.

Intent:
Keep evidence available without making role/process cards compete with the main operator flow.

Allowed files or likely files:

- `src/components/coding/*`
- existing Source Proxy client hooks or typed response adapters
- `src/components/coding/__tests__/*`
- targeted Playwright tests if present

Forbidden actions:

- New backend authority
- changing verifier/reviewer semantics
- applying files from the timeline
- commit or push affordances
- hiding blockers in order to make the UI look cleaner

Manual checks:

- Confirm raw role timeline is collapsed under `Evidence trail`.
- Confirm terminal/test evidence is collapsed unless failed or explicitly opened.
- Confirm the readable state renders in one current state card.
- Confirm a path to full diagnostics in `/proxy-backend` remains visible.

Expected output:

- The operator sees one main flow, not several competing process panels.
- Evidence exists but is collapsed by default.
- Failed evidence can surface enough detail to explain the blocker.

Next increment title:
UI-3: Diff/review summary.

## Phase UI-3: Diff And Review Pane

Status: superseded by simplification direction.

Intent:
Expose the review facts that make approval safe as a compact summary, not as another always-visible diagnostic pane.

Allowed files or likely files:

- `src/components/coding/*`
- existing diff/review rendering helpers
- `src/components/coding/__tests__/*`
- targeted Playwright tests if present

Forbidden actions:

- Diff application from this pane
- mutating allowed files, target files, or protected path results in the client
- treating reviewer advisory output as a hard pass unless the backend already says so
- commit/push controls

Manual checks:

- Confirm changed files, allowed-file result, protected-path result, target match, reviewer verdict, and verification result appear in one compact diff/review summary when preview exists.
- Confirm raw diff and role evidence are collapsed unless explicitly opened or failed.
- Confirm an `Open diagnostics in /proxy-backend` link is present.

Expected output:

- The operator can tell whether the preview is bounded and reviewable.
- Mismatches and protected-path blocks are obvious.
- Full diagnostic detail remains one click away instead of always visible.

Next increment title:
UI-4: Simplify default cockpit flow.

## Phase UI-4: Approval/Action Bar

Status: in progress.

Intent:
Replace competing visible panels with one default operator flow: task composer, current state card, safe next action bar, compact diff/review summary, and collapsed evidence trail.

Allowed files or likely files:

- `src/components/coding/*`
- existing approval/apply client integration already used by Source Proxy
- `src/components/coding/__tests__/*`
- targeted Playwright tests if present

Forbidden actions:

- Buttons that appear before backend state allows them
- apply without approval
- approval that mutates files
- apply implying commit
- verify implying push
- commit or push buttons
- hidden writes

Manual checks:

- Confirm the default `/coding` view does not show role cards, terminal evidence, receipts, or raw backend details as always-visible panels.
- Confirm the Source Proxy process remains clear: Draft -> Preview -> Approval -> Apply -> Verify.
- Confirm Preview appears for draft work only when required fields are valid.
- Confirm Approve appears only when preview gates pass and approval is legal.
- Confirm Apply appears only after approval and uses existing approval binding.
- Confirm Verify appears only after apply or when backend state says verification is needed.
- Confirm blocked state explains the blocker and the safe next action.

Expected output:

- `/coding` is simpler than before this increment.
- Preview, approve, apply, and verify are distinct.
- Illegal actions are absent or disabled with an explanation.
- Apply never implies commit; verify never implies push.

Next increment title:
UI-5: Mobile/manual remote checks after simplification.

## Phase UI-5: Mobile/Manual Remote Checks

Status: complete in `c868a8d`.

Intent:
Make `/coding` usable for Codex mobile and remote workflows without requiring a full desktop visual session for basic review.

Allowed files or likely files:

- `src/components/coding/*`
- existing responsive styles
- targeted Playwright device checks
- docs updates for manual remote checks if needed

Forbidden actions:

- Native mobile app work
- RustDesk-only workflow assumptions
- mobile-only authority bypasses
- hidden writes or shortcuts around approval
- commit/push controls

Manual checks:

- Review on iPhone-sized viewport.
- Review on Android-sized viewport.
- Confirm mobile review cards show status, changed files, blockers, evidence, and next safe action.
- Confirm Codex mobile/manual terminal workflow notes remain accurate.
- Confirm basic checks do not require RustDesk when the cockpit exposes enough state.
- Confirm RustDesk remains useful only for full visual debugging.

Expected output:

- `/coding` can be reviewed comfortably on mobile.
- Remote operation can rely on cockpit state plus terminal checks for common cases.
- Visual debugging remains available without becoming required for every check.

Next increment title:
UI-6: Closeout.

## Phase UI-6: Closeout

Status: complete in closeout pass after `c868a8d`.

Intent:
Verify the UI polish did not weaken Source Proxy safety and record the finished state.

Allowed files or likely files:

- final touched UI files
- final touched tests
- docs touched by the approved UI polish increment

Forbidden actions:

- commit or push
- destructive cleanup
- broad refactors outside the UI polish scope
- new backend authority
- autopilot, provider marketplace, AionUi bridge, Cowork console, or native mobile activation

Manual checks:

```bash
git diff --check
git status --short
```

Run available checks only after inspecting scripts and local environment:

- typecheck
- lint if available
- targeted Vitest if available
- targeted Playwright if available
- global safety regression
- dashboard smoke
- no unexpected mutation check

Expected output:

- Typecheck passes.
- Lint passes if available.
- Targeted UI tests pass if available.
- Targeted Playwright checks pass if available.
- Global safety regression remains green.
- Dashboard smoke remains green.
- No unexpected mutation occurs.
- Docs are updated.
- No commit or push occurs.

Next increment title:
Post-polish review and explicit approval for any further implementation.
