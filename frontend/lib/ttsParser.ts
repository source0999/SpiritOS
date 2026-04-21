export type TtsSegment =
  | { type: "speech"; text: string }
  | { type: "pause"; ms: number };

const STAGE_PAUSE_MS: Record<string, number> = {
  sigh: 800,
  sighs: 800,
  groan: 800,
  groans: 800,
  laughs: 600,
  laugh: 600,
  scoffs: 600,
  scoff: 600,
  pause: 700,
  exhales: 700,
  exhale: 700,
};

function splitIntoSentenceChunks(text: string): string[] {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (!cleaned) return [];

  return cleaned
    .match(/[^.!?]+[.!?]+|[^.!?]+$/g)
    ?.map((s) => s.trim())
    .filter(Boolean) ?? [];
}

export function parseTtsSegments(text: string): TtsSegment[] {
  const raw = text.trim();
  if (!raw) return [];

  const parts = raw.split(/(\[[^\]]+\])/g).filter(Boolean);
  const out: TtsSegment[] = [];

  for (const part of parts) {
    const marker = part.match(/^\[([^\]]+)\]$/);
    if (marker) {
      const key = marker[1].trim().toLowerCase();
      const ms = STAGE_PAUSE_MS[key];
      if (ms) out.push({ type: "pause", ms });
      continue;
    }

    const chunks = splitIntoSentenceChunks(part);
    for (const chunk of chunks) {
      out.push({ type: "speech", text: chunk });
    }
  }

  return out;
}
