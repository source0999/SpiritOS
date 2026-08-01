# TERRA_HIGH_GATE_2J_9T_EXECUTION_PLAN.md

Controlling implementation plan that translates `PACKET_AMENDMENT.md` (Gate 2-J.9T)
into atomic, dependency-ordered engineering goals for Terra High. This is a PLAN
ONLY: it contains no implementation code. Terra High may not begin until the
operator adopts `TERRA_HIGH_AUTHORIZATION_GATE_2J_9T_A_TO_D_DRAFT.json` and pastes
`TERRA_HIGH_GATE_2J_9T_A_TO_D_PROMPT.md`.

- Amendment: `CAMPAIGN_2J_PACKET_TOOL_LOOP_COMPATIBILITY_AMENDMENT_V1`
- Gate: `Gate 2-J.9T — Model-Ready Packet, Tool Protocol, and Agent-Loop Qualification`
- Current state: `PACKET_AMENDMENT_ACCEPTED` / `IMPLEMENTATION_NOT_STARTED`
- Real model requests in Batch 1: **PROHIBITED** (0). Batch 1 is fixtures/fake-backends only.
- Stop boundary: **independent GLM review after 2-J.9T-D.** No Batch 2 until accepted.

---

## Batch map

| Batch | Goals | Gate coverage | Real model requests | GLM review after |
| --- | --- | --- | --- | --- |
| Batch 1 — Core packet and loop foundation | 4 | 2-J.9T-A … 2-J.9T-D | 0 | yes |
| Batch 2 — Validation, profiles, harness readiness | 4 | 2-J.9T-E … 2-J.9T-H | bounded (per goal) | yes |
| Final review | 1 | 2-J.9T-I | 0 (no automatic comparison start) | decision |

Global acceptance per batch: ALL four readiness outcomes in that batch must
exist before the batch passes; no single goal may imply full readiness.

---

## BATCH 1 — Core packet and loop foundation

Visible board Terra High must post before starting:

```text
CAMPAIGN 2-J — GATE 2-J.9T BATCH 1

Overall goal:
Build the model-ready packet, preserve chat and tools through the bridge,
normalize Qwen tool requests, and complete the observation-driven agent loop.

[ ] 1/4 — 2-J.9T-A: Packet Schema and Quality Validator
[ ] 2/4 — 2-J.9T-B: Chat-Preserving Bridge
[ ] 3/4 — 2-J.9T-C: Tool-Dialect Normalization
[ ] 4/4 — 2-J.9T-D: Observation Reinjection and Agent Loop

Real model requests: 0
Frozen benchmark runs: 0
Production-default changes: 0
Daily-runtime changes: 0
```

Markers: `[✓]` complete · `[!]` blocked · `[ ]` not started. Terra High must NOT
work silently through all goals — post a `STARTING GOAL X/4` block before each
goal and a `GOAL COMPLETE: X/4` block after each.

### Goal 1/4 — Gate 2-J.9T-A — Canonical Model-Ready Packet Schema and Quality Validator

| Field | Value |
| --- | --- |
| Goal ID | 2-J.9T-A |
| Gate | 2-J.9T-A |
| Objective | Implement the canonical task-first packet defined in PACKET_AMENDMENT.md section E, plus a deterministic quality validator |
| User-visible outcome | A packet builder that emits one canonical serialized packet + a validator that reports PASS/FAIL on all quality metrics |
| Dependencies | none (first goal) |
| Source files to inspect (read-only guidance) | `source_proxy/context/canonical_broker.py`, `source_proxy/context/source_readiness.py`, `source_proxy/decision/prompt_packet.py`, `source_proxy/tests/test_prompt_packet_context_metadata.py` |
| Permitted implementation paths | `source_proxy/context/model_ready_packet.py` (new), `source_proxy/context/packet_quality_validator.py` (new), `source_proxy/tests/test_model_ready_packet.py` (new), `source_proxy/tests/fixtures/model_ready_packet/**` (new deterministic fixtures) |
| Forbidden paths | `benchmarks/**`, `qualification_fixture/**`, `fixture_proxy/**`, production prompt-packet path used by live coding, daily-runtime worktrees |
| Interfaces and schemas | `glm-review/MODEL_READY_PACKET_SCHEMA.json`; packet sections: Task, Observable desired behavior, Acceptance criteria, Writable files, Read-only supporting files, Mounted tool paths, Focused validation command, Minimal constraints, Relevant source/test context, Tool definitions, Identity and hashes, Budgets, Stop condition |
| Implementation requirements | task-first ordering (task + acceptance before context/constraints); per-file SHA-256 + byte counts; truncation receipt; excluded-path manifest; no hidden expectations; no unrelated campaign history |
| Quality metrics required | relevance ratio; first critical-content byte; governance-marker count; critical-source presence; critical-test presence; path consistency; duplicate-content ratio; truncation state; total model-visible tokens; tool-schema tokens; available output budget |
| Test requirements | unit tests for each required section; validator PASS on a clean fixture; validator FAIL on each controlled failure below |
| Controlled failures required | missing task; missing acceptance criteria; missing source; missing test; path mismatch; relevance below threshold; governance contamination; contradictory instruction; truncated critical content; duplicate packet sections; nondeterministic ordering; hidden-answer marker |
| Acceptance criteria | relevance ratio ≥ 0.40; task + acceptance within first 1,024 bytes; zero unrelated governance markers; all required files present; model-visible paths equal sandbox paths; deterministic packet bytes; deterministic packet hash; no hidden-answer leakage; paired lanes receive identical packet bytes |
| Evidence artifacts | clean-fixture packet + hash; validator report; controlled-failure matrix; per-metric measurements |
| Stop conditions | relevance floor unreachable without leaking answers; schema contradicts amendment; fixture mutation required |
| Commit policy | one goal-scoped commit `feat(c2j-9ta): model-ready packet schema and validator`; explicit paths only; no `git add -A` |
| Push policy | push to `origin/codex/source-proxy-jcode-pipeline-diagnosis-20260731`; no merge, no force-push |
| Next authorized goal | 2-J.9T-B |

### Goal 2/4 — Gate 2-J.9T-B — Chat-Preserving Bridge Contract

| Field | Value |
| --- | --- |
| Goal ID | 2-J.9T-B |
| Gate | 2-J.9T-B |
| Objective | Implement a qualification bridge that preserves message roles, order, tool schemas, tool choice, model identity, generation parameters, tool-result role/name, streaming tool fragments, finish reason, and usage — via the `/api/chat` path proven by the Sol diagnostic correction |
| User-visible outcome | A qualification bridge that is byte-for-byte equivalent (modulo documented provider normalization) between pre-bridge and model-visible structures, behind a disabled qualification flag |
| Dependencies | 2-J.9T-A |
| Source files to inspect (read-only guidance) | `source_proxy/jcode/inference_bridge.py`, `source_proxy/jcode/real_inference_bridge.py`, `source_proxy/jcode/sealed_compatibility_bridge.py`, `source_proxy/jcode/pipeline_diagnosis.py` (the proven global-correction profile `C2J-GLOBAL-CORRECTION-01`), `source_proxy/jcode/network_bridge.py` |
| Permitted implementation paths | `source_proxy/jcode/qualification_bridge.py` (new), `source_proxy/tests/test_qualification_bridge.py` (new), `source_proxy/tests/fixtures/qualification_bridge/**` (new fake-backend fixtures) |
| Forbidden paths | production bridge used by live coding routing; `benchmarks/**`, `qualification_fixture/**`, `fixture_proxy/**`, daily-runtime worktrees |
| Interfaces and schemas | OpenAI `/v1/chat/completions` request in; Ollama `/api/chat` request out; OpenAI-compatible SSE reconstructed out; preserve roles system/user/assistant/tool, ordered messages, tools, tool_choice |
| Implementation requirements | qualification-only; behind a disabled diagnostic/qualification flag; isolated from production routing; NO production default change; map tool-result messages to tool names; reconstruct assistant content or native tool calls as OpenAI SSE |
| Test requirements | fake-backend contract tests asserting each preserved field; before/after structural equivalence test; FAIL on each controlled failure below |
| Controlled failures required | dropped system role; reordered messages; missing tools; changed tool name; removed required field; changed model; fallback attempted; malformed streaming fragment; incomplete tool call; wrong tool-result role; wrong result name; missing finish reason; truncated stream |
| Acceptance criteria | pre-bridge and model-visible structures semantically AND structurally equivalent except explicitly documented provider normalization; all 13 preserved fields asserted; legacy/production default untouched |
| Evidence artifacts | before/after request examples per field; fake-backend replay receipts; field-preservation counterfactual receipts |
| Stop conditions | equivalence impossible without changing production default; provider normalization cannot be made explicit |
| Commit policy | one goal-scoped commit `feat(c2j-9tb): chat-preserving qualification bridge`; explicit paths only |
| Push policy | push to the audit branch; no merge, no force-push |
| Next authorized goal | 2-J.9T-C |

### Goal 3/4 — Gate 2-J.9T-C — Native and Textual Tool-Dialect Normalization

| Field | Value |
| --- | --- |
| Goal ID | 2-J.9T-C |
| Gate | 2-J.9T-C |
| Objective | Normalize BOTH native OpenAI-style tool calls AND strict Qwen textual JSON tool calls into ONE canonical internal tool request |
| User-visible outcome | A normalizer with parser precedence (native first, then strict textual) that emits the canonical schema and rejects ambiguous text |
| Dependencies | 2-J.9T-B |
| Source files to inspect (read-only guidance) | `source_proxy/jcode/adapter.py`, `source_proxy/jcode/canonical_io.py`, `source_proxy/jcode/event_schema.py`, `glm-review/TOOL_DIALECT_NORMALIZATION_SCHEMA.json` |
| Permitted implementation paths | `source_proxy/jcode/tool_dialect_normalizer.py` (new), `source_proxy/tests/test_tool_dialect_normalizer.py` (new), `source_proxy/tests/fixtures/tool_dialect/**` (new deterministic fixtures: native, bare JSON, fenced JSON, malformed, multi-call) |
| Forbidden paths | `benchmarks/**`, `qualification_fixture/**`, `fixture_proxy/**`, production routing, daily-runtime worktrees |
| Interfaces and schemas | canonical internal schema = `TOOL_DIALECT_NORMALIZATION_SCHEMA.json` (`{tool, arguments}`); accepted textual forms: `{tool, arguments}` and historically-observed `{name, arguments}` |
| Native input support | tool name; call ID; JSON arguments; streamed argument fragments; multiple calls when allowed |
| Textual input | strict deterministic JSON only (the two accepted envelopes above); normalize both to one internal schema |
| Reject | prose with embedded JSON; ambiguous multiple objects; unknown tool; invalid arguments; executable code extraction; shell strings; markdown examples; malformed JSON; unapproved paths |
| Implementation requirements | parser precedence native → strict textual; one call per normalization pass (ordered); reject + bounded recovery feedback (never silent acceptance); evidence per parse decision |
| Test requirements | normalizer unit tests on all fixture classes; reject-case tests; precedence tests; evidence-field tests |
| Controlled failures required | (covered by Reject list above) |
| Required evidence | raw model output hash; parser selected; normalized tool request; validation result; rejection reason; authorization result |
| Acceptance criteria | native + both accepted textual envelopes normalize to the canonical schema; every reject case is rejected with a recorded reason; parser precedence deterministic |
| Evidence artifacts | fixture matrix; per-class parse receipts; reject-case receipts |
| Stop conditions | ambiguous Qwen output cannot be deterministically bounded; canonical schema conflicts with amendment |
| Commit policy | one goal-scoped commit `feat(c2j-9tc): tool-dialect normalizer`; explicit paths only |
| Push policy | push to the audit branch; no merge, no force-push |
| Next authorized goal | 2-J.9T-D |

### Goal 4/4 — Gate 2-J.9T-D — Observation Reinjection and Bounded Agent Loop

| Field | Value |
| --- | --- |
| Goal ID | 2-J.9T-D |
| Gate | 2-J.9T-D |
| Objective | Implement the complete bounded loop that reinjects observations; fix the proven Lane-C exit defect |
| User-visible outcome | A bounded loop that, after a productive tool call, returns the observation to the model and continues until final answer / verified completion / cancellation / timeout / budget stop |
| Dependencies | 2-J.9T-C |
| Source files to inspect (read-only guidance) | `glm-review/AGENT_LOOP_CONTRACT.md`, `source_proxy/jcode/supervision.py`, `source_proxy/jcode/pipeline_diagnosis.py` (Lane-C `recommended_checks`/`_run_or_skip_checks` exit logic) |
| Permitted implementation paths | `source_proxy/jcode/bounded_agent_loop.py` (new), `source_proxy/tests/test_bounded_agent_loop.py` (new), `source_proxy/tests/fixtures/agent_loop/**` (new fake-model/fake-tool fixtures) |
| Forbidden paths | `benchmarks/**`, `qualification_fixture/**`, `fixture_proxy/**`, production routing, daily-runtime worktrees |
| Interfaces and schemas | loop = model turn → normalize tool request → authorize tool → execute tool → record observation → inject observation under correct role/name → next model turn → repeat until completion or budget stop |
| Implementation requirements | preserve prior messages; return tool results to the model; continue after successful ReadFile (the Lane-C fix); bounded multiple tool turns (≤3); stop only on final answer / verified completion / cancellation / timeout / budget exhaustion; record every turn and tool call; truthful tool errors; preserve task and context unchanged |
| Recovery rule | when the model asks for files already available: do NOT terminate; return standardized reminder; list exact available tool names; list exact available files; preserve task/context; permit ONE recovery turn; fail truthfully if model still refuses tools; do NOT reveal the answer |
| Test requirements | fake-model/fake-tool fixtures FIRST (no real models in Batch 1); reinjection trace tests; recovery tests; budget tests |
| Controlled failures required | first tool succeeds then loop exits early; observation not reinjected; wrong role; wrong tool name; duplicate call; tool error; malformed tool output; recovery reminder ignored; turn budget exhausted; tool budget exhausted; timeout; cancellation; missing final response; incomplete evidence |
| Acceptance criteria | after a productive read the observation is reinjected and the model gets another turn; ≤3 turns; every turn/tool recorded; all controlled failures fail truthfully; recovery rule implemented |
| Evidence artifacts | reinjection traces; recovery-behavior traces; per-controlled-failure receipts |
| Stop conditions | loop cannot reinject without a real model (defer real-model proof to 2-J.9T-F/G); amendment contract conflict |
| Commit policy | one goal-scoped commit `feat(c2j-9td): bounded agent loop with observation reinjection`; explicit paths only |
| Push policy | push to the audit branch; no merge, no force-push |
| Next authorized action | STOP. Produce `GLM_REVIEW_PACKET_GATE_2J_9T_A_TO_D.md` (+json). Do NOT begin Batch 2. |

### Batch 1 global acceptance

Passes only when all four readiness outcomes exist: `PACKET_READY`,
`BRIDGE_READY`, `TOOL_DIALECT_READY`, `AGENT_LOOP_READY`. After Goal 4: stop,
produce the GLM review packet, do not begin Batch 2, do not run real models,
do not start any comparison campaign.

---

## BATCH 2 — Validation, profiles, and harness readiness (planned, NOT authorized yet)

Same visible-board and per-goal format. Real model requests are bounded per goal
under a SEPARATE operator authorization. Terra High must NOT start Batch 2 until
the Batch-1 GLM review accepts and the operator authorizes Batch 2.

- **Goal 1/4 — 2-J.9T-E** Focused-Test Tool and Evaluator Alignment (qualification fixture only)
- **Goal 2/4 — 2-J.9T-F** Qwen 7B and Qwen 14B Compatibility Profiles (small real-model diagnostics)
- **Goal 3/4 — 2-J.9T-G** Baseline Harness Qualification (minimal + corrected packets)
- **Goal 4/4 — 2-J.9T-H** JCode Harness Qualification (minimal + corrected packets)

Then stop for independent GLM review.

### FINAL REVIEW — Gate 2-J.9T-I — Independent Readiness Decision

No real model requests; no automatic 20-task or 80-run start. Decision:
`READY_FOR_BOUNDED_COMPARISON_REVIEW` only if every readiness outcome passes.

---

## Required Batch-1 GLM review packet

Terra High must create after Goal 4:
`GLM_REVIEW_PACKET_GATE_2J_9T_A_TO_D.md` (+ `glm_review_packet_gate_2j_9t_a_to_d.json`).

Include: authorization ID/hash; starting and final HEAD; four gate commits;
files changed by goal; packet schema; packet quality measurements; bridge
before/after examples; tool normalization fixtures; observation reinjection
traces; recovery behavior; test progression; controlled failures; benchmark
integrity; daily-runtime integrity; production-default integrity; unresolved risks.

Scorecard:
`2-J.9T-A — Packet: PASS/PARTIAL/FAIL` · `2-J.9T-B — Bridge` · `2-J.9T-C — Tool dialect` · `2-J.9T-D — Agent loop`.

---

## Hard boundaries (all batches)

- No real model requests in Batch 1 (0).
- No benchmark access. No daily-runtime mutation. No production-default change.
- No Campaign 4 advancement. No 2-J.9J/9K, 20-task, or 80-run start.
- Explicit-path staging only; `git add -A` prohibited. No merge, no force-push.
- Terra High must stop and request authorization for: model/provider expansion;
  new write scope; network expansion; containment weakening; benchmark access;
  campaign advancement; missing evidence; scope ambiguity.
