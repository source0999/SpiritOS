# Stage 4R7 Preflight

- current HEAD: `7d4f3054f877e13c02572574d5dc0f5f101f49b4`
- staged files count: 0
- raw evidence writable: yes
- scope confirmation: Stage 4R7 only; patch `_stage4r_runner.py` packet model-lane escalation and rerun A2/A5/A9 only; no Set B/C, Stage 5, Plan 4, push, media/Jellyfin mutation, route replacement, or new engine.

## Current A2/A5/A9 Blockers

- A2: final_status=PASS decision_packet_validated=True source_count=6 blockers=
- A5: final_status=PASS decision_packet_validated=True source_count=6 blockers=
- A9: final_status=PASS decision_packet_validated=True source_count=6 blockers=

## Configured Model/Provider Lanes

- env availability: {"ANTHROPIC_API_KEY": "unset", "DEEPSEEK_API_KEY": "unset", "LITELLM_API_KEY": "unset", "OPENAI_API_KEY": "unset", "PLAN3_STAGE4R_MODEL": "unset", "PLAN3_STAGE4R_PACKET_MODEL": "unset", "PLAN3_STAGE4R_PACKET_PROVIDER": "unset"}
- available lanes: [{"lane_name": "ollama_qwen2.5-coder_7b", "model": "qwen2.5-coder:7b", "provider_type": "ollama", "reason": "structured_packet_author_primary_local_coder"}, {"lane_name": "ollama_hermes4_latest", "model": "hermes4:latest", "provider_type": "ollama", "reason": "stronger_existing_local_ollama"}, {"lane_name": "ollama_gemma3n_e4b", "model": "gemma3n:e4b", "provider_type": "ollama", "reason": "current_default_local_model"}]
- unavailable lanes: [{"lane_name": "openai", "model": "gpt-4o-mini", "provider_type": "openai", "reason": "OPENAI_API_KEY_unset_or_model_missing"}, {"lane_name": "anthropic", "model": "claude-3-5-sonnet-latest", "provider_type": "anthropic", "reason": "ANTHROPIC_API_KEY_unset_or_model_missing"}, {"lane_name": "deepseek", "model": "deepseek-chat", "provider_type": "deepseek", "reason": "DEEPSEEK_API_KEY_unset_or_model_missing"}, {"lane_name": "litellm", "model": "", "provider_type": "litellm", "reason": "LITELLM_API_KEY_unset_or_model_missing"}]
- Ollama available models: gemma3n:e4b, hermes4:latest, hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M, hermes3:8b-abliterated, mannix/llama3-8b-ablitered-v3:latest, qwen2.5-coder:7b, llama3.1:8b, llama3:latest

## Dirty Tree Note

The worktree has pre-existing unrelated SpiritFlix/media/handoff changes. This runner will not touch unrelated files.
