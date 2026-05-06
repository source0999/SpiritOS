"use client";

// ── useChatFolders - Dexie.live folder rail (Prompt 5; no drag ghosts yet) ──────
import { useLiveQuery } from "dexie-react-hooks";
import { useCallback, useMemo } from "react";

import { db } from "@/lib/chat-db";
import type { ChatFolder } from "@/lib/chat-db.types";
import { sortFoldersByOrderThenUpdated } from "@/lib/chat-folder-utils";
import {
  createFolder as createFolderRow,
  deleteFolder as deleteFolderRow,
  updateFolderCollapsed,
  updateFolderName,
} from "@/lib/chat-persistence";

export function useChatFolders(enabled: boolean) {
  const resolved = useLiveQuery(
    () => {
      if (!enabled || !db) return [] as ChatFolder[];
      return db.folders.toArray();
    },
    [enabled],
  );

  const folders = useMemo(
    () => sortFoldersByOrderThenUpdated(resolved ?? []),
    [resolved],
  );

  const isLoading = enabled && resolved === undefined;

  const createNewFolder = useCallback(async (name: string): Promise<boolean> => {
    if (!enabled || !name.trim()) return false;
    const row = await createFolderRow(name.trim());
    return row !== undefined;
  }, [enabled]);

  const renameFolder = useCallback(
    async (id: string, name: string): Promise<boolean> => {
      if (!enabled || !name.trim()) return false;
      return updateFolderName(id, name.trim());
    },
    [enabled],
  );

  const removeFolder = useCallback(
    async (id: string) => {
      if (!enabled) return;
      await deleteFolderRow(id, { moveThreadsToRoot: true });
    },
    [enabled],
  );

  const setFolderCollapsed = useCallback(
    async (id: string, collapsed: boolean) => {
      if (!enabled) return;
      await updateFolderCollapsed(id, collapsed);
    },
    [enabled],
  );

  const toggleFolderCollapsed = useCallback(
    async (id: string) => {
      if (!enabled || !db) return;
      const row = await db.folders.get(id);
      if (!row) return;
      await updateFolderCollapsed(id, !Boolean(row.collapsed));
    },
    [enabled],
  );

  return {
    folders,
    isLoading,
    createNewFolder,
    renameFolder,
    removeFolder,
    setFolderCollapsed,
    toggleFolderCollapsed,
  };
}
