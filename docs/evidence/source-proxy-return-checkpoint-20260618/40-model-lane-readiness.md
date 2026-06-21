# Model And Lane Readiness

Generated from `raw/40-model-inventory.txt`, `raw/41-lane-grep.txt`, and `raw/60-no-code-probes.txt`.

## Ollama inventory

Installed local models include:

- `qwen2.5-coder:7b`
- `gemma3n:e4b`
- `hermes4:latest`
- `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`
- `hermes3:8b-abliterated`
- `llama3.1:8b`
- `llama3:latest`

No model was loaded in `ollama ps` at capture time. Model storage resolves to `/mnt/spirit-8tb/ollama-models`.

## Source Proxy model status

`/v1/models` reports:

- `local`: enabled, `ollama_chat/hermes4:latest`, probe OK, model available.
- `coder`: enabled, `ollama_chat/qwen2.5-coder:7b`, probe OK, model available.
- `classifier`: disabled, `ollama_model_missing:phi4-mini:latest`.
- `openai`, `anthropic`, `deepseek`: configured/enabled but not called in this checkpoint.

## Lane classifications

| Lane | Status | Basis |
| --- | --- | --- |
| Qwen coder lane | `PARTIAL` | Model installed and `/v1/models` says coder enabled/probe OK; no fresh coder task was run. |
| Gemma intent/spec lane | `PARTIAL` | Gemma model installed; prior evidence shows timeout/degraded behavior under contention; no fresh lane execution. |
| Hermes critique/risk lane | `PARTIAL` | Hermes models installed; prior evidence shows occasional non-gating failures; no fresh critique run. |
| Browser verifier | `PARTIAL` | Prior Claude audit says no real browser authority existed for UI rows; later Level 5R2 claims browser evidence passed under harnessed conditions. No fresh browser run was allowed. |
| Research/search lanes | `PARTIAL` | Source files and routes exist; prior Level 5R2 evidence shows SearXNG can be used, but no fresh search/provider call was run here. |
| Obsidian/context lanes | `PARTIAL` | `/v1/self/status` reports Obsidian configured but not scanned/used; context endpoints exist. |
| Cartographer routing ownership | `PREVIEW` | `/v1/cartographer/status` is observing/read-only with write actions disabled and approval token missing. |

No lane is marked `READY` solely from installed models or old success evidence.
