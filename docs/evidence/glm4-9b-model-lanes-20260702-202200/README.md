# GLM-4-9B Source Proxy Model-Lane Benchmark

Generated: 2026-07-03T02:40:01Z
Benchmark version: `glm4-9b-model-lane-benchmark-v0.1`

## Scope

This evidence folder compares GLM-4-9B Q5_K_M against current local Source Proxy model lanes (Qwen 7B/14B, Hermes, Gemma, Ornith). It does not promote GLM, change default routing, touch SpiritFlix/Jellyfin/media paths, or use cloud models for scoring.

## Models Tested

- Qwen 2.5 Coder 7B: `qwen2.5-coder:7b`
- Qwen 2.5 Coder 14B: `qwen2.5-coder:14b`
- Ornith 1.0 9B Q4: `hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M`
- GLM-4-9B Q5: `hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF:Q5_K_M`
- Hermes 4: `hermes4:latest`
- Hermes 4 14B Q4: `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`
- Gemma 3n E4B: `gemma3n:e4b`

## Files

- `results.jsonl`: per-call structured results with bounded raw excerpts and sample paths.
- `summary.json`: aggregate scores, inventory, route status, and recommendation metadata.
- `scorecard.md`: role/model score table.
- `recommendation-matrix.md`: routing recommendation matrix.
- `samples/`: bounded raw model samples, truncated when needed.
- `model-inventory.json`: live Ollama model inventory from the benchmark host.
- `ollama-route-status.json`: Source Proxy route registry/status snapshot when importable.
- `command-log.md`: commands and verification notes.

## Recommendation

Measured results, interpretation, recommendation, and human approval are separated in `summary.json` and `recommendation-matrix.md`. No automatic replacement is recommended by the harness itself.

- coder_patch_author: NEEDS_MORE_TESTS (GLM-4-9B collected 9 hard blocker(s); do not promote from this run.)
- critique_risk_verifier: ADD_AS_SECONDARY (GLM-4-9B matched or narrowly beat the current role baseline without hard blockers; secondary-only approval is the safer recommendation.)
- intent_spec_extraction: NEEDS_MORE_TESTS (GLM-4-9B collected 11 hard blocker(s); do not promote from this run.)
- operator_closeout: ADD_AS_SECONDARY (GLM-4-9B matched or narrowly beat the current role baseline without hard blockers; secondary-only approval is the safer recommendation.)
- research_query_formulation: NEEDS_MORE_TESTS (GLM-4-9B collected 10 hard blocker(s); do not promote from this run.)
- visual_media_roles: DO_NOT_USE_FOR_ROLE (GLM-4-9B inventory proves a text-only local model; no live multimodal GLM route was found.)
- workflow_organizer: ADD_AS_SECONDARY (GLM-4-9B matched or narrowly beat the current role baseline without hard blockers; secondary-only approval is the safer recommendation.)
