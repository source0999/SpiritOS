"use client";

// ── ChatFolderSection - folder droppable + per-folder SortableContext (oldSpiritOS) ─
import { useDroppable } from "@dnd-kit/core";
import {
  defaultAnimateLayoutChanges,
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ChevronRight, FolderOpen, PenLine, Trash2 } from "lucide-react";
import { memo, useState, type CSSProperties } from "react";

import { StableChatThreadListItem } from "@/components/chat/ChatThreadListItem";
import type { DragActivatorProps } from "@/components/chat/SortableChatThreadItem";
import { SortableChatThreadItem } from "@/components/chat/SortableChatThreadItem";
import { formatThreadUpdatedLabel } from "@/lib/chat-thread-format";
import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import { buildMoveSelectModel } from "@/lib/chat-folder-utils";
import { FOLDER_DROP_PREFIX, FOLDER_SORT_PREFIX, THREAD_DND_PREFIX } from "@/lib/chat-sidebar-dnd";
import type { ChatFolder } from "@/lib/chat-db.types";
import { cn } from "@/lib/cn";

/** Folders: collision math ignores thread rows — safe to let siblings ease (threads keep animateLayoutChanges off). */
const FOLDER_SORT_MS = 145;
const FOLDER_SORT_EASING = "cubic-bezier(0.25, 0.1, 0.25, 1)";

/** Same contract as thread edge — fat invisible strip; chevron/rename/delete sit above via z-index. */
function FolderEdgeDragHandle({
  folderName,
  dragHandleProps,
  setDragActivatorRef,
  interactionDisabled,
  dndDragging,
}: {
  folderName: string;
  dragHandleProps: DragActivatorProps;
  setDragActivatorRef?: (element: HTMLElement | null) => void;
  interactionDisabled: boolean;
  dndDragging: boolean;
}) {
  return (
    <button
      type="button"
      {...dragHandleProps}
      ref={setDragActivatorRef}
      disabled={interactionDisabled}
      data-drag-handle="folder-edge"
      aria-label={`Drag to reorder folder ${folderName}`}
      className={cn(
        "spirit-folder-row__drag-edge pointer-events-auto absolute left-0 top-0 z-[10] h-full min-h-[2.25rem] touch-none",
        "w-[min(80%,calc(100%-5.5rem))]",
        "cursor-grab border-0 bg-transparent p-0 opacity-0 outline-none active:cursor-grabbing",
        "focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-[color:color-mix(in_oklab,var(--spirit-accent-strong)_35%,transparent)] focus-visible:ring-inset",
        dndDragging && "opacity-100",
      )}
      style={{ touchAction: "none" }}
    />
  );
}

export type ChatFolderHeaderRowProps = {
  folder: ChatFolder;
  collapsed: boolean;
  locked: boolean;
  onToggle: () => void;
  onRename: () => void;
  /** Called only after inline confirm - never deletes threads. */
  onDeleteConfirmed: () => void;
  folderDragHandleProps?: DragActivatorProps;
  setFolderDragActivatorRef?: (element: HTMLElement | null) => void;
  folderDndDragging?: boolean;
};

export const ChatFolderHeaderRow = memo(function ChatFolderHeaderRow({
  folder,
  collapsed,
  locked,
  onToggle,
  onRename,
  onDeleteConfirmed,
  folderDragHandleProps,
  setFolderDragActivatorRef,
  folderDndDragging = false,
}: ChatFolderHeaderRowProps) {
  const [deleteConfirming, setDeleteConfirming] = useState(false);

  return (
    <div
      className={cn(
        "spirit-sidebar-folder-row relative isolate flex min-w-0 flex-1 flex-wrap items-center gap-0.5 rounded-md border border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] bg-white/[0.02] px-1 py-0.5",
        locked && "opacity-40",
      )}
    >
      <button
        type="button"
        disabled={locked}
        onClick={() => {
          if (locked) return;
          onToggle();
        }}
        aria-expanded={!collapsed}
        className="relative z-[15] touch-manipulation rounded p-1 text-chalk/55 transition hover:bg-white/[0.05] hover:text-chalk"
        aria-label={collapsed ? `Expand folder ${folder.name}` : `Collapse folder ${folder.name}`}
      >
        <ChevronRight
          className={cn(
            "h-3.5 w-3.5 transition-transform",
            !collapsed && "rotate-90",
          )}
          aria-hidden
          strokeWidth={2}
        />
      </button>
      <FolderOpen
        className="pointer-events-none relative z-0 h-3.5 w-3.5 shrink-0 text-[color:color-mix(in_oklab,var(--spirit-accent)_55%,transparent)]"
        aria-hidden
        strokeWidth={2}
      />
      <span className="pointer-events-none relative z-0 min-w-0 flex-1 truncate font-mono text-[10px] font-semibold uppercase tracking-wide text-chalk/70">
        {folder.name}
      </span>
      <button
        type="button"
        disabled={locked}
        onClick={(e) => {
          e.stopPropagation();
          if (locked) return;
          onRename();
        }}
        aria-label={`Rename folder ${folder.name}`}
        className="relative z-[15] touch-manipulation rounded p-1 text-chalk/45 transition hover:bg-white/[0.05] hover:text-chalk"
      >
        <PenLine className="h-3 w-3" aria-hidden strokeWidth={2} />
      </button>
      {deleteConfirming ? (
        <div className="relative z-[15] flex min-w-0 basis-full flex-col gap-0.5 border-t border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] pt-0.5 sm:basis-auto sm:flex-row sm:items-center sm:border-t-0 sm:pt-0">
          <span className="min-w-0 font-mono text-[8px] leading-snug text-chalk/65">
            Delete? Threads return to Chats.
          </span>
          <div className="flex shrink-0 gap-0.5">
            <button
              type="button"
              disabled={locked}
              onClick={(e) => {
                e.stopPropagation();
                if (locked) return;
                setDeleteConfirming(false);
                onDeleteConfirmed();
              }}
              className="touch-manipulation rounded px-1.5 py-0.5 font-mono text-[8px] font-semibold uppercase tracking-wide text-rose-200/90 transition hover:bg-rose-500/20"
            >
              Confirm
            </button>
            <button
              type="button"
              disabled={locked}
              onClick={(e) => {
                e.stopPropagation();
                setDeleteConfirming(false);
              }}
              className="touch-manipulation rounded px-1.5 py-0.5 font-mono text-[8px] font-semibold uppercase tracking-wide text-chalk/55 transition hover:bg-white/[0.06]"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          disabled={locked}
          onClick={(e) => {
            e.stopPropagation();
            if (locked) return;
            setDeleteConfirming(true);
          }}
          aria-label={`Delete folder ${folder.name}`}
          className="relative z-[15] touch-manipulation rounded p-1 text-chalk/45 transition hover:bg-rose-500/15 hover:text-rose-200"
        >
          <Trash2 className="h-3 w-3" aria-hidden strokeWidth={2} />
        </button>
      )}
      {folderDragHandleProps && setFolderDragActivatorRef ? (
        <FolderEdgeDragHandle
          folderName={folder.name}
          dragHandleProps={folderDragHandleProps}
          setDragActivatorRef={setFolderDragActivatorRef}
          interactionDisabled={locked}
          dndDragging={folderDndDragging}
        />
      ) : null}
    </div>
  );
});

export type ChatFolderSectionProps = {
  section: FolderSidebarSection;
  allFolders: ChatFolder[];
  activeThreadId: string | null;
  interactionDisabled?: boolean;
  draggingThread?: boolean;
  dndEnabled?: boolean;
  threadDragLayout?: "row" | "handle";
  onToggleCollapsed: (folderId: string) => void;
  onRenameFolder: (folderId: string) => void;
  onDeleteFolder: (folderId: string) => void;
  onSelectThread: (id: string) => void;
  onRenameThread: (id: string) => void;
  onDeleteThread: (id: string) => void;
  onMoveThread: (threadId: string, folderId: string | null) => void;
  onTogglePinThread?: (threadId: string) => void;
  threadSnippets?: Record<string, string>;
  /** Folder card reorder (Dexie `folders.order`) — parent wraps list in SortableContext. */
  folderSortable?: boolean;
};

export const ChatFolderSection = memo(function ChatFolderSection({
  section,
  allFolders,
  activeThreadId,
  interactionDisabled = false,
  draggingThread = false,
  dndEnabled = false,
  threadDragLayout = "row",
  onToggleCollapsed,
  onRenameFolder,
  onDeleteFolder,
  onSelectThread,
  onRenameThread,
  onDeleteThread,
  onMoveThread,
  onTogglePinThread,
  threadSnippets,
  folderSortable = false,
}: ChatFolderSectionProps) {
  const { folder, threads } = section;
  const collapsed = Boolean(folder.collapsed);
  const locked = interactionDisabled;

  const folderSortOn = Boolean(folderSortable && !locked);

  const { setNodeRef, isOver } = useDroppable({
    id: `${FOLDER_DROP_PREFIX}${folder.id}`,
  });

  const {
    setNodeRef: setFolderSortRef,
    setActivatorNodeRef,
    attributes,
    listeners,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: `${FOLDER_SORT_PREFIX}${folder.id}`,
    disabled: !folderSortOn,
    animateLayoutChanges: defaultAnimateLayoutChanges,
    transition: {
      duration: FOLDER_SORT_MS,
      easing: FOLDER_SORT_EASING,
    },
  });

  const dragListenersOnly = listeners as unknown as DragActivatorProps;

  const sortableStyle: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? undefined,
    opacity: isDragging ? 0.68 : 1,
    pointerEvents: isDragging ? "none" : undefined,
    willChange: transform ? "transform" : undefined,
  };

  const threadIds = threads.map((t) => `${THREAD_DND_PREFIX}${t.id}`);
  const dropGlow = Boolean(draggingThread && isOver);

  const renderThread = (thread: (typeof threads)[0]) => {
    const moveModel = buildMoveSelectModel(thread, allFolders);
    const snippet = threadSnippets?.[thread.id];
    return (
      <StableChatThreadListItem
        thread={thread}
        activeThreadId={activeThreadId}
        onSelectThread={onSelectThread}
        onRenameThread={onRenameThread}
        onDeleteThread={onDeleteThread}
        onMoveThreadToFolder={onMoveThread}
        onTogglePinThread={onTogglePinThread}
        updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
        interactionDisabled={locked}
        moveSelect={moveModel.show ? moveModel : null}
        searchSnippet={snippet}
      />
    );
  };

  const renderThreadSortable = (thread: (typeof threads)[0]) => {
    const moveModel = buildMoveSelectModel(thread, allFolders);
    const snippet = threadSnippets?.[thread.id];
    const useHandle = dndEnabled && threadDragLayout === "handle";
    return (
      <SortableChatThreadItem
        key={thread.id}
        threadId={thread.id}
        disabled={locked}
        useDragHandle={useHandle}
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
            onMoveThreadToFolder={onMoveThread}
            onTogglePinThread={onTogglePinThread}
            updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
            interactionDisabled={locked}
            moveSelect={moveModel.show ? moveModel : null}
            dragActivatorProps={dragHandleProps ? undefined : dragActivatorProps}
            dragHandleProps={dragHandleProps}
            dndDragging={isDragging}
            setDragActivatorRef={setDragActivatorRef}
            searchSnippet={snippet}
          />
        )}
      </SortableChatThreadItem>
    );
  };

  const threadList =
    dndEnabled && !locked
      ? threads.map((t) => renderThreadSortable(t))
      : threads.map((t) => <div key={t.id}>{renderThread(t)}</div>);

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "spirit-sidebar-folder-section flex flex-col gap-0 rounded-md transition-colors",
        dropGlow &&
          "border border-[color:color-mix(in_oklab,var(--spirit-accent-strong)_55%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] shadow-[0_0_24px_-10px_var(--spirit-glow)]",
      )}
    >
      <div
        ref={setFolderSortRef}
        style={sortableStyle}
        className="flex min-w-0 flex-col gap-0"
        {...attributes}
        role="group"
        tabIndex={-1}
      >
        <ChatFolderHeaderRow
          key={folder.id}
          folder={folder}
          collapsed={collapsed}
          locked={locked}
          onToggle={() => onToggleCollapsed(folder.id)}
          onRename={() => onRenameFolder(folder.id)}
          onDeleteConfirmed={() => onDeleteFolder(folder.id)}
          folderDragHandleProps={folderSortOn ? dragListenersOnly : undefined}
          setFolderDragActivatorRef={folderSortOn ? setActivatorNodeRef : undefined}
          folderDndDragging={isDragging}
        />
        {!collapsed && threads.length > 0 ? (
          dndEnabled && !locked ? (
            <SortableContext items={threadIds} strategy={verticalListSortingStrategy}>
              <div className="spirit-sidebar-folder-thread-stack ml-1 flex flex-col gap-px border-l border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] pl-1.5">
                {threadList}
              </div>
            </SortableContext>
          ) : (
            <div className="spirit-sidebar-folder-thread-stack ml-1 flex flex-col gap-px border-l border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] pl-1.5">
              {threadList}
            </div>
          )
        ) : null}
      </div>
    </div>
  );
});
