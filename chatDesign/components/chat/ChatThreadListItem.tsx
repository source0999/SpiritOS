"use client";

// ── ChatThreadListItem - rail rows; Trinity Recent = demo strip + ⋮ popout ────
import type { DraggableAttributes, DraggableSyntheticListeners } from "@dnd-kit/core";
import {
  ArrowRightLeft,
  GripVertical,
  MessageCircle,
  MoreVertical,
  PenLine,
  Pin,
  PinOff,
  Trash2,
} from "lucide-react";
import { memo, useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
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
  /** Whole-row drag surface (desktop rail / trinity row mode). */
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
};

const POPOUT_W = 224;
const POPOUT_MAX_H = 320;

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

  useEffect(() => {
    if (actionLayout !== "trinity-recent") setMenuOpen(false);
  }, [actionLayout]);

  useLayoutEffect(() => {
    if (actionLayout !== "trinity-recent" || !menuOpen) {
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
              className="spirit-thread-row-popout pointer-events-auto flex flex-col gap-0.5 rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-border)_55%,rgba(255,255,255,0.35))] bg-[color:color-mix(in_oklab,white_94%,rgba(15,23,42,0.04))] p-1 shadow-[0_18px_50px_-20px_rgba(15,23,42,0.45)] backdrop-blur-xl"
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
                  className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-[13px] font-medium text-slate-700/95 transition hover:bg-slate-900/[0.06] disabled:opacity-35"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (interactionDisabled) return;
                    onTogglePin();
                    closeMenu();
                  }}
                >
                  {pinned ? (
                    <PinOff className="h-4 w-4 shrink-0 text-slate-500" aria-hidden />
                  ) : (
                    <Pin className="h-4 w-4 shrink-0 text-slate-500" aria-hidden />
                  )}
                  {pinned ? "Unpin" : "Pin"}
                </button>
              ) : null}
              <button
                type="button"
                role="menuitem"
                disabled={interactionDisabled}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-[13px] font-medium text-slate-700/95 transition hover:bg-slate-900/[0.06] disabled:opacity-35"
                onClick={(e) => {
                  e.stopPropagation();
                  if (interactionDisabled) return;
                  onRename();
                  closeMenu();
                }}
              >
                <PenLine className="h-4 w-4 shrink-0 text-slate-500" aria-hidden />
                Rename
              </button>
              {showMove ? (
                <label className="flex flex-col gap-1 rounded-lg px-2 py-1.5 hover:bg-slate-900/[0.04]">
                  <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
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
                    className="w-full cursor-pointer rounded-md border border-slate-200/90 bg-white/80 px-2 py-2 text-[12px] text-slate-700 outline-none transition hover:border-slate-300"
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
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-[13px] font-medium text-rose-700/95 transition hover:bg-rose-500/[0.08] disabled:opacity-35"
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
            "spirit-thread-row-shell group flex min-w-0 flex-col gap-0.5 rounded-xl border px-3 py-2 transition",
            interactionDisabled && "pointer-events-none opacity-35",
          )}
        >
          <div
            className={cn(
              "spirit-chat-thread-row spirit-chat-thread-row--trinity-recent flex min-w-0 items-center",
              handleDrag ? "gap-2" : "gap-0",
            )}
          >
            {handleDrag ? (
              <button
                type="button"
                {...dragHandleProps}
                ref={setDragActivatorRef}
                disabled={interactionDisabled}
                aria-label={`Drag to reorder ${thread.title}`}
                className={cn(
                  "inline-flex size-9 shrink-0 touch-none items-center justify-center self-center rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_38%,transparent)] bg-white/[0.06] text-chalk/55 transition active:scale-[0.98]",
                  "hover:border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] hover:bg-white/[0.1] hover:text-chalk/75",
                  dndDragging &&
                    "border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] text-[color:var(--spirit-accent-strong)]",
                )}
                style={{ touchAction: "none" }}
              >
                <GripVertical className="h-4 w-4 opacity-80" aria-hidden />
              </button>
            ) : null}
            <div
              className={cn(
                "spirit-thread-row__main flex min-w-0 flex-1 items-center gap-2.5 touch-manipulation",
              )}
            >
              {rowDrag ? (
                <button
                  type="button"
                  {...dragActivatorProps}
                  ref={setDragActivatorRef}
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
              ) : (
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
                      className="spirit-thread-row__pin-badge h-3 w-3 shrink-0 text-amber-200/75"
                      aria-hidden
                      strokeWidth={1.75}
                    />
                  ) : null}
                  <span
                    className={cn(
                      "spirit-thread-row__title-text min-w-0 flex-1 truncate text-[13px] font-medium leading-snug tracking-tight text-chalk/78",
                      active && "text-[color:var(--spirit-accent-strong)]",
                    )}
                  >
                    {thread.title}
                  </span>
                </span>
                {hideUpdatedLabel ? null : (
                  <span className="spirit-thread-row__meta mt-0.5 block truncate text-[10px] leading-tight tabular-nums text-chalk/38">
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
                className="inline-flex h-9 min-w-[2.25rem] shrink-0 touch-manipulation items-center justify-center rounded-lg text-chalk/45 transition hover:bg-white/[0.08] hover:text-chalk/80 disabled:opacity-30"
                onClick={(e) => {
                  e.stopPropagation();
                  if (interactionDisabled) return;
                  setMenuOpen((o) => !o);
                }}
              >
                <MoreVertical className="h-4 w-4" aria-hidden strokeWidth={2} />
              </button>
            </div>
          </div>
          {searchSnippet ? (
            <p className="line-clamp-2 pl-[calc(1.1rem+0.625rem)] pr-10 text-[10px] leading-snug text-chalk/40">
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
        "spirit-thread-row-shell group flex min-w-0 flex-col gap-1 rounded-[10px] border px-2.5 py-1.5 transition",
        active
          ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_28%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
          : "border-transparent bg-transparent hover:border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] hover:bg-white/[0.04]",
      )}
    >
      <div
        className={cn(
          "spirit-chat-thread-row grid min-w-0 items-start gap-x-2 gap-y-0.5",
          handleDrag
            ? "grid-cols-[2rem_minmax(0,1fr)_auto]"
            : "grid-cols-[minmax(0,1fr)_auto]",
        )}
      >
        {handleDrag ? (
          <button
            type="button"
            {...dragHandleProps}
            ref={setDragActivatorRef}
            disabled={interactionDisabled}
            aria-label={`Drag to reorder ${thread.title}`}
            className={cn(
              "col-start-1 row-start-1 inline-flex size-8 shrink-0 touch-none items-center justify-center self-start rounded-md border border-[color:color-mix(in_oklab,var(--spirit-border)_38%,transparent)] bg-white/[0.05] text-chalk/50 transition active:scale-[0.98]",
              "hover:border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] hover:bg-white/[0.08] hover:text-chalk/65",
              dndDragging &&
                "border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] text-[color:var(--spirit-accent-strong)]",
            )}
            style={{ touchAction: "none" }}
          >
            <GripVertical className="h-4 w-4 opacity-70" aria-hidden />
          </button>
        ) : null}
        <div
          {...(rowDrag ? dragActivatorProps : {})}
          ref={rowDrag ? setDragActivatorRef : undefined}
          className={cn(
            "spirit-thread-row__main min-w-0 touch-manipulation rounded-md py-px",
            handleDrag ? "col-start-2 row-start-1" : "col-start-1 row-start-1",
            rowDrag && "cursor-grab touch-pan-y active:cursor-grabbing",
          )}
        >
          <button
            type="button"
            onClick={onSelect}
            aria-current={active ? "true" : undefined}
            aria-label={`Open conversation · ${thread.title}`}
            className="block w-full min-w-0 touch-manipulation text-left"
          >
            <span
              className={cn(
                "spirit-thread-row__title flex min-w-0 items-center gap-1 text-[13px] font-medium leading-[1.38] tracking-tight text-chalk",
                active && "text-[color:var(--spirit-accent-strong)]",
              )}
            >
              {pinned ? (
                <Pin
                  className="spirit-thread-row__pin-badge h-3.5 w-3.5 shrink-0 text-chalk/50"
                  aria-hidden
                  strokeWidth={1.75}
                />
              ) : null}
              <span className="spirit-thread-row__title-text min-w-0 flex-1 break-words line-clamp-2">
                {thread.title}
              </span>
            </span>
            {hideUpdatedLabel ? null : (
              <span className="spirit-thread-row__meta mt-1 block truncate text-[11px] leading-tight tabular-nums text-chalk/50">
                {updatedLabel}
              </span>
            )}
            {searchSnippet ? (
              <span className="mt-1 line-clamp-2 text-[10px] leading-snug text-chalk/45">
                {searchSnippet}
              </span>
            ) : null}
          </button>
        </div>
        <div
          className={cn(
            "spirit-thread-row__actions flex shrink-0 flex-row gap-px transition-opacity",
            handleDrag ? "col-start-3 row-start-1" : "col-start-2 row-start-1",
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
              className="touch-manipulation rounded-md p-1.5 text-chalk/45 transition hover:bg-white/[0.06] hover:text-amber-100/85 disabled:opacity-30 active:scale-[0.98]"
            >
              {pinned ? (
                <PinOff className="h-3 w-3" aria-hidden />
              ) : (
                <Pin className="h-3 w-3" aria-hidden />
              )}
            </button>
          ) : null}
          <button
            type="button"
            disabled={interactionDisabled}
            onClick={(e) => {
              e.stopPropagation();
              if (interactionDisabled) return;
              onRename();
            }}
            aria-label={`Rename thread ${thread.title}`}
            className="touch-manipulation rounded-md p-1.5 text-chalk/45 transition hover:bg-white/[0.06] hover:text-chalk/80 disabled:opacity-30 active:scale-[0.98]"
          >
            <PenLine className="h-3 w-3" aria-hidden />
          </button>
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
                "touch-manipulation rounded-md p-1.5 text-chalk/45 transition hover:bg-white/[0.06] hover:text-chalk/80 disabled:opacity-30 active:scale-[0.98]",
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
            className="touch-manipulation rounded-md p-1.5 text-chalk/45 transition hover:bg-rose-500/12 hover:text-rose-200/90 disabled:opacity-30 active:scale-[0.98]"
          >
            <Trash2 className="h-3 w-3" aria-hidden />
          </button>
        </div>
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

/** @see `src/components/chat/ChatThreadListItem.tsx` — same stable row wrapper for chatDesign parity. */
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
