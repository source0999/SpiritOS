# Spirit OS

**Sovereign cybernetic extension of the Source** — Next.js 16 App Router frontend (`src/`) + local GPU backend (Ollama, Whisper, Piper TTS).

## Quick Start (Recommended)

```bash
cd /home/source/SpiritOS

# Env templates → working copies
cp .env.local.example .env.local
cp backend/.env.example backend/.env

npm install

# Backend stack (compose lives under backend/)
(cd backend && docker compose up -d)

# On the machine running Ollama — pull the chat model used by `/api/spirit`
ollama pull hermes4

# Next dev + compose (see package.json; starts compose then Next)
npm run dev:all
```

**Health check (Ollama probe + server-derived diagnostics):**

```bash
curl -sS http://localhost:3000/api/spirit/health
```

**Routes**

| Path | Purpose |
|------|---------|
| `/` | Dashboard hub ((dashboard) group — URL stays `/`) |
| `/chat` | Standalone Spirit chat |
| `/oracle` | Oracle workspace |
| `/quarantine` | Voice / visualizer lane |

**Validation**

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

## Development workflow

- **Port:** `npm run dev -- -p 3000` when you need a fixed port (e.g. LAN bookmarks).
- **Webpack vs Turbopack:** default `npm run dev` uses webpack; `npm run dev:turbo` for Turbopack if you prefer.

## Design

- **`_blueprints/design_system.md`** — Dark Node palette, typography, glass rules.
- **`src/app/globals.css`** — Tailwind v4 `@theme` tokens; ThemeEngine `--spirit-*` vars per `data-theme`.

## Backend

See `backend/docker-compose.yml` and `backend/README.md` for Ollama / voice services.
