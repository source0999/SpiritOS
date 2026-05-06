"use client";

// ── ChatThreadSidebar - GPT rail: oldSpiritOS-style DnD + inline folder mint ────
import { useDroppable } from "@dnd-kit/core";
import type { DragEndEvent } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { FolderPlus, MessageSquarePlus, X } from "lucide-react";
import {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

import { ChatFolderSection } from "@/components/chat/ChatFolderSection";
import { ChatSidebarDndProvider } from "@/components/chat/ChatSidebarDndProvider";
import { ChatThreadListItem } from "@/components/chat/ChatThreadListItem";
import { SortableChatThreadItem } from "@/components/chat/SortableChatThreadItem";
import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import { buildMoveSelectModel } from "@/lib/chat-folder-utils";
import {
  CHAT_SIDEBAR_ROOT_DROP_ID,
  computeThreadDropPlan,
  parseDragId,
  shouldEnableChatThreadSidebarDnd,
  THREAD_DND_PREFIX,
  type ThreadReorderOp,
} from "@/lib/chat-sidebar-dnd";
import type { ChatFolder, ChatThread } from "@/lib/chat-db.types";
import { formatThreadUpdatedLabel } from "@/lib/chat-thread-format";
import { cn } from "@/lib/cn";

export { formatThreadUpdatedLabel } from "@/lib/chat-thread-format";

export type ChatThreadSidebarProps = {
  savedThreadCount: number;
  rootThreads: ChatThread[];
  folderSections: FolderSidebarSection[];
  allFolders: ChatFolder[];
  activeThreadId: string | null;
  draftActive?: boolean;
  interactionDisabled?: boolean;
  muteNewChatButton?: boolean;
  onNewChat: () => void;
  /** Committed folder name only - Dexie row is minted here, never on raw Folder click. */
  onCreateFolder: (trimmedName: string) => boolean | void | Promise<boolean | void>;
  onSelectThread: (id: string) => void;
  onRenameThread: (id: string) => void;
  onDeleteThread: (id: string) => void;
  onMoveThreadToFolder: (threadId: string, folderId: string | null) => void;
  onRenameFolder: (id: string) => void;
  onDeleteFolder: (id: string) => void;
  onToggleFolderCollapsed: (id: string) => void;
  onCommitThreadDrag?: (ops: ThreadReorderOp[]) => void | Promise<void>;
  /** Hover-expand collapsed folder targets while a thread drag is in flight (~300ms). */
  onExpandFolderDuringDrag?: (folderId: string) => void | Promise<void>;
  /** When drawer is used on small screens, show a close control in the header. */
  onDrawerClose?: () => void;
  /** When hosted in MobileThreadDrawer: drop the default mobile max-height rail cap. */
  layoutVariant?: "default" | "drawer";
  /** Drawer-only: enable @dnd-kit so iOS can reorder/move threads from the handle. */
  mobileDndEnabled?: boolean;
  className?: string;
  /** Prompt 10A - pinned quick-access block (may duplicate rows below). */
  pinnedThreads?: ChatThread[];
  onTogglePinThread?: (threadId: string) => void;
  threadSnippets?: Record<string, string>;
  searchQuery?: string;
  onSearchQueryChange?: (q: string) => void;
  searchEmptyResults?: boolean;
};

export const ChatThreadSidebar = memo(function ChatThreadSidebar({
  savedThreadCount,
  rootThreads,
  folderSections,
  allFolders,
  activeThreadId,
  draftActive = false,
  interactionDisabled = false,
  muteNewChatButton = false,
  onNewChat,
  onCreateFolder,
  onSelectThread,
  onRenameThread,
  onDeleteThread,
  onMoveThreadToFolder,
  onRenameFolder,
  onDeleteFolder,
  onToggleFolderCollapsed,
  onCommitThreadDrag,
  onExpandFolderDuringDrag,
  onDrawerClose,
  layoutVariant = "default",
  mobileDndEnabled = false,
  className,
  pinnedThreads = [],
  onTogglePinThread,
  threadSnippets,
  searchQuery = "",
  onSearchQueryChange,
  searchEmptyResults = false,
}: ChatThreadSidebarProps) {
  const railLocked = interactionDisabled;
  const newChatMuted = muteNewChatButton || railLocked;
  const newFolderMuted = railLocked;

  // Row-wide drag steals the first pointer interaction from the title <button> (dnd-kit vs click).
  // Handle-only keeps drag on the grip and lets thread switch work on first tap - drawer already did this.
  const threadDragLayout = "handle";

  const lgDesktop = useSyncExternalStore(
    (onStoreChange) => {
      if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
        return () => {};
      }
      const mq = window.matchMedia("(min-width: 1024px)");
      mq.addEventListener("change", onStoreChange);
      return () => mq.removeEventListener("change", onStoreChange);
    },
    () => {
      if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
        return true;
      }
      return window.matchMedia("(min-width: 1024px)").matches;
    },
    () => true,
  );

  const useDnd = shouldEnableChatThreadSidebarDnd({
    hasCommitHandler: Boolean(onCommitThreadDrag),
    railLocked,
    lgDesktop,
    layoutVariant,
    mobileDndEnabled,
  });

  const [dragActive, setDragActive] = useState<string | null>(null);
  const [overId, setOverId] = useState<string | null>(null);

  const [creatingFolder, setCreatingFolder] = useState(false);
  const [draftFolderName, setDraftFolderName] = useState("");
  const [folderCreateError, setFolderCreateError] = useState<string | null>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const skipFolderBlurRef = useRef(false);

  const rootThreadIds = useMemo(
    () => rootThreads.map((t) => `${THREAD_DND_PREFIX}${t.id}`),
    [rootThreads],
  );

  const draggingThreadActive = Boolean(
    dragActive?.startsWith(THREAD_DND_PREFIX),
  );

  const overlayThread = useMemo((): ChatThread | null => {
    if (!dragActive?.startsWith(THREAD_DND_PREFIX)) return null;
    const tid = dragActive.slice(THREAD_DND_PREFIX.length);
    const row = [...rootThreads, ...folderSections.flatMap((s) => s.threads)].find(
      (t) => t.id === tid,
    );
    return row ?? null;
  }, [dragActive, rootThreads, folderSections]);

  const hoverExpandTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clearHoverExpand = useCallback(() => {
    if (hoverExpandTimerRef.current) {
      clearTimeout(hoverExpandTimerRef.current);
      hoverExpandTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!onExpandFolderDuringDrag || !overId || !draggingThreadActive) {
      clearHoverExpand();
      return;
    }
    const parsed = parseDragId(overId);
    if (parsed.kind !== "folder" || parsed.folderId === null) {
      clearHoverExpand();
      return;
    }
    const fid = parsed.folderId;
    const section = folderSections.find((s) => s.folder.id === fid);
    if (!section?.folder.collapsed) {
      clearHoverExpand();
      return;
    }
    clearHoverExpand();
    hoverExpandTimerRef.current = setTimeout(() => {
      hoverExpandTimerRef.current = null;
      void onExpandFolderDuringDrag(fid);
    }, 300);
    return clearHoverExpand;
  }, [
    overId,
    draggingThreadActive,
    folderSections,
    onExpandFolderDuringDrag,
    clearHoverExpand,
  ]);

  const handleDragEnd = useCallback(
    (e: DragEndEvent) => {
      const { active, over } = e;
      setDragActive(null);
      setOverId(null);
      clearHoverExpand();
      if (!over || !onCommitThreadDrag) return;
      const aid = String(active.id);
      const oid = String(over.id);
      if (!aid.startsWith(THREAD_DND_PREFIX)) return;
      const threadId = aid.slice(THREAD_DND_PREFIX.length);
      const ops = computeThreadDropPlan({
        activeThreadId: threadId,
        overId: oid,
        rootThreads,
        folderSections,
      });
      if (ops?.length) void onCommitThreadDrag(ops);
    },
    [folderSections, rootThreads, onCommitThreadDrag, clearHoverExpand],
  );

  const cancelCreateFolder = useCallback(() => {
    setCreatingFolder(false);
    setDraftFolderName("");
    setFolderCreateError(null);
  }, []);

  const commitCreateFolder = useCallback(async () => {
    const trimmed = (folderInputRef.current?.value ?? draftFolderName).trim();
    if (!trimmed) {
      cancelCreateFolder();
      return;
    }
    const ok = await Promise.resolve(onCreateFolder(trimmed));
    if (ok === false) {
      setFolderCreateError("Folder already exists");
      return;
    }
    cancelCreateFolder();
  }, [draftFolderName, onCreateFolder, cancelCreateFolder]);

  const scrollClass = cn(
    "scrollbar-hide flex min-h-0 flex-col gap-2 overflow-y-auto overflow-x-hidden p-2 pb-5 lg:flex-1",
    layoutVariant === "drawer" && "touch-pan-y",
  );

  const showColdStartHint =
    !draftActive &&
    savedThreadCount === 0 &&
    allFolders.length === 0 &&
    !searchQuery.trim();

  const { setNodeRef: setRootDropRef, isOver: rootDropOver } = useDroppable({
    id: CHAT_SIDEBAR_ROOT_DROP_ID,
    disabled: !useDnd,
  });

  const renderRootThreads = (dnd: boolean) =>
    rootThreads.map((thread) => {
      const moveModel = buildMoveSelectModel(thread, allFolders);
      const snippet = threadSnippets?.[thread.id];
      const pinProps =
        onTogglePinThread != null
          ? {
              pinned: Boolean(thread.pinned),
              onTogglePin: () => onTogglePinThread(thread.id),
            }
          : {};
      const item = (
        <ChatThreadListItem
          thread={thread}
          active={thread.id === activeThreadId}
          updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
          interactionDisabled={railLocked}
          moveSelect={moveModel.show ? moveModel : null}
          onSelect={() => onSelectThread(thread.id)}
          onRename={() => onRenameThread(thread.id)}
          onDelete={() => onDeleteThread(thread.id)}
          onMoveThread={(fid) => onMoveThreadToFolder(thread.id, fid)}
          searchSnippet={snippet}
          {...pinProps}
        />
      );
      if (dnd) {
        return (
          <SortableChatThreadItem
            key={thread.id}
            threadId={thread.id}
            disabled={railLocked}
            useDragHandle={threadDragLayout === "handle"}
          >
            {({ dragActivatorProps, dragHandleProps, isDragging }) => (
              <ChatThreadListItem
                thread={thread}
                active={thread.id === activeThreadId}
                updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
                interactionDisabled={railLocked}
                moveSelect={moveModel.show ? moveModel : null}
                dragActivatorProps={dragHandleProps ? undefined : dragActivatorProps}
                dragHandleProps={dragHandleProps}
                dndDragging={Boolean(dragHandleProps && isDragging)}
                onSelect={() => onSelectThread(thread.id)}
                onRename={() => onRenameThread(thread.id)}
                onDelete={() => onDeleteThread(thread.id)}
                onMoveThread={(fid) => onMoveThreadToFolder(thread.id, fid)}
                searchSnippet={snippet}
                {...pinProps}
              />
            )}
          </SortableChatThreadItem>
        );
      }
      return <div key={thread.id}>{item}</div>;
    });

  const renderFolderSections = (dnd: boolean) =>
    folderSections.map((section) => (
      <div key={section.folder.id} className="flex flex-col gap-1">
        <ChatFolderSection
          section={section}
          allFolders={allFolders}
          activeThreadId={activeThreadId}
          interactionDisabled={railLocked}
          dndEnabled={dnd}
          threadDragLayout={threadDragLayout}
          draggingThread={dnd && draggingThreadActive}
          onToggleCollapsed={onToggleFolderCollapsed}
          onRenameFolder={onRenameFolder}
          onDeleteFolder={onDeleteFolder}
          onSelectThread={onSelectThread}
          onRenameThread={onRenameThread}
          onDeleteThread={onDeleteThread}
          onMoveThread={onMoveThreadToFolder}
          onTogglePinThread={onTogglePinThread}
          threadSnippets={threadSnippets}
        />
      </div>
    ));

  const innerScroll = (dnd: boolean) => (
    <>
      {pinnedThreads.length > 0 ? (
        <div className="flex flex-col gap-0.5">
          <p className="px-1 font-mono text-[9px] font-semibold uppercase tracking-[0.22em] text-chalk/38">
            Pinned
          </p>
          {pinnedThreads.map((thread) => {
            const moveModel = buildMoveSelectModel(thread, allFolders);
            const snippet = threadSnippets?.[thread.id];
            const pinProps =
              onTogglePinThread != null
                ? {
                    pinned: Boolean(thread.pinned),
                    onTogglePin: () => onTogglePinThread(thread.id),
                  }
                : {};
            return (
              <ChatThreadListItem
                key={`pinned-${thread.id}`}
                thread={thread}
                active={thread.id === activeThreadId}
                updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
                interactionDisabled={railLocked}
                moveSelect={moveModel.show ? moveModel : null}
                onSelect={() => onSelectThread(thread.id)}
                onRename={() => onRenameThread(thread.id)}
                onDelete={() => onDeleteThread(thread.id)}
                onMoveThread={(fid) => onMoveThreadToFolder(thread.id, fid)}
                searchSnippet={snippet}
                {...pinProps}
              />
            );
          })}
        </div>
      ) : null}

      {draftActive ? (
        <div
          className={cn(
            "rounded-lg border px-3 py-2.5",
            "border-[color:color-mix(in_oklab,var(--spirit-accent)_38%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)]",
          )}
        >
          <p className="font-medium text-[13px] text-[color:var(--spirit-accent-strong)]">
            New chat
          </p>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-chalk/40">
            Draft · clears on first send
          </p>
        </div>
      ) : null}

      {showColdStartHint ? (
        <p className="px-3 py-6 text-center font-mono text-xs leading-relaxed text-chalk/45">
          No saved threads yet - send a line here to freeze this lane in Dexie.
        </p>
      ) : null}

      {searchEmptyResults ? (
        <p className="px-3 py-4 text-center font-mono text-[11px] leading-relaxed text-chalk/50">
          No matching chats
        </p>
      ) : null}

      {dnd ? (
        <div
          ref={setRootDropRef}
          className={cn(
            "flex min-h-[120px] flex-col gap-0.5 rounded-md px-0.5 py-1 transition-colors",
            draggingThreadActive &&
              rootDropOver &&
              "border border-[color:color-mix(in_oklab,var(--spirit-accent-strong)_55%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_8%,transparent)] shadow-[0_0_24px_-10px_var(--spirit-glow)]",
          )}
        >
          <p className="px-1 font-mono text-[9px] font-semibold uppercase tracking-[0.22em] text-chalk/38">
            Chats
          </p>
          {rootThreads.length === 0 && !draftActive ? (
            <p className="px-2 py-1 font-mono text-[9px] text-chalk/32">
              No unfiled threads
            </p>
          ) : null}
          <SortableContext
            items={rootThreadIds}
            strategy={verticalListSortingStrategy}
          >
            {renderRootThreads(true)}
          </SortableContext>
        </div>
      ) : (
        <div className="flex min-h-[44px] flex-col gap-0.5">
          <p className="px-1 font-mono text-[9px] font-semibold uppercase tracking-[0.22em] text-chalk/38">
            Chats
          </p>
          {rootThreads.length === 0 && !draftActive ? (
            <p className="px-2 py-1 font-mono text-[9px] text-chalk/32">
              No unfiled threads
            </p>
          ) : null}
          <div>{renderRootThreads(false)}</div>
        </div>
      )}

      {renderFolderSections(dnd)}
    </>
  );

  return (
    <aside
      aria-label="Saved chat threads"
      className={cn(
        "flex flex-col",
        layoutVariant === "drawer"
          ? "h-full min-h-0 max-h-none w-full flex-1 border-0 bg-transparent shadow-none backdrop-blur-none"
          : "max-h-[40dvh] shrink-0 border-b border-[color:var(--spirit-border)] bg-white/[0.02] backdrop-blur-xl lg:max-h-none lg:h-full lg:w-[280px] lg:border-b-0 lg:border-r",
        className,
      )}
    >
      <div className="flex shrink-0 flex-col gap-2 border-b border-[color:var(--spirit-border)] px-3 py-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="truncate font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-chalk/55">
              Spirit threads
            </p>
            <p className="mt-px font-mono text-[10px] text-chalk/35">
              {savedThreadCount} saved
            </p>
          </div>
          {onDrawerClose ? (
            <button
              type="button"
              onClick={onDrawerClose}
              aria-label="Close threads"
              className="inline-flex h-9 w-9 shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/70 transition hover:bg-white/[0.08] lg:hidden"
            >
              <X className="h-4 w-4" aria-hidden strokeWidth={2} />
            </button>
          ) : null}
        </div>
        <div className="flex flex-wrap items-stretch justify-end gap-1.5">
          <button
            type="button"
            onClick={() => {
              if (newChatMuted) return;
              onNewChat();
            }}
            disabled={newChatMuted}
            aria-disabled={newChatMuted}
            className={cn(
              "touch-manipulation inline-flex shrink-0 items-center gap-1.5 rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] px-3 py-2 font-mono text-[10px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)] transition hover:brightness-110 active:scale-[0.98]",
              newChatMuted && "opacity-35",
            )}
          >
            <MessageSquarePlus className="h-3.5 w-3.5" aria-hidden />
            New chat
          </button>
          <button
            type="button"
            onClick={() => {
              if (newFolderMuted) return;
              if (creatingFolder) {
                folderInputRef.current?.focus();
                folderInputRef.current?.select();
                return;
              }
              setCreatingFolder(true);
              setDraftFolderName("");
              setFolderCreateError(null);
              queueMicrotask(() => folderInputRef.current?.focus());
            }}
            disabled={newFolderMuted}
            aria-disabled={newFolderMuted}
            aria-label="New folder"
            title="New folder"
            className={cn(
              "touch-manipulation inline-flex shrink-0 items-center gap-1 rounded-full border border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] bg-white/[0.03] px-2.5 py-2 font-mono text-[10px] font-semibold uppercase tracking-wider text-chalk/60 transition hover:border-[color:color-mix(in_oklab,var(--spirit-accent)_35%,transparent)] hover:text-chalk/85 active:scale-[0.98]",
              newFolderMuted && "opacity-35",
            )}
          >
            <FolderPlus className="h-3.5 w-3.5" aria-hidden />
            Folder
          </button>
        </div>
        {creatingFolder ? (
          <div className="flex flex-col gap-1">
            <input
              ref={folderInputRef}
              value={draftFolderName}
              onChange={(e) => {
                setDraftFolderName(e.target.value);
                setFolderCreateError(null);
              }}
              placeholder="New folder"
              aria-label="New folder name"
              className={cn(
                "w-full rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/30 px-2.5 py-2 font-mono text-[11px] text-chalk outline-none",
                "placeholder:text-chalk/35 focus:border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)]",
              )}
              onKeyDown={(e) => {
                if (e.key === "Escape") {
                  e.preventDefault();
                  cancelCreateFolder();
                  return;
                }
                if (e.key === "Enter") {
                  e.preventDefault();
                  skipFolderBlurRef.current = true;
                  void commitCreateFolder();
                  queueMicrotask(() => {
                    skipFolderBlurRef.current = false;
                  });
                }
              }}
              onBlur={() => {
                if (skipFolderBlurRef.current) return;
                const trimmed = (folderInputRef.current?.value ?? "").trim();
                if (!trimmed) cancelCreateFolder();
                else void commitCreateFolder();
              }}
            />
            {folderCreateError ? (
              <p className="font-mono text-[9px] text-rose-200/90" role="alert">
                {folderCreateError}
              </p>
            ) : null}
          </div>
        ) : null}
        {onSearchQueryChange ? (
          <div className="px-0.5 pt-1">
            <label htmlFor="chat-thread-search" className="sr-only">
              Search chats
            </label>
            <input
              id="chat-thread-search"
              type="search"
              enterKeyHint="search"
              value={searchQuery}
              onChange={(e) => onSearchQueryChange(e.target.value)}
              placeholder="Search chats..."
              className="w-full rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/35 px-2.5 py-2 font-mono text-base text-chalk outline-none placeholder:text-chalk/35 focus:border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] lg:text-[11px]"
            />
          </div>
        ) : null}
      </div>

      {useDnd ? (
        <ChatSidebarDndProvider
          overlayThread={overlayThread}
          touchActivation={
            layoutVariant === "drawer"
              ? { delay: 180, tolerance: 8 }
              : { delay: 150, tolerance: 6 }
          }
          onDragStart={(ev) => {
            setDragActive(String(ev.active.id));
            setOverId(null);
          }}
          onDragOver={(ev) => {
            setOverId(ev.over ? String(ev.over.id) : null);
          }}
          onDragEnd={handleDragEnd}
        >
          <div className={scrollClass}>{innerScroll(true)}</div>
        </ChatSidebarDndProvider>
      ) : (
        <div className={scrollClass}>{innerScroll(false)}</div>
      )}
    </aside>
  );
});
