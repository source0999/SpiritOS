# Intake Classification Contract

## Purpose

The intake/context router preview classifies an operator request before any worker selection, provider call, model call, file mutation, or approval decision. It prepares a safe context packet for later phases without acting.

This Phase 3 artifact is evidence-only. It does not add a runtime route or change existing Source Proxy behavior.

## Intake Dimensions

Every intake preview should classify:

- `request_type`: question, plan, implementation_request, verification_request, troubleshooting, evidence_lookup, benchmark_review, unknown.
- `target_kind`: repo_file, route, docs_evidence, obsidian_note, durable_run, generated_artifact, service, unknown.
- `explicit_targets`: normalized target paths or identifiers if supplied.
- `target_confidence`: explicit, inferred, ambiguous, missing.
- `context_sources_requested`: repo, evidence_docs, obsidian, durable_runs, logs, browser, unknown.
- `risk_flags`: secrets_scope, broad_filesystem_scope, production_surface, generated_artifact_mutation, provider_spend_possible, worker_start_possible, obsidian_write_requested, git_mutation_requested.
- `truth_contract_refs`: Phase 1 labels/fixtures relevant to the request.
- `memory_refs`: Phase 2 read-only sources relevant to the request.
- `preview_decision`: preview_ready, needs_clarification, blocked_preview, unverified_context.
- `reason_codes`: stable machine-readable reasons.

## Preview Decisions

| Decision | Meaning |
| --- | --- |
| `preview_ready` | A safe read-only context packet can be prepared from existing sources. |
| `needs_clarification` | The request is understandable but target/scope/context is ambiguous. |
| `blocked_preview` | The request asks for forbidden Phase 3 actions such as provider calls, workers, writes, Obsidian write-back, git mutation, or broad secret-prone browsing. |
| `unverified_context` | A needed source is unavailable or intentionally skipped under the phase boundary. |

## Non-Authority Rules

The preview packet is not:

- approval to modify files
- approval to call providers or models
- approval to start workers
- proof of product PASS
- permission to write Obsidian
- permission to mutate generated artifacts
- a Phase 4 risk/permission decision

## Context Selection Rules

- Use existing context index and inventory surfaces before any new module.
- Use Obsidian only through read-only safe excerpts.
- Use evidence docs by source reference and short summary.
- Use durable run records by run ID or compact summary.
- Carry Phase 1 truth labels and Phase 2 memory metadata.
- Mark unavailable sources as `UNVERIFIED`.
- Keep blocked or forbidden requests as `blocked_preview`, not PASS.

## Phase 4 Handoff

Phase 4 may consume this preview packet to produce a risk/permission executive preview. Phase 3 does not decide permission or execute actions.

