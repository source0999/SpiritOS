# Bridge Transformation Audit

## Legacy Path

JCode emits `POST /v1/chat/completions` with ordered messages, model,
`stream: true`, `tool_choice: auto`, and native OpenAI function schemas. The
capture-only preflight proves these fields leave the pinned binary intact.

The legacy diagnostic bridge and the Gate 2-J.9I
`SealedOllamaInferenceBridge` use Ollama `/api/generate`. They concatenate
message content into one prompt, set fixed generation options, and do not send
roles, tools, function schemas, required fields, or `tool_choice`. The response
is reconstructed as OpenAI SSE assistant content only. A provider-native tool
call cannot survive this representation.

| Field | JCode request | Legacy Ollama request | Classification |
| --- | --- | --- | --- |
| Ordered roles | `system,user,user` | flattened prompt | `PROVIDER_ROLE_TRANSLATION_FAILURE` |
| Tool schemas | present and exact | absent | `TOOL_SCHEMA_DROPPED` |
| Tool names/required fields | present | absent | `TOOL_SCHEMA_TRANSFORMED_WITH_LOSS` |
| `tool_choice` | `auto` | absent | `BRIDGE_REQUEST_TRANSFORMATION_FAILURE` |
| Streamed tool-call deltas | expected by JCode | content-only reconstruction | `TOOL_CALL_PARSE_FAILURE` downstream |

All legacy D/F cells show `tools_reached_provider_unchanged: false` and empty
backend tool lists. This is exact-byte evidence, not a configuration inference.
It invalidates the prior Gate 2-J.9I wording that the model ignored exposed
tools: that receipt did not preserve raw response bytes, and the tools were not
provider-visible after bridge transformation.

## Tested Global Correction

Remediation `C2J-GLOBAL-CORRECTION-01` is a diagnostic-only, lossless
OpenAI-chat-to-Ollama-chat profile:

- preserve message order and roles;
- preserve native tool schemas;
- map tool-result messages to tool names;
- send Ollama `/api/chat` with the exact pinned model;
- reconstruct assistant content or native tool calls as OpenAI-compatible SSE;
- leave the legacy bridge as the default and make no production change.

All four confirmation receipts report `tools_reached_provider_unchanged: true`
and role order `system,user,user`. This consistently corrects the selected
bridge defect for both models and both task classes.

## Residual Failure

No confirmation task passes. Three cells produce a fenced JSON `read` in
assistant content; the remaining 7B read cell promises to read and asks for
more instruction. Ollama reports no native `tool_calls`; JCode records zero tool
events. The correction therefore changes the first failure from bridge loss to
the already observed `MODEL_TOOL_DIALECT_INCOMPATIBILITY` and
`TOOL_CALL_PARSE_FAILURE` boundary.

This is a successful counterfactual for the bridge and a failed end-to-end
qualification. It proves the pipeline is multi-factor: fixing the bridge alone
does not fix parser compatibility, loop reinjection, prompt conflict, missing
test capability, or full-packet quality.

## Production Decision

No bridge change is approved for production. Before any merge, the corrected
profile must be combined with a Qwen text-call parser/recovery profile and a
focused-test tool, then pass Gate 2-J.9T with exact packet receipts. Fallback,
cloud routing, direct JCode-to-Ollama access, and silent model substitution
remain forbidden.
