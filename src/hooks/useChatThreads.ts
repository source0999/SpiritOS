"use client";

// ── useChatThreads — Dexie.live thread list primitives (Prompt 3 sidebar eats this) ─
import { useLiveQuery } from "dexie-react-hooks";
import { useCallback } from "react";

import { db } from "@/lib/chat-db";
import { createThread, deleteThread, updateThreadTitle } from "@/lib/chat-persistence";
import type { ChatThread } from "@/lib/chat-db.types";

export function useChatThreads(enabled: boolean) {
  const threadsResolved = useLiveQuery(
    () => {
      if (!enabled || !db) return [];
      return db.threads.orderBy("updatedAt").reverse().toArray();
    },
    [enabled],
  );

  /** Sync `[]` when disabled skips the undefined suspense frame; Dexie awaits still start undefined while enabled */
  const threads = threadsResolved ?? ([] as ChatThread[]);
  const isLoading = enabled && threadsResolved === undefined;

  const createNewThread = useCallback(async () => {
    if (!enabled) return undefined;
    const row = await createThread({ title: "New chat" });
    return row?.id;
  }, [enabled]);

  const renameThread = useCallback(
    async (id: string, title: string) => {
      if (!enabled || !title.trim()) return;
      await updateThreadTitle(id, title.trim());
    },
    [enabled],
  );

  const removeThread = useCallback(
    async (id: string) => {
      if (!enabled) return;
      await deleteThread(id);
    },
    [enabled],
  );

  return {
    threads,
    isLoading,
    createNewThread,
    renameThread,
    removeThread,
  };
}
