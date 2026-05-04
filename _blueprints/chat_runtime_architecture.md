# Chat runtime architecture (SpiritOS)

> **Extracted from:** Prompt 10D-A refactor — hooks layer between UI and persistence/transport.
> **Design language:** Same contract as `/api/spirit`; local Dexie is optional.

## Text diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ SpiritChat (layout + orchestration)                              │
│  ├─ Mobile rail / workspace chrome                               │
│  ├─ ChatThreadSidebar (only when persistence + showThreadSidebar)│
│  ├─ SpiritMessage list + composer                                │
│  └─ VoiceControl / profile / activity / workflow panels           │
└───────────────┬─────────────────────────────────────────────────┘
                │
    ┌───────────┼───────────┬──────────────────┬──────────────────┐
    ▼           ▼           ▼                  ▼                  ▼
useSpirit   useSpirit   useSpirit         useSpirit          useTTS
Thread      Mode        ChatTransport     VoiceRuntime       (/api/tts)
Runtime     Runtime     (AI SDK useChat)  (speak helpers)
    │           │           │                  │
    ▼           ▼           ▼                  ▼
Dexie         Client      POST /api/spirit   POST /api/tts,
(usePersistentChat)       response headers    /api/tts/voices
```

## Intentionally local-only

- **Dexie** — saved threads, messages, pins, folders (when `persistence` is on).
- **localStorage** — TTS prefs, activity log mirror, web-search toggles where applicable.
- **Spirit user profile JSON** — personalization preview + `sendPersonalizationToServer` gate (`spirit-user-profile`).

## Server-backed

- **`/api/spirit`** — chat completion, streaming, route/workflow headers.
- **`/api/tts`**, **`/api/tts/voices`** — ElevenLabs (or configured) voice playback.
- **OpenAI web search** — when Researcher/Teacher paths enable it and keys exist.

## Deferred (do not implement here)

- Deep Research expansion, RAG, server-side chat sync, DeepSeek lane.

## Oracle Voice MVP (`/oracle`) — hands-free session (Prompt 10D-E + 10D-F persona surface)

- **`OracleVoiceSurface`** — standalone voice-first layout (not `SpiritChat`); wires **`useSpiritChatTransport`** with `runtimeSurface="oracle"` + **`persistence={false}`**, shared **`useSpiritModeRuntime`** / **`useSpiritVoiceRuntime`** / **`useTTS`**.
- **Prompt 10D-F:** `/api/spirit` receives `runtimeSurface`; **`buildModelRuntime`** adds Oracle Voice surface instructions + voice-first response budget + oracle-only token ceilings. **`x-spirit-runtime-surface`** response header echoes `oracle|chat`. Peer mode prompt is workspace-neutral (not coding-default).
- **Hands-free loop (default):** `Start session` arms recording → amplitude VAD in **`useOracleSpeechInput`** detects continuous silence (default `1.2s` past `0.035` threshold, after `700ms` min recording) → auto-stops → **`/api/stt/transcribe`** → submits transcript to `/api/spirit` → TTS → 500ms delay → re-arms recording. `Stop session` clears all of it.
- **STT:** **`useOracleSpeechInput`** — **`MediaRecorder`** → **`/api/stt/transcribe`** (proxies to Whisper **OpenAI-style** `.../v1/audio/transcriptions`). Mic choice persisted under **`spirit:oracle:selectedMicId`**; **`getUserMedia`** uses selected `deviceId` when supported. Browser Web Speech is NOT used.
- **Idempotency:** `stopRecordingAndTranscribe()` and the parent surface guard on a `stopInFlightRef` and `isProcessingTurnRef` so silence VAD + a manual **Finish now** click cannot double-submit.
- **Secure context:** **`getOracleBrowserCapabilityReport(mounted)`** is the only place we read `navigator`/`window` for mic capability. Insecure-context (plain HTTP to LAN/Tailscale IP) renders an unmissable warning banner with the same-host HTTPS upgrade link; Start session is disabled.
- **Fallback:** collapsible text composer hits the same `/api/spirit` path when STT is denied or unsupported. The advanced settings drawer also exposes a "Text fallback only" toggle.
- **STT route headers:** `/api/stt/transcribe` always emits `x-spirit-stt-provider: whisper`; emits `x-spirit-stt-duration-ms` when known.
- Status machine + hints: **`oracle-voice-session.ts`** (`hands-free | push-to-talk | manual-text`, plus `hearing-speech`, `silence-detected`, `restarting`, `blocked` statuses), **`OracleVoiceControls`**, **`OracleVoiceStatusCard`** — UI-only; no IndexedDB Oracle threads.
- See **`_blueprints/oracle_voice_mvp.md`** for scope / exclusions.

## Key files

| Hook | Role |
|------|------|
| `src/hooks/useSpiritThreadRuntime.ts` | Sidebar model: threads, folders, search, draft lane. |
| `src/hooks/useSpiritModeRuntime.ts` | Model profile, personalization summary fields for body. |
| `src/hooks/useSpiritChatTransport.ts` | `useChat`, headers, workflow/research-plan, Dexie hydrate. |
| `src/hooks/useSpiritVoiceRuntime.ts` | Speak-latest, sanitization, activity hooks around `useTTS`. |
