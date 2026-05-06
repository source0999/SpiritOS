# Basic Chat + Voice QA (Prompt 9L)

Manual checks before you ship another “mobile glow-up”. Dexie is **local-only** - no cross-device sync yet; each browser has its own threads.

## Per-origin storage (LAN vs Tailscale)

`http://10.0.0.186:3000` and `http://100.111.32.31:3000` are **different origins**. Each has its own **localStorage**, **IndexedDB/Dexie** (saved threads), **theme**, **voice / TTS settings**, and dashboard prefs. In **development**, the dashboard diagnostics sheet shows an **Origin** row as a reminder. There is no server-backed sync between origins.

## Environment

- **Tailscale / LAN dev:** set `NEXT_ALLOWED_DEV_ORIGINS` in `.env.local` (comma-separated **hostnames** only, no `http://`). Restart `npm run dev` after any change - `next.config.ts` reads this at process start.
- **ElevenLabs:** `ELEVENLABS_API_KEY`, **`ELEVENLABS_DEFAULT_VOICE_ID`** + **`ELEVENLABS_DEFAULT_VOICE_NAME`** (recommended defaults), `TTS_PROVIDER=elevenlabs`.
- **Voice allowlist:** **`Clarice:voice_id,Charlotte:voice_id`** (explicit - works without catalog). **Name-only** `Charlotte,Clarice,…` needs catalog + `voices_read`; if catalog fails, use explicit `Name:voice_id` or JSON allowlist. **`ELEVENLABS_VOICE_ALLOWLIST_JSON`** wins if both comma and JSON are set.

## Checklist

### Local desktop `/chat`

- [ ] Page loads without console spam from blocked `/_next/webpack-hmr`.
- [ ] **New Chat** clears the canvas and opens a draft lane.
- [ ] Composer accepts typing; **Enter** sends (Shift+Enter newline).
- [ ] Assistant streams and final message appears.
- [ ] Thread title / messages persist after refresh (same browser).

### LAN desktop `/chat`

- [ ] Open dev server via LAN hostname or IP (e.g. `http://10.0.0.186:3000/chat`).
- [ ] HMR not blocked if that host is in `NEXT_ALLOWED_DEV_ORIGINS`.
- [ ] Same composer + send + persistence as local.

### Tailscale `/chat`

- [ ] Open via Tailscale hostname (e.g. `*.ts.net` or IP in allowlist).
- [ ] No stuck overlay; composer focus works.
- [ ] New Chat + send + persistence.
- [ ] **TTS (Prompt 9K):** open `/chat` (e.g. `http://100.111.32.31:3000/chat`), open Voice settings, pick a voice, **Speak** - no Internal Server Error on `/api/tts`; DevTools → Network shows chosen `voice_id` in the ElevenLabs request path when provider is ElevenLabs.
- [ ] With **Auto-speak** on, send a new prompt while audio plays - old audio stops and the latest assistant reply speaks.

### iPhone Safari `/chat`

- [ ] Threads drawer + composer usable.
- [ ] **Voice** sheet opens; **Enable audio** if TTS is silent.

### Voice

- [ ] Voice settings open (desktop: portal panel not clipped; min usable width ~420px).
- [ ] `GET /api/tts/voices` returns voices or a **clear** warning + **Retry** (allowlist-only 200 is OK if catalog is blocked).
- [ ] Select a voice; **Speak** uses that voice (check “Last session” + debug line / network URL contains chosen `voice_id`).
- [ ] **Auto-speak** on: new prompt stops old audio; latest assistant reply speaks (desktop + mobile).
- [ ] **Stop** halts playback.

### Routes

- [ ] `/` dashboard hub.
- [ ] `/oracle` loads and chats.
- [ ] `/design-demo` loads (optional); **`/quarantine` is not a current App Router page** - skip until reintroduced.
- [ ] **Prompt 10C-C:** Sassy/Brutal stay short; assistant never shows `<think>` or mode-contract leaks; Researcher web defaults ON; turning web OFF yields **no** fake Sources/`[1]` citations; Teacher educational + web on returns real links or **Study aids to search**; research plan panel closes on thread/new chat/mode away; workflow rail compact above composer after dismiss on casual chats.

## Limitations (current)

- **Dexie:** local-only persistence; no server-backed cross-device sync.
- **STT / mic:** not in scope for this checklist.
- **Hydration warnings:** browser extensions that inject attributes (`bis_register`, `__processed`, etc.) are noise - if you see hydration mismatch spam, retry in a clean profile or private window before chasing app bugs.

## After env changes

Always **restart** the Next dev server (`npm run dev` or `npm run dev:all`) so `next.config.ts` and server env are re-read.
