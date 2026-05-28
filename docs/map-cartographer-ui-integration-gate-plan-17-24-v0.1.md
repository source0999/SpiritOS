# Map And Cartographer UI Integration Gate Plan 17/24

Status: Closed docs-only map integration gate
Plan: Plan 17/24, Map And Cartographer UI Integration Gate
Mode: ONE-LANE IF LIVE CART/MAP
Date: 2026-05-27

## Scope

Plan 16/24 closed with GO for non-Cart surface ownership and route-level proof planning, while keeping live Cart/map work, provider calls, storage mutations, implementation, and Plan 17 start as NO-GO without explicit operator approval.

The operator then requested the next plan if all good. Plan 16 manual verification passed before this packet started.

This packet records Plan 17 only. It does not start Plan 18/24.

Allowed scope:

- Static versus live boundary.
- Protected paths.
- Gate output.

Forbidden scope:

- Live map refresh.
- Runtime mutation.
- Evidence writes unless Cart gate allows.
- Cart activation, Cart promotion, live map mutation, queue/worker execution, approval-token action, provider/model call, storage mutation, route edit, CSS edit, app edit, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, or hidden autonomy.

## Phase 17.1 Map Boundary

### 17.1.1 Separate Static Map UI From Live Map State

Allowed work:

- Inspect `/map` route evidence.
- Separate static display from live/read-only Cart state.

Evidence:

- `src/app/map/page.tsx` imports live-state, approval-token, queue-status, receipt-evidence, stop-control, workflow-status, and read-only map data helpers.
- `src/app/map/cartographer-live-state.ts` fetches `/v1/cartographer/live-state`.
- `src/app/map/read-only-map-data.ts` defines `display-only-read-only-map` packets, read-only endpoints, and blocks repair, approval, apply, execute, queue, command, commit, push, or branch controls.

Boundary:

| Map area | Classification | Decision |
| --- | --- | --- |
| Static route shell and labels | `static_display` | May be discussed as UI only, but not edited in Plan 17. |
| Read-only Cartographer facts | `live_read_only_cart_data` | Cart-owned; no refresh or proof execution in Plan 17. |
| Approval, queue, workflow, receipt, stop controls | `cart_control_adjacent` | Cart-owned and blocked. |
| Map action/recommendation language | `authority_sensitive_display` | Must remain NO-GO/display-only until a future Cart gate clears. |

GO / NO-GO:

- GO for static/live boundary classification.
- NO-GO for live map refresh, map route edit, approval-token action, queue/workflow action, or action-control polish.

Next authorized increment: 17.1.2 Separate Cart evidence display from Cart runtime.

### 17.1.2 Separate Cart Evidence Display From Cart Runtime

Allowed work:

- Separate evidence display from runtime authority.

Evidence:

- Plan 7/24 records Cart state `blocked`, isolation `isolated`, promotion `not_promoted`, and activation NO-GO.
- Plan 7/24 records that future activation/runtime/queue/worker/token/trust-tier/live-map behavior changes require re-soak before production promotion.
- Cartographer live evidence paths and receipt paths are referenced as protected gate evidence in prior plans.

Boundary:

| Area | Classification | Decision |
| --- | --- | --- |
| Cart live evidence display | `cart_evidence_display` | Cart-owned, display-only, no writes. |
| Cart live receipts display | `cart_receipt_display` | Cart-owned, display-only, no writes. |
| Cart runtime state | `cart_runtime` | Blocked; no activation or mutation. |
| Cart queue/workflow state | `cart_runtime_control_adjacent` | Blocked; no queue/worker action. |

GO / NO-GO:

- GO for evidence/runtime separation.
- NO-GO for evidence writes, receipt writes, runtime mutation, queue/worker execution, Cart activation, or Cart promotion.

Next authorized increment: 17.1.3 Identify protected paths.

### 17.1.3 Identify Protected Paths

Allowed work:

- Identify protected Cart/map paths.
- Record stop conditions.

Protected paths:

| Path | Status | Reason |
| --- | --- | --- |
| `src/app/map/` | `protected_cart_path` | `/map` route and Cart display/control-adjacent helpers. |
| `src/app/v1/cartographer/` | `protected_cart_api_path` | Cartographer API cluster. |
| `source_proxy/cartographer/` | `protected_cart_runtime_path` | Cartographer runtime/services/soak behavior. |
| `source_proxy/api/cartographer.py` | `protected_cart_api_path` | Cart API bridge. |
| `docs/cartographer-live-evidence/` | `protected_cart_evidence_path` | Live/soak evidence. |
| `docs/cartographer-live-receipts/` | `protected_cart_receipt_path` | Live receipts. |
| `source_proxy/tests/test_cartographer_*` | `protected_cart_test_path` | Cartographer runtime/API proof tests. |

Stop conditions:

- Stop if future work requires any protected path above without explicit Cart gate clearance.
- Stop if map polish depends on live state, queue/workflow state, approval-token state, evidence writes, receipt writes, or re-soak behavior.

GO / NO-GO:

- GO for protected path list.
- NO-GO for protected path mutation.

### Phase 17.1 Review

Completed increments:

- 17.1.1 GO for static/live boundary; NO-GO for live refresh or action controls.
- 17.1.2 GO for evidence/runtime separation; NO-GO for evidence writes or runtime mutation.
- 17.1.3 GO for protected path list; NO-GO for protected path mutation.

Evidence exists:

- `/map` route helper evidence.
- Cart live/read-only data evidence.
- Plan 7 blocked/isolated Cart evidence.
- Protected path table.

Forbidden scope avoided:

- No live map refresh, runtime mutation, evidence write, route edit, CSS edit, approval-token action, queue/worker action, apply, execute-approved, or git mutation occurred.

Checks:

- Read-only grep checks returned map, Cart blocked/isolated, protected path, NO-GO, and re-soak evidence.

Phase result: GO to Phase 17.2; NO-GO for map mutation.

Next authorized increment: 17.2.1 If Cart accepted, define safe map refresh proof.

## Phase 17.2 Integration Proof

### 17.2.1 If Cart Accepted, Define Safe Map Refresh Proof

Allowed work:

- Define the proof that would be needed if Cart were accepted.
- Do not claim Cart is accepted.

Current Cart acceptance status:

| Gate | Status |
| --- | --- |
| Cart accepted for activation | `no_go` |
| Cart promotion | `not_promoted` |
| Cart isolation | `isolated` |
| Live map behavior change | `not_authorized` |

Safe map refresh proof required only after future acceptance:

| Required proof | Required before |
| --- | --- |
| Cart acceptance or explicit Cart-only approval | Any `/map` implementation. |
| Protected path write scope | Any `src/app/map`, Cart API, runtime, evidence, or receipt write. |
| Live state read-only proof | Any live `/map` data refresh. |
| Approval-token non-consumption proof | Any approval display change. |
| Queue/workflow non-execution proof | Any queue/workflow display change. |
| Re-soak impact decision | Any activation/runtime/queue/worker/token/trust-tier/live-map behavior change. |

GO / NO-GO:

- GO for future proof definition.
- NO-GO for treating this proof definition as Cart acceptance.

Next authorized increment: 17.2.2 If Cart blocked, define exclusion rules.

### 17.2.2 If Cart Blocked, Define Exclusion Rules

Allowed work:

- Define exclusion rules for current blocked Cart state.

Current state:

- Cart is blocked/isolated/not promoted.
- Plan 17 did not receive Cart acceptance.
- Therefore current map status must be exclusionary.

Exclusion rules:

| Rule | Decision |
| --- | --- |
| `/map` route work | Excluded from non-Cart UI/CSS/preflight work. |
| `/map/raw` route work | Excluded from non-Cart UI/CSS/preflight work. |
| Dashboard Cartographer widget action work | Excluded unless separately proven display-only and non-mutating. |
| Cartographer API work | Excluded. |
| Cart live evidence/receipt work | Excluded. |
| Cart runtime/queue/workflow/approval-token work | Excluded. |
| Map screenshot/visual proof | Excluded unless a future Cart-only visual proof plan is approved. |

GO / NO-GO:

- GO for blocked-state exclusion rules.
- NO-GO for map inclusion in non-Cart polish, CSS, visual proof, or preflight.

Next authorized increment: 17.2.3 If uncertain, keep map out of CSS/preflight.

### 17.2.3 If Uncertain, Keep Map Out Of CSS/Preflight

Allowed work:

- Define uncertainty default.

Uncertainty rule:

- If any future plan cannot prove whether a map surface is static display, live Cart state, evidence display, runtime-adjacent, queue/workflow-adjacent, or approval-token-adjacent, `/map` remains excluded.
- If a future CSS or visual preflight wants broad app coverage, `/map` must be omitted unless Cart gate has explicitly cleared the exact proof lane.
- If a future dashboard polish touches Cartographer widgets, it must either remove action/control scope or switch to Cart-only Plan 17/Cart-gate workflow.

GO / NO-GO:

- GO for fail-closed uncertainty rule.
- NO-GO for broad CSS/preflight coverage that silently includes `/map`.

### Phase 17.2 Review

Completed increments:

- 17.2.1 GO for future safe proof definition; NO-GO for Cart acceptance.
- 17.2.2 GO for blocked-state exclusion rules; NO-GO for map inclusion.
- 17.2.3 GO for fail-closed uncertainty rule; NO-GO for broad map CSS/preflight.

Evidence exists:

- Current Cart blocked/not-promoted/isolated evidence.
- Safe proof requirements.
- Exclusion rules.
- Uncertainty rule.

Forbidden scope avoided:

- No map refresh, runtime mutation, evidence write, route edit, CSS edit, screenshot proof, provider/model call, storage mutation, approval-token action, queue/worker action, apply, execute-approved, or git mutation occurred.

Checks:

- Protected path list and map status are recorded.

Phase result: GO to Phase 17.3; NO-GO for map implementation or visual proof execution.

Next authorized increment: 17.3.1 Mark map as allowed, excluded, or Cart-only.

## Phase 17.3 Gate Output

### 17.3.1 Mark Map As Allowed, Excluded, Or Cart-Only

Allowed work:

- Output current map status.

Map status:

| Surface | Status | Reason |
| --- | --- | --- |
| `/map` | `cart_only_excluded_from_non_cart` | Depends on Cart live/read-only helpers and Cart blocked state. |
| `/map/raw` | `cart_only_excluded_from_non_cart` | Deep Cart diagnostics. |
| `src/app/map/` | `protected_cart_path` | Cart display/control-adjacent source. |
| `/v1/cartographer/*` | `cart_only_excluded_from_non_cart` | Cart API cluster. |
| Cart dashboard widgets | `cart_only_or_display_only_with_future_proof` | Must not carry action/control mutation. |

Gate output:

- Map is not allowed for non-Cart UI polish.
- Map is not allowed for broad CSS/preflight.
- Map is Cart-only unless a future Cart gate explicitly allows exact work.

GO / NO-GO:

- GO for map status output.
- NO-GO for non-Cart map work.

Next authorized increment: 17.3.2 Define required soak/re-soak impact.

### 17.3.2 Define Required Soak/Re-Soak Impact

Allowed work:

- Define re-soak rule for map/Cart work.

Re-soak impact:

| Future change type | Re-soak impact |
| --- | --- |
| Static copy-only map label change with no live state behavior | Requires future Cart-only approval; re-soak impact must still be reviewed. |
| Live map refresh or endpoint behavior change | Re-soak required before production promotion. |
| Cart runtime behavior change | Re-soak required. |
| Queue/worker behavior change | Re-soak required. |
| Approval-token behavior change | Re-soak required. |
| Trust-tier behavior change | Re-soak required. |
| Evidence/receipt write behavior change | Re-soak required. |
| Dashboard Cartographer widget action behavior | Re-soak impact review required; likely Cart-only. |

GO / NO-GO:

- GO for re-soak impact rule.
- NO-GO for claiming map work has no soak impact without explicit future review.

Next authorized increment: 17.3.3 Output next authorized visual plan.

### 17.3.3 Output Next Authorized Visual Plan

Allowed work:

- Name the next roadmap plan only.
- Do not start it.

Next roadmap plan:

`Plan 18/24: Controlled Multi-Agent And Subagent Orchestration Boundary`

GO / NO-GO:

- GO for next-plan naming.
- NO-GO for starting Plan 18 without explicit operator approval.

### Phase 17.3 Review

Completed increments:

- 17.3.1 GO for map status output; NO-GO for non-Cart map work.
- 17.3.2 GO for re-soak impact rule; NO-GO for silent no-impact claims.
- 17.3.3 GO for next-plan naming; NO-GO for Plan 18 start.

Evidence exists:

- Map status table.
- Re-soak impact table.
- Next plan title.

Forbidden scope avoided:

- No live map refresh, runtime mutation, evidence write, route edit, CSS edit, provider/model call, storage mutation, approval-token action, queue/worker action, apply, execute-approved, or git mutation occurred.

Checks:

- Protected path list and map status are recorded.

Phase result: GO to Plan 17 closeout; NO-GO for Plan 18 start.

Next authorized increment: Plan 17/24 closeout.

## Plan 17/24 Closeout

Phase review:

- Phase 17.1 Map Boundary: GO for static/live/evidence/runtime separation and protected paths; NO-GO for map mutation.
- Phase 17.2 Integration Proof: GO for future proof and blocked-state exclusion rules; NO-GO for Cart acceptance or visual proof execution.
- Phase 17.3 Gate Output: GO for Cart-only/excluded map status and re-soak rule; NO-GO for Plan 18 start.

Increment review:

- 17.1.1 Static versus live boundary: complete.
- 17.1.2 Evidence display versus runtime: complete.
- 17.1.3 Protected paths: complete.
- 17.2.1 Future accepted-Cart proof: defined; Cart remains not accepted.
- 17.2.2 Blocked-Cart exclusion rules: complete.
- 17.2.3 Uncertainty default: exclude map from CSS/preflight.
- 17.3.1 Map status: `cart_only_excluded_from_non_cart`.
- 17.3.2 Re-soak impact: future live/runtime/queue/token/trust/evidence changes require re-soak review or re-soak.
- 17.3.3 Next visual plan: Plan 18 named only.

Evidence exists:

- Protected path list.
- Map status.
- Cart blocked/isolated/not-promoted evidence.
- Static/live/evidence/runtime separation.
- Re-soak impact rule.

Forbidden actions did not occur:

- No live map refresh.
- No runtime mutation.
- No evidence writes.
- No route edits.
- No CSS edits.
- No provider/model calls.
- No storage mutations.
- No approval-token action.
- No queue/worker execution.
- No Cart activation or promotion.
- No apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, or hidden autonomy.

Final map decision:

- Map status: `cart_only_excluded_from_non_cart`.
- Map is excluded from non-Cart UI polish, broad CSS/preflight, and visual proof unless a later Cart gate explicitly approves exact scope.
- Live state remains protected.

Final Plan 17/24 result: GO for map/Cartographer integration gate classification; NO-GO for live map work, map inclusion in non-Cart visual/CSS work, runtime mutation, evidence writes, Cart activation, or Plan 18 start without explicit operator approval.

Next roadmap plan only: `Plan 18/24: Controlled Multi-Agent And Subagent Orchestration Boundary`.

## Terminal Verification

Run from `/home/source/SpiritOS`:

```bash
cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal && grep -nE "Plan 17/24|static_display|live_read_only_cart_data|cart_control_adjacent|cart_evidence_display|protected_cart_path|protected_cart_api_path|protected_cart_runtime_path|Cart accepted|exclusion rules|CSS/preflight|cart_only_excluded_from_non_cart|re-soak|NO-GO|Plan 18/24" docs/map-cartographer-ui-integration-gate-plan-17-24-v0.1.md && grep -nE "LIVE_STATE_ENDPOINT|QUEUE_RUN_NEXT_ENDPOINT|APPROVAL_TOKEN_ENDPOINT|display-only-read-only-map|queue execution authority is not granted|Cart state: .*blocked|Cart isolation: .*isolated|not_promoted|re-soak|required later|NO-GO" src/app/map/cartographer-live-state.ts src/app/map/cartographer-queue-status.ts src/app/map/cartographer-approval-token.ts src/app/map/read-only-map-data.ts docs/cartographer-live-evidence/cartographer-plan-7-24-activation-boundary-resoak-decision-v0.1.md && git diff --check -- docs/map-cartographer-ui-integration-gate-plan-17-24-v0.1.md
```

Expected output:

- Git status shows this Plan 17 packet as untracked with prior roadmap docs still untracked.
- Plan 17 grep prints static/live boundary, evidence/runtime separation, protected paths, exclusion rules, Cart-only map status, re-soak impact, NO-GO boundaries, and Plan 18 title.
- Map/Cart grep prints live-state, queue, approval-token, read-only map, Cart blocked/isolated/not-promoted, re-soak, and NO-GO evidence.
- `git diff --check` prints no output.
