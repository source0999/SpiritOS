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

# Certs for dev:https:lan — run once if ./certificates/spirit-dev*.pem are missing (see “Tailscale / LAN dev” below)
# SPIRIT_TLS_EXTRA_HOSTS=10.0.0.186,100.111.32.31 bash scripts/gen-dev-cert.sh

# Next HTTPS dev on 0.0.0.0 (LAN/Tailscale — generate certs once; see “Tailscale / LAN dev” below)
npm run dev:https:lan
```

**Optional — Docker backends first, then same HTTPS dev:** `npm run dev:all:https:lan` (or run `(cd backend && docker compose up -d)` yourself, then `npm run dev:https:lan`).

**Health check (Ollama probe + server-derived diagnostics):**

```bash
curl -k -sS https://localhost:3000/api/spirit/health
```

**Brain vs TTS (do not conflate them):** `/api/spirit` uses `OLLAMA_MODEL` for `/chat` text generation. `/oracle` can use `ORACLE_OLLAMA_MODEL` when set. Voice is synthesized via same-origin **`/api/tts`** (`TTS_PROVIDER=piper` or `elevenlabs`); the browser never sees `ELEVENLABS_API_KEY`. Optional `ELEVENLABS_VOICE_SPEED` (default 1.12, clamped 0.7–1.2) sets ElevenLabs cadence; Voice settings can send a per-request `speed` override. **`GET /api/tts/voices`** feeds the Voice picker. **`ELEVENLABS_VOICE_ALLOWLIST`** supports **`Clarice:voice_id`** (recommended, no catalog read) or comma-separated **names only** (needs catalog + `voices_read`; if the catalog fails, switch to `Name:voice_id`). When any allowlist is set, the API returns **only** those voices—never the full catalog. Defaults prefer **`ELEVENLABS_DEFAULT_VOICE_ID`**, then **Clarice** by name, then **`ELEVENLABS_VOICE_ID`**. Response **`X-Spirit-TTS-Voice-Name-Encoded`** keeps display names ASCII-safe for Tailscale.

**Prompt 10B / 10C-C / 10D-F:** Mode presets + **response token caps** (Sassy/Brutal/Peer stay short on casual prompts). **`/oracle`** adds a **voice surface** layer on top of the same modes (`buildRuntimeSurfaceInstruction`) — live spoken context, not coding-default; tighter caps apply only when `runtimeSurface=oracle`. **Deep think** and **Web search** prefs live under the `/chat` composer (`localStorage` key `spirit:threadUiPrefs:v2`; Researcher web defaults **ON** with tri-state `unset|enabled|disabled` — legacy `o:true` migrates to disabled). Assistant text passes **`sanitizeAssistantVisibleText`** before render, copy, TTS, and Dexie persist — strips `<think>` / leaked mode-contract lines. Researcher gets **source enforcement**: no fake `[n]` citations or Sources sections when search returned no verified `http(s)` URLs; `/api/spirit` adds `x-spirit-source-count`, `x-spirit-search-provider`, `x-spirit-search-status`, **`x-spirit-runtime-surface`**. Teacher + **Web search on** + educational prompts can prefetch OpenAI web for real **Study aids** links; otherwise **Study aids to search** (quoted phrases, no invented URLs). Research plan panel + workflow visualizer clear on thread/draft switch and sit **above** the composer; visualizer has a **compact** idle line after dismiss on casual modes.

**Routes**

| Path | Purpose |
|------|---------|
| `/` | Dashboard hub ((dashboard) group — URL stays `/`) — homelab widgets use live **`/api/telemetry/cluster`** where configured. |
| `/chat` | Saved-thread workspace (Dexie), mode runtime v2 (**Peer** + profiles), local search/pins, Activity + Spirit Profile panels. Capability questions can receive **deterministic** answers from the live registry via **`/api/spirit`** (hardware, storage, model/runtime, limits). |
| `/oracle` | Oracle Voice MVP — **hands-free session**, ephemeral (no saved threads), **`runtimeSurface=oracle`** + **Oracle voice surface prompt** (Prompt 10D-F), **Whisper** via **`/api/stt/transcribe`** + MediaRecorder + amplitude VAD auto-stop + text fallback. Visual layer (orb / transcript / visualizer) in progress; **full page design pass still TODO**. (`_blueprints/oracle_voice_mvp.md`) |
| `/design-demo` | Sandboxed **visual-only** command-center preview — does not wire production APIs. (`_blueprints/design_demo.md`) |

### Telemetry & capability APIs (read-first)

| Endpoint | Role |
|----------|------|
| **`GET /api/telemetry/cluster`** | Aggregates configured nodes (e.g. Spirit Dell + **`SPIRITDESKTOP_TELEMETRY_URL`**) for dashboard cards. |
| **`GET /api/telemetry/self`** | Same schema when served by a node/agent (e.g. **`scripts/spiritdesktop-windows/agent.js`** on LAN). |
| **`GET /api/telemetry/capabilities`** | Read-only **capability registry** JSON for UI and deterministic chat answers. |

**Not wired yet:** chat UI cannot browse arbitrary folders; **app-level SSH execution** is not integrated (manual SSH outside the app is fine). See **Next Work Order** below.

## Current Checkpoint

- **Dashboard / homelab telemetry is live** — cluster polling via **`/api/telemetry/cluster`** with CPU/RAM/storage when collectors respond.
- **Cluster telemetry** can include **Spirit Dell** and **spiritdesktop** when endpoints and env are configured (Windows agent exposes **`/api/telemetry/self`**).
- **Local and remote storage** surface through telemetry payloads **where the agent/OS exposes them** (e.g. Windows logical disks via the desktop agent).
- **Capability registry** exists at **`/api/telemetry/capabilities`** (read-only).
- **`/api/spirit`** can answer **deterministic** capability questions from that registry — hardware, storage, model/runtime, “C: drive” visibility, file-access boundaries, SSH boundaries, and general capabilities — without hallucinating layout when the registry has the facts.
- **Oracle Voice MVP** is in place: STT + **`/api/spirit`** + TTS, with text fallback; hands-free loop per **`_blueprints/oracle_voice_mvp.md`**.
- **Chat + Oracle tone** — normal dating/social advice stays in scope; **consent and safety boundaries** remain enforced (Hermes/Oracle behavior refined; not a license to ignore policy).
- **Oracle visuals** — orb / fairy / visualizer direction has started; **`/oracle` still needs a full design-system pass** (polish backlog).
- **Manual Dell → desktop SSH** exists **outside** the app; **in-app SSH tools / execution are not wired** yet.
- **File/folder browsing from chat** is **not** wired yet.
- **Project / progress tracker** — **planned**, not implemented (see **`_blueprints/progress_tracker_roadmap.md`**).

## Where I Left Off

- **UI polish** — lots of small fixes remain across dashboard, chat, Oracle.
- **`/oracle` full page design** — not finished; align with **`_blueprints/design_demo.md`** patterns when ready.
- **Sitewide iOS/Android responsiveness** — needs a focused pass (breakpoints, touch, safe areas).
- **Personality / profile** — clearer settings, memory hygiene, and separation of “test chat” vs real personalization.
- **Progress tracker / project tracker** — next **major product** feature after docs stabilize; read-only discovery before any writes.
- **Safe tooling phase** — **read-only project discovery** from configured roots first — not write/edit/delete.
- **SSH command execution** — stays **later**, behind explicit **approval gates**.

## Next Work Order

**P0 — now**

- Land this checkpoint (commit + stabilize).
- **`npm run typecheck`** + **`npm test -- --run`** + **`npm run lint`** on clean intent.
- Confirm **no secrets** and **no junk** in the commit (no `.env.local`, no certs, no accidental huge artifacts).

**P1**

- **`/oracle`** — full design pass (layout, density, motion, states).
- **Mobile-first responsive pass** across dashboard / chat / Oracle (360 / 375 / 768 / 1024).
- **Personality / profile cleanup** and **memory hygiene**.
- **Progress tracker** — roadmap + data model (**`_blueprints/progress_tracker_roadmap.md`**).

**P2**

- Read-only **project discovery** (allowed roots only).
- **`SPIRIT_PROJECT_PATH`** parsing + project scan.
- **Git status** signals for the tracker (read-only at first).
- **Capability-aware** dashboard cards.

**P3**

- Approval queue UX.
- Read-only filesystem tools (scoped roots).
- **SSH command** tool behind explicit approval.
- File write/move/edit with **diff preview** + audit trail.

## Validation

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

- **Port / HTTPS:** default local dev is **`npm run dev:https:lan`** (port **3000**, `0.0.0.0` bind). For **Oracle mic from another machine**, use **`dev:https:lan`** + **`scripts/gen-dev-cert.sh`**, and open the firewall for **3000/tcp**. Use `npm run dev -- -p 3000` only if you need plain HTTP on a fixed port.
- **Webpack vs Turbopack:** default `npm run dev` uses webpack; `npm run dev:turbo` for Turbopack if you prefer.

## Design

- **`_blueprints/design_system.md`** — Dark Node palette, typography, glass rules.
- **`_blueprints/design_demo.md`** — art-direction sandbox; future **production** responsive targets called out there and in the design system.
- **`_blueprints/progress_tracker_roadmap.md`** — **planned** in-app project/progress tracker (not shipped yet).
- **`src/app/globals.css`** — Tailwind v4 `@theme` tokens; ThemeEngine `--spirit-*` vars per `data-theme`.

## Backend

See `backend/docker-compose.yml` and `backend/README.md` for Ollama / voice services.
