# Source Proxy Agent Integration Preflight Build Roadmap v0.1

## Status

Status: active build-first roadmap.

Owner: Britton.

Created: 2026-05-27.

Target: Preflight Final CSS Stage, not production launch.

Authority: roadmap and sequencing only. This document does not start Plan 0, continue Plan 23, start a soak, re-soak, activate Cartographer, run workers, call providers or models, apply changes, commit, push, or mutate source/runtime/CSS files.

## Supersession Notice

This roadmap supersedes the failed docs-heavy 24-plan chain and the active direction in `docs/masterKeyProxyProduction.md`.

The old chain remains historical evidence until Plan 0 classifies each candidate for keep, archive, or delete. Existing docs are not deleted by this roadmap. Future Codex chats must treat this file as the active source of truth for Source Proxy agent integration through Preflight Final CSS Stage.

Active roadmap:
- `docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md`

Fresh-chat handoff:
- `docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md`

## Why The Prior Roadmap Is Superseded

The prior chain preserved safety discipline, but it did not build the daily-driver proxy needed for final CSS. The current evidence shows:

- The current chain contains many docs-only or gate-only plans. It records boundaries, packets, contracts, readiness gates, and NO-GO decisions more often than shipped proxy behavior.
- Plan 18/24 was preview-only multi-agent/subagent orchestration. It did not enable workers, runtime dispatch, write authority, or real subagent output inside the proxy.
- Plan 19/24 was authority/token design. It did not enable token consumption, approved writes, execution, apply, commit, push, workers, queues, or provider/model calls.
- Plan 20/24 visual proof was a contract and readiness inventory only. It did not capture screenshot proof.
- Plan 21/24 final CSS polish gate did not approve CSS mutation, did not run screenshots, and did not perform CSS polish.
- Run 300 evidence shows strong safety discipline but usefulness NO-GO: 0 productive previews and 0 productive preview diffs. Safety without useful bounded output is not enough for the proxy to improve coding and design.
- Plan 22/24 records production readiness NO-GO.
- Plan 23/24 soak is not authorized here and should not be run from the recent chain because the recent chain did not make meaningful implementation changes that justify a soak.
- Cartographer is not daily-driver auto yet. For this roadmap, Cart must become visible inside the proxy as read-only/control-preview before final CSS. Full Cart limited daily-driver auto is deferred to the next roadmap unless Britton explicitly reorders it.

The correction is to build the actual proxy cockpit and its bounded preview, task, design, research, subagent, Cart visibility, controlled apply, diagnostic, and screenshot proof loops before final CSS polish.

## Correct PIVOT Workflow Contract

Britton's PIVOT workflow means:

1. One Codex chat works on one whole plan at a time.
2. A plan contains phases.
3. Each phase contains increments.
4. Codex works increment by increment inside the same plan.
5. After each increment, Codex must make the scoped change, run that increment's terminal/manual checks by itself, inspect the output, fix safe failures inside scope, record GO / NO-GO for that increment, and continue to the next increment automatically if GO.
6. At the end of each phase, before moving to the next phase, Codex must run a terminal/manual check covering all increments completed in that phase.
7. At the end of the whole plan, Codex must give Britton one copy-paste terminal block to verify all phases and increments completed in that plan.
8. Codex must not stop after one increment unless a stop condition triggers.
9. Codex must not interpret PIVOT as "do one increment only and stop."
10. Codex must not ask Britton for permission between every increment unless the plan requires human approval, the next action can mutate outside the approved scope, repo state is unsafe, expected proof cannot be produced honestly, or a command may affect runtime/Cart/workers/git state beyond allowed scope.

Every implementation plan created from this roadmap must include:
- Exact allowed files and forbidden files.
- What will change.
- What terminal/manual checks Codex must self-run after each increment.
- What phase-level check proves the phase.
- What stop conditions block continuation.
- A final full-plan terminal verification block.
- Explicit authority distinctions for preview, approval, apply, commit, push, and auto.

## Implementation Plan Standard And Docs Limit

Each plan must be build-first and evidence-light. It should define the smallest useful implementation surface, exact files allowed for that plan, exact files forbidden for that plan, and scoped checks that prove behavior honestly. Planning text must support execution; it must not become the deliverable when the plan is meant to build.

Implementation plans must avoid giant audit packets, broad evidence dumps, and repeated contract-only closeouts. A plan may create a short closeout or classification file when that file is needed to preserve the result of the work, but it must not create packet chains as a substitute for code, terminal proof, manual proof, screenshots, or explicit GO / NO-GO decisions.

No-packet rule:
- Do not create large packet sets, prompt banks, readiness bundles, or evidence packages unless a later plan explicitly requires them.
- Do not treat a packet, contract, or checklist as implementation proof.
- Do not continue producing docs after a phase has enough evidence to move to the next increment.
- Preserve only the decisions, candidate lists, checks, and proof needed for the next plan to run safely.
- If a future plan needs a document, keep it narrow, named to the plan, and tied to an increment or phase check.

## Preflight Final CSS Stage Definition

SpiritOS reaches Preflight Final CSS Stage when the proxy is useful enough to safely perform final design polish through its own coding/design workflow.

Required before final CSS:
- Productive bounded coding preview exists.
- `/coding` cockpit is Codex-like enough to drive tasks.
- Progress/output lanes exist.
- Task lifecycle and blockers are visible.
- Design packets are integrated.
- Subagent outputs are visible.
- Mac Mini/search/Scout research lane works in advisory mode.
- Cartographer is visible inside the proxy as read-only/control-preview.
- Human-controlled apply path exists or is explicitly gated.
- Combined coding/design/research/Cart diagnostic gauntlet passes.
- Visual proof harness captures before screenshots.
- CSS allowed files are route-scoped and evidence-based.

Not required before final CSS:
- Full unattended Cart daily-driver auto.
- Auto-push.
- Hidden workers.
- Broad mutation.
- Production deployment.

## System Architecture Target

The target architecture is a Source Proxy cockpit that makes work visible before it makes work powerful.

Core surfaces:
- `/coding` as the main command cockpit with task composer, lifecycle, progress, terminal/check output, active/blocked/completed lanes, blockers, and exact proposed diffs.
- Source Proxy backend preview route that can produce a bounded, protected-path-checked proposed diff without apply.
- Design Agent/Design Vault lane for design packets, design-to-code mapping, accepted/rejected packet state, and route/component/CSS file targeting.
- Research lane for web search, Mac Mini advisory search, Scout packets, source citations, and accepted research-to-coding handoff.
- Subagent lane for visible helper roles, read-only/advisory outputs, disagreements, and authority state.
- Cartographer lane for read-only status, evidence/receipt browsing, route protection, action catalog, and preview-only control plans.
- Human-controlled apply lane for exact approval records, diff hash/scope matching, approved apply only, focused checks, and local audit evidence.
- Visual proof harness for screenshots, responsive proof, visual blockers, route-scoped CSS files, and before/after evidence.

Authority model:
- Preview shows proposed work and proposed diffs without mutation.
- Approval records human intent for one exact scope.
- Apply mutates only exact approved files and only after approval gates pass.
- Commit remains separate from apply and is not part of this preflight roadmap.
- Push remains separate from commit and is not part of this preflight roadmap.
- Auto remains disabled except where a later explicitly approved roadmap reopens it.

## Hard Rules And Stop Conditions

Hard rules:
- Do not start or continue Plan 23 from the failed chain.
- Do not start or schedule a soak from the failed chain.
- Do not re-soak unless a later plan made meaningful behavior changes and Plan 12 decides a soak is justified.
- Do not run Cartographer activation from this roadmap.
- Do not run hidden workers.
- Do not run provider/model calls unless a future plan explicitly approves an advisory provider lane and records the exact command and stop rules.
- Do not edit source, tests, runtime, CSS, package, config, env, Cartographer runtime/evidence/receipt, or app route files until the specific plan authorizes those files.
- Do not claim readiness from contracts.
- Do not fake productive previews.
- Do not fake screenshots.
- Do not fake CSS readiness.
- Do not fake Cart daily-driver status.

Stop conditions for every plan:
- Dirty tree or untracked files affect the plan's allowed files and cannot be classified safely.
- The next increment requires files outside the approved scope.
- A terminal/manual check cannot be run or interpreted honestly.
- A command may mutate runtime, Cartographer, workers, queues, provider/model state, approval tokens, git state, or files outside approved scope.
- A protected path would be touched without exact approval.
- The plan requires human approval before mutation and approval is missing.
- Preview, approval, apply, commit, push, and auto boundaries become ambiguous.

## Full Plan List With Phases And Increments

### Plan 0: Roadmap Reset And Active Plan Cleanup

Purpose: Supersede failed 24-plan chain, stop Plan 23/soak, install correct PIVOT, classify old docs for archive/delete, and create clean active source of truth.

Changes: Docs-only cleanup and active pointer changes in approved roadmap/index docs.

Verifies: Old roadmap is frozen, Plan 23/soak is not authorized, PIVOT contract is installed, archive/delete candidates are classified, and active source of truth points to this roadmap.

Stops: Any request to delete evidence without classification, mutate source/runtime/CSS/Cart/worker/provider/git state, continue Plan 23, start Plan 1, or run soak/Cart/workers.

Authority: Preview and docs cleanup only. No apply lane, commit, push, or auto.

Phase 0.1: Old roadmap freeze
- Increment 0.1.1: Confirm Plan 23 and soak are not authorized.
- Increment 0.1.2: Locate active failed roadmap docs.
- Increment 0.1.3: Classify keep/archive/delete candidates.

Phase 0.2: PIVOT contract installation
- Increment 0.2.1: Add correct PIVOT workflow contract.
- Increment 0.2.2: Define implementation-plan standard.
- Increment 0.2.3: Define docs limit and no-packet rule.

Phase 0.3: Active roadmap switch
- Increment 0.3.1: Supersede old active roadmap pointers.
- Increment 0.3.2: Verify new roadmap is active source of truth.
- Increment 0.3.3: Produce Britton final Plan 0 terminal check block.

Initial old-roadmap docs to classify in Plan 0 before archive/delete:
- `docs/masterKeyProxyProduction.md`
- `docs/cartographer-live-evidence/cartographer-plan-1-24-post-soak-acceptance-promotion-audit-v0.1.md`
- `docs/cartographer-live-evidence/cartographer-plan-7-24-activation-boundary-resoak-decision-v0.1.md`
- `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md`
- `docs/mac-mini-workload-placement-matrix-plan-3-24-v0.1.md`
- `docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md`
- `docs/mac-mini-subagent-host-feasibility-plan-5-24-v0.1.md`
- `docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md`
- `docs/source-proxy-pr-8-3-acceptance-or-nonblocking-decision-plan-8-24-v0.1.md`
- `docs/source-proxy-run-300-blocker-reduction-plan-9-24-v0.1.md`
- `docs/source-proxy-coding-active-task-cockpit-operator-clarity-plan-10-24-v0.1.md`
- `docs/source-proxy-production-hardening-consolidation-plan-11-24-v0.1.md`
- `docs/design-agent-a-grade-dependency-unlock-plan-12-24-v0.1.md`
- `docs/design-agent-ecosystem-remediation-plan-13-24-v0.1.md`
- `docs/design-subagent-fleet-preintegration-plan-14-24-v0.1.md`
- `docs/scout-manual-controlled-intelligence-lane-plan-15-24-v0.1.md`
- `docs/surface-ownership-chat-oracle-dashboard-plan-16-24-v0.1.md`
- `docs/map-cartographer-ui-integration-gate-plan-17-24-v0.1.md`
- `docs/controlled-multi-agent-subagent-orchestration-boundary-plan-18-24-v0.1.md`
- `docs/controlled-action-authority-approval-token-ladder-plan-19-24-v0.1.md`
- `docs/visual-evidence-browser-proof-harness-plan-20-24-v0.1.md`
- `docs/final-css-polish-gate-plan-21-24-v0.1.md`
- `docs/preflight-production-readiness-review-plan-22-24-v0.1.md`

### Plan 1: Executable Baseline And Scope Lock

Purpose: Establish actual repo/runtime/proxy/Mac/Scout/Cart/design state without producing a giant packet.

Changes: Small baseline docs and exact implementation scope map only unless Britton approves source/test inspection output files.

Verifies: Real current routes, backend preview surfaces, `/coding` components, design docs/code, Scout/search/Mac state, Cart read-only/control boundaries, and first allowed implementation files.

Stops: Broad audit packet drift, source mutation, runtime start, Cart activation, workers, provider/model calls, or unclear first implementation scope.

Authority: Observe/recommend only. No preview route mutation yet, no approval, no apply, no commit, no push, no auto.

Phase 1.1: Repo and service baseline
- Increment 1.1.1: Git and dirty-tree baseline.
- Increment 1.1.2: Source Proxy route and test baseline.
- Increment 1.1.3: `/coding` UI and component baseline.

Phase 1.2: Agent surface baseline
- Increment 1.2.1: Design Agent and design docs/code baseline.
- Increment 1.2.2: Scout/search/Mac Mini baseline.
- Increment 1.2.3: Cartographer read-only/control baseline.

Phase 1.3: Build priority map
- Increment 1.3.1: Identify real implementation blockers.
- Increment 1.3.2: Identify exact allowed first source/test files.
- Increment 1.3.3: Final executable baseline check.

### Plan 2: Source Proxy Productive Bounded-Diff Preview

Purpose: Fix the major usefulness blocker: 0 productive previews and 0 productive preview diffs.

Changes: Backend/UI/test implementation for preview-only bounded diffs.

Verifies: One tiny real proposed diff is produced without apply, protected paths reject, failure reason codes are covered, and `/coding` can show preview ready/blocked/approved/applied states honestly.

Stops: Any apply behavior, provider/model calls, source writes outside allowed files, protected path bypass, fake no-op/productive proof, or hidden worker/queue behavior.

Authority: Preview only. Approval is displayed as state only if implemented without granting apply. No apply, commit, push, or auto.

Phase 2.1: Backend preview route
- Increment 2.1.1: Add or repair preview-only bounded diff route.
- Increment 2.1.2: Wire verifier and protected-path rejection.
- Increment 2.1.3: Produce one tiny real proposed diff without apply.

Phase 2.2: Tests and failure modes
- Increment 2.2.1: Add valid preview tests.
- Increment 2.2.2: Add unsafe/protected/no-diff rejection tests.
- Increment 2.2.3: Add reason-code coverage.

Phase 2.3: UI consumption
- Increment 2.3.1: Show proposed diff in `/coding`.
- Increment 2.3.2: Show preview ready vs blocked vs approved vs applied.
- Increment 2.3.3: Plan 2 final verification.

### Plan 3: Codex-Like Coding Cockpit

Purpose: Make `/coding` function like a real coding command center before design polish.

Changes: `/coding` task composer, lifecycle, details, progress, output, blocker, and work-lane UI.

Verifies: Users can compose tasks with allowed/forbidden files, inspect lifecycle and checks, see active/blocked/completed work, and understand authority limits without hidden actions.

Stops: Provider/model calls, shell execution, apply, commit, push, hidden workers, broad route rewrites, or UI that hides blockers.

Authority: Preview/display cockpit only. Approval/apply/commit/push/auto remain unavailable unless explicitly displayed as blocked.

Phase 3.1: Task composer and lifecycle
- Increment 3.1.1: Task composer with allowed/forbidden files.
- Increment 3.1.2: Lifecycle states.
- Increment 3.1.3: Task details drawer.

Phase 3.2: Progress and output
- Increment 3.2.1: Step timeline.
- Increment 3.2.2: Terminal/check output panel.
- Increment 3.2.3: Authority and blocker banner.

Phase 3.3: Work lanes
- Increment 3.3.1: Active lane.
- Increment 3.3.2: Blocked lane.
- Increment 3.3.3: Completed lane.

### Plan 4: Mac Mini, Web Search, And Scout Research Lane

Purpose: Make web search, Mac support node, and Scout packets useful inside the proxy.

Changes: Advisory research packet shape, task attachment, research lane UI, Mac node status, Mac-backed search adapter if approved, and Scout packet display/import preview.

Verifies: Search/Scout context can be attached to coding tasks without writes, Mac node health is honest, search capability is either working or blocked visibly, and accepted research can become coding context.

Stops: Autonomous Scout discovery, hidden scheduled search, provider/model calls not authorized by the plan, Mac service control, repo writes from Mac, Cart mutation, or search results without sources.

Authority: Advisory only. Research can inform preview. No approval, apply, commit, push, or auto.

Phase 4.1: Search packet route
- Increment 4.1.1: Normalize research/search packet format.
- Increment 4.1.2: Attach research packet to coding task.
- Increment 4.1.3: Add research lane UI.

Phase 4.2: Mac Mini support node
- Increment 4.2.1: Show Mac node health/stale/offline state.
- Increment 4.2.2: Verify SearXNG JSON/search capability or show blocker.
- Increment 4.2.3: Add Mac-backed search adapter in advisory mode.

Phase 4.3: Scout bridge
- Increment 4.3.1: Show Scout packets/sources in proxy.
- Increment 4.3.2: Manual import/promotion preview only.
- Increment 4.3.3: Accepted research-to-coding handoff.

### Plan 5: Subagent Integration v1

Purpose: Add visible helper agents without hidden write authority.

Changes: Helper role registry, authority levels, roster UI, subagent run/result packets, timeline integration, conflict/disagreement display.

Verifies: Multiple helper outputs are visible and read-only/advisory, conflicts are explicit, and no helper can write or dispatch work secretly.

Stops: Hidden worker start, dispatch, lease/lock creation, branch/worktree creation, write authority, provider/model call without explicit plan authority, or unresolved ownership conflicts.

Authority: Advisory subagent output only. No approval, apply, commit, push, or auto.

Phase 5.1: Agent registry
- Increment 5.1.1: Define helper roles.
- Increment 5.1.2: Add registry schema and authority levels.
- Increment 5.1.3: Show agent roster in `/coding`.

Phase 5.2: Subagent run records
- Increment 5.2.1: Subagent task packet.
- Increment 5.2.2: Subagent result packet.
- Increment 5.2.3: Timeline integration.

Phase 5.3: Parallel advisory only
- Increment 5.3.1: Run multiple read-only helper outputs.
- Increment 5.3.2: Show conflicts and disagreements.
- Increment 5.3.3: Verify no write authority.

### Plan 6: Design Agent And Design Vault Integration

Purpose: Make design agents useful inside Source Proxy before final CSS.

Changes: Design packet schema/display, accept/reject state, route/component/CSS map, design-to-code draft creation, quality bar, and drift map.

Verifies: Design packets become visible, actionable, accepted/rejected, and convertible into bounded coding task drafts tied to exact files.

Stops: CSS mutation, component edits, route edits, fake A-grade claims, design packet acceptance as apply authority, or missing route/file mapping.

Authority: Design recommend/preview only. Accepted packet may draft a coding task; it does not approve, apply, commit, push, or auto-run.

Phase 6.1: Design packet intake
- Increment 6.1.1: Design packet schema.
- Increment 6.1.2: Design packet display.
- Increment 6.1.3: Accept/reject design packets.

Phase 6.2: Design-to-code bridge
- Increment 6.2.1: Route/component/CSS map.
- Increment 6.2.2: Design recommendation to exact files.
- Increment 6.2.3: Convert accepted packet to bounded coding task draft.

Phase 6.3: Design quality bar
- Increment 6.3.1: Define AAA/Codex-like application standard.
- Increment 6.3.2: Token/component drift map.
- Increment 6.3.3: Design readiness check.

### Plan 7: Cartographer Proxy Visibility And Controlled Preview

Purpose: Bring Cart into the proxy safely instead of excluding it forever.

Changes: Read-only Cart status/evidence/route-protection display, action catalog, preview-only queue/workflow/token action plans, rejection proof, and Cart lane in the proxy cockpit.

Verifies: Cart status is visible without activation, blocked actions reject with proof, Cart dependencies appear on tasks, and readiness includes Cart preflight state.

Stops: Cart activation, live map mutation, runtime start, queue/worker execution, token consumption, evidence/receipt writes unless exactly approved, or treating preview as daily-driver auto.

Authority: Cart read-only/control-preview only. No approval-token consumption, apply, commit, push, or auto.

Phase 7.1: Read-only Cart lane
- Increment 7.1.1: Cart status card.
- Increment 7.1.2: Cart evidence/receipt browser.
- Increment 7.1.3: Cart route protection display.

Phase 7.2: Cart action preview
- Increment 7.2.1: Cart action catalog.
- Increment 7.2.2: Queue/workflow/token preview-only actions.
- Increment 7.2.3: Rejection proof for blocked actions.

Phase 7.3: Unified proxy cockpit
- Increment 7.3.1: Cart lane inside `/coding` or proxy cockpit.
- Increment 7.3.2: Cart dependency blockers on tasks.
- Increment 7.3.3: Cart preflight status included in readiness.

### Plan 8: Human-Controlled Apply Lane

Purpose: Move from preview-only to exact approved apply with no commit or push.

Changes: Approval record, diff hash/scope matching, approval UI, exact approved diff apply, post-apply checks, rollback preview, apply result card, and audit log.

Verifies: One tiny safe task proves preview to approval to apply to verify, without commit or push.

Stops: Missing approval ID/token, hash mismatch, scope mismatch, dirty-tree conflict, protected path match, apply outside exact diff, failed focused checks, rollback ambiguity, commit, push, or auto-continuation.

Authority: Human approval plus exact apply only. Commit and push are explicitly out of scope. Auto remains disabled.

Phase 8.1: Approval record
- Increment 8.1.1: Approval ID/token record.
- Increment 8.1.2: Diff hash and scope matching.
- Increment 8.1.3: Approval UI.

Phase 8.2: Exact apply
- Increment 8.2.1: Apply exact approved diff only.
- Increment 8.2.2: Post-apply focused checks.
- Increment 8.2.3: Rollback preview.

Phase 8.3: Apply evidence
- Increment 8.3.1: Apply result card.
- Increment 8.3.2: Local audit log.
- Increment 8.3.3: One tiny safe task proves preview to approval to apply to verify.

### Plan 9: Combined Coding, Design, Research, And Cart Diagnostic Gauntlet

Purpose: Prove the system can actually code and coordinate before final CSS.

Changes: Diagnostic tasks and gauntlet receipts for coding, UI, backend/schema, design, research, and safety paths.

Verifies: Real bounded tasks work across coding/design/research/Cart context, protected paths reject, bad diffs reject, and hidden authority remains absent.

Stops: Fake productive output, broad mutation, provider/model calls not authorized, Cart activation, apply beyond approved exact scope, commit, push, hidden workers, or unreviewed failed checks.

Authority: Preview and exact approved apply only where Plan 8 permits it. No commit, push, or auto.

Phase 9.1: Real coding tasks
- Increment 9.1.1: Tiny docs/code task.
- Increment 9.1.2: UI task.
- Increment 9.1.3: Backend route/schema task.

Phase 9.2: Design and research tasks
- Increment 9.2.1: Design packet intake.
- Increment 9.2.2: Design-to-code task.
- Increment 9.2.3: Search/Scout packet to coding context.

Phase 9.3: Safety tasks
- Increment 9.3.1: Protected path rejection.
- Increment 9.3.2: Bad diff rejection.
- Increment 9.3.3: Hidden authority check.

### Plan 10: Visual Proof Harness

Purpose: Capture screenshots and proof before CSS.

Changes: Screenshot capability if approved, screenshot artifact path, no-provider fixtures, route screenshot runs, blocker list, and CSS route mapping.

Verifies: Before screenshots exist for `/coding`, `/chat`, `/oracle`, dashboard, intelligence/design/search/Cart cockpit surfaces; visual blockers and allowed CSS files are route-scoped.

Stops: Runtime/browser tool not approved, screenshots not captured, blank screens, overlap/overflow, missing fixtures, provider/model calls, Cart activation, or unscoped CSS files.

Authority: Visual proof only. No CSS polish, apply, commit, push, or auto.

Phase 10.1: Screenshot tooling readiness
- Increment 10.1.1: Verify or add Playwright/screenshot capability with approval.
- Increment 10.1.2: Add screenshot artifact path.
- Increment 10.1.3: Add stable no-provider fixtures.

Phase 10.2: Route screenshots
- Increment 10.2.1: `/coding` screenshots.
- Increment 10.2.2: `/chat`, `/oracle`, dashboard screenshots.
- Increment 10.2.3: Intelligence/design/search/Cart cockpit screenshots.

Phase 10.3: Visual readiness
- Increment 10.3.1: Visual blocker list.
- Increment 10.3.2: CSS allowed files and route mapping.
- Increment 10.3.3: Final pre-CSS GO / NO-GO.

### Plan 11: Final CSS Polish Using The Proxy

Purpose: Use the now-functional proxy to make the UI look like a polished Codex-like AAA application.

Changes: Route-scoped CSS and UI polish driven by proxy workflow and visual proof.

Verifies: After screenshots, before/after comparison, responsive state, interaction state, and final CSS closeout.

Stops: Missing before screenshots, missing route/file scope, broad CSS sweep, source/runtime/Cart/provider mutation, unapproved global tokens, failed visual checks, commit, push, or auto.

Authority: Exact route-scoped CSS/UI mutation only after Plan 10 GO and approval. Apply may use Plan 8 lane. Commit/push/auto remain out of scope.

Phase 11.1: `/coding` first
- Increment 11.1.1: First viewport polish.
- Increment 11.1.2: Interaction states.
- Increment 11.1.3: Responsive polish.

Phase 11.2: Supporting surfaces
- Increment 11.2.1: `/intelligence` and Scout/search surfaces.
- Increment 11.2.2: `/chat` and `/oracle`.
- Increment 11.2.3: Dashboard and Cart/Mac/search status.

Phase 11.3: Final visual proof
- Increment 11.3.1: After screenshots.
- Increment 11.3.2: Before/after comparison.
- Increment 11.3.3: Final CSS closeout.

### Plan 12: Preflight Review And Soak Decision

Purpose: Decide whether a soak is justified only after real implementation changed behavior.

Changes: Readiness review and next-roadmap decision only.

Verifies: Source Proxy/coding, design/subagent/research, Cart visibility/control-preview, screenshots, responsive/accessibility proof, final CSS proof, and whether runtime/worker/queue/model/search/apply changes justify soak.

Stops: Calling production ready without proof, starting soak automatically, Cart activation, hidden worker/queue/model behavior, commit, push, or starting the next roadmap without Britton approval.

Authority: Review and decision only. No new preview/apply/commit/push/auto authority.

Phase 12.1: Functional readiness review
- Increment 12.1.1: Source Proxy/coding readiness.
- Increment 12.1.2: Design/subagent/research readiness.
- Increment 12.1.3: Cart visibility/control-preview readiness.

Phase 12.2: Visual readiness review
- Increment 12.2.1: Screenshot proof.
- Increment 12.2.2: Responsive/accessibility proof.
- Increment 12.2.3: Final CSS proof.

Phase 12.3: Soak decision
- Increment 12.3.1: Identify runtime/worker/queue/model/search/apply changes.
- Increment 12.3.2: Decide if soak is required.
- Increment 12.3.3: Produce next roadmap title.

## Cart Daily-Driver Auto Deferral Note

Cartographer is not daily-driver auto in this roadmap. Plan 7 integrates Cart visibility and controlled preview so the proxy can see Cart status, blockers, route protections, evidence, receipts, and preview-only action catalogs before final CSS.

Full Cart daily-driver auto is deferred until after this preflight foundation unless Britton explicitly reorders the work.

Post-preflight roadmap title:

`Cartographer Limited Daily-Driver Auto v1`

That later roadmap should target:
- Durable safe task queue.
- One controlled worker.
- Scoped approval token consumption.
- Safe write.
- Kill switch.
- No hidden continuation.
- One approved low-risk task loop.
- Then soak and promotion decision.

## Final CSS Gate Conditions

Final CSS cannot begin until all of these are true:

- Plan 2 produces at least one honest productive bounded preview diff and rejection proof.
- Plan 3 makes `/coding` usable as a Codex-like task cockpit.
- Plan 4 proves advisory research/search/Scout lane behavior.
- Plan 5 shows helper/subagent outputs without write authority.
- Plan 6 integrates design packets into bounded coding task drafts.
- Plan 7 shows Cart read-only/control-preview inside the proxy and proves blocked actions reject.
- Plan 8 either provides a human-controlled apply path or records an explicit gate keeping apply disabled.
- Plan 9 combined gauntlet passes for coding, design, research, and Cart safety.
- Plan 10 captures before screenshots and records CSS allowed files by route.
- CSS work is route-scoped, evidence-based, and approved.
- Preview, approval, apply, commit, push, and auto boundaries remain explicit.

No contract, packet, gate, or readiness statement can substitute for these proofs.

## New-Chat Handoff Reference

Use this file when starting the next Codex chat:

`docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md`

The handoff starts Plan 0 only. It requires the correct PIVOT workflow, all Plan 0 phases and increments, self-run increment checks, phase-level checks, and a final full-plan terminal block. It forbids Plan 1 start and forbids source/runtime/CSS/Cart/worker/provider/git mutation beyond Plan 0 docs cleanup scope.
