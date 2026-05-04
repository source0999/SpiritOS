// ── chat-persistence — browser-guarded CRUD helpers (no UI, no transports) ────
// > Failure mode: console.error + soft return — never chuck the orchestrator shell.
import { db, isBrowserChatDbAvailable } from "@/lib/chat-db";
import { isDuplicateFolderName, sortThreadsWithOrderFallback } from "@/lib/chat-folder-utils";
import type {
  ChatFolder,
  ChatMessage,
  ChatThread,
  NewChatMessageInput,
  NewChatThreadInput,
} from "@/lib/chat-db.types";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";

const NEW_CHAT_TITLE = "New chat";

export function buildTitleFromText(text: string): string {
  const oneLine = text.trim().replace(/\s+/g, " ");
  if (!oneLine) return NEW_CHAT_TITLE;
  const t = oneLine.slice(0, 42).trimEnd();
  return t || NEW_CHAT_TITLE;
}

export function generateChatRecordId(): string {
  try {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
  } catch {
    /* fallthrough */
  }
  return `id_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
}

export async function createThread(
  input?: Partial<NewChatThreadInput>,
): Promise<ChatThread | undefined> {
  if (!db) return undefined;
  const now = Date.now();
  const thread: ChatThread = {
    id: generateChatRecordId(),
    title: input?.title ?? NEW_CHAT_TITLE,
    createdAt: now,
    updatedAt: now,
    archived: input?.archived ?? false,
    folderId: input?.folderId ?? undefined,
    order: input?.order,
    ...(input?.modelProfileId != null
      ? { modelProfileId: input.modelProfileId }
      : {}),
  };
  try {
    await db.threads.add(thread);
    return thread;
  } catch (e) {
    console.error("[chat-persistence] createThread:", e);
    return undefined;
  }
}

export async function getThread(id: string): Promise<ChatThread | undefined> {
  if (!db) return undefined;
  try {
    return await db.threads.get(id);
  } catch (e) {
    console.error("[chat-persistence] getThread:", e);
    return undefined;
  }
}

export async function updateThreadTitle(id: string, title: string): Promise<void> {
  if (!db) return;
  try {
    const now = Date.now();
    await db.threads.update(id, {
      title,
      updatedAt: now,
    });
  } catch (e) {
    console.error("[chat-persistence] updateThreadTitle:", e);
  }
}

export async function updateThreadModelProfile(
  threadId: string,
  profileId: ModelProfileId,
): Promise<void> {
  if (!db) return;
  try {
    await db.threads.update(threadId, {
      modelProfileId: profileId,
      updatedAt: Date.now(),
    });
  } catch (e) {
    console.error("[chat-persistence] updateThreadModelProfile:", e);
  }
}

export async function touchThread(id: string): Promise<void> {
  if (!db) return;
  try {
    await db.threads.update(id, { updatedAt: Date.now() });
  } catch (e) {
    console.error("[chat-persistence] touchThread:", e);
  }
}

export async function listThreads(): Promise<ChatThread[]> {
  if (!db) return [];
  try {
    return await db.threads.orderBy("updatedAt").reverse().toArray();
  } catch (e) {
    console.error("[chat-persistence] listThreads:", e);
    return [];
  }
}

export async function deleteThread(id: string): Promise<void> {
  if (!db) return;
  try {
    await db.transaction("rw", db.threads, db.messages, async () => {
      await db!.messages.where("threadId").equals(id).delete();
      await db!.threads.delete(id);
    });
  } catch (e) {
    console.error("[chat-persistence] deleteThread:", e);
  }
}

async function countUserMessages(threadId: string): Promise<number> {
  if (!db) return 0;
  try {
    return await db.messages
      .where("threadId")
      .equals(threadId)
      .filter((m) => m.role === "user")
      .count();
  } catch (e) {
    console.error("[chat-persistence] countUserMessages:", e);
    return 0;
  }
}

async function maybeRenameFromFirstUserMessage(
  threadId: string,
  userPlainText: string,
): Promise<void> {
  if (!db) return;
  try {
    const thread = await getThread(threadId);
    if (!thread || thread.title !== NEW_CHAT_TITLE) return;
    const n = await countUserMessages(threadId);
    if (n !== 1) return;
    await updateThreadTitle(threadId, buildTitleFromText(userPlainText));
  } catch (e) {
    console.error("[chat-persistence] maybeRenameFromFirstUserMessage:", e);
  }
}

/** Inserts row + bumps thread.updatedAt (+ auto-retitle stub thread on first user line). */
export async function saveMessage(
  input: NewChatMessageInput,
): Promise<ChatMessage | undefined> {
  if (!db || !isBrowserChatDbAvailable()) return undefined;
  const now = Date.now();
  const row: ChatMessage = {
    id: input.id ?? generateChatRecordId(),
    threadId: input.threadId,
    role: input.role,
    text: input.text,
    createdAt: now,
    updatedAt: now,
  };
  try {
    await db.messages.add(row);
    await touchThread(input.threadId);
    if (input.role === "user") {
      await maybeRenameFromFirstUserMessage(input.threadId, input.text);
    }
    return row;
  } catch (e) {
    console.error("[chat-persistence] saveMessage:", e);
    return undefined;
  }
}

export async function listMessages(threadId: string): Promise<ChatMessage[]> {
  if (!db) return [];
  try {
    return await db.messages.where("threadId").equals(threadId).sortBy("createdAt");
  } catch (e) {
    console.error("[chat-persistence] listMessages:", e);
    return [];
  }
}

export async function clearThreadMessages(threadId: string): Promise<void> {
  if (!db) return;
  try {
    await db.messages.where("threadId").equals(threadId).delete();
    await touchThread(threadId);
  } catch (e) {
    console.error("[chat-persistence] clearThreadMessages:", e);
  }
}

/** Persist outbound user plaintext (Dexie-only; align `messageId` with useChat user id when persisting-first). */
export async function persistUserOutboundMessage(
  threadId: string,
  text: string,
  messageId?: string,
): Promise<void> {
  if (!threadId.trim() || !text.trim()) return;
  await saveMessage({ threadId, role: "user", text, id: messageId });
}

/**
 * Persist a completed assistant turn once (idempotent per message id).
 * Does not duplicate if the row already exists (thread switch safe).
 */
export async function persistAssistantOutboundIfAbsent(
  threadId: string,
  messageId: string,
  text: string,
): Promise<void> {
  if (!db || !threadId.trim() || !messageId.trim()) return;
  const trimmed = text.trim();
  if (!trimmed) return;
  try {
    const existing = await db.messages.get(messageId);
    if (existing) return;
    await saveMessage({ threadId, role: "assistant", text: trimmed, id: messageId });
  } catch (e) {
    console.error("[chat-persistence] persistAssistantOutboundIfAbsent:", e);
  }
}

export async function updateMessageText(messageId: string, text: string): Promise<void> {
  if (!db) return;
  try {
    const row = await db.messages.get(messageId);
    if (!row) return;
    await db.messages.update(messageId, {
      text,
      updatedAt: Date.now(),
    });
    await touchThread(row.threadId);
  } catch (e) {
    console.error("[chat-persistence] updateMessageText:", e);
  }
}

export async function deleteMessage(messageId: string): Promise<void> {
  if (!db) return;
  try {
    const row = await db.messages.get(messageId);
    if (!row) return;
    await db.messages.delete(messageId);
    await touchThread(row.threadId);
  } catch (e) {
    console.error("[chat-persistence] deleteMessage:", e);
  }
}

export async function deleteMessages(messageIds: string[]): Promise<void> {
  if (!db || messageIds.length === 0) return;
  try {
    const threadIds = new Set<string>();
    for (const id of messageIds) {
      const row = await db.messages.get(id);
      if (row) threadIds.add(row.threadId);
    }
    await db.transaction("rw", db.messages, async () => {
      for (const id of messageIds) {
        await db!.messages.delete(id);
      }
    });
    for (const tid of threadIds) {
      await touchThread(tid);
    }
  } catch (e) {
    console.error("[chat-persistence] deleteMessages:", e);
  }
}

// ── Folders (Prompt 5) — CRUD only; delete never nukes threads ─────────────────

export async function createFolder(
  name?: string,
): Promise<ChatFolder | undefined> {
  if (!db) return undefined;
  const now = Date.now();
  let order = now;
  try {
    const last = await db.folders.orderBy("order").last();
    if (last != null) order = last.order + 1;
  } catch (e) {
    console.error("[chat-persistence] createFolder order probe:", e);
  }
  const trimmedName = name?.trim() || "New folder";
  try {
    const existing = await db.folders.toArray();
    if (isDuplicateFolderName(trimmedName, existing)) {
      return undefined;
    }
  } catch (e) {
    console.error("[chat-persistence] createFolder duplicate probe:", e);
  }
  const folder: ChatFolder = {
    id: generateChatRecordId(),
    name: trimmedName,
    createdAt: now,
    updatedAt: now,
    order,
    collapsed: false,
  };
  try {
    await db.folders.add(folder);
    return folder;
  } catch (e) {
    console.error("[chat-persistence] createFolder:", e);
    return undefined;
  }
}

export async function listFolders(): Promise<ChatFolder[]> {
  if (!db) return [];
  try {
    const rows = await db.folders.toArray();
    rows.sort((a, b) => a.order - b.order || b.updatedAt - a.updatedAt);
    return rows;
  } catch (e) {
    console.error("[chat-persistence] listFolders:", e);
    return [];
  }
}

export async function updateFolderName(id: string, name: string): Promise<boolean> {
  if (!db) return false;
  const trimmed = name.trim();
  if (!trimmed) return false;
  try {
    const rows = await db.folders.toArray();
    if (isDuplicateFolderName(trimmed, rows, id)) {
      return false;
    }
    await db.folders.update(id, { name: trimmed, updatedAt: Date.now() });
    return true;
  } catch (e) {
    console.error("[chat-persistence] updateFolderName:", e);
    return false;
  }
}

export async function updateFolderCollapsed(
  id: string,
  collapsed: boolean,
): Promise<void> {
  if (!db) return;
  try {
    await db.folders.update(id, { collapsed, updatedAt: Date.now() });
  } catch (e) {
    console.error("[chat-persistence] updateFolderCollapsed:", e);
  }
}

export async function deleteFolder(
  id: string,
  options?: { moveThreadsToRoot?: boolean },
): Promise<void> {
  if (!db) return;
  const moveThreadsToRoot = options?.moveThreadsToRoot !== false;
  try {
    await db.transaction("rw", db.threads, db.folders, async () => {
      if (moveThreadsToRoot) {
        const rows = await db!.threads.where("folderId").equals(id).toArray();
        for (const t of rows) {
          await db!.threads.update(t.id, {
            folderId: undefined,
          });
        }
      }
      await db!.folders.delete(id);
    });
  } catch (e) {
    console.error("[chat-persistence] deleteFolder:", e);
    return;
  }
  try {
    const rootAll = (await db.threads.toArray()).filter((t) => !t.folderId);
    const ids = sortThreadsWithOrderFallback(rootAll).map((t) => t.id);
    await reorderThreadsInFolder(null, ids);
  } catch (e) {
    console.error("[chat-persistence] deleteFolder root reorder:", e);
  }
}

export async function updateThreadFolderAndOrder(
  threadId: string,
  folderId: string | null,
  order: number,
): Promise<void> {
  if (!db) return;
  try {
    await db.threads.update(threadId, {
      folderId: folderId ?? undefined,
      order,
      updatedAt: Date.now(),
    });
  } catch (e) {
    console.error("[chat-persistence] updateThreadFolderAndOrder:", e);
  }
}

export async function reorderThreadsInFolder(
  folderId: string | null,
  orderedThreadIds: string[],
): Promise<void> {
  if (!db) return;
  const fid = folderId ?? undefined;
  try {
    await db.transaction("rw", db.threads, async () => {
      let i = 0;
      for (const id of orderedThreadIds) {
        i += 1;
        await db!.threads.update(id, {
          folderId: fid,
          order: i * 1000,
        });
      }
    });
  } catch (e) {
    console.error("[chat-persistence] reorderThreadsInFolder:", e);
  }
}

export async function reorderFolders(orderedFolderIds: string[]): Promise<void> {
  if (!db) return;
  try {
    await db.transaction("rw", db.folders, async () => {
      let i = 0;
      for (const id of orderedFolderIds) {
        i += 1;
        await db!.folders.update(id, { order: i * 1000, updatedAt: Date.now() });
      }
    });
  } catch (e) {
    console.error("[chat-persistence] reorderFolders:", e);
  }
}

export async function moveThreadToFolder(
  threadId: string,
  folderId: string | null,
): Promise<void> {
  if (!db) return;
  try {
    const fid = folderId ?? undefined;
    const all = await db.threads.toArray();
    const siblings = all.filter(
      (t) => (t.folderId ?? undefined) === fid && t.id !== threadId,
    );
    let maxO = 0;
    for (const t of siblings) {
      if (typeof t.order === "number" && !Number.isNaN(t.order)) {
        maxO = Math.max(maxO, t.order);
      }
    }
    await db.threads.update(threadId, {
      folderId: fid,
      order: maxO + 1000,
      updatedAt: Date.now(),
    });
  } catch (e) {
    console.error("[chat-persistence] moveThreadToFolder:", e);
  }
}

// ── Pins + local search (Prompt 10A) ────────────────────────────────────────────

export type ChatThreadSearchHit = {
  thread: ChatThread;
  snippet?: string;
};

/** Case-insensitive match on title + message bodies; empty query ⇒ []. */
export async function searchThreadsAndMessages(
  query: string,
): Promise<ChatThreadSearchHit[]> {
  if (!db) return [];
  const qq = query.trim().toLowerCase();
  if (!qq) return [];

  try {
    const threads = await db.threads.toArray();
    const hits: ChatThreadSearchHit[] = [];
    const seen = new Set<string>();

    for (const t of threads) {
      if (t.archived) continue;
      if (t.title.toLowerCase().includes(qq)) {
        seen.add(t.id);
        hits.push({ thread: t });
      }
    }

    const msgRows = await db.messages
      .filter((m) => m.text.toLowerCase().includes(qq))
      .toArray();

    for (const m of msgRows) {
      if (seen.has(m.threadId)) continue;
      const thread = threads.find((x) => x.id === m.threadId);
      if (!thread || thread.archived) continue;
      seen.add(m.threadId);
      const lower = m.text.toLowerCase();
      const idx = lower.indexOf(qq);
      const start = Math.max(0, idx - 36);
      const end = Math.min(m.text.length, idx + qq.length + 72);
      let snippet = m.text.slice(start, end).replace(/\s+/g, " ");
      if (start > 0) snippet = `…${snippet}`;
      if (end < m.text.length) snippet = `${snippet}…`;
      hits.push({ thread, snippet });
    }

    hits.sort((a, b) => b.thread.updatedAt - a.thread.updatedAt);
    return hits;
  } catch (e) {
    console.error("[chat-persistence] searchThreadsAndMessages:", e);
    return [];
  }
}

export async function pinThread(id: string): Promise<void> {
  if (!db) return;
  try {
    const now = Date.now();
    await db.threads.update(id, {
      pinned: true,
      pinnedAt: now,
      updatedAt: now,
    });
  } catch (e) {
    console.error("[chat-persistence] pinThread:", e);
  }
}

export async function unpinThread(id: string): Promise<void> {
  if (!db) return;
  try {
    await db.threads.update(id, {
      pinned: false,
      pinnedAt: undefined,
      updatedAt: Date.now(),
    });
  } catch (e) {
    console.error("[chat-persistence] unpinThread:", e);
  }
}
