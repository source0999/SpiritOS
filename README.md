# SpiritOS

Monorepo for **Spirit OS**: local-first chat against Ollama, Next.js frontend, and supporting backend services.

## Active fixes

- [x] **Anti-Refusal Baked** — `backend/Modelfile` strengthened with ABSOLUTE PROHIBITIONS and refusal-pattern negation; re-run `ollama create spirit-os -f backend/Modelfile`.
- [x] **Oracle UIs Unified** — Nav labels **Oracle Chat** / **Oracle Voice**; chat is `OracleChatPage` with Oracle Chat copy; voice page header shows Oracle Voice (`frontend/components/Navigation.tsx`, `frontend/app/chat/page.tsx`, `frontend/app/oracle/page.tsx`).
- [x] **Depth Modifiers Added** — Short / Normal / Deep / Deep Dive appended via `DEPTH_DIRECTIVES` on `/api/spirit` and `/api/oracle`; chat sends `depth` through `useStream` (`frontend/hooks/useStream.ts`, API routes, both UIs).
- [x] **Oracle Memory Active** — Oracle Voice keeps `conversationHistory`, sends `history` JSON to `/api/oracle`; route uses Ollama `/api/chat` with system + history + latest transcript (`frontend/app/oracle/page.tsx`, `frontend/app/api/oracle/route.ts`).
- [x] **Continuous Mode Added** — Hands-Free toggle; after `drain()` completes, `prime()` + auto `startRecording` when enabled (`frontend/app/oracle/page.tsx`).
- [x] **Oracle TTS Fixed** — `useTTS({ alwaysOn: true })` on Oracle Voice, `prime()` on mic tap, `AudioQueue.prime()` for gesture-safe context (`frontend/hooks/useTTS.ts`, `frontend/lib/audioQueue.ts`).
- [x] **Oracle SSE Stream Fixed** — client parser widened to `parsed.text ?? parsed.message?.content ?? ""` covering both Ollama `/api/generate` and `/api/chat` response shapes (`frontend/app/oracle/page.tsx`).
- [x] **Oracle SSE Crash Fixed** — Oracle Voice `processAudio` uses an `sseLineBuffer` so `data:` lines are not split mid-chunk; terminal `data: [DONE]` is handled before `JSON.parse` (`frontend/app/oracle/page.tsx`).
- [x] **Audio Context Priming Added** — `prime()` runs at the start of `startRecording` and `AudioQueue.prime()` calls `ensureContext().resume()` for gesture-safe unlock (`frontend/app/oracle/page.tsx`, `frontend/lib/audioQueue.ts`).
- [x] **Legacy Debug Code Stripped** — all 8 `#region agent log` fetch blocks removed from `frontend/app/chat/page.tsx`; zero requests to `localhost:7454`.

## Roadmap (phased)

### Frontend

- [x] **Unfiltered 3B engine swap** — `nchapman/dolphin3.0-llama3:3b` via Tailscale Ollama host; short persona prompts for fast prefill on 8GB-class GPUs.
- [x] **History fix** — prior turns are built from Dexie thread messages and sent as `history` in `POST /api/spirit` (no more `historyTurns: 0` amnesia).
- [x] **Sentence-level streaming TTS** — LLM tokens are split on sentence boundaries mid-stream and piped to `/api/tts` via `onSentenceReady`; voice begins before generation completes.
- [x] **Synchronous replay path** — `useTTS.speak()` now stops once, enqueues speech segments synchronously, and drops pause markers for fastest first-audio.
- [x] **Ollama-only Spirit routing** — `/api/spirit` streams from local Ollama with custom model `spirit-os` at `num_ctx: 8192`.
- [x] **Oracle Chat modes + depth** — Peer / Educational / Chaos plus depth (Short–Deep Dive) drive `/api/spirit` (`frontend/app/chat/page.tsx`, `frontend/hooks/useStream.ts`).
- [x] **OpenAI TTS Cloud Pivot** — `/api/tts` now streams OpenAI `tts-1` audio (`voice: nova`, MP3) directly to the client.
- [x] **Local XTTS Decommissioned** — XTTS service removed from backend compose; voice synthesis is cloud-only.
- [x] **MSE Decode Audio Fix** — removed browser MSE path; `/api/tts` responses are decoded via `decodeAudioData` with look-ahead prefetch.
- [x] **Dolphin Model Binding** — all local Ollama inference defaults bind to `nchapman/dolphin3.0-llama3:3b`.

### Backend

- [x] **Oracle stream fix** — `/api/oracle` Ollama call switched from `stream: false` to `stream: true` with `drainOllamaStream()`; 8192 num_ctx no longer deadlocks the response pipeline.
- [x] **Spirit Modelfile Persona** — `backend/Modelfile` defines `spirit-os` from `dolphin-llama3:8b`; `backend/gpu-setup.sh` runs `ollama create spirit-os`; chat and Oracle use model `spirit-os`.
- [x] **Oracle VAD Auto-Stop** — Oracle mic capture stops after ~1.5s of silence via RMS on time-domain analyser samples (`frontend/app/oracle/page.tsx`).
- [x] **Oracle Streaming TTS Pipeline** — `/api/oracle` returns SSE after Whisper STT, streaming Ollama `/api/chat` deltas to the client; Oracle Voice enqueues sentences to `/api/tts` (Piper) via `useTTS` while the model is still generating.
- [x] **Persona Unified** — `backend/Modelfile` holds the Spirit persona; Oracle uses `MODE_DIRECTIVES` in the prompt only (no duplicate `system:`); chat uses `MODE_DIRECTIVES` in the API system message. Re-run `ollama create spirit-os -f backend/Modelfile` after Modelfile edits.
- [x] **Dynamic Modes Implemented** — Oracle footer and chat input use Peer / Educational / Chaos; form field `mode` for Oracle; `sarcasm` JSON field for chat (`frontend/app/oracle/page.tsx`, `frontend/app/chat/page.tsx`).
- [x] **Oracle Latency Fixed** — `/api/oracle` uses `OLLAMA_NUM_CTX = 2048` (hard-coded, ignores env) for lower TTFT; `/api/spirit` stays at `8192`.
- [x] **HQ Voice Upgraded** — Piper prefetch and `fable` map target `en_AU-kemie-high` (`backend/docker-compose.yml`, `backend/openedai-config/voice_to_speaker.yaml`). Restart `openedai-speech` after pull.

## Quick start (frontend)

From `frontend/`:

1. Copy `frontend/.env.example` → `frontend/.env.local` if needed.
2. On the Ollama host: `ollama pull dolphin-llama3:8b`, then from repo root: `ollama create spirit-os -f backend/Modelfile` (or run `sudo bash backend/gpu-setup.sh` after ROCm setup, which includes the same create step).
3. `npm install` && `npm run dev`

The API route `frontend/app/api/spirit/route.ts` targets **`http://100.111.32.31:11434/api/chat`** for this deployment (Tailscale). Adjust there if your host changes.

## Docs

- Deeper frontend architecture notes: [`frontend/README.md`](frontend/README.md)
