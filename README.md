# SpiritOS

Monorepo for **Spirit OS**: local-first chat against Ollama, Next.js frontend, and supporting backend services.

## Roadmap (phased)

### Frontend

- [x] **Unfiltered 3B engine swap** — `nchapman/dolphin3.0-llama3:3b` via Tailscale Ollama host; short persona prompts for fast prefill on 8GB-class GPUs.
- [x] **History fix** — prior turns are built from Dexie thread messages and sent as `history` in `POST /api/spirit` (no more `historyTurns: 0` amnesia).
- [x] **Sentence-level streaming TTS** — LLM tokens are split on sentence boundaries mid-stream and piped to `/api/tts` via `onSentenceReady`; voice begins before generation completes.
- [x] **Synchronous replay path** — `useTTS.speak()` now stops once, enqueues speech segments synchronously, and drops pause markers for fastest first-audio.
- [x] **Ollama-only Spirit routing** — `/api/spirit` streams from local Ollama with custom model `spirit-os` at `num_ctx: 8192`.
- [x] **Sovereign-locked chat UI** — chat mode toggles removed; `captureMessageEvents()` and `startStream()` always run in `"sovereign"` mode.
- [x] **OpenAI TTS Cloud Pivot** — `/api/tts` now streams OpenAI `tts-1` audio (`voice: nova`, MP3) directly to the client.
- [x] **Local XTTS Decommissioned** — XTTS service removed from backend compose; voice synthesis is cloud-only.
- [x] **MSE Decode Audio Fix** — removed browser MSE path; `/api/tts` responses are decoded via `decodeAudioData` with look-ahead prefetch.
- [x] **Dolphin Model Binding** — all local Ollama inference defaults bind to `nchapman/dolphin3.0-llama3:3b`.

### Backend

- [x] **Oracle stream fix** — `/api/oracle` Ollama call switched from `stream: false` to `stream: true` with `drainOllamaStream()`; 8192 num_ctx no longer deadlocks the response pipeline.
- [x] **Spirit Modelfile Persona** — `backend/Modelfile` defines `spirit-os` from `dolphin-llama3:8b`; `backend/gpu-setup.sh` runs `ollama create spirit-os`; chat and Oracle use model `spirit-os`.
- [x] **Oracle VAD Auto-Stop** — Oracle mic capture stops after ~1.5s of silence via RMS on time-domain analyser samples (`frontend/app/oracle/page.tsx`).
- [x] **Oracle Streaming TTS Pipeline** — `/api/oracle` returns SSE token chunks after Whisper STT; the Oracle client enqueues sentences to `/api/tts` (Piper) via `useTTS` while the model is still generating.

## Quick start (frontend)

From `frontend/`:

1. Copy `frontend/.env.example` → `frontend/.env.local` if needed.
2. On the Ollama host: `ollama pull dolphin-llama3:8b`, then from repo root: `ollama create spirit-os -f backend/Modelfile` (or run `sudo bash backend/gpu-setup.sh` after ROCm setup, which includes the same create step).
3. `npm install` && `npm run dev`

The API route `frontend/app/api/spirit/route.ts` targets **`http://100.111.32.31:11434/api/chat`** for this deployment (Tailscale). Adjust there if your host changes.

## Docs

- Deeper frontend architecture notes: [`frontend/README.md`](frontend/README.md)
