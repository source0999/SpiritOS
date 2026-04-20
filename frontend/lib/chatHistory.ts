import type { Message } from "@/lib/db.types";
import { SPIRIT_HISTORY_MESSAGE_CAP } from "@/lib/spiritConstants";

/** Map Dexie thread messages to Ollama chat turns (spirit → assistant). */
export function buildSpiritHistoryFromMessages(
  msgs: Message[] | undefined,
): { role: "user" | "assistant"; content: string }[] {
  if (!msgs?.length) return [];
  const sorted = [...msgs].sort((a, b) => a.createdAt - b.createdAt);
  const turns: { role: "user" | "assistant"; content: string }[] = [];
  for (const m of sorted) {
    const t = m.text?.trim();
    if (!t) continue;
    if (m.role === "user") turns.push({ role: "user", content: t });
    else turns.push({ role: "assistant", content: t });
  }
  return turns.slice(-SPIRIT_HISTORY_MESSAGE_CAP);
}
