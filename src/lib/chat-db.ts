// ── SpiritChatDB - local IndexedDB facade (Spirit OS chat overhaul) ────────────
import Dexie, { type Table } from "dexie";

import type { ChatFolder, ChatMessage, ChatThread, OracleMemoryEvent } from "@/lib/chat-db.types";

export function isBrowserChatDbAvailable(): boolean {
  return typeof window !== "undefined";
}

export class SpiritChatDB extends Dexie {
  folders!: Table<ChatFolder, string>;
  threads!: Table<ChatThread, string>;
  messages!: Table<ChatMessage, string>;
  oracleMemoryEvents!: Table<OracleMemoryEvent, string>;

  constructor() {
    super("SpiritChatDB");
    this.version(1).stores({
      threads: "id, updatedAt, createdAt, archived",
      messages: "id, threadId, createdAt",
    });
    this.version(2)
      .stores({
        folders: "id, order, updatedAt, createdAt",
        threads: "id, folderId, order, updatedAt, createdAt, archived",
        messages: "id, threadId, createdAt",
      })
      .upgrade(async (tx) => {
        // ── v2: folders table appears; thread rows stay valid without folderId/order ─
        const t = tx.table("threads") as typeof this.threads;
        await t.toCollection().modify((row: ChatThread) => {
          if (row.folderId === "") row.folderId = undefined;
        });
      });
    // ── v3: optional modelProfileId on threads (additive; old rows stay valid) ─────
    this.version(3).stores({
      folders: "id, order, updatedAt, createdAt",
      threads:
        "id, folderId, order, modelProfileId, updatedAt, createdAt, archived",
      messages: "id, threadId, createdAt",
    });
    // ── v4: pinned threads (Prompt 10A) - additive fields, default unpinned ───────
    this.version(4)
      .stores({
        folders: "id, order, updatedAt, createdAt",
        threads:
          "id, folderId, order, modelProfileId, pinned, pinnedAt, updatedAt, createdAt, archived",
        messages: "id, threadId, createdAt",
      })
      .upgrade(async (tx) => {
        const t = tx.table("threads") as typeof this.threads;
        await t.toCollection().modify((row: ChatThread) => {
          if (row.pinned == null) row.pinned = false;
        });
      });
    // ── v5: oracle memory events (additive; table absent → no Oracle memory writes) ─
    this.version(5).stores({
      folders: "id, order, updatedAt, createdAt",
      threads:
        "id, folderId, order, modelProfileId, pinned, pinnedAt, updatedAt, createdAt, archived",
      messages: "id, threadId, createdAt",
      oracleMemoryEvents: "id, createdAt",
    });
  }
}

/** Browser-only Dexie singleton; null on SSR / environments without IndexedDB. */
export const db: SpiritChatDB | null = isBrowserChatDbAvailable()
  ? new SpiritChatDB()
  : null;
