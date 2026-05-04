// ── tts-parser — pause markers + light markdown strip for speech (Prompt 9) ────

export type TtsSegment =
  | { type: "speech"; text: string }
  | { type: "pause"; ms: number };

function parsePauseMs(raw: string): number | null {
  const n = Number(raw);
  if (!Number.isFinite(n) || n < 0) return null;
  return Math.min(Math.round(n), 60_000);
}

/** Strip markdown-ish noise; keep readable words. */
export function stripTextForTts(input: string): string {
  let s = input;
  s = s.replace(/```[\s\S]*?```/g, " code block omitted. ");
  s = s.replace(/`([^`]+)`/g, "$1");
  s = s.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  s = s.replace(/^#{1,6}\s+/gm, "");
  s = s.replace(/^\s*[-*+]\s+/gm, "");
  s = s.replace(/^\s*\d+\.\s+/gm, "");
  s = s.replace(/\*\*([^*]+)\*\*/g, "$1");
  s = s.replace(/\*([^*]+)\*/g, "$1");
  s = s.replace(/__([^_]+)__/g, "$1");
  s = s.replace(/_([^_]+)_/g, "$1");
  return s.replace(/\s+/g, " ").trim();
}

/**
 * Replace pause markers with internal tokens, then split into segments.
 * Supports: [pause:500], [pause:1s], [[pause 500ms]]
 */
export function parseTtsSegments(raw: string): TtsSegment[] {
  let s = raw.replace(/\r\n/g, "\n");

  s = s.replace(
    /\[\[\s*pause\s+(\d+)\s*ms\s*\]\]/gi,
    (_m, ms: string) => `\u0000PAUSE:${parsePauseMs(ms) ?? 0}\u0000`,
  );
  s = s.replace(/\[pause:\s*(\d+)\s*\]/gi, (_m, ms: string) => {
    const v = parsePauseMs(ms) ?? 0;
    return `\u0000PAUSE:${v}\u0000`;
  });
  s = s.replace(/\[pause:\s*([\d.]+)\s*s\]/gi, (_m, sec: string) => {
    const n = Number(sec);
    const ms = Number.isFinite(n)
      ? (parsePauseMs(String(Math.round(n * 1000))) ?? 0)
      : 0;
    return `\u0000PAUSE:${ms}\u0000`;
  });

  const pieces = s.split(/\u0000PAUSE:(\d+)\u0000/);
  const out: TtsSegment[] = [];
  for (let i = 0; i < pieces.length; i++) {
    const piece = pieces[i]!;
    if (i % 2 === 0) {
      const t = stripTextForTts(piece);
      if (t) out.push({ type: "speech", text: t });
    } else {
      const ms = Number(piece);
      if (Number.isFinite(ms) && ms > 0) out.push({ type: "pause", ms });
    }
  }

  if (out.length === 0) {
    const t = stripTextForTts(s.replace(/\u0000PAUSE:\d+\u0000/g, " "));
    if (t) return [{ type: "speech", text: t }];
  }
  return out;
}
