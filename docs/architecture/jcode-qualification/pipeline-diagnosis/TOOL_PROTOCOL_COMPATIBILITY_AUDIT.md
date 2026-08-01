# Tool Protocol Compatibility Audit

## Decision

The current tool protocol is not qualified for either selected Qwen model.
Both models understand that a read is required, but repeatedly express the
operation as assistant text JSON rather than Ollama/OpenAI native
`tool_calls`. The direct minimal harness and JCode only parse native calls, so
no tool executes. This is compatibility failure, not proof of raw coding
incapability.

## End-to-End Transformation

| Boundary | Observed contract | Result |
| --- | --- | --- |
| Minimal Proxy harness to Ollama | `read_file`, `write_file`, `apply_patch`, `run_test` as OpenAI function schemas | Schemas reach `/api/chat` unchanged. |
| Qwen response in Lane B | Assistant `content` containing bare JSON read requests | No native `message.tool_calls`; parser reports zero calls. |
| JCode internal request | OpenAI `/v1/chat/completions`, ordered roles, `tool_choice: auto`, JCode `read`/`write`/`apply_patch` schemas | Proven exact by capture-only preflight. |
| Legacy compatibility bridge | Flattens message content to one prompt and calls Ollama `/api/generate` | Roles, tools, tool names, required fields, and `tool_choice` are dropped. |
| Corrected diagnostic bridge | Preserves messages and tools through Ollama `/api/chat`; reconstructs OpenAI SSE | Structural transformation passes. |
| Qwen response after correction | Three of four cells formulate a fenced text JSON `read`; one 7B cell promises to read | Ollama returns assistant content, not native calls. |
| JCode response parser | Expects streamed OpenAI `tool_calls` events | Text JSON is emitted as text; zero JCode tool events. |
| Dispatcher/result reinjection | Only reached after a parsed native call | Not reached in B/D/F or confirmation cells. |

Lane B is the clean counterfactual: tools arrive unchanged at Ollama, yet 7B
and 14B use text JSON for Task R and Task W. This independently proves
`MODEL_TOOL_DIALECT_INCOMPATIBILITY` plus `TOOL_CALL_PARSE_FAILURE` before
JCode is involved.

Lane C proves a separate loop defect. Both models emitted valid fenced Source
Proxy `ReadFile` actions. `parse_model_actions` accepted them and the executor
successfully read one file. Because `recommended_checks` was empty,
`_run_or_skip_checks` returned `completed`; `run_bounded_agent_loop` broke
without another model call. The action observation therefore never reentered
the model. Classifications: `AGENT_LOOP_RECOVERY_FAILURE` and
`TOOL_RESULT_REINJECTION_FAILURE`.

## Schema Completeness

Task W requires reading source and test, editing one file, and running one
focused test. JCode exposes `apply_patch`, `read`, and `write`, but no bounded
focused-test tool. Its command policy is `no command tool`. Even perfect native
tool calling could not satisfy the sealed Task W contract. Classification:
`TOOL_SCHEMA_TRANSFORMED_WITH_LOSS` at the executor capability boundary.

Paths were not the failure: every diagnostic receipt reports the same declared
files under the mounted `/workspace`, with path consistency true. No tool
authorization rejection occurred, so `PACKET_PATH_MISMATCH` and
`TOOL_AUTHORIZATION_REJECTION_NOT_REINJECTED` are not supported causes.

## Compatibility Profiles

### Qwen 7B

- Direct inline capability: Task R pass; Task W pass.
- Native minimal tools: not qualified; emits one or more bare JSON calls in
  assistant content.
- Corrected JCode profile: preserves tools, but output remains a promise or
  fenced text `read`; no native call.
- Required parser: bounded bare/fenced JSON text-call recovery, exact allowed
  tool-name and schema validation, path authorization before execution, and an
  unchanged observation-reinjection turn.
- Current decision: `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`, not read-only by raw
  capability.

### Qwen 14B

- Direct inline capability: Task R pass; Task W solution is semantically
  correct, but the restrictive AST evaluator rejects its import/assignment.
- Native minimal tools: not qualified; emits text JSON reads.
- Corrected JCode profile: emits fenced text `read` calls for both tasks; no
  native call. Latency is materially higher and multiple legacy/full cells hit
  the 300-second boundary.
- Required parser/recovery: same as 7B, plus a qualified latency/context budget.
- Current decision: `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`; raw Task W
  capability remains qualified pending evaluator alignment.

## Required Correction Set

The tested global bridge correction is necessary but insufficient. Campaign
readiness also requires a model profile that accepts the exact Qwen text-call
dialect, reconstructs one call at a time, returns tool results under the role
JCode expects, preserves prior messages, and truthfully stops within three
turns. It also requires a bounded test tool and regression coverage for native,
bare JSON, fenced JSON, malformed, multiple-call, denied-path, tool-error, and
already-present-file recovery cases.
