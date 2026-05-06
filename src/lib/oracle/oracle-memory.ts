// ── oracle-memory - optional Oracle voice session memory bridge ──────────────────
// > Writes compact exchange summaries to Dexie oracleMemoryEvents when
// > NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY=true. Default is disabled.
// > Chat surface reads these via summarizeOracleMemoryForPrompt and sends the
// > compact block in the request body → [ORACLE MEMORY CONTEXT] in system prompt.

import { db } from "@/lib/chat-db";
import type { OracleMemoryEvent } from "@/lib/chat-db.types";

const DEFAULT_MEMORY_LIMIT = 12;
const ORACLE_MEMORY_CONTEXT_MAX = 3000;

export function isOracleMemoryEnabled(): boolean {
  return process.env.NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY === "true";
}

function randomId(): string {
  try {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
      return crypto.randomUUID();
    }
  } catch {
    /* ignore */
  }
  return `omem_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

/** Writes an Oracle exchange summary to Dexie. No-op when disabled or on SSR. */
export async function appendOracleMemoryEvent(
  input: Omit<OracleMemoryEvent, "id" | "createdAt">,
): Promise<void> {
  if (!isOracleMemoryEnabled()) return;
  if (!db) return;
  const event: OracleMemoryEvent = {
    id: randomId(),
    createdAt: Date.now(),
    ...input,
  };
  await db.oracleMemoryEvents.add(event);
}

/** Returns recent Oracle memory events in chronological order (oldest first). */
export async function getRecentOracleMemoryEvents(
  limit = DEFAULT_MEMORY_LIMIT,
): Promise<OracleMemoryEvent[]> {
  if (!isOracleMemoryEnabled()) return [];
  if (!db) return [];
  const rows = await db.oracleMemoryEvents.orderBy("createdAt").reverse().limit(limit).toArray();
  return rows.reverse();
}

/** Clears all Oracle memory events regardless of the feature flag. */
export async function clearOracleMemoryEvents(): Promise<void> {
  if (!db) return;
  await db.oracleMemoryEvents.clear();
}

/** Formats events into the [ORACLE MEMORY CONTEXT] prompt block, or null if empty. */
export function summarizeOracleMemoryForPrompt(events: OracleMemoryEvent[]): string | null {
  if (events.length === 0) return null;
  const lines = events.map((e, i) => {
    const meta = [e.runtimeSurface && `surface=${e.runtimeSurface}`, e.source && `source=${e.source}`]
      .filter(Boolean)
      .join(", ");
    return `${i + 1}. ${e.summary}${meta ? ` (${meta})` : ""}`;
  });
  const block = [
    "[ORACLE MEMORY CONTEXT]",
    "Recent topics from your Oracle voice sessions (oldest first, compact):",
    ...lines,
    "Use this only as lightweight background context. Do not repeat or narrate it back unless directly relevant.",
  ].join("\n");
  return block.length > ORACLE_MEMORY_CONTEXT_MAX ? block.slice(0, ORACLE_MEMORY_CONTEXT_MAX) : block;
}
