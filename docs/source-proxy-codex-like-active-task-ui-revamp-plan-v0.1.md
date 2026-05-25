# Source Proxy Codex-Like Active Task UI Revamp Plan v0.1

Status: docs-only PIVOT plan; BLOCKED before implementation

Owner: Britton

Date: 2026-05-25

Lane: Source Proxy `/coding` UI information architecture before PR-8.3 proof, wrapper, and final CSS

## Authority Boundary

This document is planning only. It does not approve implementation, CSS edits, wrapper work, provider/API calls, Run 10/25/100 execution, real task gauntlet execution, apply, execute-approved, commit, push, branch/worktree creation, stash, reset, clean, queue/worker execution, Design Agent runtime/apply work, config/env/auth changes, or hidden mutation.

The target is a cleaner active coding task surface, not new runtime authority. Any future implementation must start with the first increment only and ask Britton before widening scope.

## References Reviewed

Repo references:

- `docs/source-proxy-codex-style-ui-reduction-pr-8-3-gauntlet-master-plan-v0.1.md`
- `docs/source-proxy-codex-style-ui-reduction-pr-8-3-gauntlet-new-chat-handoff-v0.1.md`
- `docs/source-proxy-preflight-pr-8-real-preflight-coding-workflow-proof-v0.1.md`
- `docs/source-proxy-preflight-pr-10-wrapper-final-css-decision-gate-v0.1.md`
- `docs/source-proxy-preflight-readiness-master-roadmap-v0.1.md`
- `docs/source-proxy-codex-class-production-master-plan-v1.0.md`
- `docs/source-proxy-codex-class-phase-2-productive-trial-matrix.md`
- `docs/source-proxy-manual-100-frontend-diagnostic-closeout.md`
- `docs/plan-index.md`
- `src/app/coding/page.tsx`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `src/lib/coding/*`
- `source_proxy/api/*`
- `source_proxy/codex/*`
- `source_proxy/tests/*`

External references verified live on 2026-05-25:

- OpenAI Codex CLI docs: `https://developers.openai.com/codex/cli`
- OpenAI Codex sandboxing and approvals: `https://developers.openai.com/codex/concepts/sandboxing`
- OpenAI Codex subagents: `https://developers.openai.com/codex/subagents`
- OpenAI Codex app worktrees: `https://developers.openai.com/codex/app/worktrees`
- GitHub Copilot cloud agent: `https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent`
- Nielsen Norman Group progressive disclosure: `https://www.nngroup.com/articles/progressive-disclosure/`
- Material 3 side sheets: `https://m3.material.io/components/side-sheets`
- WAI-ARIA modal dialog pattern: `https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/`

Research implications:

- Codex-like work surfaces should foreground an active task thread and keep sandbox/approval truth visible but compact.
- Codex subagent docs emphasize explicit user request, inherited sandbox policy, and surfaced approvals, so Source Proxy must not hide authority behind drawer movement.
- Codex worktree docs treat each task/thread as an environment-scoped unit, which supports task-scoped evidence drawers and no cross-task authority.
- GitHub Copilot cloud agent shows a branch/PR-oriented background-agent pattern, but Source Proxy is not adopting that authority; the useful pattern is transparent task state and reviewable diffs.
- NN/g progressive disclosure supports moving advanced details into secondary areas while making the initial display signal what matters.
- Material side sheets support supplementary task content. If any drawer is modal, WAI-ARIA dialog focus trapping, escape close, and inert background behavior apply.

## 1. Current State Summary

The current `/coding` entry renders `CodingCommandCenterShell`. The page already contains important safety and evidence truth, but the default first viewport reads more like a cockpit/dashboard than an active coding task window.

First-viewport clutter observed from source and tests:

- Left app nav and chat list are useful primary navigation.
- Workspace/project selector is visible with SpiritOS selected, `C:\Projects` future/unavailable, remote workspace skipped, and start-new-project placeholder disabled.
- Provider/model selector is visible with local/default intent and GPT/cloud unavailable/config-blocked truth.
- Active task area and composer are primary, but compete with many status, safety, diagnostic, and proof surfaces.
- Trial prompt widget, Run 10/25/100 controls, 100 diagnostic summary, blocker cards, and compact diagnostic widget are visible by default.
- Task State, Task Timeline, Progress Details and Receipts, proof run controls, raw diagnostic values, backend truth, settings, usage/time, alerts, and helper/fleet cards create repeated secondary panels.
- Safety/approval/apply/verify copy is present in many places, which is safe but noisy.

Surface classification:

| Surface | Current role | Target role |
| --- | --- | --- |
| App/project/chat navigation | Primary | Stay visible left |
| Active task transcript/story | Primary | Become center of the screen |
| Composer | Primary | Stay bottom-fixed or bottom-aligned |
| Active project/provider/safety chips | Primary compact truth | Stay top compact |
| Approval/apply/verify gates | Primary when relevant | Inline only when a task has preview/apply state |
| Task State / Task Progress right wall | Secondary status | Hidden when idle; compact active task status only |
| Trial prompts and Run 10/25/100 controls | Diagnostics-only | Diagnostics drawer |
| 100 diagnostic report and blocker cards | Diagnostics-only | Diagnostics drawer |
| Receipts, copy diag, raw proof, timeline detail | Evidence-only | Evidence/Receipts drawer |
| Settings/provider/workspace/backend/usage/time/alerts | Secondary configuration truth | Settings drawer |
| `C:\Projects`, remote skipped, start-new-project | Future/unwired | Project drawer or compact selector with unavailable copy |
| Design Agent packet display | Read-only future integration | Design intake drawer only |
| Repeated no-authority badges | Safety proof | Reduce to compact chips plus drawer details |

Test proof observed:

- Existing shell tests assert workspace/provider honesty, New Chat, chat list, trial prompts, Run controls, diagnostic widget, no forbidden controls, provider switching without calls, receipt copy, apply locks, verification separation, and local task-story reconnect behavior.
- The manual 100 frontend diagnostic closeout records terminal 25 and 100 reruns accepted with 100 total prompts, 8 productive previews, 1 already-satisfied no-op, 91 safe blockers, 0 unsafe failures, 0 unexpected files, and all authority fields false; browser verification remained pending in that closeout.

Dirty-tree state observed on 2026-05-25:

- Branch: `lane/main-cleanup-20260524`.
- Dirty tree existed before this docs task.
- Modified files include `docs/plan-index.md`, many `source_proxy/cartographer/*` and `source_proxy/tests/test_cartographer_*` files, `src/app/map/*`, `src/components/coding/CodingCommandCenterShell.tsx`, and `src/components/coding/__tests__/coding-command-center-shell.test.tsx`.
- Many untracked design-agent/cartographer docs are present.
- This plan must not clean, stage, revert, or explain away that state.

PR gate status:

- PR-8.3 is BLOCKED pending Britton approval for fresh browser/manual Run 10/25/100 proof and real coding task gauntlet.
- PR-10 is BLOCKED for wrapper/final CSS authority.
- Wrapper and final CSS remain later gates, not part of this revamp implementation.

## 2. Target A-Grade UI

Target default `/coding` screen:

- Left: app/project/chat navigation remains usable.
- Center: active coding chat/task transcript is the main surface, with task messages, preview status, human review prompts, and concise task story.
- Bottom: composer is the clear next-action point.
- Top: compact chips show active project, provider/model, safety/dirty-tree truth, and current task state.
- Idle state: no persistent right-side Task State / Task Progress wall.
- No upfront Safety/Provider/Workspace card wall.
- Trial prompt widget is not visible by default.
- Raw receipts, evidence, diagnostic reports, and proof logs are not visible by default.
- Approval/apply/verify stays honest and appears only where task state requires it.
- Provider availability remains truthful: local/default preview intent; GPT/cloud unavailable unless real config exists; no fake calls.
- Dirty-tree state remains compactly visible and drawer-accessible.

The default screen should feel like an active Codex task window: one thread, one composer, compact truth, and secondary detail one click away.

## 3. Pull-Out Drawer Model

Settings drawer:

- Contains provider/model selector, project/workspace details, usage/time, notifications, backend truth, and display-only config state.
- Does not run provider calls, change env/auth/config, create projects, restart servers, or persist settings unless a later approved implementation adds a safe route.
- Default trigger: top chip or settings icon.

Diagnostics drawer:

- Contains trial prompts, Run 10/25/100 controls, blocker summaries, accepted terminal 100 diagnostic report, PR-8.3 checklist, raw diagnostic status values, and proof-run controls.
- It is the only default location for trial prompt widgets after the revamp.
- It must say diagnostic controls are preview/manual proof only and add no provider, queue, worker, apply, commit, or push authority.

Evidence/Receipts drawer:

- Contains receipts, copy diag, timeline details, folder proof, dirty-tree evidence, raw proof, rollback notes, command/result fields, and task story export.
- Evidence is scoped to the selected task only.
- Empty state should say no evidence exists for the selected task rather than showing unrelated global proof.

Project drawer or compact project selector:

- Shows SpiritOS selected.
- Shows `C:\Projects` as future/unavailable/bridge-gated unless a real approved bridge exists.
- Shows remote workspace skipped.
- Hides or disables start-new-project placeholder until safe creation exists.
- Does not read Windows folders, create projects, mutate workspaces, or start bridge calls.

Design intake drawer:

- Displays Design Agent packet intake as read-only/proposal evidence only.
- No design apply/runtime/provider/queue/worker/git authority.
- Hidden by default until a real packet is selected or a later read-only integration diagnostic is approved.

Accessibility model:

- Non-modal drawers should behave as supplementary side sheets, preserving the active task context.
- Modal drawers must follow WAI-ARIA modal dialog expectations: focus moves inside, tab focus stays inside, Escape closes, and background content is inert.

## 4. Safety Preservation Matrix

| Moved/hidden surface | Where it moves | Visible proof that remains | Gate preservation |
| --- | --- | --- | --- |
| Provider/model cards | Settings drawer | Top provider chip: local/default or GPT/cloud unavailable | No provider call; unavailable stays unavailable |
| Workspace/project cards | Project drawer or selector | Top project chip: SpiritOS selected; future targets gated | No folder read, bridge, project creation, branch, or worktree action |
| Task State / Task Progress wall | Inline compact task status plus Evidence drawer details | Current state chip: idle, preview, blocked, needs review, done | Apply/approval/verify state still shown when relevant |
| Trial prompt widget | Diagnostics drawer | Diagnostics chip shows available/pending proof | Run 10/25/100 remains manual proof, not hidden execution |
| Run 10/25/100 controls | Diagnostics drawer | Diagnostics chip and PR-8.3 status | Controls remain disabled/gated as current authority requires |
| 100 report/blocker cards | Diagnostics drawer | Compact grade/blocker chip if useful | B- blockers stay visible on demand; no fake A-grade claim |
| Receipts/copy diag/raw proof | Evidence/Receipts drawer | Evidence chip: receipt available/unavailable | Receipts remain copy-only and task-scoped |
| Dirty-tree evidence | Evidence drawer plus top chip | Dirty-tree chip: clean/dirty/unknown at inspection time | Dirty state remains accessible; no cleanup/stage/reset |
| Backend truth/settings/usage/time/alerts | Settings drawer | Settings chip can show unavailable/config blocked | No fake backend/usage/notification authority |
| Design Agent packet display | Design intake drawer | Optional read-only packet chip | No design runtime/apply/provider/queue/worker/git authority |

Safety rules:

- Hiding a panel cannot hide authority truth. At least one compact chip must disclose unavailable/gated/dirty states.
- Drawer content is display or preview control only unless a future plan explicitly authorizes more.
- Approval, apply, verify, commit, and push remain separate. No drawer can combine them.
- No hidden authority is introduced by moving UI.

## 5. Project And Multi-Task Preview Plan

Test scenarios:

- SpiritOS selected project: default selected chip and project drawer agree; evidence drawer shows only SpiritOS task proof.
- `C:\Projects`: remains future/unavailable unless a real bridge exists; no folder access, write, project creation, or bridge call.
- Multiple preview tasks in same project: chat list can switch tasks; each task keeps its own transcript, preview status, receipts, blockers, and dirty-tree evidence.
- Task isolation: evidence drawer updates when selected chat/task changes and never shows another task's receipt as active.
- Switching chats/tasks: composer draft, provider intent, workspace context, preview state, and receipt availability follow selected chat.
- Reconnect/refresh: current local task story restores only current-session state and labels durable history gated.
- No cross-task apply/commit/push authority: selected task proof cannot approve another task; commit/push controls remain absent.

Manual acceptance should include at least two preview tasks in SpiritOS, one blocked/no-op state, one future `C:\Projects` selection, refresh/reconnect, and evidence drawer switching.

## 6. Productive-Yield Improvement Plan

The current B- blockers are safety-preserving but productivity-limiting. The UI should turn each blocker into clear copy plus a safe next action without broadening scope.

| Blocker | Better UI copy | Better next safe action | Later data/target improvement | Avoid unsafe broadening |
| --- | --- | --- | --- | --- |
| `frontend_preview_route_gap` | "The preview could not show the frontend route clearly enough for review." | Ask for the route/component and expected visible change; offer diagnostics drawer details. | Map prompt to route/component/test hints. | Do not infer broad app-wide UI ownership. |
| `scope_too_broad` | "This request spans too much. Pick one component, route, or file group." | Provide a one-click copyable narrower prompt. | Add scope-size scoring and file-family suggestions. | Do not relax allowed files automatically. |
| `missing_target_context` | "The task needs a target route, component, file, or expected output." | Ask Britton to add the target or choose from detected candidates. | Improve target candidate extraction from repo context. | Do not guess a write target silently. |
| `protected_path` | "This touches a protected area and is correctly blocked." | Keep blocked; ask for a separate protected-path plan if needed. | Better protected path explanation and owner map. | Do not add bypass controls. |
| `already_satisfied_noop_route_gap` | "This may already be done, but the no-op proof is too weak." | Show what matched and ask for confirmation or a narrower proof request. | Stronger no-op evidence receipts. | Do not create a cosmetic diff just to satisfy the task. |
| `backend_diff_generation_gap` | "The backend could not create a useful preview diff for this task shape." | Ask for metadata/target detail or mark as backend diagnostic follow-up. | Improve prompt-packet fallback and diff generation context. | Do not route to live execution. |
| `no_diff_route_gap` | "The preview finished without a useful diff or no-op explanation." | Show whether likely no-op, missing context, or generator miss. | Add route outcome taxonomy. | Do not treat no diff as success without proof. |
| `target_unresolved` | "The target could not be resolved safely." | Ask for exact file/route/component/test before rerun. | Improve target resolver and candidate display. | Do not write to nearest matching file. |

## 7. Implementation Phases

Every phase below is future work and requires Britton permission before implementation. Each phase forbids provider/API calls, apply, execute-approved, commit, push, stash, reset, clean, checkout, branch/worktree creation, queue/worker execution, config/env/auth edits, hidden mutation, and unrelated file edits.

### Phase 1: Active Task Default Screen

Goal: Make the default first viewport center on active task transcript and composer without building full drawer architecture.

Likely files: `src/components/coding/CodingCommandCenterShell.tsx`, `src/components/coding/__tests__/coding-command-center-shell.test.tsx`.

Forbidden actions: CSS files, wrapper work, backend/provider/API edits, Run 10/25/100, real gauntlet, apply/commit/push.

Terminal check block:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git diff --check
grep -nE "Task State|Task Progress|Proxy Trial Prompts|Provider|Workspace|Approval|Apply|Verify|diagnostic|receipt|authority" src/components/coding/CodingCommandCenterShell.tsx | head -240
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Manual browser checklist: active transcript dominates center; composer is bottom; project/chat nav usable; no idle right wall; compact chips show project/provider/safety; trial widget not first-viewport default.

Stop condition: any safety truth disappears, tests fail unrepaired, or implementation needs CSS/backend/provider changes.

Rollback path: revert only Phase 1 changes in the shell/test files; leave unrelated dirty files alone.

Next permission gate: Ask Britton before drawer shell work.

### Phase 2: Settings/Diagnostics/Evidence Drawer Shell

Goal: Add drawer triggers and empty shells without moving controls yet.

Likely files: `CodingCommandCenterShell.tsx`, shell test.

Forbidden actions: CSS files unless explicitly approved, provider/backend mutations, drawer controls that execute actions.

Terminal check block: same as Phase 1 plus grep for drawer labels.

Manual browser checklist: three drawers open/close; focus behavior works; active task remains readable; no new action authority appears.

Stop condition: drawers obscure core task flow or behave modally without focus handling.

Rollback path: remove drawer shell additions only.

Next permission gate: Ask before moving diagnostics.

### Phase 3: Move Trial Prompts And Proof Controls Into Diagnostics

Goal: Relocate trial prompts, Run 10/25/100 controls, blocker cards, 100 report, PR-8.3 checklist.

Likely files: shell and shell test.

Forbidden actions: running diagnostics, changing runner logic, backend edits.

Terminal check block: shell test and grep for Run controls location labels.

Manual browser checklist: trial widget hidden by default; Diagnostics drawer contains all controls and no-authority copy.

Stop condition: PR-8.3 status becomes ambiguous or controls look like live authority.

Rollback path: restore prior diagnostic render location.

Next permission gate: Ask before moving evidence.

### Phase 4: Move Receipts/Evidence Into Evidence/Receipts

Goal: Relocate receipt, copy diag, timeline details, raw proof, folder proof, dirty-tree proof, rollback notes.

Likely files: shell and shell test.

Forbidden actions: evidence-store writes, receipt persistence changes, git cleanup.

Terminal check block: shell test and receipt/evidence grep.

Manual browser checklist: selected task evidence is available; unrelated task evidence is not shown as active; dirty-tree proof remains accessible.

Stop condition: receipt copy breaks or evidence is cross-task.

Rollback path: restore prior evidence render location.

Next permission gate: Ask before project selector cleanup.

### Phase 5: Project Selector Cleanup And Multi-Task Preview Test States

Goal: Clean project selector states and prove task switching/evidence scoping.

Likely files: shell, workspace helper tests if needed.

Forbidden actions: Windows bridge calls, project creation, branch/worktree creation.

Terminal check block: shell test plus workspace context tests if touched.

Manual browser checklist: SpiritOS selected; `C:\Projects` unavailable; remote skipped; start-new-project hidden/disabled; two tasks keep separate evidence.

Stop condition: future project appears available without bridge proof.

Rollback path: restore selector changes.

Next permission gate: Ask before browser/manual acceptance.

### Phase 6: Browser/Manual Acceptance

Goal: Britton reviews the UI revamp without executing Run 10/25/100 or real gauntlet.

Likely files: closeout doc only if accepted.

Forbidden actions: implementation changes unless a defect fix is separately approved.

Terminal check block:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git diff --check
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx
```

Manual browser checklist: A-grade default screen, drawer access, truthful chips, no hidden authority.

Stop condition: Britton rejects default layout or finds safety evidence hidden too deeply.

Rollback path: use phase diffs to revert UI changes only.

Next permission gate: Ask before Run 10.

### Phase 7: Run 10

Goal: Fresh PR-8.3 Run 10 browser/manual proof.

Likely files: proof/closeout docs only unless failures require approved fixes.

Forbidden actions: Run 25/100, real gauntlet, apply/commit/push.

Terminal check block: baseline status, diff check, approved Run 10 command/checklist from active PR-8.3 plan.

Manual browser checklist: diagnostics drawer handles Run 10; receipts copied; 0 unsafe failures; no authority drift.

Stop condition: unsafe failure, unexpected files, hidden execution, or unreadable proof.

Rollback path: no source rollback expected; record failed proof.

Next permission gate: Ask before Run 25.

### Phase 8: Run 25

Goal: Fresh PR-8.3 Run 25 proof after Run 10 acceptance.

Likely files: proof/closeout docs only unless approved fixes.

Forbidden actions: Run 100, real gauntlet, apply/commit/push.

Terminal/manual checks: same pattern scaled to Run 25.

Stop condition: unsafe failure, unexpected files, authority drift, or proof unreadable.

Rollback path: record failed proof; no cleanup.

Next permission gate: Ask before Run 100.

### Phase 9: Run 100

Goal: Fresh PR-8.3 Run 100 proof accepted by Britton.

Likely files: proof/closeout docs only unless approved fixes.

Forbidden actions: real gauntlet, wrapper, final CSS, provider calls.

Terminal/manual checks: approved Run 100 command/checklist; dirty-tree before/after.

Stop condition: unsafe failure, unexpected files, authority drift, or unacceptable blocker clarity.

Rollback path: record failed proof.

Next permission gate: Ask before real coding task gauntlet.

### Phase 10: Real Coding Task Gauntlet

Goal: Run approved low-to-mid coding tasks with receipts and task isolation.

Likely files: only exact files named by the approved gauntlet task.

Forbidden actions: broad tasks, protected paths, commit/push, cross-task apply.

Terminal/manual checks: per-task status, diff check, focused tests, receipt review.

Stop condition: wrong-file preview, unapproved apply, missing verification, or dirty-tree confusion.

Rollback path: task-specific rollback notes only; no stash/reset/clean.

Next permission gate: Ask before blocker reduction.

### Phase 11: Blocker Reduction Pass

Goal: Improve B- blocker copy/data routing after proof.

Likely files: coding helper modules, shell tests, possibly Source Proxy preview tests if approved.

Forbidden actions: unsafe broadening, provider/live execution, protected-path relaxation.

Terminal/manual checks: focused helper tests, shell test, diff check.

Stop condition: blocker copy implies unsafe route or target guessing.

Rollback path: revert blocker-copy/helper changes only.

Next permission gate: Ask before Design Agent read-only intake diagnostic.

### Phase 12: Design-Agent Read-Only Intake Integration Diagnostic

Goal: Display design packet intake read-only after coding proof.

Likely files: exact read-only display/test files approved later.

Forbidden actions: design apply/runtime/provider/queue/worker/git authority.

Terminal/manual checks: read-only packet tests and shell display checks.

Stop condition: packet can mutate code or trigger runtime.

Rollback path: remove read-only display integration only.

Next permission gate: Ask before combined diagnostic.

### Phase 13: Design/Coding Combined Diagnostic

Goal: Prove read-only design packet plus coding task display can coexist without authority drift.

Likely files: docs/proof plus focused display tests.

Forbidden actions: design apply, coding apply, provider calls, queues/workers.

Terminal/manual checks: combined diagnostic checklist and safety grep.

Stop condition: authority confusion or cross-lane evidence leak.

Rollback path: record failed diagnostic; revert only approved display changes if needed.

Next permission gate: Ask before wrapper/final CSS decision.

### Phase 14: Later Wrapper/Final CSS Only After Gates Pass

Goal: Begin wrapper/final CSS only after PR-8.3, real gauntlet, and design/coding diagnostics are accepted.

Likely files: separately approved wrapper/CSS files.

Forbidden actions: starting from this plan alone.

Terminal/manual checks: PR-10 successor gate must define them.

Stop condition: any attempt to treat this plan as wrapper/CSS approval.

Rollback path: use future wrapper/CSS plan.

Next permission gate: Britton explicit wrapper/final CSS approval.

## 8. Acceptance Rubric

A-grade requires:

- Clean active task UI.
- First viewport is not cluttered.
- Trial prompts off by default.
- Settings live in a true drawer or equivalent secondary surface.
- Evidence is available but not noisy.
- 0 hidden mutation.
- 0 unapproved apply, execute-approved, commit, or push.
- 0 fake provider availability.
- 0 wrong-file preview.
- Better blocker clarity for the B- categories.
- Run 10/25/100 proof accepted after explicit Britton permission.
- Real task gauntlet accepted after explicit Britton permission.
- Design Agent remains read-only until after coding proof.

## 9. Design Agent Integration Gate

Design Agent integration is not part of the first implementation.

Required order:

1. `/coding` reaches A-grade default UI.
2. Fresh Run 100 evidence is accepted.
3. Real coding task gauntlet is accepted.
4. Design intake begins as read-only display only.
5. Combined design/coding diagnostic runs only after Britton approves it.

Forbidden until later explicit approval:

- Design apply authority.
- Design runtime authority.
- Design provider/API calls.
- Design queue/worker execution.
- Git staging, commit, push, branch, or worktree authority.
- CSS polish from design packets.

## 10. New Chat Pivot Handoff

Copy-paste this into the next chat:

```text
TITLE:
Source Proxy Codex-Like Active Task UI Revamp Plan v0.1 - First Implementation Increment

CURRENT LANE:
/home/source/SpiritOS, Source Proxy /coding UI information architecture. Start only Phase 1: Active Task Default Screen. This is the first implementation increment after the docs-only pivot plan.

DOCS CREATED:
- docs/source-proxy-codex-like-active-task-ui-revamp-plan-v0.1.md
- docs/source-proxy-codex-like-active-task-ui-revamp-new-chat-pivot-handoff-v0.1.md
- docs/plan-index.md was updated with a narrow active planning/handoff entry if present in the prior chat.

REPO STATUS / DIRTY-TREE NOTE:
The worktree was already dirty before the docs plan. Re-check current state first. Previously observed dirty files included docs/plan-index.md, src/components/coding/CodingCommandCenterShell.tsx, src/components/coding/__tests__/coding-command-center-shell.test.tsx, src/app/map/*, many source_proxy/cartographer and source_proxy/tests files, and many untracked docs. Do not clean, reset, stash, stage, or revert unrelated changes.

EXACT NEXT INCREMENT TO START:
Phase 1: Active Task Default Screen.
Goal: Make /coding default to a clean active task window: left app/project/chat nav, center active task transcript, bottom composer, compact top chips for active project/provider/safety/dirty-tree truth, no idle right-side Task State / Task Progress wall, no default trial prompt widget, no upfront Safety/Provider/Workspace card wall, and no raw evidence sprawl by default.

ALLOWED FILES FOR FIRST IMPLEMENTATION INCREMENT:
- src/components/coding/CodingCommandCenterShell.tsx
- src/components/coding/__tests__/coding-command-center-shell.test.tsx

FORBIDDEN FILES/ACTIONS:
No CSS edits. No wrapper files. No backend/source_proxy changes. No provider/API calls. No Run 10, Run 25, Run 100. No real coding task gauntlet. No apply. No execute-approved. No commit. No push. No branch/worktree creation. No stash/reset/clean/checkout. No queue/worker execution. No Design Agent runtime/apply work. No config/env/auth/package changes. No hidden mutation. Do not touch unrelated dirty files.

EXPECTED BEFORE/AFTER:
Before: /coding default first viewport feels like a cockpit/dashboard with visible trial prompts, provider/workspace cards, Task State/Task Progress wall, diagnostics, evidence, and receipts competing with the task.
After: /coding default first viewport feels like an active Codex-like coding task surface. The transcript and composer dominate. Project/chat list remains usable. Project/provider/safety/dirty-tree truth remains visible as compact chips. Detailed diagnostics/evidence can remain temporarily available lower/collapsed if Phase 1 does not yet build drawers, but they must not dominate idle first viewport.

TERMINAL VERIFICATION BLOCK:
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git diff --check
grep -nE "Run 10|Run 25|Run 100|Task State|Task Progress|Provider|Workspace|Approval|Apply|Verify|diagnostic|receipt|authority" src/components/coding/CodingCommandCenterShell.tsx | head -240
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx

BROWSER CHECKLIST:
- Open /coding.
- Confirm left app/project/chat navigation is still usable.
- Confirm active task transcript/story is the center of gravity.
- Confirm composer is bottom-aligned and obvious.
- Confirm compact chips show active project, provider/model, and safety/dirty-tree truth.
- Confirm no persistent idle right-side Task State / Task Progress wall dominates.
- Confirm no default trial prompt widget dominates the first viewport.
- Confirm no upfront Safety/Provider/Workspace card wall dominates.
- Confirm approval/apply/verify separation remains visible when relevant.
- Confirm GPT/cloud remains unavailable unless real config exists.
- Confirm no apply, execute-approved, commit, push, provider call, queue/worker, branch/worktree, reset/stash/clean, or live execution control appears.

STOP CONDITIONS:
Stop if tests fail and cannot be repaired inside the two allowed files. Stop if safety/provider/project/dirty-tree truth disappears. Stop if the change needs CSS, backend, provider, wrapper, drawer architecture, or runtime changes. Stop if unrelated dirty files would need to be modified. Stop if any authority boundary appears.

ROLLBACK NOTES:
Rollback means reverting only the changes made in src/components/coding/CodingCommandCenterShell.tsx and src/components/coding/__tests__/coding-command-center-shell.test.tsx for this increment. Do not use git reset, stash, clean, checkout, or broad restore unless Britton explicitly approves exact commands.

PERMISSION GATE:
After Phase 1 is implemented and verified, stop and ask Britton before implementation beyond this first increment. Do not begin drawer architecture, diagnostics relocation, evidence relocation, project selector cleanup, Run 10/25/100, real gauntlet, Design Agent integration, wrapper, or final CSS without Britton's explicit next approval.
```
