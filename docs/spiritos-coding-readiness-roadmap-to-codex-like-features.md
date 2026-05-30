# SpiritOS /coding Readiness Roadmap To Codex-Like Feature Planning

status: active roadmap

Status date: 2026-05-28

## Endpoint

This roadmap gets SpiritOS to this stop point:

> `/coding` is clean enough, coder is verified, designer is verified, combined coder + designer flow is verified, trial runner is usable, backend/debug clutter is moved out of the main UI, and SpiritOS is ready for a new Codex-like Features Roadmap.

This roadmap stops before Codex-like feature implementation. It also stops before creating a final CSS polish roadmap and before doing final CSS polish.

## Active Authority

This document is the active roadmap authority for `/coding` readiness work until Britton replaces it.

Future Codex chats should treat older Source Proxy, Design Agent, trial, PR-8.3, safety, audit, and readiness documents as historical/supporting unless Plan 0 of this roadmap explicitly reclassifies one as active authority for a narrow fact.

The only intended active source of truth after this document is approved is:

- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`
- `docs/plan-index.md` only as the lightweight pointer to the active roadmap
- product code, tests, UI behavior, trial runner output, copied diagnostics, and manual proof produced during future plan execution

## Boundaries

This roadmap does not implement Codex-like features.

This roadmap does not create the Codex-like Features Roadmap.

This roadmap does not create the final CSS polish plan.

This roadmap does not do final CSS polish.

This roadmap does not continue safety theater, audit loops, read-only evidence packets, or docs-only readiness as the main project.

Reasonable recovery rails still apply:

- Do not delete unrelated work.
- Do not wipe repos.
- Do not expose secrets.
- Do not commit or push without Britton asking.
- Keep backend/debug details available through `/proxy-backend`, logs, artifacts, or copied diagnostics instead of the default `/coding` cockpit.

## PIVOT Execution Rule For Future Chats

One Codex chat works on one whole plan at a time.

Inside a plan:

1. Work increment by increment.
2. Do not stop after Increment 1 unless blocked.
3. After each increment:
   - state the increment completed
   - run the relevant check
   - inspect the output
   - fix scoped failures if reasonable
   - record evidence briefly
   - state GO / NO-GO
   - if GO, continue to the next increment in the same phase
4. At the end of each phase:
   - review all increments completed in that phase
   - confirm checks passed or explain failures
   - confirm scope stayed aligned
   - state GO / NO-GO for the next phase
5. At the end of each plan:
   - give a plan closeout
   - list files changed
   - list checks run
   - list manual proof
   - state GO / NO-GO for the next plan
   - provide a copy-paste handoff for the next plan
6. Do not start the next plan until Britton approves.

Future chats must execute implementation-forward after Plan 0. A plan may include checks, but the project is product code, UI behavior, working verification, and product proof.

## Product Target

The default `/coding` UI should focus on:

- projects
- chats/tasks
- the input/composer
- active task/chat transcript
- trial runner
- clear result/status
- one Copy diagnostics or Copy report action when something fails

The default `/coding` UI should not foreground:

- Settings
- Diagnostics
- Evidence
- Project/provider/safety details
- Environment details
- safety language and status chip clutter
- dirty tree warning walls
- backend route/proof wording
- empty approval queues
- future/unwired project rows
- awkward drawers Britton must babysit
- trial runner backend/test jargon

## Readiness Classes

Use these labels consistently:

- `product-proven`: verified from the frontend/product surface with useful output and manual proof.
- `harness-proven`: verified only through a script, artifact, fixture, diagnostic, or non-product harness.
- `partial`: some path works, but important product behavior or proof is missing.
- `not proven`: no current usable proof.
- `blocked`: exact product blocker prevents meaningful verification.

## Standard Checks

Each future plan should choose the smallest useful check set for its changed surface. Prefer existing repo commands and do not install new tooling just to satisfy the roadmap.

Baseline docs checks for roadmap/doc-only edits:

- `git diff --check`
- `git status --branch --short --untracked-files=normal`

Typical product checks for `/coding` work:

- targeted unit/component tests near changed files
- existing coding frontend regression tests when relevant
- `npm run lint` or narrower lint command if available and reasonable
- manual browser check of `/coding`
- manual browser check of `/proxy-backend` when diagnostics move there
- screenshot or visual inspection for desktop, tablet, and mobile where layout changes are involved

Manual evidence should be brief: path, command or route, observed result, GO / NO-GO.

---

# Plan 0: Roadmap Reset And Truth Lock

Purpose: Briefly reconcile old plans, lock the current truth, mark stale docs historical/supporting, and install this roadmap as the active source of truth.

Plan 0 is allowed to inspect and classify old plans, but it must stay short. It must not become another long audit project.

## Phase 0.1: Old Plan Truth Check

Goal: Identify only enough old-plan truth to prevent stale docs from steering future work.

### Increment 0.1.1: Classify Prior Plans

Classify prior plans as complete, partial, docs-only, superseded, or still required.

Manual check:

- Read `docs/plan-index.md` and the latest closeouts named there.
- Verify the classification table has no more detail than needed for this roadmap.

GO when:

- The classification is concise.
- No old plan is treated as active implementation authority unless explicitly required.

### Increment 0.1.2: Identify Product/Runtime Code Changes

Identify which prior plans actually changed product/runtime code.

Manual check:

- Inspect referenced closeouts or git history only enough to tell docs-only from product code changes.
- Record paths or plan names, not full evidence packets.

GO when:

- Future chats can tell which old claims came from product changes and which came from docs.

### Increment 0.1.3: Identify Non-Guiding Plans

Identify which prior plans should not guide future execution.

Manual check:

- Confirm docs-only safety/audit/readiness loops are marked historical/supporting.
- Confirm old final CSS and Codex-like feature plans do not authorize work under this roadmap.

GO when:

- Stale plans cannot reasonably be mistaken for the next active roadmap.

## Phase 0.2: Coder/Designer/Combined Current State

Goal: Lock what is currently proven, and whether it is product-proven or only harness-proven.

### Increment 0.2.1: Locate Latest Coder Result

Locate the latest coder result and classify it as product-proven, harness-proven, partial, or not proven.

Manual check:

- Find the latest coder trial/result referenced by docs, tests, artifacts, or UI.
- Confirm whether the result was produced from `/coding` or only a harness.

GO when:

- Coder status has one readiness class and a one-line reason.

### Increment 0.2.2: Locate Latest Designer Result

Locate the latest designer result and classify it as product-proven, harness-proven, partial, or not proven.

Manual check:

- Find the latest designer trial/result referenced by docs, tests, artifacts, or UI.
- Confirm whether the result was produced from the product surface.

GO when:

- Designer status has one readiness class and a one-line reason.

### Increment 0.2.3: Locate Latest Combined Result

Locate the latest combined coder + designer result and classify it as product-proven, harness-proven, partial, or not proven.

Manual check:

- Find the latest combined trial/result.
- Confirm whether it proves a product flow or only isolated harness output.

GO when:

- Combined status has one readiness class and a one-line reason.

### Increment 0.2.4: Create Concise Readiness Table

Create one concise readiness table for coder, designer, combined, UI, and trial runner.

Manual check:

- Confirm the table names current status, proof type, exact next action, and blocker if any.

GO when:

- The table is short enough to guide Plan 1 without becoming a report.

## Phase 0.3: New Roadmap Activation

Goal: Make this roadmap the active authority and hand off Plan 1.

### Increment 0.3.1: Write Or Update Active Roadmap File

Write or update this active roadmap file.

Manual check:

- Confirm `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md` exists.
- Confirm it contains Plans 0 through 7 and the PIVOT execution rule.

GO when:

- The roadmap is present and complete.

### Increment 0.3.2: Mark Old Roadmap Paths Historical/Supporting

Mark old roadmap paths as historical/supporting where appropriate.

Manual check:

- Update only a lightweight pointer/index if one exists.
- Do not create side reports or evidence bundles.

GO when:

- Future chats see this roadmap first.

### Increment 0.3.3: Write Plan 1 Handoff

Write a copy-paste Plan 1 handoff in the Plan 0 closeout.

Manual check:

- The handoff tells the next chat to start Plan 1 and not restart Plan 0.
- It names `/coding UI Product Purge` as the next plan.

GO when:

- Britton can approve Plan 1 in a new message.

## Plan 0 Acceptance Criteria

- We know what is real, what is fake-complete, what is historical, and what the new roadmap will solve.
- Old docs are not allowed to drag the project back into safety/audit/readiness loops.
- The active pointer leads future chats to this roadmap.

## Plan 0 Phase Closeout Checks

- Phase 0.1: Prior plans classified without opening a new audit project.
- Phase 0.2: Coder, designer, combined, UI, and runner statuses classified with proof type.
- Phase 0.3: This roadmap is active and Plan 1 handoff is ready.

## Plan 0 Closeout Checks

- Files changed listed.
- Checks run listed.
- Manual proof listed.
- GO / NO-GO stated for Plan 1.
- Copy-paste handoff provided for Plan 1.

## Plan 0 Execution Closeout: Roadmap Reset And Truth Lock

Status: complete on 2026-05-28.

### Phase 0.1 Result: Old Plan Truth Check

Prior-plan classification:

| Prior plan family | Classification | Current handling |
| --- | --- | --- |
| Source Proxy Agent Integration Preflight Plans 0-12 | complete | Historical/verification authority for implemented preview/UI/route/test work only. Does not authorize soak, production readiness, apply execution, provider calls, workers, or final CSS. |
| Source Proxy post Run 300 blocker-reduction and PR-8.3 recovery docs | partial/docs-only or blocked | Supporting history only. PR-8.3 recovery remained blocked/pending acceptance and must not steer this roadmap. |
| Design Agent A-grade/readiness, ecosystem diagnostics, and PR-8.3 dependency docs | docs-only | Historical/supporting only. They do not authorize `/coding` implementation or new audit loops. |
| Unified proxy/coding/design evidence and final CSS packets | superseded/historical | Supporting evidence only. Old final CSS and Codex-like feature plans do not authorize work here. |
| Agent Runtime Trial Harness Mac Subagent Port Plans/evidence | current supporting proof | Supporting proof for trial harness/coder/designer/combined states; does not replace this active roadmap. |
| This roadmap | active | Current `/coding` readiness authority until Britton replaces it. |

Product/runtime code changes identified:

| Source | Product/runtime impact |
| --- | --- |
| Source Proxy Agent Integration Preflight Plans 2, 3, 6, 8, 9, 11 | Added or verified bounded diff preview, `/coding` command center changes, design/research/Cart preview lanes, combined gauntlet route/UI, guarded apply route tests, and mobile `/coding` nav fix. |
| Agent Runtime Trial Harness work | Added trial runner UI/helpers/scripts/tests and evidence artifacts; current proof is supporting and preview-only. |
| Design Agent A-grade/readiness and many PR-8.3 recovery packets | Mostly docs-only; not product proof. |

Non-guiding plan lock:

- Docs-only safety/audit/readiness loops are historical/supporting.
- Old final CSS plans do not authorize final polish under this roadmap.
- Old Codex-like feature plans do not authorize Codex-like feature implementation under this roadmap.
- Old Source Proxy, Design Agent, trial, and PR-8.3 handoffs do not restart their lanes from this roadmap.

Increment 0.1.1 completed. Manual check: `docs/plan-index.md` and latest closeouts named there were read; classification stayed concise. Evidence: table above. GO.

Increment 0.1.2 completed. Manual check: referenced closeouts and current trial-harness evidence were inspected only enough to separate product/runtime changes from docs-only claims. Evidence: product/runtime table above. GO.

Increment 0.1.3 completed. Manual check: docs-only safety/audit/readiness loops, old final CSS, and old Codex-like feature plans are marked historical/supporting or superseded. Evidence: non-guiding lock above. GO.

Phase 0.1 closeout: All increments completed, checks passed by manual inspection, and scope stayed limited to stale-plan reconciliation. GO for Phase 0.2.

### Phase 0.2 Result: Coder/Designer/Combined Current State

Current readiness table:

| Surface | Readiness class | Proof type | One-line reason | Exact next action | Blocker |
| --- | --- | --- | --- | --- | --- |
| Coder | product-proven | `/coding` UI harness plus artifacts | Latest coding Britton-realistic UI run passed 3/3 and Plan 2 A+ batch passed 12 prompts/26 Chromium tests with no hidden mutation or protected-path writes. | Plan 1 should clean the default `/coding` UI around the existing Agent Trials/coding workflow. | Default UI still foregrounds backend/debug clutter. |
| Designer | product-proven | `/coding` UI harness plus artifacts | Plan 3 A+ design batch passed 12 prompts/26 Chromium tests and current UI evidence keeps design packets preview-only with no fake CSS/apply authority. | Preserve designer proof while moving design/debug detail out of the default cockpit. | Designer evidence is preview/proposal-only, not implementation authority. |
| Combined coder + designer | product-proven | `/coding` UI harness plus combined report | Latest combined Britton-realistic run passed 3/3, generated 3 design packets, delivered 3 coding prompts, and recorded no hidden mutation or fake authority. | Keep combined proof available through trial runner/result views while simplifying the default screen. | Combined flow is preview/proposal-only; no apply execution. |
| `/coding` UI | partial | product/browser proof and component tests | Agent Trials is the current single normal trial surface, but the broader cockpit remains dense and backend/debug-oriented. | Start Plan 1: `/coding UI Product Purge`. | Backend/debug clutter is still visible enough to confuse normal use. |
| Trial runner | product-proven | UI runner, scripts, artifacts | Current Agent Trials UI correction passed 92 tests, coding/combined realistic UI runs, typecheck, and diff check; current UI no longer exposes legacy controls by default. | Keep runner visible as a product control and move legacy diagnostics out of primary flow. | Browser artifact parsing remains unavailable; grep/manual artifact proof is used. |

Increment 0.2.1 completed. Manual check: latest coder result found in `docs/evidence/agent-runtime-trial-harness/plan-2/plan-2-pivot-evidence.md` and current UI correction closeout; result came through `/coding` UI harness. Evidence: coder row above. GO.

Increment 0.2.2 completed. Manual check: latest designer result found in `docs/evidence/agent-runtime-trial-harness/plan-3/plan-3-pivot-evidence.md` and current UI correction closeout; result came through `/coding` UI harness. Evidence: designer row above. GO.

Increment 0.2.3 completed. Manual check: latest combined result found in `docs/evidence/agent-runtime-trial-harness/plan-6/combined-report.md` and `docs/evidence/agent-runtime-trial-harness/plan-5/summary.md`; result proves a product UI harness flow, not apply authority. Evidence: combined row above. GO.

Increment 0.2.4 completed. Manual check: readiness table names current status, proof type, next action, and blocker. Evidence: table above. GO.

Phase 0.2 closeout: All increments completed, proof types are classified, and scope stayed to current-state locking. GO for Phase 0.3.

### Phase 0.3 Result: New Roadmap Activation

Active authority:

- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`
- `docs/plan-index.md` only as the lightweight pointer to this roadmap
- Product code, tests, UI behavior, trial runner output, copied diagnostics, and manual proof produced by future approved plan execution

Increment 0.3.1 completed. Manual check: this roadmap exists and contains Plans 0 through 7 plus the PIVOT execution rule. Evidence: grep/check commands in Plan 0 closeout. GO.

Increment 0.3.2 completed. Manual check: only the lightweight pointer/index was updated; no side reports or evidence bundles were created. Evidence: `docs/plan-index.md` points future `/coding` readiness chats here and stale handoffs are historical/supporting. GO.

Increment 0.3.3 completed. Manual check: Plan 1 handoff below tells the next chat to start Plan 1 and not restart Plan 0. GO.

Phase 0.3 closeout: All increments completed, this roadmap is active, old roadmap paths are historical/supporting for this lane, and Plan 1 handoff is ready. GO for Plan 1 only after Britton approval in a new message.

### Plan 0 Final Closeout

Files changed:

- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`
- `docs/plan-index.md`

Checks run:

- `git diff --check`
- `git diff --check -- docs/plan-index.md`
- `git diff --no-index --check /dev/null docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`
- `git status --branch --short --untracked-files=normal`
- focused `grep` checks for active roadmap, PIVOT rule, Plans 0 through 7, Plan 1 handoff, historical/supporting markings, and stale active-handoff wording

Manual proof:

- Read `docs/plan-index.md`.
- Read current active roadmap Plan 0.
- Read Source Proxy Preflight Plan 9, Plan 11, and Plan 12 closeouts.
- Read PR-8.3 real-task gauntlet closeout.
- Read Agent Runtime Trial Harness Plan 2, Plan 3, Plan 5, Plan 6, and UI correction evidence.

Plan 0 result: GO.

GO / NO-GO for Plan 1: GO only after Britton approves Plan 1 in a new message.

Copy-paste Plan 1 handoff:

```text
You are Codex inside the SpiritOS repository.

Start Plan 1 only from the active roadmap:

docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md

Plan 0 is complete. Do not restart Plan 0.

MISSION:
Execute Plan 1: /coding UI Product Purge in strict PIVOT workflow.

Do not start Plan 2.
Do not implement Codex-like features.
Do not start final CSS polish.
Do not restart old Source Proxy, Design Agent, PR-8.3, trial, safety, audit, or readiness plans.

Use the Plan 0 truth lock in the active roadmap:
- coder, designer, combined, and trial runner are currently product-proven through the /coding UI harness, preview/proposal-only
- /coding UI is partial because backend/debug clutter remains
- old docs-only safety/audit/readiness/final-CSS/Codex-like plans are historical/supporting

Begin with Plan 1, Phase 1.1, Increment 1.1.1.
Work increment by increment, run relevant checks after each increment, inspect output, fix scoped failures if reasonable, record brief evidence, state GO / NO-GO, and continue within Plan 1 until Plan 1 is complete or blocked.
```

---

# Plan 1: /coding UI Product Purge

Purpose: Clear the default `/coding` screen so it stops feeling like a backend console.

## Phase 1.1: Remove Backend Clutter From Default View

Goal: Make the first view of `/coding` feel like a focused coding cockpit.

### Increment 1.1.1: Remove Settings, Diagnostics, And Evidence From Primary View

Remove Settings, Diagnostics, and Evidence from the default `/coding` primary view.

Manual check:

- Open `/coding`.
- Confirm those surfaces are not visible as primary panels, tabs, cards, or default drawers.

GO when:

- A user can start from `/coding` without seeing those surfaces by default.

### Increment 1.1.2: Hide Project/Provider/Safety Details

Remove or hide Project/Provider/Safety details from the default view.

Manual check:

- Confirm provider, safety gate, route, and project backend details are absent from the default cockpit.
- Confirm needed detail still exists in diagnostics or `/proxy-backend`.

GO when:

- The cockpit shows useful project/chat context without backend metadata clutter.

### Increment 1.1.3: Hide Environment Details

Remove or hide Environment Details from the default view.

Manual check:

- Confirm environment paths, backend state dumps, and route probes are not in the default screen.

GO when:

- Environment details are available only through `/proxy-backend`, logs, artifacts, or copied diagnostics.

### Increment 1.1.4: Compact Status Area

Replace long warning/status chip clutter with one compact status area.

Manual check:

- Confirm the default screen has one compact status/result area.
- Confirm dirty tree or safety copy does not become a warning wall.

GO when:

- The status area communicates Ready, Working, Needs input, Finished, or Failed without dominating the UI.

## Phase 1.2: Move Backend Details Out

Goal: Keep debug material useful without making `/coding` feel like a backend route monitor.

### Increment 1.2.1: Make /proxy-backend The Raw Diagnostics Home

Make `/proxy-backend` the home for raw diagnostics, backend state, route details, and evidence.

Manual check:

- Open `/proxy-backend`.
- Confirm raw diagnostic surfaces are reachable there or linked appropriately.

GO when:

- Backend details moved out of `/coding` have a clear home.

### Increment 1.2.2: Add Clean Copy Diagnostics Action

Add one clean Copy diagnostics action where needed.

Manual check:

- Trigger or simulate a failed state.
- Confirm a visible Copy diagnostics action appears without requiring drawer navigation.

GO when:

- Failure detail can be copied from the product surface.

### Increment 1.2.3: Useful Failure Packet Without Drawers

Make failed states generate a useful copy-paste packet without forcing drawer use.

Manual check:

- Copy diagnostics from a failure.
- Confirm the packet includes task, status, visible error, route or subsystem if useful, and next action.

GO when:

- The copied packet is enough for a new Codex/ChatGPT handoff.

## Phase 1.3: Clean Left Rail And Sidebar

Goal: The sidebar should show real navigation and the useful runner, not future scaffolding.

### Increment 1.3.1: Show Real Projects, Chats/Tasks, And Useful Runner

Show only real projects, chats/tasks, and the useful runner in the default left rail/sidebar.

Manual check:

- Confirm visible rows correspond to real selectable/productive items.

GO when:

- The sidebar reads as a working navigation area.

### Increment 1.3.2: Hide Future/Unwired Project Rows

Hide future or unwired project rows by default.

Manual check:

- Confirm disabled placeholders are gone or moved behind an explicit non-primary path.

GO when:

- The default project list does not advertise unwired features.

### Increment 1.3.3: Hide Empty Approval Queue

Hide the approval queue when empty.

Manual check:

- Load `/coding` with no approvals.
- Confirm no empty queue wall appears.

GO when:

- Approval UI appears only when there is something to act on.

### Increment 1.3.4: Make Trial Runner Readable

Make the trial runner readable instead of squeezed or truncated.

Manual check:

- Inspect desktop and tablet widths.
- Confirm runner controls and latest result are readable.

GO when:

- The runner is usable from its chosen sidebar or compact panel location.

## Plan 1 Acceptance Criteria

- Default `/coding` no longer shows backend/debug walls.
- Britton does not have to babysit drawers to understand normal state or failure state.
- Diagnostics and evidence still exist in appropriate backend/debug locations.

## Plan 1 Phase Closeout Checks

- Phase 1.1: Default clutter removed.
- Phase 1.2: Backend details moved to `/proxy-backend` or copy diagnostics.
- Phase 1.3: Sidebar shows only useful, real product surfaces.

## Plan 1 Closeout Checks

- Files changed listed.
- Checks run listed.
- Manual `/coding` and `/proxy-backend` proof listed.
- GO / NO-GO stated for Plan 2.
- Copy-paste Plan 2 handoff provided.

---

# Plan 2: Core Coding Cockpit Layout

Purpose: Make `/coding` structurally usable as a daily coding cockpit before any Codex-like feature roadmap begins.

## Phase 2.1: Main Workspace Reset

Goal: Center the working conversation and composer.

### Increment 2.1.1: Center Active Chat/Task Transcript

Make the active chat/task transcript the main center surface.

Manual check:

- Open `/coding`.
- Confirm the transcript is the main reading surface and is not visually secondary to backend cards.

GO when:

- A coding task conversation is the natural focal point.

### Increment 2.1.2: Composer As Primary Action Surface

Make the input/composer the primary action surface.

Manual check:

- Confirm the composer is immediately visible and usable.
- Confirm its command/state controls are not buried behind drawers.

GO when:

- A user knows where to type the next task.

### Increment 2.1.3: Replace Dead No-Task Space

Replace dead “no task drafted” space with a useful current task or empty-state card.

Manual check:

- Load with no active task.
- Confirm the empty state offers a useful next action without backend/debug copy.

GO when:

- Empty state helps start work instead of implying a broken console.

### Increment 2.1.4: Keep Context Visible But Quiet

Keep project/chat context visible without overwhelming the workspace.

Manual check:

- Confirm current project and chat/task are visible in a compact, plain area.

GO when:

- Context is present but the transcript and composer stay dominant.

## Phase 2.2: User-Facing Language Cleanup

Goal: Replace backend/proof language with clear product state.

### Increment 2.2.1: Plain State Labels

Replace backend-facing labels with plain states: Ready, Working, Needs input, Finished, Failed.

Manual check:

- Inspect default, working, finished, failure, and needs-input states where possible.

GO when:

- User-facing labels match plain product state.

### Increment 2.2.2: Remove Scared Primary Action Copy

Remove “Preview safely” from the primary user-facing action if it makes the app feel scared of itself.

Manual check:

- Confirm the primary action uses direct coding language such as Send, Run, Start task, or Run trial.

GO when:

- The primary action feels confident and clear.

### Increment 2.2.3: Replace Route/Provider/Proof Language

Replace route/provider/proof language with plain result language.

Manual check:

- Confirm phrases like route proof, provider proof, safety proof, and backend route are not default cockpit copy.

GO when:

- The UI explains outcomes rather than implementation plumbing.

### Increment 2.2.4: Keep Technical Detail Behind Copy Or Backend

Keep technical detail available only through Copy diagnostics or `/proxy-backend`.

Manual check:

- Trigger or simulate technical failure.
- Confirm details are copyable or visible in `/proxy-backend`, not sprayed across `/coding`.

GO when:

- Technical detail remains available without cluttering the cockpit.

## Phase 2.3: Responsive Sanity

Goal: Make the structural layout usable across major viewports.

### Increment 2.3.1: Verify Desktop Layout

Verify desktop layout.

Manual check:

- Inspect a desktop viewport.
- Confirm transcript, composer, sidebar, and runner fit without overlap.

GO when:

- Desktop is structurally usable.

### Increment 2.3.2: Verify Tablet Layout

Verify tablet layout.

Manual check:

- Inspect a tablet viewport.
- Confirm navigation, transcript, composer, and runner remain usable.

GO when:

- Tablet does not truncate critical controls or hide the composer.

### Increment 2.3.3: Verify Mobile Layout

Verify mobile layout.

Manual check:

- Inspect a mobile viewport.
- Confirm the user can read the transcript and use the composer.

GO when:

- Mobile is not final-polished, but it is coherent and usable.

### Increment 2.3.4: Fix Obvious Layout Defects

Fix obvious overlap, truncation, and tap-target issues found in the responsive checks.

Manual check:

- Recheck changed viewports.
- Confirm fixes did not break desktop.

GO when:

- No obvious overlap or unusable primary controls remain.

## Plan 2 Acceptance Criteria

- `/coding` feels like a usable command center.
- It is not final-polished, but its structure is correct.
- Transcript, composer, context, status, and runner each have a clear place.

## Plan 2 Phase Closeout Checks

- Phase 2.1: Main workspace reset verified.
- Phase 2.2: User-facing language cleaned up.
- Phase 2.3: Desktop/tablet/mobile sanity checked.

## Plan 2 Closeout Checks

- Files changed listed.
- Checks run listed.
- Manual viewport proof listed.
- GO / NO-GO stated for Plan 3.
- Copy-paste Plan 3 handoff provided.

## Plan 2 Execution Closeout - 2026-05-28

Scope: Executed Plan 2 only. Plan 0 and Plan 1 were not restarted. No Codex-like features, final CSS polish, historical Source Proxy, Design Agent, trial, safety, audit, or readiness plans were started.

Increment evidence:

- Increment 2.1.1 completed. Manual/product check: `/coding` center column now starts with `Task transcript`, making the active task conversation the main reading surface. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.1.2 completed. Manual/product check: composer action and required task setup controls are visible, not buried behind `Advanced options`. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.1.3 completed. Manual/product check: no-task state now offers start-work steps without backend/debug copy. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.1.4 completed. Manual/product check: compact project/task/target context appears in the main workspace while transcript and composer remain dominant. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.2.1 completed. Manual/product check: visible status labels use Ready, Working, Needs input, Finished, and Failed. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.2.2 completed. Manual/product check: primary action copy changed to direct task-start language (`Start task` / `Start`). Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.2.3 completed. Manual/product check: default cockpit copy uses result/checks/review/diagnostics language instead of backend route/provider/proof wording. Evidence: focused Vitest run passed 2 files / 7 tests after scoped assertion update. GO.
- Increment 2.2.4 completed. Manual/product check: raw technical failure detail is hidden from `/coding` failure cards and included in Copy diagnostics. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.3.1 completed. Manual viewport check: desktop 1440x900 shows transcript, composer, Start task, runner, and review pane with no horizontal overflow. Evidence: `.codex-smoke/plan2-2.3.1-coding-desktop.png`; focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.3.2 completed. Manual viewport check: tablet 820x1180 puts transcript, composer, and Start task in the first viewport; runner remains reachable below; no horizontal overflow. Evidence: `.codex-smoke/plan2-2.3.2-coding-tablet.png`; focused Vitest run passed 2 files / 7 tests. GO.
- Increment 2.3.3 completed. Manual viewport check: mobile 390x844 is coherent and usable, transcript is readable, composer is reachable, and no horizontal overflow appears. Evidence: `.codex-smoke/plan2-2.3.3-coding-mobile.png`. GO.
- Increment 2.3.4 completed. Manual viewport check: final desktop/tablet/mobile defect pass found usable primary controls and no horizontal overflow. Evidence: Chromium rect/overflow report for desktop, tablet, and mobile. GO.

Phase closeout:

- Phase 2.1: Main workspace reset verified. GO.
- Phase 2.2: User-facing language cleaned up. GO.
- Phase 2.3: Desktop/tablet/mobile sanity checked. GO.

Files changed:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `src/app/coding/__tests__/page.test.tsx`
- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`

Checks run:

- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/app/coding/__tests__/page.test.tsx`
- `npm run typecheck`
- Chromium manual viewport inspections against `http://127.0.0.1:3102/coding` for 1440x900, 820x1180, and 390x844.

Manual proof:

- Desktop screenshot: `.codex-smoke/plan2-2.3.1-coding-desktop.png`
- Tablet screenshot: `.codex-smoke/plan2-2.3.2-coding-tablet.png`
- Mobile screenshot: `.codex-smoke/plan2-2.3.3-coding-mobile.png`

Plan 2 result: GO.

GO / NO-GO for Plan 3: GO only after Britton approves Plan 3 in a new message.

Copy-paste Plan 3 handoff:

```text
You are Codex inside the SpiritOS repository.

Start Plan 3 only from the active roadmap:

docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md

Plan 0, Plan 1, and Plan 2 are complete. Do not restart them.

MISSION:
Execute Plan 3: Trial Runner Simplified And Verified in strict PIVOT workflow.

Do not implement Codex-like features.
Do not start final CSS polish.
Do not restart historical Source Proxy, Design Agent, trial, safety, audit, or readiness plans.

Begin with Plan 3, Phase 3.1, Increment 3.1.1.
Work increment by increment, run relevant checks after each increment, inspect output, fix scoped failures if reasonable, record brief evidence, state GO / NO-GO, and continue within Plan 3 until Plan 3 is complete or blocked.
```

---

# Plan 3: Trial Runner Simplified And Verified

Purpose: Make the trial runner a clean pro tool, not another artifact dashboard.

## Phase 3.1: Runner Surface Cleanup

Goal: Reduce the runner to useful controls and results.

### Increment 3.1.1: Show Run Trial, Status, Latest Score/Result

Show Run Trial, current status, and latest score/result.

Manual check:

- Open `/coding`.
- Confirm these runner elements are visible and readable.

GO when:

- The runner can be understood at a glance.

### Increment 3.1.2: Show Copy Report Only When Useful

Show Copy report only when useful.

Manual check:

- Inspect empty, running, passed, and failed states where practical.

GO when:

- Copy report appears only when there is meaningful report content.

### Increment 3.1.3: Remove Debug Runner Wording

Remove artifact paths, evidence links, grep wording, backend proof text, and advanced/debug surfaces from the default runner.

Manual check:

- Confirm the runner no longer reads like an artifact dashboard.

GO when:

- The default runner uses product language only.

### Increment 3.1.4: Make Runner Understandable In Chosen Location

Make the runner easy to understand from the sidebar or a compact panel.

Manual check:

- Inspect runner placement at desktop and tablet widths.

GO when:

- Runner controls and result fit without squeezing.

## Phase 3.2: Useful Result Categories

Goal: Make runner results prove usefulness, not just safety blocking.

### Increment 3.2.1: Show Coder Result Category

Show coder result category.

Manual check:

- Confirm coder trial output maps to a visible category.

GO when:

- Coder result is readable from the product UI.

### Increment 3.2.2: Show Designer Result Category

Show designer result category.

Manual check:

- Confirm designer trial output maps to a visible category.

GO when:

- Designer result is readable from the product UI.

### Increment 3.2.3: Show Combined Result Category

Show combined result category.

Manual check:

- Confirm combined trial output maps to a visible category.

GO when:

- Combined result is readable from the product UI.

### Increment 3.2.4: Show False Block, Stuck, Failed, And Useful Clearly

Show false block, stuck, failed, and useful result clearly.

Manual check:

- Confirm each category has distinct copy and does not require backend evidence to understand.

GO when:

- Trial results explain whether the system was useful.

### Increment 3.2.5: Stop Celebrating Safe Blockers

Stop celebrating safe blockers as if they prove coding ability.

Manual check:

- Confirm blocked or safe-refusal outcomes are not presented as coding success.

GO when:

- The runner differentiates “did not mutate unsafely” from “successfully helped.”

## Phase 3.3: Runner Manual Proof

Goal: Prove the cleaned runner from the product surface.

### Increment 3.3.1: Run Coding Trial From Cleaned UI

Run a coding trial from the cleaned UI.

Manual check:

- Start the trial from `/coding`.
- Record visible result and copied report if available.

GO when:

- Coding trial result is visible and understandable.

### Increment 3.3.2: Run Design Trial From Cleaned UI

Run a design trial from the cleaned UI.

Manual check:

- Start or select the design trial path from `/coding`.
- Record visible result and copied report if available.

GO when:

- Design trial result is visible and understandable.

### Increment 3.3.3: Run Combined Trial From Cleaned UI

Run a combined trial from the cleaned UI.

Manual check:

- Start or select the combined trial path from `/coding`.
- Record visible result and copied report if available.

GO when:

- Combined trial result is visible and understandable.

### Increment 3.3.4: Verify Copy Report Handoff

Verify Copy report gives enough material for a new ChatGPT/Codex handoff.

Manual check:

- Paste copied report into a scratch buffer.
- Confirm it includes scenario, mode, result, failure if any, and next suggested action.

GO when:

- A future chat can continue from the copied report.

## Plan 3 Acceptance Criteria

- Trial runner is clean and practical.
- It proves whether coder, designer, and combined flows are usable from the product surface.
- It no longer treats safety blockers as proof of coding ability.

## Plan 3 Phase Closeout Checks

- Phase 3.1: Runner surface cleaned.
- Phase 3.2: Useful result categories shown.
- Phase 3.3: Coding, design, and combined trial manual proof completed or blockers recorded.

## Plan 3 Closeout Checks

- Files changed listed.
- Checks run listed.
- Trial manual proof listed.
- GO / NO-GO stated for Plan 4.
- Copy-paste Plan 4 handoff provided.

## Plan 3 Execution Closeout - 2026-05-28

Scope: Executed Plan 3 only after Plan 2 manual acceptance. Plan 0, Plan 1, and Plan 2 were not restarted. No Codex-like features, final CSS polish, or historical Source Proxy/Design Agent/readiness plans were started.

Increment evidence:

- Increment 3.1.1 completed. Manual/product check: runner now shows `Run trial`, Status, Score, and Result from the product surface. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 3.1.2 completed. Manual/product check: `Copy report` is hidden before a run and appears only after a trial result exists. Evidence: focused Vitest run passed 2 files / 7 tests after scoped test-shape fix. GO.
- Increment 3.1.3 completed. Manual/product check: runner default surface no longer shows artifact path, latest evidence, grep, backend proof, or runner-command wording. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 3.1.4 completed. Manual viewport check: runner controls and result fit in the sidebar on desktop and remain readable at tablet width. Evidence: `.codex-smoke/plan3-3.1.4-runner-desktop.png`, `.codex-smoke/plan3-3.1.4-runner-tablet.png`; focused Vitest run passed 2 files / 7 tests. GO.
- Increment 3.2.1 completed. Manual/product check: coder run displays `Coder usefulness`. Evidence: focused Vitest run passed 2 files / 7 tests. GO.
- Increment 3.2.2 completed. Manual/product check: designer run displays `Designer usefulness`. Evidence: focused Vitest run passed 2 files / 8 tests. GO.
- Increment 3.2.3 completed. Manual/product check: combined run displays `Combined usefulness`. Evidence: focused Vitest run passed 2 files / 8 tests. GO.
- Increment 3.2.4 completed. Manual/product check: outcome mix distinguishes Useful, Stuck, False block, and Failed. Evidence: focused Vitest run passed 2 files / 8 tests. GO.
- Increment 3.2.5 completed. Manual/product check: Safe block is shown separately and explicitly not counted as useful coding help. Evidence: focused Vitest run passed 2 files / 8 tests. GO.
- Increment 3.3.1 completed. Manual Chromium check: coding trial run from `/coding` showed Finished, score `95/100 (S+)`, result `7 useful, 2 blocked, 0 failed`, category `Coder usefulness`. Evidence: `.codex-smoke/plan3-3.3-coding-trial.png`. GO.
- Increment 3.3.2 completed. Manual Chromium check: design trial run from `/coding` showed Finished, score `60/100 (S+)`, result `10 useful, 0 blocked, 0 failed`, category `Designer usefulness`. Evidence: `.codex-smoke/plan3-3.3-design-trial.png`. GO.
- Increment 3.3.3 completed. Manual Chromium check: combined trial run from `/coding` showed Finished, score `60/100 (S+)`, result `10 useful, 0 blocked, 0 failed`, category `Combined usefulness`. Evidence: `.codex-smoke/plan3-3.3-combined-trial.png`. GO.
- Increment 3.3.4 completed. Manual Chromium check: copied report includes scenario, mode, status, score, result, failure, and next action for coder, designer, and combined runs. Evidence: clipboard read from Chromium after `Copy report`. GO.

Phase closeout:

- Phase 3.1: Runner surface cleaned. GO.
- Phase 3.2: Useful result categories shown. GO.
- Phase 3.3: Coding, design, and combined trial manual proof completed. GO.

Files changed:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `src/app/coding/__tests__/page.test.tsx`
- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`

Checks run:

- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/app/coding/__tests__/page.test.tsx`
- `npm run typecheck`
- Chromium manual runner inspections against `http://127.0.0.1:3102/coding`.

Trial manual proof:

- Coding report: `scenario: Coder 10-prompt desktop trial`; `mode: Coder`; `status: Finished`; `score: 95/100 (S+)`; `result: 7 useful, 2 blocked, 0 failed`; `failure: none visible`; `next_action: Use the visible result category to decide the next trial.`
- Design report: `scenario: Designer 10-prompt desktop trial`; `mode: Designer`; `status: Finished`; `score: 60/100 (S+)`; `result: 10 useful, 0 blocked, 0 failed`; `failure: none visible`; `next_action: Use the visible result category to decide the next trial.`
- Combined report: `scenario: Combined 10-prompt desktop trial`; `mode: Combined`; `status: Finished`; `score: 60/100 (S+)`; `result: 10 useful, 0 blocked, 0 failed`; `failure: none visible`; `next_action: Use the visible result category to decide the next trial.`

Plan 3 result: GO.

GO / NO-GO for Plan 4: GO only after Britton approves Plan 4 in a new message.

Copy-paste Plan 4 handoff:

```text
You are Codex inside the SpiritOS repository.

Start Plan 4 only from the active roadmap:

docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md

Plan 0, Plan 1, Plan 2, and Plan 3 are complete. Do not restart them.

MISSION:
Execute Plan 4: Coder Product Proof in strict PIVOT workflow.

Do not implement Codex-like features.
Do not start final CSS polish.
Do not restart historical Source Proxy, Design Agent, trial, safety, audit, or readiness plans.

Begin with Plan 4, Phase 4.1, Increment 4.1.1.
Work increment by increment, run relevant checks after each increment, inspect output, fix scoped failures if reasonable, record brief evidence, state GO / NO-GO, and continue within Plan 4 until Plan 4 is complete or blocked.
```

---

# Plan 4: Coder Product Proof

Purpose: Verify the coder path from the frontend enough to justify future Codex-like feature planning.

This plan does not build full Codex-like features.

## Phase 4.1: Coder Path Visibility

Goal: Make a coding task understandable from submit through result.

### Increment 4.1.1: Submit Small Coding Task

Submit a small coding task from the cleaned composer.

Manual check:

- Use `/coding` to submit a narrow task.
- Record whether it starts, asks for input, finishes, or fails.

GO when:

- The task enters the product flow.

### Increment 4.1.2: Show Understood Task

Show what the system understood in plain language.

Manual check:

- Confirm the transcript displays the interpreted task or scope.

GO when:

- Britton can see what the coder thinks it is doing.

### Increment 4.1.3: Show Result Or Failure In Transcript

Show result, needed input, or failure in the task transcript.

Manual check:

- Confirm the transcript contains the final state and useful next step.

GO when:

- The product surface tells the story without backend drawers.

### Increment 4.1.4: Copy Diagnostics On Coder Failure

Make Copy diagnostics sufficient when the coder path fails.

Manual check:

- Trigger or use an existing failure.
- Copy diagnostics and confirm it includes enough context for a handoff.

GO when:

- Failure is actionable without raw UI clutter.

## Phase 4.2: Coder Task Coverage

Goal: Test coder usefulness across small realistic task shapes.

### Increment 4.2.1: Verify Small Frontend/UI Task

Verify a small frontend/UI task.

Manual check:

- Submit a UI task.
- Confirm product-visible outcome and checks.

GO when:

- Result is product-proven or exact blocker is recorded.

### Increment 4.2.2: Verify Small Backend/API Task

Verify a small backend/API task.

Manual check:

- Submit a backend/API task.
- Confirm product-visible outcome and checks.

GO when:

- Result is product-proven or exact blocker is recorded.

### Increment 4.2.3: Verify Small Test-Writing Task

Verify a small test-writing task.

Manual check:

- Submit a test-writing task.
- Confirm generated or proposed test outcome and relevant test command.

GO when:

- Result is product-proven or exact blocker is recorded.

### Increment 4.2.4: Verify Already-Satisfied/No-Op Task

Verify an already-satisfied or no-op task.

Manual check:

- Submit a task that should require no code change.
- Confirm the coder reports that clearly instead of forcing a change.

GO when:

- No-op is handled as a valid useful result.

### Increment 4.2.5: Verify Messy Britton-Style Prompt

Verify one messy Britton-style prompt does not automatically fail because a target file was not preselected.

Manual check:

- Submit a broad but small realistic prompt without preselecting a file.
- Confirm the system can clarify, route, or scope instead of hard-failing.

GO when:

- Missing preselected file does not cause an automatic useless failure.

## Phase 4.3: Coder Readiness Classification

Goal: Make an honest product-readiness decision.

### Increment 4.3.1: Classify Coder

Classify coder as product-proven, partial, or not ready.

Manual check:

- Review Phase 4.1 and 4.2 evidence.

GO when:

- One readiness class is chosen with a one-paragraph reason.

### Increment 4.3.2: List Exact Blockers

List exact blockers if coder is not ready.

Manual check:

- Each blocker names the product behavior that failed and the smallest likely fix lane.

GO when:

- Blockers are specific enough for a future plan.

### Increment 4.3.3: Write Plan 5 Handoff

Write Plan 5 handoff focused on designer proof.

Manual check:

- Handoff starts Plan 5 and summarizes coder status without reopening coder work.

GO when:

- Britton can approve Plan 5 in a new message.

## Plan 4 Acceptance Criteria

- Coder is either product-proven or exact product blockers are known.
- No vague S+ harness claims are used as proof.

## Plan 4 Phase Closeout Checks

- Phase 4.1: Coder path visibility verified.
- Phase 4.2: Frontend, backend, test, no-op, and messy-prompt tasks checked.
- Phase 4.3: Coder readiness classified honestly.

## Plan 4 Closeout Checks

- Files changed listed.
- Checks run listed.
- Manual coder proof listed.
- GO / NO-GO stated for Plan 5.
- Copy-paste Plan 5 handoff provided.

## Plan 4 Execution Closeout - 2026-05-28

Scope: Executed Plan 4 only after Plan 3 acceptance. Plan 0, Plan 1, Plan 2, and Plan 3 were not restarted. No Codex-like features or final CSS polish were started.

Increment evidence:

- Increment 4.1.1 completed. Manual/product check: a drafted task can enter `/coding` as `Needs input` when scope is missing, while fully scoped tasks still enter the preview flow. Evidence: focused Vitest run passed 2 files / 8 tests. GO.
- Increment 4.1.2 completed. Manual/product check: transcript shows `Understood task` with task text, target, allowed files, and checks. Evidence: focused Vitest run passed 2 files / 8 tests. GO.
- Increment 4.1.3 completed. Manual/product check: transcript/status surfaces show useful result or failure next step without backend drawers. Evidence: focused Vitest run passed 2 files / 8 tests. GO.
- Increment 4.1.4 completed. Manual/product check: Copy diagnostics includes task, status, visible error, target, changed files, technical detail, and next action. Evidence: focused Vitest run passed 2 files / 8 tests. GO.
- Increment 4.2.1 completed. Manual Chromium check: small frontend/UI task reached `Needs input: approval available` with product-visible understood task and preview result. Evidence: `.codex-smoke/plan4-4.2-frontend-ui.png`. GO.
- Increment 4.2.2 completed. Manual Chromium check: small backend/API task reached `Needs input: approval available` with product-visible understood task and preview result. Evidence: `.codex-smoke/plan4-4.2-backend-api.png`. GO.
- Increment 4.2.3 completed. Manual Chromium check: small test-writing task reached `Needs input: approval available` with product-visible understood task and preview result. Evidence: `.codex-smoke/plan4-4.2-test-writing.png`. GO.
- Increment 4.2.4 completed. Manual Chromium check: already-satisfied/no-op task produced a clear no-op blocker and Copy diagnostics path instead of forcing a change. Evidence: `.codex-smoke/plan4-4.2-noop.png`. GO.
- Increment 4.2.5 completed. Manual Chromium check: messy Britton-style prompt without preselected files entered `Needs input` and asked for target/allowed files instead of automatically hard-failing. Evidence: `.codex-smoke/plan4-4.2-messy-no-target.png`. GO.
- Increment 4.3.1 completed. Classification: coder is partial. Reason: `/coding` now proves the coder product surface can accept, interpret, classify, and hand off narrow coder tasks across frontend, backend/API, test-writing, no-op, and messy no-target shapes; however these Plan 4 task-shape proofs used controlled browser route responses for preview success/no-op evidence, so live coder backend usefulness is not yet product-proven from an unmocked end-to-end run. GO.
- Increment 4.3.2 completed. Exact blockers: live unmocked coder preview needs product-surface proof for frontend/API/test tasks; messy no-target prompts currently clarify for target/allowed files but do not yet discover likely target files from repo context; no-op is clear but still classified as a blocked/failure state instead of a first-class useful no-change result. Smallest likely fix lanes: live preview proof lane, target-discovery/scoping lane, and no-op result-state lane. GO.
- Increment 4.3.3 completed. Plan 5 handoff below starts designer proof and summarizes coder as partial without reopening coder work. GO.

Phase closeout:

- Phase 4.1: Coder path visibility verified. GO.
- Phase 4.2: Frontend, backend, test, no-op, and messy-prompt tasks checked. GO.
- Phase 4.3: Coder readiness classified honestly as partial. GO.

Files changed:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `src/app/coding/__tests__/page.test.tsx`
- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`

Checks run:

- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/app/coding/__tests__/page.test.tsx`
- `npm run typecheck`
- Chromium controlled product-surface coder checks against `http://127.0.0.1:3102/coding`.

Manual coder proof:

- Frontend/UI: `.codex-smoke/plan4-4.2-frontend-ui.png`, visible state `Needs input: approval available`.
- Backend/API: `.codex-smoke/plan4-4.2-backend-api.png`, visible state `Needs input: approval available`.
- Test-writing: `.codex-smoke/plan4-4.2-test-writing.png`, visible state `Needs input: approval available`.
- Already-satisfied/no-op: `.codex-smoke/plan4-4.2-noop.png`, visible state `No-op exact blocker recorded`.
- Messy no-target: `.codex-smoke/plan4-4.2-messy-no-target.png`, visible state `Needs input: missing scope`.

Plan 4 result: GO, with coder classified partial.

GO / NO-GO for Plan 5: GO only after Britton approves Plan 5 in a new message.

Copy-paste Plan 5 handoff:

```text
You are Codex inside the SpiritOS repository.

Start Plan 5 only from the active roadmap:

docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md

Plan 0, Plan 1, Plan 2, Plan 3, and Plan 4 are complete. Do not restart them.

Coder status from Plan 4: partial. The `/coding` product surface can accept, interpret, classify, and hand off coder tasks across frontend, backend/API, test-writing, no-op, and messy no-target shapes, but live unmocked coder backend usefulness still needs separate product proof.

MISSION:
Execute Plan 5: Designer Product Proof in strict PIVOT workflow.

Do not implement Codex-like features.
Do not start final CSS polish.
Do not restart historical Source Proxy, Design Agent, trial, safety, audit, or readiness plans.

Begin with Plan 5, Phase 5.1, Increment 5.1.1.
Work increment by increment, run relevant checks after each increment, inspect output, fix scoped failures if reasonable, record brief evidence, state GO / NO-GO, and continue within Plan 5 until Plan 5 is complete or blocked.
```

---

# Plan 5: Designer Product Proof

Purpose: Verify the design agent path from the frontend before claiming readiness for Codex-like planning.

## Phase 5.1: Designer Path Visibility

Goal: Make design tasks visible and understandable from the product surface.

### Increment 5.1.1: Submit Visual Critique Task

Submit a visual critique task from the cleaned UI.

Manual check:

- Submit a design critique task.
- Confirm the product surface shows task start and result/failure.

GO when:

- Visual critique path is visible from `/coding`.

### Increment 5.1.2: Submit Responsive/Mobile Check Task

Submit a responsive/mobile check task.

Manual check:

- Submit a responsive check request.
- Confirm desktop/mobile or viewport context is represented in the result.

GO when:

- Responsive design path is visible from `/coding`.

### Increment 5.1.3: Submit Component Mapping Or Design Handoff Task

Submit a component mapping or design handoff task.

Manual check:

- Submit a component/design handoff request.
- Confirm result is readable and not just raw artifacts.

GO when:

- Design handoff path is visible from `/coding`.

### Increment 5.1.4: Readable Designer Result Language

Show designer result in readable product language.

Manual check:

- Confirm the result explains findings, suggested changes, and confidence without backend/evidence dump.

GO when:

- Britton can read the designer result in the product UI.

## Phase 5.2: Designer Result Quality

Goal: Verify design results are useful from the frontend.

### Increment 5.2.1: Understandable Frontend Result

Verify the result is understandable from the frontend.

Manual check:

- Review each design result from Phase 5.1.

GO when:

- The result can guide a coding/design decision.

### Increment 5.2.2: No Raw Backend/Evidence Clutter

Verify the result does not dump raw backend/evidence clutter.

Manual check:

- Confirm artifact paths, proof jargon, and backend routes are absent from the default designer result.

GO when:

- Technical details are confined to Copy report or `/proxy-backend`.

### Increment 5.2.3: Copy Report For Design Failures

Verify Copy report works for design failures.

Manual check:

- Trigger or use a design failure.
- Copy report and confirm it includes scenario, visible failure, and next action.

GO when:

- A design failure can be handed off cleanly.

### Increment 5.2.4: Desktop And Mobile Design Proof

Verify desktop and mobile design proof are both represented.

Manual check:

- Confirm at least one desktop and one mobile/responsive observation appears in proof or result.

GO when:

- Design proof is not desktop-only unless a blocker explains why.

## Phase 5.3: Designer Readiness Classification

Goal: Make an honest designer product-readiness decision.

### Increment 5.3.1: Classify Designer

Classify designer as product-proven, partial, or not ready.

Manual check:

- Review Phase 5.1 and 5.2 evidence.

GO when:

- One readiness class is chosen with a one-paragraph reason.

### Increment 5.3.2: List Exact Blockers

List exact blockers if designer is not ready.

Manual check:

- Each blocker names the product behavior that failed and the smallest likely fix lane.

GO when:

- Blockers are specific enough for future execution.

### Increment 5.3.3: Write Plan 6 Handoff

Write Plan 6 handoff focused on combined proof.

Manual check:

- Handoff starts Plan 6 and summarizes designer status without reopening designer work.

GO when:

- Britton can approve Plan 6 in a new message.

## Plan 5 Acceptance Criteria

- Designer is verified from the product surface, not only artifact evidence.
- Designer failures are readable and copyable.

## Plan 5 Phase Closeout Checks

- Phase 5.1: Designer paths visible.
- Phase 5.2: Designer result quality checked.
- Phase 5.3: Designer readiness classified honestly.

## Plan 5 Closeout Checks

- Files changed listed.
- Checks run listed.
- Manual designer proof listed.
- GO / NO-GO stated for Plan 6.
- Copy-paste Plan 6 handoff provided.

## Plan 5 Execution Closeout - 2026-05-28

Scope: Executed Plan 5 only after Plan 4 acceptance. Plan 0 through Plan 4 were not restarted. No Codex-like features, final CSS polish, or historical Source Proxy/Design Agent/readiness plans were started.

Increment evidence:

- Increment 5.1.1 completed. Manual/product check: visual critique task from `/coding` shows task start and a readable `Designer result`. Evidence: focused Vitest run passed 2 files / 9 tests; `.codex-smoke/plan5-5.1-visual-critique.png`. GO.
- Increment 5.1.2 completed. Manual/product check: responsive/mobile task shows desktop/mobile context in the designer result. Evidence: focused Vitest run passed 2 files / 9 tests; `.codex-smoke/plan5-5.1-responsive-mobile.png`. GO.
- Increment 5.1.3 completed. Manual/product check: component mapping/design handoff task shows a compact handoff result instead of raw artifacts. Evidence: focused Vitest run passed 2 files / 9 tests; `.codex-smoke/plan5-5.1-component-handoff.png`. GO.
- Increment 5.1.4 completed. Manual/product check: designer result explains findings, suggested changes, target context, and confidence in readable product language. Evidence: focused Vitest run passed 2 files / 9 tests. GO.
- Increment 5.2.1 completed. Manual Chromium check: all three design results can guide a design/coding decision from the frontend. Evidence: Chromium result extraction found Findings, Suggested changes, and Confidence for critique, responsive, and handoff cases. GO.
- Increment 5.2.2 completed. Manual Chromium check: default designer result does not include artifact paths, proof jargon, grep wording, or backend routes. Evidence: Chromium `noBackendClutter: true` for all three cases. GO.
- Increment 5.2.3 completed. Manual Chromium check: Copy report works for design failures/missing scope and includes scenario, visible failure, target, result, and next action. Evidence: clipboard read after `Copy report` for critique, responsive, and handoff cases. GO.
- Increment 5.2.4 completed. Manual Chromium check: desktop visual critique and handoff proof plus mobile responsive proof are represented. Evidence: screenshots listed below. GO.
- Increment 5.3.1 completed. Classification: designer is partial. Reason: `/coding` now proves the designer product surface can represent critique, responsive review, design handoff, readable result language, and failure report handoff; however this Plan 5 proof uses product-surface deterministic designer summaries rather than proving a live unmocked design agent performs original visual inspection from screenshots or DOM context. GO.
- Increment 5.3.2 completed. Exact blockers: live unmocked designer critique needs product proof from an actual screen observation; responsive/mobile results need real viewport-derived observations instead of template context; design failure Copy report is clean but missing-scope design tasks still need a first-class target discovery/intake step. Smallest likely fix lanes: live visual observation proof lane, responsive evidence lane, and design intake/target-discovery lane. GO.
- Increment 5.3.3 completed. Plan 6 handoff below starts combined proof and summarizes designer as partial without reopening designer work. GO.

Phase closeout:

- Phase 5.1: Designer paths visible. GO.
- Phase 5.2: Designer result quality checked. GO.
- Phase 5.3: Designer readiness classified honestly as partial. GO.

Files changed:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `src/app/coding/__tests__/page.test.tsx`
- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`

Checks run:

- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/app/coding/__tests__/page.test.tsx`
- `npm run typecheck`
- Chromium designer product-surface checks against `http://127.0.0.1:3102/coding`.

Manual designer proof:

- Visual critique: `.codex-smoke/plan5-5.1-visual-critique.png`, result includes findings, suggested changes, target context, and confidence.
- Responsive/mobile: `.codex-smoke/plan5-5.1-responsive-mobile.png`, result includes desktop and mobile context.
- Component handoff: `.codex-smoke/plan5-5.1-component-handoff.png`, result includes compact component map/handoff language.

Plan 5 result: GO, with designer classified partial.

GO / NO-GO for Plan 6: GO only after Britton approves Plan 6 in a new message.

Copy-paste Plan 6 handoff:

```text
You are Codex inside the SpiritOS repository.

Start Plan 6 only from the active roadmap:

docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md

Plan 0, Plan 1, Plan 2, Plan 3, Plan 4, and Plan 5 are complete. Do not restart them.

Coder status from Plan 4: partial. Designer status from Plan 5: partial. Both product surfaces can represent their workflows and handoffs, but live unmocked backend/agent usefulness remains unproven.

MISSION:
Execute Plan 6: Coder + Designer Combined Readiness in strict PIVOT workflow.

Do not implement Codex-like features.
Do not start final CSS polish.
Do not restart historical Source Proxy, Design Agent, trial, safety, audit, or readiness plans.

Begin with Plan 6, Phase 6.1, Increment 6.1.1.
Work increment by increment, run relevant checks after each increment, inspect output, fix scoped failures if reasonable, record brief evidence, state GO / NO-GO, and continue within Plan 6 until Plan 6 is complete or blocked.
```

---

# Plan 6: Coder + Designer Combined Readiness

Purpose: Verify coder and designer can support one another before Codex-like feature planning begins.

This plan does not build the Codex-like feature lane.

## Phase 6.1: Combined Task Path

Goal: Prove design-to-code-to-design review can be represented and followed.

### Increment 6.1.1: Designer Critiques Real Screen

Designer critiques `/coding` or another real screen.

Manual check:

- Run or submit a design critique against a real target screen.
- Record visible critique result.

GO when:

- The designer produces a usable critique or exact blocker.

### Increment 6.1.2: Coder Uses Design Result

Coder receives or uses design result as implementation context.

Manual check:

- Submit a small implementation task using the design result.
- Confirm the coder references or applies the design context.

GO when:

- Design result can influence coder behavior from the product flow.

### Increment 6.1.3: Designer Rechecks Target

Designer rechecks target/result if possible.

Manual check:

- Run or request a recheck after coder result.
- Confirm recheck is visible or record why it is blocked.

GO when:

- Recheck either works or has an exact blocker.

### Increment 6.1.4: Product UI Shows Combined Flow

Product UI shows the combined flow clearly.

Manual check:

- Review transcript/status.
- Confirm designer, coder, and recheck steps are distinguishable without backend proof jargon.

GO when:

- Britton can understand the combined flow from `/coding`.

## Phase 6.2: Combined UI Proof

Goal: Make combined status and failure handoff visible.

### Increment 6.2.1: Show Combined State

Show combined state in the product UI.

Manual check:

- Confirm combined flow has a visible status such as Working, Needs input, Finished, or Failed.

GO when:

- Combined work has a clear product state.

### Increment 6.2.2: Show Handoff Status

Show clear handoff status between designer and coder.

Manual check:

- Confirm UI communicates when design output is ready for coder or when coder result is ready for design recheck.

GO when:

- Handoff state is understandable.

### Increment 6.2.3: Copy Combined Diagnostics

Make Copy combined diagnostics work if something fails.

Manual check:

- Trigger or use a combined failure.
- Copy diagnostics/report and confirm it includes both designer and coder context.

GO when:

- Combined failure can be handed to a new chat.

### Increment 6.2.4: Verify Combined Proof On Practical Viewports

Verify combined proof on desktop and mobile/tablet where practical.

Manual check:

- Inspect combined transcript/status at desktop and at least one smaller viewport.

GO when:

- Combined flow stays readable outside desktop or exact blocker is recorded.

## Phase 6.3: Combined Readiness Decision

Goal: Decide whether combined coder + designer workflow is ready enough for the next roadmap.

### Increment 6.3.1: Classify Combined Workflow

Classify combined workflow as ready, partial, or blocked.

Manual check:

- Review Phase 6.1 and 6.2 evidence.

GO when:

- One readiness class is chosen with a one-paragraph reason.

### Increment 6.3.2: List Exact Blockers

List exact blockers if combined workflow is not ready.

Manual check:

- Each blocker names the failed product behavior and smallest likely fix lane.

GO when:

- Blockers are actionable.

### Increment 6.3.3: Write Plan 7 Handoff

Write Plan 7 handoff for final readiness gate.

Manual check:

- Handoff summarizes UI, runner, coder, designer, and combined status.

GO when:

- Britton can approve Plan 7 in a new message.

## Plan 6 Acceptance Criteria

- We know whether coder + designer can work together enough to justify creating the next Codex-like roadmap.
- Combined proof comes from product-visible flow, not only separated artifacts.

## Plan 6 Phase Closeout Checks

- Phase 6.1: Combined task path checked.
- Phase 6.2: Combined UI proof checked.
- Phase 6.3: Combined readiness classified honestly.

## Plan 6 Closeout Checks

- Files changed listed.
- Checks run listed.
- Manual combined proof listed.
- GO / NO-GO stated for Plan 7.
- Copy-paste Plan 7 handoff provided.

## Plan 6 Execution Closeout - 2026-05-28

Scope: Executed Plan 6 only after Plan 5 acceptance. Plan 0 through Plan 5 were not restarted. No Codex-like features, final CSS polish, or historical readiness plans were started.

Increment evidence:

- Increment 6.1.1 completed. Manual/product check: combined task includes a visible designer critique against `/coding` as implementation context. Evidence: focused Vitest run passed 2 files / 10 tests; `.codex-smoke/plan6-6.2-combined-desktop.png`. GO.
- Increment 6.1.2 completed. Manual/product check: combined flow shows `Coder handoff` and names whether target/allowed files are ready or still needed. Evidence: focused Vitest run passed 2 files / 10 tests. GO.
- Increment 6.1.3 completed. Manual/product check: combined flow shows `Designer recheck` as pending after coder result, with exact blocker that no coder result exists yet. Evidence: focused Vitest run passed 2 files / 10 tests. GO.
- Increment 6.1.4 completed. Manual/product check: transcript/status distinguishes `Designer result`, `Combined flow`, designer critique, coder handoff, and designer recheck without backend proof jargon. Evidence: focused Vitest run passed 2 files / 10 tests. GO.
- Increment 6.2.1 completed. Manual/product check: combined state is visible as `Needs input`. Evidence: focused Vitest run passed 2 files / 10 tests. GO.
- Increment 6.2.2 completed. Manual/product check: handoff status explains design output is ready for coder context and coder handoff needs target/allowed files. Evidence: focused Vitest run passed 2 files / 10 tests. GO.
- Increment 6.2.3 completed. Manual/product check: `Copy combined diagnostics` includes task, combined state, designer context, coder context, recheck status, target, and next action. Evidence: focused Vitest run passed 2 files / 10 tests; Chromium clipboard read. GO.
- Increment 6.2.4 completed. Manual viewport check: combined transcript/status is readable on desktop and mobile with no horizontal overflow. Evidence: `.codex-smoke/plan6-6.2-combined-desktop.png`, `.codex-smoke/plan6-6.2-combined-mobile.png`. GO.
- Increment 6.3.1 completed. Classification: combined workflow is partial. Reason: `/coding` now proves the product surface can represent a design-to-code-to-design-review chain, including designer context, coder handoff state, pending recheck, and combined diagnostics; however live unmocked coder and designer agents still do not execute the full loop end to end from product proof. GO.
- Increment 6.3.2 completed. Exact blockers: live designer critique is still deterministic product-surface context, not actual visual inspection; coder handoff can represent design context but live unmocked coder use of that context is not proven; designer recheck is visible but blocked until a real coder result exists. Smallest likely fix lanes: live combined execution proof, design-context-to-coder binding proof, and post-coder visual recheck proof. GO.
- Increment 6.3.3 completed. Plan 7 handoff below summarizes UI, runner, coder, designer, and combined status. GO.

Phase closeout:

- Phase 6.1: Combined task path checked. GO.
- Phase 6.2: Combined UI proof checked. GO.
- Phase 6.3: Combined readiness classified honestly as partial. GO.

Files changed:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `src/app/coding/__tests__/page.test.tsx`
- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`

Checks run:

- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/app/coding/__tests__/page.test.tsx`
- `npm run typecheck`
- Chromium combined-flow checks against `http://127.0.0.1:3102/coding`.

Manual combined proof:

- Desktop combined proof: `.codex-smoke/plan6-6.2-combined-desktop.png`, visible state `Needs input`, with designer critique, coder handoff, and designer recheck.
- Mobile combined proof: `.codex-smoke/plan6-6.2-combined-mobile.png`, visible state `Needs input`, with combined flow readable and no horizontal overflow.
- Combined diagnostics: copied report includes designer context, coder context, pending recheck, target, and next action.

Plan 6 result: GO, with combined workflow classified partial.

GO / NO-GO for Plan 7: GO only after Britton approves Plan 7 in a new message.

Copy-paste Plan 7 handoff:

```text
You are Codex inside the SpiritOS repository.

Start Plan 7 only from the active roadmap:

docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md

Plan 0 through Plan 6 are complete. Do not restart them.

Status summary: /coding UI, cockpit layout, runner, coder surface, designer surface, and combined workflow are product-visible. Coder, designer, and combined readiness are classified partial because live unmocked agent usefulness remains unproven.

MISSION:
Execute Plan 7: Codex-Like Feature Planning Readiness Gate in strict PIVOT workflow.

Do not implement Codex-like features.
Do not create the Codex-like roadmap.
Do not start final CSS polish.
Do not restart historical Source Proxy, Design Agent, trial, safety, audit, or readiness plans.

Begin with Plan 7, Phase 7.1, Increment 7.1.1.
Work increment by increment, run relevant checks after each increment, inspect output, fix scoped failures if reasonable, record brief evidence, state GO / NO-GO, and continue within Plan 7 until Plan 7 is complete or blocked.
```

---

# Plan 7: Codex-Like Feature Planning Readiness Gate

Purpose: Stop here and decide whether the next roadmap can finally be the Codex-like Features Roadmap.

This plan does not implement Codex-like features.

This plan does not create the Codex-like roadmap.

This plan does not create final CSS plan.

This plan does not do final CSS polish.

## Phase 7.1: Readiness Checklist

Goal: Verify all prerequisites for Codex-like feature planning readiness.

### Increment 7.1.1: Confirm /coding UI Clean And Usable

Confirm `/coding` UI is clean and usable.

Manual check:

- Open `/coding`.
- Confirm default cockpit is focused on projects, chats/tasks, composer, transcript, runner, and status/result.

GO when:

- Backend/debug clutter is not dominant.

### Increment 7.1.2: Confirm Trial Runner Clean And Useful

Confirm trial runner is clean and useful.

Manual check:

- Inspect runner and latest result/report behavior.

GO when:

- Runner communicates useful outcomes without artifact-dashboard clutter.

### Increment 7.1.3: Confirm Coder Proof Status

Confirm coder proof status.

Manual check:

- Review Plan 4 closeout.

GO when:

- Coder is product-proven or blockers are exact and bounded.

### Increment 7.1.4: Confirm Designer Proof Status

Confirm designer proof status.

Manual check:

- Review Plan 5 closeout.

GO when:

- Designer is product-proven or blockers are exact and bounded.

### Increment 7.1.5: Confirm Combined Proof Status

Confirm combined proof status.

Manual check:

- Review Plan 6 closeout.

GO when:

- Combined workflow is ready/partial with exact status, not a vague harness claim.

### Increment 7.1.6: Confirm Copy Diagnostics Without Backend Drawers

Confirm diagnostics can be copied without opening backend drawers.

Manual check:

- Trigger or use failure states from coder, designer, runner, and combined flow where practical.

GO when:

- Copy diagnostics/report is enough for handoff.

## Phase 7.2: Blocker Decision

Goal: Decide what still blocks Codex-like feature planning.

### Increment 7.2.1: List Planning Blockers

List blockers that still prevent Codex-like feature planning.

Manual check:

- Include only blockers that prevent the next roadmap from being meaningful.

GO when:

- The blocker list is short and real.

### Increment 7.2.2: Separate Must-Fix-Now From Can-Wait

Separate must-fix-now blockers from can-wait blockers.

Manual check:

- Must-fix-now means Codex-like planning would be fantasy without it.
- Can-wait means the next roadmap can own it.

GO when:

- Britton can make a decision without another readiness essay.

### Increment 7.2.3: GO / NO-GO For Next Roadmap

Decide GO / NO-GO for creating the next Codex-like Features Roadmap.

Manual check:

- Decision references Plan 7.1 and 7.2 evidence.

GO when:

- The decision is explicit.

## Phase 7.3: Next-Roadmap Request Packet

Goal: End with a short request packet or a smallest fix list, then stop.

### Increment 7.3.1: If GO, Produce Request Packet

If GO, produce a short request packet for the future Codex-like Features Roadmap.

Manual check:

- Packet names current product readiness, intended next roadmap topic, and explicit stop before creation.

GO when:

- Britton can approve creation of the future roadmap in a new message.

### Increment 7.3.2: If NO-GO, Produce Smallest Fix List

If NO-GO, produce the smallest fix list needed before the future roadmap.

Manual check:

- Fix list contains only blocking product work.

GO when:

- The path to GO is small and executable.

### Increment 7.3.3: Stop And Ask Britton

Stop and ask Britton before creating any new roadmap.

Manual check:

- No Codex-like roadmap file is created in Plan 7.
- No final CSS polish plan is created.

GO when:

- The next action requires Britton approval.

## Plan 7 Acceptance Criteria

- The roadmap ends with a clear GO / NO-GO for creating the Codex-like Features Roadmap.
- The roadmap stops before Codex-like implementation, Codex-like roadmap creation, final CSS planning, and final CSS polish.

## Plan 7 Phase Closeout Checks

- Phase 7.1: Readiness checklist complete.
- Phase 7.2: Blocker decision complete.
- Phase 7.3: Request packet or smallest fix list complete.

## Plan 7 Closeout Checks

- Files changed listed.
- Checks run listed.
- Manual proof listed.
- GO / NO-GO stated for creating the next Codex-like Features Roadmap.
- Explicit STOP stated before any new roadmap creation.

## Plan 7 Execution Closeout - 2026-05-28

Scope: Executed Plan 7 only after Plan 6 acceptance. Plan 0 through Plan 6 were not restarted. No Codex-like features were implemented. No Codex-like Features Roadmap was created. No final CSS plan or final CSS polish was created.

Increment evidence:

- Increment 7.1.1 completed. Manual/product check: `/coding` default cockpit is focused on project/task context, transcript, composer, runner, status/result, and diagnostics links rather than backend/debug clutter. Evidence: focused Vitest run passed 2 files / 10 tests; Plan 2 result GO. GO.
- Increment 7.1.2 completed. Manual/product check: runner shows Run trial, Status, Score, Result, Category, Outcome mix, and Copy report only after a result; artifact-dashboard clutter is absent. Evidence: focused Vitest run passed 2 files / 10 tests; Plan 3 result GO. GO.
- Increment 7.1.3 completed. Manual check: Plan 4 closeout reviewed. Coder is classified partial, with exact bounded blockers around live unmocked preview proof, target discovery/scoping, and no-op result state. GO.
- Increment 7.1.4 completed. Manual check: Plan 5 closeout reviewed. Designer is classified partial, with exact bounded blockers around live visual observation proof, responsive evidence, and design intake/target discovery. GO.
- Increment 7.1.5 completed. Manual check: Plan 6 closeout reviewed. Combined workflow is classified partial, with exact bounded blockers around live combined execution, design-context-to-coder binding, and post-coder visual recheck proof. GO.
- Increment 7.1.6 completed. Manual/product check: coder Copy diagnostics, runner Copy report, designer Copy report, and combined Copy combined diagnostics are available from product surfaces. Evidence: focused Vitest run passed 2 files / 10 tests and prior Chromium clipboard checks from Plans 3, 5, and 6. GO.
- Increment 7.2.1 completed. Planning blockers listed: live unmocked agent usefulness remains unproven for coder, designer, and combined loops; target discovery/scoping still needs real proof for messy prompts; no-op should become first-class useful result instead of failure-like blocked state. GO.
- Increment 7.2.2 completed. Must-fix-now versus can-wait separated: no must-fix-now blocker prevents creating the next roadmap because the blockers are exact, bounded, and should be first-class work in that roadmap. Can-wait/next-roadmap-owned blockers are live unmocked proof, target discovery, no-op useful state, and combined post-coder recheck. GO.
- Increment 7.2.3 completed. Decision: GO for creating the next Codex-like Features Roadmap, but only in a new message after Britton approval. The next roadmap must start with live unmocked product proof and cannot treat partial readiness as full agent capability. GO.
- Increment 7.3.1 completed. Request packet produced below for the future Codex-like Features Roadmap. GO.
- Increment 7.3.2 completed. Since decision is GO, smallest fix list is not the primary output; the exact bounded blockers are included as required first roadmap topics. GO.
- Increment 7.3.3 completed. Explicit stop recorded: no new roadmap file was created, no Codex-like implementation was started, and the next action requires Britton approval. GO.

Phase closeout:

- Phase 7.1: Readiness checklist complete. GO.
- Phase 7.2: Blocker decision complete. GO.
- Phase 7.3: Request packet complete and stopped before roadmap creation. GO.

Files changed:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `src/app/coding/__tests__/page.test.tsx`
- `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`

Checks run:

- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/app/coding/__tests__/page.test.tsx`
- `npm run typecheck`
- Manual evidence review of Plan 2 through Plan 6 closeouts and `.codex-smoke` proof files.

Manual proof:

- Plan 2: `/coding` cockpit layout GO.
- Plan 3: runner GO.
- Plan 4: coder product surface GO, coder readiness partial with exact blockers.
- Plan 5: designer product surface GO, designer readiness partial with exact blockers.
- Plan 6: combined product surface GO, combined readiness partial with exact blockers.
- Current check: focused Vitest passed 2 files / 10 tests; typecheck passed.

Plan 7 result: GO.

GO / NO-GO for creating the next Codex-like Features Roadmap: GO, after Britton approval in a new message.

Future roadmap request packet:

```text
You are Codex inside the SpiritOS repository.

Create the next roadmap only after Britton explicitly approves this request.

Requested roadmap:
Codex-like Features Roadmap for SpiritOS /coding.

Current readiness:
- /coding UI is clean enough for planning.
- Core cockpit layout is usable.
- Trial runner is clean and product-readable.
- Coder product surface is partial: task intake, transcript, result/failure, diagnostics, and realistic task-shape representation are visible, but live unmocked coder usefulness is not yet proven.
- Designer product surface is partial: critique, responsive, handoff, readable result, and Copy report are visible, but live unmocked visual inspection is not yet proven.
- Combined workflow is partial: designer-to-coder-to-recheck flow is visible and copyable, but live unmocked end-to-end execution is not yet proven.

Required first topics for the next roadmap:
1. Live unmocked coder proof from /coding.
2. Live unmocked designer visual proof from /coding.
3. Live combined designer-to-coder-to-designer-recheck proof.
4. Target discovery/scoping for messy prompts.
5. First-class no-op/already-satisfied useful result state.
6. Only after those proof lanes, plan Codex-like cockpit features.

Hard stops:
- Do not start implementation while creating the roadmap.
- Do not create final CSS polish work.
- Do not treat old harness S+ claims as full product proof.
```

Explicit STOP:

- No Codex-like feature implementation was performed.
- No Codex-like Features Roadmap was created.
- No final CSS plan or final CSS polish was created.
- Wait for Britton to approve creating the next roadmap in a new message.

---

# Final Readiness Gate

SpiritOS is ready to ask for a new Codex-like Features Roadmap only when all of these are true:

- `/coding` default UI is clean enough and no longer reads as an operator/debug console.
- Backend/debug clutter is moved to `/proxy-backend`, logs, artifacts, or copied diagnostics.
- Trial runner is usable from the product surface.
- Coder path is product-proven or remaining blockers are exact and small enough not to invalidate planning.
- Designer path is product-proven or remaining blockers are exact and small enough not to invalidate planning.
- Combined coder + designer flow is verified or its remaining blockers are exact and small enough not to invalidate planning.
- Copy diagnostics/report works for meaningful failures without requiring drawer babysitting.
- Plan 7 closeout states GO for creating the next Codex-like Features Roadmap.
- Britton approves creating that next roadmap in a new message.

If any required item is false, the decision is NO-GO and Plan 7 must name the smallest product fix list before the future roadmap.

# Explicit Stop

Stop after this roadmap reaches the Plan 7 readiness decision.

Do not implement Codex-like features under this roadmap.

Do not create the Codex-like Features Roadmap under this roadmap.

Do not create or execute final CSS polish under this roadmap.

Wait for Britton to approve the next action.
