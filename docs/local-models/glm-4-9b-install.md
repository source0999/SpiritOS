# GLM-4-9B Local Challenger Install

GLM-4-9B is installed on the Dell SpiritOS host as a local Ollama challenger model for Source Proxy / Design Studio lane promotion testing. It is not the default SpiritOS coder model.

## Installed Quant

```text
hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF:Q5_K_M
```

Q5_K_M was chosen as the primary target quant: ~7.1 GB on disk, fits the RTX 3060 12GB with headroom for benchmark runs alongside other local models.

First pull attempt failed with a digest mismatch; the retry completed successfully.

## Storage

Ollama model storage resolves to the 8TB drive:

```text
/usr/share/ollama/.ollama -> /mnt/spirit-8tb/ollama-models
```

Manifest path:

```text
/mnt/spirit-8tb/ollama-models/models/manifests/hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF
```

## Local Invocation

Direct Ollama smoke:

```bash
ollama run hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF:Q5_K_M
```

Bounded API smoke:

```bash
curl -s http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  --data '{"model":"hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF:Q5_K_M","prompt":"Reply with exactly: GLM smoke OK","stream":false,"options":{"num_predict":16,"temperature":0}}'
```

First-load smoke on 2026-07-02: response `GLM smoke OK`, ~135s cold start (model load + 5 tokens).

## SpiritOS Routing

No production routing change was made. GLM is benchmark-only until Britton reviews lane evidence.

Suggested env key for future challenger wiring:

```text
SOURCE_PROXY_GLM_CHALLENGER_OLLAMA_MODEL=hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF:Q5_K_M
```

Qwen remains the primary coder lane:

```text
SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b
primary_coder_lane=qwen_local_coder
```

## Challenger-Only Rule

GLM is a candidate for coder, workflow, intent, critique, research, and closeout lanes. It is not proven better inside SpiritOS until the model-lane benchmark compares it against Qwen 7B/14B, Hermes, Gemma, and Ornith with identical prompts and scoring.

The lane disallows:

- silent replacement for any current primary lane
- default production routing
- superiority claims before benchmark evidence
- product PASS declarations without behavior evidence

## Benchmark

Run the GLM suite:

```bash
cd /home/source/SpiritOS
python3 -m source_proxy.benchmarks.model_lane_benchmark --suite glm
```

Evidence lands under `docs/evidence/glm4-9b-model-lanes-YYYYMMDD-HHMMSS/`.

## Rollback

Rollback routing without deleting the model:

1. Do not set `SOURCE_PROXY_GLM_CHALLENGER_OLLAMA_MODEL` in production env.
2. Keep benchmark evidence for audit; no registry lane was added.

To remove the local model later:

```bash
ollama rm hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF:Q5_K_M
```

Do not run model cleanup as part of benchmark prep.
