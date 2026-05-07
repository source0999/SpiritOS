// ── spirit-tool-activity-response - parse x-spirit-tool-activity-json (client-safe) ─

import type { SpiritToolActivityCard } from "@/lib/spirit/spirit-activity-events";

function isCard(x: unknown): x is SpiritToolActivityCard {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return (
    typeof o.id === "string" &&
    typeof o.timestamp === "number" &&
    typeof o.kind === "string" &&
    typeof o.label === "string" &&
    typeof o.status === "string"
  );
}

/** Compact JSON from /api/spirit response headers (deterministic tool paths). */
export function parseSpiritToolActivityHeader(res: Response): SpiritToolActivityCard[] {
  const raw = res.headers.get("x-spirit-tool-activity-json");
  if (!raw?.trim()) return [];
  try {
    const j = JSON.parse(raw) as unknown;
    if (!Array.isArray(j)) return [];
    return j.filter(isCard);
  } catch {
    return [];
  }
}
