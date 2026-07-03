# GLM-4-9B Install Evidence

Generated: 2026-07-03T02:40:00Z

## Model

- `hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF:Q5_K_M`
- Ollama ID: `02b0d18c6b7a`
- Size: 7.1 GB

## Storage (8TB)

```text
/usr/share/ollama/.ollama -> /mnt/spirit-8tb/ollama-models
/mnt/spirit-8tb/ollama-models/models/manifests/hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF
```

## Pull

- First attempt: digest mismatch after 7.1 GB download (sha256 want/got mismatch).
- Retry: success.

## Smoke

```text
prompt: Reply with exactly: GLM smoke OK
response: GLM smoke OK
eval_count: 5
total_duration_ms: 134705
```

## Benchmark

Full model-lane benchmark evidence:

```text
docs/evidence/glm4-9b-model-lanes-20260702-202200/
```

See `docs/local-models/glm-4-9b-benchmark.md` for routing verdict.
