# Ornith 1.0 9B Local Install Evidence

Date: 2026-06-28 22:07 America/New_York

## Verdict

PASS for install, storage safety, local Ollama inventory, and bounded smoke test.

NO-GO for benchmark claims. Ornith is installed as a challenger only and has not been proven better than Qwen inside SpiritOS.

## Installed model

- Ollama model: `hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M`
- Ollama ID after install: `0e5b9bbae3c6`
- Size reported by `ollama list`: `5.6 GB`
- Upstream route used: Hugging Face GGUF via Ollama, matching `ollama run hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M`

## Preflight

```text
host: Spirit
repo: /home/source/SpiritOS
branch: integration/cleanup-plan3-debug-20260623
root disk: /dev/sdb2 457G size, 357G used, 77G available, 83%
8TB disk: /dev/sda1 7.3T size, 265G used, 6.6T available, 4%
GPU: NVIDIA GeForce RTX 3060, 12288 MiB total VRAM, driver 580.159.03
Ollama service: active
Ollama service user: ollama
```

The worktree already had unrelated modified and untracked files before this task. This install touched only the Ornith routing/docs/evidence files.

## Storage proof

```text
/usr/share/ollama/.ollama -> /mnt/spirit-8tb/ollama-models
readlink -f /usr/share/ollama/.ollama: /mnt/spirit-8tb/ollama-models
/mnt/spirit-8tb/ollama-models/models/blobs: 39G
/mnt/spirit-8tb/ollama-models/models/manifests: 100K
```

No SSD model migration was needed because Ollama's default home was already symlinked to the 8TB model store. No existing models were deleted or moved.

## Ollama inventory after pull

```text
NAME                                                     ID              SIZE      MODIFIED
hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M         0e5b9bbae3c6    5.6 GB    2026-06-28
gemma3n:e4b                                              15cb39fd9394    7.5 GB    2 weeks ago
hermes4:latest                                           3e79497c9643    9.0 GB    4 weeks ago
hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M    ce5cb56a7898    9.0 GB    4 weeks ago
hermes3:8b-abliterated                                   621eb9c2e65e    4.7 GB    5 weeks ago
mannix/llama3-8b-ablitered-v3:latest                     46688a22037e    4.7 GB    5 weeks ago
qwen2.5-coder:7b                                         dae161e27b0e    4.7 GB    6 weeks ago
llama3.1:8b                                              46e0c10c039e    4.9 GB    6 weeks ago
llama3:latest                                            365c0bd3c000    4.7 GB    2 months ago
```

## Smoke test

Command path:

```text
POST http://127.0.0.1:11434/api/generate
model: hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M
prompt: Reply with exactly: Ornith smoke OK
stream: false
options: num_predict=16, temperature=0
```

Result summary:

```text
done: true
done_reason: stop
response excerpt: Ornith smoke OK
total_duration: 68.35s
load_duration: 67.48s
prompt_eval_count: 8
eval_count: 14
```

The first CLI smoke with a 90s timeout proved loading but timed out before clean text output. The HTTP smoke above completed successfully.

## VRAM snapshot

```text
before: 27 MiB / 12288 MiB
during load/generation: 6535 MiB / 12288 MiB
after response: 6549 MiB / 12288 MiB
```

Q4_K_M fits the Dell RTX 3060 12GB for a tiny local prompt with roughly 5.7GB headroom in this smoke condition.

## SpiritOS routing diff summary

- Added `ornith_coder_challenger` to `source_proxy.decision.model_lanes`.
- Kept `primary_coder_lane` as `qwen_local_coder`.
- Added `SOURCE_PROXY_ORNITH_CHALLENGER_OLLAMA_MODEL=hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M` to `config/source-proxy.example.env`.
- Added tests proving Ornith is not a primary or silent replacement.

## Next benchmark plan

Use identical prompts and identical evidence scoring across:

- Qwen primary coder lane: `qwen2.5-coder:7b`
- Ornith challenger lane: `hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M`
- Hermes critique/oracle lane where already used
- Gemma intent/context lane where relevant

Do not mark Ornith promoted until benchmark receipts include behavior verification, diff verification, no-diff failure labeling, latency/VRAM evidence, and false-positive/false-negative notes.
