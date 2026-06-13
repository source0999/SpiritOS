# Worker Selector and Handoff Preview Contract

## Purpose

The worker selector preview recommends a worker/provider/lane candidate for a request after Phase 4 risk/permission preview. It does not dispatch workers, start workers, call providers/models, execute queues, write files, mint approval tokens, or grant authority.

This Phase 5 artifact is evidence-only. Runtime adapters are deferred to later authorized phases.

## Core Rule

Worker selection is recommendation-only. If Phase 4 decision is `blocked`, `needs_clarification`, or `unverified_gate`, Phase 5 must return `selection_blocked`.

## Selector Decisions

| Decision | Meaning |
| --- | --- |
| `recommendation_ready` | A recommendation-only worker/lane/provider candidate can be named for later review. |
| `selection_blocked` | Permission, risk, target, authority, dirty-tree, or gate state blocks selection. |
| `needs_clarification` | More target, task, acceptance, lane, or permission detail is needed before selecting. |
| `no_suitable_worker` | No known worker/provider/lane satisfies the requested capability and authority constraints. |
| `unverified_capability` | Required route, provider, worker, or lane capability was not checked or is unavailable. |

## Candidate Inputs

- Phase 3 intake/context preview packet.
- Phase 4 risk/permission executive preview packet.
- Agent/provider capability registry.
- Lane registry and dirty overlap status.
- Worker contract vocabulary.
- Source Proxy route/model manifest metadata.
- Phase 1 truth labels and Phase 2 memory refs.

## Candidate Output Fields

Every future selector preview packet should include:

- `input_packet_ref`
- `permission_packet_ref`
- `selector_decision`
- `recommended_worker_role`
- `recommended_provider_id`
- `recommended_lane_id`
- `capability_match`
- `authority_flags`
- `blocked_authorities`
- `required_human_approval`
- `required_gate_refs`
- `risk_classes_carried_forward`
- `truth_refs`
- `memory_refs`
- `handoff_preview_ref`
- `phase_6_verifier_needs`
- `would_dispatch_worker`
- `would_start_worker`
- `would_call_provider`
- `would_execute`
- `would_write`
- `would_mutate_git`

## Fail-closed Rules

- `blocked`, `needs_clarification`, or `unverified_gate` from Phase 4 blocks worker selection.
- Provider/model candidates are recommendation-only unless a later phase approves calls.
- Local worker/model candidates are recommendation-only unless a later phase approves starts/calls.
- No worker/provider can grant approval, apply, commit, push, or self-approve.
- Handoff preview packets are data-only and cannot dispatch.
- Dirty-tree conflict, protected lane overlap, or broad file zone blocks selection.
- Fake-green risk must be carried into Phase 6 verifier needs.
- Capability mismatch returns `no_suitable_worker`, not a forced selection.

## Existing System Reuse

Future implementation must wrap existing systems first:

- agent/provider capabilities: `source_proxy/agents/registry.py`
- lane records: `source_proxy/cartographer/lane_registry.py`
- worker/handoff models: `source_proxy/cartographer/worker_contract.py`
- route/model manifests: `source_proxy/self_status.py`
- routing metadata: `source_proxy/routing/*`
- advisory packets: `source_proxy/decision/advisory_broker.py`

## Phase 6 Handoff

Phase 6 may consume selector previews to decide what behavior proof is required. Phase 5 does not verify behavior and cannot label product PASS.

