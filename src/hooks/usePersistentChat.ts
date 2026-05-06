"use client";

// ── usePersistentChat - Dexie shell: draft lane + optimistic deletes (no phantom rows) ─
import { useLiveQuery } from "dexie-react-hooks";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useChatFolders } from "@/hooks/useChatFolders";
import { useChatThreads } from "@/hooks/useChatThreads";

import { buildFolderSidebarModel } from "@/lib/chat-folder-utils";
import { db } from "@/lib/chat-db";
import type { ChatMessage, ChatThread } from "@/lib/chat-db.types";
import {
  buildTitleFromText,
  createThread,
  deleteMessage as persistDeleteMessage,
  deleteMessages as persistDeleteMessages,
  generateChatRecordId,
  moveThreadToFolder as persistMoveThreadToFolder,
  reorderFolders,
  reorderThreadsInFolder,
  persistAssistantOutboundIfAbsent,
  persistUserOutboundMessage,
  updateMessageText as persistUpdateMessageText,
  updateThreadModelProfile as persistUpdateThreadModelProfile,
  pinThread as persistPinThread,
  unpinThread as persistUnpinThread,
} from "@/lib/chat-persistence";
import type { ThreadReorderOp } from "@/lib/chat-sidebar-dnd";
import { DEFAULT_MODEL_PROFILE_ID } from "@/lib/spirit/model-profile.types";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";

function mintDraftLaneId(): string {
  return `draft:${generateChatRecordId()}`;
}

export function usePersistentChat(enabled: boolean) {
  const {
    threads: rawThreads,
    isLoading: threadsLoading,
    createNewThread,
    renameThread,
    removeThread,
  } = useChatThreads(enabled);

  const {
    folders,
    isLoading: foldersLoading,
    createNewFolder,
    renameFolder,
    removeFolder,
    toggleFolderCollapsed,
    setFolderCollapsed,
  } = useChatFolders(enabled);

  const threadsRef = useRef(rawThreads);

  useEffect(() => {
    threadsRef.current = rawThreads;
  }, [rawThreads]);

  const activeThreadIdRef = useRef<string | null>(null);

  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [draftLaneId, setDraftLaneId] = useState<string | null>(null);
  const [draftModelProfileId, setDraftModelProfileId] = useState<ModelProfileId>(
    DEFAULT_MODEL_PROFILE_ID,
  );
  const [pendingDeletedIds, setPendingDeletedIds] = useState(
    () => new Set<string>(),
  );

  useEffect(() => {
    activeThreadIdRef.current = activeThreadId;
  }, [activeThreadId]);

  const visibleThreads = useMemo(
    () => rawThreads.filter((t) => !pendingDeletedIds.has(t.id)),
    [rawThreads, pendingDeletedIds],
  );

  const folderModel = useMemo(
    () => buildFolderSidebarModel(visibleThreads, folders),
    [visibleThreads, folders],
  );

  const draftLaneActive = Boolean(draftLaneId && activeThreadId === null);
  /** While Dexie threads are loading, block only `activeThreadId` paths - first send can mint a thread. */
  const canSendOutbound =
    draftLaneActive || Boolean(activeThreadId) || threadsLoading;

  const activeModelProfileId = useMemo((): ModelProfileId => {
    if (!enabled) return DEFAULT_MODEL_PROFILE_ID;
    if (draftLaneActive) return draftModelProfileId;
    if (activeThreadId) {
      const row = visibleThreads.find((t) => t.id === activeThreadId);
      return row?.modelProfileId ?? DEFAULT_MODEL_PROFILE_ID;
    }
    return DEFAULT_MODEL_PROFILE_ID;
  }, [
    enabled,
    draftLaneActive,
    draftModelProfileId,
    activeThreadId,
    visibleThreads,
  ]);

  const persistedSnapshot = useLiveQuery(
    () => {
      if (!enabled || !db || !activeThreadId) return [] as ChatMessage[];
      return db.messages.where("threadId").equals(activeThreadId).sortBy("createdAt");
    },
    [enabled, activeThreadId],
  );

  const isPersistedHydrationReady =
    !enabled || activeThreadId === null || persistedSnapshot !== undefined;

  const enterDraftLane = useCallback(() => {
    setDraftModelProfileId(DEFAULT_MODEL_PROFILE_ID);
    setDraftLaneId(mintDraftLaneId());
    setActiveThreadId(null);
  }, []);

  const selectPersistedThread = useCallback((id: string) => {
    setDraftLaneId(null);
    setActiveThreadId(id);
  }, []);

  /* eslint-disable react-hooks/set-state-in-effect -- Dexie/live bootstrap reconciles observable thread list vs React focus */
  useEffect(() => {
    if (!enabled) return;
    if (threadsLoading) return;
    if (draftLaneId !== null) return;

    if (activeThreadId) {
      if (visibleThreads.some((t) => t.id === activeThreadId)) return;
      if (visibleThreads.length > 0) {
        setActiveThreadId(visibleThreads[0]!.id);
        setDraftLaneId(null);
        return;
      }
      enterDraftLane();
      return;
    }

    if (visibleThreads.length > 0) {
      setActiveThreadId(visibleThreads[0]!.id);
      return;
    }

    enterDraftLane();
  }, [
    enabled,
    threadsLoading,
    visibleThreads,
    activeThreadId,
    draftLaneId,
    enterDraftLane,
  ]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const beginNewDraftChat = useCallback(() => {
    enterDraftLane();
  }, [enterDraftLane]);

  /** Legacy/tests: persist shell thread immediately - UI should prefer draft lane instead. */
  const createPersistedShellThread = useCallback(async () => {
    const id = await createNewThread();
    if (id) {
      setDraftLaneId(null);
      setActiveThreadId(id);
    }
    return id;
  }, [createNewThread]);

  const persistAssistantMessageToThread = useCallback(
    async (threadId: string, messageId: string, text: string) => {
      if (!enabled) return;
      await persistAssistantOutboundIfAbsent(threadId, messageId, text);
    },
    [enabled],
  );

  const persistUserOutboundForSend = useCallback(
    async (
      text: string,
      preferredUserMessageId?: string,
    ): Promise<{ threadId: string } | null> => {
      if (!enabled) return null;
      const trimmed = text.trim();
      if (!trimmed) return null;

      if (activeThreadId) {
        await persistUserOutboundMessage(
          activeThreadId,
          trimmed,
          preferredUserMessageId,
        );
        return { threadId: activeThreadId };
      }

      const row = await createThread({
        title: buildTitleFromText(trimmed),
        modelProfileId: draftModelProfileId,
      });
      if (!row) return null;

      await persistUserOutboundMessage(
        row.id,
        trimmed,
        preferredUserMessageId,
      );
      setDraftLaneId(null);
      setActiveThreadId(row.id);
      return { threadId: row.id };
    },
    [enabled, activeThreadId, draftModelProfileId],
  );

  const setActiveModelProfile = useCallback(
    async (profileId: ModelProfileId) => {
      if (!enabled) return;
      if (draftLaneActive) {
        setDraftModelProfileId(profileId);
        return;
      }
      if (activeThreadId) {
        await persistUpdateThreadModelProfile(activeThreadId, profileId);
      }
    },
    [enabled, draftLaneActive, activeThreadId],
  );

  const updateThreadModelProfile = useCallback(
    async (threadId: string, profileId: ModelProfileId) => {
      if (!enabled) return;
      await persistUpdateThreadModelProfile(threadId, profileId);
    },
    [enabled],
  );

  const deleteThreadOptimistic = useCallback(
    async (id: string) => {
      if (!enabled) return;

      let restVisible: ChatThread[] = [];
      setPendingDeletedIds((prev) => {
        const n = new Set(prev);
        n.add(id);
        restVisible = threadsRef.current.filter((t) => !n.has(t.id));
        return n;
      });

      if (activeThreadIdRef.current === id) {
        const nextPick = restVisible[0]?.id ?? null;
        if (nextPick) {
          setDraftLaneId(null);
          setActiveThreadId(nextPick);
        } else {
          enterDraftLane();
        }
      }

      try {
        await removeThread(id);
      } catch (e) {
        console.error("[usePersistentChat] optimistic delete failed:", e);
      } finally {
        setPendingDeletedIds((prev) => {
          const n = new Set(prev);
          n.delete(id);
          return n;
        });
      }
    },
    [enabled, removeThread, enterDraftLane],
  );

  const renameThreadStable = renameThread;

  const moveThreadToFolder = useCallback(
    async (threadId: string, folderId: string | null) => {
      if (!enabled) return;
      await persistMoveThreadToFolder(threadId, folderId);
    },
    [enabled],
  );

  const pinThread = useCallback(
    async (id: string) => {
      if (!enabled) return;
      await persistPinThread(id);
    },
    [enabled],
  );

  const unpinThread = useCallback(
    async (id: string) => {
      if (!enabled) return;
      await persistUnpinThread(id);
    },
    [enabled],
  );

  const commitThreadSidebarOrder = useCallback(
    async (ops: ThreadReorderOp[]) => {
      if (!enabled) return;
      for (const op of ops) {
        if (op.orderedIds.length === 0) continue;
        await reorderThreadsInFolder(op.folderId, op.orderedIds);
      }
    },
    [enabled],
  );

  const commitFolderSidebarOrder = useCallback(async (ids: string[]) => {
    if (!enabled) return;
    await reorderFolders(ids);
  }, [enabled]);

  const updatePersistedMessageText = useCallback(
    async (messageId: string, text: string) => {
      if (!enabled) return;
      await persistUpdateMessageText(messageId, text);
    },
    [enabled],
  );

  const deletePersistedMessage = useCallback(
    async (messageId: string) => {
      if (!enabled) return;
      await persistDeleteMessage(messageId);
    },
    [enabled],
  );

  const deletePersistedMessages = useCallback(
    async (messageIds: string[]) => {
      if (!enabled) return;
      await persistDeleteMessages(messageIds);
    },
    [enabled],
  );

  const expandFolder = useCallback(
    async (id: string) => {
      if (!enabled) return;
      await setFolderCollapsed(id, false);
    },
    [enabled, setFolderCollapsed],
  );

  return useMemo(() => {
    const persistedMessages = persistedSnapshot ?? ([] as ChatMessage[]);
    const messagesLoading =
      Boolean(enabled && activeThreadId && persistedSnapshot === undefined);

    return {
      enabled,
      activeThreadId,
      draftLaneId,
      draftLaneActive,
      activeModelProfileId,
      canSendOutbound,
      setActiveThreadId,
      visibleThreads,
      threadsLoading,
      folders,
      foldersLoading,
      rootThreads: folderModel.rootThreads,
      folderSections: folderModel.folderSections,
      createFolder: createNewFolder,
      renameFolder,
      deleteFolder: removeFolder,
      toggleFolderCollapsed,
      expandFolder,
      moveThreadToFolder,
      pinThread,
      unpinThread,
      commitThreadSidebarOrder,
      commitFolderSidebarOrder,
      setActiveModelProfile,
      updateThreadModelProfile,
      persistedMessages,
      messagesLoading,
      isPersistedHydrationReady,
      beginNewDraftChat,
      createNewThread: createPersistedShellThread,
      selectPersistedThread,
      renameThread: renameThreadStable,
      deleteThread: deleteThreadOptimistic,
      persistUserOutboundForSend,
      persistAssistantMessageToThread,
      updatePersistedMessageText,
      deletePersistedMessage,
      deletePersistedMessages,
    };
  }, [
    enabled,
    activeThreadId,
    draftLaneId,
    draftLaneActive,
    activeModelProfileId,
    canSendOutbound,
    visibleThreads,
    threadsLoading,
    folders,
    foldersLoading,
    folderModel.rootThreads,
    folderModel.folderSections,
    createNewFolder,
    renameFolder,
    removeFolder,
    toggleFolderCollapsed,
    expandFolder,
    moveThreadToFolder,
    pinThread,
    unpinThread,
    commitThreadSidebarOrder,
    commitFolderSidebarOrder,
    setActiveModelProfile,
    updateThreadModelProfile,
    persistedSnapshot,
    isPersistedHydrationReady,
    beginNewDraftChat,
    createPersistedShellThread,
    selectPersistedThread,
    renameThreadStable,
    deleteThreadOptimistic,
    persistUserOutboundForSend,
    persistAssistantMessageToThread,
    updatePersistedMessageText,
    deletePersistedMessage,
    deletePersistedMessages,
  ]);
}
