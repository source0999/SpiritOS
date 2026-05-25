# Design Agent + Design System A-Grade Preflight Readiness Plan A: Baseline, Authority, And Source-Of-Truth Recovery v0.1

Status: docs-only Plan A complete

Owner: Britton

Date: 2026-05-24

Active master: `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md`

Plan count: 1/10

Decision: GO for Plan B only after Britton accepts the Plan A closeout and manual checks.

## 1. Purpose

Plan A starts only the first plan in the 10-plan PIVOT sequence. It recovers the missing Plan 0 baseline by written equivalence, classifies active versus historical source documents, resets A-grade targets, and audits authority boundaries before any Design System Overhaul readiness work can begin.

Plan A is docs-only. It does not implement runtime behavior, edit app routes, edit CSS, edit Source Proxy runtime, edit providers, execute queues or workers, consume approval tokens, apply changes, commit, push, branch, stash, reset, clean, checkout, or create hidden autonomy.

Plan A does not start Plan B.

Plan A does not claim preflight readiness.

Plan A does not claim a run happened unless a command is explicitly listed under self-checks.

## 2. Standing Authority Boundary

Allowed files:

- `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-baseline-authority-source-of-truth-recovery-v0.1.md`
- `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-closeout-v0.1.md`
- `docs/plan-index.md` only as a narrow active-plan index entry.

Forbidden files and actions:

- No runtime code edits.
- No app route edits.
- No CSS edits.
- No Source Proxy runtime edits.
- No providers.
- No queues.
- No workers.
- No approval-token systems.
- No apply systems.
- No git state mutation, branch, commit, push, stash, reset, clean, checkout, or worktree action.
- No hidden autonomy.
- No implementation.
- No Plan B work.

## 3. Evidence Inventory

### Phase A1: Evidence Inventory

#### Increment A1.1: Required Evidence Inventory

Objective:
List required evidence from Plan 20, remediation, DAF-5/6, design-system v0.2, and Source Proxy PR docs.

Allowed files:
Plan A docs, Plan A closeout, and the narrow `docs/plan-index.md` entry.

Forbidden files/actions:
All standing forbidden files and actions. Do not execute Source Proxy proof, browser proof, providers, queues, workers, approval-token actions, apply, or git mutation.

Expected output:
Evidence inventory table with `found`, `missing`, `stale`, `historical`, and `unresolved` statuses.

Codex self-checks:

- Confirm every required source document appears in this Plan A doc.
- Confirm blocker terms are present: `Plan 0`, `Source Proxy Preflight PR-10`, `receive/display/score`, `100-prompt`, `300-prompt`, `Visual/CSS`, `authority`, and `NO-GO`.
- Confirm no planned evidence is upgraded into executed proof.

Britton manual verification check:
Confirm the table matches repository documents and does not convert docs-only plans into proof.

Stop condition:
Stop if any evidence is treated as executed proof without an actual closeout or run record.

Rollback/recovery note:
Mark contested evidence `unresolved` and close Plan A NO-GO if evidence conflicts cannot be resolved in docs.

| Evidence item | Source document | Status | Plan A interpretation |
| --- | --- | --- | --- |
| Plan A master authorization | `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md` | found | Active master says Plan A starts first and Plan B must not start until Plan A closes. |
| Plan 20 final gate | `docs/design-agent-ecosystem-plan-20-full-design-agent-ecosystem-production-daily-use-preflight-css-polish-readiness-gate-v0.1.md` | found | Final gate is NO-GO. Missing proof remains blocking. |
| Plan 20 closeout | `docs/design-agent-ecosystem-plan-20-closeout-v0.1.md` | found | Confirms NO-GO and forbids runtime, Source Proxy proof, `/coding`, CSS, provider, queue, worker, approval-token, apply, and git authority. |
| Remediation blocker table | `docs/design-agent-ecosystem-remediation-plan-final-gate-evidence-recovery-and-lane-merge-prerequisites-v0.1.md` | found | Names missing Plan 0 artifact, Source Proxy receive/display/score proof, Visual/CSS proof, 100-prompt proof, 300-prompt proof, and daily-use score blockers. |
| Remediation closeout | `docs/design-agent-ecosystem-remediation-plan-closeout-v0.1.md` | found | Confirms remediation sequence is planning only and no evidence was executed. |
| Design-system current state | `docs/design-system-overhaul-master-v0.2.md` | found | Active design-system planning spine. Actual reusable design system is C, Design Vault is B, visual verification is C+, design apply lane is B-. |
| Design Agent Fleet preintegration readiness | `docs/design-agent-fleet-daf-5-readiness-decision-v0.1.md` | found | DAF-0 through DAF-4 are PASS for preintegration planning, supplied-data behavior, proposal-only boundaries, and helper advisory behavior. |
| DAF-6 future gate | `docs/design-agent-fleet-daf-6-future-gate-definition-v0.1.md` | found | Source Proxy integration implementation is NOT STARTED. Design Agent cannot apply UI and can only later submit proposal packets. |
| Source Proxy preflight roadmap | `docs/source-proxy-preflight-readiness-master-roadmap-v0.1.md` | found | Wrapper and final CSS remain gated. PR-8.3 proof and dirty-tree evidence remain first-class blockers. |
| Source Proxy PR-8 workflow proof | `docs/source-proxy-preflight-pr-8-real-preflight-coding-workflow-proof-v0.1.md` | found | PR-8 is BLOCKED at Phase 8.3 pending browser/manual Run 10/25/100 and real task gauntlet approval. |
| Source Proxy PR-9 dependency alignment | `docs/source-proxy-preflight-pr-9-design-cartographer-scout-dependency-alignment-v0.1.md` | found | Design, Cartographer, and Scout dependencies remain proposal-only/read-only/manual-controlled. |
| Source Proxy PR-10 wrapper/final CSS gate | `docs/source-proxy-preflight-pr-10-wrapper-final-css-decision-gate-v0.1.md` | found | Wrapper and final CSS authority remain BLOCKED. PR-8.3 fresh proof remains missing. |
| Source Proxy PR-8.3 proof gauntlet bridge | `docs/source-proxy-codex-style-ui-reduction-pr-8-3-gauntlet-master-plan-v0.1.md` | found | PIVOT docs-only bridge is BLOCKED before implementation and before PR-8.3 execution. |
| Active plan index | `docs/plan-index.md` | found | Contains active design-system spine and master plan entry. Plan A narrow index entry is appropriate. |
| Original Design Agent Ecosystem Plan 0 artifact | `docs/design-agent-ecosystem-plan-0-*.md` | missing | No matching Plan 0 artifact was found by docs-safe inspection. Requires equivalence decision. |
| Source Proxy receive/display/score proof | Plan 20 and remediation blocker rows | missing/not_started | Contract exists in planning docs, but runtime receive/display/score proof is not available. |
| Visual/CSS evidence proof | Plan 20 and design-system v0.2 | missing/not_started | Visual proof, screenshots, accessibility proof, and CSS/component relevance proof are not available. |
| 100-prompt execution result | Plan 20 and remediation blocker rows | missing/not_started | Prompt bank planning is not execution proof. |
| 300-prompt execution result | Plan 20 and remediation blocker rows | missing/not_started | Gauntlet planning is not execution proof. |
| Daily-use readiness score | Plan 20 and remediation blocker rows | missing/not_started | Score is blocked until required evidence exists. |

Phase A1 closeout gate:
GO. The evidence inventory names all Plan 20 blockers and keeps missing proof marked missing, unavailable, blocked, or not_started.

## 4. Plan 0 Recovery Or Equivalence Decision

### Phase A2: Plan 0 Recovery Or Equivalence Decision

#### Increment A2.1: Plan 0 Decision Record

Objective:
Decide whether missing Plan 0 evidence can be recovered or must be replaced by equivalent baseline evidence.

Allowed files:
Plan A docs, Plan A closeout, and the narrow `docs/plan-index.md` entry.

Forbidden files/actions:
No fake Plan 0 result, no runtime checks beyond docs-safe inspection, no Source Proxy proof, no browser proof, no provider/model call, no queue/worker action, no approval-token action, no apply, and no git mutation.

Expected output:
Decision of `recovered`, `equivalent accepted`, or `blocked` with evidence links.

Codex self-checks:

- Confirm `Plan 0`, `equivalence`, `missing/not found`, and `NO-GO` appear in this document.
- Confirm this document does not claim the original Plan 0 artifact exists.
- Confirm all equivalent evidence sources are explicit.

Britton manual verification check:
Confirm the decision does not claim old Plan 0 evidence exists if it is absent.

Stop condition:
Stop if Plan 0 cannot be proven or replaced with a written equivalence record.

Rollback/recovery note:
If Britton rejects the equivalence, close Plan A NO-GO and use the recovery title in the Plan A closeout.

Decision:
`equivalent accepted` for Plan A docs-only baseline recovery, pending Britton manual acceptance of the closeout.

Evidence basis:

- The original Design Agent Ecosystem Plan 0 artifact is missing/not found in docs-safe inspection.
- Plan 20 already identifies the missing Plan 0 artifact as a blocker instead of pretending it exists.
- The remediation plan requires Plan 0 recovery or written equivalence as the first remediation step.
- DAF-5 supplies a separate preintegration baseline and boundary evidence matrix, including DAF-0 through DAF-4 PASS closeouts.
- DAF-6 supplies a not-started Source Proxy integration boundary.
- The master plan supplies the current standing authority boundary and PIVOT sequence.
- Design-system v0.2 supplies the current design-system baseline and grade caps.
- Source Proxy PR-8, PR-9, PR-10, and the PR-8.3 bridge supply current Source Proxy preflight blockers and no-authority gates.

Equivalence rule:
For this 10-plan A-grade readiness sequence, Plan 0 is treated as replaced by the Plan A evidence inventory, source-of-truth map, grade target reset, and authority boundary audit. This replacement does not recover the old Plan 0 artifact and does not erase Plan 20 execution blockers.

Phase A2 closeout gate:
GO for docs-only equivalence. If Britton rejects this equivalence during manual review, Plan A downgrades to NO-GO and the recovery title is `Design Agent + Design System A-Grade Preflight Readiness Plan A Recovery: Plan 0 Evidence Recovery Or Equivalence Repair`.

## 5. Active-Vs-Historical Doc Map

### Phase A3: Active-Vs-Historical Doc Map

#### Increment A3.1: Source-Of-Truth Map

Objective:
Classify active, supporting, historical, stale, and blocked docs for the design-agent and design-system lanes.

Allowed files:
Plan A docs, Plan A closeout, and the narrow `docs/plan-index.md` entry.

Forbidden files/actions:
No doc deletion, no archive movement, no status rewrite outside allowed docs, no Plan B content, and no implementation.

Expected output:
Doc map with conflict resolution rule.

Codex self-checks:

- Confirm `active`, `supporting`, `historical`, `stale`, and `blocked` appear in this section.
- Confirm design-system v0.2 remains active.
- Confirm the master plan remains active for the 10-plan sequence.

Britton manual verification check:
Confirm design-system v0.2 remains the active planning spine.

Stop condition:
Stop if two active docs conflict without an owner decision.

Rollback/recovery note:
Keep both conflicting docs as unresolved and block Plan B.

| Document | Classification | Handling |
| --- | --- | --- |
| `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md` | active | Governs the 10-plan A-grade preflight readiness sequence and PIVOT rules. |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-baseline-authority-source-of-truth-recovery-v0.1.md` | active | Plan A source for baseline recovery, source-of-truth map, grade reset, and authority audit. |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-a-closeout-v0.1.md` | active closeout | Plan A decision record and GO/NO-GO gate for Plan B. |
| `docs/design-system-overhaul-master-v0.2.md` | active | Current design-system planning spine and design-system grade baseline. |
| `docs/design-agent-ecosystem-plan-20-full-design-agent-ecosystem-production-daily-use-preflight-css-polish-readiness-gate-v0.1.md` | active blocker evidence | Holds final gate NO-GO and missing evidence list. |
| `docs/design-agent-ecosystem-plan-20-closeout-v0.1.md` | active blocker closeout | Confirms Plan 20 NO-GO and authority boundary. |
| `docs/design-agent-ecosystem-remediation-plan-final-gate-evidence-recovery-and-lane-merge-prerequisites-v0.1.md` | active supporting recovery | Provides blocker table and remediation sequence; does not authorize execution. |
| `docs/design-agent-ecosystem-remediation-plan-closeout-v0.1.md` | active supporting closeout | Confirms remediation remains docs-only. |
| `docs/design-agent-fleet-daf-5-readiness-decision-v0.1.md` | supporting | Supplies preintegration evidence and proposal-only helper fleet boundary. |
| `docs/design-agent-fleet-daf-6-future-gate-definition-v0.1.md` | supporting | Supplies future Source Proxy integration title and not-started boundary. |
| `docs/source-proxy-preflight-readiness-master-roadmap-v0.1.md` | supporting | Supplies Source Proxy preflight gate state before wrapper/final CSS. |
| `docs/source-proxy-preflight-pr-8-real-preflight-coding-workflow-proof-v0.1.md` | blocked supporting | PR-8.3 remains blocked pending fresh browser/manual and real task gauntlet proof. |
| `docs/source-proxy-preflight-pr-9-design-cartographer-scout-dependency-alignment-v0.1.md` | supporting | Confirms Design, Cartographer, and Scout dependencies stay proposal-only/read-only/manual-controlled. |
| `docs/source-proxy-preflight-pr-10-wrapper-final-css-decision-gate-v0.1.md` | blocked supporting | Wrapper and final CSS remain blocked. |
| `docs/source-proxy-codex-style-ui-reduction-pr-8-3-gauntlet-master-plan-v0.1.md` | blocked supporting | PR-8.3 bridge remains docs-only and blocked before implementation and execution. |
| Earlier Design Agent Ecosystem Plans 1 through 19 | historical/supporting | Useful planning evidence, not final A-grade execution proof. |
| Missing Design Agent Ecosystem Plan 0 artifact | missing | Replaced only by Plan A equivalence for this sequence; old artifact remains absent. |

Conflict resolution rule:
If active documents conflict, follow the narrower current gate in this order: Britton prompt, Plan A closeout, master plan, Plan 20 NO-GO/remediation blockers, design-system v0.2 for design-system state, DAF-6 for Design Agent to Source Proxy boundary, and Source Proxy PR-10 for wrapper/final CSS gates. Historical docs may explain provenance but cannot grant authority over an active gate.

Phase A3 closeout gate:
GO. Active design-system and design-agent sources are unambiguous for Plan B planning.

## 6. Grade Target Table

### Phase A4: Grade Target Table

#### Increment A4.1: A-Grade Criteria Reset

Objective:
Reset grades and A evidence requirements for the six target categories.

Allowed files:
Plan A docs, Plan A closeout, and the narrow `docs/plan-index.md` entry.

Forbidden files/actions:
No grading based on unrun prompts, no readiness claim from planned evidence, no implementation.

Expected output:
Current grade, target grade, owner, evidence required for A, blocker, next plan, and GO/NO-GO table.

Codex self-checks:

- Confirm all six categories appear.
- Confirm the phrase `evidence required for A` appears.
- Confirm no category is marked final GO without evidence.

Britton manual verification check:
Confirm A requires proof, not only plan text.

Stop condition:
Stop if any category is marked GO without evidence.

Rollback/recovery note:
Downgrade to NO-GO and document missing evidence.

| Category | Current grade | Target grade | Owner lane | Evidence required for A | Blocking evidence | Next plan | Current GO/NO-GO |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Design-agent concept and architecture | B+ to A- planning | A | Design Agent docs lane | Active source-of-truth map, packet architecture, proposal-only contracts, handoff boundaries, and accepted Plan A closeout. | Missing old Plan 0 artifact is replaced only by Plan A equivalence; execution proof remains absent. | Plan C after Plan B | NO-GO for final readiness; GO for Plan B planning if Plan A accepted. |
| Subagent docs/evidence coverage | B to A- by lane | A | Design Agent helper lane | Per-subagent role, input, output, authority, fail-closed behavior, rejection cases, acceptable and blocked packet examples, manual verification, and diagnostic evidence. | Current evidence is mostly planning or supplied-data evidence; final prompt execution evidence is not complete. | Plan C | NO-GO |
| Safety boundaries | B+ docs to A- preintegration | A | Safety and authority lane | Executed or replayable proof for rights rejection, authority drift rejection, no apply, no CSS/app edit, no provider/model call, no queue/worker/autonomy, and no approval-token consumption. | Critical safety prompt execution and authority-drift counts are not_started. | Plan D | NO-GO |
| Source Proxy integration readiness | C- blocked | A for read-only design packet receive/display/score only | Source Proxy read-only bridge lane | Packet schema compatibility, read-only receive proof, read-only display proof, read-only score proof, rejection packet proof, Source Proxy owner boundary, and evidence receipt. | Receive/display/score proof is not_started; PR-8.3 remains blocked; wrapper/final CSS remain blocked. | Plan E | NO-GO |
| Design system readiness | C actual reusable system | A- minimum before gauntlet | Design system lane | Token inventory, canonical token categories, Design Vault alignment, primitive/component inventory, anatomy contracts, variant/state contracts, CSS risk map, accessibility, responsive/mobile, and visual evidence matrix. | Design-system v0.2 says actual reusable design system is C; token drift, route CSS, missing primitives, and visual evidence gaps remain. | Plan B | GO for Plan B planning only |
| Preflight design/coding gauntlet readiness | NO-GO | A-grade preflight evidence gate | Combined design/coding readiness lane | Plans A through H accepted, 100-prompt diagnostic status validated, 300-prompt mechanism approved, critical safety evidence A, and no unresolved safety blockers. | 100-prompt, 300-prompt, Visual/CSS proof, daily-use score, bounded merge approval, and PR-8.3 proof are missing/not_started. | Plan I after Plan H | NO-GO |

Phase A4 closeout gate:
GO. Grade caps are conservative, measurable, and do not claim readiness without proof.

## 7. Authority Boundary Audit

### Phase A5: Authority Boundary Audit

#### Increment A5.1: Boundary Audit

Objective:
Audit all active sources for design apply, Source Proxy, provider, queue, worker, approval-token, git, and hidden autonomy boundaries.

Allowed files:
Plan A docs, Plan A closeout, and the narrow `docs/plan-index.md` entry.

Forbidden files/actions:
No runtime inspection that executes systems, no Source Proxy proof, no app/CSS edits, no provider/model calls, no queue/worker actions, no approval-token actions, no apply, and no git mutation.

Expected output:
Authority boundary matrix and required corrections list.

Codex self-checks:

- Confirm `no apply`, `no CSS edits`, `no provider/model`, `no queue/worker`, `no approval-token`, and `no hidden autonomy` appear.
- Confirm Design Agent remains proposal-only.
- Confirm Source Proxy remains owner of diff, preview, approval, apply, and verification workflows.

Britton manual verification check:
Confirm Design Agent remains proposal-only and Source Proxy owns apply.

Stop condition:
Stop if active docs grant conflicting authority.

Rollback/recovery note:
Mark Plan A BLOCKED and use the future docs-only correction title if authority drift remains unresolved.

| Boundary | Active authority | Audit result |
| --- | --- | --- |
| Design Agent apply | Design Agent cannot apply UI. It can only later submit proposal packets. | PASS. Proposal-only boundary is consistent. |
| Source Proxy ownership | Source Proxy owns diff preview, approval binding, apply, and post-apply reporting when separately authorized. | PASS. Plan A grants no Source Proxy implementation or proof authority. |
| `/coding` | `/coding` edits are not approved by Plan A. | PASS. |
| CSS | No CSS edits and no final CSS polish. | PASS. |
| App routes/components | No app route, app UI, or component edits. | PASS. |
| Provider/model | no provider/model calls or switching implementation. | PASS. |
| Queue/worker | no queue/worker creation, mutation, or execution. | PASS. |
| Approval-token | no approval-token creation, validation, consumption, or authority change. | PASS. |
| Apply/execute-approved | no apply and no execute-approved. | PASS. |
| Git | no commit, push, branch, worktree, stash, reset, clean, checkout, or other git state mutation. | PASS. |
| Hidden autonomy | no hidden autonomy, background work, self-approval, scheduled work, or autonomous promotion. | PASS. |
| Browser/visual execution | No browser proof, Playwright run, screenshot capture, visual diff, pixel check, or image processing execution. | PASS. |

Required corrections list:

- No active authority drift correction is required for Plan A.
- Future plans must continue to quote missing evidence as missing, blocked, unavailable, or not_started until actual evidence exists.
- Plan B must remain docs-only unless Britton separately authorizes a later implementation plan.

Phase A5 closeout gate:
GO. No unresolved authority drift remains in Plan A sources.

## 8. Plan A Closeout Gate

### Phase A6: Plan A Closeout

#### Increment A6.1: Plan A Decision

Objective:
Close Plan A with GO/NO-GO for Plan B.

Allowed files:
Plan A closeout and the narrow `docs/plan-index.md` entry.

Forbidden files/actions:
All standing forbidden files and actions. Do not start Plan B.

Expected output:
Decision record with next authorized title only.

Codex self-checks:

- Run `git diff --check` for Plan A docs and `docs/plan-index.md`.
- Run focused grep for required headings and boundary terms.
- Run forbidden-claim grep for false readiness/execution wording.
- Run em dash grep and expect no lines.

Britton manual verification check:
Confirm Plan B is authorized only if Plan A evidence is accepted.

Stop condition:
Stop if any prior Phase A gate is unresolved.

Rollback/recovery note:
If any prior gate fails, leave Plan B blocked and use the recovery title only.

Plan A GO/NO-GO decision:
GO for Plan B planning, conditional on Britton accepting the Plan A closeout manual checks. NO-GO for implementation, evidence execution, Source Proxy proof, `/coding` edits, CSS edits, app edits, provider/model calls, queue/worker actions, approval-token actions, apply, execute-approved, git mutation, hidden autonomy, and final preflight readiness.

Next plan title only:
`2/10: Design Agent + Design System A-Grade Preflight Readiness Plan B: Design System Overhaul Readiness`
