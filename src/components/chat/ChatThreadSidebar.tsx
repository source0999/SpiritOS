"use client";

// ── ChatThreadSidebar - GPT rail: oldSpiritOS-style DnD + inline folder mint ────
import { useDroppable } from "@dnd-kit/core";
import type { DragCancelEvent, DragEndEvent } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { ChevronRight, FolderPlus, MessageSquarePlus, Search, X } from "lucide-react";
import {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ChatFolderSection } from "@/components/chat/ChatFolderSection";
import { ChatSidebarDndProvider } from "@/components/chat/ChatSidebarDndProvider";
import { StableChatThreadListItem } from "@/components/chat/ChatThreadListItem";
import { SortableChatThreadItem } from "@/components/chat/SortableChatThreadItem";
import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import { buildMoveSelectModel } from "@/lib/chat-folder-utils";
import {
  CHAT_SIDEBAR_ROOT_DROP_ID,
  computeFolderReorderPlan,
  computeThreadDropPlan,
  FOLDER_SORT_PREFIX,
  parseDragId,
  resetThreadCollisionSticky,
  shouldEnableChatThreadSidebarDnd,
  THREAD_DND_PREFIX,
  type ThreadReorderOp,
} from "@/lib/chat-sidebar-dnd";
import type { ChatFolder, ChatThread } from "@/lib/chat-db.types";
import { formatThreadUpdatedLabel } from "@/lib/chat-thread-format";
import { cn } from "@/lib/cn";
import { useMediaMinWidthLg } from "@/lib/hooks/useMediaMinWidthLg";

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
  onCommitFolderDrag?: (orderedFolderIds: string[]) => void | Promise<void>;
  /** Hover-expand collapsed folder targets while a thread drag is in flight (~300ms). */
  onExpandFolderDuringDrag?: (folderId: string) => void | Promise<void>;
  /** When drawer is used on small screens, show a close control in the header. */
  onDrawerClose?: () => void;
  /** When hosted in MobileThreadDrawer: drop the default mobile max-height rail cap. */
  layoutVariant?: "default" | "drawer";
  /** Drawer-only: enable @dnd-kit so iOS can reorder/move threads from the handle. */
  mobileDndEnabled?: boolean;
  className?: string;
  /** Prompt 10A - pinned quick-access block (same thread may still appear in `rootThreads` for DnD math). */
  pinnedThreads?: ChatThread[];
  onTogglePinThread?: (threadId: string) => void;
  threadSnippets?: Record<string, string>;
  searchQuery?: string;
  onSearchQueryChange?: (q: string) => void;
  searchEmptyResults?: boolean;
  chromeVariant?: "default" | "trinity";
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
  onCommitFolderDrag,
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
  chromeVariant = "default",
}: ChatThreadSidebarProps) {
  const railLocked = interactionDisabled;
  const newChatMuted = muteNewChatButton || railLocked;
  const newFolderMuted = railLocked;
  const trinityChrome = chromeVariant === "trinity";

  // Handle-only: title/open stays a real button; dnd-kit listeners live on the invisible left-edge activator.
  const threadDragLayout = "handle";

  /** PointerSensor travel before drag arms. Whole-row needed ~20px; a ~36px grip feels dead until ~5px. */
  const railPointerActivationPx = 5;

  const lgDesktop = useMediaMinWidthLg();

  const useDnd = shouldEnableChatThreadSidebarDnd({
    hasCommitHandler: Boolean(onCommitThreadDrag || onCommitFolderDrag),
    railLocked,
    lgDesktop,
    layoutVariant,
    mobileDndEnabled,
  });

  const folderReorderEnabled =
    useDnd &&
    Boolean(onCommitFolderDrag) &&
    !searchQuery.trim();

  const [dragActive, setDragActive] = useState<string | null>(null);
  const [overId, setOverId] = useState<string | null>(null);

  const [creatingFolder, setCreatingFolder] = useState(false);
  const [draftFolderName, setDraftFolderName] = useState("");
  const [folderCreateError, setFolderCreateError] = useState<string | null>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const skipFolderBlurRef = useRef(false);
  const threadScrollRef = useRef<HTMLDivElement>(null);

  const [pinnedSectionExpanded, setPinnedSectionExpanded] = useState(true);
  const [foldersSectionExpanded, setFoldersSectionExpanded] = useState(true);

  /** Pinned root threads render only under PINNED; Recent stays unpinned-only. */
  const recentRootThreads = useMemo(
    () => rootThreads.filter((t) => !t.pinned),
    [rootThreads],
  );

  /** Drop-plan bucket order must match on-screen stacking (pinned block → Recent), not raw `order` interleaving. */
  const visualRootThreadsForPlan = useMemo(
    () => [...pinnedThreads, ...recentRootThreads],
    [pinnedThreads, recentRootThreads],
  );

  const rootThreadIds = useMemo(
    () => recentRootThreads.map((t) => `${THREAD_DND_PREFIX}${t.id}`),
    [recentRootThreads],
  );

  const pinnedThreadIds = useMemo(
    () => pinnedThreads.map((t) => `${THREAD_DND_PREFIX}${t.id}`),
    [pinnedThreads],
  );

  const folderSortIds = useMemo(
    () => folderSections.map((s) => `${FOLDER_SORT_PREFIX}${s.folder.id}`),
    [folderSections],
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

  const resetThreadDragChrome = useCallback(() => {
    setDragActive(null);
    setOverId(null);
    clearHoverExpand();
  }, [clearHoverExpand]);

  const handleDragCancel = useCallback(
    (_e: DragCancelEvent) => {
      resetThreadDragChrome();
    },
    [resetThreadDragChrome],
  );

  const handleDragEnd = useCallback(
    (e: DragEndEvent) => {
      const { active, over } = e;
      const aid = String(active.id);
      const oid = over ? String(over.id) : null;
      resetThreadDragChrome();

      if (aid.startsWith(FOLDER_SORT_PREFIX)) {
        if (!oid || !onCommitFolderDrag) return;
        const activeFolderId = aid.slice(FOLDER_SORT_PREFIX.length);
        const next = computeFolderReorderPlan({
          activeFolderId,
          overId: oid,
          folderSections,
        });
        if (next?.length) void onCommitFolderDrag(next);
        return;
      }

      if (!over || !onCommitThreadDrag) return;
      if (!aid.startsWith(THREAD_DND_PREFIX)) return;
      const threadOverId = String(over.id);
      const threadId = aid.slice(THREAD_DND_PREFIX.length);
      const ops = computeThreadDropPlan({
        activeThreadId: threadId,
        overId: threadOverId,
        rootThreads: visualRootThreadsForPlan,
        folderSections,
      });
      if (ops?.length) void onCommitThreadDrag(ops);
    },
    [
      folderSections,
      onCommitFolderDrag,
      onCommitThreadDrag,
      resetThreadDragChrome,
      visualRootThreadsForPlan,
    ],
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
    "spirit-sidebar-thread-scroll scrollbar-hide flex min-h-0 flex-col gap-2 overflow-y-auto overflow-x-hidden p-2 pb-5 lg:flex-1",
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

  const renderSectionLabel = (
    label: string,
    toggle?: { expanded: boolean; onToggle: () => void },
  ) => {
    const key = label.toLowerCase();
    if (toggle) {
      return (
        <button
          type="button"
          data-sidebar-section-label={key}
          data-sidebar-section-toggle={key}
          aria-expanded={toggle.expanded}
          aria-controls={`sidebar-section-body-${key}`}
          id={`sidebar-section-heading-${key}`}
          onClick={toggle.onToggle}
          disabled={railLocked}
          className={cn(
            "spirit-sidebar-section-label spirit-sidebar-section-toggle flex w-full min-w-0 items-center gap-1 rounded-md px-1 py-0.5 text-left font-mono text-[9px] font-semibold uppercase tracking-[0.22em] text-chalk/38 outline-none transition hover:bg-white/[0.05]",
            trinityChrome && "spirit-sidebar-section-label--trinity",
            railLocked && "pointer-events-none opacity-40",
          )}
        >
          <ChevronRight
            className={cn(
              "size-3 shrink-0 text-chalk/45 transition-transform",
              toggle.expanded && "rotate-90",
            )}
            aria-hidden
            strokeWidth={2}
          />
          <span className="min-w-0 truncate">{label}</span>
        </button>
      );
    }
    return (
      <p
        data-sidebar-section-label={key}
        id={`sidebar-section-heading-${key}`}
        className={cn(
          "spirit-sidebar-section-label px-1 font-mono text-[9px] font-semibold uppercase tracking-[0.22em] text-chalk/38",
          trinityChrome && "spirit-sidebar-section-label--trinity",
        )}
      >
        {label}
      </p>
    );
  };

  const renderRootThreads = (dnd: boolean) =>
    recentRootThreads.map((thread) => {
      const moveModel = buildMoveSelectModel(thread, allFolders);
      const snippet = threadSnippets?.[thread.id];
      const item = (
        <StableChatThreadListItem
          thread={thread}
          activeThreadId={activeThreadId}
          onSelectThread={onSelectThread}
          onRenameThread={onRenameThread}
          onDeleteThread={onDeleteThread}
          onMoveThreadToFolder={onMoveThreadToFolder}
          onTogglePinThread={onTogglePinThread}
          updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
          interactionDisabled={railLocked}
          moveSelect={moveModel.show ? moveModel : null}
          searchSnippet={snippet}
          hideUpdatedLabel={trinityChrome}
          actionLayout={trinityChrome ? "trinity-recent" : "inline"}
        />
      );
      if (dnd) {
        return (
          <SortableChatThreadItem
            key={thread.id}
            threadId={thread.id}
            disabled={railLocked}
            useDragHandle
          >
            {({
              dragActivatorProps,
              dragHandleProps,
              setDragActivatorRef,
              isDragging,
            }) => (
              <StableChatThreadListItem
                thread={thread}
                activeThreadId={activeThreadId}
                onSelectThread={onSelectThread}
                onRenameThread={onRenameThread}
                onDeleteThread={onDeleteThread}
                onMoveThreadToFolder={onMoveThreadToFolder}
                onTogglePinThread={onTogglePinThread}
                updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
                interactionDisabled={railLocked}
                moveSelect={moveModel.show ? moveModel : null}
                dragActivatorProps={dragHandleProps ? undefined : dragActivatorProps}
                dragHandleProps={dragHandleProps}
                dndDragging={isDragging}
                setDragActivatorRef={setDragActivatorRef}
                searchSnippet={snippet}
                hideUpdatedLabel={trinityChrome}
                actionLayout={trinityChrome ? "trinity-recent" : "inline"}
              />
            )}
          </SortableChatThreadItem>
        );
      }
      return <div key={thread.id}>{item}</div>;
    });

  const renderFolderSections = (dnd: boolean, folderSort: boolean) =>
    folderSections.map((section) => (
      <div
        key={section.folder.id}
        className={cn(
          "spirit-sidebar-folder-item flex flex-col",
          trinityChrome ? "gap-px" : "gap-1",
        )}
      >
        <ChatFolderSection
          section={section}
          allFolders={allFolders}
          activeThreadId={activeThreadId}
          interactionDisabled={railLocked}
          dndEnabled={dnd}
          threadDragLayout={threadDragLayout}
          draggingThread={dnd && draggingThreadActive}
          folderSortable={folderSort}
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
        <div
          data-sidebar-section="pinned"
          className={cn(
            "spirit-sidebar-section spirit-sidebar-section--pinned flex flex-col",
            trinityChrome ? "gap-px" : "gap-0.5",
          )}
        >
          {renderSectionLabel("Pinned", {
            expanded: pinnedSectionExpanded,
            onToggle: () => setPinnedSectionExpanded((v) => !v),
          })}
          {pinnedSectionExpanded ? (
            <div
              id="sidebar-section-body-pinned"
              className={cn(
                "flex min-h-0 flex-col",
                trinityChrome ? "gap-px" : "gap-0.5",
              )}
            >
              {dnd ? (
                <SortableContext
                  items={pinnedThreadIds}
                  strategy={verticalListSortingStrategy}
                >
                  {pinnedThreads.map((thread) => {
                    const moveModel = buildMoveSelectModel(thread, allFolders);
                    const snippet = threadSnippets?.[thread.id];
                    return (
                      <SortableChatThreadItem
                        key={thread.id}
                        threadId={thread.id}
                        disabled={railLocked}
                        useDragHandle
                      >
                        {({
                          dragActivatorProps,
                          dragHandleProps,
                          setDragActivatorRef,
                          isDragging,
                        }) => (
                          <StableChatThreadListItem
                            thread={thread}
                            activeThreadId={activeThreadId}
                            onSelectThread={onSelectThread}
                            onRenameThread={onRenameThread}
                            onDeleteThread={onDeleteThread}
                            onMoveThreadToFolder={onMoveThreadToFolder}
                            onTogglePinThread={onTogglePinThread}
                            updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
                            interactionDisabled={railLocked}
                            moveSelect={moveModel.show ? moveModel : null}
                            searchSnippet={snippet}
                            hideUpdatedLabel={trinityChrome}
                            dragActivatorProps={
                              dragHandleProps ? undefined : dragActivatorProps
                            }
                            dragHandleProps={dragHandleProps}
                            dndDragging={isDragging}
                            setDragActivatorRef={setDragActivatorRef}
                            actionLayout={trinityChrome ? "trinity-recent" : "inline"}
                          />
                        )}
                      </SortableChatThreadItem>
                    );
                  })}
                </SortableContext>
              ) : (
                pinnedThreads.map((thread) => {
                  const moveModel = buildMoveSelectModel(thread, allFolders);
                  const snippet = threadSnippets?.[thread.id];
                  return (
                    <StableChatThreadListItem
                      key={thread.id}
                      thread={thread}
                      activeThreadId={activeThreadId}
                      onSelectThread={onSelectThread}
                      onRenameThread={onRenameThread}
                      onDeleteThread={onDeleteThread}
                      onMoveThreadToFolder={onMoveThreadToFolder}
                      onTogglePinThread={onTogglePinThread}
                      updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
                      interactionDisabled={railLocked}
                      moveSelect={moveModel.show ? moveModel : null}
                      searchSnippet={snippet}
                      hideUpdatedLabel={trinityChrome}
                    />
                  );
                })
              )}
            </div>
          ) : null}
        </div>
      ) : null}

      {showColdStartHint ? (
        <p className="px-3 py-6 text-center font-mono text-xs leading-relaxed text-chalk/45">
          No saved chats yet.
        </p>
      ) : null}

      {searchEmptyResults ? (
        <p className="px-3 py-4 text-center font-mono text-[11px] leading-relaxed text-chalk/50">
          No matching chats
        </p>
      ) : null}

      {folderSections.length > 0 ? (
        <div
          data-sidebar-section="folders"
          className={cn(
            "spirit-sidebar-section spirit-sidebar-section--folders flex flex-col",
            trinityChrome ? "gap-px" : "gap-0.5",
          )}
        >
          {renderSectionLabel("Folders", {
            expanded: foldersSectionExpanded,
            onToggle: () => setFoldersSectionExpanded((v) => !v),
          })}
          <div
            id="sidebar-section-body-folders"
            hidden={!foldersSectionExpanded}
            className={cn(
              "spirit-sidebar-folder-stack flex min-h-0 flex-col",
              trinityChrome ? "gap-px" : "gap-1",
            )}
          >
            {folderReorderEnabled ? (
              <SortableContext items={folderSortIds} strategy={verticalListSortingStrategy}>
                {renderFolderSections(dnd, true)}
              </SortableContext>
            ) : (
              renderFolderSections(dnd, false)
            )}
          </div>
        </div>
      ) : null}

      {dnd ? (
        <div
          ref={setRootDropRef}
          data-sidebar-section="recent"
          className={cn(
            "spirit-sidebar-section spirit-sidebar-section--recent spirit-sidebar-root-drop flex min-h-[120px] flex-col rounded-md px-0.5 py-1 transition-colors",
            trinityChrome ? "gap-px" : "gap-0.5",
            draggingThreadActive &&
              rootDropOver &&
              "border border-[color:color-mix(in_oklab,var(--spirit-accent-strong)_55%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_8%,transparent)] shadow-[0_0_24px_-10px_var(--spirit-glow)]",
          )}
        >
          {renderSectionLabel(trinityChrome ? "Recent" : "Chats")}
          {recentRootThreads.length === 0 && !draftActive ? (
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
        <div
          data-sidebar-section="recent"
          className={cn(
            "spirit-sidebar-section spirit-sidebar-section--recent flex min-h-[44px] flex-col",
            trinityChrome ? "gap-px" : "gap-0.5",
          )}
        >
          {renderSectionLabel(trinityChrome ? "Recent" : "Chats")}
          {recentRootThreads.length === 0 && !draftActive ? (
            <p className="px-2 py-1 font-mono text-[9px] text-chalk/32">
              No unfiled threads
            </p>
          ) : null}
          <div>{renderRootThreads(false)}</div>
        </div>
      )}

    </>
  );

  return (
    <aside
      aria-label="Saved chat threads"
      className={cn(
        "flex flex-col",
        layoutVariant === "drawer"
          ? "h-full min-h-0 max-h-none w-full flex-1 border-0 bg-transparent shadow-none backdrop-blur-none"
          : "max-h-[40dvh] shrink-0 border-b border-[color:color-mix(in_oklab,var(--spirit-border)_80%,transparent)] bg-white/[0.025] backdrop-blur-xl lg:max-h-none lg:h-full lg:w-[var(--chat-thread-rail-width)] lg:border-b-0 lg:border-r lg:border-[color:color-mix(in_oklab,var(--spirit-border)_65%,transparent)]",
        trinityChrome && "spirit-trinity-sidebar--trinity",
        className,
      )}
    >
      <div
        className={cn(
          "spirit-sidebar-header flex shrink-0 flex-col gap-2 border-b border-[color:color-mix(in_oklab,var(--spirit-border)_70%,transparent)]",
          layoutVariant === "drawer" ? "px-3 pb-3 pt-2" : "px-3 py-2.5",
        )}
      >
        {layoutVariant === "drawer" ? (
          <>
            <div className="spirit-sidebar-brand-row flex items-start justify-between gap-2">
              <div className="spirit-sidebar-brand-copy min-w-0 flex-1">
                <p
                  className={cn(
                    "truncate font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-chalk/55",
                    trinityChrome && "spirit-sidebar-brand-title",
                  )}
                >
                  {trinityChrome ? "Chats" : "Spirit threads"}
                </p>
                <p
                  className={cn(
                    "mt-px font-mono text-[10px] text-chalk/35",
                    trinityChrome && "spirit-sidebar-brand-meta",
                  )}
                >
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
            {onSearchQueryChange ? (
              <div className="spirit-sidebar-search-wrap relative px-0.5 pt-1">
                <label htmlFor="chat-thread-search" className="sr-only">
                  Search chats
                </label>
                <Search
                  className="spirit-sidebar-search-icon pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2"
                  aria-hidden
                  strokeWidth={1.8}
                />
                <input
                  id="chat-thread-search"
                  type="search"
                  enterKeyHint="search"
                  value={searchQuery}
                  onChange={(e) => onSearchQueryChange(e.target.value)}
                  placeholder="Search chats..."
                  className="spirit-sidebar-search-input w-full rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] bg-black/40 py-2.5 pl-9 pr-3 text-[15px] text-chalk outline-none placeholder:text-chalk/35 focus:border-[color:color-mix(in_oklab,var(--spirit-accent)_35%,transparent)] focus:ring-1 focus:ring-[color:color-mix(in_oklab,var(--spirit-accent)_18%,transparent)]"
                />
              </div>
            ) : null}
            <div className="spirit-sidebar-header-actions flex gap-2">
              <button
                type="button"
                data-sidebar-action="new-chat"
                onClick={() => {
                  if (newChatMuted) return;
                  onNewChat();
                }}
                disabled={newChatMuted}
                aria-disabled={newChatMuted}
                className={cn(
                  "touch-manipulation inline-flex min-h-[48px] flex-1 items-center justify-center gap-2 rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_14%,transparent)] px-3 font-sans text-[14px] font-semibold text-[color:var(--spirit-accent-strong)] transition active:scale-[0.98]",
                  newChatMuted && "opacity-35",
                )}
              >
                <MessageSquarePlus
                  className="spirit-sidebar-action-icon shrink-0"
                  aria-hidden
                  strokeWidth={1.75}
                />
                New chat
              </button>
              <button
                type="button"
                data-sidebar-action="new-folder"
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
                  "touch-manipulation inline-flex min-h-[48px] shrink-0 items-center justify-center gap-2 rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-border)_48%,transparent)] bg-white/[0.04] px-3 font-sans text-[14px] font-semibold text-chalk/65 transition hover:border-[color:color-mix(in_oklab,var(--spirit-accent)_30%,transparent)] hover:text-chalk/85 active:scale-[0.98]",
                  newFolderMuted && "opacity-35",
                )}
              >
                <FolderPlus className="spirit-sidebar-action-icon" aria-hidden strokeWidth={1.75} />
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
                    "spirit-sidebar-folder-input w-full rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/30 px-2.5 py-2 font-mono text-[11px] text-chalk outline-none",
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
          </>
        ) : (
          <>
            <div className="spirit-sidebar-brand-row flex items-start justify-between gap-2">
              <div className="spirit-sidebar-brand-copy min-w-0 flex-1">
                <p
                  className={cn(
                    "truncate font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-chalk/55",
                    trinityChrome && "spirit-sidebar-brand-title",
                  )}
                >
                  {trinityChrome ? "Chats" : "Spirit threads"}
                </p>
                <p
                  className={cn(
                    "mt-px font-mono text-[10px] text-chalk/35",
                    trinityChrome && "spirit-sidebar-brand-meta",
                  )}
                >
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
            <div className="spirit-sidebar-header-actions flex flex-wrap items-stretch justify-end gap-2">
              <button
                type="button"
                data-sidebar-action="new-chat"
                onClick={() => {
                  if (newChatMuted) return;
                  onNewChat();
                }}
                disabled={newChatMuted}
                aria-disabled={newChatMuted}
                className={cn(
                  "touch-manipulation inline-flex shrink-0 items-center gap-1.5 rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] px-3 py-2 font-mono text-[10px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)] transition active:scale-[0.98]",
                  newChatMuted && "opacity-35",
                )}
              >
                <MessageSquarePlus className="spirit-sidebar-action-icon" aria-hidden strokeWidth={1.75} />
                New chat
              </button>
              <button
                type="button"
                data-sidebar-action="new-folder"
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
                <FolderPlus className="spirit-sidebar-action-icon" aria-hidden strokeWidth={1.75} />
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
                    "spirit-sidebar-folder-input w-full rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/30 px-2.5 py-2 font-mono text-[11px] text-chalk outline-none",
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
              <div className="spirit-sidebar-search-wrap relative px-0.5 pt-1">
                <label htmlFor="chat-thread-search" className="sr-only">
                  Search chats
                </label>
                <Search
                  className="spirit-sidebar-search-icon pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2"
                  aria-hidden
                  strokeWidth={1.8}
                />
                <input
                  id="chat-thread-search"
                  type="search"
                  enterKeyHint="search"
                  value={searchQuery}
                  onChange={(e) => onSearchQueryChange(e.target.value)}
                  placeholder="Search chats..."
                  className="spirit-sidebar-search-input w-full rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/35 py-2 pl-9 pr-2.5 font-mono text-base text-chalk outline-none placeholder:text-chalk/35 focus:border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] lg:text-[11px]"
                />
              </div>
            ) : null}
          </>
        )}
      </div>

      {useDnd ? (
        <ChatSidebarDndProvider
          overlayThread={overlayThread}
          touchActivation={
            layoutVariant === "drawer"
              ? { delay: 200, tolerance: 12 }
              : { delay: 150, tolerance: 6 }
          }
          pointerActivation={{
            distance:
              layoutVariant === "drawer" ? 12 : railPointerActivationPx,
          }}
          onDragStart={(ev) => {
            const activeId = String(ev.active.id);
            resetThreadCollisionSticky();
            setDragActive(activeId);
            setOverId(null);
          }}
          onDragOver={(ev) => {
            setOverId(ev.over ? String(ev.over.id) : null);
          }}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          <div ref={threadScrollRef} className={scrollClass}>
            {innerScroll(true)}
          </div>
        </ChatSidebarDndProvider>
      ) : (
        <div ref={threadScrollRef} className={scrollClass}>
          {innerScroll(false)}
        </div>
      )}
    </aside>
  );
});
