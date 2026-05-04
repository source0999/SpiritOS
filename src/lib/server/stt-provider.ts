import "server-only";

// ── STT provider — proxy browser audio → Faster-Whisper (OpenAI-style API) ───────
// > Docker: `whisper-stt` → :8000, POST /v1/audio/transcriptions (see backend/docker-compose.yml)

export class SttProviderError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
  ) {
    super(message);
    this.name = "SttProviderError";
  }
}

/** Host URL for Faster-Whisper / compatible STT (no trailing slash required). */
export function getWhisperSttBaseURL(): string {
  const raw = process.env.WHISPER_STT_URL?.trim();
  return raw || "http://localhost:8000";
}

export function getWhisperTranscribePath(): string {
  const raw = process.env.WHISPER_STT_TRANSCRIBE_PATH?.trim();
  return raw || "/v1/audio/transcriptions";
}

export function getWhisperSttModel(): string {
  const raw = process.env.WHISPER_STT_MODEL?.trim();
  return raw || "whisper-1";
}

/** Safe label for JSON — hostname + port only, no auth path segments. */
export function getSttDiagnostics(): {
  provider: string;
  url: string;
  source: string;
  transcribePath: string;
} {
  const base = getWhisperSttBaseURL().replace(/\/$/, "");
  let hostPort = base;
  try {
    const u = new URL(base);
    hostPort = `${u.hostname}${u.port ? `:${u.port}` : ""}`;
  } catch {
    hostPort = "invalid WHISPER_STT_URL";
  }
  return {
    provider: "Whisper (Faster-Whisper)",
    url: hostPort,
    source: process.env.WHISPER_STT_URL?.trim() ? "WHISPER_STT_URL" : "default (http://localhost:8000)",
    transcribePath: getWhisperTranscribePath(),
  };
}

type TranscribeOk = {
  ok: true;
  provider: "whisper";
  text: string;
  durationMs?: number;
};

/**
 * `form` must contain `audio` (Blob/File). Optional `language` (ISO code).
 * Forwards to upstream as OpenAI-style multipart: `file`, `model`, optional `language`, `response_format`.
 */
export async function transcribeSpeech(form: FormData): Promise<TranscribeOk> {
  const audio = form.get("audio");
  if (!audio || typeof (audio as Blob).arrayBuffer !== "function") {
    throw new SttProviderError("Audio blob required", 400);
  }
  const blob = audio as Blob;
  if (blob.size < 1) {
    throw new SttProviderError("Empty audio", 400);
  }

  const base = getWhisperSttBaseURL().replace(/\/$/, "");
  const path = getWhisperTranscribePath();
  const model = getWhisperSttModel();
  const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;

  const upstream = new FormData();
  const ext = guessAudioExtension(blob.type);
  upstream.append("file", blob, `upload.${ext}`);
  upstream.append("model", model);
  upstream.append("response_format", "json");
  const lang = form.get("language");
  if (typeof lang === "string" && lang.trim()) {
    upstream.append("language", lang.trim());
  }

  let res: Response;
  try {
    res = await fetch(url, { method: "POST", body: upstream });
  } catch {
    throw new SttProviderError("Whisper backend unreachable", 503);
  }

  if (!res.ok) {
    const detail = await safeText(res);
    const msg = detail ? `Upstream STT ${res.status}: ${detail.slice(0, 200)}` : `Upstream STT ${res.status}`;
    throw new SttProviderError(msg, res.status >= 500 ? 502 : 502);
  }

  let json: unknown;
  try {
    json = await res.json();
  } catch {
    throw new SttProviderError("Invalid JSON from Whisper backend", 502);
  }

  if (!json || typeof json !== "object") {
    throw new SttProviderError("Invalid STT response shape", 502);
  }

  const text =
    typeof (json as { text?: unknown }).text === "string"
      ? (json as { text: string }).text.trim()
      : "";

  const durationMs =
    typeof (json as { duration?: unknown }).duration === "number"
      ? (json as { duration: number }).duration
      : typeof (json as { duration_ms?: unknown }).duration_ms === "number"
        ? (json as { duration_ms: number }).duration_ms
        : undefined;

  return { ok: true, provider: "whisper", text, durationMs };
}

function guessAudioExtension(mime: string): string {
  const m = mime.toLowerCase();
  if (m.includes("webm")) return "webm";
  if (m.includes("mp4") || m.includes("m4a")) return "m4a";
  if (m.includes("wav")) return "wav";
  if (m.includes("mpeg") || m.includes("mp3")) return "mp3";
  return "webm";
}

async function safeText(res: Response): Promise<string> {
  try {
    return await res.text();
  } catch {
    return "";
  }
}
