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

function splitIntoBurstChunks(text: string): string[] {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (!cleaned) return [];

  // Split at punctuation boundaries first so natural pauses stay intact.
  const clauses =
    cleaned.match(/[^,.;:!?-]+[,.;:!?-]?|[^,.;:!?-]+$/g)?.map((s) => s.trim()).filter(Boolean) ?? [];

  const out: string[] = [];
  for (const clause of clauses) {
    const words = clause.split(/\s+/).filter(Boolean);
    if (words.length <= 8) {
      out.push(clause);
      continue;
    }
    // Burst splitter: 5-8 word chunks (prefer 6 words).
    let i = 0;
    while (i < words.length) {
      const remaining = words.length - i;
      const take = remaining <= 8 ? remaining : 6;
      out.push(words.slice(i, i + take).join(" "));
      i += take;
    }
  }
  return out;
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

    const chunks = splitIntoBurstChunks(part);
    for (const chunk of chunks) {
      out.push({ type: "speech", text: chunk });
    }
  }

  return out;
}
