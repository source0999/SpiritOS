# Integrated Dry-Run Loop Contract

## Core Loop

The v0.1 integrated dry-run loop is:

`sense -> understand -> remember -> prioritize -> plan -> choose worker -> act -> verify -> learn`

For Phase 8, each step is preview-only.

## Step Mapping

| Loop Step | Input Source | Output |
| --- | --- | --- |
| sense | Phase 3 context router preview | request summary, target kind, selected read-only context |
| understand | Phase 1 truth contract and Phase 3 classification | acceptance criteria and truth references |
| remember | Phase 2 read-only memory contract | evidence and memory refs, no Obsidian writes |
| prioritize | Phase 4 risk/permission preview | risk classes, blocked actions, approval needs |
| plan | Phase 7 safe execution preview | rollback and verification requirements |
| choose worker | Phase 5 handoff preview | worker recommendation only, no dispatch |
| act | Phase 7 safe execution preview | action plan preview only, no execution |
| verify | Phase 6 behavior verifier | truth label and proof tier |
| learn | v0.2 deferred learning | learning event preview only, no write-back |

## Required Non-Authority Flags

Every integrated dry-run receipt must include:

- `would_execute=false`
- `would_write=false`
- `would_call_provider=false`
- `would_start_worker=false`
- `would_dispatch_worker=false`
- `would_write_obsidian=false`
- `would_mutate_git=false`
- `would_mutate_generated_artifacts=false`
- `safe_write_executed=false`
- `sandbox_command_run=false`
- `execute_approved_called=false`
- `product_pass_claimed=false` unless Phase 6 supplies qualifying behavior proof
- `learning_write_performed=false`

## Verdict Rules

| Final Verdict | Required Conditions |
| --- | --- |
| `DRY_RUN_READY` | All preview gates are shaped, no hard blockers, and no product PASS is claimed without Phase 6 proof. |
| `BLOCKED` | Any hard safety, permission, protected path, provider, worker, git, generated artifact, or truth conflict is present. |
| `UNVERIFIED` | Required input evidence is missing or unavailable. |
| `NEEDS_FIX` | Existing system path, route, schema, or proof pipeline is insufficient for later implementation. |
| `PARTIAL` | Some gates are ready but at least one required gate is blocked or unverified. |

## Product Truth Boundary

Integrated dry-run readiness is not product PASS. Product PASS remains controlled by Phase 1 truth labels and Phase 6 behavior proof.

## Learning Boundary

Phase 8 may describe a learning event preview, but automatic learning, Obsidian write-back, and memory updates are deferred to v0.2/stretch.
