# Spirit OS

**Sovereign cybernetic extension of the Source** - Next.js 16 App Router frontend (`src/`) + local GPU backend (Ollama, Whisper, Piper TTS).

## Worktree and host orientation

Read [`AGENTS.md`](AGENTS.md) before editing. [`docs/dev-setup/worktree-manifest.md`](docs/dev-setup/worktree-manifest.md) is the authoritative live topology: verify the selected worktree, branch, HEAD, and status instead of relying on this README for a path snapshot.

The SpiritFlix checkout is visible from Linux at `/home/source/SpiritOS` and Windows over SMB as `Z:\`; it does not own managed production services. The authoritative Source Proxy checkout owns backend `8787`, HTTPS frontend `3000`, and its Next worker `3002`. Obtain its current path from the manifest, verify each process CWD and health live, and use SSH to the Dell for Linux-only paths, archives, and process state. See [`cross-platform-repository-verification.md`](docs/dev-setup/cross-platform-repository-verification.md) for the operational commands.

## Active Plan

The active Source Proxy plan is `docs/source-proxy-production-hardening-plan.md`.
`proxyCLI.md` is retired and intentionally deleted. Phase 11, AionUi bridge, and Spirit Cowork Console language is historical or deferred unless a later active plan explicitly reopens it.

## LLM Context Packs / Repomix + Headroom

ChatGPT and other external LLM sessions cannot see this repository directly. When asking for outside review, generate a focused context pack and upload that XML instead of uploading a raw full-repo bundle. Raw full-repo packs can drag in stale plans, receipt sludge, evidence directories, backend volumes, generated artifacts, and media-adjacent noise that make review slower and easier to misread.

Generated XMLs intended for upload are written to the selected checkout root. They should remain untracked. Context-pack commands may also create ignored `repomix-output*.xml` intermediates; those are verifier/runtime artifacts, not commit targets. The context-generation scripts may use an isolated Repomix CLI fallback for pack export robustness only; this does not change Source Proxy production runtime, decision logic, API behavior, model routing, SpiritFlix, media, or Jellyfin behavior.

Headroom is active only when the generated XML metadata shows both `compressed="true"` and `tokens_saved` greater than `0`. Tree-sitter Repomix compression by itself is usable, but it is not Headroom compression. If Headroom is unreachable, or if it reports zero savings, treat the pack as Tree-sitter-only and do not claim Headroom was active.

Pack names and intended review scope:

| Pack | File | Use for |
| --- | --- | --- |
| Quick repo map pack | `repo-map-context.xml` | Repo/docs overview, README/config orientation, and high-level cleanup review. |
| Source Proxy / coding lane pack | `source-proxy-context.xml` | Source Proxy, `/coding`, worker, context, and coding-lane review. |
| Source Proxy minimal pack | `source-proxy-min-context.xml` | Existing focused Source Proxy/coding profile from `npm run context:source-proxy-min`. |
| Frontend pack | `frontend-context.xml` | Frontend app/lib/components review only. |
| SpiritFlix/media code pack | `spiritflix-media-code-context.xml` | SpiritFlix/media code only; media files are excluded. |
| Docs/plans pack | `docs-plans-context.xml` | Plans, breakpoints, roadmaps, audits, and cleanup history. |

Use these single-pack commands when you only need one review surface:

```bash
cd "$(git rev-parse --show-toplevel)"

# quick repo map pack
npm run context:repo-map

# Source Proxy / coding lane minimal pack
HEADROOM_PORT=8798 \
HEADROOM_BASE_URL=http://127.0.0.1:8798 \
HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom \
npm run context:source-proxy-min

# verify the Source Proxy minimal pack and Headroom metadata
HEADROOM_PORT=8798 \
HEADROOM_BASE_URL=http://127.0.0.1:8798 \
HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom \
npm run context:verify
```

Use this all-packs command when a secondary reviewer needs several surfaces. It installs an isolated Repomix runner under `/tmp`, excludes evidence/media/runtime sludge, and writes uploadable XMLs into `/home/source/SpiritOS/`:

```bash
bash -lc '
set -euo pipefail

WORK="$(git rev-parse --show-toplevel)"
OUT="$WORK"
TMP="/tmp/spiritos-repomix-bin-20260623"

cd "$WORK"

export HEADROOM_PORT=8798
export HEADROOM_BASE_URL="http://127.0.0.1:8798"
export HEADROOM_BIN="/home/source/SpiritOS/.venv-headroom/bin/headroom"

echo "=== installing isolated repomix runner in $TMP ==="
rm -rf "$TMP"
mkdir -p "$TMP"
npm --prefix "$TMP" install repomix@1.14.0 >/tmp/spiritos-repomix-install.log 2>&1
REPOMIX="$TMP/node_modules/.bin/repomix"
CONFIG="$TMP/repomix-focused.config.json"
cat > "$CONFIG" <<JSON
{
  "input": { "maxFileSize": 2000000 },
  "output": {
    "style": "xml",
    "parsableStyle": true,
    "compress": true,
    "fileSummary": true,
    "directoryStructure": true,
    "files": true,
    "truncateBase64": true,
    "topFilesLength": 10,
    "git": {
      "sortByChanges": true,
      "sortByChangesMaxCommits": 100,
      "includeDiffs": false,
      "includeLogs": false
    }
  },
  "ignore": {
    "useGitignore": true,
    "useDotIgnore": true,
    "useDefaultPatterns": true,
    "customPatterns": []
  },
  "security": { "enableSecurityCheck": true },
  "tokenCount": { "encoding": "o200k_base" }
}
JSON

COMMON_IGNORE="node_modules/**,.git/**,.next/**,dist/**,out/**,build/**,coverage/**,**/.venv/**,**/venv/**,**/__pycache__/**,**/*.pyc,**/*.sqlite,**/*.db,**/*.log,repomix-output*.xml,*context.xml,docs/evidence/**,docs/handoff/**,backend/searxng_data/**,backend/volumes/**,services/jellyfin/**,scripts/media/*.json,scripts/media/model_gallery/**,**/*.{mp4,mkv,mov,m4v,ts,mp3,wav,flac,jpg,jpeg,png,webp,gif,heic,zip,tar,gz,7z}"

make_pack () {
  NAME="$1"
  INCLUDE="$2"
  FINAL="$OUT/${NAME}.xml"
  echo ""
  echo "=== PACK: $NAME ==="
  rm -f "$FINAL"
  "$REPOMIX" . \
    --config "$CONFIG" \
    --compress \
    --include "$INCLUDE" \
    --ignore "$COMMON_IGNORE" \
    --output "$FINAL"
  echo "=== wrote ==="
  ls -lh "$FINAL"
  echo "=== metadata ==="
  grep -Ei "headroom|compressed|compression|tokens_saved|fallback|source_context_bundle|repomix" "$FINAL" | head -40 || true
}

make_pack "repo-map-context" "README.md,package.json,repomix*.config.json,.repomixignore,docs/**/*.md,docs/**/*.json,_blueprints/**"
make_pack "source-proxy-context" "source_proxy/**,scripts/context/**,scripts/source-proxy-*.mjs,scripts/source-proxy-*.sh,scripts/headroom-proxy-dev.sh,scripts/source-context-compress.mjs,scripts/repomix-llm.mjs,src/app/coding/**,src/components/coding/**,src/lib/coding/**,src/app/v1/**,src/app/api/coding/**,src/lib/mac-worker/**,scripts/mac-worker/**"
make_pack "frontend-context" "src/app/**,src/components/**,src/lib/**,package.json,tsconfig.json,next.config.*"
make_pack "spiritflix-media-code-context" "src/app/spiritflix/**,src/components/spiritflix/**,src/app/api/spiritflix/**,src/lib/spiritflix/**,src/lib/media/**,scripts/media/**/*.py,scripts/media/**/*.mjs,scripts/media/**/*.sh,services/jellyfin/**/*.md,services/jellyfin/**/*.yml,services/jellyfin/**/*.yaml"
make_pack "docs-plans-context" "docs/**/*.md,docs/**/*.json,_blueprints/**"

echo ""
echo "=== DONE: visible packs in $OUT ==="
ls -lh "$OUT"/repo-map-context.xml \
       "$OUT"/source-proxy-context.xml \
       "$OUT"/frontend-context.xml \
       "$OUT"/spiritflix-media-code-context.xml \
       "$OUT"/docs-plans-context.xml

echo ""
echo "Upload these as needed:"
echo "$OUT/repo-map-context.xml"
echo "$OUT/source-proxy-context.xml"
echo "$OUT/frontend-context.xml"
echo "$OUT/spiritflix-media-code-context.xml"
echo "$OUT/docs-plans-context.xml"
'
```

## Authorized Media Importer

SpiritOS includes a dedicated `/converter` route for authorized media imports. It is for Britton-owned content or content where Britton has documented written permission/license rights; it is not a public YouTube downloader.

The converter writes under the Dell output roots:

- `/mnt/spirit-8tb/converter/authorized-imports`
- `/mnt/spirit-8tb/converter/audio`
- `/mnt/spirit-8tb/converter/transcripts`
- `/mnt/spirit-8tb/converter/knowledge`
- `/mnt/spirit-8tb/converter/logs`

Use `/converter` to paste many YouTube URLs, local file paths, a local media folder path, or a manual transcript. YouTube URL jobs require the ownership/license checkbox before they can be queued, and the job stores the authorization note/proof metadata with the resulting artifacts. Local files do not require the YouTube authorization gate.

The queue validates the batch first and processes one item at a time by default. Pause, resume, cancel, active job details, completed outputs, and redacted diagnostics are available from the page. Local media conversion uses `ffmpeg` when present; authorized YouTube imports use `yt-dlp` when present. If a speech-to-text engine is not configured, audio jobs are left in `pending_transcription_engine` with transcript, summary, chunk, metadata, and knowledge-record paths prepared as far as possible.

This pass intentionally does not merge imported assets into ytmclone playback, the 999Playr local library, SpiritOS tracking, or custom feeds.

## Quick Start (Recommended)

```bash
cd /home/source/SpiritOS

# Env templates → working copies
cp .env.local.example .env.local
cp backend/.env.example backend/.env

npm install

# Backend stack (compose lives under backend/)
(cd backend && docker compose up -d)

# On the machine running Ollama - pull the chat model used by `/api/spirit`
ollama pull hermes4

# Certs for dev:https:lan - run once if ./certificates/spirit-dev*.pem are missing (see “Tailscale / LAN dev” below)
# SPIRIT_TLS_EXTRA_HOSTS=10.0.0.186,100.111.32.31 bash scripts/gen-dev-cert.sh

# Terminal 1: Next HTTPS visual app on 0.0.0.0:3000
# LAN/Tailscale - generate certs once; see “Tailscale / LAN dev” below.
npm run dev:https:lan

# Terminal 2: Source proxy HTTPS API on 0.0.0.0:8787
# First run only on a new Linux host: npm run proxy:bootstrap
npm run proxy:https:lan
```

**Optional - Docker backends first, then same HTTPS dev:** `npm run dev:all:https:lan` (or run `(cd backend && docker compose up -d)` yourself, then `npm run dev:https:lan`).

**Health check (Ollama probe + server-derived diagnostics):**

```bash
curl -k -sS https://localhost:3000/api/spirit/health
```

**Source proxy health check (VRAM diagnostics):**

```bash
curl -k -sS https://localhost:8787/healthcheck
```

Hermes 4 is the default local intelligence model for SpiritOS chat and Source Proxy local routing. The expected local IDs are `hermes4:latest` and `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`; keep `hermes3:8b-abliterated` available as the fast `/oracle`/voice-friendly fallback and keep `qwen2.5-coder:7b` selectable for explicit coding experiments. If Ollama models are intended to live on the 8TB drive, verify `OLLAMA_MODELS` or the Ollama service/home symlink resolves to `/mnt/spirit-8tb/ollama-models` before calling storage configured.

### Local HTTPS LAN Dev Servers

SpiritOS uses two local HTTPS LAN dev servers during normal development.

Frontend UI:

- Purpose: SpiritOS UI, dashboard, `/coding`, `/chat`, `/scout`, `/oracle`
- Session: `spiritos-lan`
- Script: `npm run dev:https:lan`
- Port: `3000`
- Log: `~/spiritos-dev-lan.log`
- Watchdog log: `~/spiritos-dev-lan-watchdog.log`
- URL: `https://10.0.0.186:3000/coding`

Source Proxy:

- Purpose: backend source proxy used by `/coding` workflows
- Session: `source-proxy-lan`
- Script: `npm run proxy:https:lan`
- Port: `8787`
- Log: `~/source-proxy-https-lan.log`

Use detached tmux sessions so the servers survive Cursor Remote or SSH disconnects. Normal code edits usually hot reload and do not require restarting either server. Restart mainly after `.env.local`, config, certificates, server scripts, dependency/package changes, or when compile/cache state gets stuck.

RustDesk is currently intentionally left off during stability testing. Sleep/suspend has been disabled on the server.

Start both servers:

```bash
cd ~/SpiritOS

tmux kill-session -t spiritos-lan 2>/dev/null || true
tmux kill-session -t source-proxy-lan 2>/dev/null || true

tmux new -d -s source-proxy-lan 'cd ~/SpiritOS && npm run proxy:https:lan 2>&1 | tee -a ~/source-proxy-https-lan.log'
tmux new -d -s spiritos-lan 'cd ~/SpiritOS && npm run dev:https:lan:watch'

sleep 25

tmux ls || true
ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
curl -k -I --max-time 10 https://localhost:3000/coding || true
```

Stop both servers:

```bash
cd ~/SpiritOS

tmux kill-session -t spiritos-lan 2>/dev/null || true
tmux kill-session -t source-proxy-lan 2>/dev/null || true

lsof -ti tcp:3000 2>/dev/null | xargs -r kill -TERM
lsof -ti tcp:8787 2>/dev/null | xargs -r kill -TERM

sleep 3

lsof -ti tcp:3000 2>/dev/null | xargs -r kill -KILL
lsof -ti tcp:8787 2>/dev/null | xargs -r kill -KILL

tmux ls || true
ss -ltnp | grep -E ':3000|:8787' || true
```

Clean restart both servers:

```bash
cd ~/SpiritOS

tmux kill-session -t spiritos-lan 2>/dev/null || true
tmux kill-session -t source-proxy-lan 2>/dev/null || true

lsof -ti tcp:3000 2>/dev/null | xargs -r kill -TERM
lsof -ti tcp:8787 2>/dev/null | xargs -r kill -TERM

sleep 3

lsof -ti tcp:3000 2>/dev/null | xargs -r kill -KILL
lsof -ti tcp:8787 2>/dev/null | xargs -r kill -KILL

rm -rf .next

tmux new -d -s source-proxy-lan 'cd ~/SpiritOS && npm run proxy:https:lan 2>&1 | tee -a ~/source-proxy-https-lan.log'
tmux new -d -s spiritos-lan 'cd ~/SpiritOS && npm run dev:https:lan:watch'

sleep 30

tmux ls || true
ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
curl -k -I --max-time 10 https://localhost:3000/coding || true
```

Clean restart kills tmux sessions and any orphan processes on ports `3000` and `8787` before starting fresh tmux sessions. Plain `tmux kill-session` is not always enough because the frontend can leave orphan Next processes on port `3000`.

Restart frontend only (leaves Source Proxy `:8787` and SpiritFlix `:3001` untouched):

```bash
cd ~/SpiritOS
npm run lan:restart
```

Manual equivalent:

```bash
cd ~/SpiritOS

tmux kill-session -t spiritos-lan 2>/dev/null || true

lsof -ti tcp:3000 2>/dev/null | xargs -r kill -TERM
sleep 3
lsof -ti tcp:3000 2>/dev/null | xargs -r kill -KILL

rm -rf .next

tmux new -d -s spiritos-lan 'cd ~/SpiritOS && npm run dev:https:lan:watch'

sleep 25

tmux ls || true
ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
curl -k -I --max-time 10 https://localhost:3000/coding || true
```

Restart proxy only:

```bash
cd ~/SpiritOS

tmux kill-session -t source-proxy-lan 2>/dev/null || true

lsof -ti tcp:8787 2>/dev/null | xargs -r kill -TERM
sleep 3
lsof -ti tcp:8787 2>/dev/null | xargs -r kill -KILL

tmux new -d -s source-proxy-lan 'cd ~/SpiritOS && npm run proxy:https:lan 2>&1 | tee -a ~/source-proxy-https-lan.log'

sleep 8

tmux ls || true
ss -ltnp | grep -E ':8787|:22|:11434' || true
curl -k --max-time 10 https://localhost:8787/v1/self/status | head -c 800
echo
```

Verify both servers:

```bash
cd ~/SpiritOS

echo "== tmux =="
tmux ls || true

echo
echo "== ports =="
ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true

echo
echo "== frontend =="
curl -k -I --max-time 10 https://localhost:3000/ || true
curl -k -I --max-time 10 https://localhost:3000/coding || true

echo
echo "== frontend self status route =="
curl -k -s --max-time 10 https://localhost:3000/v1/self/status | head -c 800
echo

echo
echo "== proxy self status =="
curl -k -s --max-time 10 https://localhost:8787/v1/self/status | head -c 800
echo
```

Watch frontend logs:

```bash
tail -f ~/spiritos-dev-lan.log
```

Watch proxy logs:

```bash
tail -f ~/source-proxy-https-lan.log
```

Attach to frontend tmux session:

```bash
tmux attach -t spiritos-lan
```

Attach to proxy tmux session:

```bash
tmux attach -t source-proxy-lan
```

Detach from tmux without killing the server:

```text
Ctrl+b then d
```

Open in browser:

```text
https://10.0.0.186:3000/
https://10.0.0.186:3000/coding
```

If the browser shows a white page after restart, hard refresh:

```text
Ctrl+Shift+R
```

Windows PowerShell verification:

```powershell
ssh spirit "tmux ls || true"
ssh spirit "ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true"
curl.exe -k -I https://10.0.0.186:3000/coding
Test-NetConnection 10.0.0.186 -Port 3000
Test-NetConnection 10.0.0.186 -Port 8787
```

Expected good output:

- `tmux` shows `spiritos-lan` and `source-proxy-lan`.
- `ss` shows `0.0.0.0:3000` for the frontend.
- `ss` shows `0.0.0.0:8787` for the proxy.
- `curl` to `https://localhost:3000/` returns `HTTP/1.1 200 OK` (watchdog health probe).
- `curl` to `https://localhost:3000/coding` returns `HTTP/1.1 200 OK`.
- The browser opens `https://10.0.0.186:3000/coding` after a hard refresh if needed.

### Runtime lane audit (when :3000 / :8787 / :3001 feel down or slow)

Quick audit on the Dell:

```bash
cd ~/SpiritOS
npm run lanes:audit
```

Common causes seen on the headless box:

- **Watchdog restart churn** on `:3000` when Next is still compiling or swap is full. The LAN watchdog now probes `https://127.0.0.1:3000/` (not `/coding`), waits longer before health checks, and only clears `.next` cache every 3rd restart instead of every loop.
- **Orphan `next-server` processes** on smoke ports `3020/3030` or stray dev ports like `3027` eating RAM. Smoke/admin dev must stay on `npm run spiritflix:admin:dev` and be stopped with `npm run spiritflix:admin:dev:stop`.
- **Swap exhaustion** (4G swap full) makes all three lanes feel hung. Check `free -h`; pause heavy ffmpeg/media-ingest work if lanes need to stay responsive.

Per-lane restarts (safe, tmux-managed):

```bash
npm run lan:restart                 # SpiritOS HTTPS UI :3000 only
npm run proxy:lan:restart           # Source Proxy :8787 only (now watchdog-wrapped)
npm run spiritflix:stable:restart   # SpiritFlix stable sidecar :3001 only
```

Watchdog logs:

```text
~/spiritos-dev-lan-watchdog.log
~/source-proxy-lan-watchdog.log
~/spiritflix-stable-3001-watchdog.log
```

**Brain vs TTS (do not conflate them):** `/api/spirit` uses `OLLAMA_MODEL` for `/chat` text generation. `/oracle` can use `ORACLE_OLLAMA_MODEL` when set. Voice is synthesized via same-origin **`/api/tts`** (`TTS_PROVIDER=piper` or `elevenlabs`); the browser never sees `ELEVENLABS_API_KEY`. Optional `ELEVENLABS_VOICE_SPEED` (default 1.12, clamped 0.7–1.2) sets ElevenLabs cadence; Voice settings can send a per-request `speed` override. **`GET /api/tts/voices`** feeds the Voice picker. **`ELEVENLABS_VOICE_ALLOWLIST`** supports **`Clarice:voice_id`** (recommended, no catalog read) or comma-separated **names only** (needs catalog + `voices_read`; if the catalog fails, switch to `Name:voice_id`). When any allowlist is set, the API returns **only** those voices - never the full catalog. Defaults prefer **`ELEVENLABS_DEFAULT_VOICE_ID`**, then **Clarice** by name, then **`ELEVENLABS_VOICE_ID`**. Response **`X-Spirit-TTS-Voice-Name-Encoded`** keeps display names ASCII-safe for Tailscale.

**Prompt 10B / 10C-C / 10D-F:** Mode presets + **response token caps** (Sassy/Brutal/Peer stay short on casual prompts). **`/oracle`** adds a **voice surface** layer on top of the same modes (`buildRuntimeSurfaceInstruction`) - live spoken context, not coding-default; tighter caps apply only when `runtimeSurface=oracle`. **Deep think** and **Web search** prefs live under the `/chat` composer (`localStorage` key `spirit:threadUiPrefs:v2`; Researcher web defaults **ON** with tri-state `unset|enabled|disabled` - legacy `o:true` migrates to disabled). Assistant text passes **`sanitizeAssistantVisibleText`** before render, copy, TTS, and Dexie persist - strips `<think>` / leaked mode-contract lines. Researcher gets **source enforcement**: no fake `[n]` citations or Sources sections when search returned no verified `http(s)` URLs; `/api/spirit` adds `x-spirit-source-count`, `x-spirit-search-provider`, `x-spirit-search-status`, **`x-spirit-runtime-surface`**. Teacher + **Web search on** + educational prompts can prefetch provider-router web sources for real **Study aids** links; otherwise **Study aids to search** (quoted phrases, no invented URLs). Research plan panel + workflow visualizer clear on thread/draft switch and sit **above** the composer; visualizer has a **compact** idle line after dismiss on casual modes.

**Local-first web search env:** `/api/research/web-search` and `/api/spirit` Researcher/Teacher prefetch use the provider router. Server web search is disabled by default with `WEB_SEARCH_ENABLED=false`. The default provider order is `WEB_SEARCH_PROVIDER_ORDER=cache,searxng`; set `SEARXNG_URL=http://127.0.0.1:8080` when the optional local SearXNG profile is running. Direct page fetch is not in the default ladder and requires `WEB_SEARCH_FETCH_PAGE_ENABLED=true`. Its robots handling is conservative best-effort, not full RFC 9309 compliance: a 4xx `/robots.txt` response is treated as no policy found, while 5xx, network errors, and timeouts block direct fetch. Paid OpenAI fallback stays off with `WEB_SEARCH_PAID_FALLBACK_ENABLED=false` and requires explicit approval via `WEB_SEARCH_PAID_FALLBACK_REQUIRES_APPROVAL=true`.

**Optional local SearXNG:** disabled by default. Start it only when you want local/free search:

```bash
cd backend
docker compose --profile local-search up -d searxng
curl "http://127.0.0.1:8080/search?q=test&format=json"
```

If the curl response is HTML instead of JSON, check `backend/searxng.yml` and confirm `search.formats` includes `json`, then restart SearXNG.

**Routes**

| Path | Purpose |
|------|---------|
| `/` | Dashboard hub ((dashboard) group - URL stays `/`) - homelab widgets use live **`/api/telemetry/cluster`** where configured. |
| `/chat` | Saved-thread workspace (Dexie), mode runtime v2 (**Peer** + profiles), local search/pins, Activity + Spirit Profile panels. Capability questions can receive **deterministic** answers from the live registry via **`/api/spirit`** (hardware, storage, model/runtime, limits). |
| `/oracle` | Oracle Voice MVP - **hands-free session**, ephemeral (no saved threads), **`runtimeSurface=oracle`** + **Oracle voice surface prompt** (Prompt 10D-F), **Whisper** via **`/api/stt/transcribe`** + MediaRecorder + amplitude VAD auto-stop + text fallback. Visual layer (orb / transcript / visualizer) in progress; **full page design pass still TODO**. (`_blueprints/oracle_voice_mvp.md`) |
| `/design-demo` | Sandboxed **visual-only** command-center preview - does not wire production APIs. (`_blueprints/design_demo.md`) |

### Telemetry & capability APIs (read-first)

| Endpoint | Role |
|----------|------|
| **`GET /api/telemetry/cluster`** | Aggregates configured nodes (e.g. Spirit Dell + **`SPIRITDESKTOP_TELEMETRY_URL`**) for dashboard cards. |
| **`GET /api/telemetry/self`** | Same schema when served by a node/agent (e.g. **`scripts/spiritdesktop-windows/agent.js`** on LAN). |
| **`GET /api/telemetry/capabilities`** | Read-only **capability registry** JSON for UI and deterministic chat answers. |

**Not wired yet:** app-level SSH execution is not integrated (manual SSH outside the app is fine). See **Next Work Order** below.

### Windows desktop agent: telemetry + scoped `C:\Projects` file access

Spirit chat can list an allowlisted Windows folder through `scripts/spiritdesktop-windows/agent.js`. The verified prompt was `whats in my c/projects folder?`, which returned a listing from `C:\Projects` via the Windows agent. This is **read-only**, scoped folder access; it is not arbitrary whole-machine browsing.

Run the PowerShell command below on the Windows/main PC from the folder containing `agent.js` and `windows-drive-type.js`. If the Windows machine is using a copied runtime folder, copy both `scripts/spiritdesktop-windows/agent.js` and `scripts/spiritdesktop-windows/windows-drive-type.js` into that folder before launching. Editing the repo copy does not update an already-running copied agent.

The Windows agent exposes `POST /api/files/list` only when `SPIRIT_DESKTOP_FS_ENABLED=true` and the requested path is under `SPIRIT_DESKTOP_FS_ALLOWLIST`. The Next app calls it only when `SPIRIT_WINDOWS_FS_ENABLED=true` plus `SPIRIT_WINDOWS_FS_BASE_URL`, `SPIRIT_WINDOWS_FS_TOKEN`, and `SPIRIT_WINDOWS_FS_ALLOWLIST` are configured.

The token must match between `SPIRIT_TELEMETRY_TOKEN` on Windows and `SPIRIT_WINDOWS_FS_TOKEN` on the Dell. The allowlist defaults to `C:\Projects`, but keep it explicit. Spirit can list/read only allowed Windows paths, not the whole machine. Do not use angle brackets in `SPIRIT_WINDOWS_FS_BASE_URL`.

Working PowerShell launch command on the Windows desktop agent:

```powershell
$env:PORT="3000"
$env:SPIRIT_TELEMETRY_TOKEN="3399"
$env:SPIRIT_DESKTOP_FS_ENABLED="true"
$env:SPIRIT_DESKTOP_FS_ALLOWLIST="C:\Projects"
node .\agent.js
```

Matching Dell/Next `.env.local` settings:

```bash
SPIRIT_ENABLE_LOCAL_TOOLS=false
# Hermes 4 accepts OpenAI-compatible tool schemas, but the 2026-05-29 probe
# emitted a noop tool call even when instructed not to. Keep this false unless
# a fresh operator probe proves the target model/tool policy is safe.
SPIRIT_OLLAMA_SUPPORTS_TOOLS=false
SPIRIT_WINDOWS_FS_ENABLED=true
SPIRIT_WINDOWS_FS_BASE_URL=http://REPLACE_WITH_WINDOWS_LAN_IP:3000
SPIRIT_WINDOWS_FS_TOKEN=3399
SPIRIT_WINDOWS_FS_ALLOWLIST=C:\Projects
SPIRITDESKTOP_TELEMETRY_URL=http://REPLACE_WITH_WINDOWS_LAN_IP:3000/api/telemetry/self
SPIRIT_TELEMETRY_TOKEN=3399
```

Verify telemetry from the Dell:

```bash
curl -H "Authorization: Bearer 3399" http://REPLACE_WITH_WINDOWS_LAN_IP:3000/api/telemetry/self
```

Verify from Spirit chat:

```text
whats in my c/projects folder?
```

Expected result: Spirit should return `Files in C:\Projects` with directories like `clinicPitch`, `crash-course`, `demo`, `DemoChat`, `fades-and-facials`, `hivemind`, `homelab`, and any other current allowlisted entries.

Troubleshooting:

- `The Windows agent rejected the bearer token.` means `SPIRIT_TELEMETRY_TOKEN` and `SPIRIT_WINDOWS_FS_TOKEN` do not match, or the wrong/old process is running.
- `filesystem endpoint missing` means the Windows machine is running an older copied `agent.js`; copy the updated agent and restart `node .\agent.js`.
- `outside allowlist` means `SPIRIT_DESKTOP_FS_ALLOWLIST` or `SPIRIT_WINDOWS_FS_ALLOWLIST` does not include the requested path.
- `unreachable` means the Dell cannot reach the Windows LAN IP or port `3000`.

## Current Checkpoint

- **Dashboard / homelab telemetry is live** - cluster polling via **`/api/telemetry/cluster`** with CPU/RAM/storage when collectors respond.
- **Cluster telemetry** can include **Spirit Dell** and **spiritdesktop** when endpoints and env are configured (Windows agent exposes **`/api/telemetry/self`**).
- **Local and remote storage** surface through telemetry payloads **where the agent/OS exposes them** (e.g. Windows logical disks via the desktop agent).
- **Capability registry** exists at **`/api/telemetry/capabilities`** (read-only).
- **`/api/spirit`** can answer **deterministic** capability questions from that registry - hardware, storage, model/runtime, “C: drive” visibility, file-access boundaries, SSH boundaries, and general capabilities - without hallucinating layout when the registry has the facts.
- **Oracle Voice MVP** is in place: STT + **`/api/spirit`** + TTS, with text fallback; hands-free loop per **`_blueprints/oracle_voice_mvp.md`**.
- **Chat + Oracle tone** - normal dating/social advice stays in scope; **consent and safety boundaries** remain enforced (Hermes/Oracle behavior refined; not a license to ignore policy).
- **Oracle visuals** - orb / fairy / visualizer direction has started; **`/oracle` still needs a full design-system pass** (polish backlog).
- **Manual Dell → desktop SSH** exists **outside** the app; **in-app SSH tools / execution are not wired** yet.
- **File/folder browsing from chat** is scoped and now verified for allowlisted Windows folders: workspace reads stay under `SPIRIT_PROJECT_PATH`; Windows folder listing goes through the SpiritDesktop filesystem bridge and allowlisted roots such as `C:\Projects`.
- **Project / progress tracker** - **planned**, not implemented (see **`_blueprints/progress_tracker_roadmap.md`**).

## Where I Left Off

- **UI polish** - lots of small fixes remain across dashboard, chat, Oracle.
- **`/oracle` full page design** - not finished; align with **`_blueprints/design_demo.md`** patterns when ready.
- **Sitewide iOS/Android responsiveness** - needs a focused pass (breakpoints, touch, safe areas).
- **Personality / profile** - clearer settings, memory hygiene, and separation of “test chat” vs real personalization.
- **Progress tracker / project tracker** - next **major product** feature after docs stabilize; read-only discovery before any writes.
- **Safe tooling phase** - **read-only project discovery** from configured roots first. Windows `C:\Projects` listing is verified; next work is safe context selection and prompt-packet excerpts, not write/edit/delete.
- **SSH command execution** - stays **later**, behind explicit **approval gates**.

### Seeded safety smoke harness

The repeatable seeded safety harness covers **Manual Check 7: protected/secret path blocking** and **Manual Check 8: path traversal manual diff blocking**. A passing run means these seeded safety checks passed; it does not automatically accept, commit, approve, or close out the phase.

Expected safety behavior:

- Runs in dry-run mode only.
- Does not approve anything.
- Does not apply anything.
- Does not write files.
- Reports `applied_anything: false`.
- Keeps approval unavailable for blocked cases.

Manual Check 9 is now included for normalized target mismatch / allowed-file regression coverage.

### Phase 4F proxy + Scout closeout

Run the non-approving closeout lane:

```bash
cd ~/SpiritOS
source .venv/bin/activate
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile phase-4f-closeout
```

The dashboard `Manual Checks` card exposes the same proxy and Scout runner profiles. Confirmed buttons are required for `4F Closeout`, `Search Smoke`, and `Soak Snapshot`.

Closeout runbook: `scout/docs/V0_3_PHASE4F_PROXY_SCOUT_CLOSEOUT.md`.

## Next Work Order

**P0 - now**

- Land this checkpoint (commit + stabilize).
- **`npm run typecheck`** + **`npm test -- --run`** + **`npm run lint`** on clean intent.
- Confirm **no secrets** and **no junk** in the commit (no `.env.local`, no certs, no accidental huge artifacts).

**P1**

- **`/oracle`** - full design pass (layout, density, motion, states).
- **Mobile-first responsive pass** across dashboard / chat / Oracle (360 / 375 / 768 / 1024).
- **Personality / profile cleanup** and **memory hygiene**.
- **Progress tracker** - roadmap + data model (**`_blueprints/progress_tracker_roadmap.md`**).

**P2**

- Read-only **project discovery** from `SPIRIT_PROJECT_PATH` and allowlisted Windows roots.
- Convert verified Windows folder listings into safe Source context candidates for manual prompt packets.
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

### Source proxy start (`8787`)

The Source proxy is a separate FastAPI/LiteLLM-side process from the visual Next app. Run it in its own terminal from the authoritative Source Proxy checkout named by the worktree manifest (not the SpiritFlix checkout):

```bash
cd /home/source/SpiritOS-source-proxy-20260711 # verify this path in the manifest first
npm run proxy:bootstrap   # first run only, creates .venv-source-proxy
npm run proxy:https:lan   # HTTPS API on 0.0.0.0:8787
```

The proxy launcher loads `.env`, `.env.local`, and `config/source-proxy.env` before starting Python. Restart `npm run proxy:https:lan` after adding or changing API keys.

Check it locally:

```bash
curl -k https://127.0.0.1:8787/healthcheck
```

Check it from LAN/Tailscale:

```bash
curl -k https://10.0.0.186:8787/healthcheck
```

List Source proxy routes:

```bash
curl -k https://127.0.0.1:8787/v1/models
```

Send a local Ollama generation through the unified LiteLLM route:

```bash
curl -k https://127.0.0.1:8787/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"local","messages":[{"role":"user","content":"Reply with exactly: source proxy ready"}],"max_tokens":16}'
```

For Increment 1.1, run that generation twice; the second response should include `source_proxy.response_ms` under `2000`.

For Increment 1.2, start PostgreSQL before restarting the proxy:

```bash
(cd backend && docker compose up -d source-postgres)
npm run proxy:bootstrap   # first run after requirements changed
npm run proxy:https:lan
```

After a test generation, verify asynchronous expenditure logging:

```bash
docker exec -it source-postgres psql -U source_proxy -d source_proxy \
  -c "select user_id, project_id, model_alias, routed_model, total_tokens, cost_usd from source_expenditure_log order by created_at desc limit 1;"
```

The row should contain `user_id`, `project_id`, and a calculated `cost_usd`. Local Ollama routes normally log `0.00000000` cost.

For Increment 1.3, paid cloud routes require explicit spend approval before the provider request is sent. A request without approval:

```bash
curl -k https://127.0.0.1:8787/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"openai","user_id":"source","project_id":"source","messages":[{"role":"user","content":"Say hello"}],"max_tokens":32}'
```

should return `402 Payment Required` with a `spend_before_send` breakdown. To approve the spend, resend with:

```json
"approval": "y"
```

Local Ollama requests do not require approval because their projected provider cost is `$0.00000000`.

DeepSeek is available as the `deepseek` alias when `DEEPSEEK_API_KEY` is set. The default routed model is `deepseek/deepseek-chat`, overrideable with `SOURCE_PROXY_DEEPSEEK_MODEL`.

```bash
curl -k https://127.0.0.1:8787/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek","user_id":"source","project_id":"source","messages":[{"role":"user","content":"Reply with only: deepseek route working"}],"max_tokens":16}'
```

Like other paid routes, the first request should return `402 Payment Required` with `spend_before_send`. Resend with `"approval":"y"` only when you want to spend.

For Increment 2.4, preview whether Source should use an API route, manual browser route, local route, or ask you:

```bash
curl -k https://127.0.0.1:8787/v1/decisions/route \
  -H 'Content-Type: application/json' \
  -d '{"task":"Review this repo architecture and find risks","needs_codebase_context":true,"context_tokens":45000}'
```

The response should include `task_classification`, `recommended_route`, `reason_codes`, `risk_tier`, `context_estimate`, and `next_prompt_action`.

For Increment 2.5, generate a paste-ready manual prompt packet:

```bash
curl -k https://127.0.0.1:8787/v1/decisions/prompt-packet \
  -H 'Content-Type: application/json' \
  -d '{"task":"Review the Source proxy routing architecture and propose safe next steps","needs_codebase_context":true,"wants_implementation":true,"context_tokens":45000,"relevant_context":"Files: source_proxy/routing/litellm_router.py, source_proxy/api/chat.py, proxyPlan.md"}'
```

The response should include `target_model_hint`, `task_summary`, `relevant_context`, `constraints`, `requested_output`, `paste_back_instructions`, and a copy-ready `prompt_text`.

For Increment 2.6, get a manual/browser model recommendation:

```bash
curl -k https://127.0.0.1:8787/v1/decisions/recommend-model \
  -H 'Content-Type: application/json' \
  -d '{"task":"Review this whole repo for architecture risks","needs_codebase_context":true,"context_tokens":90000}'
```

The response should include `primary_model`, `fallback_model`, `route_type`, `rationale`, and `expected_user_action`.

For Increment 2.7B, preview API-vs-manual routing before spending:

```bash
curl -k https://127.0.0.1:8787/v1/decisions/api-vs-manual-preview \
  -H 'Content-Type: application/json' \
  -d '{"task":"Review this whole repo for architecture risks","needs_codebase_context":true,"context_tokens":90000,"api_model_alias":"openai","max_completion_tokens":1024}'
```

The response should include `projected_api_cost`, `context_tokens`, `manual_model_recommendation`, `api_model_option`, `privacy_flags`, and `required_human_decision`.

If bootstrap fails with `ensurepip` / `venv` missing on Ubuntu, install the host package and rerun:

```bash
sudo apt update
sudo apt install -y python3.12-venv
npm run proxy:bootstrap
```

If the endpoint returns `503` with an NVIDIA/NVML message, the API is running but the process cannot see GPU metrics yet. Verify `nvidia-smi` works for the `source` user before continuing proxy diagnostics.

### Visual app start (`3000`)

The browser UI is the Next dev server. Run it in a separate terminal from the proxy, from that same verified authoritative Source Proxy checkout:

```bash
cd /home/source/SpiritOS-source-proxy-20260711 # verify this path in the manifest first
npm run dev:https:lan
```

Then open:

```text
https://10.0.0.186:3000
```

The common mix-up: `npm run proxy:https:lan` starts only the API on **8787**. It does not start the visual site on **3000**.

### Repository context bundles

## FULL REPO CONTEXT COMMAND

Run this when an outside LLM needs the whole repo split into uploadable compressed context files:

```bash
cd /home/source/SpiritOS
npm run context:all
```

This writes all full-repo context packs into:

```text
/home/source/SpiritOS/repomixes/
```

Generated files:

| File | What it contains |
| --- | --- |
| `repomixes/repo-map-context.xml` | repo map, README, package/config, docs, blueprints |
| `repomixes/source-proxy-context.xml` | Source Proxy, coding lane, worker code |
| `repomixes/frontend-context.xml` | app, components, lib, Next/TS config |
| `repomixes/spiritflix-media-code-context.xml` | SpiritFlix and media code |
| `repomixes/docs-plans-context.xml` | docs, plans, roadmaps, blueprints |

Equivalent alias:

```bash
npm run context:full-split
```

## PROXY ONLY CONTEXT COMMAND

Run this only when the reviewer needs Source Proxy plus the coding lane:

```bash
cd /home/source/SpiritOS
npm run context:source-proxy-min
```

Equivalent:

```bash
npx repomix --profile source-proxy-min .
```

**Output:** `repomix-output.source-proxy-min.xml` - upload this only for proxy/coding-lane review. Mirrors are also written as `repomix-output.source-proxy-min.ast.xml` and `repomix-output.source-proxy-min.headroom.xml`.

Verify size and bloat exclusions:

```bash
npm run context:verify
```

## SMALL REPO MAP ONLY

```bash
npm run context:repo-map
npm run context:verify:repo-map
```

## HEADROOM NOTES

Headroom extra token savings needs the Python proxy on **8797** - not Source Proxy on 8787:

```bash
npm run context:headroom:check
pip install "headroom-ai[proxy]"
npm run headroom:proxy
npm run context:source-proxy-min
```

Without Headroom, the context commands still generate Tree-sitter compressed Repomix packs.

Raw full-tree dump, legacy/debug only:

```bash
npm run context:pack:full
```

Prefer `npm run context:all` for real LLM review.

### Next MCP WebSocket diagnostics

Next.js 16 exposes runtime diagnostics at `/_next/mcp` while the dev server is running. The local bridge keeps a persistent WebSocket open for JSON-RPC tool calls and forwards `get_errors` / `get_page_metadata` through `next-devtools-mcp`.

Terminal 1, start the visual app:

```bash
npm run dev:https:lan
```

Terminal 2, start the WebSocket bridge:

```bash
NEXT_MCP_PORT=3000 npm run next:mcp:ws
```

Terminal 3, query current errors:

```bash
npm run next:mcp:ws:probe get_errors
```

The bridge listens on `ws://127.0.0.1:3901` by default. Override it with `NEXT_MCP_WS_PORT`.

Next blocks cross-origin dev assets unless the browser `Origin` hostname is allowlisted. Defaults live in `allowed-dev-origins.ts` and merge with **`NEXT_ALLOWED_DEV_ORIGINS`** (comma-separated hostnames in `.env.local`, no `http://` or ports). **Restart the dev server** after edits - `next.config.ts` only sees env at startup.

### Oracle microphone over LAN / Tailscale IP (`http://10…`, `http://100…`)

Browsers treat plain **`http://` to a LAN or Tailscale IP** as a **non-secure context** and **hide `navigator.mediaDevices`** - Oracle cannot capture mic there until you use **HTTPS**.

- **`npm run dev:https`** - same `-H 0.0.0.0` bind as `npm run dev`, plus Next **`--experimental-https`** (self-signed cert). Fine for **this machine** via `https://localhost:3000`.
- **`npm run dev:https:lan`** - HTTPS dev using certs that include **your LAN / Tailscale hosts** in the SAN. Generate once:
  `SPIRIT_TLS_EXTRA_HOSTS=10.0.0.186,100.111.32.31 bash scripts/gen-dev-cert.sh`
  then **`npm run dev:https:lan`** or **`npm run dev:all:https:lan`**. Then open **`https://10.0.0.186:3000/oracle`** from another device.
- **`npm run dev:all:https`** - Docker backends + **`npm run dev:https`** (quick localhost HTTPS).
- **`npm run dev:all:https:lan`** - Docker backends + **`npm run dev:https:lan`** (run **`scripts/gen-dev-cert.sh`** first).

You cannot “fix” this in React alone; it is **browser security**.

#### Remote browser shows “connection failed” (but `Ready` on the server)

1. **Firewall on the Spirit host** - allow inbound TCP **3000** for the visual app and **8787** for the proxy: e.g. `sudo ufw allow 3000/tcp`, `sudo ufw allow 8787/tcp`, then `sudo ufw reload`. Confirm listen: `ss -tlnp | grep -E ':3000|:8787'` shows `0.0.0.0:3000` and/or `0.0.0.0:8787`.
2. **Ping / route** - client must reach the host IP on your LAN or Tailscale (`tailscale ping` helps).
3. **TLS name mismatch** - use **`npm run dev:https:lan`** + **`gen-dev-cert.sh`** so the cert includes the hostname/IP you type in the bar.
4. From the client, sanity-check: `curl -vk https://10.0.0.186:3000/` - if TCP fails before TLS, it is network/firewall, not Oracle.

## Development workflow

- **Port / HTTPS:** default local dev is **`npm run dev:https:lan`** (port **3000**, `0.0.0.0` bind). For **Oracle mic from another machine**, use **`dev:https:lan`** + **`scripts/gen-dev-cert.sh`**, and open the firewall for **3000/tcp**. Use `npm run dev -- -p 3000` only if you need plain HTTP on a fixed port.
- **Webpack vs Turbopack:** default `npm run dev` uses webpack; `npm run dev:turbo` for Turbopack if you prefer.

## Design

- **`_blueprints/design_system.md`** - Dark Node palette, typography, glass rules.
- **`_blueprints/design_demo.md`** - art-direction sandbox; future **production** responsive targets called out there and in the design system.
- **`_blueprints/progress_tracker_roadmap.md`** - **planned** in-app project/progress tracker (not shipped yet).
- **`src/app/globals.css`** - Tailwind v4 `@theme` tokens; ThemeEngine `--spirit-*` vars per `data-theme`.

## Backend

See `backend/docker-compose.yml` and `backend/README.md` for Ollama / voice services.
