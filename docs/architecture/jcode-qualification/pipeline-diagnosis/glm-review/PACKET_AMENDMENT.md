# PACKET_AMENDMENT.md

Canonical controlling amendment for Campaign 2-J human-to-coder pipeline
qualification. This is the implementation-ready human-readable specification;
machine-readable schemas and receipts support it but do not override it.

Status: `PROPOSED_FOR_OPERATOR_ADOPTION` (binding on the audit branch only;
not merged into the canonical Campaign 2-J branch).

---

## A. Amendment identity

| Field | Value |
| --- | --- |
| Amendment ID | `CAMPAIGN_2J_PACKET_TOOL_LOOP_COMPATIBILITY_AMENDMENT_V1` |
| Campaign | Campaign 2-J — JCode/tool-mediated coder qualification |
| Parent campaign receipt | `OPERATOR_AUTHORIZATION__C2J_PIPELINE_DIAGNOSIS_20260731_V1` |
| Parent operator prompt SHA-256 | `f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb` (independently re-hashed during this review) |
| Audit branch | `codex/source-proxy-jcode-pipeline-diagnosis-20260731` |
| Audit HEAD | `115f4f3343f1aede103e642d6853f2677d2d4a48` (verified; 0/0 ahead-behind vs upstream) |
| Starting HEAD | `07151b44cb886ac4d8c3668e947e81825d01bd50` |
| Authorization commit | `c42d62f189542e69112e600c5e0bdef05e2705ac` |
| Sol audit prompt hash | `f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb` |
| GLM review authorization hash | (none — this is the first independent GLM review; its authority derives from the same operator authorization that authorized the audit, exercised as an independent review per the operator review instructions) |
| Gate | `Gate 2-J.9T — Model-Ready Packet, Tool Protocol, and Agent-Loop Qualification` |
| Effective status | `PROPOSED`; supersedes nothing on the canonical branch; retains all accepted safety gates |
| Superseded artifacts | None. Sol's `CAMPAIGN_2J_PACKET_TOOL_COMPATIBILITY_AMENDMENT.md` and `campaign_2j_packet_tool_compatibility_amendment.json` are the precursor drafts this amendment consolidates and corrects; they remain as audit evidence. |
| Implementation owner | Terra High (under a new prospective sub-gate authorization) |
| Review owner | GLM (independent review after each batch) |
| Stop boundary | No Gate 2-J.9T execution, no 2-J.9J/9K, no 20-task, no 80-run, no Campaign 4, no production/default change in this task |

### Naming correction note

Sol's draft used amendment ID `CAMPAIGN_2J_GATE_9T_PACKET_TOOL_COMPATIBILITY_V1`.
This amendment adopts the operator-specified canonical identity
`CAMPAIGN_2J_PACKET_TOOL_LOOP_COMPATIBILITY_AMENDMENT_V1` and gate title
`Gate 2-J.9T — Model-Ready Packet, Tool Protocol, and Agent-Loop Qualification`,
which add the agent-loop dimension Sol's draft title omitted even though the
draft's body covers it. All other Sol thresholds are retained (see section F).

---

## B. Problem statement

The Source Proxy must convert a human request into a concise coder packet,
preserve compatible tools through the bridge, complete the tool-mediated
observation loop, and evaluate behavior correctly. The Sol Ultra audit proved
this contract is broken at multiple independent boundaries:

1. **Models demonstrated useful direct capability.** Both exact Qwen models
   (`qwen2.5-coder:7b`, `qwen2.5-coder:14b`) pass direct read grounding (Task R)
   with full inline context; 7B passes direct write (Task W); 14B returns a
   semantically correct Task W implementation that the diagnostic evaluator
   rejects on AST structure (independently re-verified in this review: the 14B
   `re.sub` solution passes the actual focused test).

2. **The full mediated pipeline failed.** Zero of 24 diagnostic runs completed
   a tool-mediated task end to end. The first controlled failure is a
   tool-dialect/parser mismatch; the first JCode-specific loss is the legacy
   bridge dropping roles and tools.

3. **Current evidence does not support broad model-incapability claims.** The
   same models pass simpler equivalent tasks, so failures are attributed to the
   system, not raw model limits.

4. **Packet, tool, bridge, loop, JCode, and evaluator defects are multi-factor
   causes** (see the contract-break matrix in `SOL_AUDIT_INDEPENDENT_REVIEW.md`).

5. **Expensive campaign execution would measure known defects** rather than
   true model/harness quality. Running the 20-task diagnostics or 80-run
   comparison now would primarily re-measure the broken packet/protocol/loop
   rather than discriminate between models or harnesses.

---

## C. Retained gates

Retained without reopening, each supported by evidence:

- **Batch 1 containment and evidence infrastructure** — Gates 2-J.9B through
  2-J.9E. The diagnostic instrumentation added in this audit reuses that
  evidence scaffold.
- **Runtime and bridge safety findings** — Runtime Gates 2-J.9G-D through
  2-J.9H technical acceptance.
- **Exact model-binding protections** — the live digest checks on all 24
  requests (`dae161e2…f4364`, `9ec8897f…16849`) are reproduced by this review.
- **Direct-provider denial** — JCode had no direct route to Ollama; all
  provider traffic crossed the sealed socketpair relay and diagnostic bridge.
- **Gate 2-J.9I safety-path findings** — containment/safety/no-unauthorized-
  mutation evidence is retained unchanged.
- **Accepted authorization/governance corrections** — the one global correction
  (`C2J-GLOBAL-CORRECTION-01`, tool-preserving chat bridge) is a diagnostic-only
  counterfactual that is retained as evidence; it did not change production.

### Refinement of Gate 2-J.9I's model-quality attribution (not a safety change)

Gate 2-J.9I stated the observed no-tool result established a model quality
failure. This audit proved the legacy bridge did not expose tools to the
provider (`/api/generate` flattened messages and dropped tools), and 9I did not
retain raw response bytes. Therefore 9I's model-attribution wording is
`EVIDENCE_INCOMPLETE` and **must not be used as evidence of model
incapability**. The safety-path acceptance is unchanged.

---

## D. Blocked gates

| Gate / action | Condition required to unblock |
| --- | --- |
| Gate 2-J.9J | All required Gate 2-J.9T readiness outcomes (section P) pass for the selected task classes and exact model/digests. |
| Gate 2-J.9K | An independent reviewer accepts Gate 2-J.9T (sub-gate 2-J.9T-I). |
| 20-task sealed diagnostic execution | Gate 2-J.9T-I acceptance plus operator authorization. |
| 80-run comparison | Independent reviewer accepts Gate 2-J.9T; comparison measures a qualified pipeline, not known defects. |
| Campaign 4 | Gate 2-J.9T accepted and 2-J.9J/9K closed. |
| Production JCode promotion | Corrected bridge + parser + loop + focused-test tool + evaluator pass Gate 2-J.9T; explicit production authorization. |
| Production-default bridge change | Forbidden until Gate 2-J.9T qualification passes; legacy mode stays the default. |

---

## E. Canonical Model-Ready Task Packet

### Identity (packet header)

Every coder execution MUST serialize one packet containing:

- schema version (`source-proxy.model-ready-packet/v1`);
- task ID (immutable, e.g. `PIPE-R-001`);
- run ID; campaign ID;
- prompt hash, acceptance hash, context hash, base commit;
- executor ID, model profile ID, tool profile ID, evaluator profile ID.

### Task-first content (first model-visible section)

The first model-visible section MUST contain:

- concise task (one coding objective);
- desired observable behavior;
- exact acceptance criteria (deterministic focused checks);
- exact writable files;
- exact read-only supporting files;
- exact mounted tool paths;
- exact focused validation command;
- explicit stop condition.

### Context

Include: ordered file manifest; exact relevant source; exact relevant tests;
necessary dependency/interface excerpts; per-file SHA-256 and byte counts;
excluded-path manifest; truncation receipt; **no hidden expectations**;
**no unrelated campaign history**.

### Tools

Include only the tools needed for the task. Minimum set: `read_file`;
`apply_patch` or `write_file`; `focused_test`; optional `list`/`find` where
necessary. Each tool requires: canonical name; exact JSON schema; description;
allowed paths; error contract; result contract; timeout; evidence output.

### Constraints

Network policy (none); write policy (declared files only); prohibited paths;
no Git writes; no commit/push/deploy; bounded tool turns (≤3); bounded retries
(parser/recovery only); no cross-run memory.

### Packet ordering (canonical)

`identity → task + acceptance criteria → writable/read-only paths + tool schemas
→ prohibited actions → identity/hash bindings → critical source/test bytes only`.

Task and acceptance criteria MUST precede background constraints and context.

### Packet quality metrics (measured per run)

task-content byte position; relevant-context ratio; governance-noise count;
critical-file presence; path consistency; duplicate-content ratio; truncation
status; total model-visible tokens; tool-schema tokens; available output budget.

---

## F. Packet readiness gate (PASS/FAIL rules)

A run's packet passes only if ALL hold:

| Rule | Threshold | Justification |
| --- | --- | --- |
| Relevant-context ratio | ≥ 0.40 | Minimal packets measured ~0.455 (R 0.4561, W 0.4554); full packets measured 0.019/0.0164. 0.40 is the observed achievable clean-packet floor and is well above the failing full-packet floor. |
| First critical content position | task + acceptance criteria begin within first 1,024 bytes | Minimal packets place task at byte 26; full packets bury it at ~5,807 (R) / ~6,663 (W). 1,024 bytes reserves the opening for the task contract before any context body. |
| Zero unrelated governance markers | 0 | Minimal packets have 0; full packets have 12. Governance text in a coder execution packet is always noise for a sealed task. |
| Required source/test presence | 100% critical files/bytes | Lane E failure was not missing fixture content; it was burial/timeout. Presence is necessary but not sufficient. |
| Path equality (packet ↔ mount ↔ dispatcher) | 100% | Every diagnostic receipt already reports path consistency true; must be preserved. |
| No critical truncation | 0 critical bytes omitted, or independently-proven noncritical omission with receipt | Production slices at 6,000 chars silently; E7 telemetry showed 4,147→4,096 token pressure. |
| No contradictory instructions | 0 | JCode 2,004-char system prompt says self-modify/commit while sealed task forbids it. |
| No hidden-answer leakage | 0 | Verified: full diagnostic packets contained exact source/test and did not expose answers. |
| Deterministic packet reproduction | byte-identical across recomputation | Anti-cheat and reproducibility. |
| Paired-lane packet identity | identical canonical context bytes across paired lanes | Required for fair comparison. |
| Context/output budget sufficiency | input + 1,024 output + 256 safety ≤ profile context limit | Preserves output room; failures here must not be labeled model incapability. |

**Relevance ratio is necessary but not a sole quality measure.** A packet can
satisfy ≥0.40 while still omitting a critical test or leaking an answer, so the
presence, path, truncation, and leakage rules are independent gates.

---

## G. Tool-dialect normalization

Define ONE canonical internal tool-request schema. Two input dialects:

### Native tool calls

Normalize OpenAI/Ollama-compatible native `tool_calls` events unchanged.

### Textual JSON tool calls

Normalize ONLY when the output deterministically matches a strict accepted
envelope. Accepted textual form (one call):

```json
{
  "tool": "read_file",
  "arguments": {
    "path": "qualification_fixture/source.py"
  }
}
```

Requirements: strict JSON; exactly one allowed tool name; valid argument
schema; no surrounding executable prose unless explicitly allowed; no dynamic
evaluation; no arbitrary command extraction.

Reject ambiguous pseudo-tool text. (Lane B proved the models emit clean
deterministic JSON for declared tools — `{"name": "read_file", "arguments":
{"path": "ledger.py"}}` — so a strict envelope is feasible; Lane C proved
`fenced_json` already recovers Source Proxy `ReadFile` actions.)

Define: parser precedence (native first, then strict textual); duplicate-call
handling (one call per normalization pass, ordered); malformed-call handling
(reject + bounded recovery feedback, never silent acceptance); multi-call
policy (execute one, reinject, next turn); evidence (every parse decision
recorded with parser name + status); model feedback (truthful rejection under
the expected role/tool name).

---

## H. Bridge contract

Require a chat-preserving bridge that retains: system/user/assistant/tool
roles; ordered messages; tool definitions; `tool_choice`; model identity;
generation parameters; streaming tool fragments; tool-result names; usage;
finish reason.

`/api/chat` becomes the **required qualification transport** for tool-mediated
tasks. The legacy `/api/generate` (which flattens messages to one prompt and
drops roles/tools/`tool_choice`) is forbidden for qualification. **Production
defaults remain unchanged until qualification passes** — the corrected profile
is diagnostic-only and not the production default.

Evidence basis: legacy D/F receipts show `tools_reached_provider_unchanged:
false`; corrected s3 receipts show `tools_reached_provider_unchanged: true` in
4/4 cells with role order `system,user,user`.

---

## I. Agent-loop contract

Required bounded loop:

```text
Model turn
→ normalize tool request (native or strict textual)
→ authorize tool (path/command)
→ execute tool
→ record observation
→ inject observation under correct role/name
→ next model turn
→ repeat until completion or budget stop
```

Requirements: observation reinjection; preservation of prior turns; bounded
turn count (≤3); bounded tool calls; truthful tool errors; retry only for
parser/recovery/verification reasons defined before the run; final-answer
handling (valid answer for R; scoped diff + passing focused test for W);
cancellation; timeout; complete evidence; **no exit immediately after the first
tool unless the task is complete**.

### Recovery when the model requests files already available

1. Do NOT terminate immediately (this is the proven Lane C defect: empty
   `recommended_checks` returned `completed` and the loop broke).
2. Return a standardized tool-availability reminder.
3. Include the exact available tool names and file manifest.
4. Preserve the task unchanged.
5. Permit one bounded recovery turn.
6. Record failure if the model still refuses tools.

Do NOT reveal the answer.

---

## J. Focused-test tool

First-class focused validation tool. Requirements: exact sealed command; no
arbitrary shell; controlled CWD; timeout; output cap; exit-code capture;
stdout/stderr capture; no network; independent evidence; tool-result
reinjection. The model may request the tool but may NOT alter its command.

Evidence basis: Task W requires `python -m pytest -q focused_check.py`; JCode
exposes only `apply_patch`/`read`/`write` and its command policy is `no command
tool`. Even perfect native tool calling could not satisfy Task W without this.

---

## K. JCode compatibility profile

Define what must be changed/wrapped for JCode:

- **conflicting system instructions** — seal a project system prompt that
  removes commit/self-development/unavailable-tool/generic-workflow defaults
  (the 2,004-char default says self-modify + commit while the sealed task
  forbids both);
- **project instruction loading** — disable generic AGENTS/project ingestion
  for sealed tasks;
- **default model contamination** — exact model/digest binding carried through;
- **native-only parser** — add the textual-tool adapter (section G);
- **textual-tool adapter** — required;
- **tool-result role mapping** — map to the role/name JCode expects;
- **session/memory disabling** — already proven by fresh HOME/`JCODE_HOME`/
  overlay/session per run;
- **focused-test tool registration** — section J;
- **task-finalization behavior** — require valid final answer/diff+test.

JCode readiness is defined **independently** from model readiness. JCode is
NOT the only permitted harness — the baseline harness is an independent
qualification lane.

---

## L. Model compatibility profiles

Separate profiles for Qwen 7B and Qwen 14B. Each specifies: system prompt;
preferred tool dialect; parser mode; temperature (0 observed); output budget;
context limit; maximum turns (3); recovery prompt; known limitations;
qualified task classes; disqualified task classes. Do NOT encode task-specific
answers.

### Qwen 7B (`dae161e2…f4364`)

Direct baseline: Task R PASS, Task W PASS. Observed dialect: bare/fenced
assistant-text JSON, not native `tool_calls`. Required parser: native + strict
textual recovery for declared tools. Current: `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`.

### Qwen 14B (`9ec8897f…16849`)

Direct baseline: Task R PASS; Task W behaviorally correct (evaluator-aligned
pending). Same text dialect. Required parser: same as 7B + a qualified
latency/context budget (4 cells hit the 300s timeout; a provider timeout MUST
NOT be labeled model incapability). Current: `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`.

---

## M. Evaluator alignment

Define evaluators by observable requirements: focused tests; allowed-path
diff; interface contract; expected behavior; prohibited behavior. Do NOT
reject semantically equivalent code merely because it differs from a reference
implementation. Allow structural requirements only when the task explicitly
requires them.

Outcomes: behavioral pass; structural pass; safety pass; partial pass;
evaluator uncertainty.

Evidence basis: 14B's `re.sub(r'\s+', '-', value.strip()).lower()` is
syntactically valid and semantically correct (this review ran it against the
actual focused test — both assertions PASS), yet the AST evaluator rejected it
for `import`/assignment nodes. That is `VERIFIER_EXPECTATION_MISMATCH`.

---

## N. Diagnostic qualification matrix (minimum rerun after implementation)

| Lane | Configuration | Model coverage |
| --- | --- | --- |
| Direct inline capability | minimal packet, no tools | both Qwen |
| Minimal tools without JCode | baseline harness, minimal packet | both Qwen |
| Baseline harness, minimal packet | full corrected loop | both Qwen |
| JCode, minimal packet | corrected bridge + parser | both Qwen |
| Baseline harness, full corrected packet | full loop | both Qwen |
| JCode, full corrected packet | full loop | both Qwen |

Use both Qwen models where meaningful. Limit requests (budget per new
authorization). Use immutable tasks. Require identical packet bytes across
comparable lanes.

---

## O. Gate 2-J.9T sub-gates (dependency-ordered)

| Sub-gate | Objective | Model/real requests | Stop-for-review items |
| --- | --- | --- | --- |
| 2-J.9T-A | Canonical packet schema + packet-quality validator | none | n/a |
| 2-J.9T-B | Chat-preserving bridge contract | fake backend only | n/a |
| 2-J.9T-C | Native/textual tool normalizer | deterministic fixtures only | n/a |
| 2-J.9T-D | Observation reinjection + bounded agent loop | fake model/tool fixtures first | n/a |
| 2-J.9T-E | Focused-test tool + evaluator alignment | qualification fixture only | n/a |
| 2-J.9T-F | Qwen model compatibility profiles | small real-model diagnostics | n/a |
| 2-J.9T-G | Baseline harness qualification | minimal + corrected packets | n/a |
| 2-J.9T-H | JCode compatibility qualification | minimal + corrected packets | n/a |
| 2-J.9T-I | Independent readiness review | none (no automatic comparison start) | decision gate |

Each sub-gate defines: objective; dependencies; allowed files; forbidden
files; implementation requirements; tests; controlled failures; evidence;
acceptance; stop condition; commit policy; next authorized action.

### Terra High bounded autonomy

Terra High may use bounded autonomy for ordinary implementation defects inside
an already-authorized sub-gate. Terra High MUST stop for: model/provider
expansion; new write scope; network expansion; containment weakening; benchmark
access; campaign advancement; missing evidence; scope ambiguity.

---

## P. Readiness outcomes

`PACKET_READY`, `BRIDGE_READY`, `TOOL_DIALECT_READY`, `AGENT_LOOP_READY`,
`FOCUSED_TEST_TOOL_READY`, `EVALUATOR_READY`, `QWEN_7B_PROFILE_READY`,
`QWEN_14B_PROFILE_READY`, `BASELINE_HARNESS_READY`, `JCODE_HARNESS_READY`,
`MODEL_LIMITED_TO_READ_ONLY`, `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`,
`PIPELINE_NOT_READY`, `READY_FOR_BOUNDED_COMPARISON_REVIEW`.

**No single component may imply the full pipeline is ready.** The 80-run
comparison requires `READY_FOR_BOUNDED_COMPARISON_REVIEW` after 2-J.9T-I.

---

## Q. Advancement rule

- No 20-task run until all required readiness outcomes pass.
- No 80-run comparison until an independent reviewer accepts Gate 2-J.9T.
- No Campaign 4 advancement.
- No automatic unpause.
- No production-default bridge change before qualification.

---

## R. Anti-cheating requirements

Immutable tasks; no expected-answer exposure; no model-specific task rewriting;
no cross-run memory; no prior-output injection; no retry with changed prompt;
identical packet bytes across paired lanes; independent evaluation; preserved
failures; exact request and packet receipts.

---

## S. Terra High implementation workflow

Gate-by-gate handoff (see `TERRA_HIGH_GATE_2J_9T_HANDOFF.md`). Bounded autonomy
per section O. Stop-for list per section O.

---

## T. GLM review boundary

Independent GLM review after bounded sub-gate batches:

- **Batch 1:** 2-J.9T-A through 2-J.9T-D → GLM review
- **Batch 2:** 2-J.9T-E through 2-J.9T-H → GLM review
- **Final:** 2-J.9T-I readiness decision (independent reviewer accepts/blocks)

---

## References

- Precursor audit: `SOL_ULTRA_FINAL_PIPELINE_DIAGNOSIS.md` /
  `sol_ultra_final_pipeline_diagnosis.json`
- Precursor draft amendment: `CAMPAIGN_2J_PACKET_TOOL_COMPATIBILITY_AMENDMENT.md`
  / `campaign_2j_packet_tool_compatibility_amendment.json`
- Independent review: `SOL_AUDIT_INDEPENDENT_REVIEW.md` /
  `sol_audit_independent_review.json`
- Acceptance matrix: `PACKET_READINESS_ACCEPTANCE_MATRIX.md` /
  `packet_readiness_acceptance_matrix.json`
- Schemas: `MODEL_READY_PACKET_SCHEMA.json`,
  `TOOL_DIALECT_NORMALIZATION_SCHEMA.json`
- Contracts/profiles: `AGENT_LOOP_CONTRACT.md`, `JCODE_COMPATIBILITY_PROFILE.md`,
  `QWEN_7B_COMPATIBILITY_PROFILE.md`, `QWEN_14B_COMPATIBILITY_PROFILE.md`,
  `EVALUATOR_ALIGNMENT_CONTRACT.md`
- Handoff: `TERRA_HIGH_GATE_2J_9T_HANDOFF.md`, `COMPACT_HANDOFF_PACKET.md`
