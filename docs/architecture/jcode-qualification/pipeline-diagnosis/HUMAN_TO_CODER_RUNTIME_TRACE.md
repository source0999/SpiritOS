# Human-to-Coder Runtime Trace

## Verdict

The active generic Source Proxy path is not the intended JCode tool path. The
frontend reaches the prompt-packet API, which normalizes, routes, researches,
and constructs context. For implementation work it ultimately calls the
replacement-content Coder through the model router with a static two-message
chat request. It does not dispatch JCode and does not provide a model tool
loop. JCode preparation, containment, bridge, and evidence modules are present,
but no production HTTP callsite invokes a JCode dispatcher.

This trace is bound to Campaign 2-J starting HEAD
`07151b44cb886ac4d8c3668e947e81825d01bd50` and the exact diagnostic receipts
under `pipeline-diagnosis/runs/`. The machine-readable trace records every
required field for each edge.

## Active Path

| Order | Edge | Status | Implementation and finding |
| ---: | --- | --- | --- |
| 1 | Human request | `PROVEN_RUNTIME_ACTIVE` | `src/components/coding/CodingCockpitShell.tsx` posts to `/v1/decisions/prompt-packet`. |
| 2 | Request authentication | `ABSENT` | Neither the Next BFF `POST` nor FastAPI `prompt_packet` requires an auth assertion or route token. Network perimeter controls are outside this route proof. |
| 3 | Intent/task normalization | `PROVEN_RUNTIME_ACTIVE` | `prompt_packet` clears stale file focus and calls `build_task_spec_intake`. |
| 4 | Acceptance-criteria creation | `ABSENT` | `TaskSpecIntake` has no acceptance-criteria field; its legacy adapter emits `literal_requirements: []`. |
| 5 | Repository selection | `PROVEN_BUT_PARTIAL` | Target plugins can supply a workspace; otherwise `_workspace_root()` selects the process checkout. There is no packet-bound repository identity for the generic path. |
| 6 | Repository search | `PROVEN_RUNTIME_ACTIVE` | FIP-1 and FIP-2 context/research builders are called before model work. |
| 7 | Relevant-file discovery | `PROVEN_BUT_PARTIAL` | Explicit target resolution and research sources exist, but support/test-file completeness is not required. |
| 8 | Context construction | `PROVEN_BUT_PARTIAL` | `_build_canonical_context_packet` assembles supplied, target, research, and optional memory context. Consumer acknowledgements may still report no-go. |
| 9 | Context truncation/ordering | `DATA_TRANSFORMED_WITH_LOSS` | Target text is sliced to 6,000 characters without a critical-byte truncation receipt; generic governance and history precede or surround task data. |
| 10 | Canonical task packet | `PROVEN_BUT_PARTIAL` | `build_prompt_packet` creates a human-oriented paste-back packet, not the concise model-ready coder contract required by this audit. |
| 11 | Executor selection | `PROVEN_RUNTIME_ACTIVE` | `_bounded_coder_diff_or_stub` calls `_propose_coder_via_executor`, then `propose_coder_agent_diff_payload_from_plan`. |
| 12 | Provider-profile selection | `PROVEN_RUNTIME_ACTIVE` | `_call_coder_llm` resolves a model alias through the central model router. Exact digest binding is not carried in the generic request. |
| 13 | JCode invocation | `CONFIGURED_NOT_ACTIVE` | Qualification constants describe a JCode route, but no API/task callsite dispatches it; the referenced production `source_proxy/jcode/dispatcher.py` is absent. |
| 14-15 | JCode system/project instructions | `CODE_PRESENT_NOT_INVOKED` | The binary supplies them only in isolated JCode executions. They are not on the active generic path. |
| 16 | Model-visible messages | `PROVEN_RUNTIME_ACTIVE` | Generic Coder sends one static system message plus one rendered user packet through `get_router().completion`. |
| 17-27 | Tools, relay, bridge, parse, execute, reinject, recovery | `BYPASSED` | The active Coder asks for replacement JSON with `stream: false`; it sends no tools and has JSON-format repair, not a read/edit/test observation loop. |
| 28 | Patch/diff collection | `PROVEN_RUNTIME_ACTIVE` | Validated replacement content is converted into the approval diff payload. |
| 29 | Tests | `PROVEN_RUNTIME_ACTIVE` | Diff preview and post-apply verification paths exist and are covered by retained campaign gates. |
| 30 | Reviewer | `PROVEN_RUNTIME_ACTIVE` | `CodingOrchestrator` invokes the independent reviewer before verified completion. |
| 31 | Verifier | `PROVEN_RUNTIME_ACTIVE` | The orchestrator requires coder/reviewer completion and invokes verification. |
| 32 | Anti-cheat | `PROVEN_RUNTIME_ACTIVE` | The orchestrator invokes `run_coding_anti_cheat` and blocks on failure. |
| 33 | Canonical terminal truth | `PROVEN_RUNTIME_ACTIVE` | `terminal_truth_payload` and `terminal_truth_is_valid` gate finalization. |

## JCode Diagnostic Path

The isolated diagnostic path proves that the pinned JCode binary emits an
OpenAI-compatible request with ordered roles, `tool_choice: auto`, and native
tool schemas. The legacy compatibility bridge then flattens content into one
prompt for Ollama `/api/generate`, dropping roles and all tools. The corrected
diagnostic profile preserves those fields through `/api/chat`, but Qwen emits
the intended read operation as assistant text; JCode records zero tool events.

The next component therefore does not receive what the prior component claims
in three places: production intake loses explicit acceptance criteria, full
packet construction obscures task-critical context, and the legacy JCode bridge
loses role/tool structure. In the baseline action loop, a successful read
observation is retained internally but never returned to the model before the
loop exits.

## Evidence Boundary

No production request was generated for this audit. Runtime-active labels use
the retained Campaign 2-J acceptance receipts plus executable callsites at the
frozen HEAD. JCode transformation labels use exact captured bytes from the 24
diagnostic runs. The prior Gate 2-J.9I receipt stores request/response hashes but
not the raw response bytes, so its model-attribution statement is
`EVIDENCE_INCOMPLETE` and is refined by this audit rather than treated as raw
model incapability.
