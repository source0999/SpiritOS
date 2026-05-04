// ── Shared AI SDK message helpers ───────────────────────────────────────────
// > Design language: _blueprints/design_system.md — one source, zero dupes
import type { UIMessage } from "ai";

import type { ChatMessage } from "@/lib/chat-db.types";

/** Pull plain text from v5 UI message parts (no duplicate implementations). */
export function textFromParts(message: UIMessage): string {
  return message.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("");
}

/** Last user message text in transcript order (AI SDK UIMessage parts). */
export function lastUserTextFromMessages(messages: UIMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m?.role === "user") return textFromParts(m);
  }
  return "";
}

export function persistedChatRowsToUIMessages(rows: ChatMessage[]): UIMessage[] {
  return rows
    .filter((row) => row.role === "user" || row.role === "assistant")
    .map((row) => ({
      id: row.id,
      role: row.role,
      parts: [{ type: "text" as const, text: row.text }],
    }));
}

/**
 * Dexie hydrate + streaming useChat briefly double-book the same `id`.
 * First-seen id keeps chat order; duplicate slots collapse to latest payload (live bubble wins).
 */
export function dedupeUIMessagesById(messages: UIMessage[]): UIMessage[] {
  const order: string[] = [];
  const byId = new Map<string, UIMessage>();

  for (const m of messages) {
    if (!byId.has(m.id)) order.push(m.id);
    byId.set(m.id, m);
  }

  const out: UIMessage[] = [];
  for (const id of order) {
    const row = byId.get(id);
    if (row) out.push(row);
  }
  return out;
}

/** Replace text parts; keeps non-text parts intact. */
export function updateUIMessageText(
  messages: UIMessage[],
  id: string,
  text: string,
): UIMessage[] {
  return messages.map((m) => {
    if (m.id !== id) return m;
    const rest = m.parts.filter((p) => p.type !== "text");
    return { ...m, parts: [...rest, { type: "text" as const, text }] };
  });
}

export function deleteUIMessageById(
  messages: UIMessage[],
  id: string,
): UIMessage[] {
  return messages.filter((m) => m.id !== id);
}

/** Nearest user message strictly before `messageId` in list order. */
export function findPreviousUserMessage(
  messages: UIMessage[],
  messageId: string,
): UIMessage | undefined {
  const idx = messages.findIndex((m) => m.id === messageId);
  if (idx <= 0) return undefined;
  for (let i = idx - 1; i >= 0; i--) {
    const m = messages[i]!;
    if (m.role === "user") return m;
  }
  return undefined;
}
