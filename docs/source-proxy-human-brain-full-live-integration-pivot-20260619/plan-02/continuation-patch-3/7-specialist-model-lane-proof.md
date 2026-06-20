# Specialist Model Lane Proof

Live specialist invocation:

- Status: `INTEGRATED_LIVE`
- Task: `task_1efd570e1a6e`
- Consumer: `cartographer_specialist_packet_consumer`
- Consumer event: `consumer_896ce3ad294b44f3`
- Specialist packet hash: `949348eac2553d6fcbfe54b1fadd12d99360009fbaa9c44fa9dc31aeae2e6d2a`

Ollama inventory:

- Status: `used`
- Gemma model present: `gemma3n:e4b`
- Hermes model present: `hermes4:latest`

Gemma:

- Status: `used`
- Reason: `local_ollama_model_json_schema_valid`
- Model: `gemma3n:e4b`
- Latency: `98887ms`
- Provider errors: `[]`

Hermes:

- Status: `used`
- Reason: `local_ollama_model_json_schema_valid`
- Model: `hermes4:latest`
- Latency: `123133ms`
- Provider errors: `[]`

Route truth:

- `local_ollama_only=true`
- `cloud_provider_used=false`
- `fallback_to_qwen_attempted=false`
- `qwen_pre_coder_reasoning_used=false`
- `qwen_coder_activated=false`

Implementation hardening:

- Local model timeout default raised to `180` seconds for cold local model loads.
- FIP-3 JSON token budget raised to `512` so schema JSON is not truncated mid-string.
- Ollama `thinking` is accepted when Hermes returns JSON there and leaves `response` empty.

The verifier remains advisory and returns `UNVERIFIED`; it is not used to claim product PASS.
