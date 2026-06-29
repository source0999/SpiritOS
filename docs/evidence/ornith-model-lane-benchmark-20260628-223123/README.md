# Ornith 1.0 9B Source Proxy Model-Lane Benchmark

Generated: 2026-06-29T03:38:42Z
Benchmark version: `ornith-model-lane-benchmark-v0.1`

## Scope

This evidence folder compares Ornith 1.0 9B Q4 against current local Source Proxy model lanes. It does not promote Ornith, change default routing, touch SpiritFlix/Jellyfin/media paths, or use cloud models for scoring.

## Models Tested

- Qwen 2.5 Coder 7B: `qwen2.5-coder:7b`
- Ornith 1.0 9B Q4: `hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M`
- Hermes 4: `hermes4:latest`
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

- coder_patch_author: NEEDS_MORE_TESTS (Ornith collected 12 hard blocker(s); do not promote from this run.)
- critique_risk_verifier: NEEDS_MORE_TESTS (Ornith collected 7 hard blocker(s); do not promote from this run.)
- intent_spec_extraction: ADD_AS_SECONDARY (Ornith matched or narrowly beat the current role baseline without hard blockers; secondary-only approval is the safer recommendation.)
- operator_closeout: ADD_AS_SECONDARY (Ornith matched or narrowly beat the current role baseline without hard blockers; secondary-only approval is the safer recommendation.)
- research_query_formulation: ADD_AS_SECONDARY (No dedicated current model baseline exists; use secondary-only if Britton approves.)
- visual_media_roles: DO_NOT_USE_FOR_ROLE (Ornith inventory/model registry proves a text-only local model; no live multimodal Ornith route was found.)
- workflow_organizer: NEEDS_MORE_TESTS (Ornith collected 30 hard blocker(s); do not promote from this run.)
