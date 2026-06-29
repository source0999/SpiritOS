# Ornith 1.0 9B Local Challenger Install

Ornith 1.0 9B is installed on the Dell SpiritOS host as a local Ollama challenger model for later benchmark comparison. It is not the default SpiritOS coder model.

## Installed Quant

```text
hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M
```

Q4_K_M was chosen first because it is the smallest practical GGUF quant for proving the 9B model on the RTX 3060 12GB without downloading the full bf16 checkpoint or a larger Q5/Q8 candidate. The first smoke used about 6.55GB VRAM during a tiny prompt, leaving headroom on the 12GB card.

## Storage

Ollama model storage resolves to the 8TB drive:

```text
/usr/share/ollama/.ollama -> /mnt/spirit-8tb/ollama-models
```

The model blobs and manifests live below:

```text
/mnt/spirit-8tb/ollama-models/models/
```

Do not move or delete existing Qwen, Hermes, Gemma, or Llama models as part of Ornith benchmarking. If storage cleanup is ever needed, first prove `ollama list` still sees replacement copies from the 8TB path.

## Local Invocation

Use Ollama directly:

```bash
ollama run hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M
```

Or use the local Ollama API:

```bash
curl http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  --data '{"model":"hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M","prompt":"Reply with exactly: Ornith smoke OK","stream":false,"options":{"num_predict":16,"temperature":0}}'
```

## SpiritOS Routing

SpiritOS refers to this model as the metadata-only lane:

```text
ornith_coder_challenger
```

The configured model ID is:

```text
SOURCE_PROXY_ORNITH_CHALLENGER_OLLAMA_MODEL=hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M
```

Qwen remains the primary coder lane:

```text
SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b
primary_coder_lane=qwen_local_coder
```

## Challenger-Only Rule

Ornith is a candidate for coder/scaffold/workflow organization. It is not proven better inside SpiritOS until a benchmark run compares it against Qwen with identical prompts, identical scoring, browser or diff evidence where relevant, and explicit failure labels.

The lane disallows:

- silent replacement for `qwen_local_coder`
- default production routing
- superiority claims before benchmark evidence
- product PASS declarations without behavior evidence

## Benchmark Pointer

The first full local model-lane benchmark is summarized in:

```text
docs/local-models/ornith-1-9b-benchmark.md
```

Evidence root:

```text
docs/evidence/ornith-model-lane-benchmark-20260628-223123/
```

Result: no default routing change. Ornith remains challenger-only unless Britton explicitly approves a secondary lane after reviewing the evidence.

## Rollback

Rollback routing without deleting the model:

1. Remove or ignore `SOURCE_PROXY_ORNITH_CHALLENGER_OLLAMA_MODEL`.
2. Revert the `ornith_coder_challenger` metadata lane if the lane should disappear from previews.
3. Keep the Ollama model installed unless storage pressure requires a separate, explicitly approved cleanup.

To remove the local model later, use an explicit cleanup task and prove storage first:

```bash
ollama rm hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M
```

Do not run model cleanup as part of benchmark prep.
