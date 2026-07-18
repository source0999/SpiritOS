# Campaign 3 Plan - Extended Coding Lanes Integration

This plan is grounded in the R1 terminal codebase at `86cd484c8d09a14291da6a1226ecf24030d29caf`, with source implementation parent `ec204d63e431d10501c67db0264082db6e4d31e4`.

## Source Anchors Read

| Area | Classification | Anchors |
| --- | --- | --- |
| Production coding orchestrator | ADOPT and EXTEND | `source_proxy/coding/orchestrator.py`, `source_proxy/tests/test_coding_orchestrator.py` |
| Core lane runtime contracts | ADOPT and EXTEND | `source_proxy/contracts/coding_lane_contracts.py`, `packages/contracts/schemas/coding/core-lane-contracts.v1.json` |
| Canonical context broker | ADOPT and EXTEND | `source_proxy/context/canonical_broker.py`, `source_proxy/tests/test_canonical_context_broker.py` |
| Source Proxy task/run state | ADOPT and EXTEND | `source_proxy/tasks/long_running.py`, `source_proxy/api/coding_observability.py`, `src/app/v1/coding/runs/route.ts` |
| Target-plugin authority | ADOPT | `source_proxy/target_plugins/adapter.py`, `source_proxy/tests/test_target_plugin_adapter.py` |
| Approval authority | ADOPT | `scripts/approval-authority.py`, `source_proxy/approval/campaign_authority.py`, `source_proxy/tests/test_campaign_approval_authority.py` |
| Executor and apply path | ADOPT | `source_proxy/tasks/long_running.py`, `src/app/v1/actions/execute-approved/route.ts` |
| Reviewer and verifier boundaries | ADOPT and EXTEND | `source_proxy/decision/verifier_lane.py`, `source_proxy/verification/diff.py`, `source_proxy/tests/test_verifier_lane.py` |
| Anti-cheat boundary | ADOPT | `source_proxy/verification/anticheat/registry.py`, `source_proxy/tests/test_anticheat_production_wiring.py` |
| Evidence model | ADOPT and EXTEND | `docs/evidence-manifests/foundation-remediation-r1/`, `scripts/validate-foundation-remediation-r1-evidence.py` |
| Scout research | EXTEND | `source_proxy/decision/scout_research.py`, `source_proxy/proxy_memory/scout_intake.py`, `source_proxy/api/scout_intake.py`, `packages/contracts/schemas/scout/packet.schema.json` |
| Obsidian context | EXTEND | `source_proxy/context/obsidian.py`, `source_proxy/tests/test_obsidian_context.py` |
| Mac worker | EXTEND | `source_proxy/decision/mac_integration.py`, `scripts/mac-worker/spirit_mac_worker.py`, `packages/contracts/schemas/mac-worker/job.schema.json`, `src/app/v1/coding/mac-advisory/route.ts` |
| Retained helper/sub-agents | EXTEND or DECOMMISSION | `source_proxy/decision/model_lanes.py`, `src/app/v1/coding/helper-agents/preview/route.ts`, `source_proxy/tests/test_agent_registry.py` |
| `/coding` backend readiness | EXTEND | `source_proxy/api/coding_observability.py`, `src/app/v1/coding/self-tests/run/route.ts`, `src/app/v1/coding/dummy-product-site-preview/reset/route.ts` |

## Dependency Order

1. `gate_3_0_entry_verification_and_control_plane`
2. `gate_3_1_extended_lane_inventory_and_classification`
3. `gate_3_2_scout_and_coding_research_integration`
4. `gate_3_3_obsidian_coding_knowledge_integration`
5. `gate_3_4_mac_worker_and_mac_coding_frameworks`
6. `gate_3_5_retained_coding_sub_agents`
7. `gate_3_6_cross_lane_conflict_resolution`
8. `gate_3_7_extended_observability_and_diagnosis_backend`
9. `gate_3_8_degradation_fallback_and_resumability`
10. `gate_3_9_genuine_all_lane_proving_task`
11. `gate_3_10_coding_ui_campaign_readiness`
12. `gate_3_11_final_acceptance_and_closeout`

## Gate 3.0 - Entry Verification And Control Plane

ADOPT: R1 tag, R1 state/ledger/test-profile/evidence pattern, package command registration, Git bundle anchor pattern.

EXTEND: new C3 state, ledger, lane inventory, evidence index, test profiles, validators, completion evaluator, regression suite.

BUILD: C3-specific fail-closed validators and local control-plane recovery anchor.

Runtime acceptance: R1 tag peels to the accepted closeout commit; bundle verifies; sidecar SHA-256 matches; new branch starts at R1 terminal; control-plane validators pass; completion evaluator returns `CAMPAIGN_3_NOT_COMPLETE`.

Negative tests: malformed state, stale ledger/state disagreement, historical design C3 relabel, missing mandatory control-plane artifacts, and current state GO claims fail closed.

Evidence: evidence index, validator output, local annotated control-plane tag, bounded bundle and SHA-256 sidecar.

Recovery behavior: stop before Gate 3.1 if entry verification, branch identity, or protected refs fail.

Dependencies: none.

## Gate 3.1 - Extended-Lane Inventory And Classification

ADOPT: core lane IDs from `source_proxy/contracts/coding_lane_contracts.py` and existing references from Scout, Obsidian, Mac, model lanes, helper-agent previews, Cartographer, diagnostics, and `/coding` route projections.

EXTEND: `docs/architecture/campaign-3-lane-inventory.md`, `docs/architecture/campaign-3-decommission-registry.md`, and a future runtime lane registry contract.

BUILD: production extended-lane registry with retained/decommissioned classifications and caller/consumer anchors.

Runtime acceptance: every coding-related lane, route, framework, worker, helper, context source, model participant, and observability producer is classified; every retained lane has owner, versioned contract, authority, producer, consumer, schemas, timeout, retry, fallback, applicability, acknowledgement, observability, evidence, and migration status; ghost lanes are non-selectable.

Negative tests: prompt-only lane, callerless lane, consumerless retained lane, duplicate active lane, and placeholder `performed:true` fail.

Evidence: inventory, decommission registry, lane-registry validator output.

Recovery behavior: unclassifiable lanes block later gates.

Dependencies: Gate 3.0.

## Gate 3.2 - Scout And Coding-Research Integration

ADOPT: `source_proxy/decision/scout_research.py`, `source_proxy/proxy_memory/scout_intake.py`, `source_proxy/api/scout_intake.py`, `packages/contracts/schemas/scout/packet.schema.json`.

EXTEND: Scout as the canonical coding-research lane, with SearXNG/fetch/browser research routed through Scout.

BUILD: runtime request/result/failure contract with source provenance, context-broker inclusion, downstream consumption, citations, timeout/retry/fallback, and no mutation authority.

Runtime acceptance: task-bound research records real queries and selected current primary sources; SearXNG is provider-only; stale-source handling is explicit; planner, coder, reviewer, or verifier acknowledges consumption when applicable.

Negative tests: fabricated citations, stale source treated current, direct Scout mutation, unconsumed Scout output.

Evidence: Scout request/result/failure receipts, source list, context consumption acknowledgement.

Recovery behavior: Scout unavailable and SearXNG unavailable lower claim ceiling or block when conditionally mandatory.

Dependencies: Gate 3.1.

## Gate 3.3 - Obsidian Coding-Knowledge Integration

ADOPT: `source_proxy/context/obsidian.py`, `source_proxy/tests/test_obsidian_context.py`.

EXTEND: bounded project knowledge source selected by canonical context broker.

BUILD: vault/root registry, note identity/freshness contract, stale-note and repository-conflict detection, optional canonical write plan for SpiritOS-maintained notes.

Runtime acceptance: bounded reads include note identity, path, freshness, selected excerpts, downstream consumption, and conflict handling; write-capable mode requires exact vault/root/path binding, approval, verification, evidence, and rollback.

Negative tests: unrestricted filesystem read/write, stale note silently winning, no note identity, unconsumed context.

Evidence: note selection receipt, conflict record, optional write receipt.

Recovery behavior: Obsidian unavailable or stale context records truthful degradation.

Dependencies: Gate 3.1.

## Gate 3.4 - Mac Worker And Mac Coding Frameworks

ADOPT: `source_proxy/decision/mac_integration.py`, `scripts/mac-worker/spirit_mac_worker.py`, `packages/contracts/schemas/mac-worker/job.schema.json`, `src/app/v1/coding/mac-advisory/route.ts`.

EXTEND: Mac worker from advisory/status into authority-bound production participant for macOS-only coding validation.

BUILD: host/capability preflight, source/worktree binding, versioned request/result/failure contracts, timeout/cancellation, logs/artifact hashes, acknowledgement, cleanup, and verdict effect.

Runtime acceptance: at least one Mac-specific result affects the final task verdict; no hidden shell, SSH, queue, or direct write bypass exists; offline and timeout states are visible and recoverable.

Negative tests: host-exists-only participation, mismatched source root, missing artifact hash, hidden command path.

Evidence: Mac job receipt, logs, artifact hashes, capability preflight, cleanup proof.

Recovery behavior: Mac offline and Mac timeout produce blocking or degraded classification according to applicability.

Dependencies: Gate 3.1.

## Gate 3.5 - Retained Coding Sub-Agents

ADOPT: `source_proxy/decision/model_lanes.py`, `source_proxy/tests/test_model_lanes.py`, `source_proxy/tests/test_agent_registry.py`.

EXTEND: retained agents into runtime-enforced participants with real provider/model identity.

BUILD: sub-agent contract, invocation store, output identity, consumer acknowledgement, failure/timeout behavior, observability, immutable evidence, and decommission path.

Runtime acceptance: every retained agent has production caller, real input, real output, real consumer, and evidence; prompt-only, canned, duplicate, callerless, and consumerless agents are disabled or removed.

Negative tests: canned output, no provider identity, no consumer, duplicate retained helper.

Evidence: invocation/output/consumption receipts and decommission registry.

Recovery behavior: malformed sub-agent output fails closed and is recorded in run lineage.

Dependencies: Gate 3.1.

## Gate 3.6 - Cross-Lane Conflict Resolution

ADOPT: verifier downgrades from `source_proxy/decision/verifier_lane.py`; context-source readiness patterns from `source_proxy/context/source_readiness.py`.

EXTEND: orchestrator state and diagnosis to carry conflicts.

BUILD: conflict schema, precedence resolver, downstream acknowledgement, and claim-ceiling effect.

Runtime acceptance: conflicts between Scout, Obsidian, repository source, Mac/local validation, context models, research/code, reviewer/verifier, and stale/current context are surfaced and resolved using the required precedence order.

Negative tests: hidden conflict, stale context wins silently, no resolution authority, no claim ceiling effect.

Evidence: conflict receipt with lane IDs, claims, provenance, freshness, selected resolution, reason, and acknowledgement.

Recovery behavior: unresolved conflicts block or lower claim ceiling.

Dependencies: Gates 3.2 through 3.5.

## Gate 3.7 - Extended Observability And Diagnosis Backend

ADOPT: `source_proxy/api/coding_observability.py`, `source_proxy/coding/observability.py`, `src/app/v1/coding/runs/**`.

EXTEND: backend-owned lane lifecycle state for retained extended lanes.

BUILD: versioned diagnosis envelope API with task/run/attempt, source, repository, worktree, prompt, target plugin, core and extended lane states, provider/model, context, conflicts, errors, fallback, outputs, evidence, recovery, claim ceiling, and redaction verdict.

Runtime acceptance: every retained lane exposes applicability, requested, selected, invoked, active, completed, failed, timed out, retried, fallback, output identity, consumed, acknowledged, and evidence identity; backend truth exists for Campaign 4 UI without wiring full UI presentation.

Negative tests: UI-only lane state, missing output identity, missing redaction verdict, stale projection claiming active.

Evidence: diagnosis envelope receipt and API contract tests.

Recovery behavior: diagnosis remains available for failed and resumed runs.

Dependencies: Gates 3.2 through 3.6.

## Gate 3.8 - Degradation, Fallback, And Resumability

ADOPT: `source_proxy/coding/orchestrator.py` recovery lineage and `source_proxy/tasks/long_running.py` approval/finalization recovery checks.

EXTEND: lane-specific fallback classifications and resumable lineage for external lanes.

BUILD: failure injection controls and receipts for Scout unavailable, SearXNG unavailable, Obsidian unavailable, stale Obsidian context, Mac offline, Mac timeout, malformed sub-agent output, context-model failure, and conflicting recommendations.

Runtime acceptance: every lane declares mandatory, conditionally mandatory, substitutable, skippable, retryable, degrading, or blocking behavior; full success is impossible when required lanes are skipped or replaced.

Negative tests: skipped mandatory lane claims full success, replacement without claim-ceiling change, hidden external-host failure.

Evidence: recovery receipts and final claim-ceiling state.

Recovery behavior: each injected failure has retry/fallback/replacement/output/claim-ceiling proof.

Dependencies: Gates 3.2 through 3.7.

## Gate 3.9 - Genuine All-Lane Proving Task

ADOPT: R1 proving lifecycle and reset harness from `source_proxy/coding/orchestrator.py`, `source_proxy/tasks/long_running.py`, and dummy product reset route.

EXTEND: proving harness to require all applicable mandatory extended lanes.

BUILD: bounded task fixture that genuinely requires Cartographer, context broker, context model, Scout research, Obsidian knowledge, Mac verification, retained sub-agent contribution, target-plugin adapter, coder, authority-bound executor, reviewer, verifier, anti-cheat, and immutable evidence.

Runtime acceptance: clean isolated baseline through clean rerun; real lane invocation and consumption; model-authored non-empty diff; authenticated approval and canonical apply; at least two controlled extended-lane failures including one external-host failure; Undo/reset and teardown.

Negative tests: no-op lane participation, synthetic participant, unbound artifact, fake approval, unconsumed mandatory output.

Evidence: all-lane receipt, immutable manifest, controlled-failure receipts.

Recovery behavior: proving task must recover truthfully before final acceptance.

Dependencies: Gates 3.2 through 3.8.

## Gate 3.10 - `/coding` UI-Campaign Readiness

ADOPT: existing backend run routes under `src/app/v1/coding/runs/**`, self-test bridge, and reset route.

EXTEND: stable backend contracts needed by Campaign 4.

BUILD: task/run APIs, lane-state API, diagnosis-envelope API, conflict/recovery fields, prompt-selection API, cancel/retry API, clear/reset API, immutable evidence lookup, browser fixtures, isolated workspaces, Undo/reset harness, operator E2E fixture, failure injection, and receipt-to-UI reconciliation rules.

Runtime acceptance: backend surfaces are production-valid and characterized; Campaign 4 can wire UI against verified contracts; no full `/coding` UI wiring occurs in Campaign 3.

Do not fully wire the UI yet.

Negative tests: UI-only state, mutation through read-only run projection, missing fixture reset, missing reconciliation rules.

Evidence: API contract tests and backend readiness receipt.

Recovery behavior: clear/reset and retry APIs must preserve authority and evidence boundaries.

Dependencies: Gates 3.7 through 3.9.

## Gate 3.11 - Final Acceptance And Closeout

ADOPT: R1 closeout evidence, tag, bundle, sidecar, and restoration pattern.

EXTEND: final acceptance validators for extended-lane participation.

BUILD: terminal receipt, immutable evidence manifest, annotated terminal tag, verified bundle, SHA-256 sidecar, and restoration instructions.

Runtime acceptance: registered lane tests, production call-graph tests, research provenance, Obsidian tests, Mac tests, sub-agent tests, conflict tests, recovery tests, all-lane proving task, validators, typecheck, Python compile, production build, secret scan, diff check, Git integrity, protected-ref checks, and clean final worktree all pass; completion evaluator returns `CAMPAIGN_3_EXTENDED_CODING_LANES_INTEGRATED`.

Negative tests: any missing proof, stale ledger/state disagreement, historical design C3 relabel, evidence not source-bound, or protected-ref drift fails.

Evidence: terminal receipt, immutable manifest, tag, bundle, sidecar, restoration instructions.

Recovery behavior: final recovery anchor must restore the exact terminal state without mutating protected history.

Dependencies: Gates 3.0 through 3.10.
