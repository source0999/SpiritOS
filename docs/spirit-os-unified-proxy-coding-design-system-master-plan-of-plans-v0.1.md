# Spirit OS Unified Proxy Coding + Design System Master Plan of Plans v0.1

## 1. Short Status

This is a planning artifact.

This roadmap spans 3 to 7 days of incremental work. It does not authorize implementation by itself. All future implementation, testing, validation, proof collection, experiments, file edits, browser checks, and closeout evidence must occur only in an isolated proxy lane unless a later operator instruction approves one exact increment.

The main repository state must not be disturbed. The ongoing 24-hour Cartographer soak test must not be disturbed. Work should continue on Proxy, Design System, `/coding`, Codex-like UI, multimedia, projects, and settings surfaces while the soak runs. Only Cartographer-dependent integration increments should wait for accepted soak results. Final comprehensive CSS polish is intentionally last.

Isolation rule repeated for this plan: do not touch the main repository execution path; do not mutate unrelated dirty files; do not clean, stash, reset, checkout, stage, commit, push, branch, or create a worktree unless a later explicit operator approval names the exact command and lane; do not disturb the ongoing 24-hour Cartographer soak test; do not write to Cartographer soak logs; do not write to Scout soak logs; do not write to Cartographer runtime state; do not write to Cartographer live evidence; do not mutate production map state; do not mutate production Source Proxy state; do not run tests that mutate shared soak state; do not claim stability from tests that did not run inside the isolated proxy lane; do not claim Cartographer integration readiness until isolated-lane proof exists and the 24-hour soak result is available where required; do not wait on the Cartographer soak for work that is safely independent of Cartographer.

## 2. Repository Evidence Reviewed

| Document or code surface | Lane | Current status | What it contributes to the unified plan | Grants implementation authority? | Conflicts, blockers, Cartographer-soak dependency |
|---|---|---:|---|---:|---|
| `/home/source/SpiritOS/docs/codingUI.md` | Proxy Coding Command Center | Active planning | Establishes `/coding` as everyday coding command center and `/proxy-backend` as deeper diagnostics. Preserves Source Proxy loop: Draft -> Preview -> Approval -> Apply -> Verify. | No | Supports active-task UI revamp. Prior screenshot proof was blocked by missing browser tooling. |
| `/home/source/SpiritOS/docs/source-proxy-codex-like-active-task-ui-revamp-plan-v0.1.md` | Codex-like `/coding` UX | Active docs-only plan | Defines pivot target: left navigation, center active task transcript, bottom composer, compact truth chips, drawers for settings/diagnostics/evidence/design intake. | No | Docs-only. Must not be treated as execution proof. Safe while soak runs if isolated. |
| `/home/source/SpiritOS/docs/source-proxy-codex-like-active-task-ui-revamp-new-chat-pivot-handoff-v0.1.md` | Codex-like `/coding` UX | Supporting handoff | Narrows first increment to active task default screen and forbids backend/provider/apply/Run 10 work. | No | Helpful but not a full master plan. |
| `/home/source/SpiritOS/docs/source-proxy-coding-agent-a-plus-stress-gauntlet.md` | Source Proxy safety | Accepted/supporting | Records A+ engine readiness for separate wrapper work, with engine contracts as authority. | No | Does not authorize wrapper implementation or production mutation. |
| `/home/source/SpiritOS/docs/source-proxy-production-hardening-plan.md` | Source Proxy hardening | Active/supporting | Establishes safety regressions, approval/apply/verification/commit proposal/push queue boundaries, and `/coding` UI polish as next safe track. | No | Evidence predates current operator instruction; use as supporting proof only. |
| `/home/source/SpiritOS/docs/source-proxy-v0.3-stress-testing-plan.md` | Source Proxy testing | Archived/historical | Provides stress tiers and no-mutation principles. | No | Archived/deprecated; evidence only. |
| `/home/source/SpiritOS/docs/source-proxy-regression-matrix.md` | Source Proxy testing | Supporting | Gives test categories and warns that passing tests does not approve apply/commit/push. | No | Some profiles may write soak snapshots; forbidden during active shared soak unless isolated/safe. |
| `/home/source/SpiritOS/docs/source-proxy-worktree-study.md` | Isolation strategy | Supporting study | Worktree-style isolation is useful, but repo rule is stricter because dirty state and soak evidence must be protected. | No | No worktree creation allowed without exact approval. |
| `/home/source/SpiritOS/docs/proxy-test-runner-plan.md` | Test runner | Supporting/docs-only | Defines evidence/reporting runner concepts. | No | Runner profiles that write shared soak logs are forbidden for this roadmap. |
| `/home/source/SpiritOS/docs/source-proxy-pr-8-3-real-coding-task-gauntlet-receipt-pr8-3-real-01-v0.1.md` | PR-8.3 | Accepted receipt | Proves one narrow real coding task gauntlet receipt: 63 Vitest tests passed and `git diff --check` passed for the documented change. | No | Accepted receipt proves only the exact checks documented. Broader PR-8.3 unblock remains NEEDS OPERATOR REVIEW. |
| `/home/source/SpiritOS/docs/source-proxy-pr-8-3-real-low-to-mid-coding-task-gauntlet-closeout-v0.1.md` | PR-8.3 | Blocked/historical | Records earlier blocked state pending dirty-tree disposition. | No | Conflicts with later narrow accepted receipt; safest state is NEEDS OPERATOR REVIEW for broad PR-8.3. |
| `/home/source/SpiritOS/docs/source-proxy-pr-8-3-real-low-to-mid-coding-task-gauntlet-receipt-v0.1.md` | PR-8.3 | Blocked/historical | Earlier blocked receipt trail. | No | Conflicts with later accepted receipt; broad acceptance unresolved. |
| `/home/source/SpiritOS/source_proxy/api/*` | Source Proxy backend | Active code | Backend owner for preview, decision, long-running task, and execute-approved boundaries. | No | Must not call apply/execute-approved without separately approved increment. |
| `/home/source/SpiritOS/source_proxy/codex/*` | Codex adapter | Active code | Task packet and proposal-only Codex contract. | No | Wrapper must consume contracts; wrapper must not become source of truth. |
| `/home/source/SpiritOS/source_proxy/testing/*` | Source Proxy tests | Supporting code | Test helpers and proof structures. | No | Tests must run in isolated lane only and avoid shared soak mutation. |
| `/home/source/SpiritOS/source_proxy/verification/*` | Source Proxy verification | Supporting code | Verification contracts for post-apply safety. | No | No apply authority granted. |
| `/home/source/SpiritOS/source_proxy/tests/*` | Source Proxy tests | Supporting code | Pytest surfaces including safety and Cartographer checks. | No | Select only non-mutating targeted tests while soak runs. |
| `/home/source/SpiritOS/src/app/coding/page.tsx` | `/coding` command center | Active code | Everyday coding command center entry point. | No | Safe UI shell work only in isolated lane. |
| `/home/source/SpiritOS/src/components/coding/*` | `/coding` command center | Active code | Current command center shell, chips, drawers, receipt/proof display, design packet display candidates. | No | Large shell requires careful increment boundaries. |
| `/home/source/SpiritOS/src/lib/coding/*` | Coding truth surfaces | Active code | Settings, provider/model truth, backend truth, workspace context, usage/time surfaces. | No | Safe display first; no env/config/provider mutation. |
| `/home/source/SpiritOS/src/app/proxy-backend/page.tsx` | Diagnostics | Active code | Deeper diagnostics surface, explicitly planned/not wired. | No | Must remain deeper diagnostics, not everyday command center. |
| `/home/source/SpiritOS/src/app/v1/actions/preview/route.ts` | Source Proxy route | Active code | Preview boundary. | No | UI may display preview intent; route calls require separate approved increment. |
| `/home/source/SpiritOS/src/app/v1/actions/execute-approved/route.ts` | Source Proxy route | Active code | Execute-approved boundary requiring approved payload. | No | Forbidden until exact operator approval and safety gate. |
| `/home/source/SpiritOS/src/app/v1/coding/*` | Coding API routes | Active code | Coding/Codex status and safe blocked defaults. | No | Read-only/display only until approved. |
| `/home/source/SpiritOS/src/app/v1/tasks/long-running/*` | Long-running task route | Active code | Long-running proxy boundaries. | No | No hidden worker or queue advancement. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md` | Design Agent/System | Active docs-only plan | Design Agent + Design System A-grade preflight sequence. Design Agent is proposal/read-only until proof. | No | Docs-only; not execution proof. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-planning-closeout-v0.1.md` | Design Agent/System | Accepted planning closeout | Confirms planning closeout only, no implementation/evidence execution. | No | Requires later increments for proof. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-baseline-authority-source-of-truth-recovery-v0.1.md` | Design Agent/System | Supporting docs-only | Authority/source-of-truth recovery concepts. | No | Docs-only. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-closeout-v0.1.md` | Design Agent/System | Accepted closeout | Plan A planning closeout. | No | Accepted closeout proves only its planning scope. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-b-design-system-overhaul-readiness-v0.1.md` | Design System | Supporting docs-only | Design-system overhaul readiness sequence. | No | Docs-only. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-b-closeout-v0.1.md` | Design System | Accepted closeout | Plan B closeout. | No | Accepted for planning scope only. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-c-subagent-a-grade-evidence-upgrade-v0.1.md` | Design Agent | Supporting docs-only | Evidence upgrade plan. | No | Docs-only. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-d-safety-boundary-a-grade-proof-plan-v0.1.md` | Safety | Supporting docs-only | Safety-boundary proof requirements. | No | Docs-only. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-e-source-proxy-read-only-integration-proof-v0.1.md` | Source Proxy/Design | Supporting docs-only | Read-only Source Proxy integration proof plan. | No | Must be executed later in isolated lane. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-f-diagnostic-batch-harness-proof-v0.1.md` | Diagnostics | Supporting docs-only | Diagnostic batch harness proof plan. | No | Do not run mutating harnesses against shared soak. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-g-visual-css-evidence-proof-v0.1.md` | CSS/visual | Supporting docs-only | Visual/CSS proof plan. | No | CSS polish remains last. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-plan-h-source-proxy-pr-8-3-alignment-v0.1.md` | PR-8.3 alignment | Blocked/historical | Earlier alignment blocker. | No | Later narrow accepted PR-8.3 receipt conflicts; broad state NEEDS OPERATOR REVIEW. |
| `/home/source/SpiritOS/docs/design-agent-design-system-a-grade-preflight-readiness-source-proxy-pr-8-3-*.md` | PR-8.3 | Mixed | Includes blocked docs and later accepted receipt reference. | No | Conflict ledger below controls authority. |
| `/home/source/SpiritOS/docs/design-system-overhaul-master-v0.2.md` | Design System | Active/supporting plan | Rates design intelligence A-, reusable design system C, visual verification C+. | No | Indicates design-system polish is needed but not authorized. |
| `/home/source/SpiritOS/docs/design-systems-master-v0.1.md` | Design System | Supporting/docs-only | Design Vault/source cards/token model, manual-first plan. | No | No runtime implementation started. |
| `/home/source/SpiritOS/docs/design-agent-ecosystem-plan-16-100-prompt-design-and-proxy-integration-diagnostic-v0.1.md` | Design Agent diagnostics | Docs-only | 100-prompt diagnostic bank/report mapping. | No | Prompts not run. |
| `/home/source/SpiritOS/docs/design-agent-ecosystem-plan-19-300-prompt-combined-coding-design-gauntlet-v0.1.md` | Design/Coding gauntlet | Docs-only/not started | 300-prompt gauntlet fixtures. | No | Run not started. |
| `/home/source/SpiritOS/docs/design-agent-ecosystem-plan-20-full-design-agent-ecosystem-production-daily-use-preflight-css-polish-readiness-gate-v0.1.md` | Final readiness | Blocked/NO-GO | Final readiness gate closed NO-GO, listing missing safety/visual/integration proof. | No | Confirms CSS polish cannot start early. |
| `/home/source/SpiritOS/docs/source-proxy-design-apply-lane-v0.1.md` | Design apply lane | Supporting/docs-only | Design packs are advisory proposal evidence. Source Proxy remains only write/apply authority. | No | No design apply authority. |
| `/home/source/SpiritOS/docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md` | Design preview | Docs-only | Controlled preview concept. | No | No exact files/test method approved. |
| `/home/source/SpiritOS/docs/design-agent-ecosystem-remediation-plan-final-gate-evidence-recovery-and-lane-merge-prerequisites-v0.1.md` | Remediation | Docs-only | Remediation order for final gate recovery. | No | No authority. |
| `/home/source/SpiritOS/src/app/coding/design-demo/page.tsx` | Design demo | Active code | Isolated design demo candidate. | No | Safe only inside isolated lane. |
| `/home/source/SpiritOS/src/components/ui/*` | UI primitives | Active code | SpiritButton, GlassPanel, SectionLabel and related primitives. | No | Token/component mapping required before CSS polish. |
| `/home/source/SpiritOS/src/app/globals.css` | CSS | Active code | Global styles and utilities. | No | CSS-wide changes last only. |
| `/home/source/SpiritOS/src/styles/*` | CSS | Active code | Shared style surfaces. | No | Route-scoped risk inventory required first. |
| `/home/source/SpiritOS/src/theme/*` | Theme | Active code | Palette/token registry and CSS variables. | No | Token vocabulary contract required. |
| `/home/source/SpiritOS/src/components/dashboard/*` | Dashboard | Active code | Dashboard widgets including Cartographer status. | No | Avoid hidden visual changes to Cartographer surfaces. |
| `/home/source/SpiritOS/src/components/layouts/*` | Layout | Active code | Shared layouts. | No | Layout edits require route-scoped evidence. |
| `/home/source/SpiritOS/src/app/media/page.tsx` | Multimedia | Active code | Media route. | No | Integration safe as read-only cards only. |
| `/home/source/SpiritOS/src/components/media/*` | Multimedia | Active code | Media experience and storage/progress surfaces. | No | Must not mutate IndexedDB/localStorage. |
| `/home/source/SpiritOS/src/lib/media/*` | Multimedia | Active code | Media catalog/storage helpers. | No | No storage migration or persistent writes. |
| `/home/source/SpiritOS/src/app/chat/page.tsx` | Chat lanes | Active code | Chat route. | No | Read-only lane integration first. |
| `/home/source/SpiritOS/src/components/chat/*` | Chat lanes | Active code | Trinity chat and coding agent route selectors. | No | Do not call providers or mutate persistent chat state. |
| `/home/source/SpiritOS/src/hooks/useChatThreads.ts` | Chat persistence | Active code | Thread state/persistence. | No | Read-only display only unless storage writes approved. |
| `/home/source/SpiritOS/src/hooks/useChatFolders.ts` | Chat persistence | Active code | Folder state/persistence. | No | No destructive storage changes. |
| `/home/source/SpiritOS/src/hooks/useSpiritChatTransport.ts` | Chat provider transport | Active code | Provider call transport. | No | Provider calls forbidden. |
| `/home/source/SpiritOS/src/hooks/usePersistentChat.ts` | Chat persistence | Active code | Persistent chat behavior. | No | No storage writes. |
| `/home/source/SpiritOS/src/lib/chat-*.ts` | Chat library | Active code | Chat helpers. | No | Read-only integration first. |
| `/home/source/SpiritOS/src/lib/spirit/*` | Spirit chat/work surfaces | Active code | Spirit-specific chat helpers. | No | No provider/model calls. |
| `/home/source/SpiritOS/src/app/v1/cartographer/projects/route.ts` | Projects/Cartographer | Active code | Project route proxy to Cartographer. | No | Read-only only while soak runs; live use may be gated. |
| `/home/source/SpiritOS/source_proxy/cartographer/project_discovery.py` | Cartographer | Active code | Allowlisted read-only project discovery. | No | No filesystem scanning outside allowlisted roots. |
| `/home/source/SpiritOS/source_proxy/cartographer/project_health.py` | Cartographer | Active code | Read-only project health, authority blockers. | No | Do not mutate project health state. |
| `/home/source/SpiritOS/source_proxy/cartographer/component_mapper.py` | Cartographer | Active code | Component/path mapping. | No | No live write integration during soak. |
| `/home/source/SpiritOS/source_proxy/cartographer/repo_map.py` | Cartographer | Active code | Read-oriented repo mapping with limits/skips. | No | Do not refresh production map state during soak. |
| `/home/source/SpiritOS/source_proxy/cartographer/git_status.py` | Cartographer | Active code | Git truth summaries. | No | Read-only only. |
| `/home/source/SpiritOS/source_proxy/cartographer/live_state.py` | Cartographer | Active code | Read-only live state truth packets. | No | Do not write live evidence or runtime state. |
| `/home/source/SpiritOS/docs/cartographer-*.md` | Cartographer | Mixed | Plans, gates, receipts, activation readiness. | No | Latest operator instruction says current 24-hour soak is running. That wins. |
| `/home/source/SpiritOS/docs/cartographer-live-evidence/*` | Cartographer evidence | Evidence/docs | Prior soak/drill evidence and blocked activation evidence. | No | Do not write live evidence during current soak. |
| `/home/source/SpiritOS/docs/cartographer-live-receipts/*` | Cartographer receipts | Accepted/supporting | Supervised receipt discipline and limited candidate review only. | No | No full auto/unattended authority. |
| `/home/source/SpiritOS/source_proxy/tests/test_cartographer_*` | Cartographer tests | Supporting code | Cartographer safety tests. | No | Only non-mutating tests in isolated lane. |
| `/home/source/SpiritOS/src/app/map/*` | Map/Cartographer UI | Active code | Cartographer map/manual control center. | No | Production map state forbidden until post-soak gates. |
| Dashboard Cartographer widgets | Cartographer UI | Active code | Status widgets. | No | Visual non-regression only; no live mutation. |

Specific synthesis:

- `/coding` is the everyday coding command center.
- `/proxy-backend` is the deeper diagnostics surface.
- Source Proxy safety loop is preserved: Draft -> Preview -> Approval -> Apply -> Verify.
- Codex-like active task pivot target is: left navigation, center active task transcript, bottom composer, compact truth chips, drawers for settings/diagnostics/evidence/design intake.
- Design Agent + Design System A-grade preflight is active as a docs-first safety sequence, not implementation proof.
- PR-8.3 / Run 10 / Run 25 / Run 100 / real coding task gauntlet has conflicting records. Narrow PR8.3-REAL-01 evidence is accepted for its exact receipt. Broad PR-8.3 unblocking is NEEDS OPERATOR REVIEW.
- Current operator instruction says the 24-hour Cartographer soak is running. That is authoritative. Cartographer soak logs, Scout soak logs, Cartographer runtime state, Cartographer live evidence, production map state, and production Source Proxy state are protected boundaries.
- Proxy, Design System, `/coding`, Codex-like UI, multimedia lanes, read-only projects, settings truth display, and fixture-only Cartographer preparation can proceed before the 24-hour soak result.
- Live Cartographer integration, production map refresh, Cartographer write bridge, and any Cartographer-dependent final visual assertions are blocked until soak acceptance.

## 3. Conflict Resolution and Authority Ledger

| Conflict area | Older source | Newer/source-of-truth source | Resolution | Safe state |
|---|---|---|---|---|
| Master plan file absent | Handoff implied a master plan existed | This file is now the repo artifact | The prior handoff was incomplete. This document becomes the planning artifact only after operator review. | NEEDS OPERATOR REVIEW until accepted |
| PR-8.3 blocked vs accepted | Plan H and low/mid gauntlet blocked closeouts | PR8.3-REAL-01 accepted receipt and later accepted reference | Accepted receipt proves only exact PR8.3-REAL-01 checks. Broad PR-8.3 acceptance remains unresolved. | NEEDS OPERATOR REVIEW for broad unblocking |
| Design-system readiness | Design Agent plans propose A-grade sequence | Plan 20 final gate NO-GO | Foundation and evidence must be rebuilt in isolated lane before CSS polish. | NO-GO for final CSS |
| Cartographer prior soak evidence vs current soak | Prior docs show earlier soak/drill evidence | Latest operator instruction: current 24-hour soak is running | Latest explicit operator instruction wins. Current soak must not be disturbed. | Safe non-Cartographer work continues |
| Worktree study vs strict lane rule | Worktree study recommends future possible worktree | Operator forbids branch/worktree without exact approval | No branch/worktree creation. Isolation is logical/evidence-lane until exact approval. | Worktree NO-GO |
| Test runner soak snapshot profiles | Runner plan includes soak snapshot writes | Operator forbids writing soak logs/shared state | Do not run profiles that write shared soak evidence during current soak. | Use non-mutating checks only |
| Design Agent apply lane | Design apply lane proposes controlled future bridge | Source Proxy loop remains sole authority path | Design packets are read-only/proposal evidence. No apply bridge until separately approved. | Design apply NO-GO |
| UI drawer movement and authority | Revamp plans move settings/diagnostics/evidence to drawers | Authority boundary docs | Moving UI into drawers does not reduce or grant authority. Chips and copy must preserve truth. | Safe display only |

Rules applied:

- Latest explicit operator instruction wins.
- Accepted closeouts outrank planning docs.
- Docs-only plans are never execution proof.
- Accepted receipts prove only the exact checks they document.
- If required proof is unclear, mark NEEDS OPERATOR REVIEW.
- If Cartographer soak result is not yet accepted, continue all safe non-Cartographer work and gate only true Cartographer integration.

## 4. Non-Negotiable Authority Boundary

Hard boundary for every plan, phase, increment, check, manual validation, evidence packet, and future handoff:

- Do not touch the main repository execution path.
- Do not disturb the 24-hour Cartographer soak test.
- Do not edit Cartographer soak logs.
- Do not edit Scout soak logs.
- Do not edit Cartographer live evidence.
- Do not mutate Cartographer runtime state.
- Do not mutate production map state.
- Do not mutate production Source Proxy state.
- Do not modify unrelated dirty files.
- Do not clean or normalize dirty state.
- Do not run broad git actions.
- Do not self-approve.
- Do not create hidden workers.
- Do not create hidden queues.
- Do not use automatic apply.
- Do not call `execute-approved`.
- Do not call provider/model APIs unless separately scoped.
- Do not commit.
- Do not push.
- Do not create branches or worktrees unless separately approved.
- Do not stash, reset, clean, or checkout.
- Do not start CSS-wide polish before foundation gates pass.
- Do not grant design apply authority before read-only design intake is proven.
- Do not grant runtime design authority before the coding/design foundation is stable.
- Do not start Cartographer integration before soak-dependent gates are accepted.
- Do not treat UI drawer movement as authority reduction or authority grant.

## 5. Master Strategy

The unified strategy is to make `/coding` the daily operator cockpit while preserving Source Proxy as the only authority-bearing path. `/proxy-backend` remains the deeper diagnostics console for backend truth, runner evidence, and low-level proof surfaces. The Design System becomes the visual/component contract layer. The Design Agent remains read-only proposal evidence until later proof establishes a safe design-apply lane. Codex-like UI becomes the active-task operating model: navigation on the left, active transcript in the center, composer at the bottom, compact truth chips at the top, and drawers for settings, diagnostics, evidence/receipts, and design intake.

Multimedia work chat lanes are downstream work lanes after the foundation is stable. Projects integration starts as read-only project/workspace context. Settings starts as truth display and configuration intent only. Cartographer is future project/component/drift intelligence; it must not be mutated during the active 24-hour soak. Final CSS polish is last, after functional, safety, design-system, responsive, accessibility, project/settings, multimedia, and Cartographer-prep gates pass.

How coding and design systems swap and communicate seamlessly:

- Shared task context contract: task id, operator intent, active transcript events, proposed files, blocked states, verification state.
- Shared project/workspace context contract: selected project, workspace root, read-only health, component ownership, route ownership, Cartographer availability.
- Shared design packet display contract: design packet id, source, screenshots/mock states, token suggestions, component mapping, risk notes, no-apply status.
- Shared component/token vocabulary: UI primitives, theme palette names, CSS variable names, route-level component ownership, responsive and accessibility rules.
- Shared evidence drawer model: receipts, manual checks, test commands, browser proof, screenshots, no-authority proof.
- Shared route/model/provider truth chips: current route, backend status, model/provider availability, workspace, dirty tree, Source Proxy safety state, approval state.
- Shared safety-state display: Draft, Preview, Approval Required, Apply Disabled, Verify Required, Blocked, Cartographer Protected.
- Shared approval boundary language: design proposal approval is not Source Proxy apply approval; preview is not apply; verification is not merge.
- Explicit no-apply bridge from Design Agent to Source Proxy until a later approved design-apply lane exists.
- Explicit proof that design packets can be viewed, compared, and discussed without applying code.
- Explicit proof that Source Proxy remains the only authority path for Preview -> Approval -> Apply -> Verify.

External anchors incorporated:

- Codex-style sandboxing and approvals: sandbox and approval boundaries appear as chips, drawers, stop conditions, and GO/NO-GO gates.
- Worktree-style isolation: useful concept, but this repo's rule is stricter; no worktree without exact approval.
- Component-driven isolated UI development: hard-to-reach UI states are built and tested in isolation before route-wide polish.
- Testing Library principle: tests must resemble operator use of the command center.
- Next.js App Router boundaries: UI shell work is separate from backend route mutation.
- WAI-ARIA modal dialog pattern: settings, diagnostics, evidence, and design-intake drawers require keyboard/focus checks.

## 6. Work-While-Soak-Runs Strategy

| Workstream | Can proceed during 24-hour Cartographer soak? | Why safe or unsafe | Required isolation | Cartographer dependency | Stop point |
|---|---:|---|---|---|---|
| Proxy lane baseline | Yes | Defines boundaries without touching runtime. | Evidence-only isolated proxy lane. | NOT DEPENDENT ON SOAK | Stop if lane ambiguous. |
| Coding/design architecture contract | Yes | Docs/contract inventory only. | Read-only repo inspection and isolated evidence. | SAFE WHILE SOAK RUNS | Stop before UI implementation. |
| Minimum `/coding` active-task shell | Yes | UI-only isolated-lane shell with no backend/provider/apply calls. | Isolated proxy lane files only after explicit increment approval. | SAFE WHILE SOAK RUNS | Stop before backend route mutation. |
| Shared chips | Yes | Displays truth/safety states only. | Isolated proxy lane. | SAFE WHILE SOAK RUNS | Stop if chip would call live Cartographer write path. |
| Drawers | Yes | Settings/diagnostics/evidence/design intake drawers are display-only. | Isolated proxy lane. | SAFE WHILE SOAK RUNS | Stop if drawer gains authority. |
| Read-only design packet display | Yes | Proposal evidence only; no apply. | Isolated proxy lane fixtures. | SAFE WHILE SOAK RUNS | Stop if design packet can apply. |
| Design token/component mapping | Yes | Contract/display only; no CSS-wide sweep. | Isolated proxy lane. | NOT DEPENDENT ON SOAK | Stop before route-wide CSS polish. |
| Integrated foundation tests | Yes | Targeted isolated tests prove UI/safety boundaries. | Isolated test output directory. | SAFE WHILE SOAK RUNS | Stop if tests mutate shared state. |
| Multimedia work chat lanes | Yes | Read-only lane cards and context display. | Fixtures or no-write adapters. | NOT DEPENDENT ON SOAK | Stop before storage/provider mutation. |
| Projects interface read-only shell | Partial | Static fixtures or safe read-only routes are okay; live Cartographer writes are not. | Fixtures or isolated read-only mocks. | SAFE WHILE SOAK RUNS until live integration | Stop at live Cartographer boundary. |
| Settings window truth display | Yes | Displays existing truth and disabled states. | No provider/env/config writes. | NOT DEPENDENT ON SOAK | Stop before persistence. |
| Cartographer preparation | Partial | Inventory/contracts/fixture simulation safe; live integration unsafe. | No-write isolated simulation. | PARTIAL WHILE SOAK RUNS | Stop before live bridge. |
| Full Cartographer integration | No | Requires accepted soak result and explicit operator decision. | Post-soak isolated lane only. | CARTOGRAPHER SOAK RESULT REQUIRED BEFORE THIS INCREMENT | Stop until soak accepted. |
| Final CSS polish | Partial | Route-scoped readiness and component polish can be prepared; Cartographer-integrated visuals wait. | Isolated proxy lane screenshots/tests. | Partial; Cartographer/map polish POST-SOAK ONLY | Stop until foundation and integration gates pass. |

## 7. Master Plan Overview

| Plan | Primary outcome | Can happen during soak? | Requires soak result? | Estimated day band | Main risk | Closeout gate |
|---|---|---:|---:|---|---|---|
| Plan 0: Isolated Proxy Lane Baseline | Explicit lane, evidence, forbidden paths, rollback model. | Yes | No | Day 1 | Ambiguous isolation. | Lane/evidence boundary accepted. |
| Plan 1: Unified Coding + Design Foundation Architecture | Contracts for `/coding`, Source Proxy, Design System, Design Agent, drawers, chips. | Yes | No | Day 1 | Authority expansion hidden in UI. | Contracts explicit and no-authority preserved. |
| Plan 2: Minimum Isolated-Lane Coding/Design Foundation Implementation | Minimum command-center foundation in isolated lane. | Yes | No | Day 1-2 | Touching production path or backend authority. | Renders in isolated lane with boundaries intact. |
| Plan 3: Integrated Foundation Testing and Validation | Proof package for foundation. | Yes | No | Day 2 | Tests mutate shared state or overclaim stability. | Tests/manual proof accepted. |
| Plan 4: Codex-like Active Task Feature Completion | Task transcript, composer intent, plan preview, evidence/diagnostics states. | Yes | No | Day 2-3 | Provider/apply/queue execution leaks. | UI displays states without authority crossing. |
| Plan 5: Multimedia Work Chat Lanes Integration | Chat/media lane display and evidence integration. | Yes | No | Day 3 | Persistent storage/provider mutation. | Read-only lane navigation proven. |
| Plan 6: Projects Interface Read-Only Integration | Project selector, health, ownership, context display. | Yes if fixture/read-only | Only for live Cartographer | Day 3-4 | Live Cartographer boundary crossed. | Read-only mode proven. |
| Plan 7: Settings Window Integration | Settings truth display and disabled config intent. | Yes | No | Day 4 | Env/config/provider mutation. | Settings displays truth without mutation. |
| Plan 8: Pre-Soak-Completion Stabilization and Feature Assurance | Stabilize all safe non-Cartographer features. | Yes | No | Day 4-5 | Broad polish before gates. | Only true remaining blocker is Cartographer soak/integration approval. |
| Plan 9: Cartographer Integration Preparation | Contracts, no-write bridge simulation, blocked states. | Partial | Live integration yes | Day 5 | Disturbing soak or live evidence. | Future integration decision packet only. |
| Plan 10: Cartographer Soak Result Gate and Full Integration Decision | Accept/classify soak result and decide next step. | No | Yes | Day 5+ | Treating incomplete soak as pass. | Operator GO/NO-GO. |
| Plan 11: Full Cartographer Integration Gate Plan | Future exact approval template and integration gate. | Post-soak planning | Yes | Day 6 | Integration implied without approval. | Exact future approval requirements documented. |
| Plan 12: Final Comprehensive CSS Polish Readiness | Route/component/token/accessibility/responsive readiness. | Partial | Only for Cartographer surfaces | Day 6 | CSS-wide changes too early. | Route-scoped polish safe to execute. |
| Plan 13: Final Comprehensive CSS Polish Execution Plan | Final route-by-route polish proof. | Last only | Cartographer surfaces may require it | Day 7 | Visual changes hide authority states. | Final visual/test/no-authority proof accepted. |

## 8. Plan 0: Isolated Proxy Lane Baseline

Purpose: establish the isolated proxy lane before any implementation, testing, validation, or proof. This plan is SAFE WHILE SOAK RUNS.

PIVOT structure: PLAN -> PHASE -> INCREMENT -> CHECKS -> STOP CONDITIONS -> CLOSEOUT GATE -> NEXT AUTHORIZED INCREMENT.

Plan 0 global forbidden actions: production source edits, Cartographer writes, Scout soak writes, live evidence writes, runtime state writes, production map writes, production Source Proxy writes, provider/model calls, apply, execute-approved, hidden workers, queue mutation, branch/worktree/stash/reset/clean/checkout/stage/commit/push.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 0.1 Lane identity and boundary packet | 0.1.1 Name the isolated proxy lane and evidence root | Objective: name lane and evidence root. Scope: evidence-only isolated proxy lane. Allowed: docs/evidence-only or lane metadata only, no production files. Forbidden: all global forbidden actions and Cartographer soak paths. Work: record lane name, evidence root, isolation rule, no-main/no-soak declaration. Tests: `pwd`, repo path existence, no mutating command. Manual validation: operator reviews lane/root specificity. Evidence: Increment 0.1.1 boundary packet. Stop: ambiguous lane/root or root overlaps runtime. Recovery: stop, report NEEDS OPERATOR REVIEW; no cleanup. GO/NO-GO: GO only if lane/root explicit. Next: 0.1.2 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.1 Lane identity and boundary packet | 0.1.2 Record main repo path and forbidden shared-state paths | Objective: lock repo and forbidden shared-state boundaries. Scope: read-only path inventory. Allowed: evidence metadata, read-only `find`/`test -d`. Forbidden: production edits and all global forbidden actions. Work: record `/home/source/SpiritOS`, Cartographer soak/log/evidence/runtime/map/source-proxy shared-state path classes. Tests: read-only path existence checks. Manual: operator confirms path list. Evidence: forbidden shared-state path packet. Stop: repo mismatch or unknown path needed. Recovery: stop. GO/NO-GO: GO only if boundaries explicit. Next: 0.2.1 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.2 Main repo read-only status snapshot | 0.2.1 Capture read-only `git status --short` or equivalent snapshot without cleanup | Objective: baseline dirty state without mutation. Scope: read-only git inspection. Allowed: `git status --short --branch --untracked-files=normal`. Forbidden: clean/stash/reset/checkout/stage/commit/push/branch/worktree. Work: capture status output to evidence packet. Tests: command exits 0. Manual: compare against expected dirty evidence. Evidence: status snapshot. Stop: git command unavailable or suggests mutation. Recovery: do not repair, stop. GO/NO-GO: GO if status captured and no cleanup. Next: 0.2.2 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.2 Main repo read-only status snapshot | 0.2.2 Capture diff summary without modifying files | Objective: capture diff summary. Scope: read-only git diff. Allowed: `git diff --stat`, `git diff --name-only`. Forbidden: diff apply, checkout, reset, staging. Work: record summary. Tests: command exits 0. Manual: confirm no production mutation. Evidence: diff summary packet. Stop: command would require cleanup. Recovery: stop. GO/NO-GO: GO if diff summary captured. Next: 0.3.1 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.3 Cartographer soak-protection declaration | 0.3.1 Identify active Cartographer soak locations | Objective: identify candidate soak/log/evidence/runtime locations without writing. Scope: read-only path discovery. Allowed: read-only `find`/`grep` on docs/source files. Forbidden: opening files in write mode, running soak profiles. Work: list Cartographer docs/evidence/receipts/runtime classes and mark active/unknown. Tests: no files modified. Manual: operator reviews candidate locations. Evidence: soak location inventory. Stop: active soak path unknown but needed for next work. Recovery: mark unknown forbidden. GO/NO-GO: GO if all unknowns are forbidden. Next: 0.3.2 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.3 Cartographer soak-protection declaration | 0.3.2 Mark Cartographer soak logs/live evidence/runtime state as forbidden | Objective: convert inventory into hard forbidden matrix. Scope: evidence-only. Allowed: plan/evidence metadata. Forbidden: Cartographer writes, soak/log/live evidence/runtime/map writes. Work: record forbidden paths/actions. Tests: none beyond no-mutation status. Manual: operator confirms hard boundary. Evidence: Cartographer protection declaration. Stop: any future increment requires protected path. Recovery: gate that increment. GO/NO-GO: GO if protected paths forbidden. Next: 0.4.1 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.4 Dirty-tree classification without cleanup | 0.4.1 Classify dirty files as owned/unowned/unknown without edits | Objective: classify dirty state without cleanup. Scope: read-only status/diff. Allowed: git status/diff name-only. Forbidden: clean/stash/reset/checkout/stage. Work: classify each dirty item. Tests: no-mutation status after classification. Manual: operator approves classifications or marks unknown. Evidence: dirty-tree classification. Stop: ownership unclear for file needed later. Recovery: mark unknown forbidden. GO/NO-GO: GO if needed files are owned/allowed or unknown-gated. Next: 0.5.1 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.5 Allowed/forbidden path matrix | 0.5.1 Produce allowed path matrix for proxy/design/coding work | Objective: define allowed zones for future isolated work. Scope: matrix only. Allowed: proposed isolated lane/evidence; later explicit UI zones only after approval. Forbidden: production mutation now. Work: list proxy/design/coding allowed zones by future plan. Tests: review for overlap with forbidden paths. Manual: operator confirms. Evidence: allowed path matrix. Stop: allowed zone overlaps soak/runtime. Recovery: remove/gate zone. GO/NO-GO: GO if allowed matrix precise. Next: 0.5.2 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.5 Allowed/forbidden path matrix | 0.5.2 Produce forbidden path matrix for Cartographer soak and shared state | Objective: define no-go path/action matrix. Scope: matrix only. Allowed: evidence metadata. Forbidden: global forbidden actions. Work: list Cartographer, Scout, production Source Proxy, map, queue, provider, git mutation zones. Tests: matrix consistency check. Manual: operator confirms. Evidence: forbidden path matrix. Stop: missing known protected area. Recovery: add as forbidden. GO/NO-GO: GO if forbidden matrix complete enough. Next: 0.6.1 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.6 Test sandbox and evidence directory definition | 0.6.1 Define isolated test output directory | Objective: define where test outputs go. Scope: evidence/test-output planning. Allowed: isolated evidence root path only. Forbidden: shared soak logs, production logs, runtime state. Work: name test-output directory and retention rule. Tests: path does not overlap protected state. Manual: operator confirms. Evidence: test sandbox definition. Stop: overlap with production/shared logs. Recovery: choose new path. GO/NO-GO: GO if isolated. Next: 0.6.2 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.6 Test sandbox and evidence directory definition | 0.6.2 Define evidence packet naming convention | Objective: standardize evidence naming. Scope: docs/evidence metadata. Allowed: evidence root naming only. Forbidden: runtime logs and shared soak evidence. Work: define names like `plan-00-phase-01-increment-01-boundary-packet-v0.1.md`. Tests: naming review. Manual: operator confirms legibility. Evidence: naming convention packet. Stop: names collide with live evidence. Recovery: rename before use. GO/NO-GO: GO if unique. Next: 0.7.1 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.7 Rollback model | 0.7.1 Define rollback without stash/reset/clean/checkout | Objective: define recovery model that avoids destructive git. Scope: planning only. Allowed: evidence metadata. Forbidden: stash/reset/clean/checkout/branch/worktree. Work: define stop/report/manual operator review model; future patches revert only owned files by explicit patch. Tests: no git mutation. Manual: operator approves. Evidence: rollback model. Stop: rollback requires forbidden git. Recovery: stop. GO/NO-GO: GO if recovery is non-destructive. Next: 0.8.1 only. Cartographer: SAFE WHILE SOAK RUNS. |
| 0.8 Closeout gate | 0.8.1 Closeout packet and GO/NO-GO | Objective: decide whether Plan 1 may start. Scope: evidence summary only. Allowed: closeout packet. Forbidden: implementation. Work: summarize increments, evidence, no-mutation proof, Cartographer protection, next increment. Tests: status/diff read-only proof. Manual: phase-by-phase review. Evidence: Plan 0 closeout packet. Stop: missing evidence or mutation. Recovery: NO-GO and operator review. GO/NO-GO: GO only if lane explicit, evidence isolated, main repo untouched, Cartographer protected. Next: Plan 1, Phase 1.1, Increment 1.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 9. Plan 1: Unified Coding + Design Foundation Architecture

Purpose: define the contract between Proxy Coding Command Center, Source Proxy safety loop, Design System, Design Agent read-only packets, and Codex-like active-task UX. This plan is SAFE WHILE SOAK RUNS. This plan is docs-first and contract-first. Do not implement UI here unless separately authorized.

Plan 1 global forbidden actions: implementation edits to production routes/components/backend, provider calls, apply, execute-approved, Cartographer writes, git mutation, CSS polish, package changes, hidden workers/queues.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 1.1 Current `/coding` IA inventory | 1.1.1 Inventory `/coding` current first viewport | Objective: document current first-viewport IA. Scope: read-only `/home/source/SpiritOS/src/app/coding/page.tsx` and coding shell. Allowed: read-only inspection/evidence. Forbidden: edits. Work: capture visible regions, clutter, chips, composer/drawer placement. Tests: no-mutation status. Manual: compare against `/coding` command-center intent. Evidence: IA inventory. Stop: source unreadable. Recovery: mark NEEDS OPERATOR REVIEW. GO/NO-GO: GO if current IA documented. Next: 1.1.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.1 Current `/coding` IA inventory | 1.1.2 Inventory `/proxy-backend` diagnostics boundaries | Objective: preserve diagnostics separation. Scope: read-only `/home/source/SpiritOS/src/app/proxy-backend/page.tsx`. Allowed: inspection. Forbidden: backend wiring. Work: document deep diagnostics role and not-everyday status. Tests: no mutation. Manual: boundary review. Evidence: diagnostics boundary packet. Stop: page authority unclear. Recovery: mark unknown no-go. GO/NO-GO: GO if `/proxy-backend` remains secondary. Next: 1.1.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.1 Current `/coding` IA inventory | 1.1.3 Inventory `/home/source/SpiritOS/src/components/coding/*` | Objective: identify coding components and ownership. Scope: read-only component inventory. Allowed: file listing/targeted reads. Forbidden: refactor. Work: list shell, tests, drawers/chips/proof displays. Tests: no mutation. Manual: operator reviews ownership. Evidence: component inventory. Stop: ownership conflicts. Recovery: gate conflicting file. GO/NO-GO: GO if component surfaces mapped. Next: 1.1.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.1 Current `/coding` IA inventory | 1.1.4 Inventory `/home/source/SpiritOS/src/lib/coding/*` | Objective: identify coding truth surfaces. Scope: read-only lib inventory. Allowed: settings/provider/backend/workspace/usage reads. Forbidden: env/config mutation. Work: map truth objects and no-write settings. Tests: no mutation. Manual: truth source review. Evidence: lib inventory. Stop: provider calls required. Recovery: mark provider unavailable. GO/NO-GO: GO if truth surfaces mapped. Next: 1.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.2 Design-system token/component inventory | 1.2.1 Inventory UI primitives, theme, styles, globals | Objective: map design-system surfaces. Scope: read-only `/components/ui`, `/theme`, `/styles`, `globals.css`. Allowed: inventory. Forbidden: CSS edits. Work: list primitives, palette tokens, global risks. Tests: no mutation. Manual: design-system review. Evidence: token/component inventory. Stop: global CSS ownership unclear. Recovery: mark route-scoped later. GO/NO-GO: GO if vocabulary baseline exists. Next: 1.2.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.2 Design-system token/component inventory | 1.2.2 Define design token/component vocabulary reference | Objective: define shared names for future UI. Scope: contract only. Allowed: evidence doc. Forbidden: code/CSS. Work: map primitive, token, density, drawer, chip, transcript, composer terms. Tests: review completeness. Manual: operator validates vocabulary. Evidence: vocabulary contract. Stop: term collision. Recovery: revise contract. GO/NO-GO: GO if clear enough for implementation. Next: 1.3.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.3 Source Proxy safety contract mapping | 1.3.1 Map Draft -> Preview -> Approval -> Apply -> Verify states to UI chips | Objective: align Source Proxy loop with compact chips. Scope: contract. Allowed: docs/evidence. Forbidden: route calls/apply. Work: define chip labels, states, disabled copy, no-authority indicators. Tests: check all loop states present. Manual: safety review. Evidence: chip state contract. Stop: any chip implies authority not granted. Recovery: rewrite label. GO/NO-GO: GO if loop preserved. Next: 1.3.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.3 Source Proxy safety contract mapping | 1.3.2 Define no-authority and backend route boundaries | Objective: separate UI display from Next route mutation. Scope: contract. Allowed: route inventory. Forbidden: calling preview/execute-approved. Work: document preview, execute-approved, long-running boundaries and blocked states. Tests: route boundary checklist. Manual: operator validates no hidden authority. Evidence: backend boundary contract. Stop: UI requires backend mutation. Recovery: gate to later plan. GO/NO-GO: GO if no-authority explicit. Next: 1.4.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.4 Design packet read-only intake contract | 1.4.1 Map Design Agent packet fields to read-only display fields | Objective: define design packet display. Scope: contract. Allowed: docs/evidence. Forbidden: apply/preview writes. Work: fields for packet id, source, tokens, components, screenshots, risks, discussion prompts. Tests: read-only checklist. Manual: design packet review. Evidence: design packet contract. Stop: apply field appears. Recovery: remove/apply-gate. GO/NO-GO: GO if display-only. Next: 1.4.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.4 Design packet read-only intake contract | 1.4.2 Define no-apply design bridge | Objective: prove design packets cannot apply code. Scope: authority contract. Allowed: evidence. Forbidden: Source Proxy apply bridge. Work: write bridge rule: design approval is discussion approval only; Source Proxy owns Preview -> Approval -> Apply -> Verify. Tests: authority language review. Manual: operator confirms. Evidence: no-apply bridge contract. Stop: bridge grants apply. Recovery: NO-GO. GO/NO-GO: GO if no-apply explicit. Next: 1.5.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.5 Shared drawer model | 1.5.1 Define settings drawer contract | Objective: settings as truth/config-intent display. Scope: contract. Allowed: settings-surface inventory. Forbidden: persisting env/config/auth. Work: provider/model, workspace, usage/time, backend truth, disabled persistence states. Tests: no-provider/no-persist checklist. Manual: WAI-ARIA dialog intent review. Evidence: settings drawer contract. Stop: mutation required. Recovery: disabled state. GO/NO-GO: GO if display-only. Next: 1.5.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.5 Shared drawer model | 1.5.2 Define diagnostics drawer contract | Objective: diagnostics as secondary proof surface. Scope: contract. Allowed: read-only diagnostics display. Forbidden: runner profiles that write shared soak logs, Run 10/25/100 execution without approval. Work: define trial prompts, blockers, safety proof, manual controls as display/preview. Tests: no-run checklist. Manual: diagnostics boundary review. Evidence: diagnostics drawer contract. Stop: live runner required. Recovery: fixture/blocked state. GO/NO-GO: GO if no execution authority. Next: 1.5.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.5 Shared drawer model | 1.5.3 Define evidence drawer contract | Objective: evidence and receipts browsable without mutation. Scope: contract. Allowed: read-only receipt display. Forbidden: writing live evidence/soak logs. Work: define receipt list, task timeline, dirty-tree proof, rollback notes. Tests: evidence source boundary check. Manual: operator review. Evidence: evidence drawer contract. Stop: live evidence write needed. Recovery: use fixture/isolated evidence. GO/NO-GO: GO if read-only. Next: 1.5.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.5 Shared drawer model | 1.5.4 Define design-intake drawer contract | Objective: design intake as read-only proposal lane. Scope: contract. Allowed: design packets/fixtures. Forbidden: design apply authority. Work: define compare/discuss/reject/propose states with no apply. Tests: no-apply review. Manual: operator validates labels. Evidence: design-intake contract. Stop: apply control appears. Recovery: remove/gate. GO/NO-GO: GO if proposal-only. Next: 1.6.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.6 Shared task/project/context contract | 1.6.1 Define active task transcript data model | Objective: transcript event model. Scope: contract. Allowed: schema doc/evidence. Forbidden: worker execution. Work: event types for operator prompt, plan, preview, approval, verify, blocked, receipt. Tests: schema review. Manual: operator walk-through. Evidence: transcript model. Stop: implies hidden worker. Recovery: mark UI-only. GO/NO-GO: GO if display model clear. Next: 1.6.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.6 Shared task/project/context contract | 1.6.2 Define bottom composer boundaries | Objective: composer captures intent without provider execution. Scope: contract. Allowed: UI intent model. Forbidden: provider calls, queue submit, long-running task advancement. Work: define disabled/send-preview states and approval language. Tests: no-provider/no-queue checklist. Manual: operator validates copy. Evidence: composer boundary contract. Stop: submit would execute. Recovery: disabled state. GO/NO-GO: GO if intent-only. Next: 1.6.3. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.6 Shared task/project/context contract | 1.6.3 Define project/workspace context object | Objective: project/workspace display contract. Scope: contract. Allowed: read-only project/workspace fields. Forbidden: project creation, filesystem scan outside allowlist, Cartographer writes. Work: define selected project, root, health, ownership, availability, blockers. Tests: read-only context checklist. Manual: operator review. Evidence: project/workspace contract. Stop: live Cartographer write required. Recovery: fixture mode. GO/NO-GO: GO if read-only. Next: 1.6.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.6 Shared task/project/context contract | 1.6.4 Define provider/model truth object | Objective: provider/model truth chip contract. Scope: contract. Allowed: existing truth surfaces. Forbidden: provider calls, fake availability. Work: fields for local/cloud/codex worker/unavailable/config blockers. Tests: no-provider-call checklist. Manual: truth review. Evidence: provider truth contract. Stop: live provider needed. Recovery: unavailable state. GO/NO-GO: GO if truth-only. Next: 1.6.5. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.6 Shared task/project/context contract | 1.6.5 Define dirty-tree truth object | Objective: dirty-tree display contract. Scope: contract. Allowed: read-only status display. Forbidden: cleanup/stash/reset/checkout. Work: fields for clean/dirty/unknown, owned/unowned, action blocked. Tests: no-cleanup checklist. Manual: operator validates. Evidence: dirty truth contract. Stop: cleanup required. Recovery: unknown blocks. GO/NO-GO: GO if non-mutating. Next: 1.7.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 1.7 Accessibility and responsive baseline | 1.7.1 Define keyboard/focus behavior for drawers | Objective: WAI-ARIA dialog/drawer behavior. Scope: contract. Allowed: accessibility spec. Forbidden: code changes. Work: focus trap, Escape, restore focus, labelled drawer, scroll lock, reduced motion. Tests: future manual/test checklist. Manual: a11y review. Evidence: drawer a11y contract. Stop: behavior vague. Recovery: refine. GO/NO-GO: GO if testable. Next: 1.7.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.7 Accessibility and responsive baseline | 1.7.2 Define responsive breakpoints and mobile collapse behavior | Objective: responsive contract for command center. Scope: contract. Allowed: layout spec. Forbidden: CSS implementation. Work: desktop/tablet/mobile layout, left rail collapse, drawer width, composer persistence, chip wrapping. Tests: viewport checklist. Manual: operator validates. Evidence: responsive baseline. Stop: overlapping text likely. Recovery: revise spec. GO/NO-GO: GO if implementable. Next: 1.8.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 1.8 Closeout gate | 1.8.1 Produce architecture closeout | Objective: decide if Plan 2 can implement. Scope: closeout packet only. Allowed: evidence summary. Forbidden: implementation. Work: summarize contracts, authority boundaries, unresolved NEEDS OPERATOR REVIEW items. Tests: no-authority checklist. Manual: operator acceptance. Evidence: Plan 1 closeout. Stop: contracts not explicit. Recovery: return to blocked increment. GO/NO-GO: GO only if enough for isolated-lane implementation and no authority expansion. Next: Plan 2, Phase 2.1, Increment 2.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 10. Plan 2: Minimum Isolated-Lane Coding/Design Foundation Implementation

Purpose: implement the minimum integrated coding/design foundation inside the isolated proxy lane only. This plan is SAFE WHILE SOAK RUNS.

Constraints: no apply authority, no execute-approved, no provider calls, no network calls, no git mutation, no Cartographer mutation, no Cartographer soak log reads that alter timestamps or state, no CSS polish beyond minimal functional layout needed for validation, no broad refactor, no package changes unless separately approved, no hidden workers, no queue mutation.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 2.1 Isolated implementation surface | 2.1.1 Establish isolated implementation surface | Objective: define exact editable isolated lane. Scope: only operator-approved isolated files. Allowed: lane files named by Plan 0/1. Forbidden: main route/backend/Cartographer/runtime. Work: create or identify implementation surface. Tests: status/diff confirm limited scope. Manual: operator verifies scope. Evidence: surface packet. Stop: surface ambiguous. Recovery: stop, no cleanup. GO/NO-GO: GO if isolated. Next: 2.1.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.1 Isolated implementation surface | 2.1.2 Confirm allowed file set for first UI shell increment | Objective: file allowlist. Scope: exact files only. Allowed: first-shell file set. Forbidden: all other files. Work: write allowlist and ownership. Tests: compare diff names against allowlist. Manual: operator confirms. Evidence: allowlist. Stop: need unlisted file. Recovery: request approval. GO/NO-GO: GO if allowlist exact. Next: 2.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.2 Active task shell alignment | 2.2.1 Implement active-task transcript skeleton | Objective: render center transcript skeleton. Scope: isolated UI shell. Allowed: exact UI files. Forbidden: backend/provider. Work: add transcript layout/events fixtures. Tests: targeted UI render. Manual: browser inspect. Evidence: screenshot/checklist. Stop: production mutation. Recovery: revert owned patch only by explicit patch. GO/NO-GO: GO if skeleton renders. Next: 2.2.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.2 Active task shell alignment | 2.2.2 Implement bottom composer placement without provider calls | Objective: place composer as intent-only. Scope: isolated UI shell. Allowed: UI markup/state. Forbidden: provider/network/queue. Work: composer input disabled or draft-only. Tests: no-provider assertion. Manual: type interaction does not send. Evidence: composer proof. Stop: send executes. Recovery: disable. GO/NO-GO: GO if no call path. Next: 2.2.3. Cartographer: NOT DEPENDENT ON SOAK. |
| 2.2 Active task shell alignment | 2.2.3 Implement left navigation/project/chat lane placeholder | Objective: left rail placeholder. Scope: UI-only. Allowed: nav placeholders. Forbidden: live project/chat storage mutation. Work: add project/chat lane labels/status. Tests: render test. Manual: mobile/desktop scan. Evidence: nav proof. Stop: live storage/provider needed. Recovery: fixture placeholder. GO/NO-GO: GO if display-only. Next: 2.3.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.3 Shared truth chips | 2.3.1 Replace first-viewport clutter with compact truth chips | Objective: reduce clutter with chips. Scope: UI-only shell. Allowed: chip component/state. Forbidden: authority changes. Work: add compact chip row. Tests: render labels. Manual: check no hidden safety copy. Evidence: chip screenshot/checklist. Stop: chip hides critical blocker. Recovery: restore blocker visibility. GO/NO-GO: GO if clearer and truthful. Next: 2.3.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.3 Shared truth chips | 2.3.2 Add project/workspace chip | Objective: show project/workspace truth. Scope: UI display. Allowed: fixture/existing truth data. Forbidden: project creation/scanning. Work: add chip with read-only/unknown states. Tests: label test. Manual: blocked state review. Evidence: project chip proof. Stop: live Cartographer required. Recovery: unavailable state. GO/NO-GO: GO if read-only. Next: 2.3.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.3 Shared truth chips | 2.3.3 Add provider/model chip | Objective: show provider/model truth. Scope: UI display. Allowed: existing provider truth. Forbidden: provider calls. Work: add availability/unavailable states. Tests: no-provider-call assertion. Manual: copy review. Evidence: provider chip proof. Stop: network call appears. Recovery: stub/unavailable. GO/NO-GO: GO if truth-only. Next: 2.3.4. Cartographer: NOT DEPENDENT ON SOAK. |
| 2.3 Shared truth chips | 2.3.4 Add safety-state chip | Objective: expose Source Proxy state. Scope: UI display. Allowed: fixture/contract state. Forbidden: backend mutation. Work: render Draft/Preview/Approval/Apply Disabled/Verify/Blocked. Tests: state matrix. Manual: copy review. Evidence: safety chip proof. Stop: grants apply. Recovery: relabel/disable. GO/NO-GO: GO if loop preserved. Next: 2.3.5. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.3 Shared truth chips | 2.3.5 Add dirty-tree chip | Objective: display dirty truth. Scope: UI only. Allowed: status fixture/read-only data. Forbidden: cleanup. Work: clean/dirty/unknown chip and blockers. Tests: chip states. Manual: dirty copy review. Evidence: dirty chip proof. Stop: cleanup control appears. Recovery: remove. GO/NO-GO: GO if no cleanup. Next: 2.3.6. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.3 Shared truth chips | 2.3.6 Add approval-state chip | Objective: expose approval boundary. Scope: UI only. Allowed: approval state fixture. Forbidden: approval/apply execution. Work: render approval required/none/blocked. Tests: label asserts. Manual: authority review. Evidence: approval chip proof. Stop: approval implies apply. Recovery: relabel. GO/NO-GO: GO if boundary clear. Next: 2.4.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.4 Drawer shell wiring | 2.4.1 Add Settings drawer shell | Objective: settings drawer shell. Scope: UI-only. Allowed: drawer component. Forbidden: persistence/provider/env. Work: open/close shell and disabled states. Tests: drawer render/focus smoke. Manual: keyboard check. Evidence: settings drawer proof. Stop: config write path. Recovery: display-only. GO/NO-GO: GO if no mutation. Next: 2.4.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 2.4 Drawer shell wiring | 2.4.2 Add Diagnostics drawer shell | Objective: diagnostics drawer shell. Scope: UI-only. Allowed: fixture evidence. Forbidden: running diagnostics/soak writers. Work: display diagnostics categories. Tests: render/focus. Manual: no-run controls review. Evidence: diagnostics drawer proof. Stop: starts runner. Recovery: remove action. GO/NO-GO: GO if display-only. Next: 2.4.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.4 Drawer shell wiring | 2.4.3 Add Evidence/Receipts drawer shell | Objective: evidence drawer shell. Scope: UI-only. Allowed: fixture/isolated receipts. Forbidden: live evidence writes. Work: receipt list placeholder. Tests: render/focus. Manual: read-only check. Evidence: evidence drawer proof. Stop: writes live evidence. Recovery: fixture-only. GO/NO-GO: GO if read-only. Next: 2.4.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.4 Drawer shell wiring | 2.4.4 Add Design Intake drawer shell | Objective: design intake drawer shell. Scope: UI-only. Allowed: design packet fixture. Forbidden: design apply. Work: display packet tabs/empty states. Tests: render/focus. Manual: no-apply review. Evidence: design drawer proof. Stop: apply appears. Recovery: remove/gate. GO/NO-GO: GO if proposal-only. Next: 2.5.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 2.5 Read-only design packet display | 2.5.1 Add read-only design packet card | Objective: display packet safely. Scope: UI-only. Allowed: fixture data. Forbidden: code apply/preview mutation. Work: render packet fields and no-apply label. Tests: read-only assertions. Manual: packet review. Evidence: design packet proof. Stop: action mutates code. Recovery: remove action. GO/NO-GO: GO if read-only. Next: 2.6.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 2.6 Token/component vocabulary mapping | 2.6.1 Add design token vocabulary reference | Objective: show token vocabulary. Scope: UI display. Allowed: token names/read-only. Forbidden: CSS edits. Work: render token reference. Tests: render. Manual: design review. Evidence: token display proof. Stop: changes tokens. Recovery: revert owned display. GO/NO-GO: GO if display-only. Next: 2.6.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 2.6 Token/component vocabulary mapping | 2.6.2 Add component mapping display | Objective: show component/path vocabulary. Scope: UI display. Allowed: fixture/read-only component list. Forbidden: Cartographer write scan. Work: render mapping card. Tests: render. Manual: ownership review. Evidence: mapping proof. Stop: live write scan. Recovery: fixture-only. GO/NO-GO: GO if no mutation. Next: 2.7.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.7 Empty and blocked states | 2.7.1 Add blocked state for provider unavailable | Objective: provider unavailable state. Scope: UI-only. Allowed: fixture truth. Forbidden: provider calls. Work: render unavailable copy. Tests: no-call assertion. Manual: copy review. Evidence: blocked provider proof. Stop: probes provider. Recovery: static truth. GO/NO-GO: GO if no call. Next: 2.7.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 2.7 Empty and blocked states | 2.7.2 Add blocked state for apply disabled | Objective: apply disabled state. Scope: UI-only. Allowed: display state. Forbidden: execute-approved. Work: render disabled apply label. Tests: no execute-approved assertion. Manual: authority review. Evidence: apply-disabled proof. Stop: apply control enabled. Recovery: disable/remove. GO/NO-GO: GO if no apply path. Next: 2.7.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.7 Empty and blocked states | 2.7.3 Add blocked state for Cartographer soak protected | Objective: show soak protection. Scope: UI-only. Allowed: static/fixture state. Forbidden: live Cartographer write/read that alters state. Work: render protected status. Tests: no Cartographer mutation proof. Manual: soak boundary review. Evidence: soak-protected proof. Stop: live integration needed. Recovery: blocked state. GO/NO-GO: GO if protection visible. Next: 2.7.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 2.7 Empty and blocked states | 2.7.4 Add blocked state for design apply not authorized | Objective: design apply no-go state. Scope: UI-only. Allowed: display state. Forbidden: design apply bridge. Work: render no-apply design state. Tests: no apply action. Manual: authority review. Evidence: design-apply-blocked proof. Stop: design apply appears. Recovery: remove. GO/NO-GO: GO if proposal-only. Next: 2.8.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 2.8 Closeout gate | 2.8.1 Produce closeout evidence | Objective: close Plan 2. Scope: evidence package. Allowed: isolated evidence. Forbidden: production merge. Work: summarize implementation diffs, tests, screenshots/manual checks, authority proof. Tests: status/diff/typecheck targeted as available. Manual: phase review. Evidence: Plan 2 closeout. Stop: boundaries crossed. Recovery: owned patch reversal by explicit patch, no git reset. GO/NO-GO: GO if foundation renders in isolated lane and authority unchanged. Next: Plan 3, Phase 3.1, Increment 3.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 11. Plan 3: Integrated Foundation Testing and Validation

Purpose: prove the integrated coding/design foundation is stable inside the isolated proxy lane before remaining Codex features are added. This plan is SAFE WHILE SOAK RUNS.

Every Plan 3 increment must specify exact command/manual check, expected output, artifact saved in isolated lane, proof main repo was not touched, proof Cartographer soak was not disturbed, and failure meaning.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 3.1 Static checks | 3.1.1 Run diff/status check from isolated lane | Objective: prove scope. Scope: read-only status/diff. Allowed: `git status --short --branch`, `git diff --name-only`, `git diff --stat`. Forbidden: git mutation. Work: capture outputs. Tests: commands exit 0. Manual: compare diff to allowlist. Evidence: status/diff artifact. Stop: unexpected files. Recovery: classify, no cleanup. GO/NO-GO: GO if scoped. Next: 3.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 3.2 TypeScript checks | 3.2.1 Run TypeScript check | Objective: TS safety. Scope: isolated lane command. Allowed: `npm run typecheck` if available. Forbidden: package install. Work: run/capture output. Expected: pass. Manual: review errors. Evidence: typecheck log. Stop: TS fail outside allowed scope. Recovery: fix only allowed files. GO/NO-GO: GO if pass or accepted unrelated known fail. Next: 3.2.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 3.2 TypeScript checks | 3.2.2 Run lint if available | Objective: lint safety. Scope: isolated lane command. Allowed: `npm run lint`. Forbidden: autofix broad changes. Work: run/capture. Expected: pass or known unrelated failures documented. Manual: review. Evidence: lint log. Stop: new lint failures. Recovery: fix allowed files only. GO/NO-GO: GO if clean/known. Next: 3.3.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 3.3 Unit tests | 3.3.1 Run targeted Vitest checks for `/coding` shell | Objective: render foundation. Scope: targeted frontend tests. Allowed: `npx --no-install vitest run ...coding...`. Forbidden: broad mutating tests. Work: run shell tests. Expected: pass. Manual: review summary. Evidence: vitest log. Stop: shell fail. Recovery: allowed-file fix. GO/NO-GO: GO if pass. Next: 3.3.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 3.3 Unit tests | 3.3.2 Run targeted tests for chip labels and blocked states | Objective: verify chips/blocked states. Scope: targeted tests. Allowed: Vitest/Testing Library. Forbidden: provider/backend calls. Work: assert chip labels and disabled states. Expected: pass. Manual: review states. Evidence: chip test log. Stop: misleading state. Recovery: fix UI/tests in allowlist. GO/NO-GO: GO if pass. Next: 3.3.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 3.3 Unit tests | 3.3.3 Run drawer open/close behavior tests | Objective: drawer behavior. Scope: targeted UI tests. Allowed: Testing Library. Forbidden: persistence/provider. Work: open/close settings/diagnostics/evidence/design. Expected: pass. Manual: review failure output. Evidence: drawer test log. Stop: drawer inaccessible. Recovery: fix allowed UI. GO/NO-GO: GO if pass. Next: 3.6.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 3.6 Accessibility smoke checks | 3.6.1 Run keyboard/focus smoke for drawers | Objective: WAI-ARIA smoke. Scope: tests/manual. Allowed: keyboard simulation. Forbidden: hidden focus traps. Work: assert focus enters/restores, Escape closes. Expected: pass. Manual: keyboard checklist. Evidence: a11y smoke log. Stop: focus broken. Recovery: fix drawer focus. GO/NO-GO: GO if pass. Next: 3.5.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 3.5 Design packet read-only tests | 3.5.1 Run read-only design packet test | Objective: prove packets display without apply. Scope: targeted test. Allowed: fixture display. Forbidden: apply/preview mutation. Work: assert no apply control and read-only labels. Expected: pass. Manual: inspect UI. Evidence: design packet test log. Stop: apply action. Recovery: remove/gate. GO/NO-GO: GO if read-only. Next: 3.9.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 3.9 No-authority proof | 3.9.1 Run no-apply/no-execute-approved assertion | Objective: ensure no apply route invoked. Scope: tests/static grep. Allowed: targeted assertions. Forbidden: route call. Work: assert no `execute-approved` action from UI. Expected: none. Manual: review. Evidence: no-apply proof. Stop: execute path present. Recovery: remove/gate. GO/NO-GO: GO if absent/disabled. Next: 3.9.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 3.9 No-authority proof | 3.9.2 Run no-provider-call assertion | Objective: ensure no provider calls. Scope: tests/static checks. Allowed: mocks/assertions. Forbidden: network. Work: assert composer/settings do not call provider. Expected: none. Manual: review. Evidence: no-provider proof. Stop: call path present. Recovery: disable. GO/NO-GO: GO if absent. Next: 3.4.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 3.4 Source Proxy safety regression | 3.4.1 Run Source Proxy safety contract targeted pytest checks | Objective: backend safety unaffected. Scope: targeted non-mutating pytest. Allowed: specific safety tests that do not write shared soak state. Forbidden: soak snapshot writers/live mutation. Work: run selected `pytest source_proxy/tests/...` safety tests. Expected: pass. Manual: review command list. Evidence: pytest log. Stop: mutating test required. Recovery: skip and mark NEEDS OPERATOR REVIEW. GO/NO-GO: GO if pass/non-mutating. Next: 3.10.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 3.10 Cartographer soak non-interference proof | 3.10.1 Run no-Cartographer-mutation proof | Objective: prove soak untouched. Scope: read-only status/path timestamp review where safe. Allowed: git status, diff name-only, forbidden-path diff check. Forbidden: writing/reading with side effects. Work: show no changes in Cartographer logs/live evidence/runtime/map. Expected: no modifications. Manual: operator reviews. Evidence: no-Cartographer-mutation packet. Stop: any protected path changed. Recovery: NO-GO. GO/NO-GO: GO if untouched. Next: 3.8.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 3.8 Manual browser checklist | 3.8.1 Run manual desktop `/coding` checklist | Objective: desktop manual proof. Scope: local isolated dev only if approved and non-mutating. Allowed: browser check/screenshot inside evidence. Forbidden: provider/apply/Cartographer writes. Work: inspect `/coding` desktop states. Expected: layout correct, no authority confusion. Manual: checklist required. Evidence: desktop checklist/screenshot if available. Stop: overlap/broken controls. Recovery: fix allowed UI. GO/NO-GO: GO if accepted. Next: 3.8.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 3.8 Manual browser checklist | 3.8.2 Run manual mobile/narrow viewport checklist | Objective: responsive proof. Scope: browser/manual. Allowed: narrow viewport screenshot/checklist. Forbidden: CSS-wide polish. Work: verify chips/drawers/composer no overlap. Expected: usable. Manual: checklist. Evidence: mobile checklist. Stop: layout unusable. Recovery: targeted allowed fix. GO/NO-GO: GO if accepted. Next: 3.11.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 3.11 Evidence package | 3.11.1 Capture evidence package | Objective: consolidate logs/proof. Scope: isolated evidence root. Allowed: evidence files only. Forbidden: live evidence/soak logs. Work: index commands, outputs, screenshots/checklists, no-authority proof. Tests: artifact existence. Manual: operator reviews index. Evidence: Plan 3 package. Stop: missing artifact. Recovery: rerun safe check. GO/NO-GO: GO if complete. Next: 3.12.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 3.12 Closeout gate | 3.12.1 Closeout GO/NO-GO | Objective: decide Plan 4 readiness. Scope: closeout. Allowed: evidence summary. Forbidden: implementation. Work: summarize pass/fail, main untouched, soak untouched. Tests: final status/diff. Manual: operator acceptance. Evidence: Plan 3 closeout. Stop: failed required check. Recovery: return to failing increment. GO/NO-GO: GO only if isolated foundation passes and no shared state touched. Next: Plan 4, Phase 4.1, Increment 4.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 12. Plan 4: Codex-like Active Task Feature Completion

Purpose: complete remaining safe Codex-like command-center features after the integrated foundation is proven stable. This plan is SAFE WHILE SOAK RUNS.

Constraints: no provider calls, no apply, no execute-approved, no queue execution, no hidden workers, no long-running task advancement, no branch/worktree/git mutation, no Cartographer mutation, isolated proxy lane only.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 4.1 Active task transcript behavior | 4.1.1 Map task packet schema | Objective: map task packet fields. Scope: UI/schema only. Allowed: task packet contract/fixtures. Forbidden: worker execution. Work: field map for id,intent,files,states,evidence. Tests: schema tests. Manual: review. Evidence: schema packet. Stop: hidden worker needed. Recovery: fixture state. GO/NO-GO: GO if display-safe. Next: 4.1.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.1 Active task transcript behavior | 4.1.2 Render active task timeline | Objective: timeline display. Scope: UI-only. Allowed: fixture events. Forbidden: queue mutation. Work: render transcript events. Tests: render/order tests. Manual: browser review. Evidence: timeline proof. Stop: live task advancement. Recovery: fixture-only. GO/NO-GO: GO if display-only. Next: 4.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.2 Composer intent handling | 4.2.1 Render operator prompt/composer input safely | Objective: intent capture. Scope: UI-only. Allowed: local component state. Forbidden: provider/network/queue. Work: draft input and disabled submit/preview-intent. Tests: no-call tests. Manual: type/no-send check. Evidence: composer proof. Stop: provider call. Recovery: disable. GO/NO-GO: GO if safe. Next: 4.3.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 4.3 Plan preview and task packet display | 4.3.1 Render plan preview card | Objective: display proposed plan. Scope: UI fixture. Allowed: mock-safe plan data. Forbidden: apply/preview route call. Work: plan card with no-authority label. Tests: render/label. Manual: review. Evidence: plan preview proof. Stop: starts preview route. Recovery: display-only. GO/NO-GO: GO if no route call. Next: 4.3.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.3 Plan preview and task packet display | 4.3.2 Render proposed file list | Objective: proposed file display. Scope: UI fixture. Allowed: file list display. Forbidden: file edits. Work: render allowed/forbidden file badges. Tests: label tests. Manual: ownership review. Evidence: file list proof. Stop: file mutation. Recovery: remove action. GO/NO-GO: GO if display-only. Next: 4.6.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.6 UI-only state transitions | 4.6.1 Render approval-required state | Objective: approval boundary display. Scope: UI fixture. Allowed: state display. Forbidden: approval execution. Work: show approval required and no apply. Tests: state tests. Manual: authority review. Evidence: approval-required proof. Stop: approve button applies. Recovery: disable. GO/NO-GO: GO if no apply. Next: 4.6.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.6 UI-only state transitions | 4.6.2 Render verify-required state | Objective: verification state display. Scope: UI fixture. Allowed: display. Forbidden: verification worker. Work: show verify-required/readiness labels. Tests: state tests. Manual: review. Evidence: verify state proof. Stop: worker starts. Recovery: display-only. GO/NO-GO: GO if safe. Next: 4.6.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.6 UI-only state transitions | 4.6.3 Render blocked state | Objective: blocked state display. Scope: UI fixture. Allowed: blocked reasons. Forbidden: bypass controls. Work: provider/apply/Cartographer/dirty blocked states. Tests: blocked state tests. Manual: review. Evidence: blocked proof. Stop: bypass exists. Recovery: remove. GO/NO-GO: GO if unambiguous. Next: 4.4.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.4 Evidence/receipt browsing display | 4.4.1 Render evidence receipt list | Objective: display receipts. Scope: read-only fixture/isolated evidence. Allowed: list display. Forbidden: live evidence writes. Work: receipt rows and filters. Tests: render. Manual: review. Evidence: receipt list proof. Stop: writes receipts. Recovery: fixture-only. GO/NO-GO: GO if read-only. Next: 4.5.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.5 Diagnostics drawer detail expansion | 4.5.1 Render diagnostics summary | Objective: diagnostics details. Scope: UI display. Allowed: fixture/safe summary. Forbidden: runner execution. Work: summary cards and blocker list. Tests: render/no-run. Manual: check buttons disabled/preview-only. Evidence: diagnostics proof. Stop: runner starts. Recovery: disable. GO/NO-GO: GO if display-only. Next: 4.6.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.6 UI-only state transitions | 4.6.4 Render active task empty state | Objective: safe default. Scope: UI-only. Allowed: empty state. Forbidden: auto-create task. Work: render no active task and next action copy. Tests: render. Manual: review. Evidence: empty state proof. Stop: hidden task creation. Recovery: remove. GO/NO-GO: GO if no background work. Next: 4.7.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.7 Tests and manual validation | 4.7.1 Add tests for state transitions | Objective: automated state proof. Scope: targeted tests. Allowed: Vitest. Forbidden: provider/backend. Work: test empty/blocked/approval/verify states. Expected: pass. Manual: review. Evidence: test log. Stop: failing required tests. Recovery: fix allowed UI/tests. GO/NO-GO: GO if pass. Next: 4.7.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.7 Tests and manual validation | 4.7.2 Add manual checklist | Objective: operator rehearsal. Scope: checklist/evidence. Allowed: manual route checks. Forbidden: execution. Work: checklist for timeline/composer/preview/receipts/diagnostics. Tests: manual pass. Evidence: checklist. Stop: unclear control. Recovery: fix or block. GO/NO-GO: GO if accepted. Next: 4.8.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 4.8 Closeout gate | 4.8.1 Closeout gate | Objective: decide Plan 5 readiness. Scope: closeout. Allowed: evidence summary. Forbidden: implementation continuation without approval. Work: summarize state features and authority proof. Tests: final status/diff/no-call. Manual: operator review. Evidence: Plan 4 closeout. Stop: authority boundary crossed. Recovery: return to offending increment. GO/NO-GO: GO if command center displays task states/operator controls without crossing boundaries. Next: Plan 5, Phase 5.1, Increment 5.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 13. Plan 5: Multimedia Work Chat Lanes Integration

Purpose: integrate multimedia work chat lanes into the unified command center while preserving safety and design-system contracts. This plan is SAFE WHILE SOAK RUNS.

Constraints: no media storage migration unless separately approved, no destructive IndexedDB/localStorage changes, no provider calls, no hidden background workers, no cross-lane mutation, no new persistent storage writes unless separately approved, isolated proxy lane only.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 5.1 Media/chat surface inventory | 5.1.1 Inventory `/home/source/SpiritOS/src/app/chat/page.tsx` | Objective: route inventory. Scope: read-only. Allowed: inspect. Forbidden: edits/provider. Work: record chat entry. Tests: no mutation. Manual: review. Evidence: chat route inventory. Stop: unreadable. Recovery: mark unknown. GO/NO-GO: GO. Next: 5.1.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.1 Media/chat surface inventory | 5.1.2 Inventory `/home/source/SpiritOS/src/components/chat/*` | Objective: chat component inventory. Scope: read-only. Allowed: inspect. Forbidden: edits/provider. Work: map Trinity chat/coding agent surfaces. Tests: no mutation. Manual: review. Evidence: chat component inventory. Stop: ownership unclear. Recovery: gate. GO/NO-GO: GO. Next: 5.1.3. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.1 Media/chat surface inventory | 5.1.3 Inventory chat hooks | Objective: persistence/provider risk inventory. Scope: read-only hooks. Allowed: inspect. Forbidden: storage writes/provider calls. Work: map `useChatThreads`, folders, transport, persistent chat. Tests: no mutation. Manual: risk review. Evidence: chat hooks inventory. Stop: hidden storage dependency unclear. Recovery: read-only card only. GO/NO-GO: GO. Next: 5.1.4. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.1 Media/chat surface inventory | 5.1.4 Inventory `/home/source/SpiritOS/src/app/media/page.tsx` | Objective: media route inventory. Scope: read-only. Allowed: inspect. Forbidden: edits/storage. Work: record media entry. Tests: no mutation. Manual: review. Evidence: media route inventory. Stop: unreadable. Recovery: mark unknown. GO/NO-GO: GO. Next: 5.1.5. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.1 Media/chat surface inventory | 5.1.5 Inventory `/home/source/SpiritOS/src/components/media/*` and `/home/source/SpiritOS/src/lib/media/*` | Objective: media storage/catalog inventory. Scope: read-only. Allowed: inspect. Forbidden: storage migration/writes. Work: map catalog, progress, watchlist risks. Tests: no mutation. Manual: review. Evidence: media inventory. Stop: storage mutation required. Recovery: display status only. GO/NO-GO: GO. Next: 5.2.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.2 Work-lane data contract | 5.2.1 Define chat lane contract | Objective: chat lane display model. Scope: contract. Allowed: fixture/read-only. Forbidden: provider/storage writes. Work: thread/folder/status/last activity display. Tests: contract review. Manual: review. Evidence: chat lane contract. Stop: requires persistence. Recovery: disabled/read-only. GO/NO-GO: GO. Next: 5.2.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.2 Work-lane data contract | 5.2.2 Define media lane contract | Objective: media lane display model. Scope: contract. Allowed: catalog/status display. Forbidden: storage migration. Work: catalog/storage/status/recent media fields. Tests: review. Manual: review. Evidence: media lane contract. Stop: write needed. Recovery: read-only. GO/NO-GO: GO. Next: 5.3.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.3 Read-only media lane preview | 5.3.1 Add read-only media lane card | Objective: media card. Scope: UI display. Allowed: fixtures/safe read-only. Forbidden: storage writes. Work: render media card/status. Tests: render/no-storage. Manual: review. Evidence: media card proof. Stop: storage write. Recovery: fixture-only. GO/NO-GO: GO. Next: 5.4.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.4 Chat-thread lane mapping | 5.4.1 Add read-only chat lane card | Objective: chat card. Scope: UI display. Allowed: fixtures/safe read-only. Forbidden: provider/storage. Work: render chat card. Tests: render/no-provider. Manual: review. Evidence: chat card proof. Stop: provider call. Recovery: fixture-only. GO/NO-GO: GO. Next: 5.4.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.4 Chat-thread lane mapping | 5.4.2 Add thread/folder context display | Objective: context display. Scope: UI read-only. Allowed: fixtures/existing safe data. Forbidden: IndexedDB/localStorage mutation. Work: render thread/folder counts/status. Tests: no-storage write. Manual: review. Evidence: thread/folder proof. Stop: storage write. Recovery: fixture-only. GO/NO-GO: GO. Next: 5.3.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.3 Read-only media lane preview | 5.3.2 Add media catalog/storage status display | Objective: media status truth. Scope: UI read-only. Allowed: display status. Forbidden: catalog mutation. Work: render catalog/storage available/unavailable. Tests: render. Manual: review. Evidence: media status proof. Stop: migration/write. Recovery: disabled state. GO/NO-GO: GO. Next: 5.5.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.5 Evidence drawer integration | 5.5.1 Add evidence drawer entries for chat/media | Objective: receipt entries. Scope: UI display. Allowed: isolated evidence/fixtures. Forbidden: live writes. Work: add chat/media evidence rows. Tests: render. Manual: review. Evidence: evidence integration proof. Stop: writes evidence outside lane. Recovery: fixture-only. GO/NO-GO: GO. Next: 5.6.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.6 Responsive behavior | 5.6.1 Add mobile collapse behavior | Objective: narrow layout. Scope: UI. Allowed: route-scoped minimal layout. Forbidden: CSS-wide polish. Work: collapse lane cards. Tests: responsive check. Manual: mobile checklist. Evidence: mobile proof. Stop: overlap. Recovery: targeted fix. GO/NO-GO: GO. Next: 5.7.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.7 Tests and manual validation | 5.7.1 Add tests | Objective: automated proof. Scope: targeted tests. Allowed: Vitest. Forbidden: storage/provider. Work: chat/media lane tests. Expected: pass. Manual: review. Evidence: test log. Stop: fail. Recovery: fix allowed. GO/NO-GO: GO. Next: 5.7.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.7 Tests and manual validation | 5.7.2 Add manual validation | Objective: operator check. Scope: manual. Allowed: browser no-write check. Forbidden: storage mutation. Work: navigate lane cards. Evidence: checklist. Stop: mutation/overlap. Recovery: fix/gate. GO/NO-GO: GO. Next: 5.8.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 5.8 Closeout gate | 5.8.1 Closeout gate | Objective: decide Plan 6 readiness. Scope: closeout. Allowed: evidence summary. Forbidden: further implementation. Work: summarize read-only lane proof. Tests: status/diff/no-provider/no-storage. Manual: operator review. Evidence: Plan 5 closeout. Stop: storage/provider mutation. Recovery: return to offender. GO/NO-GO: GO if lanes displayed/navigated safely. Next: Plan 6, Phase 6.1, Increment 6.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 14. Plan 6: Projects Interface Read-Only Integration

Purpose: integrate project selection, project health, workspace context, and project-aware task display as read-only UI first. This plan is SAFE WHILE SOAK RUNS if implemented against static fixtures, existing safe read-only routes, or isolated-lane mocks. This plan becomes CARTOGRAPHER SOAK RESULT REQUIRED BEFORE THIS INCREMENT only if it attempts live Cartographer integration or Cartographer mutation.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 6.1 Project discovery contract inventory | 6.1.1 Inventory existing project routes and Python services | Objective: map project surfaces. Scope: read-only route/service inventory. Allowed: inspect `/v1/cartographer/projects` and cartographer project modules. Forbidden: live writes/scans outside allowlist. Work: document read-only routes/services. Tests: no mutation. Manual: review. Evidence: project inventory. Stop: write dependency. Recovery: fixture mode. GO/NO-GO: GO. Next: 6.1.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.1 Project discovery contract inventory | 6.1.2 Define read-only project object | Objective: project data contract. Scope: contract. Allowed: fixture schema. Forbidden: project creation. Work: fields id,name,root,health,availability,blockers. Tests: schema review. Manual: review. Evidence: project object contract. Stop: needs live write. Recovery: blocked state. GO/NO-GO: GO. Next: 6.1.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.1 Project discovery contract inventory | 6.1.3 Define project-health display model | Objective: health model. Scope: contract. Allowed: read-only health fields. Forbidden: health mutation. Work: status, dirty summary, blockers, stale flags. Tests: review. Manual: review. Evidence: health contract. Stop: mutation required. Recovery: unavailable. GO/NO-GO: GO. Next: 6.1.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.1 Project discovery contract inventory | 6.1.4 Define component/path ownership display model | Objective: ownership display. Scope: contract. Allowed: fixture/read-only map. Forbidden: repo map refresh writes. Work: route/component/path owner fields. Tests: review. Manual: ownership review. Evidence: ownership contract. Stop: live map write needed. Recovery: fixture-only. GO/NO-GO: GO. Next: 6.1.5. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.1 Project discovery contract inventory | 6.1.5 Define workspace root display model | Objective: workspace truth model. Scope: contract. Allowed: read-only root display. Forbidden: filesystem scanning outside allowlist. Work: root, availability, read-list-only labels. Tests: review. Manual: review. Evidence: workspace model. Stop: broad scan needed. Recovery: unknown state. GO/NO-GO: GO. Next: 6.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.2 Read-only project selector | 6.2.1 Add project selector UI in isolated lane | Objective: selector display. Scope: UI fixture/read-only. Allowed: project fixture/safe route if approved. Forbidden: project creation/live mutation. Work: render selector and unavailable states. Tests: render/no-write. Manual: selector review. Evidence: selector proof. Stop: creation/mutation. Recovery: fixture-only. GO/NO-GO: GO. Next: 6.3.1. Cartographer: SAFE WHILE SOAK RUNS unless live integration attempted. |
| 6.3 Project health display | 6.3.1 Add project health card | Objective: health card. Scope: UI read-only. Allowed: fixture/read-only data. Forbidden: health mutation. Work: render health/blockers/stale. Tests: render. Manual: review. Evidence: health card proof. Stop: mutation. Recovery: fixture. GO/NO-GO: GO. Next: 6.4.1. Cartographer: SAFE WHILE SOAK RUNS unless live integration attempted. |
| 6.4 Component/path ownership display | 6.4.1 Add component ownership card | Objective: ownership card. Scope: UI read-only. Allowed: fixture. Forbidden: map refresh writes. Work: render ownership/path risk. Tests: render. Manual: review. Evidence: ownership card proof. Stop: live write map. Recovery: fixture. GO/NO-GO: GO. Next: 6.5.1. Cartographer: SAFE WHILE SOAK RUNS unless live integration attempted. |
| 6.5 Project-scoped task context | 6.5.1 Add project-scoped task context chip | Objective: task/project link display. Scope: UI-only. Allowed: fixture project context. Forbidden: task execution/project mutation. Work: chip state. Tests: label. Manual: review. Evidence: project chip proof. Stop: live mutation. Recovery: unavailable. GO/NO-GO: GO. Next: 6.6.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.6 Design-system project context handoff | 6.6.1 Add design-context handoff display | Objective: project context in design packet. Scope: UI display. Allowed: fixture context. Forbidden: design apply/live Cartographer writes. Work: display project routes/components/tokens for design discussion. Tests: render/no-apply. Manual: review. Evidence: handoff proof. Stop: write bridge. Recovery: display-only. GO/NO-GO: GO. Next: 6.6.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.6 Design-system project context handoff | 6.6.2 Add blocked state for live Cartographer unavailable | Objective: gate live integration. Scope: UI state. Allowed: blocked label. Forbidden: probing/mutating live Cartographer. Work: render “soak result required/live unavailable” state. Tests: state test. Manual: gate review. Evidence: blocked proof. Stop: live call needed. Recovery: blocked state. GO/NO-GO: GO. Next: 6.7.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.7 Tests and manual validation | 6.7.1 Add tests | Objective: projects tests. Scope: targeted UI tests. Allowed: fixtures. Forbidden: live Cartographer writes. Work: selector/health/ownership/chip tests. Expected: pass. Manual: review. Evidence: test log. Stop: live mutation. Recovery: fixture test. GO/NO-GO: GO. Next: 6.7.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.7 Tests and manual validation | 6.7.2 Add manual checklist | Objective: manual proof. Scope: browser/no-write. Allowed: fixture/read-only mode. Forbidden: project creation/scan outside allowlist. Work: review selector/health/blocked states. Evidence: checklist. Stop: live mutation. Recovery: block. GO/NO-GO: GO. Next: 6.8.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 6.8 Closeout gate | 6.8.1 Closeout gate | Objective: Plan 7 readiness. Scope: closeout. Allowed: evidence summary. Forbidden: live integration. Work: summarize read-only projects proof and Cartographer gate. Tests: status/diff/no-Cartographer-write. Manual: operator review. Evidence: Plan 6 closeout. Stop: live dependency unresolved. Recovery: mark gated. GO/NO-GO: GO if project UI works read-only and does not disturb soak. Next: Plan 7, Phase 7.1, Increment 7.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 15. Plan 7: Settings Window Integration

Purpose: integrate the settings drawer/window as a safe display and configuration-intent surface. This plan is SAFE WHILE SOAK RUNS.

Constraints: do not persist settings unless later approved safe route exists; do not mutate env/config/auth; do not call providers; do not restart servers; do not create projects; do not fake provider availability; isolated proxy lane only.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 7.1 Settings surface inventory | 7.1.1 Inventory `settings-surface.ts` | Objective: settings inventory. Scope: read-only `/home/source/SpiritOS/src/lib/coding/settings-surface.ts`. Allowed: inspect. Forbidden: edits/persist. Work: map writable false rows. Tests: no mutation. Manual: review. Evidence: settings inventory. Stop: config writes. Recovery: display-only. GO/NO-GO: GO. Next: 7.1.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.1 Settings surface inventory | 7.1.2 Inventory provider/model surfaces | Objective: provider inventory. Scope: read-only model-provider status. Allowed: inspect. Forbidden: provider calls. Work: map availability truth. Tests: no mutation. Manual: review. Evidence: provider inventory. Stop: live call needed. Recovery: unavailable. GO/NO-GO: GO. Next: 7.1.3. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.1 Settings surface inventory | 7.1.3 Inventory backend truth surfaces | Objective: backend truth inventory. Scope: read-only backend truth. Allowed: inspect. Forbidden: route mutation. Work: map backend status fields. Tests: no mutation. Manual: review. Evidence: backend truth inventory. Stop: live mutation. Recovery: blocked. GO/NO-GO: GO. Next: 7.1.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 7.1 Settings surface inventory | 7.1.4 Inventory workspace context surfaces | Objective: workspace inventory. Scope: read-only workspace context. Allowed: inspect. Forbidden: project creation/scanning. Work: map read-list-only boundaries. Tests: no mutation. Manual: review. Evidence: workspace inventory. Stop: mutation needed. Recovery: display-only. GO/NO-GO: GO. Next: 7.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 7.2 Provider/model truth display | 7.2.1 Add settings drawer layout | Objective: drawer layout. Scope: UI. Allowed: isolated UI. Forbidden: persistence/provider. Work: sections/tabs/layout. Tests: render/focus. Manual: review. Evidence: layout proof. Stop: config write. Recovery: disable. GO/NO-GO: GO. Next: 7.2.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.2 Provider/model truth display | 7.2.2 Add provider/model truth display | Objective: provider truth display. Scope: UI. Allowed: existing truth/fixtures. Forbidden: provider calls/fake availability. Work: render local/cloud/codex/unavailable. Tests: no-call assertions. Manual: review. Evidence: provider display proof. Stop: network call. Recovery: unavailable. GO/NO-GO: GO. Next: 7.3.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.3 Workspace/project details display | 7.3.1 Add workspace/project truth display | Objective: workspace truth. Scope: UI. Allowed: read-only context. Forbidden: project creation/live mutation. Work: render root/project/read-list-only status. Tests: render. Manual: review. Evidence: workspace display proof. Stop: mutation. Recovery: blocked. GO/NO-GO: GO. Next: 7.6.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 7.6 Backend truth display | 7.6.1 Add backend status display | Objective: backend truth. Scope: UI. Allowed: existing safe status/fixtures. Forbidden: starting/restarting servers. Work: render backend availability/blocked route states. Tests: render/no-call if fixture. Manual: review. Evidence: backend display proof. Stop: restart needed. Recovery: unavailable. GO/NO-GO: GO. Next: 7.4.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 7.4 Usage/time/cost display | 7.4.1 Add usage/time display if safe data exists | Objective: usage display. Scope: UI. Allowed: existing safe data only. Forbidden: provider/billing calls. Work: render usage or disabled unavailable state. Tests: no-call. Manual: review. Evidence: usage proof. Stop: external call required. Recovery: unavailable state. GO/NO-GO: GO. Next: 7.5.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.5 Notification preference display | 7.5.1 Add disabled persistence state | Objective: show persistence disabled. Scope: UI. Allowed: display. Forbidden: persisting settings. Work: notification/preference controls disabled with reason. Tests: disabled assertions. Manual: review. Evidence: disabled state proof. Stop: persistence writes. Recovery: disable. GO/NO-GO: GO. Next: 7.6.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.6 Backend truth display | 7.6.2 Add no-provider-call proof | Objective: prove settings no external calls. Scope: tests/static assertion. Allowed: mocks. Forbidden: network. Work: assert no provider invocation. Expected: pass. Manual: review. Evidence: no-provider proof. Stop: call path. Recovery: remove. GO/NO-GO: GO. Next: 7.7.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.7 Accessibility and responsive behavior | 7.7.1 Add focus/keyboard behavior checks | Objective: WAI-ARIA drawer proof. Scope: tests/manual. Allowed: keyboard sim. Forbidden: hidden traps. Work: Escape/focus restore/labels. Tests: pass. Manual: keyboard checklist. Evidence: focus proof. Stop: inaccessible drawer. Recovery: fix. GO/NO-GO: GO. Next: 7.8.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.8 Tests and manual validation | 7.8.1 Add tests | Objective: settings tests. Scope: targeted UI tests. Allowed: Vitest. Forbidden: provider/env/config mutation. Work: truth display, disabled states, focus. Expected: pass. Manual: review. Evidence: test log. Stop: fail. Recovery: fix allowed. GO/NO-GO: GO. Next: 7.8.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.8 Tests and manual validation | 7.8.2 Add manual validation | Objective: operator settings review. Scope: manual. Allowed: browser no-write. Forbidden: save/persist. Work: inspect settings sections and disabled states. Evidence: checklist. Stop: mutation. Recovery: disable/gate. GO/NO-GO: GO. Next: 7.9.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 7.9 Closeout gate | 7.9.1 Closeout gate | Objective: Plan 8 readiness. Scope: closeout. Allowed: evidence summary. Forbidden: further implementation. Work: summarize truth/no-mutation proof. Tests: status/diff/no-provider. Manual: operator review. Evidence: Plan 7 closeout. Stop: env/config/provider mutation. Recovery: return to offender. GO/NO-GO: GO if settings displays truth and disabled states without mutation. Next: Plan 8, Phase 8.1, Increment 8.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 16. Plan 8: Pre-Soak-Completion Stabilization and Feature Assurance

Purpose: use remaining time while the 24-hour Cartographer soak continues to stabilize every safe Proxy, Design System, Codex-like, multimedia, projects-read-only, and settings-read-only feature before Cartographer integration. This plan is SAFE WHILE SOAK RUNS.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 8.1 Cross-feature regression matrix | 8.1.1 Build cross-feature matrix | Objective: matrix all safe features. Scope: evidence/test planning. Allowed: matrix doc. Forbidden: implementation. Work: list states/routes/tests/manual checks. Tests: review coverage. Manual: operator validates. Evidence: matrix. Stop: missing critical feature. Recovery: add row. GO/NO-GO: GO. Next: 8.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.2 `/coding` route manual operator rehearsal | 8.2.1 Test all command center states | Objective: operator rehearsal. Scope: manual/targeted tests. Allowed: isolated route. Forbidden: provider/apply. Work: empty/timeline/preview/approval/verify/blocked. Tests: relevant UI tests. Manual: checklist. Evidence: rehearsal proof. Stop: unsafe control. Recovery: fix/gate. GO/NO-GO: GO. Next: 8.3.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.3 Drawer and chip consistency pass | 8.3.1 Test all drawer states | Objective: drawer consistency. Scope: UI tests/manual. Allowed: drawers. Forbidden: mutation. Work: settings/diagnostics/evidence/design. Tests: open/close/focus. Manual: review. Evidence: drawer matrix. Stop: broken focus/authority. Recovery: fix. GO/NO-GO: GO. Next: 8.3.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.3 Drawer and chip consistency pass | 8.3.2 Test all chips | Objective: chip consistency. Scope: UI tests/manual. Allowed: chip states. Forbidden: hidden truth. Work: project/provider/safety/dirty/approval. Tests: label assertions. Manual: review. Evidence: chip matrix. Stop: misleading chip. Recovery: relabel. GO/NO-GO: GO. Next: 8.3.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.3 Drawer and chip consistency pass | 8.3.3 Test all blocked states | Objective: blocked-state proof. Scope: UI. Allowed: fixtures. Forbidden: bypass. Work: provider/apply/Cartographer/design/storage blocked. Tests: state tests. Manual: review. Evidence: blocked matrix. Stop: bypass. Recovery: block. GO/NO-GO: GO. Next: 8.4.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.4 Design token consistency pass without full CSS polish | 8.4.1 Test read-only design packet display | Objective: design packet regression. Scope: tests/manual. Allowed: display. Forbidden: apply. Work: view/compare/discuss labels. Tests: read-only assertions. Manual: review. Evidence: design packet proof. Stop: apply authority. Recovery: remove. GO/NO-GO: GO. Next: 8.5.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 8.5 Chat/media/projects/settings navigation rehearsal | 8.5.1 Test chat/media lane cards | Objective: lane nav proof. Scope: UI/manual. Allowed: read-only. Forbidden: storage/provider. Work: lane cards and evidence rows. Tests: render/no-storage. Manual: review. Evidence: chat/media proof. Stop: mutation. Recovery: fixture. GO/NO-GO: GO. Next: 8.5.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 8.5 Chat/media/projects/settings navigation rehearsal | 8.5.2 Test projects read-only shell | Objective: projects read-only proof. Scope: UI/manual. Allowed: fixture/read-only. Forbidden: live Cartographer mutation. Work: selector/health/ownership/blocked live state. Tests: render/no-write. Manual: review. Evidence: projects proof. Stop: live mutation. Recovery: blocked. GO/NO-GO: GO. Next: 8.5.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.5 Chat/media/projects/settings navigation rehearsal | 8.5.3 Test settings truth display | Objective: settings proof. Scope: UI/manual. Allowed: display. Forbidden: env/config/provider. Work: provider/workspace/backend/usage/disabled. Tests: no-provider. Manual: review. Evidence: settings proof. Stop: mutation. Recovery: disable. GO/NO-GO: GO. Next: 8.6.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 8.6 No-authority gauntlet | 8.6.1 Confirm no apply path | Objective: no apply proof. Scope: static/test. Allowed: grep/tests. Forbidden: execute-approved. Work: assert no enabled apply control. Tests: pass. Manual: review. Evidence: no-apply proof. Stop: apply path. Recovery: remove. GO/NO-GO: GO. Next: 8.6.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.6 No-authority gauntlet | 8.6.2 Confirm no execute-approved path | Objective: execute-approved blocked. Scope: static/test. Allowed: no-call assertion. Forbidden: route call. Work: assert route not invoked. Tests: pass. Manual: review. Evidence: no-execute proof. Stop: invocation. Recovery: remove. GO/NO-GO: GO. Next: 8.6.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.6 No-authority gauntlet | 8.6.3 Confirm no provider calls | Objective: provider blocked. Scope: tests/static. Allowed: mocks. Forbidden: network. Work: assert no provider/model calls. Tests: pass. Manual: review. Evidence: no-provider proof. Stop: call path. Recovery: disable. GO/NO-GO: GO. Next: 8.6.4. Cartographer: NOT DEPENDENT ON SOAK. |
| 8.6 No-authority gauntlet | 8.6.4 Confirm no Cartographer writes | Objective: Cartographer protected. Scope: status/diff/path review. Allowed: read-only. Forbidden: writes/log mutation. Work: check protected paths unchanged. Tests: status/diff. Manual: review. Evidence: no-Cartographer-write proof. Stop: protected change. Recovery: NO-GO. GO/NO-GO: GO. Next: 8.6.5. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.6 No-authority gauntlet | 8.6.5 Confirm no shared storage mutation | Objective: storage safety. Scope: tests/manual. Allowed: no-write assertions. Forbidden: IndexedDB/localStorage destructive writes. Work: verify no storage mutation. Tests: pass. Manual: review. Evidence: storage proof. Stop: storage changed. Recovery: NO-GO/fix. GO/NO-GO: GO. Next: 8.6.6. Cartographer: NOT DEPENDENT ON SOAK. |
| 8.6 No-authority gauntlet | 8.6.6 Confirm no soak log mutation | Objective: soak logs untouched. Scope: read-only status/path check. Allowed: no-write proof. Forbidden: log writes. Work: confirm no soak log changes. Tests: status/diff. Manual: review. Evidence: soak log proof. Stop: log changed. Recovery: NO-GO. GO/NO-GO: GO. Next: 8.7.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.7 Evidence consolidation | 8.7.1 Produce readiness evidence | Objective: consolidate Plan 8. Scope: evidence root. Allowed: isolated evidence. Forbidden: live evidence. Work: package matrix/proofs/checklists. Tests: artifact review. Manual: operator review. Evidence: readiness package. Stop: missing proof. Recovery: rerun safe checks. GO/NO-GO: GO. Next: 8.8.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 8.8 Closeout gate | 8.8.1 Closeout gate | Objective: decide Plan 9 readiness. Scope: closeout. Allowed: evidence summary. Forbidden: Cartographer live integration. Work: identify only remaining true blockers. Tests: final status/diff/no-authority. Manual: operator acceptance. Evidence: Plan 8 closeout. Stop: non-Cartographer features unstable. Recovery: return to failing increment. GO/NO-GO: GO if only remaining blocker is soak acceptance or exact integration approval. Next: Plan 9, Phase 9.1, Increment 9.1.1 only. Cartographer: SAFE WHILE SOAK RUNS. |

## 17. Plan 9: Cartographer Integration Preparation

Purpose: prepare for full Cartographer integration while ensuring the active 24-hour Cartographer soak test remains undisturbed. This plan is PARTIAL WHILE SOAK RUNS. Read-only inventory, contract drafting, fixture simulation, and no-write bridge simulation are SAFE WHILE SOAK RUNS. Any live Cartographer integration is CARTOGRAPHER SOAK RESULT REQUIRED BEFORE THIS INCREMENT.

Constraints: no Cartographer writes, no soak log writes, no live evidence writes, no proposal approval, no blueprint refresh writes, no project-health mutation, no worker dispatch, no task queue mutation, no branch/worktree/commit/push, isolated proxy lane only.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 9.1 Cartographer live boundary inventory | 9.1.1 Inventory Cartographer routes | Objective: route inventory. Scope: read-only `/src/app/v1/cartographer/*` and `/src/app/map/*`. Allowed: inspect. Forbidden: live calls that mutate. Work: map routes and method boundaries. Tests: no mutation. Manual: review. Evidence: route inventory. Stop: route behavior unclear. Recovery: mark forbidden. GO/NO-GO: GO. Next: 9.1.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.1 Cartographer live boundary inventory | 9.1.2 Inventory Cartographer Python modules | Objective: module inventory. Scope: read-only `source_proxy/cartographer/*`. Allowed: inspect. Forbidden: running mutating modules. Work: map project discovery/health/component/repo/live state. Tests: no mutation. Manual: review. Evidence: module inventory. Stop: write risk unclear. Recovery: forbid. GO/NO-GO: GO. Next: 9.1.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.1 Cartographer live boundary inventory | 9.1.3 Inventory soak log and live evidence paths | Objective: protect evidence. Scope: read-only path inventory. Allowed: list only. Forbidden: writes/touch. Work: identify docs/live evidence/receipts/log classes. Tests: no mutation. Manual: review. Evidence: soak path inventory. Stop: active path unknown. Recovery: mark broad forbidden. GO/NO-GO: GO. Next: 9.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.2 Soak-state protection map | 9.2.1 Identify forbidden write paths | Objective: no-write map. Scope: contract. Allowed: evidence. Forbidden: writes. Work: mark logs, runtime, map, live evidence, queues, workers. Tests: path overlap review. Manual: operator confirms. Evidence: forbidden write map. Stop: missing path. Recovery: add/gate. GO/NO-GO: GO. Next: 9.3.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.3 Read-only project/component/drift contract | 9.3.1 Define read-only map/project/component/drift display contract | Objective: display contract. Scope: contract/fixtures. Allowed: read-only schema. Forbidden: map refresh writes. Work: fields for project, components, drift, staleness, source. Tests: schema review. Manual: review. Evidence: contract. Stop: live write needed. Recovery: fixture. GO/NO-GO: GO. Next: 9.4.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.4 Cartographer evidence display contract | 9.4.1 Define evidence display contract | Objective: evidence display. Scope: read-only contract. Allowed: isolated evidence references. Forbidden: live evidence writes. Work: receipt/evidence/state display fields. Tests: no-write review. Manual: review. Evidence: evidence contract. Stop: write needed. Recovery: read-only. GO/NO-GO: GO. Next: 9.5.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.5 Event vocabulary | 9.5.1 Define event vocabulary | Objective: Cartographer-to-command-center vocabulary. Scope: contract. Allowed: event names. Forbidden: worker dispatch. Work: events for unavailable, stale, drift, health, recommendation, blocked. Tests: review. Manual: review. Evidence: vocabulary. Stop: event triggers mutation. Recovery: display-only. GO/NO-GO: GO. Next: 9.6.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.6 No-write bridge simulation | 9.6.1 Build fixture-only bridge simulation | Objective: simulate bridge without live Cartographer. Scope: fixtures/tests. Allowed: isolated fixtures. Forbidden: live integration. Work: fixture adapter returns read-only packets. Tests: render/schema. Manual: review. Evidence: simulation proof. Stop: live call required. Recovery: fixture only. GO/NO-GO: GO. Next: 9.6.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.6 No-write bridge simulation | 9.6.2 Build no-write proof test | Objective: prove no writes. Scope: tests/static assertions. Allowed: fixture/mocks. Forbidden: writes/logs. Work: assert no Cartographer write APIs/log paths invoked. Tests: pass. Manual: review. Evidence: no-write proof. Stop: write path. Recovery: remove. GO/NO-GO: GO. Next: 9.6.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.6 No-write bridge simulation | 9.6.3 Build blocked state for "soak running" | Objective: UI blocker. Scope: UI fixture. Allowed: blocked display. Forbidden: live mutation. Work: render soak-running blocker. Tests: state test. Manual: review. Evidence: blocker proof. Stop: bypass. Recovery: block. GO/NO-GO: GO. Next: 9.6.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.6 No-write bridge simulation | 9.6.4 Build blocked state for "soak result required" | Objective: integration gate display. Scope: UI fixture. Allowed: blocked display. Forbidden: integration. Work: render exact `CARTOGRAPHER SOAK RESULT REQUIRED BEFORE THIS INCREMENT`. Tests: state test. Manual: review. Evidence: gate proof. Stop: live integration enabled. Recovery: disable. GO/NO-GO: GO. Next: 9.7.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.7 Tests and manual validation | 9.7.1 Add manual checklist | Objective: preparation proof. Scope: manual/targeted tests. Allowed: fixture simulation. Forbidden: live writes. Work: checklist routes/modules/no-write/blockers. Tests: no-write tests. Manual: operator review. Evidence: checklist/logs. Stop: mutation. Recovery: NO-GO. GO/NO-GO: GO. Next: 9.8.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 9.8 Closeout gate | 9.8.1 Closeout gate | Objective: future decision readiness only. Scope: closeout. Allowed: evidence summary. Forbidden: full integration. Work: summarize preparation and gates. Tests: final no-write/status/diff. Manual: operator review. Evidence: Plan 9 closeout. Stop: missing protection. Recovery: return. GO/NO-GO: GO only for a future explicit Cartographer integration decision; this does not execute integration. Next: Plan 10 only when soak result exists; otherwise Plan 8 safe stabilization. Cartographer: PARTIAL WHILE SOAK RUNS. |

## 18. Plan 10: Cartographer Soak Result Gate and Full Integration Decision

Purpose: define the point where work may need to wait for the 24-hour Cartographer soak result. This plan is CARTOGRAPHER SOAK RESULT REQUIRED.

Do not start this plan until the 24-hour Cartographer soak has completed, the soak result exists, the result has been reviewed, any failure is triaged, and the operator accepts the result or explicitly allows proceeding with known risk.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 10.1 Soak result evidence intake | 10.1.1 Locate soak result evidence without mutating it | Objective: find result. Scope: read-only evidence intake. Allowed: read-only open/list. Forbidden: writing/touching logs. Work: locate final result. Tests: no mutation. Manual: operator confirms source. Evidence: intake note. Stop: result absent. Recovery: continue Plan 8 safe work. GO/NO-GO: GO if result exists. Next: 10.1.2. Cartographer: CARTOGRAPHER SOAK RESULT REQUIRED BEFORE THIS INCREMENT. |
| 10.1 Soak result evidence intake | 10.1.2 Verify no soak gaps | Objective: completeness. Scope: read-only review. Allowed: inspect result. Forbidden: editing evidence. Work: check duration/gaps. Tests: checklist. Manual: review. Evidence: gap review. Stop: gaps. Recovery: classify warning/fail. GO/NO-GO: GO if complete/accepted. Next: 10.2.1. Cartographer: POST-SOAK ONLY. |
| 10.2 Soak result classification | 10.2.1 Verify no hidden mutation, approval bypass, worker/queue anomalies, runtime corruption | Objective: safety review. Scope: evidence review. Allowed: read-only logs/receipts. Forbidden: repair mutation. Work: review mutation/bypass/worker/queue/runtime indicators. Tests: checklist. Manual: operator review. Evidence: safety review. Stop: anomaly. Recovery: classify fail/inconclusive. GO/NO-GO: GO if no blocking anomaly or accepted risk. Next: 10.2.2. Cartographer: POST-SOAK ONLY. |
| 10.2 Soak result classification | 10.2.2 Classify PASS / PASS WITH WARNINGS / FAIL / INCONCLUSIVE | Objective: result classification. Scope: decision packet. Allowed: evidence summary. Forbidden: integration. Work: assign classification and rationale. Tests: classification review. Manual: operator review. Evidence: classification packet. Stop: unclear evidence. Recovery: NEEDS OPERATOR REVIEW. GO/NO-GO: GO if classification accepted. Next: 10.3.1. Cartographer: POST-SOAK ONLY. |
| 10.3 Cartographer safety readiness decision | 10.3.1 Produce safety readiness decision | Objective: decide if integration planning can proceed. Scope: decision only. Allowed: packet. Forbidden: integration. Work: compare result to Plan 9 gates. Tests: checklist. Manual: operator review. Evidence: readiness decision. Stop: fail/inconclusive unaccepted. Recovery: block integration. GO/NO-GO: GO if accepted. Next: 10.4.1. Cartographer: POST-SOAK ONLY. |
| 10.4 Integration risk review | 10.4.1 Review integration risks | Objective: risk register. Scope: planning. Allowed: evidence. Forbidden: live writes. Work: risks by route/service/evidence/rollback. Tests: review. Manual: operator accepts. Evidence: risk register. Stop: unbounded risk. Recovery: narrow scope. GO/NO-GO: GO if risks bounded. Next: 10.5.1. Cartographer: POST-SOAK ONLY. |
| 10.5 Operator decision packet | 10.5.1 Produce decision packet and ask for operator GO/NO-GO if required | Objective: operator decision. Scope: packet. Allowed: decision text. Forbidden: self-approval. Work: summarize result/classification/risk/next exact increment. Tests: completeness. Manual: operator decision. Evidence: decision packet. Stop: no operator decision. Recovery: NO-GO. GO/NO-GO: GO only with accepted result or explicit constrained risk approval. Next: Plan 11, Phase 11.1, Increment 11.1.1 only if approved. Cartographer: POST-SOAK ONLY. |
| 10.6 Closeout gate | 10.6.1 Closeout gate | Objective: close Plan 10. Scope: closeout. Allowed: summary. Forbidden: integration. Work: record PASS/PASS WITH WARNINGS/FAIL/INCONCLUSIVE and next. Tests: final no-mutation. Manual: operator acceptance. Evidence: Plan 10 closeout. Stop: result not ready. Recovery: continue Plan 8 or other safe non-Cartographer work; do not mutate Cartographer to help soak finish. GO/NO-GO: GO only if accepted. Next: Plan 11 exact increment only. Cartographer: POST-SOAK ONLY. |

## 19. Plan 11: Full Cartographer Integration Gate Plan

Purpose: define the future gate for full Cartographer integration after preparation is accepted and soak results permit continuation. This plan must not execute integration unless separately approved.

The future approval must include exact allowed files, exact forbidden files, exact Cartographer read/write boundary, soak-test protection procedure, evidence directory, test matrix, rollback procedure, and operator acceptance checklist.

Constraints: do not execute full integration unless operator separately authorizes exact increment; no live writes until read-only bridge passes; no proposal approval until proposal display passes; no apply-approved until Preview -> Approval -> Apply -> Verify gates are independently accepted; no hidden workers; no hidden queues; no autonomous promotion; no branch/worktree/commit/push.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 11.1 Integration prerequisites | 11.1.1 Define exact integration prerequisites | Objective: prerequisites list. Scope: planning. Allowed: evidence. Forbidden: integration. Work: accepted Plan 9, accepted Plan 10, exact approval, allowlist, tests. Tests: checklist. Manual: operator review. Evidence: prerequisites packet. Stop: missing acceptance. Recovery: block. GO/NO-GO: GO if complete. Next: 11.2.1. Cartographer: POST-SOAK ONLY. |
| 11.2 Required acceptance evidence | 11.2.1 Define required acceptance evidence | Objective: evidence requirements. Scope: planning. Allowed: matrix. Forbidden: live writes. Work: commands, screenshots, no-write proof, rollback, manual checklist. Tests: review. Manual: operator review. Evidence: acceptance evidence matrix. Stop: proof vague. Recovery: refine. GO/NO-GO: GO. Next: 11.3.1. Cartographer: POST-SOAK ONLY. |
| 11.3 Safe read-only bridge first | 11.3.1 Define safe read-only bridge first increment | Objective: first integration increment template. Scope: planning. Allowed: exact future file set. Forbidden: writes. Work: define read-only adapter, tests, blocked states. Tests: plan review. Manual: operator approval needed later. Evidence: bridge template. Stop: live writes. Recovery: narrow. GO/NO-GO: GO for planning only. Next: 11.4.1. Cartographer: POST-SOAK ONLY. |
| 11.4 Optional proposal-display bridge | 11.4.1 Define optional proposal-display bridge | Objective: proposal display gate. Scope: planning. Allowed: display-only future scope. Forbidden: proposal approval/apply. Work: template for displaying Cartographer recommendations. Tests: review. Manual: approval later. Evidence: proposal bridge template. Stop: authority expansion. Recovery: display-only. GO/NO-GO: GO. Next: 11.5.1. Cartographer: POST-SOAK ONLY. |
| 11.5 Optional approval-preview bridge | 11.5.1 Define optional approval-preview bridge | Objective: preview bridge gate. Scope: planning. Allowed: future preview-only scope. Forbidden: apply-approved. Work: define how preview enters Source Proxy loop. Tests: authority review. Manual: approval later. Evidence: preview bridge template. Stop: apply implied. Recovery: remove. GO/NO-GO: GO. Next: 11.6.1. Cartographer: POST-SOAK ONLY. |
| 11.6 Full integration GO/NO-GO decision packet | 11.6.1 Produce full integration decision packet | Objective: future exact approval packet. Scope: planning. Allowed: packet. Forbidden: execution. Work: allowed/forbidden files, read/write boundaries, tests, rollback, acceptance. Tests: completeness. Manual: operator decision required later. Evidence: decision packet. Stop: missing exact command/lane. Recovery: NO-GO. GO/NO-GO: GO only as planning. Next: 11.7.1. Cartographer: POST-SOAK ONLY. |
| 11.7 Closeout gate | 11.7.1 Closeout gate | Objective: close Plan 11. Scope: closeout. Allowed: summary. Forbidden: integration. Work: state that future full integration requires separate exact approval. Tests: no-mutation. Manual: operator review. Evidence: Plan 11 closeout. Stop: integration implied. Recovery: revise. GO/NO-GO: GO only if no execution occurred. Next: Plan 12, Phase 12.1, Increment 12.1.1 only. Cartographer: POST-SOAK ONLY. |

## 20. Plan 12: Final Comprehensive CSS Polish Readiness

Purpose: determine whether the site is ready for final CSS polish using the proxy system. This plan can partially proceed before Cartographer full integration, but any Cartographer-dependent visual surface is post-soak/post-integration.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 12.1 Route-scoped CSS risk inventory | 12.1.1 Inventory all routes that need polish | Objective: route list. Scope: inventory. Allowed: read-only. Forbidden: CSS edits. Work: list `/coding`, chat/media, projects/settings, dashboard/map. Tests: review. Manual: operator review. Evidence: route inventory. Stop: ownership unclear. Recovery: classify unknown. GO/NO-GO: GO. Next: 12.1.2. Cartographer: SAFE WHILE SOAK RUNS except map live surfaces. |
| 12.1 Route-scoped CSS risk inventory | 12.1.2 Classify route risk | Objective: risk levels. Scope: inventory. Allowed: evidence. Forbidden: edits. Work: classify high/medium/low and authority visibility risk. Tests: review. Manual: review. Evidence: route risk matrix. Stop: hidden authority risk. Recovery: high-risk gate. GO/NO-GO: GO. Next: 12.1.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 12.1 Route-scoped CSS risk inventory | 12.1.3 Identify CSS files and component files per route | Objective: file map. Scope: inventory. Allowed: read-only. Forbidden: edits. Work: map globals/styles/theme/components. Tests: overlap review. Manual: review. Evidence: file map. Stop: broad global risk. Recovery: route-scope. GO/NO-GO: GO. Next: 12.2.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 12.2 Design token readiness check | 12.2.1 Classify shared component risk | Objective: component risk. Scope: inventory. Allowed: evidence. Forbidden: edits. Work: UI primitive impact map. Tests: review. Manual: design review. Evidence: component risk matrix. Stop: shared breakage likely. Recovery: isolate. GO/NO-GO: GO. Next: 12.2.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 12.2 Design token readiness check | 12.2.2 Define token cleanup plan | Objective: token plan. Scope: planning. Allowed: no code. Forbidden: token edits. Work: cleanup order and validation. Tests: review. Manual: review. Evidence: token cleanup plan. Stop: one-note palette/global risk. Recovery: route-scope. GO/NO-GO: GO. Next: 12.2.3. Cartographer: NOT DEPENDENT ON SOAK. |
| 12.2 Design token readiness check | 12.2.3 Define no-global-breakage plan | Objective: CSS safety. Scope: planning. Allowed: evidence. Forbidden: global sweep. Work: route screenshots/tests before shared CSS edits. Tests: review. Manual: review. Evidence: no-global-breakage plan. Stop: broad sweep. Recovery: route-by-route. GO/NO-GO: GO. Next: 12.3.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 12.3 Component consistency inventory | 12.3.1 Define screenshot/manual proof requirements | Objective: proof checklist. Scope: planning. Allowed: checklist. Forbidden: CSS edits. Work: route screenshot checklist. Tests: review. Manual: review. Evidence: screenshot proof plan. Stop: proof unavailable. Recovery: fallback manual. GO/NO-GO: GO. Next: 12.3.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 12.3 Component consistency inventory | 12.3.2 Define mobile/tablet/desktop viewports | Objective: viewport spec. Scope: planning. Allowed: evidence. Forbidden: CSS edits. Work: define widths and acceptance. Tests: review. Manual: review. Evidence: viewport spec. Stop: overlap risk untested. Recovery: add viewport. GO/NO-GO: GO. Next: 12.8.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 12.8 Accessibility readiness | 12.8.1 Define accessibility proof requirements | Objective: a11y readiness. Scope: planning. Allowed: checklist. Forbidden: CSS edits. Work: focus, contrast, labels, reduced motion, drawers. Tests: review. Manual: review. Evidence: a11y proof requirements. Stop: untestable. Recovery: refine. GO/NO-GO: GO. Next: 12.4.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 12.4 Command center polish readiness | 12.4.1 Assess command center polish readiness | Objective: `/coding` readiness. Scope: inventory/checks. Allowed: evidence. Forbidden: CSS edits. Work: check foundation/Plan 4 proof. Tests: review. Manual: route review. Evidence: `/coding` readiness. Stop: foundation unstable. Recovery: return Plan 2-4. GO/NO-GO: GO. Next: 12.5.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 12.5 Chat/media polish readiness | 12.5.1 Assess chat/media polish readiness | Objective: lane readiness. Scope: evidence. Allowed: review. Forbidden: storage mutation/CSS edits. Work: check Plan 5 proof. Tests: review. Manual: review. Evidence: chat/media readiness. Stop: storage risk. Recovery: return Plan 5. GO/NO-GO: GO. Next: 12.6.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 12.6 Projects/settings polish readiness | 12.6.1 Assess projects/settings polish readiness | Objective: readiness. Scope: evidence. Allowed: review. Forbidden: config/live mutation/CSS edits. Work: check Plans 6-7 proof. Tests: review. Manual: review. Evidence: projects/settings readiness. Stop: live dependency. Recovery: block live parts. GO/NO-GO: GO. Next: 12.7.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 12.7 Cartographer/map polish dependency check | 12.7.1 Identify Cartographer-dependent surfaces that must wait | Objective: gate map surfaces. Scope: dependency classification. Allowed: evidence. Forbidden: map polish/integration. Work: mark map/dashboard Cartographer visuals post-soak/integration if needed. Tests: review. Manual: operator review. Evidence: Cartographer visual dependency matrix. Stop: tries to polish live surface. Recovery: gate. GO/NO-GO: GO if gated. Next: 12.9.1. Cartographer: CARTOGRAPHER SOAK RESULT REQUIRED BEFORE THIS INCREMENT for live integrated polish; otherwise SAFE for planning. |
| 12.9 Responsive readiness | 12.9.1 Assess responsive readiness | Objective: responsive gate. Scope: checklist. Allowed: manual/fixture checks. Forbidden: CSS edits. Work: route viewport readiness. Tests: review. Manual: checklist. Evidence: responsive readiness. Stop: major overlap. Recovery: plan targeted fix. GO/NO-GO: GO. Next: 12.10.1. Cartographer: SAFE WHILE SOAK RUNS. |
| 12.10 Closeout gate | 12.10.1 Produce CSS readiness closeout | Objective: decide Plan 13 readiness. Scope: closeout. Allowed: evidence. Forbidden: polish execution. Work: summarize route risks, file map, proof plan, gates. Tests: status/diff. Manual: operator acceptance. Evidence: Plan 12 closeout. Stop: CSS cannot be route-scoped safely. Recovery: return to readiness increment. GO/NO-GO: GO only if final CSS polish can execute route-by-route inside proxy system without breaking safety or authority visibility. Next: Plan 13, Phase 13.1, Increment 13.1.1 only. Cartographer: PARTIAL WHILE SOAK RUNS. |

## 21. Plan 13: Final Comprehensive CSS Polish Execution Plan

Purpose: perform final CSS polish across the Next.js and TypeScript architecture only after foundation, Codex-like command center features, multimedia lanes, projects read-only shell, settings window, Cartographer preparation, and any required Cartographer integration gates are stable. This plan is last.

Constraints: no CSS-wide sweep before route-scoped risks are known; no hidden visual changes to Cartographer live surfaces; no mutation of soak state; no design-agent apply authority; no Source Proxy authority changes; no package changes unless separately approved; isolated proxy lane proof first; main repo merge only after explicit operator approval.

| Phase | Increment title | PIVOT card |
|---|---|---|
| 13.1 Route-scoped CSS risk inventory confirmation | 13.1.1 Confirm token audit and route risk | Objective: confirm Plan 12. Scope: evidence. Allowed: review. Forbidden: edits until GO. Work: confirm route order/files. Tests: checklist. Manual: operator review. Evidence: confirmation. Stop: risk unresolved. Recovery: Plan 12. GO/NO-GO: GO. Next: 13.2.1. Cartographer: PARTIAL. |
| 13.2 Token cleanup | 13.2.1 Token audit | Objective: inspect tokens. Scope: exact approved files. Allowed: route-scoped token cleanup if authorized. Forbidden: broad palette rewrite. Work: audit/apply minimal token cleanup. Tests: visual/type/lint. Manual: screenshots. Evidence: token proof. Stop: global breakage. Recovery: owned patch reversal. GO/NO-GO: GO. Next: 13.2.2. Cartographer: NOT DEPENDENT ON SOAK. |
| 13.2 Token cleanup | 13.2.2 Global CSS risk review | Objective: global CSS safety. Scope: review/targeted edits only if approved. Allowed: minimal utility fixes. Forbidden: sweeping globals. Work: inspect global impacts. Tests: route snapshots/manual. Manual: review. Evidence: global risk proof. Stop: hidden breakage. Recovery: revert owned CSS. GO/NO-GO: GO. Next: 13.3.1. Cartographer: SAFE WHILE SOAK RUNS for non-map routes. |
| 13.3 Component consistency pass | 13.3.1 UI component class consistency | Objective: consistent UI primitives. Scope: approved component files. Allowed: class consistency. Forbidden: authority copy changes. Work: polish primitive classes. Tests: component tests. Manual: visual review. Evidence: component proof. Stop: authority hidden. Recovery: restore labels. GO/NO-GO: GO. Next: 13.4.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 13.4 `/coding` command-center polish | 13.4.1 `/coding` desktop polish | Objective: desktop polish. Scope: approved `/coding` UI files. Allowed: visual/layout only. Forbidden: backend/provider/apply. Work: desktop spacing/density/readability. Tests: UI tests. Manual: desktop screenshot. Evidence: desktop proof. Stop: overlap/authority hidden. Recovery: targeted revert. GO/NO-GO: GO. Next: 13.4.2. Cartographer: SAFE WHILE SOAK RUNS. |
| 13.4 `/coding` command-center polish | 13.4.2 `/coding` mobile polish | Objective: mobile polish. Scope: approved UI/CSS. Allowed: responsive fixes. Forbidden: broad redesign. Work: mobile collapse, composer, chips. Tests: responsive checks. Manual: mobile screenshot. Evidence: mobile proof. Stop: text overlap. Recovery: targeted fix/revert. GO/NO-GO: GO. Next: 13.4.3. Cartographer: SAFE WHILE SOAK RUNS. |
| 13.4 `/coding` command-center polish | 13.4.3 Drawer polish | Objective: drawer visuals. Scope: drawer components. Allowed: spacing/focus styles. Forbidden: authority changes. Work: settings/diagnostics/evidence/design drawers. Tests: focus. Manual: keyboard/screenshot. Evidence: drawer proof. Stop: focus broken. Recovery: fix/revert. GO/NO-GO: GO. Next: 13.4.4. Cartographer: SAFE WHILE SOAK RUNS. |
| 13.4 `/coding` command-center polish | 13.4.4 Chip polish | Objective: chip readability. Scope: chips. Allowed: style only. Forbidden: hiding states. Work: chip density/contrast/wrapping. Tests: chip label. Manual: screenshot. Evidence: chip proof. Stop: state hidden. Recovery: restore. GO/NO-GO: GO. Next: 13.4.5. Cartographer: SAFE WHILE SOAK RUNS. |
| 13.4 `/coding` command-center polish | 13.4.5 Active task transcript polish | Objective: transcript readability. Scope: transcript UI. Allowed: spacing/typography. Forbidden: event behavior changes. Work: timeline readability. Tests: render. Manual: screenshot. Evidence: transcript proof. Stop: event confusion. Recovery: revert. GO/NO-GO: GO. Next: 13.4.6. Cartographer: SAFE WHILE SOAK RUNS. |
| 13.4 `/coding` command-center polish | 13.4.6 Composer polish | Objective: composer usability. Scope: composer UI. Allowed: visual/disabled styles. Forbidden: provider submit. Work: polish input/buttons/blocked states. Tests: no-call/render. Manual: check typing. Evidence: composer proof. Stop: submit executes. Recovery: disable. GO/NO-GO: GO. Next: 13.4.7. Cartographer: NOT DEPENDENT ON SOAK. |
| 13.4 `/coding` command-center polish | 13.4.7 Design packet polish | Objective: design packet readability. Scope: packet UI. Allowed: layout/visual. Forbidden: apply controls. Work: improve packet card/compare. Tests: read-only. Manual: screenshot. Evidence: design packet proof. Stop: apply implied. Recovery: remove. GO/NO-GO: GO. Next: 13.5.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 13.5 Chat/media lane polish | 13.5.1 Chat/media polish | Objective: lane polish. Scope: approved chat/media lane display. Allowed: visual only. Forbidden: storage/provider. Work: cards/lists/responsive. Tests: no-storage/no-provider. Manual: screenshots. Evidence: lane proof. Stop: mutation. Recovery: revert. GO/NO-GO: GO. Next: 13.6.1. Cartographer: NOT DEPENDENT ON SOAK. |
| 13.6 Projects/settings polish | 13.6.1 Projects/settings polish | Objective: polish read-only surfaces. Scope: approved UI. Allowed: visual/layout. Forbidden: config/project mutation. Work: selector/health/settings drawers. Tests: no-write/no-provider. Manual: screenshots. Evidence: projects/settings proof. Stop: mutation. Recovery: revert. GO/NO-GO: GO. Next: 13.7.1. Cartographer: SAFE WHILE SOAK RUNS for read-only surfaces. |
| 13.7 Dashboard/map non-regression review | 13.7.1 Dashboard non-regression | Objective: dashboard unaffected. Scope: manual/tests. Allowed: review. Forbidden: hidden Cartographer visual changes. Work: inspect dashboard widgets. Tests: targeted if available. Manual: screenshot. Evidence: dashboard proof. Stop: regression. Recovery: fix/revert. GO/NO-GO: GO. Next: 13.7.2. Cartographer: SAFE WHILE SOAK RUNS for non-live review. |
| 13.7 Dashboard/map non-regression review | 13.7.2 Map/Cartographer visual non-regression, if integration is allowed and stable | Objective: map visual proof only if gates allow. Scope: post-soak/integration allowed files. Allowed: review/polish only after approval. Forbidden: live surface mutation before gate. Work: inspect/polish map surfaces if approved. Tests: screenshots/no-write. Manual: review. Evidence: map proof. Stop: soak/integration not accepted. Recovery: skip/gate. GO/NO-GO: GO only post-gate. Next: 13.8.1. Cartographer: CARTOGRAPHER SOAK RESULT REQUIRED BEFORE THIS INCREMENT when live integrated. |
| 13.8 Accessibility pass | 13.8.1 Accessibility keyboard/focus check | Objective: a11y proof. Scope: all polished routes. Allowed: manual/tests. Forbidden: behavior authority changes. Work: keyboard/focus/labels/contrast. Tests: a11y smoke. Manual: checklist. Evidence: a11y proof. Stop: inaccessible control. Recovery: fix. GO/NO-GO: GO. Next: 13.9.1. Cartographer: SAFE WHILE SOAK RUNS for non-map. |
| 13.9 Responsive/mobile pass | 13.9.1 Responsive viewport check | Objective: responsive proof. Scope: all polished routes. Allowed: manual/screenshots. Forbidden: CSS-wide new sweep. Work: mobile/tablet/desktop checks. Tests: visual/manual. Evidence: viewport proof. Stop: overlap. Recovery: targeted fix. GO/NO-GO: GO. Next: 13.10.1. Cartographer: SAFE WHILE SOAK RUNS for non-map. |
| 13.10 Browser/manual visual proof | 13.10.1 Manual screenshot checklist | Objective: visual evidence. Scope: browser proof. Allowed: screenshots in isolated evidence. Forbidden: live evidence/soak writes. Work: capture route screenshots and notes. Tests: manual. Evidence: screenshot package. Stop: missing critical route. Recovery: capture/fix. GO/NO-GO: GO. Next: 13.11.1. Cartographer: PARTIAL. |
| 13.11 Final regression test package | 13.11.1 Final evidence package | Objective: final regression. Scope: tests/evidence. Allowed: typecheck/lint/targeted tests/manual. Forbidden: mutating soak/provider/apply. Work: run final matrix. Expected: pass. Manual: review. Evidence: final package. Stop: failing required check. Recovery: fix allowed. GO/NO-GO: GO. Next: 13.12.1. Cartographer: PARTIAL. |
| 13.12 Closeout gate | 13.12.1 Closeout gate | Objective: final polish decision. Scope: closeout. Allowed: evidence summary. Forbidden: merge/self-approval. Work: summarize tests, visual proof, no-authority regression, remaining gates. Tests: final status/diff. Manual: operator acceptance. Evidence: Plan 13 closeout. Stop: proof incomplete or authority hidden. Recovery: return to failing increment. GO/NO-GO: GO only if visual polish is proven and no-authority regression holds. Next: no next plan unless operator authorizes merge/next roadmap. Cartographer: PARTIAL/POST-SOAK for live surfaces. |

## 22. Multi-Day Execution Cadence

This roadmap spans 3 to 7 days. It advances increment by increment. It does not promise exact completion dates, imply background work, or claim asynchronous continuation.

| Day band | Work | Soak posture |
|---|---|---|
| Day 1 | Plan 0 isolated lane baseline. Plan 1 unified architecture contract. Begin Plan 2 minimum implementation. | Safe while Cartographer soak runs. |
| Day 2 | Finish Plan 2. Execute Plan 3 foundation tests. Begin Plan 4 Codex-like active task feature completion. | Safe while Cartographer soak runs. |
| Day 3 | Finish Plan 4. Execute Plan 5 multimedia work chat lanes. Begin Plan 6 projects read-only integration. | Safe while Cartographer soak runs. |
| Day 4 | Finish Plan 6. Execute Plan 7 settings window. Execute Plan 8 pre-soak stabilization and feature assurance. | Safe while Cartographer soak runs. |
| Day 5 | Execute Plan 9 Cartographer preparation. If 24-hour soak result is complete and accepted, execute Plan 10 decision gate. If result is not ready or not accepted, continue non-Cartographer stabilization and do not mutate Cartographer. | Partial; live integration gated. |
| Day 6 | If approved, execute Plan 11 Cartographer integration gate planning. Execute Plan 12 final CSS readiness. Begin route-scoped polish planning. | Post-soak where needed. |
| Day 7 | Execute Plan 13 final comprehensive CSS polish execution plan only after required gates are satisfied. | Last; Cartographer surfaces only after gates. |

## 23. Required Testing Matrix

| Test category | First appears | Exact command or manual check | Isolated-lane evidence artifact | Failure meaning | Blocks next increment? | Cartographer soak dependency |
|---|---|---|---|---|---:|---|
| Git status snapshot | 0.2.1 | `git status --short --branch --untracked-files=normal` | `plan-00-status-snapshot` | Dirty state unknown or unexpected. | Yes | SAFE WHILE SOAK RUNS |
| Diff check | 0.2.2 / 3.1.1 | `git diff --stat` and `git diff --name-only` | `plan-00-diff-summary`, later plan diff logs | Scope unclear. | Yes | SAFE WHILE SOAK RUNS |
| TypeScript check | 3.2.1 | `npm run typecheck` | `plan-03-typecheck.log` | Type safety failed or unrelated failure needs review. | Yes unless accepted known unrelated | NOT DEPENDENT ON SOAK |
| Lint check if available | 3.2.2 | `npm run lint` | `plan-03-lint.log` | New lint failure. | Yes | NOT DEPENDENT ON SOAK |
| Targeted Vitest checks | 3.3.1 | `npx --no-install vitest run <targeted coding tests>` | `plan-03-vitest-coding.log` | UI foundation broken. | Yes | SAFE WHILE SOAK RUNS |
| Chip/blocked state tests | 3.3.2 | Targeted Vitest/Testing Library assertions | `plan-03-chip-blocked-tests.log` | Truth/safety display misleading. | Yes | SAFE WHILE SOAK RUNS |
| Drawer behavior checks | 3.3.3 | Testing Library open/close tests | `plan-03-drawer-tests.log` | Drawer unreliable. | Yes | NOT DEPENDENT ON SOAK |
| Settings drawer focus checks | 3.6.1 / 7.7.1 | Keyboard/focus smoke: Tab, Shift+Tab, Escape, restore focus | `drawer-focus-proof.md` | WAI-ARIA drawer baseline failed. | Yes | NOT DEPENDENT ON SOAK |
| Design packet read-only checks | 3.5.1 | Assert no apply control and read-only labels | `design-packet-read-only-proof.log` | Design apply authority leaked. | Yes | NOT DEPENDENT ON SOAK |
| Provider truth checks | 7.2.2 | Render local/cloud/codex/unavailable truth without calls | `provider-truth-proof.log` | Truth display faked or calls provider. | Yes | NOT DEPENDENT ON SOAK |
| No-apply/no-execute-approved | 3.9.1 | Static/test assertion no enabled `execute-approved` path | `no-apply-proof.md` | Apply path exposed. | Yes | SAFE WHILE SOAK RUNS |
| No-provider-call | 3.9.2 / 7.6.2 | Mock/static assertion no provider/model calls | `no-provider-proof.md` | Network/provider side effect. | Yes | NOT DEPENDENT ON SOAK |
| No-hidden-worker | 8.6 | Static/test/manual assertion no worker dispatch | `no-hidden-worker-proof.md` | Background work possible. | Yes | SAFE WHILE SOAK RUNS |
| No-queue-mutation | 8.6 | Static/test/manual assertion no queue advancement | `no-queue-mutation-proof.md` | Hidden task advancement possible. | Yes | SAFE WHILE SOAK RUNS |
| Targeted Python pytest Source Proxy safety | 3.4.1 | `pytest <selected non-mutating source_proxy/tests>` | `source-proxy-safety-pytest.log` | Backend safety regression or unsafe test selection. | Yes | SAFE WHILE SOAK RUNS |
| No-Cartographer-soak-mutation | 3.10.1 / 8.6.4 / 8.6.6 | Read-only status/diff/protected path review | `no-cartographer-mutation-proof.md` | Soak/evidence/runtime touched. | Yes | SAFE WHILE SOAK RUNS |
| Manual `/coding` browser checklist | 3.8.1 | Desktop route checklist | `coding-desktop-checklist.md` | Operator workflow unclear/broken. | Yes | SAFE WHILE SOAK RUNS |
| Active task transcript behavior | 4.7.1 | Timeline state tests/manual | `active-task-transcript-proof.log` | Active task operating model broken. | Yes | SAFE WHILE SOAK RUNS |
| Composer blocked-state checks | 4.2.1 / 8.2.1 | Type into composer; confirm no send/provider/queue | `composer-blocked-proof.md` | Composer executes. | Yes | NOT DEPENDENT ON SOAK |
| Chat/media lane checks | 5.7.1 | Targeted lane render/no-storage/no-provider tests | `chat-media-lane-proof.log` | Storage/provider mutation risk. | Yes | NOT DEPENDENT ON SOAK |
| Projects read-only checks | 6.7.1 | Selector/health/ownership tests with fixtures | `projects-read-only-proof.log` | Project UI requires live mutation. | Yes | SAFE WHILE SOAK RUNS unless live integration attempted |
| Settings truth display checks | 7.8.1 | Settings render/no-persist/no-provider tests | `settings-truth-proof.log` | Config/env/provider mutation risk. | Yes | NOT DEPENDENT ON SOAK |
| Responsive checks | 3.8.2 / 12.9 / 13.9 | Manual mobile/tablet/desktop viewport checks | `responsive-proof.md` | Overlap/unusable layout. | Yes | SAFE WHILE SOAK RUNS for non-map |
| Accessibility checks | 3.6.1 / 13.8 | Keyboard/focus/labels/contrast checklist | `accessibility-proof.md` | Inaccessible drawers/controls. | Yes | NOT DEPENDENT ON SOAK |
| Final route visual checks | 13.10 | Screenshot/manual checklist per route | `final-visual-proof-package` | Polish not proven. | Yes | PARTIAL; Cartographer live surfaces post-soak |

## 24. Acceptance Rubric

A-grade acceptance requires:

- Coding and design foundation communicate through explicit contracts.
- Design packets are read-only unless a future approved apply lane exists.
- Source Proxy remains owner of Draft -> Preview -> Approval -> Apply -> Verify.
- `/coding` remains the everyday command center.
- `/proxy-backend` remains deep diagnostics.
- Settings, diagnostics, evidence, and design intake are drawer/secondary surfaces.
- Codex-like active task UI is clear, compact, and operator-first.
- Multimedia chat lanes integrate without cross-lane mutation.
- Projects interface is read-only until explicitly approved otherwise.
- Settings window does not mutate env/config/auth.
- Cartographer integration is prepared without disturbing the 24-hour soak.
- Full Cartographer integration waits only at the true soak-result gate.
- Safe work continues while soak runs.
- CSS polish is last.
- Tests and manual validation produce evidence.
- Every increment remains isolated in the proxy lane.
- Main repo and ongoing Cartographer soak state remain untouched.

## 25. Global Stop Conditions

Stop immediately if:

- Isolated lane is ambiguous.
- Main repo mutation is detected.
- Cartographer soak state changes.
- Cartographer soak logs are written.
- Cartographer live evidence is written.
- Dirty tree is cleaned or normalized.
- Unapproved provider/model call occurs.
- Apply or execute-approved appears.
- Branch/worktree/stash/reset/clean/checkout is attempted without explicit approval.
- Hidden worker or queue appears.
- Design packet gains apply authority.
- Tests fail and cannot be repaired inside the allowed isolated lane.
- CSS polish starts before foundation gates pass.
- Cartographer integration starts before soak-result gate permits it.
- Route ownership is unclear.
- Evidence cannot prove what happened and what did not happen.

## 26. Required Final Sections

### A. Next Authorized Action Only

Plan 0, Phase 0.1, Increment 0.1.1: Isolated Proxy Lane Identity And Boundary Packet.

### B. First Increment To Run

Increment 0.1.1 names the isolated proxy lane and evidence root. It records the rule that every future implementation, test, validation, proof, browser check, and closeout must occur only inside the isolated proxy lane unless the operator later authorizes one exact increment. It does not implement code. It does not touch production routes, components, backend files, Source Proxy runtime, Cartographer runtime, map state, provider/model calls, apply, execute-approved, queues, workers, or git state.

### C. Files Allowed For First Increment

Docs/evidence-only or lane metadata only.

No production route/component/backend files.

Allowed zone, if operator confirms creation/use:

- `/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/`

### D. Forbidden Actions For First Increment

- Do not edit production files.
- Do not edit Source Proxy runtime files.
- Do not edit Cartographer runtime files.
- Do not write Cartographer soak logs.
- Do not write Scout soak logs.
- Do not write Cartographer live evidence.
- Do not mutate production map state.
- Do not mutate production Source Proxy state.
- Do not run provider/model calls.
- Do not call apply.
- Do not call execute-approved.
- Do not create hidden workers.
- Do not mutate queues.
- Do not clean, stash, reset, checkout, stage, commit, push, branch, or create a worktree.
- Do not run tests that mutate shared soak state.
- Do not claim Cartographer integration readiness.
- Do not start Plan 1.

### E. Manual Verification Block

Before allowing Increment 0.1.2, the operator manually verifies:

- The lane name is explicit.
- The evidence root is explicit and does not overlap runtime state.
- The main repo path is recorded.
- Cartographer soak protection is stated.
- No production file edits occurred.
- No git mutation occurred.
- No Cartographer soak/log/live evidence/runtime/map state was touched.
- The next authorized increment is exactly Plan 0, Phase 0.1, Increment 0.1.2.

### F. GO/NO-GO Decision Template

```text
Increment:
Evidence reviewed:
Main repo untouched: Yes/No
Cartographer soak untouched: Yes/No
Tests passed: Yes/No
Manual validation accepted: Yes/No
Known risks:
Decision: GO / NO-GO / NEEDS OPERATOR REVIEW
Next authorized increment:
```

### G. New Chat Handoff Prompt

```text
You are Codex inside the Spirit OS repository.

MISSION:
Continue the Spirit OS Unified Proxy Coding + Design System Master Plan of Plans v0.1 in strict PIVOT workflow.

Source-of-truth plan file:
/home/source/SpiritOS/docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md

Current authorized position:
Plan 0
Phase 0.1
Increment 0.1.1: Isolated Proxy Lane Identity And Boundary Packet

Latest GO/NO-GO status:
NOT STARTED. Needs Increment 0.1.1 execution.

ABSOLUTE ISOLATION RULE:
All future implementation, testing, validation, proof, experiments, file edits, browser checks, and closeout evidence must occur only in an isolated proxy lane unless a later operator instruction approves one exact increment.

Do not touch the main repository execution path.
Do not mutate unrelated dirty files.
Do not clean, stash, reset, checkout, stage, commit, push, branch, or create a worktree.
Do not disturb the ongoing 24-hour Cartographer soak test.
Do not write to Cartographer soak logs.
Do not write to Scout soak logs.
Do not write to Cartographer runtime state.
Do not write to Cartographer live evidence.
Do not mutate production map state.
Do not mutate production Source Proxy state.
Do not run tests that mutate shared soak state.
Do not claim stability from tests that did not run inside the isolated proxy lane.
Do not claim Cartographer integration readiness until isolated-lane proof exists and the 24-hour soak result is available where required.
Do not wait on Cartographer soak for safe proxy/design/Codex-like work that is independent of Cartographer.
Do not call providers.
Do not call apply.
Do not call execute-approved.
Do not create hidden workers or mutate queues.
Do not self-approve future phases/plans.

Allowed files for first increment:
Docs/evidence-only or lane metadata only.
No production route/component/backend files.

Proposed evidence root:
/home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/

Forbidden actions for first increment:
Production edits, Cartographer/Scout soak or live evidence writes, runtime/map/Source Proxy production mutation, provider/model calls, apply, execute-approved, hidden workers, queue mutation, branch/worktree/stash/reset/clean/checkout/stage/commit/push.

Workflow:
Use PIVOT for every increment:
PLAN -> PHASE -> INCREMENT -> CHECKS -> STOP CONDITIONS -> CLOSEOUT GATE -> NEXT AUTHORIZED INCREMENT.

For every increment include:
1. Increment title.
2. Objective.
3. Isolated proxy lane scope.
4. Allowed files or file zones.
5. Forbidden files, paths, systems, and actions.
6. Exact work to perform.
7. Required tests.
8. Required manual validation.
9. Required evidence artifact.
10. Stop conditions.
11. Rollback or recovery note.
12. GO/NO-GO exit rule.
13. Next authorized increment only.
14. Cartographer soak dependency status.

Do the current increment only.
Run its checks yourself.
Record evidence.
Give GO / NO-GO / NEEDS OPERATOR REVIEW.
Name exactly one next authorized increment.

At the end of each phase:
Manually review all increments completed in that phase before moving to the next phase.

At the end of each plan:
Give the operator one singular copy-paste terminal block to verify the work before moving to the next plan.
Then give one singular copy-paste new-chat handoff prompt for the next plan in the same workflow.

Begin only:
Plan 0, Phase 0.1, Increment 0.1.1.
```
