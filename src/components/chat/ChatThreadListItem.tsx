"use client";

// ── ChatThreadListItem - row drag on trinity /chat; handle mode elsewhere (9F) ──
import type { DraggableAttributes, DraggableSyntheticListeners } from "@dnd-kit/core";
import { ArrowRightLeft, GripVertical, PenLine, Pin, PinOff, Trash2 } from "lucide-react";
import { memo, useCallback, useState } from "react";

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
};

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
}: ChatThreadListItemProps) {
  const [moveOpen, setMoveOpen] = useState(false);
  const showMove =
    Boolean(moveSelect && onMoveThread) && !interactionDisabled;

  const closeMove = useCallback(() => setMoveOpen(false), []);

  const handleDrag = Boolean(dragHandleProps);
  const rowDrag = Boolean(dragActivatorProps && !dragHandleProps);

  return (
    <div
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
          className={cn(
            "min-w-0 touch-manipulation rounded-md py-px",
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
                "spirit-thread-row__title line-clamp-2 text-[13px] font-semibold leading-[1.38] tracking-tight text-chalk",
                active && "text-[color:var(--spirit-accent-strong)]",
              )}
            >
              {pinned ? (
                <Pin
                  className="mr-0.5 inline h-3 w-3 shrink-0 text-amber-200/90"
                  aria-hidden
                />
              ) : null}
              {thread.title}
            </span>
            <span className="spirit-thread-row__meta mt-1 block truncate text-[11px] leading-tight tabular-nums text-chalk/50">
              {updatedLabel}
            </span>
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
