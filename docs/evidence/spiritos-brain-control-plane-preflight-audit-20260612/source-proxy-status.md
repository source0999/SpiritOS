# Source Proxy Status

## Current Routes And Entry Points

Source Proxy FastAPI entry point is `source_proxy/main.py`. It includes routers for:

- `/healthcheck`
- `/v1/actions/preview`
- `/v1/cartographer/**`
- `/v1/chat/completions`
- `/v1/models`
- `/v1/coding/codex`
- `/v1/coding/bounded-diff-preview`
- `/v1/coding/self-tests/run`
- `/v1/context/index`
- `/v1/context/inventory`
- `/v1/context/obsidian/query`
- `/v1/decisions/route`
- `/v1/decisions/prompt-packet`
- `/v1/decisions/recommend-model`
- `/v1/decisions/api-vs-manual-preview`
- `/v1/verification/diff-preview`
- `/v1/verification/manual-result-preview`
- `/v1/tasks/long-running/**`
- `/v1/sandbox/terminal/**`
- `/v1/self/status`
- `/v1/tools/manifest`
- `/v1/workspace/list`
- `/v1/workspace/read`

Next.js bridge routes under `src/app/v1/**` proxy or expose many of these to the app shell, including `/v1/coding/runs/**`, `/v1/coding/codex`, `/v1/coding/bounded-diff-preview`, `/v1/actions/execute-approved`, and Cartographer routes.

## Model Routing Behavior

`source_proxy/routing/litellm_router.py` defines aliases:

- `local`: Ollama general local route.
- `coder`: Ollama coder route, preferring Qwen coder candidates when available.
- `classifier`: Ollama classifier route, preferring Phi-4 Mini.
- `openai`, `anthropic`, `deepseek`: key-gated paid/provider routes.

`/v1/models` reports route status. `/v1/chat/completions` checks `central_gate_check("model_call")` before calling the LiteLLM router. Paid routes also run spend-before-send approval.

## Local Model Behavior

Local model availability is probed through Ollama `/api/tags` with short timeout and cached status. The coder alias prefers `qwen2.5-coder:7b`, then larger/alternate coder models, then the default local model. This audit did not send any model prompt.

## Provider/API Route Boundaries

Provider/API calls are behind:

- central external gate for `model_call`
- alias enabled checks
- spend approval hook for paid providers
- no streaming in current route

Focused tests confirm routing/status code paths, but a coding diagnostics test failed because gate state approved `evaluation-round` instead of expected increment `1.3`.

## Artifact Creation Behavior

Source Proxy can create prompt packets, proposed diffs, verification previews, long-running task state, and coding run diagnostics. `/v1/coding/bounded-diff-preview` is preview-only and returns a deterministic bounded diff for allowed trial IDs. `/v1/tasks/long-running/{id}/execute-approved` is the actual apply path and requires explicit approval fields.

## Scoring/Verdict Behavior

There are multiple verdict layers:

- route decisions: local/API/manual/ask-user
- diff preview: preview ready/blocked with reason codes
- coding runner rows: PASS, NEEDS FIX, INVALID, RUNNING, etc.
- evidence docs: GO/NO-GO/PASS/FAIL language
- durable store: status, result labels, reason codes, provenance

Current risk: labels are not fully canonical. Preview success can still be confused with behavior success unless the verifier forces product behavior proof.

## Known False-Positive Risks

- Artifact exists but behavior fails.
- Diff present but product behavior untested.
- UI class toggles but no visible state changes.
- Static output marked as success.
- Preview-only route marked as production-ready.
- Provider/model route configured but no successful prompt proof.
- Obsidian diagnostics present but no selected memory used in decision.

## Diagnostics Available

- `/v1/self/status`
- `/v1/tools/manifest`
- `/v1/models`
- coder diagnostics fields in prompt-packet/coder payloads
- context metadata with Obsidian diagnostics
- diff verification result and reason codes
- durable run store write debug and invariant violations
- Cartographer repo/health/trust/evidence endpoints

## Obsidian/Context Integration

Current integration points:

- `source_proxy/context/obsidian.py`
- `source_proxy/api/obsidian_context.py`
- `source_proxy/context/source_readiness.py`
- `source_proxy/self_status.py`
- `source_proxy/decision/prompt_packet.py`
- `source_proxy/tasks/long_running.py`

Source Proxy can query Obsidian through `/v1/context/obsidian/query`. Prompt packets include `memory_context_diagnostics`, but baseline prompt packet generation does not select or inject note excerpts. Coder diagnostics include `obsidian_context_used_in_prompt: false`.

Does Source Proxy actually query Obsidian today: yes, through the dedicated context query endpoint and context-source readiness builder. Not proven in the main route/model/planning path.

Does Obsidian affect route/model/planning decisions today: not proven; likely no for route/model selection.

## Tests Proving Real Behavior

Passed in this audit:

- `python -m pytest -q source_proxy/tests/test_obsidian_context.py source_proxy/tests/test_context_source_readiness.py source_proxy/tests/test_self_status.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_proxy_agent_routing.py source_proxy/tests/test_ollama_route.py`
- Result: 87 passed.

Also passed:

- `npm run typecheck`

## Not Proven

- No live Source Proxy prompt/model call was run.
- No live browser behavior proof was run.
- No Obsidian-selected notes were proven to affect route choice.
- No active deployed route health was tested.
- No full frontend regression pass was obtained on `Z:\`.

## Before Source Proxy Becomes Cognitive Route Brain

- Make context-source readiness an actual route/planner input or label it advisory.
- Create a canonical verdict model separating runtime, artifact, preview, apply, and product behavior.
- Add route tests proving Obsidian/memory signals are either used or explicitly ignored.
- Add behavior verifiers for UI/product tasks.
- Keep model/provider calls behind explicit gate and spend approval.
