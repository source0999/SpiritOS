# Stage 4R7 Packet Model-Lane Escalation

## Available lanes
- ollama_qwen2.5-coder_7b provider=ollama model=qwen2.5-coder:7b reason=structured_packet_author_primary_local_coder
- ollama_hermes4_latest provider=ollama model=hermes4:latest reason=stronger_existing_local_ollama
- ollama_gemma3n_e4b provider=ollama model=gemma3n:e4b reason=current_default_local_model
## Unavailable lanes
- openai provider=openai model=gpt-4o-mini reason=OPENAI_API_KEY_unset_or_model_missing
- anthropic provider=anthropic model=claude-3-5-sonnet-latest reason=ANTHROPIC_API_KEY_unset_or_model_missing
- deepseek provider=deepseek model=deepseek-chat reason=DEEPSEEK_API_KEY_unset_or_model_missing
- litellm provider=litellm model= reason=LITELLM_API_KEY_unset_or_model_missing
## Routing
- Lane order is PLAN3_STAGE4R_PACKET_MODEL if set, then existing local hermes4:latest, then the current default local model, then preconfigured API/provider lanes only if credentials already exist.
- This run does not add providers, request keys, install packages, or send unrelated repo dumps.
- Each lane attempt writes prompt/response hashes, response excerpts, parse status, validation status, and validation errors under raw evidence.
## Why this is not cheating
- The model still authors the structured packet from live evidence.
- The runner only validates evidence IDs, parses JSON, records attempts, and renders fields after validation.
- The hardened grader still derives final_status.
## Secrets
- Environment values are recorded only as SET/unset in preflight; API keys are never written to raw evidence.
