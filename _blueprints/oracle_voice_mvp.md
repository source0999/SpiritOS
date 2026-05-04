# Oracle Voice MVP (Prompt 10D-E — hands-free session)

> **Extracted from:** Hands-free `/oracle` loop — **MediaRecorder** + amplitude VAD → **`/api/stt/transcribe`** (Whisper) → **`/api/spirit`** (`runtimeSurface="oracle"`) → **`/api/tts`** → auto-relisten in **hands-free** mode.
> **Design language:** Same runtime + TTS stack as `/chat`; Dexie stays off for Oracle until product decides otherwise. Spirit owns one Oracle layout; do not fork it for "wake word" experiments.

## Persona vs surface (Prompt 10D-F)

- **Mode = personality** (`MODEL_PROFILES` / Peer, Teacher, Researcher, Brutal, Sassy). Peer is **surface-neutral**: conversational first; coding/tech only when the user steers there.
- **Surface = context**: `buildRuntimeSurfaceInstruction("oracle")` in `spirit-runtime-surface.ts` appends after the mode prompt (before response budget + web digest). It flags live **Oracle Voice** — not the coding workspace — without replacing mode tone.
- **`buildModelRuntime`** merges: profile → Oracle surface block (if `runtimeSurface: "oracle"`) → response budget (includes Oracle-specific spoken-length hints when on oracle) → Deep Think → web digest → personalization → answer contract.
- **`resolveSpiritMaxOutputTokens`** applies tighter **spoken** ceilings only when `runtimeSurface === "oracle"`; `/chat` budgets unchanged.

## Current status

| Aspect | State |
|--------|-------|
| Surface | **`OracleVoiceSurface`** — standalone page (does not mount **`SpiritChat`**) |
| Persistence | **`false`** — ephemeral browser session only |
| Threads | **No** saved-thread sidebar; no Dexie lane for Oracle |
| STT | **Whisper backend** (primary) via **`/api/stt/transcribe`**; browser Web Speech only as legacy/optional fallback — not the main path |
| Mic selection | **`spirit:oracle:selectedMicId`** in `localStorage`; **`getUserMedia`** with `deviceId` when possible, fallback to default with error hint |
| Loop | **Hands-free** by default (silence VAD auto-sends), Push-to-talk and Text-only available as knobs |
| RAG / DeepSeek / server sync | **Out of scope** |

## Hands-free loop (default)

1. User taps **Start session** → mic permission if needed → **MediaRecorder** + audio meter armed.
2. While recording, an `AnalyserNode` polls amplitude every ~60ms. Above `silenceThreshold` (default `0.035`) is "hearing speech"; below is silence.
3. After at least `minRecordingMs` (default `700ms`) AND continuous silence for `silenceDurationMs` (default `1200ms`) — **and** at least one frame of speech was heard — recording auto-stops.
4. Audio **POST** `multipart/form-data` `audio` → **`/api/stt/transcribe`** → Whisper transcript.
5. Transcript flows into the same **`useSpiritChatTransport`** path as chat with **`runtimeSurface: "oracle"`** + **`persistence={false}`**.
6. Assistant reply → **`useSpiritVoiceRuntime`**/**`useTTS`** → `/api/tts` (ElevenLabs/Piper).
7. When TTS goes idle AND the session is still active AND no errors are pending → schedule a **500ms** delay, then re-arm `startRecording()`.
8. **Stop session** sets `sessionActiveRef=false`, cancels recording, stops TTS, clears the relisten timer, latches `stopped`.
9. **Finish now** stays as a backup button visible only while listening/hearing-speech — same code path as silence VAD; idempotent stop guard means a click + auto-stop does NOT double-submit.
10. Empty transcripts (Whisper heard nothing) do not submit; if session active, the loop returns to listening.

`maxRecordingMs` (default `60000ms`) is a hard cap per utterance — Spirit refuses to record forever.

**Docker:** `npm run dev:all` / compose should have **`spirit-whisper`** reachable (default Next env **`WHISPER_STT_URL=http://localhost:8000`**). See **`.env.local.example`**.

## Secure context — mandatory for mic

**Browser mic APIs require a [secure context](https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts).** Plain `http://` to a LAN/Tailscale IP hides `navigator.mediaDevices` by design. Use one of:

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- HTTPS via a tunnel/domain (Tailscale Serve/Funnel, Caddy, ngrok, trusted local cert)
- `npm run dev:https:lan` + `scripts/gen-dev-cert.sh` for LAN HTTPS testing

`/oracle` detects this via **`getOracleBrowserCapabilityReport(mounted)`** and renders an unmissable rose banner with the same-host HTTPS URL upgrade link. The Start session button is disabled in this state. Text fallback remains available.

## Shared systems (reuse, don’t fork)

- **Modes:** `useSpiritModeRuntime` — Peer, Teacher, Researcher, Brutal, Sassy.
- **Spirit Profile:** same personalization gate as `/chat` (`spirit-user-profile`).
- **Transport:** `useSpiritChatTransport` — oracle attaches body fields the same way as chat.
- **Voice:** `useSpiritVoiceRuntime` + `useTTS` → `/api/tts`; **`sanitizeAssistantVisibleText`** before speak.

## UI session model

`src/lib/oracle/oracle-voice-session.ts` — statuses include `listening`, `hearing-speech`, `silence-detected`, `transcribing`, `thinking`, `speaking`, `restarting`, `stopped`, `blocked`, `requesting-mic`, `permission-needed`, etc. **`OracleVoiceLoopMode`** is `hands-free | push-to-talk | manual-text` (default = `hands-free`). Helpers: **`deriveOracleVoiceStatus`**, **`shouldOracleAutoRestartListening`**, **`oracleSessionStatusLabel`**, **`oracleSessionStatusHint`**. Capped activity events. Not persisted.

## Capability + secure-context module

`src/lib/oracle/oracle-browser-capabilities.ts` — `getOracleBrowserCapabilityReport(mounted)` returns the SSR-stable shape used by **`useOracleSpeechInput`**, **`OracleVoiceControls`**, and **`OracleVoiceStatusCard`** to decide between `Mic ready.`, `Mic access is blocked on this HTTP address...`, `MediaRecorder unsupported`, and the rest. Avoid reading `navigator`/`window` outside this module.

## Deferred / not built

- Wake word.
- Advanced VAD (RNNoise / Silero / WebRTC VAD).
- Continuous barge-in (interrupt assistant TTS while speaking).
- Persistent Oracle threads / cross-device Oracle history.
- Whisper tuning UI (model swap / language pinning UI).
- OpenAI cloud Whisper fallback in-app (route is provider-shaped for later).
- RAG, DeepSeek lane, server-backed chat sync.
- Deep Research orchestration resume.

## STT route headers (Stage 8)

`/api/stt/transcribe` always sets `x-spirit-stt-provider: whisper`. When the upstream returns a duration, `x-spirit-stt-duration-ms` is added. Dev console logs audio size + upstream status; raw transcripts are NOT logged unless `SPIRIT_DEV_STT_DUMP=1`.

## Key files

| File | Role |
|------|------|
| `src/app/api/stt/transcribe/route.ts` | Proxies audio to Whisper OpenAI-compatible transcriptions; provider/duration headers; dev-only size + status logs. |
| `src/lib/server/stt-provider.ts` | STT env + `transcribeSpeech` / diagnostics. |
| `src/lib/oracle/oracle-browser-capabilities.ts` | SSR-safe mic + secure-context probe. |
| `src/components/oracle/OracleVoiceSurface.tsx` | Hands-free session loop, relisten after TTS, transport + TTS, idempotency latches. |
| `src/components/oracle/OracleVoiceControls.tsx` | Start session / Stop session / Finish now backup, mic strip, audio meter, silence indicator, advanced (silence + sensitivity + text fallback) settings. |
| `src/hooks/useOracleSpeechInput.ts` | MediaRecorder + `/api/stt/transcribe`; mic enumeration; audio amplitude VAD; idempotent stop. |
| `src/lib/oracle/oracle-voice-session.ts` | Status + event helpers + auto-restart predicate. |
| `src/components/oracle/OracleVoiceStatusCard.tsx` | Compact telemetry (mode, runtime, STT, mic, audio level, silence ms, transcript, TTS). |
