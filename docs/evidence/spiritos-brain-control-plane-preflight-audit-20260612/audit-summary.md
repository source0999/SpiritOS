# SpiritOS Brain Control Plane Preflight Audit Summary

Date: 2026-06-12
Repo path audited: `Z:\`
Scope: audit only. No implementation plan, architecture patch, routing patch, Source Proxy refactor, model/provider call, benchmark prompt, branch, commit, staging, stash, reset, checkout, clean, or generated benchmark artifact mutation was performed.

## Overall Grade

Overall readiness grade: PARTIAL

SpiritOS has many real pieces of a cognitive control plane: Source Proxy, route selection, model alias discovery, local Ollama status probing, prompt packets, long-running task state, approval gates, diff verification, Cartographer repo/context packets, Codex command-envelope validation, `/coding` durable run storage, and a read-only Obsidian context adapter. The system is not yet ready to be treated as a unified brain-inspired control plane because too much behavior is split across overlapping surfaces, several important paths are preview-only, and recent evidence shows old pass/GO labels can overstate product behavior.

## Current State

The current system is a collection of strong subsystems, not yet a single executive loop. Source Proxy can decide routes, build prompt packets, expose self-status, guard model calls behind central gate checks, preview diffs, and require approval before apply. `/coding` has a real UI shell and durable run store. Cartographer has extensive repo-health, component-map, approval-token, safe-write, queue, evidence, and trust modules. Obsidian exists as a read-only context source with discovery, query, redaction, and tests, but it is not yet a trusted decision-making memory backbone.

## Biggest Strengths

- Clear approval boundaries exist in code for model calls, apply, commit, push, terminal, Codex, and workspace writes.
- Source Proxy has concrete FastAPI routers for decisions, chat/model routes, context index/inventory, Obsidian query, verification, Codex preview, long-running tasks, sandbox terminal, self-status, and Cartographer.
- `/coding` has durable JSON-backed run storage at `data/coding-runs.json` by default, active/recent run APIs, row upsert, duplicate-running-row demotion, terminal-reopen blocking, and diagnostic fields.
- Verification is stronger than artifact-existence only: diff preview, replacement-content validation, protected path checks, visual-diff materiality gates, changed-file diagnostics, and durable-run invariants exist.
- Obsidian has a real read-only adapter, not just docs: `source_proxy/context/obsidian.py`, `/v1/context/obsidian/query`, `source_proxy/context/source_readiness.py`, and tests.

## Biggest Risks

- False-positive risk remains: old evidence and some UI labels can still make preview/runtime success look like product behavior success.
- Obsidian is discoverable and searchable, but not freshness-ranked, metadata-normalized, audited, write-safe, or proven to improve routing decisions.
- The context-source readiness packet is tested but not clearly wired into the main route-selection or coder prompt execution path.
- Local worker/model paths are real but gate/config/state sensitive. A focused test failed because the central gate approved increment was `evaluation-round` while the test expected `1.3`.
- `/coding` frontend regression hit a Vitest module-resolution failure on `Z:\`, so browser/UI proof remains weaker than backend/type proof in this audit.

## Close To Brain Design

- Brainstem: health/status endpoints and self-status manifest are close.
- Thalamus: decision router and prompt-packet path are real but incomplete.
- Sensory cortex: repo map, context inventory, Scout/search, design vault, and Obsidian adapters exist.
- Hippocampus: evidence docs, Cartographer state, durable run store, and Obsidian read-only notes exist.
- Amygdala/Prefrontal: path safety, central gates, approval boundaries, and Cartographer risk logic exist.
- Cerebellum: diff verification and focused regression tests are real.
- Motor cortex: terminal/Codex/model/apply surfaces exist, but most are guarded or preview-only.

## Missing Before Revamp

- One canonical cognitive loop: sense -> understand -> remember -> prioritize -> plan -> choose worker -> act -> verify -> learn.
- A single source-of-truth memory/context packet used by route selection and worker selection.
- Behavior-level verifier criteria for product tasks, not only existence/diff/runtime checks.
- Explicit Obsidian trust policy: metadata, freshness, conflict handling, citation/evidence links, write approvals, and audit trail.
- Clear deprecation/quarantine list for doc-only plans, stale evidence, and preview-only surfaces.

## Obsidian Readiness

Obsidian trust level: READ-ONLY ONLY

Obsidian is ready to be used as bounded, read-only advisory context for memory/context packets. It is not ready for automatic write-back, authoritative planning, or route/model selection. The code can discover `data/design-vault`, query Markdown notes, apply exclude globs, redact secret-shaped values, and return safe excerpts. It lacks durable indexing, metadata contracts, freshness scoring, bidirectional evidence links, write audit, approval gates for writes, and demonstrated influence on Source Proxy route/model/planning decisions.

## Must Fix Before Revamp

- Separate runtime GO from product behavior PASS in all runner/evidence labels.
- Make context-source readiness an actual input to route and worker selection, or clearly label it advisory-only.
- Add Obsidian metadata/frontmatter conventions, freshness checks, and evidence links before trusting it beyond read-only.
- Repair focused coding diagnostics failures and the `Z:\` Vitest module-resolution issue or document them as current environment blockers.
- Define a single memory write-back policy with Britton approval.

## Recommended Next Step

Create a short approval-gated design brief for Hippocampus v0.1 that promotes Obsidian to read-only contextual memory first, while keeping evidence docs and durable run store as the authoritative proof trail.

No implementation plan has been created yet unless Britton approves.
