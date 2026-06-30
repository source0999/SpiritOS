# Qwen2.5-Coder 14B Local Challenger Install Evidence

Date: 2026-06-29

## Verdict

PASS for install, storage placement, metadata routing prep, and tiny local smokes. No benchmark comparison was run.

## Preflight

- Repo path: `/home/source/SpiritOS`
- Windows mapped path: `Z:\`
- Git tree: dirty before this task with unrelated SpiritFlix, Source Proxy, and evidence changes already present.
- Root filesystem before pull: `/dev/sdb2`, 457G size, 357G used, 77G available.
- 8TB filesystem before pull: `/dev/sda1`, 7.3T size, 316G used, 6.6T available.
- GPU: NVIDIA GeForce RTX 3060, 12288 MiB total, 4921 MiB used, 6988 MiB free before install check.
- Ollama service user: `ollama`
- Ollama service group: `ollama`
- Ollama service path: `/etc/systemd/system/ollama.service`

## Storage Proof

- `/usr/share/ollama/.ollama -> /mnt/spirit-8tb/ollama-models`
- `readlink -f /usr/share/ollama/.ollama` returned `/mnt/spirit-8tb/ollama-models`
- Model store size before install: 39G
- Model store size after install: 47G
- Qwen 14B manifest path exists under `/mnt/spirit-8tb/ollama-models/models/manifests/registry.ollama.ai/library/qwen2.5-coder/14b`
- Largest new model blob observed under `/mnt/spirit-8tb/ollama-models/models/blobs/sha256-7ad9be1e446e3da0c149fdf55284c90be666d3e13c6e2581587853f4f9538073`

## Install Proof

Installed with:

```bash
ollama pull qwen2.5-coder:14b
```

Post-install `ollama list` showed:

```text
qwen2.5-coder:14b  9ec8897f747e  9.0 GB
qwen2.5-coder:7b   dae161e27b0e  4.7 GB
hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M  0e5b9bbae3c6  5.6 GB
gemma3n:e4b        15cb39fd9394  7.5 GB
hermes4:latest     3e79497c9643  9.0 GB
```

Root filesystem after pull: `/dev/sdb2`, 457G size, 357G used, 77G available.

8TB filesystem after pull: `/dev/sda1`, 7.3T size, 325G used, 6.6T available.

## Smoke Proof

Qwen 14B API smoke:

```json
{
  "ok": true,
  "elapsed_s": 60.63,
  "response": "Qwen 14B smoke OK",
  "model": "qwen2.5-coder:14b",
  "done": true
}
```

Qwen 14B runtime/GPU note:

```text
NVIDIA GeForce RTX 3060, 12288 MiB total, 8807 MiB used, 3102 MiB free, 76% GPU utilization
Ollama API ps: qwen2.5-coder:14b, size_vram 8966774784, context_length 512
```

Qwen 7B default model smoke:

```json
{
  "ok": true,
  "elapsed_s": 58.06,
  "response": "Qwen 7B smoke OK",
  "model": "qwen2.5-coder:7b",
  "done": true
}
```

Qwen 7B runtime/GPU note:

```text
NVIDIA GeForce RTX 3060, 12288 MiB total, 4725 MiB used, 7184 MiB free, 29% GPU utilization
Ollama API ps: qwen2.5-coder:7b, size_vram 4718686208, context_length 512
```

An initial CLI smoke timed out after 10 minutes while an existing 7B runner was still loaded. The stuck client was killed without stopping Ollama or deleting models, then the bounded API smoke with `num_predict: 8` completed successfully.

## Routing Proof

Changed `source_proxy/decision/model_lanes.py` to add `qwen14b_coder_challenger` as an installed challenger lane. The registry still reports `primary_coder_lane: qwen_local_coder`.

Focused tests cover that:

- `qwen_local_coder` remains primary.
- `qwen14b_coder_challenger` is benchmark-prep only.
- Qwen 14B cannot silently replace the primary Qwen 7B lane.
- Ornith remains a separate challenger lane.

## Next Benchmark Recommendation

Run a separate benchmark prompt comparing Qwen2.5-Coder 7B, Qwen2.5-Coder 14B, and Ornith 9B with identical inputs across coder, workflow organizer, repair, closeout, and verifier-support roles. Keep Qwen 14B challenger-only unless that evidence justifies promotion.
