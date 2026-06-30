# Qwen2.5-Coder 14B Local Challenger

## Installed Model

- Ollama model id: `qwen2.5-coder:14b`
- SpiritOS lane id: `qwen14b_coder_challenger`
- Storage root: `/mnt/spirit-8tb/ollama-models`
- Ollama home symlink: `/usr/share/ollama/.ollama -> /mnt/spirit-8tb/ollama-models`

## Role

Qwen2.5-Coder 14B is installed as a local challenger only. It is heavier than the existing Qwen2.5-Coder 7B primary coder lane and needs benchmark evidence before any promotion.

Current roles:

- Primary coder: `qwen2.5-coder:7b` via `qwen_local_coder`
- Challenger: `qwen2.5-coder:14b` via `qwen14b_coder_challenger`
- Challenger: `hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M` via `ornith_coder_challenger`
- Hermes and Gemma lanes remain unchanged.

## Invocation

Direct Ollama smoke:

```bash
ollama run qwen2.5-coder:14b "Reply exactly: Qwen 14B smoke OK"
```

Bounded API smoke:

```bash
python3 - <<'PY'
import json, urllib.request

payload = {
    "model": "qwen2.5-coder:14b",
    "prompt": "Reply exactly: Qwen 14B smoke OK",
    "stream": False,
    "keep_alive": "1m",
    "options": {"temperature": 0, "num_predict": 8, "num_ctx": 512},
}
request = urllib.request.Request(
    "http://127.0.0.1:11434/api/generate",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=180) as response:
    print(response.read().decode())
PY
```

## Promotion Boundary

Do not promote Qwen 14B or make it the default `/coding` route until a separate benchmark compares:

- Qwen2.5-Coder 7B primary
- Qwen2.5-Coder 14B challenger
- Ornith 9B challenger

The benchmark should cover coder, workflow organizer, repair, closeout, and verifier-support roles with identical prompts and behavior-based grading.

## Rollback

Routing rollback only:

1. Remove `qwen14b_coder_challenger` from `source_proxy/decision/model_lanes.py`.
2. Remove the focused test assertions for `qwen14b_coder_challenger`.
3. Leave the Ollama model files in place unless a separate cleanup task explicitly approves deletion.

Do not delete model blobs as part of a routing rollback.
