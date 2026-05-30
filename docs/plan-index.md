# SpiritOS Plan Index

status: active

Status date: 2026-05-28

## Active /coding Readiness Direction

The active SpiritOS `/coding` readiness roadmap is `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`.

Fresh chats should follow that roadmap one plan at a time in strict PIVOT workflow. The endpoint is Codex-like feature planning readiness, not Codex-like implementation and not final CSS polish.

Older Source Proxy, Design Agent, trial, PR-8.3, safety, audit, and readiness documents are historical/supporting for this lane unless Plan 0 of the active roadmap explicitly reclassifies a narrow fact.

## Active Agent Runtime Trial Harness Direction

The active roadmap is `docs/agent-runtime-trial-harness-mac-subagent-port-master-plan-v0.1.md`.

Fresh chats should use `docs/agent-runtime-trial-harness-mac-subagent-port-new-chat-handoff-v0.1.md`, read the latest completed closeout for this roadmap, continue only the next uncompleted plan, and do not invent roadmap content.

The old Source Proxy Agent Integration Preflight roadmap is closed through Plan 12/12 and is historical/verification authority only. Do not restart it, do not start final CSS polish, and do not implement Codex-like features outside the active roadmap.

## Source Proxy Agent Integration Preflight Direction

The Source Proxy Agent Integration Preflight Build Roadmap is closed through Plan 12/12 and is ready for manual review:

- `docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md`
- `docs/source-proxy-agent-integration-preflight-plan-12-closeout-v0.1.md`

The build-first roadmap supersedes the failed docs-heavy 24-plan chain and the active direction in `docs/masterKeyProxyProduction.md`. Do not start or continue old Plan 23, start a soak, re-soak, activate Cartographer, run workers, call providers/models, apply changes, or mutate source/runtime/CSS/Cart files from the old chain.

Preflight closeout and next-roadmap boundary:

- Plans 0 through 12 are closed with GO closeouts.
- Production readiness remains NO-GO until Britton approves the next runtime/soak roadmap.
- Automatic soak remains NO-GO in the completed preflight chat.
- Next roadmap title only: `Cartographer Limited Daily-Driver Auto v1`.

## Active Plans

| Plan | Status | Role | Authority |
| --- | --- | --- | --- |
| `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md` | status: active roadmap | SpiritOS `/coding` readiness to Codex-like feature planning, beginning with Plan 0/7 | Current source of truth for `/coding` readiness; one whole plan per chat; implementation-forward after Plan 0; stops before Codex-like features and final CSS polish |
| `docs/agent-runtime-trial-harness-mac-subagent-port-master-plan-v0.1.md` | status: active roadmap | Agent Runtime Trial Harness + Mac Advisory Subagent Port v1, beginning with Plan 0/8 | Current source of truth; one approved plan at a time; no invented future scope |
| `docs/agent-runtime-trial-harness-mac-subagent-port-new-chat-handoff-v0.1.md` | status: active handoff | Fresh-chat continuation guard for the active runtime trial harness roadmap | Read master plan and latest closeout, continue next uncompleted plan only, do not restart old Source Proxy preflight |
| `docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md` | status: closed build-first roadmap | Source Proxy agent integration and Preflight Final CSS roadmap completed through Plan 12/12 | Historical/verification authority only; next runtime/soak roadmap requires Britton approval |
| `docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md` | status: historical handoff | Fresh-chat handoff used to start the completed preflight roadmap | Do not replay Plan 0 or restart the closed roadmap from this handoff |
| `docs/source-proxy-agent-integration-preflight-plan-12-closeout-v0.1.md` | status: Plan 12/12 complete | Final preflight review and soak decision closeout | GO for manual review; production readiness NO-GO; automatic soak NO-GO |
| `docs/source-proxy-agent-integration-preflight-plan-0-closeout-v0.1.md` | status: Plan 0 complete | Plan 0 closeout, old-roadmap classification, and final verification block | Historical closeout only; does not authorize archive/delete execution, source/runtime/CSS edits, Cart activation, workers, provider/model calls, apply, or auto |
| `docs/source-proxy-production-hardening-plan.md` | status: supporting reference | Source Proxy production safety boundary | Records the green safety gate; active sequencing now comes from the completed preflight closeout and the next approved roadmap |
| `docs/source-proxy-codex-class-production-master-plan-v1.0.md` | status: historical roadmap | Earlier Source Proxy `/coding` Codex-class roadmap | Superseded for active sequencing by the completed preflight roadmap; keep as reference only |
| `docs/source-proxy-codex-class-new-chat-handoff-v1.0.md` | status: historical handoff | Earlier `/coding` roadmap handoff | Do not use to start new active work without Britton approval |
| `docs/source-proxy-codex-like-active-task-ui-revamp-plan-v0.1.md` | status: historical docs-only PIVOT plan | Earlier Source Proxy `/coding` active task UI revamp plan | Superseded by the implemented preflight `/coding` work; keep as reference only |
| `docs/source-proxy-codex-like-active-task-ui-revamp-new-chat-pivot-handoff-v0.1.md` | status: historical handoff | Earlier active-task UI revamp handoff | Do not use to restart completed work |
| `docs/source-proxy-post-run-300-blocker-reduction-real-task-trial-roadmap-v0.1.md` | status: historical docs-only PIVOT roadmap | Earlier post Run 300 blocker reduction and real task trial roadmap | Superseded by the completed preflight productive-preview and diagnostic-gauntlet work |
| `docs/source-proxy-coding-trial-widget-hardening-plan-v0.1.md` | status: planning-only | Source Proxy Phase 6.2R trial widget reliability, revert harness, and productive-diff gauntlet roadmap | Does not authorize implementation, apply, commit, push, provider authority, or Phase 7 live previews |
| `docs/backend-console-usability-reset-plan-v0.1.md` | status: planning-only | `/proxy-backend` usability reset plan | Plans a plain backend operator page only; does not authorize implementation, autonomy, or execution controls |
| `docs/cartographer-map-read-only-wiring-kickoff-plan-v0.1.md` | status: planning-only | Current `/map` read-only command-center wiring kickoff | Consolidates older Cartographer map plans for the next read-only adapter hardening step; does not authorize approval tokens, writes, queue execution, commits, pushes, or autonomy |
| `docs/cartographer-map-preview-controls-plan-v0.1.md` | status: planning-only | Next `/map` preview-only controls and project-card plan | Plans display-only preview controls from GET/read-only data; does not authorize POST, writes, queue/workflow execution, git mutation, project mutation, worker starts, or autonomy |
| `docs/codingUI.md` | status: supporting reference | `/coding` UI polish reference | Supporting context only after Plan 11/12; implementation still requires a new approved roadmap |
| `docs/design-system-overhaul-master-v0.2.md` | status: planning active | Active SpiritOS design-system overhaul planning spine | Does not authorize implementation; keeps future design work Source Proxy gated |
| `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md` | status: corrected docs-only master plan complete; current decision NO-GO | Sequential PIVOT master plan for Plans A through J to bring Design Agent, subagents, safety, Source Proxy read-only design packet proof, Visual/CSS evidence, and design-system readiness to A-grade evidence before any preflight design/coding gauntlet. Plan A is already drafted docs-only. Next title only: 2/10 Design Agent + Design System A-Grade Preflight Readiness Plan B: Design System Overhaul Readiness | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-baseline-authority-source-of-truth-recovery-v0.1.md` | status: docs-only Plan A complete; GO for Plan B planning after Britton manual acceptance | 1/10 baseline, authority, and source-of-truth recovery. Records evidence inventory, Plan 0 equivalence decision, active-vs-historical doc map, grade target table, and authority boundary audit. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-closeout-v0.1.md` | status: docs-only Plan A closeout | Closes Plan A and names next title only: 2/10 Design Agent + Design System A-Grade Preflight Readiness Plan B: Design System Overhaul Readiness | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-b-design-system-overhaul-readiness-v0.1.md` | status: docs-only Plan B complete; GO for Plan C planning after Britton manual acceptance | 2/10 design-system overhaul readiness. Defines token inventory, canonical token categories, Design Vault alignment, primitive/component inventory, anatomy contracts, variant/state contracts, route CSS risk map, accessibility baseline, responsive/mobile baseline, visual target matrix, and future implementation sequencing. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-b-closeout-v0.1.md` | status: docs-only Plan B closeout | Closes Plan B and names next title only: 3/10 Design Agent + Design System A-Grade Preflight Readiness Plan C: Subagent A-Grade Evidence Upgrade | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-c-subagent-a-grade-evidence-upgrade-v0.1.md` | status: docs-only Plan C complete; GO for Plan D planning after Britton manual acceptance | 3/10 subagent A-grade evidence upgrade. Defines A-grade diagnostic packets for Source Rights Gatekeeper, Design Vault, Reverse Designer, Design Blender, Design Pack Authoring, Visual Verification, Design Coding Proposal Agent, Component Mapper, Safety Reviewer, Test Scribe, Authority Auditor, Lane Guard, Receipt/Handoff helper, and Release Steward helper. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-c-closeout-v0.1.md` | status: docs-only Plan C closeout | Closes Plan C and names next title only: 4/10 Design Agent + Design System A-Grade Preflight Readiness Plan D: Safety Boundary A-Grade Proof Plan | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-d-safety-boundary-a-grade-proof-plan-v0.1.md` | status: docs-only Plan D complete; GO for Plan E planning after Britton manual acceptance | 4/10 safety boundary A-grade proof plan. Defines source-rights rejection, authority drift rejection, no apply, no CSS/app edits, no provider/model calls, no queue/worker/autonomy, no approval-token consumption, critical prompt bank, false-block review, and final safety grade gate. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-d-closeout-v0.1.md` | status: docs-only Plan D closeout | Closes Plan D and names next title only: 5/10 Design Agent + Design System A-Grade Preflight Readiness Plan E: Source Proxy Read-Only Integration Proof | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-e-source-proxy-read-only-integration-proof-v0.1.md` | status: docs-only Plan E complete; GO for Plan F planning after Britton manual acceptance | 5/10 Source Proxy read-only integration proof. Defines packet schema compatibility, read-only receive proof, read-only display proof, read-only score proof, rejection packet proof, Source Proxy owner boundary, `/coding` trial widget or design-mode surface decision, and evidence receipt format. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-e-closeout-v0.1.md` | status: docs-only Plan E closeout | Closes Plan E and names next title only: 6/10 Design Agent + Design System A-Grade Preflight Readiness Plan F: Diagnostic Batch Harness Proof | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-f-diagnostic-batch-harness-proof-v0.1.md` | status: docs-only Plan F complete; GO for Plan G planning after Britton manual acceptance | 6/10 diagnostic batch harness proof. Defines batch report schema, 10-prompt smoke diagnostic plan, 30-prompt subagent diagnostic plan, 100-prompt design/proxy diagnostic plan, evidence counters, useful/blocked/unsafe/false-block count rules, authority drift reporting, visual evidence quality scoring, CSS/component relevance scoring, and manual review flow. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-f-closeout-v0.1.md` | status: docs-only Plan F closeout | Closes Plan F and names next title only: 7/10 Design Agent + Design System A-Grade Preflight Readiness Plan G: Visual/CSS Evidence Proof | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-g-visual-css-evidence-proof-v0.1.md` | status: docs-only Plan G complete; GO for Plan H planning after Britton manual acceptance | 7/10 visual/CSS evidence proof. Defines screenshot targets, viewport matrix, accessibility smoke checklist, token alignment proof, component relevance proof, CSS risk proof, route visual-readiness scoring, and not_started/unavailable honesty rules. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-g-closeout-v0.1.md` | status: docs-only Plan G closeout | Closes Plan G and names next title only: 8/10 Design Agent + Design System A-Grade Preflight Readiness Plan H: Source Proxy PR-8.3 Alignment | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-h-source-proxy-pr-8-3-alignment-v0.1.md` | status: docs-only Plan H complete; NO-GO for Plan I | 8/10 Source Proxy PR-8.3 alignment. Inventories PR-8.3 status, Run 10/25/100 dependencies, real low-to-mid coding task gauntlet dependency, dirty-tree evidence, receipt package requirements, and acceptance gate. PR-8.3 accepted receipts or Britton explicit nonblocking decision are missing. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-h-closeout-v0.1.md` | status: docs-only Plan H closeout; Plan I blocked | Closes Plan H and names recovery title only: Source Proxy PR-8.3 Acceptance Recovery: Fresh Run 10/25/100 And Real Coding Task Gauntlet Receipts | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-source-proxy-pr-8-3-acceptance-recovery-fresh-run-10-25-100-real-coding-task-gauntlet-receipts-v0.1.md` | status: docs-only PR-8.3 recovery plan complete; NO-GO for Plan I | Recovery plan defining the receipt package required to unblock Plan I: Britton execution authority record, Run 10, Run 25, Run 100, real low-to-mid coding task gauntlet, dirty-tree and terminal receipts, and acceptance decision record. Receipts are still missing. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-source-proxy-pr-8-3-acceptance-recovery-closeout-v0.1.md` | status: docs-only PR-8.3 recovery closeout; Plan I blocked | Closes the docs-only recovery and names next title only: Source Proxy PR-8.3 Acceptance Recovery Execution Request: Run 10 Receipt Only | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-source-proxy-pr-8-3-acceptance-recovery-execution-request-run-10-receipt-only-v0.1.md` | status: docs-only Run 10 execution request complete; NO-GO for Run 10 execution and Plan I | Defines the approval packet required before a future Run 10 receipt: explicit Britton approval scope, dirty-tree receipt, browser/manual observation, copied diagnostic receipt, authority false fields, and manual acceptance line. Receipt remains missing. | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-source-proxy-pr-8-3-acceptance-recovery-execution-request-run-10-closeout-v0.1.md` | status: docs-only Run 10 request closeout; Run 10 and Plan I blocked | Closes the docs-only Run 10 execution request and names next title only: Source Proxy PR-8.3 Acceptance Recovery Execution Approval: Run 10 Browser/Manual Receipt | No implementation authority |
| `docs/design-agent-design-system-a-grade-preflight-readiness-source-proxy-pr-8-3-acceptance-recovery-execution-approval-run-10-browser-manual-receipt-closeout-v0.1.md` | status: Run 10 browser/manual receipt closed FAIL; Plan I blocked | Records Britton-approved Run 10-only browser/manual receipt. Authority stayed false and unexpected files stayed 0, but the lifecycle stopped on unsafe failure at Trial 10 of 10. Run 10 was not accepted; Run 25 remains blocked. | No implementation authority |
| `docs/source-proxy-pr-8-3-real-low-to-mid-coding-task-gauntlet-receipt-v0.1.md` | status: real low-to-mid coding task gauntlet receipt BLOCKED; Plan I blocked | Records Britton-approved PR-8.3 real-task gauntlet receipt, dirty-tree before/after evidence, terminal verification evidence, authority-false receipt, and BLOCKED result pending disposition of outside-allowed source/test dirty-tree evidence. | No Plan I, Plan J, runtime, apply, commit, push, provider, queue, worker, branch/worktree, stash/reset/clean, or hidden autonomy authority |
| `docs/source-proxy-pr-8-3-real-low-to-mid-coding-task-gauntlet-closeout-v0.1.md` | status: real low-to-mid coding task gauntlet closeout BLOCKED; Plan I blocked | Closes the approved PR-8.3 real-task gauntlet receipt step as BLOCKED pending Britton disposition of outside-allowed source/test dirty-tree evidence. | No Plan I, Plan J, runtime, apply, commit, push, provider, queue, worker, branch/worktree, stash/reset/clean, or hidden autonomy authority |
| `docs/design-agent-ecosystem-integration-diagnostic-master-plan-v0.1.md` | status: proposed docs-only master plan | Design Agent Ecosystem Integration + Diagnostic Master Plan v0.1. Next plan: Design Agent Ecosystem Plan 0: Baseline Audit and Lane Boundary | No implementation authority |
| `docs/design-agent-ecosystem-plan-1-design-ecosystem-map-and-subagent-inventory-v0.1.md` | status: docs-only inventory complete | Design Agent Ecosystem Plan 1 inventory for design subagents/helpers. Next plan: Design Agent Ecosystem Plan 2: Design Grading Rubric And Diagnostic Report Schema | No implementation authority |
| `docs/design-agent-ecosystem-plan-2-design-grading-rubric-and-diagnostic-report-schema-v0.1.md` | status: docs-only rubric complete | Design Agent Ecosystem Plan 2 grading rubric and diagnostic report schema. Next plan: Design Agent Ecosystem Plan 3: Design System Source-Of-Truth Cleanup Plan | No implementation authority |
| `docs/design-agent-ecosystem-plan-3-design-system-source-of-truth-cleanup-plan-v0.1.md` | status: docs-only source-of-truth plan complete | Design Agent Ecosystem Plan 3 source-of-truth cleanup policy for design-system diagnostics. Next plan: Design Agent Ecosystem Plan 4: Source Rights Gatekeeper + Design Vault Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-4-source-rights-gatekeeper-design-vault-diagnostic-v0.1.md` | status: docs-only diagnostic complete | Design Agent Ecosystem Plan 4 source-rights and Design Vault diagnostic prompt set and docs/evidence grades. Next plan: Design Agent Ecosystem Plan 5: Reverse Designer Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-5-reverse-designer-diagnostic-v0.1.md` | status: docs-only diagnostic complete | Design Agent Ecosystem Plan 5 Reverse Designer diagnostic prompt set and docs/evidence grade. Next plan: Design Agent Ecosystem Plan 6: Design Blender Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-6-design-blender-diagnostic-v0.1.md` | status: docs-only diagnostic complete | Design Agent Ecosystem Plan 6 of 21 Design Blender diagnostic prompt set and docs/evidence grade. Next plan: Design Agent Ecosystem Plan 7 of 21: Design Pack Authoring Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-duplication-and-lane-integrity-audit-v0.1.md` | status: docs-only audit complete | Duplication and lane-integrity audit before Design Agent Ecosystem Plan 7 of 21 | No implementation authority |
| `docs/design-agent-ecosystem-plan-7-design-pack-authoring-diagnostic-v0.1.md` | status: docs-only diagnostic complete | Design Agent Ecosystem Plan 7 of 21 Design Pack Authoring diagnostic prompt set and docs/evidence grade. Next plan: Design Agent Ecosystem Plan 8 of 21: Visual Verification Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-8-visual-verification-diagnostic-v0.1.md` | status: docs-only diagnostic complete | Design Agent Ecosystem Plan 8 of 21 Visual Verification diagnostic prompt set and docs/evidence grade. Next plan: Design Agent Ecosystem Plan 9 of 21: Design Coding Proposal Agent Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-9-design-coding-proposal-agent-diagnostic-v0.1.md` | status: docs-only diagnostic complete | Design Agent Ecosystem Plan 9 of 21 Design Coding Proposal Agent diagnostic prompt set and docs/evidence grade. Next plan: Design Agent Ecosystem Plan 10 of 21: Component Mapper, Safety Reviewer, and Test Scribe Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-10-component-mapper-safety-reviewer-test-scribe-diagnostic-v0.1.md` | status: docs-only diagnostic complete | Design Agent Ecosystem Plan 10 of 21 Component Mapper, Safety Reviewer, and Test Scribe diagnostic prompt set and docs/evidence grades. Next plan: Design Agent Ecosystem Plan 11 of 21: Authority Auditor + Lane Guard Fail-Closed Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-11-authority-auditor-lane-guard-fail-closed-diagnostic-v0.1.md` | status: docs-only diagnostic complete | Design Agent Ecosystem Plan 11 of 21 Authority Auditor + Lane Guard fail-closed diagnostic prompt set and docs/evidence grades. Next plan: Design Agent Ecosystem Plan 12 of 21: Design Agent To Source Proxy Read-Only Bridge Plan | No implementation authority |
| `docs/design-agent-ecosystem-plan-12-design-agent-to-source-proxy-read-only-bridge-plan-v0.1.md` | status: docs-only bridge plan complete | Design Agent Ecosystem Plan 12 of 21 Design Agent To Source Proxy Read-Only Bridge contract and docs/evidence grade. Next plan: Design Agent Ecosystem Plan 13 of 21: /coding Trial Widget Design-Mode Diagnostic Plan | No implementation authority |
| `docs/design-agent-ecosystem-plan-13-coding-trial-widget-design-mode-diagnostic-plan-v0.1.md` | status: docs-only diagnostic plan complete | Design Agent Ecosystem Plan 13 of 21 `/coding` Trial Widget Design-Mode diagnostic plan and docs/evidence grade. Next plan: Design Agent Ecosystem Plan 14 of 21: 10-Prompt Design Packet Smoke Test | No implementation authority |
| `docs/design-agent-ecosystem-plan-14-10-prompt-design-packet-smoke-test-v0.1.md` | status: docs-only smoke-test plan complete | Design Agent Ecosystem Plan 14 of 21 10-Prompt Design Packet Smoke Test fixtures and dry-run readiness. Next plan: Design Agent Ecosystem Plan 15 of 21: 30-Prompt Design Ecosystem Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-15-30-prompt-design-ecosystem-diagnostic-v0.1.md` | status: docs-only diagnostic plan complete | Design Agent Ecosystem Plan 15 of 21 30-Prompt Design Ecosystem Diagnostic prompt bank and coverage reconciliation. Next plan: Design Agent Ecosystem Plan 16 of 21: 100-Prompt Design And Proxy Integration Diagnostic | No implementation authority |
| `docs/design-agent-ecosystem-plan-16-100-prompt-design-and-proxy-integration-diagnostic-v0.1.md` | status: docs-only diagnostic plan complete | Design Agent Ecosystem Plan 16 of 21 100-Prompt Design And Proxy Integration Diagnostic prompt bank and read-only report mapping. Next plan: Design Agent Ecosystem Plan 17 of 21: Visual/CSS Evidence Harness Readiness | No implementation authority |
| `docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md` | status: docs-only readiness plan complete | Design Agent Ecosystem Plan 17 of 21 Visual/CSS Evidence Harness Readiness evidence schema, responsive/accessibility/token criteria, and no-execution boundaries. Next plan: Design Agent Ecosystem Plan 18 of 21: Controlled Design-Code Preview Lane | No implementation authority |
| `docs/design-agent-ecosystem-plan-18-controlled-design-code-preview-lane-v0.1.md` | status: docs-only preview-lane plan complete | Design Agent Ecosystem Plan 18 of 21 Controlled Design-Code Preview Lane scope, approval separation, evidence requirements, and residual-risk boundaries. Next plan: Design Agent Ecosystem Plan 19 of 21: 300-Prompt Combined Coding/Design Gauntlet | No implementation authority |
| `docs/design-agent-ecosystem-plan-19-300-prompt-combined-coding-design-gauntlet-v0.1.md` | status: docs-only gauntlet plan complete | Design Agent Ecosystem Plan 19 of 21 300-Prompt Combined Coding/Design Gauntlet prompt bank, run-readiness fields, and scoring requirements. Next plan requires Britton approval: Design Agent Ecosystem Plan 20 of 21 final readiness gate | No implementation authority |
| `docs/design-agent-ecosystem-plan-20-full-design-agent-ecosystem-production-daily-use-preflight-css-polish-readiness-gate-v0.1.md` | status: docs-only final readiness gate complete; NO-GO | Design Agent Ecosystem Plan 20 of 21 final readiness gate. Decision: NO-GO for merge and production CSS polish. Remediation title only: Final Gate Evidence Recovery And Lane-Merge Prerequisites | No implementation authority |
| `docs/design-agent-ecosystem-remediation-plan-final-gate-evidence-recovery-and-lane-merge-prerequisites-v0.1.md` | status: docs-only remediation plan complete | Remediation sequencing after Plan 20 NO-GO. Identifies missing final-gate evidence and title-only future remediation steps. | No implementation authority |
| `docs/design-systems-master-v0.1.md` | status: planning complete | Manual-first Design Intelligence Stack plan | Does not authorize implementation; next increment requires explicit approval |
| `productionProxy.md` | status: historical | Uploaded staging copy | Historical only; follow the durable repo copy instead |

## Design System Status Summary

`docs/design-system-overhaul-master-v0.2.md` is the active planning spine for the SpiritOS design-system overhaul. It keeps future design-system work manual-controlled and Source Proxy gated.

Current handling:

- v0.2 is planning-only and does not authorize implementation.
- For design-system overhaul planning, `docs/design-system-overhaul-master-v0.2.md` is the current source of truth.
- v0.1 design intelligence docs remain supporting references and history.
- Design Vault artifacts are proposal evidence, not runtime or apply authority.
- Reverse Designer, Design Blender, Scout design intake, visual verification, and design apply lane work remain contract/scaffold level until later approved increments.
- No production UI, route, package, Scout runtime, Source Proxy runtime, or Cartographer authority change is authorized by the design-system plan.

## Source Proxy Plan Authority Map

The green Source Proxy safety gate passed on 2026-05-20 based on user-provided evidence: global safety regression passed, Source Proxy tests passed, Scout backend tests passed, Cartographer safety passed, dashboard smoke passed, no unexpected mutation occurred, no unexpected Level 2 evidence appeared, no commit occurred during the run, HEAD stayed stable at `3e55bdc`, and `main` matched `origin/main` at `3e55bdc`.

### Current Source Proxy Production Roadmap

| Plan | Handling |
| --- | --- |
| `docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md` | Closed build-first Source Proxy agent integration and Preflight Final CSS roadmap. Plans 0 through 12 are complete. |
| `docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md` | Historical handoff. Do not use it to restart Plan 0 or replay the completed roadmap. |
| `docs/source-proxy-agent-integration-preflight-plan-0-closeout-v0.1.md` | Plan 0 closeout and old-roadmap classification. Archive/delete candidates require future Britton approval before action. |
| `docs/source-proxy-agent-integration-preflight-plan-12-closeout-v0.1.md` | Final preflight review and soak decision. Manual review GO; production readiness NO-GO; automatic soak NO-GO. |
| `docs/source-proxy-codex-class-production-master-plan-v1.0.md` | Superseded for active Source Proxy agent integration sequencing by the build-first preflight roadmap. Keep as historical/reference context only. |
| `docs/source-proxy-codex-class-new-chat-handoff-v1.0.md` | Superseded handoff for active Source Proxy agent integration sequencing. Keep as historical/reference context only. |
| `docs/source-proxy-coding-trial-widget-hardening-plan-v0.1.md` | Planning-only Phase 6.2R hardening lane for trial widget reliability, audit evidence, safe revert design, and productive-diff gauntlet readiness before Phase 7. |
| `docs/source-proxy-codex-style-ui-reduction-pr-8-3-gauntlet-master-plan-v0.1.md` | Planning-only PIVOT bridge for `/coding` Codex-style UI reduction and fresh PR-8.3 proof gauntlet preparation. It does not authorize implementation, browser proof execution, wrapper work, final CSS, provider calls, apply, execute-approved, commit, push, or cleanup. |
| `docs/source-proxy-codex-like-active-task-ui-revamp-plan-v0.1.md` | Docs-only PIVOT plan for moving `/coding` from cockpit/dashboard mode to a Codex-like active task window. It does not authorize implementation, browser proof execution, wrapper work, final CSS, provider calls, apply, execute-approved, commit, push, or cleanup. |
| `docs/source-proxy-codex-like-active-task-ui-revamp-new-chat-pivot-handoff-v0.1.md` | Historical handoff. Do not use it to restart the old active-task UI revamp; current `/coding` readiness sequencing comes from `docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md`. |
| `docs/source-proxy-post-run-300-blocker-reduction-real-task-trial-roadmap-v0.1.md` | Docs-only PIVOT roadmap after a clean-safety but all-blocked Run 300. It sequences blocker overclassification reduction, real task trial packets, a preview-only real task widget and runner, Codex-like feature-gap prep, and preflight CSS readiness gates. It does not authorize implementation, provider calls, queues, workers, Source Proxy shell actions, apply, commit, push, Cartographer activation, design apply, production CSS, or cleanup. |

### Active Source Of Truth

| Plan | Handling |
| --- | --- |
| `docs/source-proxy-agent-integration-preflight-build-roadmap-v0.1.md` | Closed source of truth for the completed Source Proxy agent integration preflight. |
| `docs/source-proxy-agent-integration-preflight-new-chat-handoff-v0.1.md` | Historical fresh-chat handoff for the now-completed build-first roadmap. |
| `docs/source-proxy-agent-integration-preflight-plan-0-closeout-v0.1.md` | Plan 0 result and exact old-roadmap classification; no archive/delete execution authority. |
| `docs/source-proxy-agent-integration-preflight-plan-12-closeout-v0.1.md` | Plan 12/12 final review and soak decision; next roadmap title only is `Cartographer Limited Daily-Driver Auto v1`. |
| `docs/source-proxy-production-hardening-plan.md` | Supporting production authority and safety boundary. It records the green gate, but it no longer supersedes the build-first Source Proxy agent integration roadmap. |
| `docs/codingUI.md` | Supporting `/coding` UI polish reference only. Future use requires a new approved roadmap and existing Source Proxy contracts/gates. |

### Completed Preflight Closeouts

| Plan | Handling |
| --- | --- |
| `docs/source-proxy-agent-integration-preflight-plan-0-closeout-v0.1.md` | Plan 0 roadmap reset and old-roadmap classification. |
| `docs/source-proxy-agent-integration-preflight-plan-1-closeout-v0.1.md` | Plan 1/12 executable baseline and scope lock. |
| `docs/source-proxy-agent-integration-preflight-plan-2-closeout-v0.1.md` | Plan 2/12 productive bounded-diff preview verification. |
| `docs/source-proxy-agent-integration-preflight-plan-3-closeout-v0.1.md` | Plan 3/12 Codex-like coding cockpit. |
| `docs/source-proxy-agent-integration-preflight-plan-4-closeout-v0.1.md` | Plan 4/12 Mac Mini, web search, and Scout research lane. |
| `docs/source-proxy-agent-integration-preflight-plan-5-closeout-v0.1.md` | Plan 5/12 subagent integration v1. |
| `docs/source-proxy-agent-integration-preflight-plan-6-closeout-v0.1.md` | Plan 6/12 Design Agent and Design Vault integration. |
| `docs/source-proxy-agent-integration-preflight-plan-7-closeout-v0.1.md` | Plan 7/12 Cartographer proxy visibility and controlled preview. |
| `docs/source-proxy-agent-integration-preflight-plan-8-closeout-v0.1.md` | Plan 8/12 human-controlled apply lane. |
| `docs/source-proxy-agent-integration-preflight-plan-9-closeout-v0.1.md` | Plan 9/12 combined coding, design, research, and Cart diagnostic gauntlet. |
| `docs/source-proxy-agent-integration-preflight-plan-10-closeout-v0.1.md` | Plan 10/12 visual proof harness and before screenshots. |
| `docs/source-proxy-agent-integration-preflight-plan-11-closeout-v0.1.md` | Plan 11/12 final CSS/UI polish using visual proof. |
| `docs/source-proxy-agent-integration-preflight-plan-12-closeout-v0.1.md` | Plan 12/12 preflight review and soak decision. |

### Superseded 24-Plan Chain Cleanup Classification

These docs are commit-worthy historical evidence and should not be treated as active roadmap authority after the Source Proxy Agent Integration Preflight closeout:

| Plan | Handling |
| --- | --- |
| `docs/masterKeyProxyProduction.md` | Superseded traffic-control roadmap. Preserved with an explicit supersession notice. |
| `docs/cartographer-live-evidence/cartographer-plan-1-24-post-soak-acceptance-promotion-audit-v0.1.md` | Historical Cartographer post-soak audit evidence. |
| `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md` | Historical Mac Mini support-node baseline. |
| `docs/mac-mini-workload-placement-matrix-plan-3-24-v0.1.md` | Historical Mac workload placement matrix. |
| `docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md` | Historical Mac/search/Scout intake planning packet. |
| `docs/mac-mini-subagent-host-feasibility-plan-5-24-v0.1.md` | Historical Mac subagent feasibility packet. |
| `docs/mac-mini-remote-worker-control-telemetry-dashboard-plan-6-24-v0.1.md` | Historical Mac telemetry/control planning packet. |
| `docs/cartographer-live-evidence/cartographer-plan-7-24-activation-boundary-resoak-decision-v0.1.md` | Historical Cartographer activation boundary and re-soak decision. |
| `docs/source-proxy-pr-8-3-acceptance-or-nonblocking-decision-plan-8-24-v0.1.md` | Historical Source Proxy PR-8.3 acceptance decision packet. |
| `docs/source-proxy-run-300-blocker-reduction-plan-9-24-v0.1.md` | Historical Run 300 blocker-reduction packet. |
| `docs/source-proxy-coding-active-task-cockpit-operator-clarity-plan-10-24-v0.1.md` | Historical `/coding` active task cockpit clarity packet. |
| `docs/source-proxy-production-hardening-consolidation-plan-11-24-v0.1.md` | Historical Source Proxy production-hardening consolidation packet. |
| `docs/design-agent-a-grade-dependency-unlock-plan-12-24-v0.1.md` | Historical Design Agent dependency-unlock packet. |
| `docs/design-agent-ecosystem-remediation-plan-13-24-v0.1.md` | Historical Design Agent remediation packet. |
| `docs/design-subagent-fleet-preintegration-plan-14-24-v0.1.md` | Historical design subagent fleet preintegration packet. |
| `docs/scout-manual-controlled-intelligence-lane-plan-15-24-v0.1.md` | Historical Scout manual-controlled intelligence lane packet. |
| `docs/surface-ownership-chat-oracle-dashboard-plan-16-24-v0.1.md` | Historical surface ownership packet. |
| `docs/map-cartographer-ui-integration-gate-plan-17-24-v0.1.md` | Historical map and Cartographer UI integration gate. |
| `docs/controlled-multi-agent-subagent-orchestration-boundary-plan-18-24-v0.1.md` | Historical preview-only orchestration boundary packet. |
| `docs/controlled-action-authority-approval-token-ladder-plan-19-24-v0.1.md` | Historical authority/token ladder design packet. |
| `docs/visual-evidence-browser-proof-harness-plan-20-24-v0.1.md` | Historical visual proof harness contract. |
| `docs/final-css-polish-gate-plan-21-24-v0.1.md` | Historical final CSS gate review. |
| `docs/preflight-production-readiness-review-plan-22-24-v0.1.md` | Historical production-readiness review with production readiness NO-GO. |

### Active Supporting References

| Plan | Handling |
| --- | --- |
| `docs/source-proxy-regression-matrix.md` | Keep as the regression command and safety guarantee map. |
| `docs/source-proxy-daily-use-runbook.md` | Keep as the operator workflow reference. |
| `docs/source-proxy-remote-manual-checks.md` | Keep as the remote/mobile/manual check reference. |
| `docs/source-proxy-worktree-study.md` | Keep as the worktree and branch-safety reference. |
| `docs/continue-lite-console-plan.md` | Keep as supporting reference only where it describes implemented `/coding` console history and read-only history patterns. |

### Scout Manual-Controlled Stop Points

| Plan | Handling |
| --- | --- |
| `docs/scout-v0-6-dry-run-closeout-index-and-stop-point.md` | Scout v0.6 dry-run-only lane is parked/manual-controlled. It does not authorize proxy intake, proxy memory writes, coding context writes, promotion finalization, background workers, scheduled writes, commits, or pushes. |
| `docs/scout-v0-7-reopen-decision-record.md` | Scout v0.7 decision keeps Scout-to-Proxy import parked. It authorizes planning for read-only review ergonomics only and does not reopen proxy intake, proxy memory writes, coding context writes, promotion finalization, background workers, scheduled writes, commits, or pushes. |
| `docs/scout-v0-7-manual-controlled-review-ergonomics-plan.md` | Scout v0.7 review ergonomics plan is planning/manual-controlled. It only plans read-only review clarity and does not authorize source automation, discovery execution, packet promotion, proxy intake, proxy memory writes, coding context writes, background workers, scheduled writes, commits, or pushes. |
| `docs/scout-v0-7-diagnostics-summary-copy.md` | Scout v0.7 diagnostics summary copy is active/manual-controlled. It only adds live read-only Scout safety copy to the dashboard and `/intelligence`; it does not authorize source automation, discovery execution, packet promotion, proxy intake, proxy memory writes, coding context writes, background workers, scheduled writes, commits, or pushes. |
| `docs/scout-v0-7-review-ergonomics-stop-point.md` | Scout v0.7 review ergonomics is parked/manual-controlled. It records the stop point after read-only review clarity work and requires a new operator decision before any further Scout increment. |
| `docs/scout-v0-8-next-lane-decision-record.md` | Scout v0.8 next lane decision record is planning/manual-controlled. It chooses to keep Scout parked until a later explicit lane selection and does not authorize Scout implementation, automation, proxy memory writes, coding context writes, commits, or pushes. |
| `docs/scout-v0-8-closeout-summary.md` | Scout v0.8 closeout summary is closed/manual-controlled. It records Scout as parked with green read-only gates, zero backlog, dry-run-only closeout mode, and no proxy memory, coding context, or promotion finalization writes. |
| `docs/scout-v0-9-next-phases-plan.md` | Scout v0.9 next phases plan is planning/manual-controlled. It selects Manual-Controlled Lane Expansion and keeps autonomy, scheduled writes, proxy memory writes, coding context writes, hidden workers, commits, and pushes forbidden. |
| `docs/scout-v0-9-lane-contract-schema.md` | Scout v0.9 increment 0.3.1 is planning/manual-controlled. It defines the lane contract schema only and keeps all Scout writes, autonomy, scheduled work, hidden workers, commits, and pushes forbidden. |
| `docs/scout-v0-9-dry-run-receipt-format.md` | Scout v0.9 increment 0.3.2 is planning/manual-controlled. It defines advisory dry-run receipt fields only and does not authorize execution, receipt emission, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-review-decision-labels.md` | Scout v0.9 increment 0.3.3 is planning/manual-controlled. It defines advisory review decision labels only and does not authorize source mutation, packet promotion, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-phase-0-3-closeout.md` | Scout v0.9 increment 0.3.4 is closed/manual-controlled. It closes lane contracts, dry-run receipts, and review labels as docs-only and keeps all writes, autonomy, scheduled work, hidden workers, commits, and pushes forbidden. |
| `docs/scout-v0-9-design-intake-plan.md` | Scout v0.9 increment 1.1 is planning/manual-controlled. It plans stored-only, manual-fed design intake and does not authorize crawling, auto-discovery, design extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-design-pattern-taxonomy.md` | Scout v0.9 increment 1.2 is planning/manual-controlled. It defines design pattern taxonomy for manual stored-only references and does not authorize crawling, extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-design-review-packet-format.md` | Scout v0.9 increment 1.3 is planning/manual-controlled. It defines advisory design review packet fields and does not authorize analysis execution, code generation, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-phase-1-closeout.md` | Scout v0.9 increment 1.4 is closed/manual-controlled. It closes stored-only design intake planning and does not authorize implementation, crawling, extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-review-grouping-plan.md` | Scout v0.9 increment 2.1 is planning/manual-controlled. It plans advisory review grouping only and does not authorize source mutation, discovery, extraction, promotion, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-better-summaries-plan.md` | Scout v0.9 increment 2.2 is planning/manual-controlled. It defines advisory review summary fields only and does not authorize automatic generation, mutation, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-operator-decision-flow.md` | Scout v0.9 increment 2.3 is planning/manual-controlled. It defines human operator decisions only and does not authorize runtime source mutation, discovery, extraction, promotion, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-phase-2-closeout.md` | Scout v0.9 increment 2.4 is closed/manual-controlled. It closes review intelligence planning and does not authorize source mutation, discovery, extraction, promotion, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-manual-triggered-discovery-boundary.md` | Scout v0.9 increment 3.1 is planning/manual-controlled. It defines a manual-trigger-only discovery boundary and does not authorize scheduled discovery, background workers, source activation, extraction, writes, autonomy, commits, or pushes. |
| `docs/scout-v0-9-source-allowlist-model.md` | Scout v0.9 increment 3.2 is planning/manual-controlled. It defines source lifecycle states only and does not authorize source record writes, activation, discovery, extraction, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-discovery-budget-rate-limits.md` | Scout v0.9 increment 3.3 is planning/manual-controlled. It defines conservative discovery budgets only and does not authorize discovery execution, source activation, extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-phase-3-closeout.md` | Scout v0.9 increment 3.4 is closed/manual-controlled. It closes safe discovery prep and does not authorize discovery execution, crawling, source activation, extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-context-handoff-packet.md` | Scout v0.9 increment 4.1 is planning/manual-controlled. It defines an advisory context handoff packet only and does not authorize proxy intake, proxy memory writes, coding context writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-approval-gate-requirements.md` | Scout v0.9 increment 4.2 is planning/manual-controlled. It defines future human approval requirements only and does not authorize proxy intake, proxy memory writes, coding context writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-integration-risk-table.md` | Scout v0.9 increment 4.3 is planning/manual-controlled. It lists integration risks and mitigations only and does not authorize proxy intake, proxy memory writes, coding context writes, autonomy, scheduled work, hidden workers, commits, or pushes. |

### Historical Or Reference Only

| Plan | Handling |
| --- | --- |
| `productionProxy.md` | Historical uploaded staging copy. It may explain old sequencing, but the durable repo authority is `docs/source-proxy-production-hardening-plan.md`. |
| `docs/source-proxy-closeout-consolidation-plan.md` | Historical closeout/consolidation planning after the green gate. |
| `docs/source-proxy-hardening-closeout.md` | Historical closeout evidence and summary. |
| `docs/aionui-reference-study.md` | UX/reference research only. |
| `docs/agent-wrapper-reference-study.md` | UX/provider-reference research only. |
| `docs/spirit-cowork-gap-report.md` | Historical gap report only. |
| `docs/cartographer-level-1-autonomy-plan.md`, `docs/cartographer-level-2-autonomy-plan.md`, `docs/cartographer-level-3-autonomy-plan.md` | Historical phase plans unless a future active plan explicitly reopens a specific bounded increment. |

### Deferred, Not Active

The following topics are visible but inactive. Do not promote them into implementation work from stale docs:

- AionUi bridge
- Cowork console
- provider-layer expansion
- scheduled provider tasks
- native mobile app
- autopilot or autonomy features
- default Codex promotion
- commit/push automation

`proxyCLI.md` is retired, intentionally absent, and must not be recreated. Phase 11 language is historical and must not be used to invent new increments.

## Retired Or Historical Plans

| Plan Or Topic | Status | Handling |
| --- | --- | --- |
| `proxyCLI.md` | status: historical | Retired and intentionally deleted |
| Phase 11 language | status: historical | Do not treat as next action |
| AionUi bridge | status: deferred | Do not build unless a later active plan explicitly reopens it |
| Spirit Cowork Console | status: deferred | Do not build unless a later active plan explicitly reopens it |
| Provider-layer implementation | status: deferred | Do not build unless a later active plan explicitly reopens it |

## Reference Research

| Document | Status | Handling |
| --- | --- | --- |
| `docs/aionui-reference-study.md` | status: historical | Research input only |
| `docs/agent-wrapper-reference-study.md` | status: historical | Research input only |
| `docs/spirit-cowork-gap-report.md` | status: historical | Gap report only |

These files are research inputs. They do not authorize provider-layer implementation, AionUi integration, or Cowork Console work.

## Resolution Rule

When plan documents conflict, follow the single `status: active` Source Proxy plan above. Treat `status: historical` documents as evidence and `status: deferred` topics as visible but inactive.

## Old Plan Cleanup Queue

No deletion was performed during this planning pass. Archive or deletion work requires explicit user approval unless a later pass lists exact files and receives permission.

| File path | Category | Reason | Risk if deleted | Recommended action | User permission required |
| --- | --- | --- | --- | --- | --- |
| `docs/source-proxy-production-hardening-plan.md` | keep active | Current Source Proxy authority and green-gate status. | High: deleting would remove the safety boundary and source of truth. | Keep active. | No |
| `docs/codingUI.md` | keep active | Next active `/coding` UI polish plan. | High: deleting would remove the next approved track. | Keep active. | No |
| `docs/source-proxy-regression-matrix.md` | keep reference | Maps safety guarantees to commands and failure meanings. | Medium: deleting would make future gate checks less reviewable. | Keep reference. | No |
| `docs/source-proxy-daily-use-runbook.md` | keep reference | Operator workflow for daily Source Proxy use. | Medium: deleting would remove practical manual workflow guidance. | Keep reference. | No |
| `docs/source-proxy-remote-manual-checks.md` | keep reference | Codex mobile, SSH, and remote manual check reference. | Medium: deleting would weaken remote review workflow guidance. | Keep reference. | No |
| `docs/source-proxy-worktree-study.md` | keep reference | Captures worktree/branch safety guidance. | Medium: deleting would lose context for future branch/worktree decisions. | Keep reference. | No |
| `docs/continue-lite-console-plan.md` | keep reference | Useful where it records implemented read-only console history and workflow memory ideas. | Low/medium: deleting could lose UI history context. | Keep reference, cite only when aligned with current gates. | No |
| `productionProxy.md` | mark historical | Uploaded staging copy with old sequencing and duplicate plan text. | Low/medium: deleting could lose provenance for old plan decisions. | Archive candidate after review; do not use as active authority. | Yes |
| `docs/source-proxy-closeout-consolidation-plan.md` | mark historical | Closeout planning now superseded by green-gate status. | Low: mostly planning provenance. | Keep historical or archive with closeout docs. | Yes |
| `docs/source-proxy-hardening-closeout.md` | mark historical | Green-gate closeout/evidence record. | Medium: deleting could remove useful evidence summary. | Keep historical evidence, not active plan. | Yes |
| `docs/spirit-cowork-gap-report.md` | mark historical | Contains old Phase 11/Cowork/AionUi language but also explicitly defers it. | Low/medium: deleting could lose research rationale. | Keep historical or archive under research if archive structure is approved. | Yes |
| `docs/aionui-reference-study.md` | mark historical | Toy-repo AionUi UX research only. | Low: deleting loses UX notes. | Keep as reference research. | Yes |
| `docs/agent-wrapper-reference-study.md` | mark historical | Provider-wrapper research with broad future ideas. | Low: deleting loses comparison notes. | Keep as reference research. | Yes |
| `docs/aionui-bridge-reassessment.md` | mark historical | Explicit no-build decision for AionUi bridge. | Medium: deleting could make the deferral less discoverable. | Keep historical decision record. | Yes |
| `docs/spirit-cowork-console-reassessment.md` | mark historical | Explicit no-build decision for separate Cowork console. | Medium: deleting could make the deferral less discoverable. | Keep historical decision record. | Yes |
| `docs/scheduled-provider-tasks-design.md` | mark historical/deferred | Explicitly defers scheduled provider tasks. | Medium: deleting could hide why scheduled work is inactive. | Keep as deferred decision record. | Yes |
| `docs/limited-autopilot-design.md` | mark historical/deferred | Explicitly defers limited autopilot. | Medium: deleting could hide autopilot boundaries. | Keep as deferred decision record. | Yes |
| `docs/spiritos-mobile-surface-decision.md` | mark historical/deferred | Defers native mobile app while keeping responsive `/coding` active. | Low/medium: deleting could revive native app confusion. | Keep as deferred decision record. | Yes |
| `docs/cartographer-level-1-autonomy-plan.md` | archive candidate | Old phase plan; may contain implemented or superseded autonomy details. | Medium: deleting could lose historical Cartographer context. | Archive only after a Cartographer docs review. | Yes |
| `docs/cartographer-level-2-autonomy-plan.md` | archive candidate | Old phase plan; superseded by current safety cap and green-gate status. | Medium: deleting could lose historical autonomy constraints. | Archive only after a Cartographer docs review. | Yes |
| `docs/cartographer-level-3-autonomy-plan.md` | archive candidate | Old phase plan; not active for `/coding` polish. | Medium: deleting could lose historical execution-gate rationale. | Archive only after a Cartographer docs review. | Yes |
| `proxyCLI.md` | delete candidate if found | Retired and intentionally absent; recreating it would be misleading. | None if absent; high confusion risk if recreated. | Keep absent. If it reappears as a stale copy, request permission to delete. | Yes |
