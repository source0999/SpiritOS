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
- Oracle STT / mic — reuse mode + TTS hooks first; add capture later.

## Oracle Voice — sensible next steps

1. Add `OracleVoicePanel` (or extend chrome) with a small **voice state machine** (idle → streaming → speak → idle).
2. Reuse **`useSpiritModeRuntime`** + **`useSpiritVoiceRuntime`** + **`ModelProfileSelector`** / **`VoiceControl`** — no duplicate TTS wiring.
3. Add STT only after playback path is stable.

## Key files

| Hook | Role |
|------|------|
| `src/hooks/useSpiritThreadRuntime.ts` | Sidebar model: threads, folders, search, draft lane. |
| `src/hooks/useSpiritModeRuntime.ts` | Model profile, personalization summary fields for body. |
| `src/hooks/useSpiritChatTransport.ts` | `useChat`, headers, workflow/research-plan, Dexie hydrate. |
| `src/hooks/useSpiritVoiceRuntime.ts` | Speak-latest, sanitization, activity hooks around `useTTS`. |
