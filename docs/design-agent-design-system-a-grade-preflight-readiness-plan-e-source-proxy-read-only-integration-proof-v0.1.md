# Design Agent + Design System A-Grade Preflight Readiness Plan E: Source Proxy Read-Only Integration Proof v0.1

Status: docs-only Plan E complete

Date: 2026-05-24

Count: 5/10

Owner lane: Source Proxy read-only bridge lane

Prerequisite: Plan D GO for planning

Decision: GO for Plan F planning only after Britton accepts the Plan E closeout and manual checks.

## 1. Purpose

Plan E defines the Source Proxy read-only integration proof model needed before diagnostic batch harness proof planning. It brings Source Proxy integration readiness from C- blocked to an A target for read-only design packet receive, display, score, reject, receipt, and owner-boundary evidence only.

Plan E is docs-only. It does not run Source Proxy, edit Source Proxy runtime, edit `/coding`, edit app routes, edit CSS, call providers/models, execute queues/workers, read or consume approval tokens, apply changes, mutate git state, or create hidden autonomy.

Plan E does not start Plan F.

Plan E does not claim Source Proxy proof ran.

Plan E does not claim read-only receive/display/score proof ran.

## 2. Grade And Lane

| Field | Value |
| --- | --- |
| Current grade | C- blocked |
| Target grade | A for read-only design packet receive/display/score only |
| Owner lane | Source Proxy read-only bridge lane |
| Allowed next plan | Plan F only after Plan E closeout is accepted |
| Current implementation status | NO-GO |
| Current evidence execution status | NO-GO |

## 3. Standing Forbidden Set

- No runtime code edits.
- No Source Proxy runtime edits.
- No CSS edits.
- No app route edits.
- No `/coding` UI edits.
- No provider/model calls.
- No queue or worker execution.
- No approval-token reads, writes, validation, creation, or consumption.
- No apply.
- No execute-approved.
- No browser, screenshot, or visual proof execution.
- No package, config, env, auth, generated/cache, protected-path, test, or app UI edits.
- No commit, push, branch, worktree, stash, reset, clean, checkout, or git mutation.
- No self-approval or hidden autonomy.
- No claim that Source Proxy proof ran.
- No claim that read-only proof ran.
- No claim that preflight readiness passed.

## 4. Evidence Inputs

| Evidence source | Plan E handling |
| --- | --- |
| `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md` | Supplies Plan E scope, phases, gates, and next authorized title. |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-d-safety-boundary-a-grade-proof-plan-v0.1.md` | Supplies safety proof preconditions and hard failure caps. |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-d-closeout-v0.1.md` | Supplies Plan D closeout and Plan E authorization boundary. |
| `docs/design-agent-ecosystem-plan-12-design-agent-to-source-proxy-read-only-bridge-plan-v0.1.md` | Supplies docs-only bridge contract, read-only packet fields, display/scoring constraints, and B-grade limitation. |
| `docs/source-proxy-preflight-pr-8-real-preflight-coding-workflow-proof-v0.1.md` | Supplies Source Proxy preflight dependency and PR-8.3 blocked status. |
| `docs/source-proxy-preflight-pr-9-design-cartographer-scout-dependency-alignment-v0.1.md` | Supplies proposal-only Design Agent and read-only Cartographer boundary alignment. |
| `docs/source-proxy-preflight-pr-10-wrapper-final-css-decision-gate-v0.1.md` | Supplies wrapper/final CSS blocked status and separate request boundary. |

## 5. Phase E1: Packet Schema Compatibility

### Increment E1.1: Schema Compatibility Plan

Objective:

Align Design Agent packet fields with Source Proxy read-only receive, display, and score needs.

Allowed files:

Plan E docs, Plan E closeout, and narrow `docs/plan-index.md` update.

Forbidden files/actions:

No Source Proxy runtime edits, no Source Proxy execution, no `/coding` edits, no provider/model calls, no approval-token actions, no apply, and no git mutation.

Expected output:

Compatibility table with required, optional, rejected, and unknown fields.

Codex self-checks:

Confirm `packet schema`, `read-only`, `receive`, `display`, `score`, `rejected field`, and `unknown field` appear.

Britton manual verification check:

Confirm schema does not include apply authority, approval-token authority, provider/model authority, queue/worker authority, or git authority.

Stop condition:

Stop if schema compatibility requires Source Proxy mutation now.

Rollback or recovery note:

Keep mismatches as blockers and request Plan E recovery.

| Field group | Fields | Handling | Grade impact |
| --- | --- | --- | --- |
| Required packet identity | `packet_id`, `packet_version`, `created_at`, `source_plan`, `owner_lane` | Required for receive and audit. | Missing identity blocks. |
| Required authority boundary | `no_authority_statement`, `forbidden_files`, `forbidden_actions`, `allowed_files_proposal_only` | Required for safe display. | Missing boundary blocks. |
| Required source rights | `source_rights_status`, `source_card_refs`, `rights_rejection_reasons` | Required before usefulness scoring. | Missing or rejected rights blocks use. |
| Required design evidence | `design_system_refs`, `token_refs`, `component_refs`, `visual_evidence_status`, `unavailable_evidence` | Required for display and advisory score. | Missing evidence lowers score or blocks if hidden. |
| Required safety summary | `safety_summary`, `authority_drift_flags`, `blocked_reasons`, `Plan D cap status` | Required for reject and safety score. | Missing safety summary blocks. |
| Optional handoff | `Source Proxy handoff summary`, `manual_checks`, `rollback_notes`, `expected_receipts` | Optional but recommended for useful handoff. | Missing handoff lowers usefulness. |
| Optional scoring hints | `css_component_relevance`, `visual_quality_notes`, `design_system_alignment_notes` | Advisory only. | Cannot approve apply. |
| Rejected fields | `apply_intent`, `execute_approved_intent`, `approval_token`, `provider_call_request`, `queue_worker_request`, `git_mutation_request`, `runtime_file_edit_request`, `hidden_autonomy_request` | Rejected field forces blocked packet. | Any present rejected field keeps Plan E NO-GO. |
| Unknown fields | Any unrecognized authority or execution field | Display as unknown and block if authority-bearing. | Unknown unsafe fields block. |

Closeout gate:

GO. Packet schema compatibility is defined without apply authority.

## 6. Phase E2: Read-Only Receive Proof

### Increment E2.1: Receive Proof Recipe

Objective:

Define proof that Source Proxy can receive Design Agent packets read-only.

Allowed files:

Plan E docs and closeout.

Forbidden files/actions:

No Source Proxy execution in this plan, no endpoint calls, no database writes, no queue/worker action, no approval-token action, and no apply.

Expected output:

Receive proof steps, evidence receipt fields, and expected no-apply result.

Codex self-checks:

Confirm `read-only receive proof`, `no apply`, `received_read_only`, and `runtime_mutation: false` appear.

Britton manual verification check:

Confirm future proof is display/input only and cannot call apply or consume approval tokens.

Stop condition:

Stop if receive proof requires an apply route, execute-approved route, or Source Proxy runtime edit inside Plan E.

Rollback or recovery note:

Require Source Proxy owner decision before any future implementation.

Future receive proof recipe:

1. Submit an inert Design Agent packet to the future read-only receive surface.
2. Confirm packet is parsed without runtime mutation.
3. Confirm rejected fields are detected before display or score.
4. Confirm no approval-token read, validation, creation, or consumption occurs.
5. Confirm no apply, execute-approved, queue, worker, provider/model, or git action occurs.

Expected receipt fields:

| Field | Expected value |
| --- | --- |
| `received_read_only` | `true` |
| `packet_parsed` | `true` for valid packet |
| `packet_persisted_runtime` | `false` unless separately approved |
| `apply_attempted` | `false` |
| `execute_approved_attempted` | `false` |
| `approval_consumed` | `false` |
| `provider_call_count` | `0` |
| `queue_items_created` | `0` |
| `workers_started` | `0` |
| `runtime_mutation` | `false` |
| `git_mutation` | `false` |

Closeout gate:

GO. Receive proof can be run later without apply.

## 7. Phase E3: Read-Only Display Proof

### Increment E3.1: Display Proof Recipe

Objective:

Define proof that packets display clearly without granting action authority.

Allowed files:

Plan E docs and closeout.

Forbidden files/actions:

No `/coding` edit, no design-mode UI edit, no app UI edit, no CSS edit, no browser proof, and no screenshot capture now.

Expected output:

Display proof target, receipt fields, and blocked-state expectations.

Codex self-checks:

Confirm `display proof`, `read-only`, `blocked`, `no controls`, and `not_started` appear.

Britton manual verification check:

Confirm UI display is not required until separately approved.

Stop condition:

Stop if display proof edits UI in this plan.

Rollback or recovery note:

Split display implementation into a future Source Proxy implementation plan.

Future display requirements:

| Display area | Required content | Forbidden content |
| --- | --- | --- |
| Packet status | received, blocked, caution, not_started, unavailable | Apply-ready status without Source Proxy proof |
| Source rights | source card refs, rights status, rejection reason | Hidden rejected or unclear rights |
| Visual evidence | screenshot target status, not_started/unavailable labels | Fake visual proof or implied screenshot run |
| Safety boundary | no-authority statement, forbidden actions, blocked reasons | Approval or execute controls |
| Handoff | proposal-only summary, allowed files proposal, rollback notes | Diff application, approval-token, or queue controls |
| Score | advisory score only | Any score that grants apply |

Surface decision status:

Display surface implementation is not_started. Existing `/coding` trial widget, a design-mode surface, or another read-only display may be considered later only with separate Source Proxy owner approval.

Closeout gate:

GO. Display proof scope is read-only and implementation remains not_started.

## 8. Phase E4: Read-Only Score Proof

### Increment E4.1: Score Proof Recipe

Objective:

Define proof that packets can be scored for usefulness, safety, visual evidence, CSS/component relevance, and Source Proxy handoff quality.

Allowed files:

Plan E docs and closeout.

Forbidden files/actions:

No runtime scoring implementation, no provider/model scoring call, no queue/worker action, no apply approval, and no Source Proxy execution.

Expected output:

Score proof matrix and expected counters.

Codex self-checks:

Confirm `score proof`, `usefulness`, `safety`, `visual evidence`, `CSS/component`, and `advisory` appear.

Britton manual verification check:

Confirm scoring does not approve apply.

Stop condition:

Stop if score proof grants approval, apply, execute-approved, or provider/model authority.

Rollback or recovery note:

Downgrade scoring to advisory only and block Plan E until corrected.

| Score category | Inputs | Output | Cap |
| --- | --- | --- | --- |
| usefulness | complete packet, clear handoff, allowed files proposal, rollback notes | advisory usefulness score | Cannot override safety block. |
| safety | Plan D caps, forbidden fields, blocked reasons, no-authority statement | PASS/BLOCKED/CAUTION | Any critical unsafe pass blocks. |
| visual evidence | screenshot targets, not_started/unavailable labels, future receipt refs | advisory visual evidence status | Missing proof cannot be treated as pass. |
| CSS/component relevance | Plan B contracts, component refs, CSS risk notes | advisory relevance score | Cannot authorize CSS edits. |
| Source Proxy handoff quality | owner boundary, no apply, expected checks, receipt fields | advisory handoff score | Cannot transfer apply ownership. |

Expected counters:

| Counter | Meaning |
| --- | --- |
| `useful_count` | Packets useful for future Source Proxy review. |
| `blocked_count` | Packets blocked due to safety, schema, rights, or authority issues. |
| `unsafe_count` | Packets that attempted unsafe authority or hidden execution. |
| `false_block_count` | Safe docs-only packets that were blocked and need manual review. |
| `unavailable_count` | Evidence correctly labeled unavailable or not_started. |

Closeout gate:

GO. Scoring is advisory and auditable.

## 9. Phase E5: Rejection Packet Proof

### Increment E5.1: Rejection Proof Recipe

Objective:

Define proof that bad packets are rejected and reasons are visible.

Allowed files:

Plan E docs and closeout.

Forbidden files/actions:

No runtime execution, no Source Proxy call, no apply, no approval-token action, and no mutation now.

Expected output:

Rejection packet set and receipt format.

Codex self-checks:

Confirm `rejection packet`, `blocked reason`, `authority drift`, and `rejected field` appear.

Britton manual verification check:

Confirm rejected packet cannot be applied.

Stop condition:

Stop if rejection only warns but permits unsafe flow.

Rollback or recovery note:

Block Plan E until reject behavior is defined.

| Rejection packet | Trigger | Expected blocked reason |
| --- | --- | --- |
| Missing no-authority statement | `no_authority_statement` absent | `missing_no_authority_statement` |
| Missing forbidden actions | `forbidden_actions` absent | `missing_forbidden_actions` |
| False integration approval | Packet claims Source Proxy proof passed without receipt | `false_source_proxy_proof_claim` |
| Apply intent | `apply_intent` or execute-approved intent present | `apply_not_authorized` |
| Approval token | Approval-token field or request present | `approval_token_not_authorized` |
| Provider/model request | Provider/model call requested | `provider_model_not_authorized` |
| Queue/worker request | Queue or worker action requested | `queue_worker_not_authorized` |
| Git mutation request | commit, push, branch, stash, reset, clean, checkout, or worktree request | `git_mutation_not_authorized` |
| Hidden autonomy request | background task or self-approval requested | `hidden_autonomy_not_authorized` |
| Invalid source rights | missing, unclear, rejected, or mismatch source rights | `source_rights_blocked` |

Closeout gate:

GO. Rejection evidence is clear.

## 10. Phase E6: Source Proxy Owner Boundary

### Increment E6.1: Owner Boundary Record

Objective:

Record that Source Proxy/Coding Agent own diff, preview, apply, and verification.

Allowed files:

Plan E docs and closeout.

Forbidden files/actions:

No owner transfer, no runtime edits, no apply, no Source Proxy execution, and no `/coding` edits.

Expected output:

Boundary table and handoff rule.

Codex self-checks:

Confirm `Coding Agent`, `Source Proxy`, `diff`, `apply`, `verification`, and `proposal-only` appear.

Britton manual verification check:

Confirm Design Agent remains proposal-only.

Stop condition:

Stop if the design lane claims apply ownership.

Rollback or recovery note:

Correct boundary or stop Plan E.

| Capability | Owner | Design Agent Plan E status |
| --- | --- | --- |
| Design packet proposal | Design Agent | proposal-only |
| Source rights summary | Design Agent helper lane | advisory/proposal-only |
| Component and CSS relevance notes | Design Agent helper lane | advisory/proposal-only |
| Diff generation | Source Proxy/Coding Agent | not owned by Design Agent |
| Preview | Source Proxy/Coding Agent | not owned by Design Agent |
| Apply or execute-approved | Source Proxy/Coding Agent under separate approval | not authorized |
| Verification | Source Proxy/Coding Agent plus Britton manual checks | not executed in Plan E |
| Approval-token handling | Source Proxy owner under separate gated plan | forbidden in Plan E |

Handoff rule:

Design Agent may propose bounded, inert packet content. Source Proxy/Coding Agent decides whether and how to convert that packet into any future coding workflow under separate approval.

Closeout gate:

GO. Owner boundaries are explicit.

## 11. Phase E7: `/coding` Trial Widget Or Design-Mode Surface Decision

### Increment E7.1: Surface Decision Record

Objective:

Decide whether future proof uses existing `/coding` trial widget, a design-mode surface, or another read-only display.

Allowed files:

Plan E docs and closeout.

Forbidden files/actions:

No `/coding` edit now, no UI implementation, no route edit, no CSS edit, and no Source Proxy runtime edit.

Expected output:

Decision record with prerequisites for any future UI implementation.

Codex self-checks:

Confirm `/coding`, `trial widget`, `design-mode`, `separate approval`, and `not_started` appear.

Britton manual verification check:

Confirm decision does not start widget work.

Stop condition:

Stop if surface decision implies implementation authority.

Rollback or recovery note:

Leave surface undecided and block Plan E.

Decision:

Future proof should prefer a read-only design-mode display surface if Source Proxy owner accepts it. Existing `/coding` trial widget remains a candidate only if Britton and the Source Proxy owner explicitly approve that surface in a future implementation plan. Plan E grants no `/coding` edit authority.

Prerequisites for any future surface:

| Prerequisite | Required status |
| --- | --- |
| Source Proxy owner acceptance | Required |
| Plan D safety caps | Accepted |
| Read-only schema | Accepted |
| No action controls | Required |
| No apply or execute-approved | Required |
| Manual proof receipt | Required |
| Separate implementation approval | Required |

Closeout gate:

GO. Surface decision is bounded and not_started.

## 12. Phase E8: Evidence Receipt Format

### Increment E8.1: Read-Only Proof Receipt

Objective:

Define receipt fields for receive, display, score, rejection, owner boundary, and unavailable evidence.

Allowed files:

Plan E docs and closeout.

Forbidden files/actions:

No runtime receipt storage, no database write, no Source Proxy execution, no browser proof, and no screenshot proof.

Expected output:

Receipt template.

Codex self-checks:

Confirm `receipt`, `receive`, `display`, `score`, `rejection`, `owner boundary`, and `unavailable` appear.

Britton manual verification check:

Confirm receipt is enough to evaluate a future Plan E run later.

Stop condition:

Stop if receipt hides blocked or unsafe counts.

Rollback or recovery note:

Add missing counters before closeout.

Receipt template:

| Receipt field | Required value or note |
| --- | --- |
| `plan_id` | Plan E |
| `packet_id` | Required |
| `source_proxy_surface` | `/coding`, design-mode, other, or not_started |
| `receive_status` | received, blocked, not_started, or unavailable |
| `display_status` | displayed, blocked, not_started, or unavailable |
| `score_status` | scored, blocked, not_started, or unavailable |
| `rejection_status` | rejected as expected, failed to reject, not_started, or unavailable |
| `owner_boundary_status` | accepted or blocked |
| `blocked_reasons` | Required when blocked |
| `unsafe_count` | Required |
| `blocked_count` | Required |
| `false_block_count` | Required |
| `unavailable_count` | Required |
| `apply_attempted` | must be false |
| `execute_approved_attempted` | must be false |
| `approval_token_consumed` | must be false |
| `provider_call_count` | must be 0 |
| `queue_items_created` | must be 0 |
| `workers_started` | must be 0 |
| `runtime_mutation` | must be false |
| `git_mutation` | must be false |
| `manual_reviewer` | Britton or named reviewer |
| `next_plan_decision` | GO/NO-GO for Plan F planning only |

Closeout gate:

GO. Receipt supports audit.

## 13. Phase E9: Plan E Closeout

### Increment E9.1: Source Proxy Read-Only Decision

Objective:

Decide GO/NO-GO for Plan F.

Allowed files:

Plan E closeout and optional `docs/plan-index.md` note.

Forbidden files/actions:

Standing forbidden set.

Expected output:

Source Proxy read-only integration readiness grade and next authorized title only.

Codex self-checks:

Run docs diff check, read-only grep, forbidden-claim grep, focused status, and em dash grep.

Britton manual verification check:

Confirm no design apply was allowed.

Stop condition:

Stop if receive, display, score, or reject proof remains undefined or unsafe.

Rollback or recovery note:

Request Plan E recovery.

Plan E GO/NO-GO decision gate:

GO for Plan F planning only. Plan E defines read-only receive, display, score, rejection, owner-boundary, surface-decision, and receipt proof models. NO-GO remains for Source Proxy runtime implementation, Source Proxy proof execution, `/coding` edits, app/CSS edits, provider/model calls, queues/workers, approval-token actions, apply, git mutation, browser proof, visual proof, and final readiness.

Next authorized title only:

6/10: Design Agent + Design System A-Grade Preflight Readiness Plan F: Diagnostic Batch Harness Proof
