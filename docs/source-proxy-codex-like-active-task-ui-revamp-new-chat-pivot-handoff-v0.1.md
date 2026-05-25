# Source Proxy Codex-Like Active Task UI Revamp New Chat Pivot Handoff v0.1

Copy-paste this into a fresh Codex chat:

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
