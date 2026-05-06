"use client";

// ── ChatFolderSection - folder droppable + per-folder SortableContext (oldSpiritOS) ─
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { ChevronRight, FolderOpen, PenLine, Trash2 } from "lucide-react";
import { memo, useEffect, useState } from "react";

import { ChatThreadListItem } from "@/components/chat/ChatThreadListItem";
import { SortableChatThreadItem } from "@/components/chat/SortableChatThreadItem";
import { formatThreadUpdatedLabel } from "@/lib/chat-thread-format";
import type { FolderSidebarSection } from "@/lib/chat-folder-utils";
import { buildMoveSelectModel } from "@/lib/chat-folder-utils";
import { FOLDER_DROP_PREFIX, THREAD_DND_PREFIX } from "@/lib/chat-sidebar-dnd";
import type { ChatFolder } from "@/lib/chat-db.types";
import { cn } from "@/lib/cn";

export type ChatFolderHeaderRowProps = {
  folder: ChatFolder;
  collapsed: boolean;
  locked: boolean;
  onToggle: () => void;
  onRename: () => void;
  /** Called only after inline confirm - never deletes threads. */
  onDeleteConfirmed: () => void;
};

export const ChatFolderHeaderRow = memo(function ChatFolderHeaderRow({
  folder,
  collapsed,
  locked,
  onToggle,
  onRename,
  onDeleteConfirmed,
}: ChatFolderHeaderRowProps) {
  const [deleteConfirming, setDeleteConfirming] = useState(false);

  useEffect(() => {
    setDeleteConfirming(false);
  }, [folder.id]);

  return (
    <div
      className={cn(
        "flex min-w-0 flex-1 flex-wrap items-center gap-0.5 rounded-md border border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] bg-white/[0.02] px-1 py-0.5",
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
        className="touch-manipulation rounded p-1 text-chalk/55 transition hover:bg-white/[0.05] hover:text-chalk"
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
        className="h-3.5 w-3.5 shrink-0 text-[color:color-mix(in_oklab,var(--spirit-accent)_55%,transparent)]"
        aria-hidden
        strokeWidth={2}
      />
      <span className="min-w-0 flex-1 truncate font-mono text-[10px] font-semibold uppercase tracking-wide text-chalk/70">
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
        className="touch-manipulation rounded p-1 text-chalk/45 transition hover:bg-white/[0.05] hover:text-chalk"
      >
        <PenLine className="h-3 w-3" aria-hidden strokeWidth={2} />
      </button>
      {deleteConfirming ? (
        <div className="flex min-w-0 basis-full flex-col gap-0.5 border-t border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] pt-0.5 sm:basis-auto sm:flex-row sm:items-center sm:border-t-0 sm:pt-0">
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
          className="touch-manipulation rounded p-1 text-chalk/45 transition hover:bg-rose-500/15 hover:text-rose-200"
        >
          <Trash2 className="h-3 w-3" aria-hidden strokeWidth={2} />
        </button>
      )}
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
}: ChatFolderSectionProps) {
  const { folder, threads } = section;
  const collapsed = Boolean(folder.collapsed);
  const locked = interactionDisabled;

  const { setNodeRef, isOver } = useDroppable({
    id: `${FOLDER_DROP_PREFIX}${folder.id}`,
  });

  const threadIds = threads.map((t) => `${THREAD_DND_PREFIX}${t.id}`);
  const dropGlow = Boolean(draggingThread && isOver);

  const renderThread = (thread: (typeof threads)[0]) => {
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
        thread={thread}
        active={thread.id === activeThreadId}
        updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
        interactionDisabled={locked}
        moveSelect={moveModel.show ? moveModel : null}
        onSelect={() => onSelectThread(thread.id)}
        onRename={() => onRenameThread(thread.id)}
        onDelete={() => onDeleteThread(thread.id)}
        onMoveThread={(fid) => onMoveThread(thread.id, fid)}
        searchSnippet={snippet}
        {...pinProps}
      />
    );
  };

  const renderThreadSortable = (thread: (typeof threads)[0]) => {
    const moveModel = buildMoveSelectModel(thread, allFolders);
    const snippet = threadSnippets?.[thread.id];
    const pinProps =
      onTogglePinThread != null
        ? {
            pinned: Boolean(thread.pinned),
            onTogglePin: () => onTogglePinThread(thread.id),
          }
        : {};
    const useHandle = dndEnabled && threadDragLayout === "handle";
    return (
      <SortableChatThreadItem
        key={thread.id}
        threadId={thread.id}
        disabled={locked}
        useDragHandle={useHandle}
      >
        {({ dragActivatorProps, dragHandleProps, isDragging }) => (
          <ChatThreadListItem
            thread={thread}
            active={thread.id === activeThreadId}
            updatedLabel={formatThreadUpdatedLabel(thread.updatedAt)}
            interactionDisabled={locked}
            moveSelect={moveModel.show ? moveModel : null}
            dragActivatorProps={dragHandleProps ? undefined : dragActivatorProps}
            dragHandleProps={dragHandleProps}
            dndDragging={Boolean(dragHandleProps && isDragging)}
            onSelect={() => onSelectThread(thread.id)}
            onRename={() => onRenameThread(thread.id)}
            onDelete={() => onDeleteThread(thread.id)}
            onMoveThread={(fid) => onMoveThread(thread.id, fid)}
            searchSnippet={snippet}
            {...pinProps}
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
        "flex flex-col gap-1 rounded-md transition-colors",
        dropGlow &&
          "border border-[color:color-mix(in_oklab,var(--spirit-accent-strong)_55%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] shadow-[0_0_24px_-10px_var(--spirit-glow)]",
      )}
    >
      <ChatFolderHeaderRow
        folder={folder}
        collapsed={collapsed}
        locked={locked}
        onToggle={() => onToggleCollapsed(folder.id)}
        onRename={() => onRenameFolder(folder.id)}
        onDeleteConfirmed={() => onDeleteFolder(folder.id)}
      />
      {!collapsed ? (
        dndEnabled && !locked ? (
          <SortableContext items={threadIds} strategy={verticalListSortingStrategy}>
            <div className="ml-1 flex flex-col gap-0.5 border-l border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] pl-1.5">
              {threads.length === 0 ? (
                <p className="py-0.5 pl-0.5 font-mono text-[8px] text-chalk/35">
                  Drop chats here
                </p>
              ) : null}
              {threadList}
            </div>
          </SortableContext>
        ) : (
          <div className="ml-1 flex flex-col gap-0.5 border-l border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] pl-1.5">
            {threads.length === 0 ? (
              <p className="py-0.5 pl-0.5 font-mono text-[8px] text-chalk/35">Drop chats here</p>
            ) : null}
            {threadList}
          </div>
        )
      ) : (
        <div className="ml-1 min-h-[24px] border-l border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] pl-1.5">
          <p className="py-0.5 pl-0.5 font-mono text-[8px] text-chalk/35">
            Collapsed - drop to file
          </p>
        </div>
      )}
    </div>
  );
});
