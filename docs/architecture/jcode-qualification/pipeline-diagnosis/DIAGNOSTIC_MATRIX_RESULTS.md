# Diagnostic Matrix Results

## Controls

- Tasks: immutable non-benchmark `PIPE-R-001` and `PIPE-W-001`.
- Models: exact `qwen2.5-coder:7b` and `qwen2.5-coder:14b` digests.
- Runs: 24. Requests: 24 of 36. Maximum observed turns: 1 of 3.
- Frozen benchmark runs: 0. Applied production mutations: 0. Daily-runtime
  mutations: 0. Diagnostic fixture mutations persisted after runs: 0.
- Timeouts: six (`08`, `09`, `10`, `12`, `18`, `20`).
- Evidence: 23 byte-complete request captures and one explicit
  `EVIDENCE_INCOMPLETE` request-body gap for `s1-r-e-7b`; no retry or
  reconstruction was performed.

## Task R - Read/Grounding

| Lane | 7B | 14B | Causal reading |
| --- | --- | --- | --- |
| A direct inline | PASS, 58.935s | PASS, 125.789s | Both models can ground the exact function, schema, and test with complete inline context. |
| B direct minimal tools | FAIL, 60.657s | FAIL, 118.327s | Both emit `read_file` as assistant text JSON; Ollama returns no native tool call. |
| C baseline loop/minimal | FAIL, 94.211s | FAIL, 191.849s | Parser accepts one `ReadFile` and executor reads successfully; loop exits before observation reinjection/final answer. |
| D JCode/minimal legacy | FAIL, 123.733s | TIMEOUT, 302.559s | Bridge drops roles/tools; 7B returns generic acknowledgement, 14B hits backend timeout. |
| E baseline/full Proxy | TIMEOUT, incomplete exact request | TIMEOUT, 300.334s | Full packet expands to 12,579 bytes, 1.9% relevant lower bound; E7 has the sole capture gap. |
| F JCode/full legacy | FAIL, 114.079s | TIMEOUT, 304.609s | Same first-turn bridge loss as D; mounted full packet cannot be read. |

## Task W - Tool/Write

| Lane | 7B | 14B | Causal reading |
| --- | --- | --- | --- |
| A direct inline | PASS, 53.634s | Evaluator FAIL, 114.139s | 7B returns a passing complete file. 14B returns semantically correct `re.sub` code; restricted AST evaluator rejects import/assignment. No candidate is applied. |
| B direct minimal tools | FAIL, 70.076s | FAIL, 131.714s | Both emit assistant-text JSON reads; zero native calls, edits, or tests. |
| D JCode/minimal legacy | FAIL, 163.150s | TIMEOUT, 309.712s | Roles/tools dropped; no mutation. |
| F JCode/full legacy | FAIL, 127.830s | TIMEOUT, 312.568s | Roles/tools dropped; no mutation. |

Task W Lane A 14B is audit-classified
`SEMANTIC_PATCH_CAPABLE_EVALUATOR_REJECTED`, rooted in
`VERIFIER_EXPECTATION_MISMATCH`. It is not evidence that 14B lacks this coding
capability.

## Global-Correction Confirmation

The only correction was the tool-preserving chat bridge. Four minimal JCode D
cells held model, task, fixtures, JCode binary, prompts, and containment fixed.

| Cell | Structural bridge result | Task result |
| --- | --- | --- |
| R 7B | Roles/tools preserved | FAIL: promises to read and requests further instruction; zero tool events. |
| R 14B | Roles/tools preserved | FAIL: fenced text JSON `read`; zero tool events. |
| W 7B | Roles/tools preserved | FAIL: fenced text JSON `read`; zero tool events. |
| W 14B | Roles/tools preserved | FAIL: fenced text JSON `read`; zero tool events. |

The correction consistently removes `TOOL_SCHEMA_DROPPED` and
`PROVIDER_ROLE_TRANSLATION_FAILURE` at the bridge. It does not remove
`MODEL_TOOL_DIALECT_INCOMPATIBILITY`, `TOOL_CALL_PARSE_FAILURE`, missing test
capability, or JCode prompt conflict. End-to-end passes remain zero in JCode.

## Matrix Decision

Both models pass direct grounding. 7B passes direct write capability. 14B
produces a behaviorally correct direct write candidate that the diagnostic
evaluator rejects structurally. Neither model is qualified for the current
native tool dialect. The baseline loop and JCode path each add independent
system failures. The full Proxy packet adds severe context pressure. The causal
verdict is `MULTI_FACTOR_FAILURE`, not model incapability.
