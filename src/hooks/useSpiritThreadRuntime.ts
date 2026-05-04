"use client";

/* eslint-disable react-hooks/set-state-in-effect -- Dexie search + sidebar; same pattern as pre-extract SpiritChat */
import { useEffect, useMemo, useState } from "react";

import { usePersistentChat } from "@/hooks/usePersistentChat";
import { filterFolderSidebarModel } from "@/lib/chat-folder-utils";
import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import type { ChatFolder, ChatMessage, ChatThread } from "@/lib/chat-db.types";
import { searchThreadsAndMessages } from "@/lib/chat-persistence";

/** Search sidebar empty state — Dexie returned zero thread ids for query */
export function spiritThreadSearchEmpty(args: {
  sidebarFeaturesEnabled: boolean;
  debouncedSearchTrimmed: string;
  searchPending: boolean;
  searchAllow: Set<string> | null;
}): boolean {
  return (
    Boolean(args.sidebarFeaturesEnabled) &&
    args.debouncedSearchTrimmed.length > 0 &&
    !args.searchPending &&
    args.searchAllow !== null &&
    args.searchAllow.size === 0
  );
}

export type UseSpiritThreadRuntimeInput = {
  /** Mirrors `persistence` prop — Dexie on/off */
  enabled: boolean;
  /** Saved-thread sidebar features (search, debounced hits); off for ephemeral surfaces */
  sidebarFeaturesEnabled: boolean;
};

export type SpiritThreadRuntime = {
  persistent: ReturnType<typeof usePersistentChat>;
  savedThreadCount: number;
  rootThreads: ChatThread[];
  folderSections: FolderSidebarSection[];
  allFolders: ChatFolder[];
  activeThreadId: string | null;
  draftActive: boolean;
  activeThread: ChatThread | null;
  activeThreadIdOrDraftKey: string;
  persistedMessages: ChatMessage[] | undefined;
  isPersistedHydrationReady: boolean;
  isThreadHydrating: boolean;

  beginNewChat(): void;
  selectThread(threadId: string): void;
  deleteThread(threadId: string): void;
  renameThread(threadId: string, title: string): void;
  pinThread(threadId: string): void;
  unpinThread(threadId: string): void;

  createFolder(name: string): Promise<boolean>;
  renameFolder(folderId: string, name: string): Promise<boolean>;
  deleteFolder(folderId: string): void;
  toggleFolderCollapsed(folderId: string): void;
  moveThreadToFolder(threadId: string, folderId: string | null): void;
  commitThreadSidebarOrder: ReturnType<
    typeof usePersistentChat
  >["commitThreadSidebarOrder"];

  searchQuery: string;
  setSearchQuery: (query: string) => void;
  debouncedSearchTrimmed: string;
  searchPending: boolean;
  searchSnippets: Record<string, string>;
  searchAllow: Set<string> | null;
  searchEmptyResults: boolean;
  pinnedThreadsDisplay: ChatThread[];
};

export function useSpiritThreadRuntime(
  input: UseSpiritThreadRuntimeInput,
): SpiritThreadRuntime {
  const persistent = usePersistentChat(input.enabled);

  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(searchInput), 220);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  const [searchAllow, setSearchAllow] = useState<Set<string> | null>(null);
  const [searchSnippets, setSearchSnippets] = useState<Record<string, string>>({});
  const [searchPending, setSearchPending] = useState(false);

  useEffect(() => {
    if (!input.sidebarFeaturesEnabled || !persistent.enabled) {
      setSearchAllow(null);
      setSearchSnippets({});
      setSearchPending(false);
      return;
    }
    const q = debouncedSearch.trim();
    if (!q) {
      setSearchAllow(null);
      setSearchSnippets({});
      setSearchPending(false);
      return;
    }
    setSearchPending(true);
    let cancelled = false;
    void searchThreadsAndMessages(q).then((hits) => {
      if (cancelled) return;
      const rec: Record<string, string> = {};
      const s = new Set<string>();
      for (const h of hits) {
        s.add(h.thread.id);
        if (h.snippet && !rec[h.thread.id]) rec[h.thread.id] = h.snippet;
      }
      setSearchAllow(s);
      setSearchSnippets(rec);
      setSearchPending(false);
    });
    return () => {
      cancelled = true;
    };
  }, [input.sidebarFeaturesEnabled, persistent.enabled, debouncedSearch]);

  const filteredSidebarModel = useMemo(() => {
    const base = {
      rootThreads: persistent.rootThreads,
      folderSections: persistent.folderSections,
    };
    if (!searchAllow) return base;
    return filterFolderSidebarModel(base, searchAllow);
  }, [persistent.rootThreads, persistent.folderSections, searchAllow]);

  const pinnedThreadsDisplay = useMemo(() => {
    const list = persistent.visibleThreads.filter((t) => t.pinned);
    list.sort((a, b) => (b.pinnedAt ?? 0) - (a.pinnedAt ?? 0));
    if (!searchAllow) return list;
    return list.filter((t) => searchAllow.has(t.id));
  }, [persistent.visibleThreads, searchAllow]);

  const activeThread =
    persistent.activeThreadId == null
      ? null
      : persistent.visibleThreads.find((t) => t.id === persistent.activeThreadId) ?? null;

  const activeThreadIdOrDraftKey = persistent.draftLaneActive
    ? `draft:${persistent.draftLaneId ?? ""}`
    : (persistent.activeThreadId ?? "");

  const isThreadHydrating = Boolean(
    persistent.messagesLoading &&
      !persistent.draftLaneActive &&
      persistent.activeThreadId,
  );

  const debouncedSearchTrimmed = debouncedSearch.trim();
  const searchEmptyResults = spiritThreadSearchEmpty({
    sidebarFeaturesEnabled: input.sidebarFeaturesEnabled,
    debouncedSearchTrimmed,
    searchPending,
    searchAllow,
  });

  return useMemo(
    (): SpiritThreadRuntime => ({
      persistent,
      savedThreadCount: persistent.visibleThreads.length,
      rootThreads: filteredSidebarModel.rootThreads,
      folderSections: filteredSidebarModel.folderSections,
      allFolders: persistent.folders,
      activeThreadId: persistent.activeThreadId,
      draftActive: persistent.draftLaneActive,
      activeThread,
      activeThreadIdOrDraftKey,
      persistedMessages: persistent.persistedMessages,
      isPersistedHydrationReady: persistent.isPersistedHydrationReady,
      isThreadHydrating,

      beginNewChat: persistent.beginNewDraftChat,
      selectThread: persistent.selectPersistedThread,
      deleteThread: persistent.deleteThread,
      renameThread: persistent.renameThread,
      pinThread: persistent.pinThread,
      unpinThread: persistent.unpinThread,

      createFolder: persistent.createFolder,
      renameFolder: persistent.renameFolder,
      deleteFolder: persistent.deleteFolder,
      toggleFolderCollapsed: persistent.toggleFolderCollapsed,
      moveThreadToFolder: persistent.moveThreadToFolder,
      commitThreadSidebarOrder: persistent.commitThreadSidebarOrder,

      searchQuery: searchInput,
      setSearchQuery: setSearchInput,
      debouncedSearchTrimmed,
      searchPending,
      searchSnippets,
      searchAllow,
      searchEmptyResults,
      pinnedThreadsDisplay,
    }),
    [
      persistent,
      filteredSidebarModel.rootThreads,
      filteredSidebarModel.folderSections,
      activeThread,
      activeThreadIdOrDraftKey,
      searchInput,
      debouncedSearchTrimmed,
      searchPending,
      searchSnippets,
      searchAllow,
      searchEmptyResults,
      pinnedThreadsDisplay,
      isThreadHydrating,
    ],
  );
}
