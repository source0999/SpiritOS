# Model-Visible Packet Schema

Status: diagnostic-only, immutable per run

Schema ID: `source-proxy.model-visible-packet/v1`

Every controlled run stores `exact_model_visible_packet.json` beside the raw provider response and request bytes. The receipt binds the run, task, lane, exact local model digest, JCode binary when applicable, executor/bridge/context-builder versions, ordered messages or prompts, exact tools, backend request bodies, request hashes, and role order.

## Evidence Boundary

- `messages_or_prompts` records the executor-facing input.
- `backend_requests` records what was actually serialized to Ollama after all transformations.
- Each backend request also appears with exact UTF-8 request bytes in `raw_model_response.json`.
- JCode lanes additionally record the redacted OpenAI-compatible request received by the diagnostic bridge and every bridge transformation.
- Raw authorization headers are never retained.
- Context manifests bind ordered full file contents, per-file hashes, exclusions, truncation state, mounted-path policy, and total bytes.
- Response evidence includes the full non-streamed Ollama body; JCode evidence additionally preserves its NDJSON stream, parser output, tool ledger, diff, and independent evaluation.

The JSON Schema is in `model_visible_packet_schema.json`. Fields may be expanded in receipts, but existing fields cannot be silently reinterpreted within version `v1`.
