# Scout Plan 15/24 Manual-Controlled Intelligence Lane

Status: Closed docs-only manual-controlled lane review
Plan: Plan 15/24, Scout Manual-Controlled Intelligence Lane
Mode: PARALLEL DOCS-ONLY / MANUAL-CONTROLLED / MAC-BACKED OPTIONAL
Date: 2026-05-27

## Scope

Plan 14/24 closed with GO for advisory subagent fleet preintegration and future inert packet display eligibility, while keeping apply authority, direct repo writes, hidden workers, Cart workflows, `/coding` implementation, Source Proxy implementation, CSS edits, prompt execution, provider/model calls, queue/worker execution, and Plan 15 start as NO-GO without explicit operator approval.

The operator then requested the next plan if all good. Plan 14 manual verification passed before this packet started.

This packet records Plan 15 only. It does not start Plan 16/24.

Allowed scope:

- Parked-state confirmation.
- Proxy intake contract.
- Parallel safety decision.

Forbidden scope:

- Autonomous discovery.
- Writes.
- Proxy memory writes.
- Coding context writes.
- Promotion finalization.
- Scout intake calls, source activation, source candidate extraction into Scout state, Cart touch, runtime start, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, or hidden workers.

## Phase 15.1 Parked State Confirmation

### 15.1.1 Confirm Manual-Controlled State

Allowed work:

- Review Scout parked/manual-controlled evidence.
- Record state decision.

Evidence:

- `docs/scout-v0-7-reopen-decision-record.md` records `status: decided/manual-controlled` and says only read-only review ergonomics and diagnostics are allowed.
- `docs/scout-v0-8-next-lane-decision-record.md` records Scout remains parked as a manual-controlled intelligence center.
- `docs/scout-v0-9-phase-0-3-closeout.md` records Scout remains stable, parked, manual-controlled, and not autonomous.

Decision:

- Scout state: `parked_manual_controlled`.
- Scout may support advisory review only.

GO / NO-GO:

- GO for manual-controlled state confirmation.
- NO-GO for implementation, runtime activation, source activation, discovery execution, or promotion finalization.

Next authorized increment: 15.1.2 Confirm writes disabled.

### 15.1.2 Confirm Writes Disabled

Allowed work:

- Review Scout write boundary evidence.
- Confirm writes remain disabled.

Evidence:

- `docs/scout-v0-7-reopen-decision-record.md` records `would_write_proxy_memory: false` and `would_write_coding_context: false`.
- `docs/scout-v0-8-next-lane-decision-record.md` records proxy memory writes and coding context writes as `false`.
- `docs/scout-v0-9-design-review-packet-format.md`, `docs/scout-v0-9-dry-run-receipt-format.md`, and `docs/scout-v0-9-context-handoff-packet.md` require `writes_allowed: false`.
- `docs/cartographer-level-10-scout-blueprint-handoff-preview.md` records Scout, proxy memory, coding context, blueprint, and evidence writes disabled for preview-only handoff.

Decision:

- Scout writes: `disabled`.
- Proxy memory writes: `false`.
- Coding context writes: `false`.
- Active context writes: `false`.
- Promotion finalization: `false`.

GO / NO-GO:

- GO for write-disabled confirmation.
- NO-GO for Scout writes, proxy memory writes, coding context writes, active context writes, scheduled writes, or promotion finalization.

Next authorized increment: 15.1.3 Confirm no autonomous discovery.

### 15.1.3 Confirm No Autonomous Discovery

Allowed work:

- Review discovery boundary evidence.
- Confirm no autonomous discovery is authorized.

Evidence:

- `docs/scout-v0-9-manual-triggered-discovery-boundary.md` records Scout remains parked, manual-controlled, and not autonomous.
- It defines future discovery as manually triggered, bounded, and stopped before implementation.
- It explicitly forbids scheduled discovery, source activation, packet promotion, proxy intake calls, proxy memory writes, coding context writes, and active context writes.

Decision:

- Autonomous discovery: `no_go`.
- Manual-triggered discovery planning: `docs_only`.
- Discovery execution: `not_authorized`.

GO / NO-GO:

- GO for no-autonomous-discovery confirmation.
- NO-GO for scheduled discovery, automatic discovery execution, source activation, extraction into Scout state, or hidden workers.

### Phase 15.1 Review

Completed increments:

- 15.1.1 GO for manual-controlled state; NO-GO for activation.
- 15.1.2 GO for writes disabled; NO-GO for proxy/coding context writes.
- 15.1.3 GO for no autonomous discovery; NO-GO for discovery execution.

Evidence exists:

- Scout v0.7 reopen decision.
- Scout v0.8 next-lane decision.
- Scout v0.9 manual-triggered discovery boundary.
- Scout v0.9 closeout and packet docs.

Forbidden scope avoided:

- No Scout feature implementation, discovery run, source activation, proxy intake call, memory/context write, promotion finalization, provider/model call, queue/worker execution, apply, execute-approved, or git mutation occurred.

Checks:

- Read-only grep checks returned expected parked/manual-controlled, writes false, not autonomous, and NO-GO evidence.

Phase result: GO to Phase 15.2; NO-GO for opening Scout execution.

Next authorized increment: 15.2.1 Define advisory research packet.

## Phase 15.2 Proxy Intake Contract

### 15.2.1 Define Advisory Research Packet

Allowed work:

- Define advisory research packet shape.
- Preserve no-write boundary.

Evidence:

- `docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md` defines a Mac search advisory packet with `packet_type: mac_search_advisory_packet`, bounded provider results, allowed use for operator review, and forbidden use against repo writes, Scout intake writes, Cart mutation, and Source Proxy mutation.
- `docs/scout-v0-9-design-review-packet-format.md` defines a manual-controlled design review packet with `writes_allowed: false` and `execution_status: advisory-only, not implemented`.
- `docs/scout-v0-9-context-handoff-packet.md` defines an advisory context handoff packet with `advisory_only: true` and `writes_allowed: false`.

Required advisory research packet:

| Field | Required | Value boundary |
| --- | --- | --- |
| `packet_type` | yes | `scout_advisory_research_packet` |
| `packet_id` | yes | Stable id. |
| `source` | yes | Manual source, Mac search packet, or cited evidence. |
| `query_or_context` | yes | Bounded human-readable request. |
| `summary` | yes | Advisory summary only. |
| `citations` | yes | Source links or evidence refs when available. |
| `candidate_sources` | yes | Candidate list only, not Scout state. |
| `allowed_use` | yes | Operator review and possible later approved packet. |
| `forbidden_use` | yes | No repo write, Scout intake write, proxy memory write, coding context write, Cart mutation, Source Proxy mutation, or promotion finalization. |
| `manual_decision_needed` | yes | `true` |
| `writes_allowed` | yes | `false` |

GO / NO-GO:

- GO for advisory research packet definition.
- NO-GO for proxy intake calls, Scout intake writes, memory/context writes, or automatic promotion.

Next authorized increment: 15.2.2 Define promotion queue preview.

### 15.2.2 Define Promotion Queue Preview

Allowed work:

- Define preview-only promotion queue semantics.
- Keep promotion finalization blocked.

Evidence:

- `docs/scout-v0-7-reopen-decision-record.md` keeps import parked and avoids packet promotion, proxy memory writes, and coding context writes.
- `docs/scout-v0-9-dry-run-receipt-format.md` defines dry-run receipts for human review without mutating source, packet, proxy memory, coding context, or promotion state.

Promotion queue preview fields:

| Field | Required | Boundary |
| --- | --- | --- |
| `preview_id` | yes | Stable preview id. |
| `candidate_packet_id` | yes | Advisory packet reference only. |
| `queue_status` | yes | `preview_only`, `blocked`, or `save_later`. |
| `manual_decision` | yes | `save_later`, `reject`, `block`, or `approve_future_review`. |
| `promotion_finalization` | yes | Always `false` in Plan 15. |
| `writes_allowed` | yes | Always `false` in Plan 15. |

GO / NO-GO:

- GO for promotion queue preview definition.
- NO-GO for packet promotion, promotion finalization, proxy intake, or context writes.

Next authorized increment: 15.2.3 Define no-write boundary.

### 15.2.3 Define No-Write Boundary

Allowed work:

- Define no-write boundary for Scout advisory continuation.

No-write boundary:

| Area | Plan 15 status |
| --- | --- |
| Scout state write | `no_go` |
| Source candidate extraction into Scout state | `no_go` |
| Proxy memory write | `no_go` |
| Coding context write | `no_go` |
| Active context write | `no_go` |
| Source Proxy mutation | `no_go` |
| Cartographer mutation or Cart touch | `no_go` |
| Repo write outside this Plan 15 packet | `no_go` |
| Promotion finalization | `no_go` |
| Advisory packet docs | `go` |

GO / NO-GO:

- GO for no-write boundary definition.
- NO-GO for any Scout, proxy memory, coding context, active context, Source Proxy, Cart, or promotion write.

### Phase 15.2 Review

Completed increments:

- 15.2.1 GO for advisory research packet; NO-GO for intake calls or writes.
- 15.2.2 GO for promotion queue preview; NO-GO for promotion finalization.
- 15.2.3 GO for no-write boundary; NO-GO for runtime or state mutation.

Evidence exists:

- Mac advisory search packet evidence.
- Scout design review packet evidence.
- Scout dry-run receipt evidence.
- Scout context handoff packet evidence.

Forbidden scope avoided:

- No proxy intake call, Scout intake write, proxy memory write, coding context write, active context write, promotion finalization, Source Proxy mutation, Cart touch, provider/model call, queue/worker execution, apply, execute-approved, or git mutation occurred.

Checks:

- Read-only grep checks returned expected packet examples, `writes_allowed: false`, advisory-only fields, and no-write boundaries.

Phase result: GO to Phase 15.3; NO-GO for proxy intake or promotion execution.

Next authorized increment: 15.3.1 Decide what Scout can do during Proxy work.

## Phase 15.3 Parallel Safety Decision

### 15.3.1 Decide What Scout Can Do During Proxy Work

Allowed work:

- Decide allowed Scout advisory activity while Source Proxy work proceeds.

Decision:

Scout can do the following during non-Cart Source Proxy work only after an explicit manual request:

- Produce advisory research packets from manual context or approved search scope.
- Summarize cited evidence for operator review.
- Produce dry-run receipts with `writes_allowed: false`.
- Suggest manual next decisions such as `save_later`, `reject`, `block`, or `approve_future_review`.
- Route Mac-backed search only through the advisory packet contract.

GO / NO-GO:

- GO for manual-controlled advisory continuation during Proxy work.
- NO-GO for autonomous discovery, proxy intake calls, proxy memory writes, coding context writes, Source Proxy mutation, or implementation.

Next authorized increment: 15.3.2 Decide what Scout cannot do during Cart isolation.

### 15.3.2 Decide What Scout Cannot Do During Cart Isolation

Allowed work:

- Preserve Cart isolation boundary.

Evidence:

- Plan 7/24 records Cartographer state as `blocked`, isolation as `isolated`, promotion as `not_promoted`, and activation as NO-GO.
- Plan 7 allows non-Cart lanes only if they do not touch Cart, map, live evidence, runtime, queues, workers, approval tokens, trust tiers, or soak behavior.
- Cartographer Level 10 Scout handoff preview is preview-only and records Scout writes, proxy memory writes, coding context writes, blueprint writes, and evidence writes as disabled.

Decision:

Scout cannot do the following during Cart isolation:

- Touch Cartographer, Cart live map, live evidence, blueprint files, run history, or Cart receipts.
- Mutate Scout state through Cart handoff.
- Promote Cart evidence or infer Cart activation.
- Trigger Cart runtime, queues, workers, approval-token behavior, trust-tier behavior, or soak behavior.

GO / NO-GO:

- GO for non-Cart Scout advisory continuation.
- NO-GO for Cart touch, Cart mutation, Cart promotion, Cart activation, live-map work, soak-affecting work, or Cart handoff writes.

Next authorized increment: 15.3.3 Decide whether Scout search can route through Mac.

### 15.3.3 Decide Whether Scout Search Can Route Through Mac

Allowed work:

- Decide Mac search routing eligibility.
- Do not run search.

Evidence:

- Plan 4/24 records Mac Python/curl and SearXNG as proven for future scoped advisory search.
- Plan 4/24 records direct Scout intake as NO-GO, direct Source Proxy mutation as NO-GO, direct Cart mutation as NO-GO, hidden scheduled discovery as NO-GO, and Docker/Homebrew provider paths as NO-GO until proven and approved.

Decision:

- Scout search can route through Mac only as manually requested advisory search with exact scope.
- Preferred provider remains SearXNG through the existing advisory packet model.
- Mac search output remains a research packet only.
- Mac search must not write files directly into the repo, Scout state, Source Proxy memory, Cartographer evidence, or application routes.

GO / NO-GO:

- GO for Mac-backed advisory search routing eligibility.
- NO-GO for autonomous search, scheduled discovery, Scout intake writes, repo writes, Source Proxy mutation, Cart mutation, Docker/Homebrew provider path, or hidden workers.

### Phase 15.3 Review

Completed increments:

- 15.3.1 GO for manual-controlled Scout advisory continuation during Proxy work; NO-GO for intake/writes.
- 15.3.2 GO for non-Cart continuation; NO-GO for Cart touch.
- 15.3.3 GO for Mac-backed advisory search eligibility; NO-GO for autonomous search or writes.

Evidence exists:

- Scout parked/manual-controlled docs.
- Mac search advisory contract.
- Cart isolation and preview-only handoff evidence.
- This Plan 15 packet's advisory research packet and no-write boundary.

Forbidden scope avoided:

- No autonomous discovery, writes, proxy memory writes, coding context writes, promotion finalization, Scout intake call, Cart touch, Mac search execution, provider/model call, queue/worker execution, apply, execute-approved, or git mutation occurred.

Checks:

- Scout parked-state grep and packet example grep are available in the terminal verification section.

Phase result: GO to Plan 15 closeout; NO-GO for Plan 16 start.

Next authorized increment: Plan 15/24 closeout.

## Plan 15/24 Closeout

Phase review:

- Phase 15.1 Parked State Confirmation: GO for Scout parked/manual-controlled state; NO-GO for activation, writes, or autonomous discovery.
- Phase 15.2 Proxy Intake Contract: GO for advisory research packet, preview queue, and no-write boundary; NO-GO for proxy intake or promotion execution.
- Phase 15.3 Parallel Safety Decision: GO for manual-controlled advisory continuation and Mac-backed advisory eligibility; NO-GO for Cart touch or autonomous execution.

Increment review:

- 15.1.1 Scout state: `parked_manual_controlled`.
- 15.1.2 Writes: `disabled`.
- 15.1.3 Autonomous discovery: `no_go`.
- 15.2.1 Advisory research packet: defined.
- 15.2.2 Promotion queue preview: `preview_only`.
- 15.2.3 No-write boundary: defined.
- 15.3.1 Scout during Proxy work: `manual_controlled_advisory_only`.
- 15.3.2 Scout during Cart isolation: `non_cart_only_no_touch`.
- 15.3.3 Mac search routing: `manual_advisory_eligible`.

Evidence exists:

- Scout parked-state grep evidence.
- Advisory packet example.
- No-write boundary.
- Mac routing evidence.
- Cart isolation boundary evidence.

Forbidden actions did not occur:

- No autonomous discovery.
- No writes outside this Plan 15 packet.
- No proxy memory writes.
- No coding context writes.
- No promotion finalization.
- No Scout intake call.
- No source activation or source candidate extraction into Scout state.
- No Cart touch.
- No runtime, provider/model, queue/worker, approval-token, apply, execute-approved, commit, push, branch, worktree, stash, reset, clean, checkout, or hidden worker.

Final Scout status:

- Scout remains `parked_manual_controlled`.
- Exact next lane is Plan 16 only.
- Manual-controlled advisory continuation is eligible.
- Mac-backed search is eligible only as manually requested advisory packet routing.

Final Plan 15/24 result: GO for manual-controlled advisory continuation; NO-GO for autonomous discovery, writes, proxy memory writes, coding context writes, promotion finalization, Scout intake calls, Cart touch, Mac hidden workers, implementation, or Plan 16 start without explicit operator approval.

Next roadmap plan only: `Plan 16/24: Chat, Oracle, Dashboard, And Supporting Surface Ownership`.

## Terminal Verification

Run from `/home/source/SpiritOS`:

```bash
cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal && grep -nE "Plan 15/24|parked_manual_controlled|writes_allowed|writes disabled|Autonomous discovery|scout_advisory_research_packet|promotion queue preview|no-write boundary|manual_controlled_advisory_only|non_cart_only_no_touch|manual_advisory_eligible|NO-GO|Plan 16/24" docs/scout-manual-controlled-intelligence-lane-plan-15-24-v0.1.md && grep -nE "manual-controlled|parked|would_write_proxy_memory: false|would_write_coding_context: false|writes_allowed: false|not autonomous|proxy intake|coding context writes|promotion finalization|advisory_only: true|NO-GO" docs/scout-v0-7-reopen-decision-record.md docs/scout-v0-8-next-lane-decision-record.md docs/scout-v0-9-manual-triggered-discovery-boundary.md docs/scout-v0-9-design-review-packet-format.md docs/scout-v0-9-context-handoff-packet.md && grep -nE "Plan 4/24|mac_search_advisory_packet|Source Proxy remains|Direct Scout intake|Direct Cart mutation|Hidden scheduled discovery|SearXNG|NO-GO" docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md && git diff --check -- docs/scout-manual-controlled-intelligence-lane-plan-15-24-v0.1.md
```

Expected output:

- Git status shows this Plan 15 packet as untracked with prior roadmap docs still untracked.
- Plan 15 grep prints parked/manual-controlled state, writes disabled, advisory packet fields, promotion preview, no-write boundary, parallel safety decisions, NO-GO boundaries, and Plan 16 title.
- Scout grep prints manual-controlled/parked evidence, proxy/coding context writes false, `writes_allowed: false`, advisory-only fields, and NO-GO boundaries.
- Mac grep prints Plan 4 advisory search packet, SearXNG, Source Proxy gate, and direct intake/Cart/scheduled discovery NO-GO lines.
- `git diff --check` prints no output.
