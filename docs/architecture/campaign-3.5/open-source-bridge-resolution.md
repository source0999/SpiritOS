# Campaign 3.5 open-source bridge resolution

## Decision

Source Proxy remains the only canonical local coding control plane. No
LangGraph, OpenHands, or OpenAI Agents SDK dependency is installed. Adding one
only to make a benchmark label appear in a trace would be decorative and would
create a second owner for workflow state, tool dispatch, or approval.

The six requested candidates are resolved as follows:

| Candidate | Resolution | Bounded responsibility and claim ceiling |
| --- | --- | --- |
| LangGraph | `SUPERSEDED_BY_SOURCE_PROXY_NATIVE_CONTROL_PLANE` | Native durable lane state, recovery lineage, causal events, and human approval cover the Campaign 3.5 workflow responsibility. This is not a claim that LangGraph ran. |
| OpenHands | `SUPERSEDED_BY_SOURCE_PROXY_NATIVE_CODER` | The authenticated Source Proxy lifecycle owns planning, proposal, review, verification, and gated apply. This is a comparison for the local coder responsibility, not a claim of feature parity with the whole OpenHands product. |
| OpenAI Agents SDK | `SUPERSEDED_BY_SOURCE_PROXY_NATIVE_LANES` | Source Proxy owns typed lane contracts, handoff outputs, consumer acknowledgements, model invocation records, and final evidence. This is not an Agents SDK invocation claim. |
| Mac Search | `UNSUITABLE_FOR_CANONICAL_CODER_SEARCH` | The worker's `repo_context_search` is a useful read-only diagnostic, but it searches the Mac's fixed checkout, is not bound to the disposable target worktree, and has no non-test Source Proxy caller. Canonical target-bound architect/context selection supersedes it for coding. |
| Scout | `INTEGRATED_AS_OPTIONAL_EVIDENCE_ONLY_RESEARCH` | Scout is a bounded research adapter and extended advisory lane. Empty or unavailable results remain explicit; Scout has no apply, approval, or proxy-memory mutation authority. It is not automatically influential in every coder run. |
| Obsidian / retained context | `INTEGRATED_AS_READ_ONLY_CONTEXT` | Obsidian supplies bounded local-note excerpts to Source Proxy context packets and the extended advisory lane. Selection is not consumption: the canonical broker still requires explicit downstream acknowledgement. |

## Repository capability comparison

| Required capability | Candidate expectation | Existing Source Proxy evidence | Authority/state decision |
| --- | --- | --- | --- |
| Durable, resumable workflow | LangGraph-style graph/checkpoint ownership | `source_proxy/coding/orchestrator.py` defines `CodingLaneStateMachine`, persisted causal events, attempt/recovery lineage, `_restore`, and explicit lane transitions. | Keep one durable state owner. A second graph store would split recovery truth. |
| Local coding agent and workspace loop | OpenHands-style agent/tool/workspace ownership | `source_proxy/coding/orchestrator.py`, `source_proxy/target_plugins/adapter.py`, `source_proxy/verification/diff.py`, and `source_proxy/approval/campaign_authority.py` form the native proposal-to-verification boundary. | Source Proxy remains the authenticated task owner; exact-diff approval and apply cannot be delegated to a second control plane. |
| Agent handoffs and traces | Agents SDK-style agent/handoff/trace responsibility | `source_proxy/coding/orchestrator.py` records runtime outputs, acknowledgements, consumptions, participant records, model invocations, and final authority evidence. `source_proxy/approval/external_gate.py` is the central model/apply gate. | Native receipts are the canonical trace. An SDK may be reconsidered only if it adds a capability without owning durable state or approval. |
| Target-repository search | Mac Search | `source_proxy/planning/architect.py` and `source_proxy/context/canonical_broker.py` operate on the selected target workspace and require bounded, acknowledged context. | Mac Search is not accepted as coder evidence because `run_mac_worker_for_task(..., mode="mac_search_packet")` has no production caller and its search receipt is not source-bound. |
| Current research | Scout | `source_proxy/decision/scout_research.py` filters reviewed packets and marks authority `evidence_only`; `source_proxy/context/source_readiness.py` and `source_proxy/coding/extended_lanes.py` adapt it to bounded context/receipts. | Optional advisory input only. Missing sources degrade or block when explicitly required; they never manufacture citations. |
| Retained local knowledge | Obsidian / retained context | `source_proxy/context/obsidian.py` filters paths, excerpts, freshness, and conflicts; `source_proxy/context/source_readiness.py` adapts notes to the canonical broker. | Read-only retrieval only. `source_proxy/proxy_memory/scout_intake.py` is a separate append-only intake boundary and does not automatically promote records into coding context. |

The dependency manifests `requirements.core.txt`, `requirements.txt`,
`requirements.cuda.txt`, `package.json`, and `package-lock.json` contain no
LangGraph, OpenHands, or OpenAI Agents SDK package. A runtime-source scan found
no imports for those three candidates outside documentation, benchmark
metadata, and tests. Their statuses are therefore supersession decisions, not
installed or executed integrations.

The native-control-plane runtime anchor is the authenticated Phase 0 receipt at
`docs/evidence/campaign-3.5-integrated-coder-backend/phase-0-authenticated-run-20260719.json`:
it records one model invocation, an applied proposal awaiting verification,
completed verification, and a `GO` truth status. The associated trace map binds
that run to real Source Proxy emitters. This proof is deliberately narrow: it
does not establish general feature parity with any third-party framework or
prove the current uncommitted source head.

## Runtime probes and their limits

The sanitized receipt is
`docs/architecture/campaign-3.5/open-source-bridge-runtime-probes-20260722.json`.

- Mac connectivity was verified through the configured Dell hop. The Darwin
  worker executed `repo_context_search`, searched 1,538 tracked files, and
  returned three candidates. This proves the worker/search implementation is
  real. It does **not** prove production caller, target-source binding, broker
  consumption, or coder influence; those missing properties are why Mac Search
  is rejected for canonical coder search.
- The local Scout service on `127.0.0.1:8077` reported healthy/observing. A real
  `run_scout_research_diagnostics` call reached it and truthfully returned
  `skipped` with zero current packets. No hosted provider or bounded-fetch path
  was called. This proves the local adapter boundary, not useful downstream
  research for that query.
- A real local `query_obsidian_context` call returned `used`, selected five of
  five considered notes, and reported `obsidian_read_only: true`. It proves
  retrieval. It does not by itself prove a downstream consumer acknowledged
  those notes.

## M15 inventory correction

The immutable v1.1 benchmark task files remain unchanged. The generated
Campaign 3.5 inventory now renders M15's forward requirement as:

- `openai_agents_sdk_adapter capability required; runtime SDK invocation is not asserted`
- `OpenAI Agents SDK-equivalent orchestration capability is required; a runtime SDK trace is not asserted until an SDK adapter is implemented`

`source_proxy/benchmarks/campaign_3_5_assets/inventory.py` owns this presentation
overlay so a future inventory refresh cannot restore the false runtime
implication. This wording neither satisfies M15 nor authorizes an evaluator to
invent an SDK trace. If the immutable v1.1 oracle continues to require a literal
SDK invocation, M15 remains ineligible for that point until an independently
accepted versioned amendment recognizes the native equivalent.

The same evidence rule applies to the immutable M13 phrase "LangGraph step
trace": native Source Proxy events cannot be relabeled as a LangGraph runtime
trace. The supersession decision above resolves architecture ownership; it does
not rewrite historical v1.1 task definitions or fabricate framework execution.

## Reopen criteria

Reconsider an external framework only when a named missing capability is shown
with a production test and the integration can preserve all of these boundaries:
one Source Proxy task store, one approval authority, one central model/apply
gate, target-worktree binding, explicit context consumption, local execution,
and truthful failure receipts. Package presence, an adapter label, or a
synthetic trace is never sufficient.
