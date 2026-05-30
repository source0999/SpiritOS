# Phase 1 Closeout - Host and model storage verification

Date: 2026-05-29

## Result

GO.

## Evidence

- Increment 1.1: `/mnt/spirit-8tb` is mounted and `/usr/share/ollama/.ollama` resolves to `/mnt/spirit-8tb/ollama-models`; `hermes4:latest` is visible in `ollama list`.
- Increment 1.2: `hermes4` alias returned `HERMES4_ALIAS_OK`; base HF model is visible in Ollama tags as `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`.
- Increment 1.3: model references were inventoried from example env files, README, `src`, `source_proxy`, `docs`, and `scripts` without reading real `.env.local`.

## Notes

- Running process `OLLAMA_MODELS` could not be read from `/proc/$pid/environ` due permissions, but the active Ollama home symlink proves model storage resolves to the 8TB path.
- The repository had many pre-existing dirty and untracked files outside this gate. They were not reverted or cleaned.
- `git diff --check` passed at phase closeout.
