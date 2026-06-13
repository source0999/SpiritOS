# Worker And Route Status

## Local Model Route Support

Local route support exists through Ollama:

- `source_proxy/routing/ollama_route.py`
- `source_proxy/routing/litellm_router.py`
- aliases: `local`, `coder`, `classifier`
- `/v1/models`
- `/v1/chat/completions`

The coder route prefers Qwen coder models when installed. The classifier route prefers Phi-4 Mini. Route status is probed without sending a prompt.

## Codex/CLI/Handoff Support

Codex support exists as a safe command-envelope validator:

- `source_proxy/codex/adapter.py`
- `source_proxy/api/codex_adapter.py`
- `src/app/v1/coding/codex/route.ts`

It validates safe sandboxes, blocks dangerous flags, blocks `danger-full-access`, and returns command preview/status. Server-side live Codex execution is explicitly disabled in the route response.

Manual prompt packet/handoff support exists through `/v1/decisions/prompt-packet`.

## Continue/Aider/Goose/Raw API Evidence

Scripts exist under `scripts/agent-trials/**` for Aider, Goose, Continue, Qwen/Ollama diagnostics, and comparison runs. This audit did not run them and did not mutate previous benchmark artifacts.

## Route Choice

Route choice is mostly automatic/rule-based:

- implementation tasks force local route
- current research/codebase context can recommend research
- sensitive/high-risk routes add constraints
- model aliases depend on env and local probes

Worker choice is not yet a mature basal-ganglia selector. It does not appear to consider Obsidian memory, prior model performance, budget, user frustration, or recent failure evidence as first-class inputs.

## Cost/Usage Policy

Paid API routes require spend-before-send approval. Model calls require central gate. The route status reports missing API keys. No full cost optimizer/usage planner was found.

## Local Model Limitations

Some limitations are known in code/evidence:

- model output can be malformed
- no-diff/productive-output failures exist
- coder route can timeout
- local prompt proof depends on central gate state and configured alias
- tests failed on gate mismatch in this audit

## Out-Of-Scope Handoff Packets

Manual prompt packets and blocked route responses exist. Codex route returns preview/config-blocked payloads rather than executing. Protected/unsafe targets produce reason-coded blocks.

## Memory/Obsidian Influence

No proof found that Obsidian influences worker choice today. Prompt metadata can report Obsidian diagnostics, and context-source readiness can include Obsidian notes, but basal-ganglia route/worker selection does not appear memory-driven.

## Grade

Worker routing grade: PARTIAL

## Basal Ganglia v0.1 Requires

- Single worker registry with capabilities, cost, latency, risk, model limitations, and required approvals.
- Explicit local-vs-Codex-vs-API-vs-manual handoff policy.
- Memory/evidence-informed selection, including prior failures and model performance.
- A no-hidden-worker rule.
- Tests proving wrong-scope/high-cost/provider routes ask first.
- Clear route receipts for why a worker was chosen.
