# Gate 2-J.9 Sealed Authority Decisions

status: `ALL_FIVE_DECISIONS_SEALED_FROM_EVIDENCE`

schema: `source-proxy.gate-2j-9-sealed-authority-decisions/v1`
sealed_by: GLM campaign authority architect
sealed_at_utc: 2026-07-29T20:10:00Z

This record seals the five Gate 2-J.9 authority decisions from current repository source, the
live model registry, current executor implementations, existing campaign policy, Dell host
capabilities, prior qualification evidence, frozen-benchmark constraints, and safety/authority
invariants. No operator choice among technically resolvable options was required. Machine-readable
canonical artifacts accompany each decision (see references).

## Verified evidence basis

- Live registry (2026-07-29): `http://127.0.0.1:11434/api/tags` reachable, 12 models.
  `qwen2.5-coder:7b` digest `dae161e2...` and `qwen2.5-coder:14b` digest `9ec8897f...` both
  present and exact-matching the sealed snapshot.
- Port 4000 (`http://127.0.0.1:4000/v1`, referenced by the Gate 2-J.8.5 packet as
  `jcode_sandbox_endpoint`) is NOT live. Only 11434 is live. The sealed provider profile binds
  to 11434; the 4000 slot is retracted.
- Proven local-model executor: `run_bounded_agent_loop` (`source_proxy/decision/tool_action_loop.py`)
  driven by `_ollama_generate` (`source_proxy/decision/human_messy_homepage.py`), model client
  `OllamaRouteResolution` (`source_proxy/routing/ollama_route.py`).
- Orchestrator authority: `CodingOrchestrator` (`source_proxy/coding/orchestrator.py`, `coding-orchestrator/v2`).
- Context builder: `build_context_broker_report` (`source_proxy/context/canonical_broker.py`, schema 2).

## Decision 1 - Lane and executor binding (SEALED)

- Lane A (existing baseline, primary): `run_bounded_agent_loop` + `qwen2.5-coder:7b`.
- Lane B (JCode, primary): sealed JCode CLI dispatcher (pending impl) + `qwen2.5-coder:7b`.
- Lane C (existing baseline, challenger): `run_bounded_agent_loop` + `qwen2.5-coder:14b`
  (strongest suitable local coding challenger: present, available, exact coding-family, larger
  params, exact digest, compatible with the proven coding endpoint).
- Lane D (JCode, challenger): sealed JCode CLI dispatcher (pending impl) + `qwen2.5-coder:14b`.
- Rejected: hermes4, llama3.x, gemma3n, advisory GGUF pulls, cloud models (rationales in
  `gate_2j_9_lane_bindings.json`).
- Reference: `gate_2j_9_lane_bindings.json`.

## Decision 2 - Context-packet construction (SEALED)

- Adapt `build_context_broker_report` into `spiritos-qualification-context-builder/v1`.
- Canonical task -> deterministic builder -> immutable packet -> identical packet per pair
  (A==B, C==D). Ordered manifest, per-file SHA-256, packet SHA-256 via canonical JSON.
- Excludes hidden tests, benchmark expectations, verifier internals, prior solutions, daily
  runtime, campaign-history dumps. Budget 256 KiB / 48 files / 32 KiB per file.
- Reference: `gate_2j_9_context_policy.json`.

## Decision 3 - Provider profile and model bridge (SEALED)

- Profile `spiritos-qualification`; bridge `sealed-loopback-inference-bridge/v1` over the
  existing fixed-loopback Unix byte bridge; permitted endpoint `http://127.0.0.1:11434/api/generate`.
- No-auth; no credentials in the JCode environment; LiteLLM `ollama_chat/<model>` transport;
  `direct_ollama` bypass forbidden.
- Rejects `/coding`, external/cloud providers, arbitrary base URL/redirect, model fallback,
  unregistered models, recursion. Fails closed when identity unproven.
- Corrects the dead 4000 slot.
- Reference: `gate_2j_9_provider_profile.json`.

## Decision 4 - Budgets and limits (SEALED)

- Conservative qualification budgets across process / model / tools / evidence, each with
  rationale. Shared per pair. Exhaustion -> `BLOCKED_OR_DEGRADED_TRUTHFULLY`, never silent
  extension, never `COMPLETED_VERIFIED` on incomplete evidence.
- Highlights: wall-clock 300 s, inactivity 60 s, pids 256, CPU 400%, memory 6 GiB,
  max requests 8, tokens 32768 in/out, tool calls 48, shell commands 0, deletes 0,
  NDJSON line 256 KiB, events 50000. Full table in `gate_2j_9_budget_policy.json`.
- Reference: `gate_2j_9_budget_policy.json`.

## Decision 5 - Real-model identity probe (SEALED)

- Deferred to Gate 2-J.9H. No real model request during Gate 2-J.9F.
- Gate 2-J.9F uses a fake deterministic inference endpoint with signed/hashed expected model
  metadata plus negative tests (mismatch, budget, recursion, external egress).
- First real local-model request only at Gate 2-J.9H under its explicit gate authorization,
  after containment, supervision, event capture, writable-overlay, bridge enforcement, and
  JCode no-model execution are all proven.

## Effect on prior amendment artifacts

- `GATE_2J_9_AUTHORITY_CONSTANTS_MATRIX.md`: the six previously-MISSING execution constants and
  the budget/event-schema slots are now SEALED (values in the machine-readable JSON). The
  matrix is superseded for sealed values by `gate_2j_9_authority_constants.json`.
- `GATE_2J_9_SEALED_EXECUTION_ARCHITECTURE.md` "Open operator decisions": all five are resolved
  here; the architecture's mechanism selections (bwrap + systemd scope + cgroup v2; attesting
  loopback bridge; strict NDJSON; pgrp+cgroup supervision; read-only base + overlay + independent
  diff) are unchanged and now backed by sealed constants.
- No authority model change. JCode remains disabled. No benchmark or daily-runtime change.
