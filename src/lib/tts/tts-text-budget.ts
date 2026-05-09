// ── tts-text-budget - keep /api/tts under 800 chars (Prompt 10B) ───────────────────

export const TTS_TEXT_LIMIT = 800;
export const TTS_SUMMARY_TRIGGER_CHARS = 700;
export const TTS_FULL_CHUNK_SIZE = 650;

/** Strip markdown-ish noise for spoken summaries (no LLM round-trip). */
export function stripMarkdownishForTts(raw: string): string {
  let s = raw.replace(/\r\n/g, "\n");
  s = s.replace(/```[\s\S]*?```/g, " ");
  s = s.replace(/`([^`]+)`/g, "$1");
  s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  s = s.replace(/[#>*_\-~]/g, "");
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

function firstSentences(text: string, maxCount: number): string[] {
  const t = text.trim();
  if (!t) return [];
  const rough = t.split(/(?<=[.!?])\s+/).filter(Boolean);
  if (rough.length <= maxCount) return rough;
  return rough.slice(0, maxCount);
}

/**
 * First 1–3 sentences up to ~500 chars, then hard cap at `maxLen`.
 * Prefix optional “Quick summary: ” stays inside maxLen.
 */
export function summarizeTextForTts(
  raw: string,
  opts?: { maxLen?: number; prefix?: string },
): string {
  const maxLen = Math.min(opts?.maxLen ?? 500, TTS_TEXT_LIMIT - 48);
  const prefix = opts?.prefix ?? "Quick summary: ";
  const flat = stripMarkdownishForTts(raw);
  if (!flat) return prefix.trim().slice(0, TTS_TEXT_LIMIT);

  let body = firstSentences(flat, 3).join(" ");
  if (body.length > maxLen) {
    body = `${body.slice(0, Math.max(0, maxLen - 1)).trim()}…`;
  }

  let out = `${prefix}${body}`.trim();
  if (out.length > TTS_TEXT_LIMIT) {
    out = `${out.slice(0, TTS_TEXT_LIMIT - 1).trim()}…`;
  }
  return out;
}

/** Split into speech-safe chunks; none exceed `TTS_TEXT_LIMIT`. */
export function splitTextIntoTtsChunks(
  raw: string,
  chunkSize: number = TTS_FULL_CHUNK_SIZE,
): string[] {
  const flat = stripMarkdownishForTts(raw);
  if (!flat) return [];
  const cap = Math.min(chunkSize, TTS_TEXT_LIMIT);
  const out: string[] = [];
  let rest = flat;

  while (rest.length > 0) {
    if (rest.length <= cap) {
      out.push(rest);
      break;
    }
    let cut = rest.lastIndexOf(" ", cap);
    if (cut < cap * 0.5) cut = cap;
    const piece = rest.slice(0, cut).trim();
    if (!piece) {
      out.push(rest.slice(0, cap).trim());
      rest = rest.slice(cap).trim();
      continue;
    }
    out.push(piece);
    rest = rest.slice(cut).trim();
  }

  return out
    .filter(Boolean)
    .map((c) => (c.length > TTS_TEXT_LIMIT ? c.slice(0, TTS_TEXT_LIMIT) : c))
    .filter((c) => c.length > 0);
}

export function pickTtsSpeakPayload(
  fullText: string,
  mode: "summary" | "full-chunks",
): { segments: string[]; spokenSummaryLine: string } {
  const t = fullText.trim();
  if (!t) return { segments: [], spokenSummaryLine: "Spoken: (empty)" };
  if (t.length <= TTS_TEXT_LIMIT) {
    return { segments: [t], spokenSummaryLine: "Spoken: full message" };
  }
  if (mode === "summary") {
    const s = summarizeTextForTts(t);
    return { segments: [s], spokenSummaryLine: "Spoken: summary (message was long)" };
  }
  const chunks = splitTextIntoTtsChunks(t);
  const n = chunks.length;
  return {
    segments: chunks,
    spokenSummaryLine: `Spoken: full response in ${n} chunk${n === 1 ? "" : "s"}`,
  };
}
