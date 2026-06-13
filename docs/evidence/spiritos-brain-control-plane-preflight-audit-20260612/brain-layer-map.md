# Brain Layer Map

## Brainstem Health

Intended role: uptime, survival, service health, status truth.

Existing pieces: `source_proxy/main.py`, `source_proxy/api/healthcheck.py`, `source_proxy/self_status.py`, `/healthcheck`, `/v1/self/status`, `/v1/models`, `routing_status()`, `ollama_route_status_entry()`, `src/app/v1/self/status/route.ts`.

Real wiring: Source Proxy includes healthcheck and self-status routers. Self-status reports configured roots, tools, routes, model routes, provider capabilities, Codex CLI status, context bundle status, and Obsidian diagnostics.

Partial/stale/doc-only evidence: status manifests are read-only and do not prove active end-to-end task success. `/v1/models` can report configured/enabled models but does not prove a prompt completed.

Grade: PARTIAL

Proof still needed: live service availability checks from the deployed lane, fresh `/healthcheck`, `/v1/self/status`, and `/v1/models` receipts without provider calls.

## Thalamus Router

Intended role: route inputs and context to the right processing lane.

Existing pieces: `source_proxy/decision/router.py`, `source_proxy/api/decision.py`, `/v1/decisions/route`, `/v1/decisions/prompt-packet`, `DecisionInput`, `RouteDecision`, `recommend_route`, target resolution, unsafe target checks.

Real wiring: decision router is imported by prompt-packet generation and decision API. Implementation tasks are forced toward local route. Hard target blocks remove repo-first research expectations.

Partial/stale/doc-only evidence: context-source readiness exists separately and is not clearly part of `decide_route()`. Obsidian diagnostics are present but do not appear to drive route choice.

Grade: PARTIAL

Proof still needed: test proving context packets and memory/Obsidian signals affect route decisions, or a documented advisory-only boundary.

## Sensory Parsers

Intended role: parse repo, logs, screenshots, browser state, files, media, calendar, evidence, and external signals.

Existing pieces: `source_proxy/context/inventory.py`, `source_proxy/context/source_readiness.py`, `source_proxy/cartographer/repo_map.py`, `source_proxy/cartographer/component_mapper.py`, `source_proxy/decision/research.py`, Scout APIs, design-vault packet code, `repomix` scripts.

Real wiring: context-source readiness builds Cartographer, Obsidian, Scout search, and design packets. Cartographer packet includes repo map, component map, dirty-tree status, and blueprint truth.

Partial/stale/doc-only evidence: browser/screenshot behavior verification exists mostly in tests and prior evidence; not unified into Source Proxy's core route loop.

Grade: PARTIAL

Proof still needed: one canonical sensory packet consumed by router, planner, worker selector, and verifier.

## Hippocampus Memory

Intended role: project memory, prior failures, evidence history, user preferences, Obsidian vault, durable context.

Existing pieces: `docs/evidence/**`, `data/coding-runs.json`, `source_proxy/context/obsidian.py`, `source_proxy/context/source_readiness.py`, `source_proxy/proxy_memory/scout_intake.py`, `_blueprints/**`, Cartographer audit/evidence modules, `data/design-vault/**`.

Real wiring: Obsidian can discover a default local vault at `data/design-vault`, query Markdown notes, rank by query terms, return safe excerpts, and expose `/v1/context/obsidian/query`. Context-source readiness includes Obsidian as read-only source. Prompt-packet metadata includes Obsidian diagnostics.

Partial/stale/doc-only evidence: default prompt packets call `obsidian_context_diagnostics()` but do not include selected Obsidian note excerpts. Long-running coder diagnostics explicitly set `obsidian_context_used_in_prompt: false`. No proof found that Obsidian affects Source Proxy route/model/planning decisions today.

Obsidian vault discovery: PARTIAL. Discovers `OBSIDIAN_VAULT_PATH` or local `data/design-vault`.

Obsidian note access: PARTIAL. Reads Markdown excerpts with exclusions and redaction.

Obsidian indexing/search: WEAK. Uses filesystem globbing and simple term scoring, not a durable index or semantic ranking.

Obsidian context packet generation: PARTIAL. `build_obsidian_context_packet()` exists and is tested.

Obsidian write/update safety: MISSING for writes by design. Current adapter is read-only.

Obsidian mode: read-only, not write-capable.

Source Proxy use today: diagnostics and optional context-source readiness packet; not proven as main route/model/planning input.

Ready for higher trust: only as read-only advisory context.

Grade: PARTIAL

Proof still needed: freshness metadata, source citations, conflict handling, approval-gated writes, and route/planner integration tests.

## Amygdala Risk/Vibe Judge

Intended role: risk, urgency, fake-green detection, user-frustration/vibe, workflow conflict detection.

Existing pieces: `source_proxy/safety/paths.py`, `source_proxy/verification/contracts.py`, `source_proxy/verification/diff.py`, `source_proxy/approval/external_gate.py`, Cartographer safety/trust modules, durable run invariants, false-positive evidence.

Real wiring: protected path, secret path, path escape, central gate, approval preview, visual materiality, replacement-content validation, and run-invariant checks exist.

Partial/stale/doc-only evidence: user-frustration/vibe and fake-green detection are not a unified service; product behavior checks are still uneven.

Grade: PARTIAL

Proof still needed: standard failure taxonomy that blocks GO when product behavior is untested.

## Prefrontal Planner

Intended role: ARPA planner, phase/increment manager, permission gates, executive judgment.

Existing pieces: `source_proxy/planning/*`, long-running tasks, `source_proxy/approval/*`, `.gate/state.json` workflow, Cartographer approval-token/runtime modules.

Real wiring: model calls and apply paths use central/external gates. Long-running tasks have plan, advance, reject, execute-approved, verification, cancel, and stream routes.

Partial/stale/doc-only evidence: many Cartographer autonomy levels are broad and partly doc/preview/dry-run. This audit did not run live planner flows.

Grade: PARTIAL

Proof still needed: a single permission gate model for planning, memory reads, memory writes, worker calls, and apply.

## Basal Ganglia Model Selector

Intended role: choose local vs Codex vs API vs handoff worker.

Existing pieces: `source_proxy/routing/litellm_router.py`, `source_proxy/routing/ollama_route.py`, `source_proxy/decision/recommendation.py`, `source_proxy/codex/adapter.py`, `source_proxy/api/codex_adapter.py`, worker scripts, `/v1/models`.

Real wiring: model aliases include `local`, `coder`, `classifier`, `openai`, `anthropic`, `deepseek`. Local Ollama probes are cached and choose candidate models. Codex route validates safe command envelopes but does not execute live tasks.

Partial/stale/doc-only evidence: selection is mostly rule/config based. Memory/Obsidian does not influence worker choice today.

Grade: PARTIAL

Proof still needed: explicit worker-selection policy with cost, capability, confidence, context, and approval gates.

## Cerebellum Verifier

Intended role: tests, browser probes, screenshots, diffs, simulation, behavior checks.

Existing pieces: `source_proxy/verification/*`, `source_proxy/api/diff_verification.py`, Vitest/pytest suites, Playwright tests, UI agent trials, durable run invariants.

Real wiring: diff preview and replacement-content validation are API-backed. Focused context/routing pytest passed. Typecheck passed.

Partial/stale/doc-only evidence: frontend regression command failed on `Z:\` module resolution. Product behavior verification remains incomplete.

Grade: PARTIAL

Proof still needed: browser/product behavior probes that can fail calculator/theme/static-habit false positives.

## Motor Cortex Executor

Intended role: terminal, file edits, browser automation, Codex launch, local model calls, apply.

Existing pieces: `/v1/tasks/long-running/{task_id}/execute-approved`, `/v1/sandbox/terminal/run`, Codex command envelope, Cartographer safe-write/apply/queue modules, Source Proxy chat completions.

Real wiring: apply requires approved request. Chat completions require central model-call gate and spend approval before provider routes. Sandbox terminal is read-only bubblewrap with 30 second timeout.

Partial/stale/doc-only evidence: Codex server-side live execution is disabled by route response. Cartographer has many executor-looking surfaces that need careful gating.

Grade: WEAK

Proof still needed: controlled executor with receipts, no hidden workers, clear rollback, and real behavior verification.

## Feedback/Learning Loop

Intended role: evidence, diagnostics, memory updates, learning from success/failure.

Existing pieces: `docs/evidence/**`, durable run store, Cartographer audit trail/evidence modules, coding diagnostics, Source Proxy expenditure logger, Scout intake memory.

Real wiring: `/coding` stores run rows and diagnostics. Evidence docs are extensive. Source Proxy exposes diagnostics and stores some expenditure records.

Partial/stale/doc-only evidence: no unified learner. Obsidian write-back is absent. Evidence docs are not consistently indexed into route decisions.

Grade: WEAK

Proof still needed: approved memory ingestion pipeline from verified outcomes to Obsidian/evidence/index, with stale/conflict handling.
