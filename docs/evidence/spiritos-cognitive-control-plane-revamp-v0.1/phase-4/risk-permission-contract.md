# Risk/Permission Executive Preview Contract

## Purpose

The risk/permission executive preview consumes a Phase 3 intake/context preview packet and classifies risk, required gates, and next safe decision. It does not approve, execute, call models, start workers, apply diffs, mutate files, or prove product behavior.

This Phase 4 artifact is evidence-only. Runtime adapters are deferred to later authorized phases.

## Core Rule

Risk preview is fail-closed. Unknown or unavailable gate state must not become permission.

## Permission Preview Decisions

| Decision | Meaning |
| --- | --- |
| `preview_only` | The request may continue as read-only planning/context work only. |
| `requires_human_approval` | The request might be valid later, but needs explicit human approval before mutation, spend, worker start, or apply. |
| `blocked` | The request is forbidden or unsafe under current boundaries. |
| `needs_clarification` | The request cannot be classified safely because target, action, or acceptance criteria are ambiguous. |
| `unverified_gate` | A required gate, state file, route, or authority signal was not checked or unavailable. |

## Risk Classes

- `secret_or_credential_scope`
- `broad_filesystem_scope`
- `path_escape_or_absolute_target`
- `production_surface_mutation`
- `generated_artifact_mutation`
- `git_mutation`
- `obsidian_write`
- `provider_spend`
- `model_call`
- `worker_start`
- `apply_or_execute`
- `self_approval`
- `fake_green_risk`
- `truth_contract_gap`
- `dirty_tree_conflict`
- `missing_target`
- `ambiguous_target`
- `unavailable_gate`

## Required Gate Fields

Every future executive preview packet should include:

- `input_packet_ref`
- `permission_decision`
- `risk_classes`
- `reason_codes`
- `required_human_approval`
- `required_gate_refs`
- `blocked_actions`
- `allowed_preview_actions`
- `would_execute`
- `would_write`
- `would_call_provider`
- `would_start_worker`
- `would_write_obsidian`
- `would_mutate_git`
- `product_pass_claimed`
- `truth_contract_refs`
- `memory_refs`
- `phase_5_handoff`

## Fail-closed Rules

- Secret-shaped or credential-scope requests are `blocked`.
- Broad filesystem or path-escape requests are `blocked`.
- Provider/model calls require explicit spend/model-call approval and are not allowed in Phase 4.
- Worker starts require separate approval and are not allowed in Phase 4.
- Apply/execute routes require explicit human approval and are not allowed in Phase 4.
- Obsidian writes are deferred to v0.2/stretch and remain blocked.
- Git mutation is blocked unless separately approved.
- Generated artifact mutation is blocked unless separately approved.
- Memory/context evidence is not approval.
- Model/provider recommendations are not approval.
- PASS claims without behavior proof carry `fake_green_risk`.
- Missing or unavailable gate state is `unverified_gate`, not permission.

## Existing System Reuse

Future implementation must wrap existing systems first:

- central gate: `source_proxy/approval/external_gate.py`
- spend gate: `source_proxy/approval/gate.py`
- unsafe path detection: `source_proxy/safety/paths.py`
- action preview: `source_proxy/self_status.py::build_action_preview`
- authority registry: `source_proxy/agents/registry.py`
- `/coding` approval binding: `src/components/coding/approval-gate-binding.ts`

## Phase 5 Handoff

Phase 5 may consume this preview to select a worker/model handoff candidate. Phase 4 does not choose a worker, start a worker, or approve a model/provider call.

