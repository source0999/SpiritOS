# Hermes 4 Full Integration Closeout

Date: 2026-05-29

## Gate Result

NO-GO for full daily-driver cutover until the live SpiritOS frontend runtime is updated from `llama3.1:8b` to Hermes 4 and Next is restarted with approval.

GO for host/model install, 8TB storage proof, Source Proxy local routing, and Source Proxy local chat smoke.

## Model IDs

- Default local model: `hermes4:latest`
- Base HF model: `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`
- Fast fallback/oracle/voice-friendly model: `hermes3:8b-abliterated`
- Selectable non-default coding model: `qwen2.5-coder:7b`

## Storage

8TB model storage is proven GO. `/mnt/spirit-8tb` is mounted and `/usr/share/ollama/.ollama` resolves to `/mnt/spirit-8tb/ollama-models`. Direct running-process `OLLAMA_MODELS` proof was blocked by `/proc` permissions, so the accepted proof is the mounted drive plus active Ollama home symlink.

## Integration Status

- SpiritOS repo default: Hermes 4 in code/env examples.
- Live SpiritOS frontend health: currently reports `llama3.1:8b`; operator fix required in live env, then approved Next restart.
- Source Proxy local model: `ollama_chat/hermes4:latest`.
- `/coding` status surface: provider/model truth is sourced from Source Proxy status/prompt-packet enrichment and prefers resolved model when available.
- Hermes 3: preserved as fast fallback/oracle/voice-friendly lane.
- Qwen: preserved as explicitly selectable/non-default.
- Tool compatibility: Hermes 4 accepts OpenAI-compatible tool schemas, but emitted a noop tool call despite instruction not to. Keep local tools disabled by default.

## Checks Run

- Ollama service/storage/model path checks.
- Hermes 4 alias runtime smoke.
- Ollama tags/base model visibility.
- OpenAI-compatible Hermes 4 chat probe.
- Tool schema probe.
- Spirit frontend health.
- Source Proxy health, self status, models, and local chat completion.
- `npm run lint`: warnings only.
- `npm run typecheck`: passed.
- Focused Vitest: `model-provider-status` and `agent-trials-ui` passed.
- Source Proxy pytest was not available: `python3 -m pytest` reported missing `pytest`.

## Remaining Risks

- Live frontend env still points at `llama3.1:8b`.
- Live Source Proxy has not reloaded the new requested/resolved/storage-proof status fields, though it already routes local chat to Hermes 4.
- Hermes 4 is slower than Hermes 3/Qwen in observed smokes.
- Tool schema support should not be treated as safe file/command tool readiness.

## Rollback

To switch local default back if Hermes 4 is too slow or unstable:

- Frontend chat: set `OLLAMA_MODEL=hermes3:8b-abliterated` or `OLLAMA_MODEL=qwen2.5-coder:7b` in the live frontend environment and restart Next when approved.
- Source Proxy local route: set `SOURCE_PROXY_OLLAMA_MODEL=hermes3:8b-abliterated` or `SOURCE_PROXY_OLLAMA_MODEL=qwen2.5-coder:7b` and restart Source Proxy when approved.
- Keep `ORACLE_OLLAMA_MODEL=hermes3:8b-abliterated` for fast oracle/voice-friendly use.

## Not Changed

- No Ollama models were deleted.
- No Ollama prune ran.
- No Qwen, Hermes 3, llama, or older models were removed.
- No `/mnt/spirit-8tb` ownership or symlink changes were made.
- No secrets were read or printed.
- No OpenAI/Anthropic/DeepSeek provider support was removed.
- No commit or push ran.
