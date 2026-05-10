"use client";

// ── ChatThreadListItem - rail rows; Trinity Recent = demo strip + ⋮ popout ────
import type { DraggableAttributes, DraggableSyntheticListeners } from "@dnd-kit/core";
import {
  ArrowRightLeft,
  MessageCircle,
  MoreVertical,
  PenLine,
  Pin,
  PinOff,
  Trash2,
} from "lucide-react";
import {
  memo,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

import type { MoveSelectOption } from "@/lib/chat-folder-utils";
import type { ChatThread } from "@/lib/chat-db.types";
import { cn } from "@/lib/cn";

export type ChatThreadDragActivatorProps = DraggableAttributes &
  DraggableSyntheticListeners;

export type ChatThreadListItemProps = {
  thread: ChatThread;
  active: boolean;
  updatedLabel: string;
  onSelect: () => void;
  onRename: () => void;
  onDelete: () => void;
  moveSelect?: { value: string; options: MoveSelectOption[] } | null;
  onMoveThread?: (folderId: string | null) => void;
  /** Optional search hit snippet (under title) */
  searchSnippet?: string | null;
  pinned?: boolean;
  onTogglePin?: () => void;
  /** Row drag (listeners on bubble / rail strip) — only when no handle; never on title. */
  dragActivatorProps?: ChatThreadDragActivatorProps;
  /** Drawer: drag listeners live only on the grip — unused when row-only. */
  dragHandleProps?: ChatThreadDragActivatorProps;
  /** dnd-kit: drawer handle drag pulse (ignored when row-drag). */
  dndDragging?: boolean;
  interactionDisabled?: boolean;
  /** Trinity pinned rail: demo-style single line, no “2h ago” under title. */
  hideUpdatedLabel?: boolean;
  /** Trinity Recent: left bubble · title · kebab; actions live in a portal popout. */
  actionLayout?: "inline" | "trinity-recent";
  /** Same DOM node as drag `listeners` (Sortable → useSortable.setActivatorNodeRef). */
  setDragActivatorRef?: (element: HTMLElement | null) => void;
  /**
   * @deprecated Whole-row drag competed with title clicks; handle-only DnD is the contract now.
   */
  dragWholeRowSurface?: boolean;
};

const POPOUT_W = 224;
const POPOUT_MAX_H = 320;

/** dnd-kit activator — min(80% row, remaining width after actions); trinity = ⋮ strip, inline = fat icon rail. */
function ThreadEdgeDragHandle({
  threadTitle,
  dragHandleProps,
  setDragActivatorRef,
  interactionDisabled,
  dndDragging,
  actionLayout,
}: {
  threadTitle: string;
  dragHandleProps: ChatThreadDragActivatorProps;
  setDragActivatorRef?: (element: HTMLElement | null) => void;
  interactionDisabled: boolean;
  dndDragging: boolean;
  actionLayout: "trinity-recent" | "inline";
}) {
  return (
    <button
      type="button"
      {...dragHandleProps}
      ref={setDragActivatorRef}
      disabled={interactionDisabled}
      data-drag-handle="thread-edge"
      aria-label={`Drag to reorder ${threadTitle}`}
      className={cn(
        "spirit-thread-row__drag-edge pointer-events-auto absolute left-0 top-0 z-[10] h-full min-h-[2.25rem] touch-none",
        actionLayout === "trinity-recent"
          ? "w-[min(80%,calc(100%-2.75rem))]"
          : "w-[min(80%,calc(100%-7.5rem))]",
        "cursor-grab border-0 bg-transparent p-0 opacity-0 outline-none active:cursor-grabbing",
        "focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-[color:color-mix(in_oklab,var(--spirit-accent-strong)_35%,transparent)] focus-visible:ring-inset",
        dndDragging && "opacity-100",
      )}
      style={{ touchAction: "none" }}
    />
  );
}

export const ChatThreadListItem = memo(function ChatThreadListItem({
  thread,
  active,
  updatedLabel,
  onSelect,
  onRename,
  onDelete,
  moveSelect,
  onMoveThread,
  searchSnippet,
  pinned = false,
  onTogglePin,
  dragActivatorProps,
  dragHandleProps,
  dndDragging = false,
  interactionDisabled = false,
  hideUpdatedLabel = false,
  actionLayout = "inline",
  setDragActivatorRef,
  dragWholeRowSurface: _dragWholeRowSurface = false,
}: ChatThreadListItemProps) {
  const [moveOpen, setMoveOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [popoutPos, setPopoutPos] = useState<{
    top: number;
    left: number;
    width: number;
    maxHeight: number;
  } | null>(null);

  const menuBtnRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const showMove =
    Boolean(moveSelect && onMoveThread) && !interactionDisabled;
  const closeMove = useCallback(() => setMoveOpen(false), []);
  const closeMenu = useCallback(() => setMenuOpen(false), []);

  const handleDrag = Boolean(dragHandleProps);
  const rowDrag = Boolean(dragActivatorProps && !dragHandleProps);
  const rowDragBubble = rowDrag;

  const bindDragActivatorRef = useCallback(
    (element: HTMLElement | null) => {
      setDragActivatorRef?.(element);
    },
    [setDragActivatorRef],
  );

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- popout only valid in trinity-recent layout
    if (actionLayout !== "trinity-recent") setMenuOpen(false);
  }, [actionLayout]);

  useLayoutEffect(() => {
    if (actionLayout !== "trinity-recent" || !menuOpen) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- clear fixed popout when menu closes
      setPopoutPos(null);
      return;
    }
    const btn = menuBtnRef.current;
    if (!btn) return;
    const r = btn.getBoundingClientRect();
    const width = POPOUT_W;
    let left = r.right - width;
    left = Math.max(10, Math.min(left, window.innerWidth - width - 10));
    let top = r.bottom + 8;
    const spaceBelow = window.innerHeight - top - 12;
    const spaceAbove = r.top - 12;
    let maxHeight = POPOUT_MAX_H;
    if (spaceBelow < 160 && spaceAbove > spaceBelow) {
      maxHeight = Math.min(POPOUT_MAX_H, spaceAbove - 8);
      top = Math.max(10, r.top - maxHeight - 8);
    } else {
      maxHeight = Math.min(POPOUT_MAX_H, spaceBelow);
    }
    setPopoutPos({ top, left, width, maxHeight });
  }, [actionLayout, menuOpen]);

  useEffect(() => {
    if (actionLayout !== "trinity-recent" || !menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeMenu();
    };
    const onPtr = (e: PointerEvent) => {
      const t = e.target as Node;
      if (menuBtnRef.current?.contains(t) || panelRef.current?.contains(t)) return;
      // Defer so the row’s title <button> still receives the full click sequence if another row’s
      // ⋮ menu was open (capture runs before the target’s click).
      queueMicrotask(() => {
        closeMenu();
      });
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("pointerdown", onPtr, true);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("pointerdown", onPtr, true);
    };
  }, [actionLayout, menuOpen, closeMenu]);

  if (actionLayout === "trinity-recent") {
    const popout =
      menuOpen && popoutPos != null && typeof document !== "undefined"
        ? createPortal(
            <div
              ref={panelRef}
              role="menu"
              aria-label={`Actions for ${thread.title}`}
              data-trinity-liquid="popout"
              className="spirit-thread-row-popout spirit-trinity-modal-glass pointer-events-auto flex flex-col gap-0.5 rounded-xl border border-transparent bg-transparent p-1 shadow-none backdrop-blur-xl"
              style={{
                position: "fixed",
                top: popoutPos.top,
                left: popoutPos.left,
                width: popoutPos.width,
                maxHeight: popoutPos.maxHeight,
                zIndex: 320,
                overflowY: "auto",
              }}
            >
              {onTogglePin ? (
                <button
                  type="button"
                  role="menuitem"
                  disabled={interactionDisabled}
                  className="spirit-trinity-popout-item flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-[13px] font-medium text-chalk/88 transition hover:bg-white/[0.06] disabled:opacity-35"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (interactionDisabled) return;
                    onTogglePin();
                    closeMenu();
                  }}
                >
                  {pinned ? (
                    <PinOff className="h-4 w-4 shrink-0 text-chalk/55" aria-hidden />
                  ) : (
                    <Pin className="h-4 w-4 shrink-0 text-chalk/55" aria-hidden />
                  )}
                  {pinned ? "Unpin" : "Pin"}
                </button>
              ) : null}
              <button
                type="button"
                role="menuitem"
                disabled={interactionDisabled}
                className="spirit-trinity-popout-item flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-[13px] font-medium text-chalk/88 transition hover:bg-white/[0.06] disabled:opacity-35"
                onClick={(e) => {
                  e.stopPropagation();
                  if (interactionDisabled) return;
                  onRename();
                  closeMenu();
                }}
              >
                <PenLine className="h-4 w-4 shrink-0 text-chalk/55" aria-hidden />
                Rename
              </button>
              {showMove ? (
                <label className="spirit-trinity-popout-move flex flex-col gap-1 rounded-lg px-2 py-1.5">
                  <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-chalk/52">
                    <ArrowRightLeft className="h-3 w-3" aria-hidden />
                    Move to folder
                  </span>
                  <select
                    value={moveSelect!.value}
                    title="Move chat"
                    disabled={interactionDisabled}
                    onChange={(e) => {
                      const v = e.target.value;
                      if (!onMoveThread) return;
                      if (v === moveSelect!.value) return;
                      onMoveThread(v === "__root__" ? null : v);
                      closeMenu();
                    }}
                    className="spirit-trinity-glass-select w-full cursor-pointer rounded-md border border-transparent bg-transparent px-2 py-2 text-[12px] text-chalk/88 outline-none"
                  >
                    {moveSelect!.options.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
              <button
                type="button"
                role="menuitem"
                disabled={interactionDisabled}
                className="spirit-trinity-popout-item spirit-trinity-popout-item--danger flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-[13px] font-medium transition disabled:opacity-35"
                onClick={(e) => {
                  e.stopPropagation();
                  if (interactionDisabled) return;
                  onDelete();
                  closeMenu();
                }}
              >
                <Trash2 className="h-4 w-4 shrink-0" aria-hidden />
                Delete
              </button>
            </div>,
            document.body,
          )
        : null;

    return (
      <>
        <div
          data-active={active ? "true" : undefined}
          data-pinned={pinned ? "true" : undefined}
          data-action-layout="trinity-recent"
          className={cn(
            "spirit-thread-row-shell group relative flex min-w-0 flex-col gap-0.5 rounded-md border border-transparent px-1.5 py-0.5 transition",
            interactionDisabled && "pointer-events-none opacity-35",
          )}
        >
          <div
            className={cn(
              "spirit-chat-thread-row spirit-chat-thread-row--trinity-recent relative isolate flex min-w-0 items-center gap-1.5",
            )}
          >
            <div
              className={cn(
                "spirit-thread-row__main flex min-w-0 flex-1 items-center gap-1.5 touch-manipulation",
                handleDrag && "relative z-0",
              )}
            >
              {rowDragBubble ? (
                <button
                  type="button"
                  {...dragActivatorProps}
                  ref={bindDragActivatorRef}
                  disabled={interactionDisabled}
                  aria-label={`Drag to reorder ${thread.title}`}
                  className={cn(
                    "spirit-thread-row__drag-bubble inline-flex shrink-0 touch-none items-center justify-center rounded-md p-1.5 text-chalk/42 transition active:scale-[0.98]",
                    "cursor-grab hover:bg-white/[0.06] hover:text-chalk/60 active:cursor-grabbing",
                    dndDragging && "text-[color:var(--spirit-accent-strong)]",
                  )}
                  style={{ touchAction: "none" }}
                >
                  <MessageCircle
                    className="spirit-thread-row__leading-icon h-[1.1rem] w-[1.1rem] shrink-0"
                    aria-hidden
                    strokeWidth={1.65}
                  />
                </button>
              ) : handleDrag ? null : (
                <MessageCircle
                  className="spirit-thread-row__leading-icon h-[1.1rem] w-[1.1rem] shrink-0 text-chalk/40"
                  aria-hidden
                  strokeWidth={1.65}
                />
              )}
              <button
                type="button"
                onClick={onSelect}
                aria-current={active ? "true" : undefined}
                aria-label={`Open conversation · ${thread.title}`}
                className="spirit-thread-row__title-button flex min-w-0 flex-1 flex-col items-stretch text-left touch-manipulation"
              >
                <span className="spirit-thread-row__title flex min-w-0 w-full items-center gap-1">
                  {pinned ? (
                    <Pin
                      className="spirit-thread-row__pin-badge h-2.5 w-2.5 shrink-0 text-amber-200/75"
                      aria-hidden
                      strokeWidth={1.75}
                    />
                  ) : null}
                  <span
                    className={cn(
                      "spirit-thread-row__title-text min-w-0 flex-1 truncate text-[12px] font-medium leading-tight tracking-tight text-chalk/78",
                      active && "text-[color:var(--spirit-accent-strong)]",
                    )}
                  >
                    {thread.title}
                  </span>
                </span>
                {hideUpdatedLabel ? null : (
                  <span className="spirit-thread-row__meta block truncate text-[9px] leading-tight tabular-nums text-chalk/36">
                    {updatedLabel}
                  </span>
                )}
              </button>
            </div>
            <div
              className="spirit-thread-row__actions spirit-thread-row__actions--popout flex shrink-0 items-center self-stretch"
              onPointerDown={(e) => e.stopPropagation()}
            >
              <button
                ref={menuBtnRef}
                type="button"
                disabled={interactionDisabled}
                aria-expanded={menuOpen}
                aria-haspopup="menu"
                aria-label={`Thread options · ${thread.title}`}
                className="inline-flex h-7 w-7 shrink-0 touch-manipulation items-center justify-center rounded-md text-chalk/45 transition hover:bg-white/[0.08] hover:text-chalk/80 disabled:opacity-30 [@media(pointer:coarse)]:h-9 [@media(pointer:coarse)]:w-9"
                onClick={(e) => {
                  e.stopPropagation();
                  if (interactionDisabled) return;
                  setMenuOpen((o) => !o);
                }}
              >
                <MoreVertical className="h-3.5 w-3.5 [@media(pointer:coarse)]:h-4 [@media(pointer:coarse)]:w-4" aria-hidden strokeWidth={2} />
              </button>
            </div>
            {handleDrag && dragHandleProps ? (
              <ThreadEdgeDragHandle
                threadTitle={thread.title}
                dragHandleProps={dragHandleProps}
                setDragActivatorRef={bindDragActivatorRef}
                interactionDisabled={interactionDisabled}
                dndDragging={dndDragging}
                actionLayout="trinity-recent"
              />
            ) : null}
          </div>
          {searchSnippet ? (
            <p className="line-clamp-2 pl-1 pr-8 text-[9px] leading-snug text-chalk/40">
              {searchSnippet}
            </p>
          ) : null}
        </div>
        {popout}
      </>
    );
  }

  return (
    <div
      data-active={active ? "true" : undefined}
      data-pinned={pinned ? "true" : undefined}
      className={cn(
        "spirit-thread-row-shell group relative flex min-w-0 flex-col gap-0.5 rounded-md border px-1.5 py-0.5 transition",
        active
          ? "border-chalk/10 bg-white/[0.04] border-l-2 border-l-[color:var(--spirit-accent-strong)]"
          : "border-transparent hover:border-chalk/8 hover:bg-white/[0.03]",
      )}
    >
      <div
        className={cn("spirit-chat-thread-row relative isolate flex min-w-0 items-center gap-1.5")}
      >
        <div
          {...(rowDrag ? dragActivatorProps : {})}
          ref={rowDrag ? bindDragActivatorRef : undefined}
          className={cn(
            "spirit-thread-row__main min-w-0 flex-1 touch-manipulation rounded-sm py-px",
            rowDrag && "cursor-grab touch-pan-y active:cursor-grabbing",
            handleDrag && "relative z-0",
          )}
        >
          <button
            type="button"
            onClick={onSelect}
            aria-current={active ? "true" : undefined}
            aria-label={`Open conversation · ${thread.title}`}
            className="spirit-thread-row__title-button block w-full min-w-0 touch-manipulation text-left"
          >
            <span
              className={cn(
                "spirit-thread-row__title flex min-w-0 items-center gap-1 text-[12px] font-medium leading-tight tracking-tight text-chalk/88",
                active && "text-[color:var(--spirit-accent-strong)]",
              )}
            >
              {pinned ? (
                <Pin
                  className="spirit-thread-row__pin-badge h-3 w-3 shrink-0 text-chalk/48"
                  aria-hidden
                  strokeWidth={1.75}
                />
              ) : null}
              <span className="spirit-thread-row__title-text min-w-0 flex-1 truncate">
                {thread.title}
              </span>
            </span>
            {hideUpdatedLabel ? null : (
              <span className="spirit-thread-row__meta mt-0.5 block truncate text-[9px] leading-tight tabular-nums text-chalk/42">
                {updatedLabel}
              </span>
            )}
            {searchSnippet ? (
              <span className="mt-0.5 line-clamp-2 text-[9px] leading-snug text-chalk/40">
                {searchSnippet}
              </span>
            ) : null}
          </button>
        </div>
        <div
          className={cn(
            "spirit-thread-row__actions flex shrink-0 flex-row items-center gap-px transition-opacity",
            "max-sm:opacity-40 max-sm:group-hover:opacity-90 max-sm:group-focus-within:opacity-90",
            "sm:opacity-0 sm:group-hover:opacity-100 sm:group-focus-within:opacity-100",
            interactionDisabled && "pointer-events-none opacity-25",
          )}
          onPointerDown={(e) => e.stopPropagation()}
        >
          {onTogglePin ? (
            <button
              type="button"
              disabled={interactionDisabled}
              onClick={(e) => {
                e.stopPropagation();
                if (interactionDisabled) return;
                onTogglePin();
              }}
              aria-label={pinned ? `Unpin ${thread.title}` : `Pin ${thread.title}`}
              className="touch-manipulation rounded-sm p-1 text-chalk/42 transition hover:bg-white/[0.06] hover:text-amber-100/85 disabled:opacity-30 active:scale-[0.98] [@media(pointer:coarse)]:p-1.5"
            >
              {pinned ? (
                <PinOff className="h-3 w-3" aria-hidden />
              ) : (
                <Pin className="h-3 w-3" aria-hidden />
              )}
            </button>
          ) : null}
          {showMove ? (
            <button
              type="button"
              disabled={interactionDisabled}
              onClick={(e) => {
                e.stopPropagation();
                if (interactionDisabled) return;
                setMoveOpen((v) => !v);
              }}
              aria-expanded={moveOpen}
              aria-label={`Move thread ${thread.title}`}
              className={cn(
                "touch-manipulation rounded-sm p-1 text-chalk/42 transition hover:bg-white/[0.06] hover:text-chalk/78 disabled:opacity-30 active:scale-[0.98] [@media(pointer:coarse)]:p-1.5",
                moveOpen && "bg-white/[0.06] text-chalk/75",
              )}
            >
              <ArrowRightLeft className="h-3 w-3" aria-hidden />
            </button>
          ) : null}
          <button
            type="button"
            disabled={interactionDisabled}
            onClick={(e) => {
              e.stopPropagation();
              if (interactionDisabled) return;
              onDelete();
            }}
            aria-label={`Delete thread ${thread.title}`}
            className="touch-manipulation rounded-sm p-1 text-chalk/42 transition hover:bg-rose-500/12 hover:text-rose-200/90 disabled:opacity-30 active:scale-[0.98] [@media(pointer:coarse)]:p-1.5"
          >
            <Trash2 className="h-3 w-3" aria-hidden />
          </button>
        </div>
        {handleDrag && dragHandleProps ? (
          <ThreadEdgeDragHandle
            threadTitle={thread.title}
            dragHandleProps={dragHandleProps}
            setDragActivatorRef={bindDragActivatorRef}
            interactionDisabled={interactionDisabled}
            dndDragging={dndDragging}
            actionLayout={actionLayout}
          />
        ) : null}
      </div>
      {showMove && moveOpen ? (
        <div
          className="pl-0.5 pt-0.5"
          onPointerDown={(e) => e.stopPropagation()}
        >
          <label className="flex flex-col gap-0.5">
            <span className="text-[10px] font-medium uppercase tracking-[0.12em] text-chalk/42">
              Move to folder
            </span>
            <select
              value={moveSelect!.value}
              title="Move chat"
              onChange={(e) => {
                const v = e.target.value;
                if (!onMoveThread) return;
                if (v === moveSelect!.value) return;
                onMoveThread(v === "__root__" ? null : v);
                closeMove();
              }}
              className={cn(
                "w-full max-w-full cursor-pointer rounded-md border border-[color:color-mix(in_oklab,var(--spirit-border)_45%,transparent)] bg-black/20 px-1.5 py-1 text-[11px] text-chalk/75 outline-none transition",
                "hover:border-[color:color-mix(in_oklab,var(--spirit-accent)_35%,transparent)]",
              )}
            >
              {moveSelect!.options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}
    </div>
  );
});

/** Sidebar/folder rows: stable handler identities so `memo(ChatThreadListItem)` survives parent re-renders. */
export type StableChatThreadListItemProps = Omit<
  ChatThreadListItemProps,
  "active" | "onSelect" | "onRename" | "onDelete" | "onMoveThread" | "pinned" | "onTogglePin"
> & {
  thread: ChatThread;
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
  onRenameThread: (id: string) => void;
  onDeleteThread: (id: string) => void;
  onMoveThreadToFolder: (threadId: string, folderId: string | null) => void;
  onTogglePinThread?: (id: string) => void;
};

export const StableChatThreadListItem = memo(function StableChatThreadListItem({
  thread,
  activeThreadId,
  onSelectThread,
  onRenameThread,
  onDeleteThread,
  onMoveThreadToFolder,
  onTogglePinThread,
  ...rest
}: StableChatThreadListItemProps) {
  const onSelect = useCallback(() => {
    onSelectThread(thread.id);
  }, [onSelectThread, thread.id]);
  const onRename = useCallback(() => {
    onRenameThread(thread.id);
  }, [onRenameThread, thread.id]);
  const onDelete = useCallback(() => {
    onDeleteThread(thread.id);
  }, [onDeleteThread, thread.id]);
  const onMoveThread = useCallback(
    (folderId: string | null) => {
      onMoveThreadToFolder(thread.id, folderId);
    },
    [onMoveThreadToFolder, thread.id],
  );
  const onTogglePin = useCallback(() => {
    onTogglePinThread?.(thread.id);
  }, [onTogglePinThread, thread.id]);

  return (
    <ChatThreadListItem
      thread={thread}
      active={thread.id === activeThreadId}
      onSelect={onSelect}
      onRename={onRename}
      onDelete={onDelete}
      onMoveThread={onMoveThread}
      {...(onTogglePinThread != null
        ? { pinned: Boolean(thread.pinned), onTogglePin }
        : {})}
      {...rest}
    />
  );
});
