# Increment 5.1 - Closeout doc

Date: 2026-05-29T20:04:34-04:00

```text
9:GO for host/model install, 8TB storage proof, Source Proxy local routing, and Source Proxy local chat smoke.
13:- Default local model: `hermes4:latest`
20:8TB model storage is proven GO. `/mnt/spirit-8tb` is mounted and `/usr/share/ollama/.ollama` resolves to `/mnt/spirit-8tb/ollama-models`. Direct running-process `OLLAMA_MODELS` proof was blocked by `/proc` permissions, so the accepted proof is the mounted drive plus active Ollama home symlink.
26:- Source Proxy local model: `ollama_chat/hermes4:latest`.
27:- `/coding` status surface: provider/model truth is sourced from Source Proxy status/prompt-packet enrichment and prefers resolved model when available.
28:- Hermes 3: preserved as fast fallback/oracle/voice-friendly lane.
29:- Qwen: preserved as explicitly selectable/non-default.
30:- Tool compatibility: Hermes 4 accepts OpenAI-compatible tool schemas, but emitted a noop tool call despite instruction not to. Keep local tools disabled by default.
40:- Source Proxy health, self status, models, and local chat completion.
44:- Source Proxy pytest was not available: `python3 -m pytest` reported missing `pytest`.
49:- Live Source Proxy has not reloaded the new requested/resolved/storage-proof status fields, though it already routes local chat to Hermes 4.
50:- Hermes 4 is slower than Hermes 3/Qwen in observed smokes.
51:- Tool schema support should not be treated as safe file/command tool readiness.
58:- Source Proxy local route: set `SOURCE_PROXY_OLLAMA_MODEL=hermes3:8b-abliterated` or `SOURCE_PROXY_OLLAMA_MODEL=qwen2.5-coder:7b` and restart Source Proxy when approved.
65:- No Qwen, Hermes 3, llama, or older models were removed.
```

## Result

Closeout doc created with GO/NO-GO truth, model IDs, storage proof, live runtime caveats, rollback notes, and not-changed guarantees.
