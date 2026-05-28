# Surface Ownership Plan 16/24 Chat Oracle Dashboard And Supporting Surfaces

Status: Closed docs-only surface ownership review
Plan: Plan 16/24, Chat, Oracle, Dashboard, And Supporting Surface Ownership
Mode: MULTI-LANE ELIGIBLE IF NON-CART
Date: 2026-05-27

## Scope

Plan 15/24 closed with GO for manual-controlled advisory continuation, while keeping autonomous discovery, writes, proxy memory writes, coding context writes, promotion finalization, Scout intake calls, Cart touch, Mac hidden workers, implementation, and Plan 16 start as NO-GO without explicit operator approval.

The operator then requested the next plan if all good. Plan 15 manual verification passed before this packet started.

This packet records Plan 16 only. It does not start Plan 17/24.

Allowed scope:

- Ownership map.
- Route constraints.
- Support lane readiness.

Forbidden scope:

- Live Cart/map mutation.
- Provider calls.
- Storage mutations without approval.
- Runtime start, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, Scout writes, Source Proxy writes, Cartographer activation, or hidden autonomy.

## Phase 16.1 Surface Ownership

### 16.1.1 Chat Ownership

Allowed work:

- Inspect `/chat` route ownership.
- Classify Chat as roadmap driver or support surface.

Evidence:

- `src/app/chat/page.tsx` declares `/chat` as the Trinity chat workspace and renders `SpiritTrinityChatShell`.
- `src/components/chat/SpiritChat.tsx` records `/api/spirit` as the default API and uses `runtimeSurface` to distinguish chat and oracle behavior.
- Chat components reference Dexie/local storage for saved workspace behavior.

Ownership decision:

| Surface | Route | Owner lane | Surface class | Runtime/storage risk | Plan 16 decision |
| --- | --- | --- | --- | --- | --- |
| Chat | `/chat` | Chat lane | Roadmap driver | `/api/spirit`, TTS/STT adjacent APIs, Dexie/local storage | Eligible for future non-Cart work only with explicit provider and storage proof needs. |

GO / NO-GO:

- GO for Chat ownership classification.
- NO-GO for provider calls, storage writes, saved-thread mutation, or Chat implementation in Plan 16.

Next authorized increment: 16.1.2 Oracle ownership.

### 16.1.2 Oracle Ownership

Allowed work:

- Inspect `/oracle` route ownership.
- Classify Oracle as roadmap driver or support surface.

Evidence:

- `src/app/oracle/page.tsx` declares `/oracle` as a voice-first ephemeral Oracle lane.
- The route comment records `runtimeSurface=oracle -> /api/spirit + ORACLE_OLLAMA_MODEL when env set`.
- The same route comment records no Dexie threads in the MVP.
- `src/components/oracle/OracleVoiceSurface.tsx` uses `/api/spirit`, `/api/tts`, local storage activity state, and optional STT paths.

Ownership decision:

| Surface | Route | Owner lane | Surface class | Runtime/storage risk | Plan 16 decision |
| --- | --- | --- | --- | --- | --- |
| Oracle | `/oracle` | Oracle lane | Roadmap driver | `/api/spirit`, `ORACLE_OLLAMA_MODEL`, `/api/tts`, optional STT, local activity state | Eligible for future non-Cart work only with explicit provider, voice, and local-storage proof needs. |

GO / NO-GO:

- GO for Oracle ownership classification.
- NO-GO for provider calls, voice backend calls, env changes, storage writes, or Oracle implementation in Plan 16.

Next authorized increment: 16.1.3 Dashboard ownership.

### 16.1.3 Dashboard Ownership

Allowed work:

- Inspect dashboard ownership.
- Separate dashboard support widgets from Cart-owned areas.

Evidence:

- `src/app/(dashboard)/page.tsx` is the dashboard route and renders `SpiritDashboardHome`.
- Dashboard route fetches Scout overview/source/candidate/discovery-job data from Scout APIs when available.
- Dashboard components include Chat, Oracle, Scout, telemetry, storage, backend health, test runner, blueprint, and Cartographer widgets.
- Plan 6/24 records dashboard planning as GO and dashboard implementation as NO-GO in that plan.

Ownership decision:

| Surface | Route/component area | Owner lane | Surface class | Runtime/storage risk | Plan 16 decision |
| --- | --- | --- | --- | --- | --- |
| Dashboard shell | `/` via `src/app/(dashboard)/page.tsx` | Dashboard support lane | Supporting UI | Scout API fetches, telemetry widgets, mixed action widgets | Eligible for future non-Cart display/support work with exact route proof. |
| Dashboard Chat widgets | `HomelabChatCoreWidget`, dashboard shell links | Chat support | Supporting UI | Display-only unless wired to runtime | Eligible if display-only or Chat proof exists. |
| Dashboard Oracle widgets | `HomelabOracleVoiceWidget`, `OracleStagePanel` | Oracle support | Supporting UI | `/api/spirit/health`, `/api/tts` labels | Eligible if provider/voice calls are explicitly bounded. |
| Dashboard Scout widgets | `HomelabScoutIntelligenceWidget`, `ScoutIntelligenceCenter` | Scout support | Supporting UI | Scout API actions can mutate Scout state | NO-GO for writes; display/manual-controlled only. |
| Dashboard Cartographer widgets | `HomelabCartographerWidget`, blueprint/Cart controls | Cartographer lane | Cart-owned support UI | `/v1/cartographer/*`, approval/queue/workflow risks | Blocked unless Cart gate clears or display-only proof is explicit. |

GO / NO-GO:

- GO for dashboard ownership map.
- NO-GO for dashboard implementation, Scout mutation, Cart mutation, provider calls, storage mutation, or action wiring in Plan 16.

### Phase 16.1 Review

Completed increments:

- 16.1.1 GO for Chat ownership; NO-GO for provider/storage work.
- 16.1.2 GO for Oracle ownership; NO-GO for provider/voice/env/storage work.
- 16.1.3 GO for Dashboard ownership; NO-GO for mixed-surface implementation.

Evidence exists:

- `/chat`, `/oracle`, dashboard, and component route evidence.
- Plan 6 dashboard planning boundary.

Forbidden scope avoided:

- No runtime start, provider call, storage mutation, dashboard code edit, Chat edit, Oracle edit, Scout write, Cart touch, apply, execute-approved, or git mutation occurred.

Checks:

- Read-only `grep`/`sed` inspection returned route and component evidence.

Phase result: GO to Phase 16.2; NO-GO for implementation.

Next authorized increment: 16.2.1 Exclude live Cart/map unless Cart gate clears.

## Phase 16.2 Route Constraints

### 16.2.1 Exclude Live Cart/Map Unless Cart Gate Clears

Allowed work:

- Define Cart/map exclusion rule.
- Preserve Cartographer isolated state.

Evidence:

- Plan 7/24 records Cart state `blocked`, isolation `isolated`, promotion `not_promoted`, and activation NO-GO.
- Plan 7 permits non-Cart lanes only if they do not touch Cart, map, live evidence, runtime, queues, workers, approval tokens, trust tiers, or soak behavior.
- `src/app/map/page.tsx` imports live Cartographer state helpers, queue status, approval token status, workflow status, receipt evidence, and read-only map data.
- `src/app/map/read-only-map-data.ts` records read-only Cartographer endpoints and blocks mutating files, queues, events, approvals, evidence, receipts, audit ledgers, branches, worktrees, runtime, tests, dashboard, `/coding`, package/config/env, generated, Scout, API, or Source Proxy state.

Excluded surfaces:

| Surface | Route/path | Status | Reason |
| --- | --- | --- | --- |
| Map shell | `/map`, `/map/raw` | `cart_only_blocked` | Live/read-only Cartographer display depends on blocked Cart gate. |
| Cartographer API cluster | `/v1/cartographer/*` | `cart_only_blocked` | Approval, queue, workflow, evidence, and runtime authority risks. |
| Cart live evidence and receipts | `docs/cartographer-live-evidence`, `docs/cartographer-live-receipts` | `cart_only_blocked` | Live evidence/soak boundary. |
| Cart runtime/source | `source_proxy/cartographer`, `source_proxy/api/cartographer.py`, `src/app/map` | `cart_only_blocked` | Cart-owned protected path set. |

GO / NO-GO:

- GO for live Cart/map exclusion.
- NO-GO for map refresh, live map mutation, Cart evidence writes, Cart runtime work, approval-token action, queue/workflow action, or Cart activation.

Next authorized increment: 16.2.2 Separate display-only surfaces from runtime surfaces.

### 16.2.2 Separate Display-Only Surfaces From Runtime Surfaces

Allowed work:

- Classify surface route types.

Route constraints:

| Route/surface | Surface type | Runtime/storage dependencies | Plan 16 eligibility |
| --- | --- | --- | --- |
| `/chat` | Runtime-backed app surface | `/api/spirit`, Dexie/local storage, TTS/STT adjacent APIs | Eligible later only with provider/storage proof. |
| `/oracle` | Runtime-backed app surface | `/api/spirit`, Oracle model env, TTS/STT, local activity state | Eligible later only with provider/voice/storage proof. |
| `/` dashboard shell | Mixed support surface | Scout fetches, telemetry, widget action risks | Eligible later for display-only non-Cart work with route proof. |
| `/intelligence` | Scout/intelligence surface | Scout state/action risks | Manual-controlled advisory only; writes blocked. |
| `/coding` | Source Proxy surface | task routes, verification, apply gates | Source Proxy lane only. |
| `/map` and `/map/raw` | Cart display/control-adjacent surface | Cartographer live/read-only endpoints, approval, queue, workflow | Excluded until Cart gate clears. |
| `/api/spirit`, `/api/tts`, `/api/stt/*` | Runtime/provider API | provider/voice/backend side effects | NO-GO without explicit provider proof plan. |
| `/api/scout/*` | Scout API | Scout writes/promotion/discovery risks | Manual-controlled read/display only unless separately approved. |
| `/v1/cartographer/*` | Cart API | live Cart/approval/queue/workflow/evidence risks | Excluded until Cart gate clears. |

GO / NO-GO:

- GO for display/runtime separation.
- NO-GO for treating a display surface as safe when it hides runtime, provider, storage, Scout, Source Proxy, or Cart mutation.

Next authorized increment: 16.2.3 Define route-level proof needs.

### 16.2.3 Define Route-Level Proof Needs

Allowed work:

- Define proof requirements before future route work.

Route-level proof needs:

| Surface | Required proof before implementation |
| --- | --- |
| Chat | Provider call boundary, Dexie/local storage mutation boundary, `/api/spirit` behavior proof, TTS/STT non-regression if touched. |
| Oracle | Oracle runtimeSurface proof, provider/env boundary, `/api/spirit` and `/api/tts` behavior proof, no saved-thread/Dexie claim unless approved. |
| Dashboard non-Cart shell | Widget inventory, action-button audit, route fetch map, display-only proof, no Scout/Cart/Source Proxy mutation. |
| Dashboard Scout widgets | Manual-controlled Scout proof, writes false, no discovery execution, no promotion finalization. |
| Dashboard Cartographer widgets | Cart gate clearance or explicit display-only Cart proof; no queue/workflow/approval/evidence mutation. |
| `/coding` | Source Proxy approval gate, diff verification, workspace/path safety, no apply/commit/push confusion. |
| `/map` | Cart gate clearance, protected path list, read-only/live state proof, re-soak impact decision. |

GO / NO-GO:

- GO for route-level proof map.
- NO-GO for future route work without explicit proof needs.

### Phase 16.2 Review

Completed increments:

- 16.2.1 GO for Cart/map exclusion; NO-GO for Cart touch.
- 16.2.2 GO for display/runtime separation; NO-GO for hidden runtime mutation.
- 16.2.3 GO for route-level proof map; NO-GO for unproven route work.

Evidence exists:

- Cart blocked/isolated evidence.
- `/map` and read-only Cart data evidence.
- Chat/Oracle/Dashboard route evidence.
- Route-level proof table.

Forbidden scope avoided:

- No live Cart/map mutation, provider call, storage mutation, route edit, app edit, Scout write, Source Proxy write, apply, execute-approved, or git mutation occurred.

Checks:

- Route table and excluded surfaces are recorded.

Phase result: GO to Phase 16.3; NO-GO for live Cart/map or provider/storage mutation.

Next authorized increment: 16.3.1 Decide which support surfaces can move in parallel.

## Phase 16.3 Support Lane Readiness

### 16.3.1 Decide Which Support Surfaces Can Move In Parallel

Allowed work:

- Decide non-Cart support surfaces eligible for future parallel work.

Parallel-eligible support surfaces:

| Surface | Parallel status | Conditions |
| --- | --- | --- |
| Dashboard non-Cart display shell | `eligible_with_proof` | Display-only route proof and action audit required. |
| Dashboard telemetry cards | `eligible_with_proof` | Read-only telemetry proof; no service restart/control. |
| Dashboard Chat summary widgets | `eligible_with_proof` | Display-only or Chat proof required. |
| Dashboard Oracle summary widgets | `eligible_with_proof` | Display-only or Oracle provider/voice proof required. |
| Scout advisory/intelligence display | `eligible_with_proof` | Manual-controlled, writes false, no discovery/promotion execution. |
| Mac status telemetry display | `eligible_with_proof` | Read-only telemetry only; no launchctl/restart/search execution buttons. |

GO / NO-GO:

- GO for non-Cart support surface eligibility with explicit proof needs.
- NO-GO for implementation in Plan 16.

Next authorized increment: 16.3.2 Decide which are blocked by Cart.

### 16.3.2 Decide Which Are Blocked By Cart

Allowed work:

- Decide Cart-blocked surfaces.

Cart-blocked surfaces:

| Surface | Block status | Reason |
| --- | --- | --- |
| `/map` | `blocked_by_cart_gate` | Cart state remains blocked/isolated and map imports live/read-only Cart helpers. |
| `/map/raw` | `blocked_by_cart_gate` | Deep Cart diagnostics are Cart-owned. |
| Dashboard Cartographer widget action paths | `blocked_by_cart_gate` | Fetches `/v1/cartographer/*` action/review endpoints. |
| Blueprint/Cartographer dashboard controls | `blocked_by_cart_gate` | Cart workflow/proposal/evidence boundary. |
| Cartographer API cluster | `blocked_by_cart_gate` | Live Cart authority surface. |
| Cart live evidence/receipts | `blocked_by_cart_gate` | Soak/live evidence boundary. |

GO / NO-GO:

- GO for Cart-blocked classification.
- NO-GO for Cart UI work, Cart API work, map refresh, live evidence writes, or re-soak-impacting changes.

Next authorized increment: 16.3.3 Output surface lane order.

### 16.3.3 Output Surface Lane Order

Allowed work:

- Output future surface lane order.
- Do not start next plan.

Surface lane order:

1. Dashboard non-Cart display/support shell with route proof and action audit.
2. Chat ownership lane with provider/storage proof.
3. Oracle ownership lane with provider/voice/storage proof.
4. Scout advisory/intelligence display lane with manual-controlled writes-false proof.
5. Mac telemetry display lane with read-only proof and no service controls.
6. Source Proxy `/coding` lane only under Source Proxy approval gates.
7. Map/Cartographer lane only after Cart gate clears or Plan 17 marks it Cart-only/excluded.

GO / NO-GO:

- GO for surface lane order.
- NO-GO for starting Plan 17 without explicit operator approval.

### Phase 16.3 Review

Completed increments:

- 16.3.1 GO for non-Cart support eligibility with proof; NO-GO for implementation.
- 16.3.2 GO for Cart-blocked classification; NO-GO for Cart work.
- 16.3.3 GO for surface lane order; NO-GO for Plan 17 start.

Evidence exists:

- Eligible support surface table.
- Cart-blocked surface table.
- Surface lane order.

Forbidden scope avoided:

- No live Cart/map mutation, provider call, storage mutation, route edit, app edit, Scout write, Source Proxy write, apply, execute-approved, or git mutation occurred.

Checks:

- Route table and excluded surfaces are recorded.

Phase result: GO to Plan 16 closeout; NO-GO for Plan 17 start.

Next authorized increment: Plan 16/24 closeout.

## Plan 16/24 Closeout

Phase review:

- Phase 16.1 Surface Ownership: GO for Chat, Oracle, and Dashboard ownership map; NO-GO for implementation.
- Phase 16.2 Route Constraints: GO for Cart/map exclusion, display/runtime separation, and proof needs; NO-GO for unproven route work.
- Phase 16.3 Support Lane Readiness: GO for non-Cart surface lane order; NO-GO for Cart work or Plan 17 start.

Increment review:

- 16.1.1 Chat ownership: roadmap driver, eligible later with provider/storage proof.
- 16.1.2 Oracle ownership: roadmap driver, eligible later with provider/voice/storage proof.
- 16.1.3 Dashboard ownership: mixed support hub, eligible only for non-Cart display/support proof.
- 16.2.1 Live Cart/map: excluded until Cart gate clears.
- 16.2.2 Display-only vs runtime: separated.
- 16.2.3 Route-level proof needs: defined.
- 16.3.1 Parallel support surfaces: non-Cart surfaces eligible with proof.
- 16.3.2 Cart-blocked surfaces: classified.
- 16.3.3 Surface lane order: recorded.

Evidence exists:

- Route ownership table.
- Excluded surfaces table.
- Display/runtime route table.
- Route-level proof map.
- Surface lane order.

Forbidden actions did not occur:

- No live Cart/map mutation.
- No provider calls.
- No storage mutations.
- No route edits.
- No app edits.
- No Scout writes.
- No Source Proxy writes.
- No Cartographer activation.
- No runtime start, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch, worktree, stash, reset, clean, checkout, or hidden autonomy.

Final surface lane order:

1. Dashboard non-Cart display/support shell.
2. Chat.
3. Oracle.
4. Scout advisory/intelligence display.
5. Mac telemetry display.
6. Source Proxy `/coding`.
7. Map/Cartographer only after Cart gate clears or Plan 17 marks it Cart-only/excluded.

Final Plan 16/24 result: GO for non-Cart surface ownership and route-level proof planning; NO-GO for live Cart/map work, provider calls, storage mutations, implementation, or Plan 17 start without explicit operator approval.

Next roadmap plan only: `Plan 17/24: Map And Cartographer UI Integration Gate`.

## Terminal Verification

Run from `/home/source/SpiritOS`:

```bash
cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal && grep -nE "Plan 16/24|Chat ownership|Oracle ownership|Dashboard ownership|Route constraints|cart_only_blocked|display/runtime|route-level proof|eligible_with_proof|blocked_by_cart_gate|Surface lane order|NO-GO|Plan 17/24" docs/surface-ownership-chat-oracle-dashboard-plan-16-24-v0.1.md && grep -nE "Trinity chat workspace|runtimeSurface=oracle|Dashboard route|SpiritDashboardHome|LIVE_STATE_ENDPOINT|display-only-read-only-map|queue execution authority is not granted|Cart state: .*blocked|Cart isolation: .*isolated|NO-GO" src/app/chat/page.tsx src/app/oracle/page.tsx 'src/app/(dashboard)/page.tsx' src/app/map/cartographer-live-state.ts src/app/map/read-only-map-data.ts docs/cartographer-live-evidence/cartographer-plan-7-24-activation-boundary-resoak-decision-v0.1.md && git diff --check -- docs/surface-ownership-chat-oracle-dashboard-plan-16-24-v0.1.md
```

Expected output:

- Git status shows this Plan 16 packet as untracked with prior roadmap docs still untracked.
- Plan 16 grep prints ownership, route constraints, excluded Cart surfaces, display/runtime split, proof needs, support readiness, surface lane order, NO-GO boundaries, and Plan 17 title.
- Route/evidence grep prints `/chat`, `/oracle`, dashboard, `/map` live/read-only evidence, Cart blocked/isolated evidence, and NO-GO lines.
- `git diff --check` prints no output.
