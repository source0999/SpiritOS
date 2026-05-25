# Design Agent + Design System A-Grade Preflight Readiness Master Plan Of Plans v0.1

Status: corrected docs-only PIVOT master plan

Owner: Britton

Date: 2026-05-24

Decision: NO-GO for preflight design/coding gauntlet until Plans A through J close GO with evidence.

Correction status: This is the top-level roadmap for Plans A through J. Plan A has already been drafted docs-only as a child/detail artifact at `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-baseline-authority-source-of-truth-recovery-v0.1.md` with closeout at `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-closeout-v0.1.md`. Plans B through J are represented in this master roadmap and are not started as standalone execution.

## 1. Purpose

This document is the sequential master plan of plans for upgrading the Design Agent, Design Agent helper fleet, Source Proxy read-only design packet bridge, visual/CSS evidence lane, and actual reusable design system to A-grade evidence before any preflight design/coding gauntlet.

This plan does not implement runtime behavior. It does not run Source Proxy, edit `/coding`, edit CSS, edit app routes, edit providers, execute queues/workers, consume approval tokens, apply changes, commit, push, branch, stash, reset, clean, or create hidden autonomy.

## 2. Evidence Analyzed

- `docs/design-agent-ecosystem-remediation-plan-final-gate-evidence-recovery-and-lane-merge-prerequisites-v0.1.md`
- `docs/design-agent-ecosystem-remediation-plan-closeout-v0.1.md`
- `docs/design-agent-ecosystem-plan-20-full-design-agent-ecosystem-production-daily-use-preflight-css-polish-readiness-gate-v0.1.md`
- `docs/design-agent-ecosystem-plan-20-closeout-v0.1.md`
- `docs/design-agent-ecosystem-integration-diagnostic-master-plan-v0.1.md`
- `docs/design-agent-fleet-preintegration-master-plan-v0.1.md`
- `docs/design-agent-fleet-daf-5-readiness-decision-v0.1.md`
- `docs/design-agent-fleet-daf-6-future-gate-definition-v0.1.md`
- `docs/design-system-overhaul-master-v0.2.md`
- `docs/source-proxy-preflight-readiness-master-roadmap-v0.1.md`
- `docs/source-proxy-codex-style-ui-reduction-pr-8-3-gauntlet-master-plan-v0.1.md`
- `docs/source-proxy-preflight-pr-8-real-preflight-coding-workflow-proof-v0.1.md`
- `docs/source-proxy-preflight-pr-9-design-cartographer-scout-dependency-alignment-v0.1.md`
- `docs/source-proxy-preflight-pr-10-wrapper-final-css-decision-gate-v0.1.md`
- `docs/plan-index.md`

Related anchor searches were reviewed for Plan 0 Evidence Recovery, NO-GO, read-only receive, display proof, score proof, 100-prompt, 300-prompt, Source Proxy integration, Visual/CSS, Design Vault, Source Rights Gatekeeper, Design Blender, Reverse Designer, Design Pack Authoring, Visual Verification, Authority Auditor, Lane Guard, Test Scribe, Component Mapper, daily-use readiness, and preflight CSS polish.

## 3. Standing Authority Boundary

Allowed in this document:

- Create this docs-only master plan.
- Create the docs-only planning closeout.
- Add a narrow index entry if `docs/plan-index.md` has an appropriate section.
- Run docs-safe verification commands.

Forbidden in this document and inherited by every future plan unless Britton approves a later exact implementation or execution plan:

- No source code edits.
- No CSS edits.
- No app route edits.
- No test edits in this task.
- No runtime integration.
- No provider/model calls.
- No queue or worker execution.
- No Source Proxy execution.
- No `/coding` UI edits.
- No approval-token changes.
- No apply, execute-approved, commit, push, branch, worktree, stash, reset, clean, checkout, or git mutation.
- No hidden autonomy.
- No background task claims.
- No claim that any gauntlet succeeded.
- No claim that missing evidence exists.

Design Agent remains proposal-only. Coding Agent and Source Proxy remain the owners of diff, preview, approval, apply, and verification workflows.

## 4. Required Grading Model

| Category | Current grade | Target grade | Evidence required for A | Owner lane | Blocking docs | Allowed next plan | Current GO/NO-GO |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Design-agent concept and architecture | B+ to A- planning | A | Active source-of-truth map, packet architecture, proposal-only contracts, handoff boundaries, and accepted Plan A closeout | Design Agent docs lane | Plan 20 NO-GO, remediation blocker table, missing Plan 0 closeout | Plan B after Plan A acceptance | GO for Plan B planning only; NO-GO for final readiness |
| Subagent docs/evidence coverage | B to A- by lane | A | Per-subagent role, input, output, authority, fail-closed behavior, rejection cases, acceptable and blocked packet examples, manual verification, and diagnostic evidence | Design Agent helper lane | Plan 20 grade review, DAF-5/DAF-6 preintegration boundaries | Plan C after Plan B | NO-GO |
| Safety boundaries | B+ docs to A- preintegration | A | Executed or replayable proof for rights rejection, authority drift rejection, no apply, no CSS/app edit, no provider/model call, no queue/worker/autonomy, and no approval-token consumption | Safety and authority lane | Plan 20 critical safety blockers, DAF boundary docs | Plan D after Plan C | NO-GO |
| Source Proxy integration readiness | C- blocked | A for read-only design packet receive/display/score only | Packet schema compatibility, read-only receive proof, read-only display proof, read-only score proof, rejection packet proof, Source Proxy owner boundary, and evidence receipt | Source Proxy read-only bridge lane | Plan 12 docs-only bridge, Plan 20 not_started receive/display/score, PR-9 proposal-only boundary | Plan E after Plan D | NO-GO |
| Design system readiness | C actual reusable system | A- minimum before gauntlet | Token inventory, canonical token categories, Design Vault alignment, primitive/component inventory, anatomy contracts, variant/state contracts, CSS risk map, accessibility, responsive/mobile, and visual evidence matrix | Design system lane | Design-system v0.2 current-state summary | Plan B after Plan A | NO-GO |
| Preflight design/coding gauntlet readiness | NO-GO | A-grade preflight evidence gate | Plans A through H accepted, 100-prompt diagnostic status validated, 300-prompt mechanism approved but not run until gate, and no unresolved safety blockers | Combined design/coding readiness lane | Plan 20 final NO-GO, PR-8.3 dependency docs | Plan I after Plan H | NO-GO |

## 4.1 Plan Sequence Matrix

| Plan | Purpose | Current grade | Target grade | Owner lane | Prerequisites | Status | Next authorized title only |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1/10 Plan A: Baseline, Authority, And Source-Of-Truth Recovery | Recover or replace missing Plan 0 baseline, map active sources, reset grades, and audit authority. | B+ planning baseline with missing Plan 0 artifact | A-grade source-of-truth baseline for planning | Design Agent docs lane | Master plan accepted by Britton | Already drafted docs-only in Plan A child docs; pending Britton acceptance for next plan | `2/10: Design Agent + Design System A-Grade Preflight Readiness Plan B: Design System Overhaul Readiness` |
| 2/10 Plan B: Design System Overhaul Readiness | Define design-system readiness before subagent A-grade proof. | C actual reusable design system | A- minimum before gauntlet | Design system lane | Plan A accepted | Not started | `3/10: Design Agent + Design System A-Grade Preflight Readiness Plan C: Subagent A-Grade Evidence Upgrade` |
| 3/10 Plan C: Subagent A-Grade Evidence Upgrade | Upgrade all required subagent/helper evidence packets. | B to A- docs/evidence by lane | A diagnostic evidence | Design Agent helper lane | Plan B GO | Not started | `4/10: Design Agent + Design System A-Grade Preflight Readiness Plan D: Safety Boundary A-Grade Proof Plan` |
| 4/10 Plan D: Safety Boundary A-Grade Proof Plan | Define A-grade safety proof and critical prompt evidence. | B+ docs to A- preintegration | A safety evidence | Safety and authority lane | Plan C GO | Not started | `5/10: Design Agent + Design System A-Grade Preflight Readiness Plan E: Source Proxy Read-Only Integration Proof` |
| 5/10 Plan E: Source Proxy Read-Only Integration Proof | Prove read-only packet receive, display, score, reject, and ownership boundaries. | C- blocked | A for read-only integration only | Source Proxy read-only bridge lane | Plan D GO | Not started | `6/10: Design Agent + Design System A-Grade Preflight Readiness Plan F: Diagnostic Batch Harness Proof` |
| 6/10 Plan F: Diagnostic Batch Harness Proof | Define diagnostic batch reporting, counters, prompt ladders, scoring, and review flow. | B planning with execution missing | A- diagnostic harness readiness | Diagnostic evidence lane | Plan E GO | Not started | `7/10: Design Agent + Design System A-Grade Preflight Readiness Plan G: Visual/CSS Evidence Proof` |
| 7/10 Plan G: Visual/CSS Evidence Proof | Define screenshot, viewport, accessibility, token, component, CSS risk, and visual-readiness proof. | C+ visual readiness and C actual design system | A- visual/CSS evidence readiness | Visual/CSS evidence lane | Plan F GO | Not started | `8/10: Design Agent + Design System A-Grade Preflight Readiness Plan H: Source Proxy PR-8.3 Alignment` |
| 8/10 Plan H: Source Proxy PR-8.3 Alignment | Align with Source Proxy PR-8.3 Run 10/25/100 and real coding task dependencies. | BLOCKED pending PR-8.3 acceptance | Accepted dependency status or explicit nonblocking decision | Source Proxy dependency lane | Plan G GO | Not started | `9/10: Design Agent + Design System A-Grade Preflight Readiness Plan I: 300-Prompt Combined Design/Coding Gauntlet Readiness` |
| 9/10 Plan I: 300-Prompt Combined Design/Coding Gauntlet Readiness | Freeze prompt bank, define scoring, safety caps, execution gate, and final report shape. | NO-GO, mechanism not approved | A-grade gauntlet readiness | Combined diagnostic lane | Plans A through H GO | Not started | `10/10: Design Agent + Design System A-Grade Preflight Readiness Plan J: Final A-Grade Preflight Readiness Gate` |
| 10/10 Plan J: Final A-Grade Preflight Readiness Gate | Validate all category evidence and decide final GO/NO-GO for preflight design/coding gauntlet and separate wrapper/final CSS request eligibility. | NO-GO | A-grade final gate evidence | Final readiness lane | Plans A through I accepted or exceptions recorded | Not started | No later plan title until Plan J closes with evidence |

## 5. PIVOT Rules

- Plans are sequential. Do not skip to later plans.
- Each phase has small increments.
- Each increment records objective, allowed files, forbidden files/actions, expected output, Codex self-checks, Britton manual verification check, stop condition, and rollback or recovery note.
- Each phase has a closeout gate.
- Each plan has a GO/NO-GO decision gate.
- Planning and implementation stay separate.
- Evidence unavailable means unavailable.
- A run is not claimed unless it actually ran.
- Read-only Source Proxy design packet proof does not grant design apply.

## 6. Shared Increment Defaults

Unless an increment narrows the scope further:

- Allowed files: new docs for the active future plan and its closeout, plus `docs/plan-index.md` only when an appropriate index section exists.
- Forbidden files/actions: all standing forbidden items in section 3.
- Expected output: a docs-only artifact with exact evidence language and no runtime claims.
- Codex self-checks: `git diff --check -- <allowed docs>`, focused grep for required headings and boundaries, grep for forbidden readiness claims, and grep for em dash with no output.
- Britton manual verification check: read the phase closeout, confirm allowed files only, confirm unavailable evidence is named, and confirm no future plan grants hidden authority.
- Stop condition: any request or wording implies runtime work, apply, CSS/app edit, Source Proxy execution, provider/model call, queue/worker action, approval-token action, or git mutation.
- Rollback or recovery note: remove only the docs created by the active increment or write a BLOCKED closeout if evidence conflicts cannot be resolved without implementation.

## Plan A: Baseline, Authority, And Source-Of-Truth Recovery

Purpose: Recover or formally replace missing Plan 0 evidence, identify stale docs, define active source-of-truth docs, and reset grading criteria.

Current grade: B+ planning baseline with missing original Plan 0 artifact.

Target grade: A-grade source-of-truth baseline for planning.

Owner lane: Design Agent docs lane.

Prerequisite: Britton approves Plan A by separate prompt.

Current status: already drafted docs-only in `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-baseline-authority-source-of-truth-recovery-v0.1.md` and closed in `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-closeout-v0.1.md`. This master plan references Plan A as a completed child/detail artifact and does not replace it.

### Phase A1: Evidence Inventory

#### Increment A1.1: Required Evidence Inventory

- Objective: List required evidence from Plan 20, remediation, DAF-5/6, design-system v0.2, and Source Proxy PR docs.
- Allowed files: Plan A docs and closeout only.
- Forbidden files/actions: standing forbidden set.
- Expected output: evidence table with found, missing, stale, historical, and unresolved statuses.
- Codex self-checks: grep for every required source document and blocker term.
- Britton manual verification check: confirm the table matches the repo documents and does not convert docs-only plans into proof.
- Stop condition: any evidence is treated as executed proof without a closeout.
- Rollback or recovery note: mark contested evidence `unresolved` and stop Plan A.

Closeout gate: GO only if the evidence inventory names all missing Plan 20 blockers.

### Phase A2: Plan 0 Recovery Or Equivalence Decision

#### Increment A2.1: Plan 0 Decision Record

- Objective: Decide whether missing Plan 0 evidence can be recovered or must be replaced by equivalent baseline evidence.
- Allowed files: Plan A docs and closeout only.
- Forbidden files/actions: no creation of fake Plan 0 result, no runtime checks beyond docs-safe inspection.
- Expected output: `recovered`, `equivalent accepted`, or `blocked` decision with evidence links.
- Codex self-checks: grep for `Plan 0`, `equivalence`, `missing/not found`, and `NO-GO`.
- Britton manual verification check: confirm the decision does not claim old evidence exists if it is absent.
- Stop condition: Plan 0 cannot be proven or replaced with a written equivalence record.
- Rollback or recovery note: leave Plan A NO-GO and request a dedicated Plan 0 recovery prompt.

Closeout gate: GO only if Britton accepts recovered or equivalent Plan 0 baseline.

### Phase A3: Active-Vs-Historical Doc Map

#### Increment A3.1: Source-Of-Truth Map

- Objective: Classify active, supporting, historical, stale, and blocked docs for the design-agent and design-system lanes.
- Allowed files: Plan A docs, closeout, optional narrow `docs/plan-index.md` update.
- Forbidden files/actions: no doc deletion, no archive movement, no status rewrite outside allowed docs.
- Expected output: doc map with conflict resolution rule.
- Codex self-checks: grep for `active`, `supporting`, `historical`, `stale`, and `blocked`.
- Britton manual verification check: confirm design-system v0.2 remains the active planning spine.
- Stop condition: two active docs conflict without an owner decision.
- Rollback or recovery note: keep both docs as unresolved and block Plan B.

Closeout gate: GO only if active design-system and design-agent sources are unambiguous.

### Phase A4: Grade Target Table

#### Increment A4.1: A-Grade Criteria Reset

- Objective: Reset grades and A evidence requirements for the six target categories.
- Allowed files: Plan A docs and closeout.
- Forbidden files/actions: no grading based on unrun prompts.
- Expected output: current grade, target grade, owner, evidence, blocker, next plan, and GO/NO-GO table.
- Codex self-checks: grep for all six categories and `evidence required for A`.
- Britton manual verification check: confirm A requires proof, not only plan text.
- Stop condition: any category is marked GO without evidence.
- Rollback or recovery note: downgrade to NO-GO and document missing evidence.

Closeout gate: GO only if grade caps are conservative and measurable.

### Phase A5: Authority Boundary Audit

#### Increment A5.1: Boundary Audit

- Objective: Audit all active sources for design apply, Source Proxy, provider, queue, worker, approval-token, git, and hidden autonomy boundaries.
- Allowed files: Plan A docs and closeout.
- Forbidden files/actions: no runtime inspection that executes systems.
- Expected output: authority boundary matrix and required corrections list.
- Codex self-checks: grep for `no apply`, `no CSS edits`, `no provider/model`, `no queue/worker`, `no approval-token`, and `no hidden autonomy`.
- Britton manual verification check: confirm Design Agent remains proposal-only and Source Proxy owns apply.
- Stop condition: active docs grant conflicting authority.
- Rollback or recovery note: mark Plan A BLOCKED and create a future docs-only correction title.

Closeout gate: GO only if no authority drift remains unresolved.

### Phase A6: Plan A Closeout

#### Increment A6.1: Plan A Decision

- Objective: Close Plan A with GO/NO-GO for Plan B.
- Allowed files: Plan A closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: decision record with next authorized title only.
- Codex self-checks: diff check, required grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm Plan B is authorized only if Plan A evidence is accepted.
- Stop condition: any prior Phase A gate is unresolved.
- Rollback or recovery note: leave next title blank except a Plan A recovery title.

Plan A GO/NO-GO decision gate: GO for Plan B only when Plan 0 recovery/equivalence, source-of-truth map, grade table, and authority audit are accepted.

## Plan B: Design System Overhaul Readiness

Purpose: Bring the actual reusable design system from C toward A before any design agent can safely generate or propose UI.

Current grade: C actual reusable design system.

Target grade: A- minimum before gauntlet.

Owner lane: Design system lane.

Prerequisite: Plan A GO.

### Phase B1: Token Inventory

#### Increment B1.1: Token Source Inventory

- Objective: Inventory token sources in Design Vault, theme files, global CSS variables, route CSS, and palette files.
- Allowed files: Plan B docs and closeout only.
- Forbidden files/actions: no token edits, no CSS edits, no app edits.
- Expected output: token source table with owner, status, drift risk, and evidence path.
- Codex self-checks: grep for `Design Vault`, `globals.css`, `spiritPalettes`, `route-scoped`, and `drift`.
- Britton manual verification check: confirm inventory is real and no token is changed.
- Stop condition: source inspection suggests hidden runtime edits are needed now.
- Rollback or recovery note: mark unknown token source `unavailable` and stop if it blocks canonical categories.

Closeout gate: GO only if token sources and drift risks are visible.

### Phase B2: Canonical Token Categories

#### Increment B2.1: Canonical Token Category Contract

- Objective: Define color, type, spacing, radius, shadow, motion, z-index, layout, state, and semantic token categories.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no token implementation.
- Expected output: category contract with required fields and examples.
- Codex self-checks: grep all token category names.
- Britton manual verification check: confirm categories are complete enough for future UI proposals.
- Stop condition: category naming conflicts with active design-system source of truth.
- Rollback or recovery note: defer contested category to Plan B blocked notes.

Closeout gate: GO only if canonical categories can guide future implementation.

### Phase B3: Design Vault Alignment

#### Increment B3.1: Vault Alignment Matrix

- Objective: Map Design Vault token and pack artifacts to canonical token categories and proposal evidence rules.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no Design Vault writes unless a later plan approves them.
- Expected output: Design Vault alignment matrix with gaps and future migration notes.
- Codex self-checks: grep for `tokens.raw.json`, `tokens.json`, `theme.css`, `components-map.json`, and `proposal evidence`.
- Britton manual verification check: confirm vault remains evidence, not runtime authority.
- Stop condition: alignment implies production CSS import.
- Rollback or recovery note: keep vault alignment advisory and block implementation sequencing.

Closeout gate: GO only if Design Vault evidence maps to canonical categories without apply authority.

### Phase B4: Primitive/Component Inventory

#### Increment B4.1: Reusable Primitive Inventory

- Objective: Inventory existing primitives, feature components, route components, and missing primitives.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no component edits.
- Expected output: primitive/component table with reuse status and ownership.
- Codex self-checks: grep for `GlassPanel`, `SectionLabel`, `SpiritButton`, `feature-local`, and `missing primitive`.
- Britton manual verification check: confirm the inventory distinguishes reusable system parts from route-specific styling.
- Stop condition: no stable source can identify component ownership.
- Rollback or recovery note: mark ownership questions and block anatomy contracts.

Closeout gate: GO only if reusable versus feature-local parts are separated.

### Phase B5: Component Anatomy Contracts

#### Increment B5.1: Anatomy Contract Plan

- Objective: Define anatomy fields for button, card, panel, field, nav, rail, table/list, modal, toast, badge, tabs, and command surface components.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no component code, no Storybook setup.
- Expected output: anatomy contract template with slots, density, state, accessibility, and evidence expectations.
- Codex self-checks: grep all component families and `slots`.
- Britton manual verification check: confirm contracts are specific enough for future Design Coding Proposal packets.
- Stop condition: anatomy contract hides route-specific CSS risk.
- Rollback or recovery note: mark missing families as gaps before Plan C.

Closeout gate: GO only if component anatomy can be reviewed without code.

### Phase B6: Variant/State Contracts

#### Increment B6.1: Variant And State Matrix

- Objective: Define variant, hover, active, focus, disabled, loading, error, empty, selected, responsive, and reduced-motion states.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no CSS or tests.
- Expected output: state matrix with required visual evidence later.
- Codex self-checks: grep for every state name and `reduced-motion`.
- Britton manual verification check: confirm no state is waived without reason.
- Stop condition: state expectations require unapproved screenshot capture now.
- Rollback or recovery note: mark visual proof as future Plan G dependency.

Closeout gate: GO only if required states are explicit.

### Phase B7: Route-Scoped CSS Risk Map

#### Increment B7.1: CSS Risk Map

- Objective: Map route-scoped CSS, feature-local styling, token drift, specificity risk, and mobile risk.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no CSS edits or CSS cleanup.
- Expected output: route CSS risk table and future sequencing recommendation.
- Codex self-checks: grep for `route-scoped CSS`, `specificity`, `mobile`, and `risk`.
- Britton manual verification check: confirm risk language does not start CSS polish.
- Stop condition: any CSS file must be touched to complete the map.
- Rollback or recovery note: leave risk item as `unknown` and continue only if nonblocking.

Closeout gate: GO only if CSS risks are known enough to block unsafe proposals.

### Phase B8: Accessibility Baseline

#### Increment B8.1: Accessibility Criteria

- Objective: Define contrast, focus, keyboard, touch target, motion, semantics, text scale, and state visibility baseline.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no accessibility implementation or test edits.
- Expected output: accessibility checklist for future proposals and visual evidence.
- Codex self-checks: grep for all baseline criteria.
- Britton manual verification check: confirm accessibility is a grade cap.
- Stop condition: accessibility evidence is claimed without a run.
- Rollback or recovery note: mark unavailable evidence and require Plan G proof.

Closeout gate: GO only if accessibility baseline is reviewable.

### Phase B9: Responsive/Mobile Baseline

#### Increment B9.1: Responsive Criteria

- Objective: Define mobile, tablet, desktop, wide, reduced-motion, and touch review expectations.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no browser run unless later approved.
- Expected output: viewport matrix and responsive acceptance criteria.
- Codex self-checks: grep for `mobile`, `tablet`, `desktop`, `wide`, and `touch`.
- Britton manual verification check: confirm criteria match actual SpiritOS review needs.
- Stop condition: viewport proof is claimed before capture.
- Rollback or recovery note: mark viewports as target list only.

Closeout gate: GO only if responsive targets are explicit.

### Phase B10: Visual Evidence Target Matrix

#### Increment B10.1: Visual Evidence Matrix

- Objective: Define screenshots, viewport coverage, component examples, route examples, token checks, and unavailable-proof rules.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no screenshot capture in this phase.
- Expected output: visual target matrix for Plan G.
- Codex self-checks: grep for `screenshot target`, `viewport`, `token alignment`, and `unavailable`.
- Britton manual verification check: confirm matrix is realistic and does not claim evidence exists.
- Stop condition: matrix depends on unapproved tool installation.
- Rollback or recovery note: defer tool choice to Plan G.

Closeout gate: GO only if Plan G can consume the matrix.

### Phase B11: Future Implementation Sequencing

#### Increment B11.1: Implementation Sequence Plan

- Objective: Sequence future implementation after docs readiness: tokens, primitives, contracts, route risk reduction, visual proof.
- Allowed files: Plan B docs and closeout.
- Forbidden files/actions: no implementation now.
- Expected output: future plan titles with prerequisites and stop conditions.
- Codex self-checks: grep for `future implementation`, `separate approval`, and `NO-GO`.
- Britton manual verification check: confirm sequence does not jump to CSS polish.
- Stop condition: future implementation plan grants authority now.
- Rollback or recovery note: convert overbroad step to title-only.

Closeout gate: GO only if future sequencing is separate and gated.

### Phase B12: Plan B Closeout

#### Increment B12.1: Plan B Decision

- Objective: Decide GO/NO-GO for Plan C.
- Allowed files: Plan B closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: design-system readiness grade, gap list, and next authorized title only.
- Codex self-checks: docs diff check, required grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm actual reusable design system can support subagent diagnostics.
- Stop condition: actual design system remains too ambiguous for subagent packet grading.
- Rollback or recovery note: request additional Plan B recovery increment.

Plan B GO/NO-GO decision gate: GO for Plan C only when design-system target evidence and A- path are clear.

## Plan C: Subagent A-Grade Evidence Upgrade

Purpose: Upgrade each design helper/subagent from docs/planning readiness to A-grade diagnostic readiness.

Current grade: B to A- by lane.

Target grade: A diagnostic evidence.

Owner lane: Design Agent helper lane.

Prerequisite: Plan B GO.

Shared subagent increment expected output: a subagent A-grade packet with role, input contract, output contract, authority boundary, fail-closed behavior, evidence required for A, rejection cases, example acceptable packet, example blocked packet, manual verification, and current grade.

Shared subagent stop condition: any subagent claims runtime, apply, CSS/app edit, provider/model, queue/worker, approval-token, git, or hidden autonomy authority.

### Phase C1: Source Rights Gatekeeper

#### Increment C1.1: Source Rights A Packet

- Objective: Prove the Source Rights Gatekeeper blocks unclear rights and protects approved-use boundaries.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no crawling, fetching, asset copying, or vault writes.
- Expected output: subagent A-grade packet covering role, input contract, output contract, authority boundary, fail-closed behavior, evidence required for A, rejection cases, acceptable packet, blocked packet, and manual verification.
- Codex self-checks: grep for `source-card`, `rights basis`, `rejected`, `fail-closed`, and `protected`.
- Britton manual verification check: test the packet against one approved internal source and one unclear external source.
- Stop condition: unclear rights pass.
- Rollback or recovery note: leave grade below A and add rejection-case recovery.

Closeout gate: GO only if unclear or rejected rights block.

### Phase C2: Design Vault

#### Increment C2.1: Design Vault A Packet

- Objective: Prove vault outputs are source-linked, useful, and never runtime authority.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no Design Vault writes, no CSS import.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `provenance`, `pack`, `proposal evidence`, `duplicate`, and `path`.
- Britton manual verification check: review one complete pack reference and one missing-provenance packet.
- Stop condition: missing provenance passes.
- Rollback or recovery note: keep Design Vault below A and require pack consistency recovery.

Closeout gate: GO only if vault packets are traceable and inert.

### Phase C3: Reverse Designer

#### Increment C3.1: Reverse Designer A Packet

- Objective: Prove Reverse Designer uses only approved inputs and blocks protected-copying traps.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no URL fetch, Figma API, image processing, or runtime analysis.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `approved inputs`, `observations`, `copying`, `blocked`, and `source card`.
- Britton manual verification check: compare an approved internal route note with an unapproved site request.
- Stop condition: unapproved input is analyzed.
- Rollback or recovery note: retain B-level status and add stricter input gate.

Closeout gate: GO only if unapproved analysis fails closed.

### Phase C4: Design Blender

#### Increment C4.1: Design Blender A Packet

- Objective: Prove blended directions are original, traceable, accessible, and safe for review.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no image generation, provider call, CSS write, or brand replica.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `originality`, `influence`, `accessibility`, `dominance`, and `blocked`.
- Britton manual verification check: review one multi-influence packet and one single-source replica trap.
- Stop condition: replica or laundering request passes.
- Rollback or recovery note: downgrade grade and add originality trap cases.

Closeout gate: GO only if originality and provenance are enforceable.

### Phase C5: Design Pack Authoring

#### Increment C5.1: Design Pack Authoring A Packet

- Objective: Prove design packs are complete proposal evidence and do not become app-write authority.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no route, Storybook, pack file, JSON, CSS, or preview writes.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `required files`, `preview-only`, `source-card`, `draft`, and `blocked`.
- Britton manual verification check: inspect one complete pack draft and one out-of-vault packet.
- Stop condition: out-of-vault or duplicate source packet passes.
- Rollback or recovery note: leave below A and require pack completeness recovery.

Closeout gate: GO only if pack output is complete and inert.

### Phase C6: Visual Verification

#### Increment C6.1: Visual Verification A Packet

- Objective: Prove visual evidence quality can be judged and fake or unavailable proof is blocked.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no browser, Playwright, screenshot, pixel compare, or baseline write.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `screenshot`, `viewport`, `unavailable`, `visual evidence`, and `blocked`.
- Britton manual verification check: review one honest missing-evidence packet and one fake screenshot claim.
- Stop condition: fake evidence passes.
- Rollback or recovery note: require Plan G evidence rule recovery.

Closeout gate: GO only if unavailable evidence is labeled honestly.

### Phase C7: Design Coding Proposal Agent

#### Increment C7.1: Design Coding Proposal A Packet

- Objective: Prove coding proposals are bounded, complete, useful for Source Proxy, and inert.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no diff generation, file edit, Source Proxy call, approval-token action, apply, or git action.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `proposal-only`, `allowed files`, `forbidden actions`, `rollback`, and `handoff`.
- Britton manual verification check: compare one acceptable handoff with one packet asking to apply.
- Stop condition: design proposal includes diff/apply authority.
- Rollback or recovery note: downgrade and add authority-drift rejection cases.

Closeout gate: GO only if proposal packets are useful and non-executing.

### Phase C8: Component Mapper

#### Increment C8.1: Component Mapper A Packet

- Objective: Prove component mapping improves target clarity without broadening authority.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no component edits or ownership assignment beyond advisory notes.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `component map`, `ownership`, `protected path`, and `advisory`.
- Britton manual verification check: review one specific component map and one overbroad file request.
- Stop condition: mapper widens allowed files.
- Rollback or recovery note: add stricter allowed-file source rule.

Closeout gate: GO only if maps stay advisory.

### Phase C9: Safety Reviewer

#### Increment C9.1: Safety Reviewer A Packet

- Objective: Prove unsafe scope, protected paths, dirty-tree risk, and authority drift are blocked.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no approval, token, apply, or hidden work.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `dirty-tree`, `protected`, `authority drift`, `blocked`, and `fail-closed`.
- Britton manual verification check: review one safe packet and one unsafe authority packet.
- Stop condition: unsafe authority drift passes.
- Rollback or recovery note: keep below A and feed failures to Plan D.

Closeout gate: GO only if safety review blocks critical drift.

### Phase C10: Test Scribe

#### Increment C10.1: Test Scribe A Packet

- Objective: Prove test suggestions are scoped, executable later, and aligned with risk.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no test execution or test edits.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `check matrix`, `manual`, `visual`, `accessibility`, and `not run`.
- Britton manual verification check: confirm suggested checks do not imply they were run.
- Stop condition: Test Scribe runs or edits tests.
- Rollback or recovery note: relabel checks as future-only and downgrade.

Closeout gate: GO only if checks are useful and honest.

### Phase C11: Authority Auditor

#### Increment C11.1: Authority Auditor A Packet

- Objective: Prove authority wording traps are detected across packets, docs, UI copy, and reports.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no authority grant or mutation.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `apply`, `provider`, `queue`, `worker`, `git`, and `hidden autonomy`.
- Britton manual verification check: review one clean packet and one false approval packet.
- Stop condition: false authority passes.
- Rollback or recovery note: feed trap into Plan D critical prompt set.

Closeout gate: GO only if unclear authority blocks.

### Phase C12: Lane Guard

#### Increment C12.1: Lane Guard A Packet

- Objective: Prove allowed files, forbidden files, dirty-tree ownership, and lane boundaries are protected.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no clean, reset, stash, checkout, or unrelated worktree claim.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `allowed files`, `forbidden files`, `dirty-tree`, `unrelated`, and `blocked`.
- Britton manual verification check: review one valid docs-only scope and one mixed CSS/source scope.
- Stop condition: forbidden file scope passes.
- Rollback or recovery note: keep below A and add path rejection cases.

Closeout gate: GO only if lane conflicts are surfaced early.

### Phase C13: Receipt/Handoff Helper

#### Increment C13.1: Receipt And Handoff A Packet

- Objective: Prove receipts and handoffs are complete, auditable, and cannot be mistaken for approval.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no next-lane start, runtime write, or approval claim.
- Expected output: full subagent A-grade packet for Receipt Scribe and Handoff Scribe.
- Codex self-checks: grep for `counts`, `grades`, `next title`, `no authority`, and `handoff`.
- Britton manual verification check: confirm receipt counts and next title are clear.
- Stop condition: receipt approves next execution.
- Rollback or recovery note: remove approval language and downgrade.

Closeout gate: GO only if receipts remain reporting only.

### Phase C14: Release Steward Helper

#### Increment C14.1: Release Steward A Packet

- Objective: Prove release/daily-use readiness advice is conservative and blocker-driven.
- Allowed files: Plan C docs and closeout.
- Forbidden files/actions: no release, tag, deploy, push, or autonomy approval.
- Expected output: full subagent A-grade packet.
- Codex self-checks: grep for `GO/NO-GO`, `blocker`, `daily-use`, `advisory`, and `no release`.
- Britton manual verification check: confirm the steward cannot override missing evidence.
- Stop condition: release or daily-use GO appears without evidence.
- Rollback or recovery note: force NO-GO and add evidence requirement.

Closeout gate: GO only if readiness advice stays conservative.

### Phase C15: Full Subagent Matrix Closeout

#### Increment C15.1: Subagent Matrix Decision

- Objective: Combine all subagent grades and decide GO/NO-GO for Plan D.
- Allowed files: Plan C closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: subagent matrix with current grade, target grade, A evidence, blockers, and Plan D handoff.
- Codex self-checks: grep all subagent names and `A evidence`.
- Britton manual verification check: confirm no subagent below A is hidden.
- Stop condition: any critical subagent remains below A without accepted recovery.
- Rollback or recovery note: request a targeted Plan C recovery phase.

Plan C GO/NO-GO decision gate: GO for Plan D only when every required subagent has A-grade diagnostic packet evidence or an explicit accepted exception.

## Plan D: Safety Boundary A-Grade Proof Plan

Purpose: Make safety boundaries A-grade before Source Proxy integration.

Current grade: B+ docs to A- preintegration.

Target grade: A safety evidence.

Owner lane: Safety and authority lane.

Prerequisite: Plan C GO.

### Phase D1: Source-Rights Rejection Cases

#### Increment D1.1: Rights Rejection Proof Set

- Objective: Define replayable rights rejection cases for missing, unclear, rejected, exact-use mismatch, and protected asset packets.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no external fetch or asset processing.
- Expected output: rejection prompt set with expected blocked results.
- Codex self-checks: grep for all rejection case names.
- Britton manual verification check: confirm the expected result is block, not caution.
- Stop condition: protected material can pass.
- Rollback or recovery note: add missing rejection fixture before proceeding.

Closeout gate: GO only if every rights trap has expected block behavior.

### Phase D2: Authority Drift Rejection Cases

#### Increment D2.1: Authority Drift Proof Set

- Objective: Define traps for apply, coding approval, provider/model, queue/worker, git, Source Proxy execution, CSS/app edit, and hidden autonomy drift.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no execution of trapped actions.
- Expected output: authority-drift prompt set with expected blocked results.
- Codex self-checks: grep for each forbidden authority term.
- Britton manual verification check: confirm block reasons are understandable.
- Stop condition: any drift case is expected to pass.
- Rollback or recovery note: correct expected result or stop.

Closeout gate: GO only if all critical drift traps are blocked.

### Phase D3: No Apply Proof

#### Increment D3.1: No Apply Replay Proof

- Objective: Define replayable evidence that Design Agent outputs do not call apply or execute-approved.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no apply endpoint call.
- Expected output: no-apply proof recipe and acceptance criteria.
- Codex self-checks: grep for `no apply`, `execute-approved`, and `blocked`.
- Britton manual verification check: confirm proof is replayable without consuming approval.
- Stop condition: proof requires apply call.
- Rollback or recovery note: replace with inert packet replay.

Closeout gate: GO only if no-apply proof is replayable and inert.

### Phase D4: No CSS/App Edit Proof

#### Increment D4.1: No CSS Or App Edit Replay Proof

- Objective: Define proof that diagnostics do not edit CSS, app routes, components, or tests.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no CSS/app/test edits.
- Expected output: file-scope proof recipe and diff-name expectations.
- Codex self-checks: grep for `no CSS edits`, `no app route edits`, `no component edits`, and `docs-only`.
- Britton manual verification check: confirm file list excludes runtime paths.
- Stop condition: proof needs runtime file mutation.
- Rollback or recovery note: block Plan D and ask for a new authority decision.

Closeout gate: GO only if file-scope evidence is clear.

### Phase D5: No Provider/Model Call Proof

#### Increment D5.1: Provider Call Absence Proof

- Objective: Define replayable proof that diagnostics do not call providers/models.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no provider/model/API call.
- Expected output: provider absence evidence recipe.
- Codex self-checks: grep for `provider/model`, `no call`, and `unavailable`.
- Britton manual verification check: confirm absence proof does not rely on hidden logs.
- Stop condition: proof requires an API call.
- Rollback or recovery note: replace with config/status inspection proof only.

Closeout gate: GO only if provider calls remain blocked.

### Phase D6: No Queue/Worker/Autonomy Proof

#### Increment D6.1: Queue Worker Autonomy Absence Proof

- Objective: Define proof that diagnostics do not enqueue, start workers, or create background autonomy.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no queue/worker execution.
- Expected output: queue/worker/autonomy absence proof recipe.
- Codex self-checks: grep for `queue`, `worker`, `background autonomy`, and `blocked`.
- Britton manual verification check: confirm no long-running task is started.
- Stop condition: proof requires a worker run.
- Rollback or recovery note: switch to read-only status evidence.

Closeout gate: GO only if queue/worker/autonomy remain absent.

### Phase D7: No Approval Token Consumption Proof

#### Increment D7.1: Approval Token Absence Proof

- Objective: Define proof that diagnostics do not consume approval tokens or create approval records.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no approval-token read/write/consume action.
- Expected output: approval-token absence proof recipe.
- Codex self-checks: grep for `approval-token`, `consume`, `no approval`, and `blocked`.
- Britton manual verification check: confirm no token action is required.
- Stop condition: proof requires token consumption.
- Rollback or recovery note: use no-token-required packet evidence.

Closeout gate: GO only if token authority remains absent.

### Phase D8: Critical Safety Prompt Set

#### Increment D8.1: Critical Prompt Bank

- Objective: Combine all critical safety traps into an approved replayable prompt set.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no prompt execution unless separately approved.
- Expected output: prompt bank with expected useful, blocked, unsafe, false-block, and authority-drift counters.
- Codex self-checks: grep for `unsafe_count`, `false_block_count`, `authority_drift_count`, and `blocked_count`.
- Britton manual verification check: confirm prompt coverage is sufficient.
- Stop condition: prompt bank omits a critical safety boundary.
- Rollback or recovery note: add missing prompt category before Plan D closeout.

Closeout gate: GO only if prompt bank covers all critical boundaries.

### Phase D9: False-Block Review

#### Increment D9.1: False-Block Review Rules

- Objective: Define how to count and review false blocks without weakening safety.
- Allowed files: Plan D docs and closeout.
- Forbidden files/actions: no execution.
- Expected output: false-block criteria and review workflow.
- Codex self-checks: grep for `false-block`, `manual review`, and `safety cap`.
- Britton manual verification check: confirm useful safe packets can be recovered later.
- Stop condition: false-block reduction allows unsafe pass.
- Rollback or recovery note: safety cap wins and Plan D remains blocked.

Closeout gate: GO only if false-block handling preserves fail-closed safety.

### Phase D10: Final Safety Grade Gate

#### Increment D10.1: Safety A Decision

- Objective: Decide whether safety evidence reaches A for Plan E.
- Allowed files: Plan D closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: safety grade table and GO/NO-GO for Plan E.
- Codex self-checks: docs diff check, safety grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm critical safety prompts are executed or replayable as required.
- Stop condition: any critical unsafe or unresolved authority drift remains.
- Rollback or recovery note: request targeted Plan D safety recovery.

Plan D GO/NO-GO decision gate: GO for Plan E only if safety boundary evidence is A and no critical drift remains.

## Plan E: Source Proxy Read-Only Integration Proof

Purpose: Bring Source Proxy integration readiness from C-/blocked to A without allowing design apply.

Current grade: C- blocked.

Target grade: A for read-only design packet receive/display/score only.

Owner lane: Source Proxy read-only bridge lane.

Prerequisite: Plan D GO.

### Phase E1: Packet Schema Compatibility

#### Increment E1.1: Schema Compatibility Plan

- Objective: Align Design Agent packet fields with Source Proxy read-only receive/display/score needs.
- Allowed files: Plan E docs and closeout.
- Forbidden files/actions: no Source Proxy runtime edits or execution.
- Expected output: compatibility table with required, optional, rejected, and unknown fields.
- Codex self-checks: grep for `packet schema`, `read-only`, `receive`, `display`, and `score`.
- Britton manual verification check: confirm schema does not include apply authority.
- Stop condition: schema requires Source Proxy mutation now.
- Rollback or recovery note: keep mismatches as blockers.

Closeout gate: GO only if schema compatibility is defined.

### Phase E2: Read-Only Receive Proof

#### Increment E2.1: Receive Proof Recipe

- Objective: Define proof that Source Proxy can receive design packets read-only.
- Allowed files: Plan E docs and closeout.
- Forbidden files/actions: no Source Proxy execution in this plan.
- Expected output: receive proof steps, evidence receipt fields, and expected no-apply result.
- Codex self-checks: grep for `read-only receive proof` and `no apply`.
- Britton manual verification check: confirm future proof is display/input only.
- Stop condition: receive proof requires apply route.
- Rollback or recovery note: require Source Proxy owner decision.

Closeout gate: GO only if receive proof can be run later without apply.

### Phase E3: Read-Only Display Proof

#### Increment E3.1: Display Proof Recipe

- Objective: Define proof that packets display clearly without granting action authority.
- Allowed files: Plan E docs and closeout.
- Forbidden files/actions: no `/coding` or design-mode UI edit now.
- Expected output: display proof target, receipt fields, and blocked-state expectations.
- Codex self-checks: grep for `display proof`, `read-only`, and `blocked`.
- Britton manual verification check: confirm UI display is not required until separately approved.
- Stop condition: display proof edits UI in this plan.
- Rollback or recovery note: split into future Source Proxy implementation plan.

Closeout gate: GO only if display proof scope is read-only.

### Phase E4: Read-Only Score Proof

#### Increment E4.1: Score Proof Recipe

- Objective: Define proof that packets can be scored for usefulness, safety, visual evidence, CSS/component relevance, and proxy handoff quality.
- Allowed files: Plan E docs and closeout.
- Forbidden files/actions: no runtime scoring implementation.
- Expected output: score proof matrix and expected counters.
- Codex self-checks: grep for `score proof`, `usefulness`, `safety`, `visual evidence`, and `CSS/component`.
- Britton manual verification check: confirm scoring does not approve apply.
- Stop condition: score proof grants approval.
- Rollback or recovery note: downgrade scoring to advisory only.

Closeout gate: GO only if scoring is advisory and auditable.

### Phase E5: Rejection Packet Proof

#### Increment E5.1: Rejection Proof Recipe

- Objective: Define proof that bad packets are rejected and reasons are visible.
- Allowed files: Plan E docs and closeout.
- Forbidden files/actions: no runtime execution now.
- Expected output: rejection packet set and receipt format.
- Codex self-checks: grep for `rejection packet`, `blocked reason`, and `authority drift`.
- Britton manual verification check: confirm rejected packet cannot be applied.
- Stop condition: rejection only warns but permits unsafe flow.
- Rollback or recovery note: block Plan E until reject behavior is defined.

Closeout gate: GO only if rejection evidence is clear.

### Phase E6: Source Proxy Owner Boundary

#### Increment E6.1: Owner Boundary Record

- Objective: Record that Source Proxy/Coding Agent own diff, preview, apply, and verification.
- Allowed files: Plan E docs and closeout.
- Forbidden files/actions: no owner transfer.
- Expected output: boundary table and handoff rule.
- Codex self-checks: grep for `Coding Agent`, `Source Proxy`, `diff`, `apply`, and `verification`.
- Britton manual verification check: confirm Design Agent remains proposal-only.
- Stop condition: design lane claims apply ownership.
- Rollback or recovery note: correct boundary or stop.

Closeout gate: GO only if owner boundaries are explicit.

### Phase E7: `/coding` Trial Widget Or Design-Mode Surface Decision

#### Increment E7.1: Surface Decision Record

- Objective: Decide whether future proof uses existing `/coding` trial widget, a design-mode surface, or another read-only display.
- Allowed files: Plan E docs and closeout.
- Forbidden files/actions: no `/coding` edit now.
- Expected output: decision record with prerequisites for any future UI implementation.
- Codex self-checks: grep for `/coding`, `trial widget`, `design-mode`, and `separate approval`.
- Britton manual verification check: confirm decision does not start widget work.
- Stop condition: surface decision implies implementation authority.
- Rollback or recovery note: leave surface undecided and block Plan E.

Closeout gate: GO only if surface decision is bounded.

### Phase E8: Evidence Receipt Format

#### Increment E8.1: Read-Only Proof Receipt

- Objective: Define receipt fields for receive, display, score, rejection, owner boundary, and unavailable evidence.
- Allowed files: Plan E docs and closeout.
- Forbidden files/actions: no runtime receipt storage.
- Expected output: receipt template.
- Codex self-checks: grep for `receipt`, `receive`, `display`, `score`, `rejection`, and `unavailable`.
- Britton manual verification check: confirm receipt is enough to evaluate Plan E run later.
- Stop condition: receipt hides blocked or unsafe counts.
- Rollback or recovery note: add missing counters.

Closeout gate: GO only if receipt supports audit.

### Phase E9: Plan E Closeout

#### Increment E9.1: Source Proxy Read-Only Decision

- Objective: Decide GO/NO-GO for Plan F.
- Allowed files: Plan E closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: Source Proxy read-only integration readiness grade and next authorized title only.
- Codex self-checks: docs diff check, read-only grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm no design apply was allowed.
- Stop condition: receive/display/score proof remains undefined or unsafe.
- Rollback or recovery note: request Plan E recovery.

Plan E GO/NO-GO decision gate: GO for Plan F only when read-only receive/display/score/reject proof is defined and owner boundaries are accepted.

## Plan F: Diagnostic Batch Harness Proof

Purpose: Prove design-agent outputs can be tested repeatedly and reported clearly.

Current grade: B planning with execution missing.

Target grade: A- diagnostic harness readiness.

Owner lane: Diagnostic evidence lane.

Prerequisite: Plan E GO.

### Phase F1: Batch Report Schema

#### Increment F1.1: Report Schema

- Objective: Define fields for prompt id, category, subagent, result, block reason, unsafe flag, false-block flag, authority drift, visual evidence quality, CSS/component relevance, and manual review.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no harness implementation.
- Expected output: batch report schema.
- Codex self-checks: grep for every report field.
- Britton manual verification check: confirm schema makes failures visible.
- Stop condition: schema hides unsafe or unavailable evidence.
- Rollback or recovery note: add missing counters before proceeding.

Closeout gate: GO only if schema is auditable.

### Phase F2: 10-Prompt Smoke Diagnostic

#### Increment F2.1: 10-Prompt Proof Plan

- Objective: Define a future 10-prompt smoke diagnostic and expected receipt.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no prompt run unless separately approved.
- Expected output: 10-prompt plan with useful, blocked, unsafe, false-block, and drift counters.
- Codex self-checks: grep for `10-prompt`, `unsafe_count`, and `blocked_count`.
- Britton manual verification check: confirm this is a plan, not a run.
- Stop condition: prompt results are fabricated.
- Rollback or recovery note: mark run status `not_started`.

Closeout gate: GO only if 10-prompt smoke criteria are clear.

### Phase F3: 30-Prompt Subagent Diagnostic

#### Increment F3.1: 30-Prompt Proof Plan

- Objective: Define a future 30-prompt subagent diagnostic across all helper categories.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no batch execution.
- Expected output: 30-prompt category matrix.
- Codex self-checks: grep for `30-prompt`, all subagent families, and `not_started`.
- Britton manual verification check: confirm coverage includes weak helpers.
- Stop condition: subagent category omitted.
- Rollback or recovery note: add missing category before proceeding.

Closeout gate: GO only if subagent coverage is complete.

### Phase F4: 100-Prompt Design/Proxy Diagnostic Plan

#### Increment F4.1: 100-Prompt Proof Plan

- Objective: Define future 100-prompt design/proxy diagnostic plan and acceptance counters.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no 100-prompt run in this plan.
- Expected output: 100-prompt plan with handoff, safety, visual, CSS/component, and Source Proxy read-only categories.
- Codex self-checks: grep for `100-prompt`, `Source Proxy`, `visual`, and `CSS/component`.
- Britton manual verification check: confirm Plan 16 prior work is referenced as planning only.
- Stop condition: 100-prompt run is claimed.
- Rollback or recovery note: correct status to `not_started`.

Closeout gate: GO only if 100-prompt proof can be separately authorized.

### Phase F5: Evidence Counters

#### Increment F5.1: Counter Definitions

- Objective: Define useful, blocked, unsafe, false-block, unavailable, fail-closed, and authority drift counters.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no runtime counter implementation.
- Expected output: counter glossary.
- Codex self-checks: grep for all counter names.
- Britton manual verification check: confirm counters are not subjective mush.
- Stop condition: unsafe output can be hidden inside useful count.
- Rollback or recovery note: safety counters override usefulness.

Closeout gate: GO only if counters are unambiguous.

### Phase F6: Useful/Blocked/Unsafe/False-Block Counts

#### Increment F6.1: Count Review Rules

- Objective: Define how batch reports calculate useful, blocked, unsafe, and false-block counts.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no run.
- Expected output: counting rules and examples.
- Codex self-checks: grep for `useful`, `blocked`, `unsafe`, and `false-block`.
- Britton manual verification check: confirm examples classify correctly.
- Stop condition: unsafe outputs do not force NO-GO.
- Rollback or recovery note: safety cap overrides count goals.

Closeout gate: GO only if count rules are conservative.

### Phase F7: Authority Drift Reporting

#### Increment F7.1: Drift Reporting Rules

- Objective: Define authority drift fields and severity.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no execution.
- Expected output: drift severity table.
- Codex self-checks: grep for `authority_drift_count`, `critical`, `major`, and `minor`.
- Britton manual verification check: confirm critical drift blocks Plan I.
- Stop condition: critical drift can pass.
- Rollback or recovery note: reset severity to blocking.

Closeout gate: GO only if drift reporting blocks critical risk.

### Phase F8: Visual Evidence Quality Scoring

#### Increment F8.1: Visual Scoring Rules

- Objective: Define visual evidence quality scoring for unavailable, partial, complete, stale, and contradictory evidence.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no screenshot capture.
- Expected output: visual evidence scoring rubric.
- Codex self-checks: grep for `visual_evidence_quality`, `unavailable`, `partial`, `complete`, and `stale`.
- Britton manual verification check: confirm no screenshot is assumed.
- Stop condition: fake visual evidence can score complete.
- Rollback or recovery note: require Plan G proof.

Closeout gate: GO only if visual scoring is honest.

### Phase F9: CSS/Component Relevance Scoring

#### Increment F9.1: CSS Component Scoring Rules

- Objective: Define CSS/component relevance scoring against design-system tokens, components, states, and route risk.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no CSS edits.
- Expected output: CSS/component scoring rubric.
- Codex self-checks: grep for `css_component_relevance`, `tokens`, `components`, `states`, and `route risk`.
- Britton manual verification check: confirm relevance cannot bypass design-system Plan B.
- Stop condition: generic CSS advice earns high score.
- Rollback or recovery note: lower scoring criteria and add examples.

Closeout gate: GO only if scoring rewards repo-specific relevance.

### Phase F10: Manual Review Flow

#### Increment F10.1: Manual Review Workflow

- Objective: Define Britton review steps, sample size, evidence receipts, and rerun rules.
- Allowed files: Plan F docs and closeout.
- Forbidden files/actions: no background run.
- Expected output: manual review flow.
- Codex self-checks: grep for `manual review`, `receipt`, `rerun`, and `sample`.
- Britton manual verification check: confirm review is easy to resume in a new Codex chat.
- Stop condition: review flow depends on hidden state.
- Rollback or recovery note: add explicit handoff block.

Closeout gate: GO only if manual review is practical.

### Phase F11: Plan F Closeout

#### Increment F11.1: Batch Harness Decision

- Objective: Decide GO/NO-GO for Plan G.
- Allowed files: Plan F closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: diagnostic harness proof plan decision and next authorized title only.
- Codex self-checks: docs diff check, batch grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm no batch was claimed as run.
- Stop condition: batch mechanism is unclear or unsafe.
- Rollback or recovery note: request Plan F recovery.

Plan F GO/NO-GO decision gate: GO for Plan G only when batch proof can report repeated diagnostics clearly.

## Plan G: Visual/CSS Evidence Proof

Purpose: Make Visual/CSS evidence real before CSS polish or design/coding gauntlet.

Current grade: C+ visual readiness and C actual reusable design system.

Target grade: A- visual/CSS evidence readiness.

Owner lane: Visual/CSS evidence lane.

Prerequisite: Plan F GO.

No CSS edits in this plan unless Britton later approves a separate implementation plan.

### Phase G1: Screenshot Target List

#### Increment G1.1: Screenshot Targets

- Objective: Define route, component, state, and packet screenshot targets.
- Allowed files: Plan G docs and closeout.
- Forbidden files/actions: no screenshot capture unless separately approved.
- Expected output: screenshot target list.
- Codex self-checks: grep for `screenshot target`, `route`, `component`, and `state`.
- Britton manual verification check: confirm target list covers actual weak surfaces.
- Stop condition: target list claims screenshots exist.
- Rollback or recovery note: mark all targets as target-only.

Closeout gate: GO only if targets are specific.

### Phase G2: Viewport Matrix

#### Increment G2.1: Viewport Matrix

- Objective: Define mobile, tablet, desktop, wide, reduced-motion, and touch viewport expectations.
- Allowed files: Plan G docs and closeout.
- Forbidden files/actions: no browser run.
- Expected output: viewport matrix.
- Codex self-checks: grep for all viewport categories.
- Britton manual verification check: confirm mobile evidence is first-class.
- Stop condition: viewport coverage is optional without reason.
- Rollback or recovery note: require Britton exception for omitted viewport.

Closeout gate: GO only if viewport coverage is sufficient.

### Phase G3: Accessibility Smoke Checklist

#### Increment G3.1: Accessibility Smoke Checklist

- Objective: Define visual accessibility checks for contrast, focus, keyboard path, touch targets, text scale, motion, and state visibility.
- Allowed files: Plan G docs and closeout.
- Forbidden files/actions: no accessibility test run.
- Expected output: accessibility smoke checklist.
- Codex self-checks: grep for each accessibility criterion.
- Britton manual verification check: confirm checklist is usable in manual review.
- Stop condition: accessibility proof is claimed before evidence.
- Rollback or recovery note: mark evidence unavailable.

Closeout gate: GO only if checklist is reviewable.

### Phase G4: Token Alignment Proof

#### Increment G4.1: Token Alignment Proof Recipe

- Objective: Define how future visual evidence proves token alignment.
- Allowed files: Plan G docs and closeout.
- Forbidden files/actions: no token or CSS edit.
- Expected output: token alignment proof recipe.
- Codex self-checks: grep for `token alignment`, `Design Vault`, and `canonical`.
- Britton manual verification check: confirm proof ties to Plan B token categories.
- Stop condition: proof requires live token change now.
- Rollback or recovery note: defer to future implementation plan.

Closeout gate: GO only if token proof is tied to canonical categories.

### Phase G5: Component Relevance Proof

#### Increment G5.1: Component Relevance Proof Recipe

- Objective: Define how future evidence proves proposals map to actual primitives, anatomy, variants, and states.
- Allowed files: Plan G docs and closeout.
- Forbidden files/actions: no component edit.
- Expected output: component relevance proof recipe.
- Codex self-checks: grep for `component relevance`, `anatomy`, `variant`, and `state`.
- Britton manual verification check: confirm proof rejects generic component advice.
- Stop condition: proof cannot map to actual repo surfaces.
- Rollback or recovery note: return to Plan B component inventory recovery.

Closeout gate: GO only if component relevance can be proven.

### Phase G6: CSS Risk Proof

#### Increment G6.1: CSS Risk Proof Recipe

- Objective: Define proof for route CSS risk, specificity risk, token drift, and responsive risk.
- Allowed files: Plan G docs and closeout.
- Forbidden files/actions: no CSS edits.
- Expected output: CSS risk proof recipe.
- Codex self-checks: grep for `CSS risk`, `specificity`, `token drift`, and `responsive`.
- Britton manual verification check: confirm risk proof blocks unsafe polish.
- Stop condition: proof starts CSS cleanup.
- Rollback or recovery note: keep risk proof read-only.

Closeout gate: GO only if CSS risk proof is non-mutating.

### Phase G7: Route Visual-Readiness Scoring

#### Increment G7.1: Route Scoring Rules

- Objective: Define route visual-readiness scoring and evidence thresholds.
- Allowed files: Plan G docs and closeout.
- Forbidden files/actions: no route edits.
- Expected output: route scoring table.
- Codex self-checks: grep for `route visual-readiness`, `score`, `threshold`, and `NO-GO`.
- Britton manual verification check: confirm weak routes stay blocked.
- Stop condition: route scores are assigned without evidence.
- Rollback or recovery note: leave scores `not_started`.

Closeout gate: GO only if scoring is evidence-based.

### Phase G8: Not Started/Unavailable Honesty Rules

#### Increment G8.1: Honesty Rules

- Objective: Define `not_started`, `unavailable`, `blocked`, `partial`, and `accepted` statuses for visual/CSS proof.
- Allowed files: Plan G docs and closeout.
- Forbidden files/actions: no evidence fabrication.
- Expected output: honesty status rules.
- Codex self-checks: grep for all honesty statuses.
- Britton manual verification check: confirm unavailable evidence cannot pass as accepted.
- Stop condition: missing proof is softened into readiness.
- Rollback or recovery note: force NO-GO for missing proof.

Closeout gate: GO only if honesty rules are strict.

### Phase G9: Plan G Closeout

#### Increment G9.1: Visual/CSS Evidence Decision

- Objective: Decide GO/NO-GO for Plan H.
- Allowed files: Plan G closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: visual/CSS evidence proof readiness decision and next authorized title only.
- Codex self-checks: docs diff check, Visual/CSS grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm no CSS edits occurred and no screenshots were fabricated.
- Stop condition: visual/CSS proof remains target-only when Plan H needs accepted evidence.
- Rollback or recovery note: request Plan G recovery or separate visual execution approval.

Plan G GO/NO-GO decision gate: GO for Plan H only when Visual/CSS evidence proof is defined and honest.

## Plan H: Source Proxy PR-8.3 Alignment

Purpose: Make sure the Source Proxy side is not blocking the design-agent lane.

Current grade: BLOCKED pending PR-8.3 acceptance.

Target grade: accepted dependency status or explicit nonblocking decision.

Owner lane: Source Proxy dependency lane.

Prerequisite: Plan G GO.

This plan does not run PR-8.3. It defines dependencies and sequencing so Britton knows when to start that lane.

### Phase H1: Current PR-8.3 Status Inventory

#### Increment H1.1: PR-8.3 Inventory

- Objective: Inventory PR-8.3 plan status, blocker status, browser proof needs, real task gauntlet needs, and dirty-tree requirements.
- Allowed files: Plan H docs and closeout.
- Forbidden files/actions: no Source Proxy run, no `/coding` edit.
- Expected output: PR-8.3 dependency table.
- Codex self-checks: grep for `PR-8.3`, `Run 10`, `Run 25`, `Run 100`, and `dirty tree`.
- Britton manual verification check: confirm this is dependency planning only.
- Stop condition: PR-8.3 execution is started.
- Rollback or recovery note: stop and write BLOCKED closeout.

Closeout gate: GO only if PR-8.3 status is clear.

### Phase H2: Run 10 Manual/Browser Proof Dependency

#### Increment H2.1: Run 10 Dependency

- Objective: Define what accepted Run 10 manual/browser proof must provide before design/coding readiness.
- Allowed files: Plan H docs and closeout.
- Forbidden files/actions: no browser run.
- Expected output: Run 10 dependency criteria.
- Codex self-checks: grep for `Run 10`, `manual/browser proof`, and `accepted`.
- Britton manual verification check: confirm criteria can be checked by Britton later.
- Stop condition: Run 10 is claimed accepted without receipt.
- Rollback or recovery note: mark dependency `not_started`.

Closeout gate: GO only if Run 10 dependency is explicit.

### Phase H3: Run 25 Manual/Browser Proof Dependency

#### Increment H3.1: Run 25 Dependency

- Objective: Define accepted Run 25 proof criteria.
- Allowed files: Plan H docs and closeout.
- Forbidden files/actions: no browser run.
- Expected output: Run 25 dependency criteria.
- Codex self-checks: grep for `Run 25`, `manual/browser proof`, and `receipt`.
- Britton manual verification check: confirm acceptance evidence shape.
- Stop condition: Run 25 is claimed accepted without receipt.
- Rollback or recovery note: mark dependency `not_started`.

Closeout gate: GO only if Run 25 dependency is explicit.

### Phase H4: Run 100 Manual/Browser Proof Dependency

#### Increment H4.1: Run 100 Dependency

- Objective: Define accepted Run 100 proof criteria.
- Allowed files: Plan H docs and closeout.
- Forbidden files/actions: no browser run.
- Expected output: Run 100 dependency criteria.
- Codex self-checks: grep for `Run 100`, `manual/browser proof`, and `receipt`.
- Britton manual verification check: confirm existing pending manual proof is not treated as accepted unless Britton accepts it.
- Stop condition: pending proof is upgraded without manual acceptance.
- Rollback or recovery note: keep dependency blocked.

Closeout gate: GO only if Run 100 dependency is explicit.

### Phase H5: Real Low-To-Mid Coding Task Gauntlet Dependency

#### Increment H5.1: Real Task Dependency

- Objective: Define dependency on a real low-to-mid coding task gauntlet with receipts.
- Allowed files: Plan H docs and closeout.
- Forbidden files/actions: no coding task execution.
- Expected output: real-task gauntlet criteria and receipt needs.
- Codex self-checks: grep for `real coding task`, `low-to-mid`, `gauntlet`, and `receipt`.
- Britton manual verification check: confirm task proof remains Source Proxy lane-owned.
- Stop condition: design lane attempts coding task.
- Rollback or recovery note: return dependency to Source Proxy PR-8.3 lane.

Closeout gate: GO only if task dependency is owned by Source Proxy.

### Phase H6: Dirty-Tree Evidence Requirement

#### Increment H6.1: Dirty-Tree Requirement

- Objective: Define dirty/untracked worktree evidence required before PR-8.3 acceptance can unblock design/coding readiness.
- Allowed files: Plan H docs and closeout.
- Forbidden files/actions: no git mutation.
- Expected output: dirty-tree evidence requirement and stop conditions.
- Codex self-checks: grep for `dirty tree`, `untracked`, `git status`, and `no reset`.
- Britton manual verification check: confirm evidence is reported, not cleaned.
- Stop condition: plan asks to stash, reset, clean, checkout, or branch.
- Rollback or recovery note: remove mutation language and block.

Closeout gate: GO only if dirty-tree evidence is first-class.

### Phase H7: Receipt Package Requirement

#### Increment H7.1: Receipt Package

- Objective: Define required receipt package for PR-8.3 to unblock Plan I.
- Allowed files: Plan H docs and closeout.
- Forbidden files/actions: no run.
- Expected output: receipt package checklist.
- Codex self-checks: grep for `receipt package`, `browser`, `terminal`, `manual`, and `NO-GO`.
- Britton manual verification check: confirm receipts are sufficient for later gate review.
- Stop condition: receipts omit failures.
- Rollback or recovery note: add failure fields.

Closeout gate: GO only if receipt package supports acceptance decision.

### Phase H8: Acceptance Decision Gate

#### Increment H8.1: PR-8.3 Alignment Decision

- Objective: Decide whether PR-8.3 dependencies are satisfied or still block Plan I.
- Allowed files: Plan H closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: acceptance dependency decision and next authorized title only.
- Codex self-checks: docs diff check, PR-8.3 grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm Plan H did not run PR-8.3.
- Stop condition: dependency acceptance lacks receipts.
- Rollback or recovery note: leave Plan I NO-GO until PR-8.3 receipts exist.

Plan H GO/NO-GO decision gate: GO for Plan I only when PR-8.3 dependencies are accepted or explicitly nonblocking by Britton decision record.

## Plan I: 300-Prompt Combined Design/Coding Gauntlet Readiness

Purpose: Only after Plans A through H are GO, decide whether the 300-prompt combined design/coding gauntlet can be authorized.

Current grade: NO-GO, mechanism not approved.

Target grade: A-grade gauntlet readiness.

Owner lane: Combined diagnostic lane.

Prerequisite: Plans A through H all GO.

Do not claim the 300-prompt gauntlet is ready until all prior plans are accepted.

### Phase I1: Prompt Bank Freeze

#### Increment I1.1: Prompt Bank Freeze

- Objective: Freeze prompt bank source, version, categories, and allowed execution mechanism for review.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no 300-prompt execution.
- Expected output: frozen prompt bank index.
- Codex self-checks: grep for `prompt bank freeze`, `300-prompt`, and `not_started`.
- Britton manual verification check: confirm no prompts were run.
- Stop condition: prompt outputs are claimed.
- Rollback or recovery note: reset status to `not_started`.

Closeout gate: GO only if prompt bank is frozen.

### Phase I2: Prompt Categories

#### Increment I2.1: Category Matrix

- Objective: Define prompt categories for design system, subagents, safety, read-only Source Proxy handoff, visual/CSS, batch reporting, and daily-use readiness.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no execution.
- Expected output: 300-prompt category matrix.
- Codex self-checks: grep for all category names.
- Britton manual verification check: confirm categories reflect Plans A through H evidence.
- Stop condition: category omits a prior blocker.
- Rollback or recovery note: add missing category.

Closeout gate: GO only if all blocker families are covered.

### Phase I3: Execution Mechanism Approval

#### Increment I3.1: Mechanism Approval Gate

- Objective: Define the exact future execution mechanism and approvals required before a 300-prompt run.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no provider/model call, queue/worker execution, Source Proxy execution, or app run here.
- Expected output: execution approval checklist.
- Codex self-checks: grep for `execution mechanism`, `approval`, `provider/model`, and `queue/worker`.
- Britton manual verification check: confirm future mechanism is explicit and separately approved.
- Stop condition: mechanism is vague or implies hidden autonomy.
- Rollback or recovery note: leave gauntlet NO-GO.

Closeout gate: GO only if execution approval is explicit.

### Phase I4: Safety Caps

#### Increment I4.1: Safety Caps

- Objective: Define zero-critical-unsafe, zero-unresolved-authority-drift, and fail-closed caps.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no execution.
- Expected output: safety cap table.
- Codex self-checks: grep for `zero critical unsafe`, `authority drift`, and `fail-closed`.
- Britton manual verification check: confirm safety vetoes usefulness.
- Stop condition: unsafe output can pass.
- Rollback or recovery note: restore veto rule.

Closeout gate: GO only if safety caps are strict.

### Phase I5: Source Proxy Handoff Scoring

#### Increment I5.1: Handoff Scoring

- Objective: Define Source Proxy handoff scoring for read-only packet quality and owner boundary preservation.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no Source Proxy execution.
- Expected output: handoff scoring rubric.
- Codex self-checks: grep for `Source Proxy handoff`, `read-only`, `owner boundary`, and `score`.
- Britton manual verification check: confirm scoring does not imply apply.
- Stop condition: handoff score approves diff/apply.
- Rollback or recovery note: make score advisory only.

Closeout gate: GO only if handoff scoring is bounded.

### Phase I6: Visual/CSS Scoring

#### Increment I6.1: Visual CSS Scoring

- Objective: Define visual/CSS scoring from Plan G evidence.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no CSS edit or screenshot capture.
- Expected output: visual/CSS scoring rubric.
- Codex self-checks: grep for `Visual/CSS`, `evidence`, `route`, and `score`.
- Britton manual verification check: confirm score uses accepted evidence only.
- Stop condition: missing evidence scores as accepted.
- Rollback or recovery note: mark category NO-GO.

Closeout gate: GO only if Visual/CSS scoring depends on accepted proof.

### Phase I7: Design System Scoring

#### Increment I7.1: Design System Scoring

- Objective: Define design-system scoring from Plan B token, component, state, accessibility, responsive, and risk evidence.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no design-system implementation.
- Expected output: design-system scoring rubric.
- Codex self-checks: grep for `design-system`, `token`, `component`, `accessibility`, and `responsive`.
- Britton manual verification check: confirm actual reusable system weakness cannot be hidden.
- Stop condition: C-grade actual system passes.
- Rollback or recovery note: require Plan B recovery.

Closeout gate: GO only if design-system scoring has A- floor.

### Phase I8: Subagent Scoring

#### Increment I8.1: Subagent Scoring

- Objective: Define per-subagent scoring from Plan C packets and Plan F diagnostics.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no execution.
- Expected output: subagent scoring rubric.
- Codex self-checks: grep for all subagent names and `score`.
- Britton manual verification check: confirm no helper can be ungraded.
- Stop condition: missing subagent score.
- Rollback or recovery note: return to Plan C recovery.

Closeout gate: GO only if every helper is scored.

### Phase I9: Daily-Use Readiness Score

#### Increment I9.1: Daily-Use Readiness Formula

- Objective: Define daily-use readiness score from safety, usefulness, repeatability, read-only handoff, visual/CSS, design-system, and manual review fields.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no daily-use approval.
- Expected output: daily-use readiness formula and caps.
- Codex self-checks: grep for `daily-use readiness score`, `caps`, and `NO-GO`.
- Britton manual verification check: confirm score cannot override blockers.
- Stop condition: score grants final approval by itself.
- Rollback or recovery note: make score advisory.

Closeout gate: GO only if formula is conservative.

### Phase I10: 300-Prompt Execution Gate

#### Increment I10.1: Execution GO/NO-GO Gate

- Objective: Decide whether Britton may separately authorize the 300-prompt run.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no run.
- Expected output: execution gate checklist.
- Codex self-checks: grep for `300-prompt execution gate`, `separate approval`, and `NO-GO`.
- Britton manual verification check: confirm Plans A through H are accepted before any run.
- Stop condition: any prior plan is not GO.
- Rollback or recovery note: keep gauntlet blocked.

Closeout gate: GO only if all prerequisites are satisfied.

### Phase I11: Final Report Shape

#### Increment I11.1: Final Report Template

- Objective: Define final 300-prompt report shape with category grades, subagent grades, counters, receipts, blockers, and next decision.
- Allowed files: Plan I docs and closeout.
- Forbidden files/actions: no report result fabrication.
- Expected output: final report template.
- Codex self-checks: grep for `final report`, `category grades`, `subagent grades`, and `counters`.
- Britton manual verification check: confirm template cannot hide failures.
- Stop condition: template includes prefilled pass results.
- Rollback or recovery note: remove result values until run exists.

Closeout gate: GO only if final report is auditable.

### Phase I12: Plan I Closeout

#### Increment I12.1: Gauntlet Readiness Decision

- Objective: Decide GO/NO-GO for Plan J.
- Allowed files: Plan I closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: 300-prompt readiness decision and next authorized title only.
- Codex self-checks: docs diff check, 300-prompt grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm the 300-prompt gauntlet was not run unless separately approved in a later task.
- Stop condition: gauntlet status is ambiguous.
- Rollback or recovery note: leave Plan J NO-GO.

Plan I GO/NO-GO decision gate: GO for Plan J only when 300-prompt execution is approved or when Plan J is limited to validating readiness without execution.

## Plan J: Final A-Grade Preflight Readiness Gate

Purpose: Rerun the readiness decision after evidence exists.

Current grade: NO-GO.

Target grade: A-grade final gate evidence.

Owner lane: Final readiness lane.

Prerequisite: Plans A through I have accepted closeouts or written Britton exceptions.

### Phase J1: Validate All A-Grade Category Evidence

#### Increment J1.1: Category Evidence Validation

- Objective: Validate evidence for all six categories in the required grading model.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no new evidence execution.
- Expected output: category evidence validation table.
- Codex self-checks: grep for all six categories and `validated`.
- Britton manual verification check: confirm each validation points to accepted evidence.
- Stop condition: a category lacks accepted evidence.
- Rollback or recovery note: Plan J remains NO-GO and points to the failed plan.

Closeout gate: GO only if every category has accepted evidence.

### Phase J2: Validate Design-System A-/A Evidence

#### Increment J2.1: Design-System Validation

- Objective: Validate design-system evidence meets A- minimum and any claimed A criteria.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no design-system edits.
- Expected output: design-system validation result.
- Codex self-checks: grep for `A-`, `design-system`, `token`, and `component`.
- Britton manual verification check: confirm actual reusable system no longer sits at C.
- Stop condition: design system remains C or unproven.
- Rollback or recovery note: return to Plan B or future implementation plan.

Closeout gate: GO only if design-system evidence is at least A-.

### Phase J3: Validate Safety A Evidence

#### Increment J3.1: Safety Validation

- Objective: Validate safety A evidence from Plan D and diagnostic results.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no safety prompt run in this gate unless separately approved.
- Expected output: safety validation result.
- Codex self-checks: grep for `Safety A`, `unsafe`, `authority drift`, and `fail-closed`.
- Britton manual verification check: confirm zero critical unsafe and zero unresolved authority drift.
- Stop condition: any critical safety gap remains.
- Rollback or recovery note: return to Plan D.

Closeout gate: GO only if safety A is proven.

### Phase J4: Validate Source Proxy Read-Only Integration A Evidence

#### Increment J4.1: Read-Only Integration Validation

- Objective: Validate receive, display, score, rejection, and owner-boundary proof.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no Source Proxy execution in this gate.
- Expected output: read-only integration validation result.
- Codex self-checks: grep for `receive`, `display`, `score`, `rejection`, and `owner boundary`.
- Britton manual verification check: confirm proof is read-only and accepted.
- Stop condition: any read-only proof is missing.
- Rollback or recovery note: return to Plan E.

Closeout gate: GO only if read-only integration evidence is accepted.

### Phase J5: Validate PR-8.3 Dependency Status

#### Increment J5.1: PR-8.3 Validation

- Objective: Validate PR-8.3 dependency receipts and acceptance decision.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no PR-8.3 run.
- Expected output: PR-8.3 validation result.
- Codex self-checks: grep for `PR-8.3`, `Run 10`, `Run 25`, `Run 100`, and `real coding task`.
- Britton manual verification check: confirm dependency status came from Source Proxy lane receipts.
- Stop condition: PR-8.3 remains blocked.
- Rollback or recovery note: return to Plan H or Source Proxy lane.

Closeout gate: GO only if PR-8.3 is not blocking.

### Phase J6: Validate 100-Prompt Diagnostic Status

#### Increment J6.1: 100-Prompt Validation

- Objective: Validate 100-prompt diagnostic status and receipt if run later.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no 100-prompt run in this gate unless separately approved.
- Expected output: 100-prompt validation result.
- Codex self-checks: grep for `100-prompt`, `receipt`, and `not_started`.
- Britton manual verification check: confirm run status is true.
- Stop condition: 100-prompt is missing when required.
- Rollback or recovery note: return to Plan F.

Closeout gate: GO only if 100-prompt status is accepted.

### Phase J7: Validate 300-Prompt Readiness

#### Increment J7.1: 300-Prompt Validation

- Objective: Validate 300-prompt readiness or later run receipt if separately approved.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no 300-prompt run here.
- Expected output: 300-prompt validation result.
- Codex self-checks: grep for `300-prompt`, `readiness`, and `receipt`.
- Britton manual verification check: confirm no run is claimed without actual execution.
- Stop condition: readiness is asserted before prerequisites.
- Rollback or recovery note: return to Plan I.

Closeout gate: GO only if 300-prompt readiness is valid.

### Phase J8: Decide GO/NO-GO For Preflight Design/Coding Gauntlet

#### Increment J8.1: Preflight Gate Decision

- Objective: Decide GO/NO-GO for preflight design/coding gauntlet.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no gauntlet execution.
- Expected output: final GO/NO-GO decision with blockers.
- Codex self-checks: grep for `GO/NO-GO`, `preflight design/coding gauntlet`, and `blockers`.
- Britton manual verification check: confirm all accepted evidence is linked.
- Stop condition: any prerequisite category is below target.
- Rollback or recovery note: final decision remains NO-GO.

Closeout gate: GO only if all evidence gates pass.

### Phase J9: Decide Whether Wrapper/Final CSS Can Be Separately Requested

#### Increment J9.1: Wrapper/CSS Separate Request Decision

- Objective: Decide whether wrapper or final CSS can be separately requested after preflight evidence.
- Allowed files: Plan J docs and closeout.
- Forbidden files/actions: no wrapper or CSS work.
- Expected output: title-only next request or NO-GO reason.
- Codex self-checks: grep for `wrapper`, `final CSS`, `separate request`, and `NO-GO`.
- Britton manual verification check: confirm wrapper/final CSS remains separately authorized.
- Stop condition: final CSS starts inside Plan J.
- Rollback or recovery note: remove authority language and keep separate request blocked.

Closeout gate: GO only if wrapper/final CSS decision is title-only and separately gated.

### Phase J10: Plan J Closeout

#### Increment J10.1: Final A-Grade Gate Closeout

- Objective: Close the final readiness gate with exact evidence, GO/NO-GO, and next authorized title only.
- Allowed files: Plan J closeout and optional index note.
- Forbidden files/actions: standing forbidden set.
- Expected output: final decision record.
- Codex self-checks: docs diff check, gate grep, forbidden-claim grep, em dash grep.
- Britton manual verification check: confirm decision is evidence-backed and conservative.
- Stop condition: any evidence is missing or overstated.
- Rollback or recovery note: final status remains NO-GO.

Plan J GO/NO-GO decision gate: GO for preflight design/coding gauntlet only if every prior evidence gate is accepted. Otherwise NO-GO.

## 7. Resume Rules For New Codex Chats

1. Start with `docs/plan-index.md`, this master plan, and the latest closeout for the active plan.
2. Confirm the latest accepted plan letter.
3. Do not skip the next sequential plan.
4. Re-read the standing authority boundary before editing.
5. Treat `not_started`, `unavailable`, `blocked`, and `pending Britton manual verification` as blockers, not soft passes.
6. Return only the next authorized title when a plan closes.

## 8. Current Master Decision

Current decision: NO-GO for preflight design/coding gauntlet.

Allowed next title only:

2/10: Design Agent + Design System A-Grade Preflight Readiness Plan B: Design System Overhaul Readiness
