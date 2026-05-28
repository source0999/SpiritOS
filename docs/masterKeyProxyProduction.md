# SUPERSEDED ACTIVE DIRECTION NOTICE

Status: superseded for active roadmap direction as of 2026-05-27.

This document is preserved as historical evidence and traffic-control context. It is no longer the active source of truth for the Source Proxy agent integration, preflight CSS, Cart visibility, Mac/search/Scout, design, subagent, and final CSS path.

Use the build-first replacement roadmap instead:

- `docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md`
- `docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md`

Do not continue old Plan 23, start a soak, re-soak, activate Cartographer, run workers, or treat the old 24-plan chain as active direction from this file. The old chain must be classified in Plan 0 before any archive/delete action.

# Master Key Proxy Production Roadmap

Status: master production roadmap and traffic-control document

Owner: Britton

Created: 2026-05-26

Authority: planning and traffic control only. This document does not implement features, start runtimes, run tests, mutate queues, consume approval tokens, start workers, activate Cartographer, create branches or worktrees, commit, push, stash, reset, clean, or grant hidden autonomy.

## Purpose

This is the single production roadmap for the full SpiritOS proxy, Cartographer, design, Scout, Mac Mini support node, subagents, routes, final visual/CSS preflight work, production hardening, staged multi-lane execution, one-lane isolation, soak gates, and re-soak gates.

It tells future Codex runs where the repo is, what is active versus historical, which lane must be isolated first, when parallel work is safe, when parallel work must stop, when Cartographer is protected, when another soak is required, and how every future plan must follow PIVOT with phases, increments, manual checks, expected output, GO/NO-GO, and the next plan title.

## Current Truth Snapshot

- Cartographer is the main bottleneck until post-soak acceptance and promotion decisions clear.
- Latest audited Cartographer evidence records promotion status as not promoted, activation blocked or NO-GO, dirty-tree evidence as a blocker in the prior evidence, Level 8 runtime not started, and the limited auto-loop not run.
- Source Proxy PR-8.3 has narrow useful evidence but remains pending Britton acceptance or an explicit nonblocking decision before downstream Design Agent work can treat it as clear.
- Design Agent remains blocked or advisory until the Source Proxy gate clears.
- Design Agent Ecosystem Plan 20 is NO-GO until remediation evidence exists.
- Scout remains manual-controlled, parked, advisory, and writes disabled.
- Unified Proxy Coding/Design has valid non-Cart planning and evidence, but Cart/map/live surfaces remain gated.
- Some old docs are stale or historical. They must not be treated as active source of truth just because they exist.
- Closeout does not always mean accepted.
- Docs-only does not mean execution proof.
- Mac Mini 2018 with 16GB RAM exists as a support node with telemetry and SSH. It needs a baseline, workload-placement plan, and safety boundary before workloads move.
- Final CSS/preflight waits for visual proof, route-level proof, and lane gates.

## Authority Boundary

- No hidden autonomy.
- No self-promotion.
- No broad apply authority.
- No branch, worktree, commit, push, stash, reset, clean, or checkout without explicit approval.
- No Cartographer activation without explicit Britton acceptance.
- No live Cartographer, live map, queue, worker, approval-token, or runtime mutation during protected states.
- Source Proxy remains the write/apply gate.
- Design Agent and Design Agent subagents are advisory until explicitly promoted.
- Scout is manual-controlled until explicitly promoted.
- Mac Mini is support, advisory, search, telemetry, and subagent infrastructure until explicitly promoted.
- A manual check is proof only if the expected output is recorded and accepted.
- A passed docs-only plan does not authorize implementation.
- A narrow accepted receipt proves only the exact scope it documents.

## Source-Of-Truth Map

| Lane | Active source docs | Historical/stale docs | Current status | Current blocker | Britton decision needed |
| --- | --- | --- | --- | --- | --- |
| Cartographer | `docs/cartographer-live-evidence/`, `docs/cartographer-live-receipts/`, `docs/cartographer-a-grade-daily-driver-activation-pivot-plan-v0.1.md`, latest Plan 12 blocked evidence | Older `docs/cartographer-level-*` plans, root `cartographerBeta.md`, `cartogrpaherPlanAuto.md` unless revalidated | Main bottleneck, activation blocked, Level 8 not started in latest blocked evidence | Post-soak acceptance, promotion decision, dirty-tree/kill-switch blockers | Accept, reject, defer, or require another soak |
| Source Proxy | `docs/source-proxy-production-hardening-plan.md`, `docs/source-proxy-post-run-300-blocker-reduction-real-task-trial-roadmap-v0.1.md`, PR-8.3 receipts and closeouts, `docs/source-proxy-daily-use-runbook.md` | Root `productionProxy.md`, older closeout consolidation docs | Safety strong, usefulness and PR-8.3 acceptance still gated | PR-8.3 broad acceptance or nonblocking decision | Accept PR-8.3, mark nonblocking, or keep blocked |
| `/coding` cockpit | `docs/source-proxy-codex-like-active-task-ui-revamp-plan-v0.1.md`, `docs/codingUI.md`, unified proxy plan | Older UI plans not indexed as active | UI work can be Source Proxy only after gates | No hidden route calls, no apply, PR-8.3 downstream dependencies | Approve exact UI increments |
| Design Agent | `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md`, Plan H closeout | Older Design Agent exploratory docs | Advisory and blocked for Plan I | PR-8.3 accepted or nonblocking decision missing | Approve advisory continuation or wait |
| Design subagents | Design Agent Plan C, ecosystem plans 10 to 14, Plan 20 closeout | Prototype subagent docs not tied to current gates | Advisory only | No Source Proxy receive/display/score proof | Approve packet display only after gate |
| Design Agent Ecosystem | `docs/design-agent-ecosystem-plan-20-closeout-v0.1.md`, remediation plan | Plans 1 to 19 as evidence, not final proof | Final gate NO-GO | Missing Plan 0/equivalence, 100/300 prompt proof, visual/CSS proof, receive/display/score proof | Approve remediation execution later |
| Scout | `docs/scout-v0-8-closeout-summary.md`, `docs/scout-v0-9-next-phases-plan.md`, v0.9 planning docs | Earlier Scout root docs and v0.5/v0.6 docs as history unless indexed | Parked, manual-controlled, writes disabled | No new lane approval | Confirm Scout remains parked or approve exact docs-only lane |
| Mac Mini support node | Current prompt, telemetry/SSH operator knowledge, latest git history showing Mac telemetry lane merged | No durable master placement doc before this file | Support node candidate | Baseline and workload placement not yet recorded | Approve baseline and placement plan |
| Internet search routing | This roadmap, future Mac Mini Plan 4 | Prior research docs as reference only | Planned advisory/search lane | Provider, Docker, script, and packet boundaries undecided | Approve search routing scope |
| Chat, Oracle, dashboard | Unified proxy plan and current route ownership docs | Older root app roadmaps | Supporting surfaces | Must not touch live Cart/map unless Cart gate clears | Approve route-specific scope |
| Map/live Cart surfaces | Cartographer evidence and `src/app/map` only after gate | General UI polish docs | Gated | Cart acceptance and re-soak impact | Decide allowed, excluded, or Cart-only |
| Visual/CSS polish | Design Plan G, Design Ecosystem Plan 20, unified proxy plan | CSS polish claims without screenshot evidence | NO-GO for final polish | Visual proof and lane gates missing | Approve visual proof, then CSS scope |
| Production hardening | Source Proxy hardening, Cartographer activation docs, this roadmap | Old pre-v1 docs | Staged, not final | Multi-lane gates incomplete | Approve preflight after evidence rollup |

## Execution Modes

| Mode | Definition |
| --- | --- |
| ONE-LANE | Exactly one lane is active. Used when Cart, Source Proxy acceptance, runtime authority, protected paths, or dirty-tree conflicts are involved. |
| LIMITED MULTI-LANE | Multiple lanes may prepare docs, evidence, or advisory packets only when scopes are disjoint and Cart/live surfaces are excluded. |
| MULTI-LANE | Multiple non-Cart implementation or proof lanes may run only after blocking gates are accepted and file ownership is explicit. |
| DOCS-ONLY | Planning, inventories, packet contracts, decision registers, and manual check definitions only. No runtime or code mutation. |
| ADVISORY | A lane may produce recommendations, packets, summaries, citations, or review notes but cannot write/apply/execute. |
| INFRASTRUCTURE | Node setup, telemetry, SSH, service inventory, dashboards, or support-node proof. Starts read-only and requires explicit service authority. |
| SOAK-HOLD | Feature work stops or narrows while a soak is running, inconclusive, or awaiting acceptance. No disturbing live state. |
| FINAL REVIEW | Evidence rollup, production scorecard, and GO/NO-GO only. No new features. |

## Traffic-Control Rules

| Situation | Required mode | What Codex must do | What Codex must not do |
| --- | --- | --- | --- |
| Cart soak active | SOAK-HOLD / ONE-LANE for Cart only | Protect soak, avoid Cart runtime/log/live evidence writes, continue only safe non-Cart docs if approved | Start runtimes, queues, workers, tests that touch soak state, curl live Cart endpoints, edit live evidence |
| Cart post-soak not accepted | ONE-LANE / CARTOGRAPHER ISOLATED | Classify soak result and ask for Britton acceptance | Treat soak as accepted or resume live Cart/map work |
| Cart accepted but PR-8.3 blocked | LIMITED MULTI-LANE | Allow non-Cart docs and Source Proxy decision work | Start Design Plan I, final CSS, or broad multi-lane execution |
| Cart isolated and non-Cart work does not touch Cart/map/live evidence | LIMITED MULTI-LANE | Permit docs/advisory/non-Cart source planning with explicit exclusions | Touch protected paths or claim Cart readiness |
| Mac setup only | INFRASTRUCTURE / READ-ONLY FIRST | Baseline node identity, telemetry, SSH, Docker/Homebrew/script facts | Move workloads or start hidden services |
| Mac search/subagent advisory only | LIMITED MULTI-LANE / ADVISORY | Produce research packets and status summaries | Write repo files, call apply, mutate Cart, or run hidden workers |
| Mac job writes repo files | ONE-LANE | Require explicit approval and exact file list | Treat Mac as autonomous write host |
| Mac job touches Cart/map/live evidence | ONE-LANE / CARTOGRAPHER ISOLATED | Stop and route through Cart decision gate | Run in parallel or mutate live state |
| PR-8.3 accepted or nonblocking | LIMITED MULTI-LANE, then MULTI-LANE if other gates clear | Unlock Design Plan I and Run 300 reduction sequencing | Skip manual acceptance record |
| Runtime, queue, worker, approval-token, or trust-tier behavior changes | ONE-LANE and likely SOAK-HOLD | Require explicit approval, focused proof, and re-soak decision | Hide behavior changes inside UI/CSS work |
| Dirty tree or protected path conflict | ONE-LANE | Inventory status, stop if conflict affects scope, ask for decision | Clean, stash, reset, checkout, or normalize dirty state |

## PIVOT Rules For Every Future Plan

Every future plan must include:

- Plan number in the form `Plan N/24`.
- Mode.
- Purpose.
- Sequencing reason.
- Allowed scope.
- Forbidden scope.
- Phases.
- Increments.
- Codex self-checks after each increment.
- Phase closeout after every phase.
- Plan closeout after every plan.
- One terminal manual check block for Britton.
- Exact expected output.
- Final GO/NO-GO.
- Next plan title and count.

Every increment must stop after evidence. Codex may not skip phases, merge plans, or treat a future title as authority. Every manual check must use non-destructive commands unless Britton explicitly approves otherwise.

## The 24 Plan Master Roadmap

### Plan 1/24: Cartographer Post-Soak Result Acceptance And Promotion Decision Audit

Mode: ONE-LANE / CARTOGRAPHER ISOLATED

Purpose: Decide what the 24h soak means after it finishes.

Why it is sequenced here: Cartographer is the production bottleneck and must be classified before live Cart/map behavior or broad multi-lane work resumes.

Allowed scope: Read-only branch/status/evidence inventory, soak result classification, promotion decision record.

Forbidden scope: Runtime start, queue start, worker start, approval-token mutation, live map mutation, push, branch, worktree, commit, cleanup.

Phase 1.1: Post-Soak Baseline

- 1.1.1 Confirm branch, HEAD, and clean or dirty state.
- 1.1.2 Inventory final soak evidence, receipts, and soak logs.
- 1.1.3 Confirm no hidden runtime, queue, worker, autopilot, approval-token, or live map mutation started.

Phase 1.2: Soak Result Classification

- 1.2.1 Classify soak as ACCEPTED, REJECTED, ACCEPTED_WITH_CONDITIONS, INCONCLUSIVE, or NEEDS_ANOTHER_SOAK.
- 1.2.2 Check promotion status, activation status, dirty-tree blocker, and kill-switch blocker.
- 1.2.3 Decide whether Cart remains isolated.

Phase 1.3: Promotion Decision Boundary

- 1.3.1 Record whether Britton accepts, rejects, or defers promotion.
- 1.3.2 Decide whether another soak is required.
- 1.3.3 Output next authorized plan only.

Stop conditions: Missing soak evidence, dirty-tree conflict, any runtime mutation, unclear Britton acceptance, or live map impact.

Manual check requirement: Terminal block with `git status`, HEAD, evidence grep, and no runtime-start proof.

Expected output requirement: Cart state is one of isolated, promoted, blocked, or re-soak.

GO/NO-GO requirement: GO only with explicit Britton acceptance or explicit deferral. NO-GO keeps Cart isolated.

Next plan title requirement: Plan 2/24: Mac Mini Support Node Baseline And Safety Boundary.

### Plan 2/24: Mac Mini Support Node Baseline And Safety Boundary

Mode: INFRASTRUCTURE / READ-ONLY FIRST

Purpose: Make the Mac Mini official in the system without moving workloads yet.

Why it is sequenced here: Mac Mini can be baselined in parallel with non-Cart decision work, but only as infrastructure and telemetry.

Allowed scope: Read-only node identity, telemetry, SSH, OS, hardware, compatibility, and boundary documentation.

Forbidden scope: Workload migration, autonomous writes, Cart mutation, Source Proxy mutation, hidden workers.

Phase 2.1: Node Identity

- 2.1.1 Confirm hostname, LAN IP, SSH access, user, and OS version.
- 2.1.2 Confirm telemetry identity is visible in SpiritOS.
- 2.1.3 Confirm hardware profile, including Mac Mini 2018 and 16GB RAM.

Phase 2.2: Capability Baseline

- 2.2.1 Record CPU, RAM, storage, network, and uptime.
- 2.2.2 Check Docker and macOS compatibility before assuming containers.
- 2.2.3 Decide Homebrew service, Docker service, or plain-script preference.

Phase 2.3: Safety Boundary

- 2.3.1 Declare Mac Mini cannot mutate Cart while Cart is gated.
- 2.3.2 Declare Mac Mini cannot write to Source Proxy without approval.
- 2.3.3 Declare Mac Mini can run search/advisory jobs only after explicit scope.

Stop conditions: SSH ambiguity, telemetry mismatch, Docker assumption without proof, or any write requirement.

Manual check requirement: One read-only SSH/telemetry block and expected identity output.

Expected output requirement: Baseline packet and safety boundary.

GO/NO-GO requirement: GO only for support-node registration, not workload migration.

Next plan title requirement: Plan 3/24: Mac Mini Workload Placement Matrix.

### Plan 3/24: Mac Mini Workload Placement Matrix

Mode: PLANNING / NO MIGRATION YET

Purpose: Decide what should run on Mac, server, GPU node, or not move.

Why it is sequenced here: Placement must be explicit before any Mac workload moves.

Allowed scope: Workload inventory and placement decision table.

Forbidden scope: Migration, service start, repo writes, Cart/live evidence access.

Phase 3.1: Workload Inventory

- 3.1.1 List Scout workloads.
- 3.1.2 List subagent workloads.
- 3.1.3 List internet search workloads.
- 3.1.4 List telemetry/dashboard workloads.

Phase 3.2: Placement Decision

- 3.2.1 Mark each workload Mac preferred, Server preferred, GPU node preferred, do not move, or later.
- 3.2.2 Identify memory-heavy jobs that should not run on the 16GB Mac.
- 3.2.3 Identify always-on jobs that fit the Mac well.

Phase 3.3: Conflict Model

- 3.3.1 If a Mac job touches Cart, isolate Cart.
- 3.3.2 If a Mac job writes repo files, require explicit approval.
- 3.3.3 If a Mac job only searches and creates advisory packets, allow limited parallel mode.

Stop conditions: A job needs hidden write authority, Cart access, or more memory than the Mac budget.

Manual check requirement: Workload table review with no migration commands.

Expected output requirement: Placement matrix.

GO/NO-GO requirement: GO only for future scoped setup plans.

Next plan title requirement: Plan 4/24: Mac Mini Internet Search And Scout Intake Node.

### Plan 4/24: Mac Mini Internet Search And Scout Intake Node

Mode: MAC SUPPORT NODE / ADVISORY ONLY

Purpose: Route internet search and Scout-style discovery through the Mac when safe.

Why it is sequenced here: Search can feed Source Proxy, Scout, and Design Agent without granting write authority.

Allowed scope: Read-only search policy, provider choice, packet contract.

Forbidden scope: Direct repo mutation, direct Cart mutation, auto-promotion, hidden scheduled discovery.

Phase 4.1: Search Boundary

- 4.1.1 Define search jobs as read-only.
- 4.1.2 Define allowed output: search summaries, citations, packets, and candidates.
- 4.1.3 Forbid direct repo mutation from search jobs.

Phase 4.2: Search Provider Decision

- 4.2.1 Decide whether to run SearXNG, browser automation, CLI search, or API search.
- 4.2.2 Decide whether Docker is required or scripts are safer.
- 4.2.3 Define fallback if Docker is unsupported or too heavy.

Phase 4.3: Proxy Integration

- 4.3.1 Define how Source Proxy asks Mac for search.
- 4.3.2 Define how Mac returns research packets.
- 4.3.3 Confirm Source Proxy remains the approval/write gate.

Stop conditions: Search wants writes, crawling is unsafely broad, provider credentials are unclear, or Docker is unstable.

Manual check requirement: Provider capability proof and packet example.

Expected output requirement: Search routing contract.

GO/NO-GO requirement: GO only for advisory search.

Next plan title requirement: Plan 5/24: Mac Mini Subagent Host Feasibility.

### Plan 5/24: Mac Mini Subagent Host Feasibility

Mode: SUBAGENT ADVISORY / NO WRITE AUTHORITY

Purpose: Decide which subagents can run on the Mac.

Why it is sequenced here: Subagents can become useful only after compute and authority boundaries are clear.

Allowed scope: Advisory subagent inventory, compute fit, memory budget, routing contract.

Forbidden scope: Apply authority, Cart workflows, hidden worker host, direct commits.

Phase 5.1: Subagent Inventory

- 5.1.1 Component mapper.
- 5.1.2 Safety reviewer.
- 5.1.3 Test scribe.
- 5.1.4 Design packet reviewer.
- 5.1.5 Scout research helper.

Phase 5.2: Compute Fit

- 5.2.1 CPU-only agent fit.
- 5.2.2 Memory budget per agent.
- 5.2.3 Concurrency cap for 16GB RAM.

Phase 5.3: Routing Boundary

- 5.3.1 Mac subagents can prepare packets.
- 5.3.2 Mac subagents cannot apply code.
- 5.3.3 Mac subagents cannot start Cart workflows.
- 5.3.4 Mac subagents report back to Source Proxy.

Stop conditions: Memory pressure, unscoped writes, hidden task queue, or Cart workflow dependency.

Manual check requirement: Subagent role table and concurrency cap.

Expected output requirement: Feasibility decision.

GO/NO-GO requirement: GO only for advisory packet production.

Next plan title requirement: Plan 6/24: Mac Mini Remote Worker Control And Telemetry Dashboard Integration.

### Plan 6/24: Mac Mini Remote Worker Control And Telemetry Dashboard Integration

Mode: INFRASTRUCTURE / OBSERVABILITY

Purpose: Make the Mac visible and controllable from SpiritOS without blind mutation.

Why it is sequenced here: Observability must precede any service or worker control.

Allowed scope: Telemetry visibility, SSH read-only controls, dashboard planning.

Forbidden scope: Blind restart, hidden worker start, repo mutation, Cart mutation.

Phase 6.1: Telemetry

- 6.1.1 Confirm node status in dashboard.
- 6.1.2 Confirm uptime, storage, memory, and CPU telemetry.
- 6.1.3 Confirm stale/offline state handling.

Phase 6.2: SSH Control

- 6.2.1 Define read-only SSH check commands.
- 6.2.2 Define approved service restart commands.
- 6.2.3 Define forbidden commands during soak or Cart isolation.

Phase 6.3: Operator UX

- 6.3.1 Add Mac status to dashboard planning.
- 6.3.2 Add Mac search/subagent job status later.
- 6.3.3 Add manual controls only after approval.

Stop conditions: Telemetry stale, SSH unverified, command list includes mutation without approval.

Manual check requirement: Dashboard/telemetry readout and SSH command list.

Expected output requirement: Observability plan and command boundary.

GO/NO-GO requirement: GO for visibility only unless restart authority is explicit.

Next plan title requirement: Plan 7/24: Cartographer Activation Boundary And Re-Soak Decision.

### Plan 7/24: Cartographer Activation Boundary And Re-Soak Decision

Mode: ONE-LANE / CARTOGRAPHER ONLY

Purpose: Decide whether Cart can move beyond blocked activation.

Why it is sequenced here: Activation and re-soak must be settled before live Cart/map or trust-tier work.

Allowed scope: Blocker review, authority boundary, re-soak branch decision.

Forbidden scope: Auto-promotion, push/commit/branch/worktree authority, approval-token mutation, runtime start without approval.

Phase 7.1: Activation Blockers

- 7.1.1 Review dirty-tree blocker.
- 7.1.2 Review kill-switch and demotion gate.
- 7.1.3 Review Level 8 runtime readiness.

Phase 7.2: Authority Boundary

- 7.2.1 Confirm no auto-promotion.
- 7.2.2 Confirm no push, commit, branch, or worktree authority.
- 7.2.3 Confirm approval-token boundaries.

Phase 7.3: Re-Soak Branch

- 7.3.1 If activation behavior changes, mark re-soak required.
- 7.3.2 If no behavior changes, permit non-Cart lanes to resume.
- 7.3.3 Output Cart state: isolated, promoted, blocked, or re-soak.

Stop conditions: Any behavior change without soak plan, unclear dirty tree, unclear kill switch.

Manual check requirement: Activation blocker packet and re-soak decision.

Expected output requirement: Cart state and permitted next lane.

GO/NO-GO requirement: GO only for explicitly bounded activation next step or non-Cart resume.

Next plan title requirement: Plan 8/24: Source Proxy PR-8.3 Acceptance Or Nonblocking Decision.

### Plan 8/24: Source Proxy PR-8.3 Acceptance Or Nonblocking Decision

Mode: ONE-LANE / SOURCE PROXY DECISION

Purpose: Clear or explicitly defer the dependency blocking Design Agent and final preflight.

Why it is sequenced here: Design Agent Plan I and several final gates depend on PR-8.3 being accepted or declared nonblocking.

Allowed scope: Receipt package review and Britton decision record.

Forbidden scope: New PR-8.3 run, browser proof, implementation, provider, queue, worker, apply, commit, push.

Phase 8.1: Receipt Package Review

- 8.1.1 Inventory PR-8.3 receipt package.
- 8.1.2 Separate narrow accepted evidence from broad PR-8.3 acceptance.
- 8.1.3 Identify dirty-tree evidence that still blocks.

Phase 8.2: Britton Decision

- 8.2.1 Option A: accept PR-8.3.
- 8.2.2 Option B: mark PR-8.3 nonblocking.
- 8.2.3 Option C: keep PR-8.3 blocked.

Phase 8.3: Downstream Gate

- 8.3.1 Decide whether Design Agent Plan I can start.
- 8.3.2 Decide whether Run 300 recovery can start.
- 8.3.3 Decide whether /coding UI work is allowed.

Stop conditions: Evidence conflict, unaccepted dirty-tree issue, or attempt to treat narrow receipt as broad acceptance.

Manual check requirement: Receipt grep and decision line.

Expected output requirement: PR-8.3 accepted, nonblocking, or blocked.

GO/NO-GO requirement: GO only with explicit Britton decision.

Next plan title requirement: Plan 9/24: Source Proxy Run 300 Blocker Reduction.

### Plan 9/24: Source Proxy Run 300 Blocker Reduction

Mode: SOURCE PROXY ONLY

Purpose: Fix usefulness without weakening safety.

Why it is sequenced here: Source Proxy is safe but overblocking. Usefulness must improve before daily-driver or CSS claims.

Allowed scope: Safe-blocker category map, proposal/no-op/diff-preview semantics, focused approved checks only.

Forbidden scope: Apply, provider, queue, worker, shell execution, Cart activation, final CSS.

Phase 9.1: Run 300 Classification

- 9.1.1 Build safe-blocker category map.
- 9.1.2 Identify overblocking versus correct blocking.
- 9.1.3 Define productive no-op, proposal, and diff-preview outputs.

Phase 9.2: Preview Usefulness

- 9.2.1 Improve safe no-op explanations.
- 9.2.2 Improve proposal packet structure.
- 9.2.3 Improve diff-preview readiness without apply authority.

Phase 9.3: Regression Proof

- 9.3.1 Re-run approved focused checks only if authorized.
- 9.3.2 Record safety metrics.
- 9.3.3 Decide whether Run 300 rerun is authorized.

Stop conditions: Unsafe category becomes productive, authority flag changes, or Cart path enters scope.

Manual check requirement: Safety metrics and focused check output if approved.

Expected output requirement: Blocker map and usefulness delta.

GO/NO-GO requirement: GO only if safety remains 0 unsafe failures and no authority drift.

Next plan title requirement: Plan 10/24: /coding Active Task Cockpit And Operator Clarity.

### Plan 10/24: /coding Active Task Cockpit And Operator Clarity

Mode: SOURCE PROXY UI ONLY

Purpose: Make the coding agent feel usable without hidden authority.

Why it is sequenced here: Operator clarity improves daily use after Source Proxy decision and blocker work are scoped.

Allowed scope: UI truth surfaces, evidence visibility, approval boundary display.

Forbidden scope: Hidden route calls, backend mutation, provider calls, apply, commit, push.

Phase 10.1: UI Truth Surfaces

- 10.1.1 Show task target.
- 10.1.2 Show allowed and forbidden files.
- 10.1.3 Show provider/model status.

Phase 10.2: Evidence Visibility

- 10.2.1 Show dirty-tree state.
- 10.2.2 Show preview, no-op, and proposal status.
- 10.2.3 Show manual check readiness.

Phase 10.3: Approval Boundary

- 10.3.1 Ensure approval, apply, commit, and push remain separate.
- 10.3.2 Ensure no hidden route calls.
- 10.3.3 Produce final UI readiness gate.

Stop conditions: UI implies authority not granted, route call appears, or protected path scope is unclear.

Manual check requirement: Route/UI proof and grep for authority copy.

Expected output requirement: `/coding` readiness gate.

GO/NO-GO requirement: GO only for display clarity with Source Proxy authority unchanged.

Next plan title requirement: Plan 11/24: Source Proxy Production Hardening Consolidation.

### Plan 11/24: Source Proxy Production Hardening Consolidation

Mode: SOURCE PROXY ONLY

Purpose: Consolidate safety and identify missing production proof.

Why it is sequenced here: Hardening must precede staged multi-lane execution.

Allowed scope: Safety map, authority freeze, readiness delta.

Forbidden scope: New autonomy, provider/model calls, apply/execute-approved, git mutation.

Phase 11.1: Safety Surface Map

- 11.1.1 Map approval gate.
- 11.1.2 Map diff verification.
- 11.1.3 Map workspace/path safety.

Phase 11.2: Authority Freeze

- 11.2.1 Confirm no provider/model call unless explicit.
- 11.2.2 Confirm no apply/execute-approved unless explicit.
- 11.2.3 Confirm no commit, push, branch, or worktree authority.

Phase 11.3: Production Readiness Delta

- 11.3.1 List missing proof.
- 11.3.2 List required tests.
- 11.3.3 Decide whether Proxy can enter staged multi-lane mode.

Stop conditions: Missing proof hidden as pass, broad authority implied, or tests required but not approved.

Manual check requirement: Safety map grep and missing-proof table.

Expected output requirement: Readiness delta.

GO/NO-GO requirement: GO only when missing proof is explicit.

Next plan title requirement: Plan 12/24: Design Agent A-Grade Dependency Unlock.

### Plan 12/24: Design Agent A-Grade Dependency Unlock

Mode: DESIGN ADVISORY ONLY until PR-8.3 clears

Purpose: Move Design Agent only after its dependency gate is honest.

Why it is sequenced here: Design Agent Plan I is blocked until Source Proxy dependency is accepted or nonblocking.

Allowed scope: Gate audit, A-grade criteria, advisory packet continuation.

Forbidden scope: Design apply, CSS edits, Source Proxy writes, final gauntlet execution.

Phase 12.1: Plan H/I Gate

- 12.1.1 Confirm Plan H was docs-only.
- 12.1.2 Confirm Plan I remains blocked or is newly authorized.
- 12.1.3 Confirm no design apply authority.

Phase 12.2: A-Grade Criteria

- 12.2.1 Define evidence required for A grade.
- 12.2.2 Define visual proof requirements.
- 12.2.3 Define Source Proxy receive/display/score proof.

Phase 12.3: Design Lane Continuation

- 12.3.1 Decide advisory-only continuation.
- 12.3.2 Decide packet format.
- 12.3.3 Decide next Design Agent plan.

Stop conditions: PR-8.3 unresolved, packet implies apply, or visual proof missing.

Manual check requirement: Plan H/I gate grep and decision record.

Expected output requirement: Design status is blocked, advisory, or newly authorized.

GO/NO-GO requirement: GO only after PR-8.3 decision clears dependency.

Next plan title requirement: Plan 13/24: Design Agent Ecosystem Remediation.

### Plan 13/24: Design Agent Ecosystem Remediation

Mode: DESIGN ADVISORY / DOCS-FIRST

Purpose: Recover from Plan 20 NO-GO honestly.

Why it is sequenced here: Remediation must happen before Design/CSS claims.

Allowed scope: Missing-evidence table, prompt gauntlet readiness, remediation GO/NO-GO.

Forbidden scope: Merge implementation, production CSS polish, Source Proxy proof execution without approval.

Phase 13.1: Missing Evidence Table

- 13.1.1 Plan 0/equivalence status.
- 13.1.2 Source Proxy receive/display/score status.
- 13.1.3 Visual/CSS proof status.

Phase 13.2: Prompt Gauntlet Readiness

- 13.2.1 100-prompt proof readiness.
- 13.2.2 300-prompt proof readiness.
- 13.2.3 Daily-use score readiness.

Phase 13.3: Remediation GO/NO-GO

- 13.3.1 Mark each blocker missing, not_started, blocked, partial, or accepted.
- 13.3.2 Decide whether remediation execution may start.
- 13.3.3 Output next design plan.

Stop conditions: NO-GO softened, docs-only treated as proof, missing visual proof.

Manual check requirement: Plan 20 blocker grep and remediation table.

Expected output requirement: Honest remediation status.

GO/NO-GO requirement: GO only for explicitly approved remediation execution.

Next plan title requirement: Plan 14/24: Design Subagent Fleet Preintegration.

### Plan 14/24: Design Subagent Fleet Preintegration

Mode: ADVISORY ONLY / MAC-AWARE

Purpose: Bring subagents into the proxy ecosystem without write/apply authority.

Why it is sequenced here: Subagents can support Design and Source Proxy once packet contracts are clear.

Allowed scope: Helper role map, proposal packet contract, integration gate.

Forbidden scope: Apply authority, direct repo writes, Cart workflows, hidden subagent workers.

Phase 14.1: Helper Role Map

- 14.1.1 Component mapper boundary.
- 14.1.2 Safety reviewer boundary.
- 14.1.3 Test scribe boundary.
- 14.1.4 Mac-hosted advisory option.

Phase 14.2: Proposal Packet Contract

- 14.2.1 Define packet fields.
- 14.2.2 Define scoring fields.
- 14.2.3 Define blocked-reason fields.

Phase 14.3: Integration Gate

- 14.3.1 Confirm no apply authority.
- 14.3.2 Confirm Source Proxy remains write gate.
- 14.3.3 Decide whether subagent packets can display in /coding.

Stop conditions: Packet implies direct apply, Mac becomes hidden worker, or Source Proxy gate is bypassed.

Manual check requirement: Packet schema and no-apply grep.

Expected output requirement: Display eligibility decision.

GO/NO-GO requirement: GO only for advisory packet display.

Next plan title requirement: Plan 15/24: Scout Manual-Controlled Intelligence Lane.

### Plan 15/24: Scout Manual-Controlled Intelligence Lane

Mode: PARALLEL DOCS-ONLY / MANUAL-CONTROLLED / MAC-BACKED OPTIONAL

Purpose: Keep Scout useful without autonomy.

Why it is sequenced here: Scout can support discovery/search while remaining parked and manual-controlled.

Allowed scope: Parked-state confirmation, proxy intake contract, parallel safety decision.

Forbidden scope: Autonomous discovery, writes, proxy memory writes, coding context writes, promotion finalization.

Phase 15.1: Parked State Confirmation

- 15.1.1 Confirm manual-controlled state.
- 15.1.2 Confirm writes disabled.
- 15.1.3 Confirm no autonomous discovery.

Phase 15.2: Proxy Intake Contract

- 15.2.1 Define advisory research packet.
- 15.2.2 Define promotion queue preview.
- 15.2.3 Define no-write boundary.

Phase 15.3: Parallel Safety Decision

- 15.3.1 Decide what Scout can do during Proxy work.
- 15.3.2 Decide what Scout cannot do during Cart isolation.
- 15.3.3 Decide whether Scout search can route through Mac.

Stop conditions: Scout writes, auto-discovery, proxy intake calls, or Cart touch.

Manual check requirement: Scout parked-state grep and packet example.

Expected output requirement: Scout remains parked or exact next lane is named.

GO/NO-GO requirement: GO only for manual-controlled advisory continuation.

Next plan title requirement: Plan 16/24: Chat, Oracle, Dashboard, And Supporting Surface Ownership.

### Plan 16/24: Chat, Oracle, Dashboard, And Supporting Surface Ownership

Mode: MULTI-LANE ELIGIBLE IF NON-CART

Purpose: Define which surfaces are roadmap drivers and which are supporting UI.

Why it is sequenced here: Surface ownership prevents visual or route work from crossing into Cart accidentally.

Allowed scope: Ownership map, route constraints, support lane readiness.

Forbidden scope: Live Cart/map mutation, provider calls, storage mutations without approval.

Phase 16.1: Surface Ownership

- 16.1.1 Chat ownership.
- 16.1.2 Oracle ownership.
- 16.1.3 Dashboard ownership.

Phase 16.2: Route Constraints

- 16.2.1 Exclude live Cart/map unless Cart gate clears.
- 16.2.2 Separate display-only surfaces from runtime surfaces.
- 16.2.3 Define route-level proof needs.

Phase 16.3: Support Lane Readiness

- 16.3.1 Decide which support surfaces can move in parallel.
- 16.3.2 Decide which are blocked by Cart.
- 16.3.3 Output surface lane order.

Stop conditions: Route ownership unclear, live Cart dependency, or provider/storage mutation needed.

Manual check requirement: Route table and excluded surfaces.

Expected output requirement: Surface lane order.

GO/NO-GO requirement: GO only for non-Cart surfaces with explicit proof needs.

Next plan title requirement: Plan 17/24: Map And Cartographer UI Integration Gate.

### Plan 17/24: Map And Cartographer UI Integration Gate

Mode: ONE-LANE IF LIVE CART/MAP

Purpose: Prevent non-Cart UI polish from accidentally mutating Cart.

Why it is sequenced here: Map work is the common place where UI polish can cross into live Cart state.

Allowed scope: Static versus live boundary, protected paths, gate output.

Forbidden scope: Live map refresh, runtime mutation, evidence writes unless Cart gate allows.

Phase 17.1: Map Boundary

- 17.1.1 Separate static map UI from live map state.
- 17.1.2 Separate Cart evidence display from Cart runtime.
- 17.1.3 Identify protected paths.

Phase 17.2: Integration Proof

- 17.2.1 If Cart accepted, define safe map refresh proof.
- 17.2.2 If Cart blocked, define exclusion rules.
- 17.2.3 If uncertain, keep map out of CSS/preflight.

Phase 17.3: Gate Output

- 17.3.1 Mark map as allowed, excluded, or Cart-only.
- 17.3.2 Define required soak/re-soak impact.
- 17.3.3 Output next authorized visual plan.

Stop conditions: Live map ambiguity, protected path conflict, or re-soak impact unclear.

Manual check requirement: Protected path list and map status.

Expected output requirement: Map allowed, excluded, or Cart-only.

GO/NO-GO requirement: GO only if live state is protected or explicitly accepted.

Next plan title requirement: Plan 18/24: Controlled Multi-Agent And Subagent Orchestration Boundary.

### Plan 18/24: Controlled Multi-Agent And Subagent Orchestration Boundary

Mode: PREVIEW ONLY

Purpose: Prepare worker/subagent coordination without hidden autonomy.

Why it is sequenced here: Multi-agent work must be designed before any worker orchestration is trusted.

Allowed scope: Worker identity, lane ownership, handoff packet, block rules.

Forbidden scope: Hidden worker start, branch/worktree implication, protected path mutation.

Phase 18.1: Worker Identity

- 18.1.1 Define worker identity.
- 18.1.2 Define lane ownership.
- 18.1.3 Define allowed/forbidden files.

Phase 18.2: Handoff Packets

- 18.2.1 Define handoff packet fields.
- 18.2.2 Define conflict-report fields.
- 18.2.3 Define lease/lock awareness.

Phase 18.3: Block Rules

- 18.3.1 Block unknown worker, task, or lane.
- 18.3.2 Block protected path scope.
- 18.3.3 Block hidden mutation or branch/worktree implication.

Stop conditions: Unknown worker, missing ownership, protected path overlap, hidden mutation.

Manual check requirement: Worker registry preview and packet schema.

Expected output requirement: Orchestration preview contract.

GO/NO-GO requirement: GO only for preview-only coordination.

Next plan title requirement: Plan 19/24: Controlled Action Authority And Approval Token Ladder.

### Plan 19/24: Controlled Action Authority And Approval Token Ladder

Mode: AUTHORITY DESIGN ONLY unless explicitly approved

Purpose: Define future narrow write/execution authority without broad autonomy.

Why it is sequenced here: Any later write or execution authority needs a precise ladder and token model.

Allowed scope: Authority ladder, token requirements, event ledger design.

Forbidden scope: Token consumption, approved writes, execution, apply, commit, push unless separately approved.

Phase 19.1: Authority Ladder

- 19.1.1 Observe.
- 19.1.2 Recommend.
- 19.1.3 Preview.
- 19.1.4 Dry run.
- 19.1.5 Approved write.
- 19.1.6 Approved local execution.

Phase 19.2: Token Requirements

- 19.2.1 Required token fields.
- 19.2.2 Expiration and revocation rules.
- 19.2.3 Scope mismatch failure rules.

Phase 19.3: Event Ledger

- 19.3.1 Define event types.
- 19.3.2 Define no-silent-rewrite rule.
- 19.3.3 Define action closeout requirements.

Stop conditions: Broad token scope, silent rewrite, token without expiration, or authority ladder skipped.

Manual check requirement: Token schema review.

Expected output requirement: Authority design packet.

GO/NO-GO requirement: GO only for design unless Britton approves exact authority.

Next plan title requirement: Plan 20/24: Visual Evidence And Browser Proof Harness.

### Plan 20/24: Visual Evidence And Browser Proof Harness

Mode: NON-CART ONLY UNTIL CART CLEARS

Purpose: Create honest visual proof before final CSS polish.

Why it is sequenced here: CSS polish must follow screenshots, responsive proof, and route scoring.

Allowed scope: Route inventory, screenshot contract, responsive/accessibility relevance scoring.

Forbidden scope: Live `/map` unless allowed, final CSS edits, hidden browser automation during protected soak.

Phase 20.1: Route Inventory

- 20.1.1 /coding.
- 20.1.2 dashboard.
- 20.1.3 chat/oracle.
- 20.1.4 exclude /map unless allowed.

Phase 20.2: Visual Proof Contract

- 20.2.1 Screenshot evidence.
- 20.2.2 Responsive evidence.
- 20.2.3 Accessibility/token/component relevance.

Phase 20.3: Readiness Scoring

- 20.3.1 Route score.
- 20.3.2 Blocker score.
- 20.3.3 Final visual GO/NO-GO.

Stop conditions: Browser proof would touch live Cart, screenshots unavailable, or CSS scope appears early.

Manual check requirement: Screenshot list, route list, and excluded map status.

Expected output requirement: Visual readiness score.

GO/NO-GO requirement: GO only for routes with proof.

Next plan title requirement: Plan 21/24: Final CSS Polish Gate.

### Plan 21/24: Final CSS Polish Gate

Mode: MULTI-LANE ONLY IF GATES CLEAR

Purpose: Do final CSS only after visual proof, not before.

Why it is sequenced here: Polish is last because it can hide functional, routing, or Cart state problems if done early.

Allowed scope: Approved CSS files, route-specific polish, component-specific polish, responsive proof.

Forbidden scope: Runtime files, Cart paths, broad sweep, live map work unless Cart gate clears.

Phase 21.1: CSS Scope

- 21.1.1 Define allowed CSS files.
- 21.1.2 Define forbidden runtime/Cart paths.
- 21.1.3 Define no broad sweep rule.

Phase 21.2: Patch Increments

- 21.2.1 Route-specific polish.
- 21.2.2 Component-specific polish.
- 21.2.3 Responsive polish.

Phase 21.3: Proof

- 21.3.1 Screenshot before/after.
- 21.3.2 Typecheck/lint/focused UI checks only if approved.
- 21.3.3 CSS closeout and rollback notes.

Stop conditions: Missing visual proof, unapproved test command, Cart path touched, or broad CSS sweep.

Manual check requirement: Before/after screenshots and focused diff.

Expected output requirement: Route-scoped polish closeout.

GO/NO-GO requirement: GO only when gates clear and proof exists.

Next plan title requirement: Plan 22/24: Preflight Production Readiness Review.

### Plan 22/24: Preflight Production Readiness Review

Mode: MULTI-LANE REVIEW / NO NEW FEATURES

Purpose: Review the whole system against production criteria.

Why it is sequenced here: Feature work must stop before production review.

Allowed scope: Lane readiness, operational readiness, launch checklist.

Forbidden scope: New features, hidden fixes, unapproved tests, runtime changes.

Phase 22.1: Lane Readiness

- 22.1.1 Cart readiness.
- 22.1.2 Proxy readiness.
- 22.1.3 Design readiness.
- 22.1.4 Scout readiness.
- 22.1.5 Mac support node readiness.

Phase 22.2: Operational Readiness

- 22.2.1 Runbooks/manual checks.
- 22.2.2 Rollback/demotion.
- 22.2.3 Observability/evidence.

Phase 22.3: Launch Checklist

- 22.3.1 Required proof present.
- 22.3.2 Missing proof marked honestly.
- 22.3.3 Production GO/NO-GO.

Stop conditions: Missing proof, unresolved blocker, or new feature request.

Manual check requirement: Evidence rollup command block.

Expected output requirement: Production checklist.

GO/NO-GO requirement: GO only if each lane has accepted proof or explicit exclusion.

Next plan title requirement: Plan 23/24: Soak, Re-Soak, And Staged Multi-Lane Scheduler.

### Plan 23/24: Soak, Re-Soak, And Staged Multi-Lane Scheduler

Mode: SOAK-HOLD OR GREEN MULTI-LANE depending on gates

Purpose: Define when feature work stops and reliability soak starts, and when staged multi-lane can resume.

Why it is sequenced here: Reliability scheduling determines final production confidence.

Allowed scope: Soak triggers, evidence policy, lane scheduler, soak exit decision.

Forbidden scope: Disturbing soak, changing runtime during soak, parallel work that touches protected state.

Phase 23.1: Soak Triggers

- 23.1.1 Runtime behavior change trigger.
- 23.1.2 Queue/worker change trigger.
- 23.1.3 Approval-token/trust-tier/daily-driver change trigger.
- 23.1.4 Mac migration trigger if it affects runtime/search/subagent orchestration.

Phase 23.2: Soak Evidence

- 23.2.1 Evidence packet.
- 23.2.2 Snapshot/receipt policy.
- 23.2.3 No-disturb rule.

Phase 23.3: Multi-Lane Scheduler

- 23.3.1 Define active lanes.
- 23.3.2 Define blocked lanes.
- 23.3.3 Define safe parallel lanes.
- 23.3.4 Define Mac-backed advisory lanes.

Phase 23.4: Soak Exit

- 23.4.1 Accept/reject/inconclusive.
- 23.4.2 Re-soak required or not required.
- 23.4.3 Resume one-lane or multi-lane.

Stop conditions: Protected state mutation, unaccepted soak result, or re-soak trigger ignored.

Manual check requirement: Soak evidence and scheduler table.

Expected output requirement: Resume mode and blocked lanes.

GO/NO-GO requirement: GO only when soak exit is accepted.

Next plan title requirement: Plan 24/24: Final Production Master Closeout And Next Roadmap Gate.

### Plan 24/24: Final Production Master Closeout And Next Roadmap Gate

Mode: FINAL REVIEW

Purpose: Close the master plan honestly and decide the next roadmap.

Why it is sequenced here: Final closeout must roll up all lanes and name the next roadmap without starting it.

Allowed scope: Evidence rollup, production scorecard, final closeout.

Forbidden scope: New features, hidden implementation, cleanup, git mutation without approval.

Phase 24.1: Evidence Rollup

- 24.1.1 Cart evidence.
- 24.1.2 Proxy evidence.
- 24.1.3 Design/subagent evidence.
- 24.1.4 Scout evidence.
- 24.1.5 Mac Mini support node evidence.

Phase 24.2: Production Scorecard

- 24.2.1 Safety score.
- 24.2.2 Usefulness score.
- 24.2.3 Visual/CSS score.
- 24.2.4 Autonomy score.
- 24.2.5 Infrastructure/support-node score.

Phase 24.3: Final Closeout

- 24.3.1 Manual check block.
- 24.3.2 Expected output.
- 24.3.3 Final GO/NO-GO.
- 24.3.4 Next roadmap title.

Stop conditions: Any lane is unscored, missing proof is hidden, or next roadmap implies authority.

Manual check requirement: Full final evidence block.

Expected output requirement: Master closeout and next roadmap title.

GO/NO-GO requirement: GO only if all blocking lanes are accepted, excluded, or explicitly deferred.

Next plan title requirement: Britton chooses the next production roadmap title after Plan 24/24 closeout.

## Mac Mini Support Node Strategy

### Intended Role

- Support node.
- Internet search node.
- Scout-style discovery node.
- Advisory subagent host.
- Documentation and indexing helper.
- Telemetry participant.
- Read-only repo scan/helper node.
- Possible SearXNG or search broker host if compatible.
- Possible lightweight service host if hardware and macOS support it.

### Not Intended Role

- Not the main local LLM inference box.
- Not the primary Source Proxy runtime.
- Not a Cartographer activation node.
- Not an autonomous write node.
- Not a hidden worker host.
- Not a direct apply/commit/push authority source.
- Not a place to bypass Source Proxy approval gates.

### Preferred Workloads

- Search summaries with citations.
- Advisory Scout intake packets.
- Design Agent packet review.
- Test-scribe notes without running tests unless approved.
- Documentation indexing.
- Read-only telemetry and health reporting.
- Lightweight background status checks after approval.

### Forbidden Workloads

- Cartographer activation.
- Cartographer live map mutation.
- Approval-token mutation.
- Source Proxy apply or execute-approved calls.
- Git commit, push, branch, worktree, reset, stash, clean, or checkout authority.
- Hidden queues, hidden workers, or scheduled mutation.
- Memory-heavy local model inference that would destabilize the 16GB machine.

### Telemetry Requirements

- Node identity must be visible.
- Uptime, CPU, memory, storage, network, and stale/offline state must be recorded.
- Telemetry must distinguish advisory/search work from write-capable work.
- Any migration that changes runtime/search/subagent orchestration requires a soak-impact decision.

### SSH Requirements

- SSH user, hostname, LAN IP, and OS version must be recorded.
- Read-only SSH checks are allowed only after scope is explicit.
- Service restart commands require explicit approval.
- During Cart soak or Cart isolation, SSH commands must not touch Cart, queues, workers, approval tokens, or live map state.

### Docker/Homebrew/Script Decision

- Docker is not assumed. It must be checked for compatibility and memory cost.
- Homebrew services may be preferable for lightweight search or telemetry helpers if they are easier to inspect and stop.
- Plain scripts are preferred for first-pass advisory/search jobs when they can be run on demand and produce packets without daemon state.
- If Docker is unsupported or too heavy, use scripts or remote API search instead.

### Search Routing Policy

- Mac search jobs are read-only.
- Allowed outputs are summaries, citations, candidate packets, and blocked-reason notes.
- Search output may feed Source Proxy, Scout, Design Agent, or Britton, but it cannot apply changes.
- Source Proxy remains the approval and write gate.

### Scout Routing Policy

- Scout can receive Mac-assisted research only as advisory packets.
- Scout remains manual-controlled.
- No proxy memory writes, coding context writes, auto-discovery, scheduled writes, or promotion finalization are allowed without later approval.

### Subagent Routing Policy

- Mac subagents can act as component mapper, safety reviewer, test scribe, design packet reviewer, or Scout research helper.
- Mac subagents cannot apply code, start Cart workflows, write repo files, or trigger Source Proxy actions.
- Mac subagents report to Source Proxy or Britton through packets.

### Source Proxy Integration Policy

- Source Proxy may request a Mac advisory packet only after the request scope is explicit.
- Mac results must be displayed as proposals, research, or advisory evidence.
- Source Proxy remains the only write/apply gate.
- Mac-generated packets must show source, timestamp, confidence, allowed use, forbidden use, and manual decision needed.

### Cart Isolation Policy

- Mac Mini can never touch Cart while Cart is gated.
- If a Mac job touches Cart, map, live evidence, runtime, queue, worker, approval-token, trust-tier, or soak behavior, switch to ONE-LANE / CARTOGRAPHER ISOLATED.
- If uncertain, exclude Cart and continue only non-Cart advisory work.

### Soak Impact Policy

- Mac migration requires a soak decision if it affects runtime behavior, search orchestration, subagent orchestration, queues, workers, approval tokens, trust tiers, dashboards that control live state, or daily-driver behavior.
- Read-only advisory search does not automatically require a soak, but must stop if it touches protected Cart state.
- Any always-on Mac service needs heartbeat proof and stale/offline behavior before production use.

### Concurrency And 16GB RAM Caution

- Default to one advisory job at a time until memory evidence says otherwise.
- Avoid local LLM inference as a primary workload.
- Avoid parallel browser automation plus Docker plus indexing unless memory headroom is proven.
- Prefer bounded jobs with timeouts, logs, and manual stop instructions.

## Manual Check Template

Every plan must end with one terminal copy-paste block.

Rules:

- Use non-destructive commands unless Britton explicitly approves otherwise.
- Include exact expected output.
- Include GO/NO-GO interpretation.
- Include next plan title.
- Do not include install, test, lint, typecheck, browser, curl, Docker, runtime, queue, worker, branch, worktree, commit, push, stash, reset, clean, or checkout commands unless the plan explicitly received approval.

Template:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
grep -nE "PLAN_SPECIFIC_REQUIRED_TERMS" docs/PLAN_FILE.md
git diff -- docs/PLAN_FILE.md
```

Expected output:

- Branch and dirty tree match the plan baseline.
- Required terms are present.
- Diff is limited to the approved files.
- No forbidden runtime, queue, worker, approval-token, Cart, map, branch, worktree, commit, push, stash, reset, clean, or checkout action appears.

GO/NO-GO interpretation:

- GO only if the expected output matches and Britton accepts the manual check.
- NO-GO if output is missing, ambiguous, dirty state conflicts with scope, or forbidden authority appears.

Next plan title:

- `Plan N/24: Exact Next Plan Title`

## Britton Decision Register

| Decision | Current value | Required before |
| --- | --- | --- |
| Cart soak accepted/rejected/conditions | pending | Cart promotion or live Cart/map work |
| Cart promotion decision | pending | Cart activation |
| Cart re-soak required? | pending | Resuming Cart behavior changes |
| PR-8.3 accepted? | pending | Design Agent Plan I, downstream preflight |
| PR-8.3 marked nonblocking? | pending | Design can proceed without broad acceptance |
| Mac Mini support node approved? | pending | Mac official support-node work |
| Mac Mini search routing approved? | pending | Mac search jobs feeding proxy/scout/design |
| Mac Mini subagent routing approved? | pending | Mac advisory subagent jobs |
| Scout remains parked? | current default: yes | Any Scout lane change |
| Design Agent advisory continuation approved? | pending | Design advisory packets after PR-8.3 decision |
| Visual/CSS proof allowed? | pending | Browser/screenshot proof harness |
| Final CSS polish allowed? | pending | Final CSS work |

## Stale And Historical Doc Handling Rules

- Active docs win over historical docs.
- Latest explicit Britton instruction wins over older docs.
- Accepted closeouts prove only their scoped work.
- Docs-only closeouts do not prove execution.
- Historical root docs are context only unless a newer active roadmap cites them as authority.
- Conflicting evidence must be surfaced in the source-of-truth map or decision register.
- Do not delete or rewrite historical evidence without explicit approval. Mark superseded content instead.

## Final Output Instructions For This Codex Run

After writing this file, Codex must respond with:

### A. Short status

- File created or updated.
- No runtime/code/test/git mutation beyond allowed file write.
- Branch and HEAD.
- Dirty tree summary.

### B. Files changed

- List `docs/masterKeyProxyProduction.md` only.
- If any other file changed, explain why and mark as unexpected.

### C. What the roadmap now controls

- Cart.
- Proxy.
- Design.
- Subagents.
- Scout.
- Mac Mini.
- Search.
- Routes.
- Visual/CSS.
- Production hardening.

### D. Britton manual check block

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git diff -- docs/masterKeyProxyProduction.md
grep -nE "Plan 1/24|Plan 8/24|Plan 12/24|Plan 21/24|Plan 24/24|Mac Mini Support Node Strategy|ONE-LANE|MULTI-LANE|SOAK-HOLD|Britton Decision Register" docs/masterKeyProxyProduction.md
```

### E. Expected output

Britton should see:

- `docs/masterKeyProxyProduction.md` as the only changed file. On first creation it may appear as untracked in `git status`.
- `git diff -- docs/masterKeyProxyProduction.md` may print no output while the file is still untracked. If the file is already tracked in a later run, the diff must be limited to this roadmap only.
- Grep hits for the named plan gates, Mac Mini strategy, execution modes, and decision register.
- No runtime/code/test/git mutation beyond this docs file.

### F. Next recommended plan title

`Plan 1/24: Cartographer Post-Soak Result Acceptance And Promotion Decision Audit`
