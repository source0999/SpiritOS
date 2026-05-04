> **Extracted from:** Product direction toward a full GPT-style workspace on `/chat` inside the Spirit OS shell.  
> **Design language:** Phased rollout — stability before gimmicks; Dexie/thread truth stays local-first.

## Chat workspace rebuild — phased roadmap

We are rebuilding the old Spirit OS chat brain **by extracting patterns**, not cloning monolithic bundles. `/` stays the dashboard; `/chat` is the saved-thread surface.

### Phase 0 — **Stabilize** (current)

- Draft-first **New chat** — no empty Dexie thread until first user line.
- Thread switch clears UI immediately then hydrates from Dexie deterministically.
- Optimistic deletes with instant sidebar updates; streaming guarded (no noisy rail swaps).
- Diagnostics rail: **single chevron** collapse, persisted preference, `/chat` defaults thin.
- Message list dedupe by id (Dexie × AI SDK overlaps).

_Reference (old repo): draft-first composer, rail auto-collapse hints — recreated here intentionally thin._

### Phase 1 — Folders schema + UI (**Prompt 5 — shipped**)

- Dexie v2: `folders` table + thread `folderId` / `order` indexes; additive migration from v1.
- Sidebar: Chats (root) + folder sections, collapse/rename/delete, thread move via compact `<select>`.
- Delete folder moves threads to root; threads are never deleted by folder removal.

### Phase 2 — Drag-and-drop (**@dnd-kit**, **Prompt 6 — shipped**)

- `DndContext` + nested `SortableContext`s (root threads, per-folder threads, folder rank grips only — no nested sortable hell).
- Droppable **Chats** root + per-folder targets; cyan glow on hover while dragging a thread.
- `reorderThreadsInFolder` / `reorderFolders` + `updateThreadFolderAndOrder` in Dexie; `sortThreadsWithOrderFallback` respects `order`.

### Phase 3 — Message actions

- Per-bubble copy, edit stub, delete, regenerate (transport hooks), keyboard affordances.

### Phase 4 — Search & filters (**Prompt 10A — baseline shipped**)

- Client-side thread title + message body search in the thread sidebar (`Search chats…`), debounced; case-insensitive; optional snippet line on hits.
- Server/embeddings / cross-device sync remain future prompts.

### Phase 5 — Pinned / archive / export (**Prompt 10A — pins baseline**)

- Pin/unpin with Dexie `pinned` / `pinnedAt` (v4 migration); **Pinned** section above Chats; duplicate row in folder/root still allowed for clarity.
- Soft-archive + Markdown/JSON export still TODO.

### Mode Runtime V2 (**Prompt 10A**)

- Modes are behavior + sampling presets (system prompt, temperature, max tokens, future flags like `searchPreferred` on Researcher).
- **Peer** replaces the old **Normal** label; profile id stays `normal-peer` for backwards compatibility.
- Optional **Spirit Profile** (local) builds a short `personalizationSummary` appended on the server after the mode system prompt (validated length).

### Workspace signals (**Prompt 10A**)

- **Activity** panel: runtime model hint, voice backend, “search not enabled”, local-only memory note, capped recent events (message sent, assistant done, mode change, TTS). No hidden CoT.

### Prompt 10C-C — hygiene + research honesty (**shipped**)

- Assistant output sanitizer strips hidden tags and leaked instruction lines before UI, clipboard, TTS, and persistence.
- Researcher: server appends **source enforcement** block; client strips fake citations if the model ignored policy; `x-spirit-web-sources` only lists verified `http(s)` URLs.
- Researcher web search defaults **ON** (`unset` preference); explicit user OFF stays OFF; `user_disabled_web_search` appears only when the user actually disabled web for that thread.
- Teacher web prefetch triggers on **educational** phrasing (explain/teach/study/ABA/…) when Teacher web toggle is on — not on generic chit-chat.
- Research plan + workflow UI state is keyed to active thread/draft; clears on switch; visualizer supports compact completed line above composer.

### Deferred (not claimed)

- Full **Deep Research** orchestration, **RAG**, **server chat sync**, **DeepSeek** runtime, **Continue** terminal mode, **STT/mic**.

### Phase 6 — Voice / TTS / STT

- **Prompt 9C (shipped):** server-side TTS abstraction (`TTS_PROVIDER=piper|elevenlabs`), Piper fallback, `/api/tts` response headers for latency diagnostics, mobile-first `/chat` (thread drawer, diagnostics hidden below `lg`), Oracle lane `ORACLE_OLLAMA_MODEL` via `runtimeSurface` on `/api/spirit` (TTS stays `/api/tts` — never through the LLM).
- Oracle/quarantine pipelines feed here only after desktop chat parity.

### Phase 7 — Homelab widgets & tools

- NUT probes, filesystem scanners, scripted actions — right rail or dashboard cards only when chat core is trustworthy.

---

### Persistence & cross-device (explicit)

- **Current persistence is Dexie (IndexedDB) local-only.** Each browser profile holds its own thread/message truth; nothing is pushed to a server in this stack yet.
- **Cross-device desktop/mobile sync** is **Prompt 9E-B** (server-backed chat sync). Until that ships, **each browser/device keeps its own local IndexedDB** — do not assume continuity when switching machines or Safari vs Chrome.
- **Prompt 10B (shipped):** OpenAI Responses `web_search` behind `WEB_SEARCH_ENABLED` + `OPENAI_API_KEY`; `/api/research/web-search` for proof calls; `/api/spirit` uses AI SDK `system` option (no system-in-messages warning); Researcher gets `x-spirit-web-search` response header; **Deep think** + **Web search** toggles per thread; TTS long replies default to **local summary** with optional **chunked full read**; high-level workflow strip (not CoT); Spirit Profile “what Spirit knows” rows with source + wrong-perspective flag.
- **Later** — RAG, DeepSeek reasoning lane, STT/mic, full automatic memory, Gemini-style Deep Research plan editor (10C).

