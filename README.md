# SpiritOS

Monorepo for **Spirit OS**: local-first chat against Ollama, Next.js frontend, and supporting backend services.

## Roadmap (phased)

### Frontend

- [x] **Unfiltered 3B engine swap** — `nchapman/dolphin3.0-llama3:3b` via Tailscale Ollama host; short persona prompts for fast prefill on 8GB-class GPUs.
- [x] **History fix** — prior turns are built from Dexie thread messages and sent as `history` in `POST /api/spirit` (no more `historyTurns: 0` amnesia).
- [ ] **Module 4: XTTS v2 voice pipeline** — TTS playback and `audioUrl` on messages (see `frontend/lib/db.types.ts`).
- [x] **Micro-Segmented Audio** — burst-split TTS segments (5-8 words / punctuation) with look-ahead fetch.
- [x] **Studio Speaker Activation** — XTTS uses studio speaker conditioning (default: `Claribel Dervla`).

### Backend

- [ ] **Voice / auxiliary services** — align `backend/docker-compose.yml` and deployment with Module 4 when ready.

## Quick start (frontend)

From `frontend/`:

1. Copy `frontend/.env.example` → `frontend/.env.local` if needed.
2. On the Ollama host (Dell): `ollama pull nchapman/dolphin3.0-llama3:3b`
3. `npm install` && `npm run dev`

The API route `frontend/app/api/spirit/route.ts` targets **`http://100.111.32.31:11434/api/chat`** for this deployment (Tailscale). Adjust there if your host changes.

## Docs

- Deeper frontend architecture notes: [`frontend/README.md`](frontend/README.md)
