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

**Brain vs TTS (do not conflate them):** `/api/spirit` uses `OLLAMA_MODEL` for `/chat` text generation. `/oracle` can use `ORACLE_OLLAMA_MODEL` when set. Voice is synthesized via same-origin **`/api/tts`** (`TTS_PROVIDER=piper` or `elevenlabs`); the browser never sees `ELEVENLABS_API_KEY`. Optional `ELEVENLABS_VOICE_SPEED` (default 1.12, clamped 0.7–1.2) sets ElevenLabs cadence; Voice settings can send a per-request `speed` override. **`GET /api/tts/voices`** feeds the Voice picker. **`ELEVENLABS_VOICE_ALLOWLIST`** supports **`Clarice:voice_id`** (recommended, no catalog read) or comma-separated **names only** (needs catalog + `voices_read`; if the catalog fails, switch to `Name:voice_id`). When any allowlist is set, the API returns **only** those voices—never the full catalog. Defaults prefer **`ELEVENLABS_DEFAULT_VOICE_ID`**, then **Clarice** by name, then **`ELEVENLABS_VOICE_ID`**. Response **`X-Spirit-TTS-Voice-Name-Encoded`** keeps display names ASCII-safe for Tailscale.

**Prompt 10B / 10C-C / 10D-F:** Mode presets + **response token caps** (Sassy/Brutal/Peer stay short on casual prompts). **`/oracle`** adds a **voice surface** layer on top of the same modes (`buildRuntimeSurfaceInstruction`) — live spoken context, not coding-default; tighter caps apply only when `runtimeSurface=oracle`. **Deep think** and **Web search** prefs live under the `/chat` composer (`localStorage` key `spirit:threadUiPrefs:v2`; Researcher web defaults **ON** with tri-state `unset|enabled|disabled` — legacy `o:true` migrates to disabled). Assistant text passes **`sanitizeAssistantVisibleText`** before render, copy, TTS, and Dexie persist — strips `<think>` / leaked mode-contract lines. Researcher gets **source enforcement**: no fake `[n]` citations or Sources sections when search returned no verified `http(s)` URLs; `/api/spirit` adds `x-spirit-source-count`, `x-spirit-search-provider`, `x-spirit-search-status`, **`x-spirit-runtime-surface`**. Teacher + **Web search on** + educational prompts can prefetch OpenAI web for real **Study aids** links; otherwise **Study aids to search** (quoted phrases, no invented URLs). Research plan panel + workflow visualizer clear on thread/draft switch and sit **above** the composer; visualizer has a **compact** idle line after dismiss on casual modes.

**Routes**

| Path | Purpose |
|------|---------|
| `/` | Dashboard hub ((dashboard) group — URL stays `/`) |
| `/chat` | Saved-thread workspace (Dexie), mode runtime v2 (**Peer** + profiles), local search/pins, Activity + Spirit Profile panels |
| `/oracle` | Oracle Voice MVP — **hands-free session**, ephemeral (no saved threads), **`runtimeSurface=oracle`** + **Oracle voice surface prompt** (Prompt 10D-F), **Whisper** via **`/api/stt/transcribe`** + MediaRecorder + amplitude VAD auto-stop + text fallback. `Start session` → silence VAD auto-sends → TTS speaks → re-arms recording → repeat until `Stop session`. `Finish now` is a backup button. Insecure-context (plain http:// to LAN/Tailscale IP) shows an unmissable warning + same-host HTTPS upgrade link. Shared mode/TTS/profile stack. (`_blueprints/oracle_voice_mvp.md`) |
| `/quarantine` | Voice / visualizer lane |

**Validation**

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

## Tailscale / LAN dev (HMR)

Next blocks cross-origin dev assets unless the browser `Origin` hostname is allowlisted. Defaults live in `allowed-dev-origins.ts` and merge with **`NEXT_ALLOWED_DEV_ORIGINS`** (comma-separated hostnames in `.env.local`, no `http://` or ports). **Restart the dev server** after edits — `next.config.ts` only sees env at startup.

### Oracle microphone over LAN / Tailscale IP (`http://10…`, `http://100…`)

Browsers treat plain **`http://` to a LAN or Tailscale IP** as a **non-secure context** and **hide `navigator.mediaDevices`** — Oracle cannot capture mic there until you use **HTTPS**.

- **`npm run dev:https`** — same `-H 0.0.0.0` bind as `npm run dev`, plus Next **`--experimental-https`** (self-signed cert). Fine for **this machine** via `https://localhost:3000`.
- **`npm run dev:https:lan`** — HTTPS dev using certs that include **your LAN / Tailscale hosts** in the SAN. Generate once:  
  `SPIRIT_TLS_EXTRA_HOSTS=10.0.0.186,100.111.32.31 bash scripts/gen-dev-cert.sh`  
  then **`npm run dev:https:lan`** or **`npm run dev:all:https:lan`**. Then open **`https://10.0.0.186:3000/oracle`** from another device.
- **`npm run dev:all:https`** — Docker backends + **`npm run dev:https`** (quick localhost HTTPS).
- **`npm run dev:all:https:lan`** — Docker backends + **`npm run dev:https:lan`** (run **`scripts/gen-dev-cert.sh`** first).

You cannot “fix” this in React alone; it is **browser security**.

#### Remote browser shows “connection failed” (but `Ready` on the server)

1. **Firewall on the Spirit host** — allow inbound TCP **3000**: e.g. `sudo ufw allow 3000/tcp` then `sudo ufw reload`. Confirm listen: `ss -tlnp | grep 3000` shows `0.0.0.0:3000`.
2. **Ping / route** — client must reach the host IP on your LAN or Tailscale (`tailscale ping` helps).
3. **TLS name mismatch** — use **`npm run dev:https:lan`** + **`gen-dev-cert.sh`** so the cert includes the hostname/IP you type in the bar.
4. From the client, sanity-check: `curl -vk https://10.0.0.186:3000/` — if TCP fails before TLS, it is network/firewall, not Oracle.

## Development workflow

- **Port / HTTPS:** `npm run dev -- -p 3000` when you need a fixed port. For **Oracle mic from another machine**, see *Oracle microphone over LAN / Tailscale IP* — **`dev:https:lan`** + **`scripts/gen-dev-cert.sh`**, and open the firewall for **3000/tcp**.
- **Webpack vs Turbopack:** default `npm run dev` uses webpack; `npm run dev:turbo` for Turbopack if you prefer.

## Design

- **`_blueprints/design_system.md`** — Dark Node palette, typography, glass rules.
- **`src/app/globals.css`** — Tailwind v4 `@theme` tokens; ThemeEngine `--spirit-*` vars per `data-theme`.

## Backend

See `backend/docker-compose.yml` and `backend/README.md` for Ollama / voice services.
