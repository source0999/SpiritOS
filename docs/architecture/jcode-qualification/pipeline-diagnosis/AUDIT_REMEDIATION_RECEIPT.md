# Audit Remediation Receipt

Receipt type: `AUDIT_REMEDIATION_RECEIPT`

Remediation ID: `C2J-GLOBAL-CORRECTION-01`

Authorization: `OPERATOR_AUTHORIZATION__C2J_PIPELINE_DIAGNOSIS_20260731_V1`, bound to operator prompt SHA-256 `f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb`.

## Selected Global Correction

Enable the isolated diagnostic bridge's lossless OpenAI-chat-to-Ollama-chat compatibility profile with `--bridge-mode tool_preserving`.

The profile preserves ordered roles and native tool schemas, sends the request to Ollama `/api/chat`, maps tool-result messages to tool names, and reconstructs assistant content or native tool calls as OpenAI-compatible SSE. This is one semantic correction: preserve the chat/tool protocol across the bridge boundary.

The legacy mode remains the default. No production path, daily runtime, frozen benchmark, model, task, prompt, fixture, JCode binary, authority, network policy, or mutation boundary changes.

## Causal Basis

Every pre-correction JCode D/F receipt proves that the OpenAI request contained roles and tools while the Ollama `/api/generate` request contained neither. Both pinned models pass direct grounding, and both formulate the write action in a text tool dialect, so raw incapability does not explain the first system failure.

The correction targets `TOOL_SCHEMA_DROPPED`, `PROVIDER_ROLE_TRANSLATION_FAILURE`, and `BRIDGE_REQUEST_TRANSFORMATION_FAILURE`. It does not attempt to fix the independently proven baseline-loop reinjection defect, full-packet pressure, 14B timeout behavior, JCode instruction contamination, or missing focused-test tool.

## Confirmation

The four confirmation cells hold all non-bridge variables constant: Task R and Task W through JCode minimal Lane D for both exact models. They may consume at most 12 additional requests, leaving the total below the operator limit of 36.

Improvement means provider-visible roles/tools are preserved and grounded or tool-executing behavior appears. A write that passes the independent focused test but cannot invoke that test through JCode is evidence of improvement, not complete tool-task qualification.
