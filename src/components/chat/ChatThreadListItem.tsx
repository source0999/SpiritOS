"use client";

// ── ChatThreadListItem - handle drag for rail + drawer (row drag stole first tap vs select) (9F) ──
import type { DraggableAttributes, DraggableSyntheticListeners } from "@dnd-kit/core";
import { ArrowRightLeft, PenLine, Pin, PinOff, Trash2 } from "lucide-react";
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
  /** Whole-row drag surface (desktop rail). */
  dragActivatorProps?: ChatThreadDragActivatorProps;
  /** Drawer: drag listeners live only on the grip - keeps scroll usable. */
  dragHandleProps?: ChatThreadDragActivatorProps;
  /** dnd-kit: accent the handle while dragging (drawer handle mode). */
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

  const rowDrag = Boolean(dragActivatorProps && !dragHandleProps);
  const handleDrag = Boolean(dragHandleProps);

  return (
    <div
      className={cn(
        "group flex min-w-0 gap-1 rounded-lg border px-1.5 py-1.5 transition",
        active
          ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_32%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_8%,transparent)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]"
          : "border-transparent bg-transparent hover:border-[color:color-mix(in_oklab,var(--spirit-border)_45%,transparent)] hover:bg-white/[0.025]",
      )}
    >
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <div className="flex min-w-0 items-start gap-0.5">
          {handleDrag ? (
            <button
              type="button"
              {...dragHandleProps}
              disabled={interactionDisabled}
              aria-label={`Drag to reorder ${thread.title}`}
              className={cn(
                "mt-0.5 inline-flex min-h-[40px] min-w-[40px] shrink-0 touch-none items-center justify-center rounded-full border border-transparent bg-transparent text-chalk/30 transition active:scale-[0.98]",
                "hover:border-white/[0.06] hover:bg-white/[0.03] hover:text-chalk/45",
                dndDragging &&
                  "border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_8%,transparent)] text-[color:var(--spirit-accent-strong)] shadow-[0_0_16px_-4px_var(--spirit-glow)]",
              )}
              style={{ touchAction: "none" }}
            >
              <span
                className="grid grid-cols-3 gap-[2px] opacity-50"
                aria-hidden
              >
                {Array.from({ length: 6 }).map((_, i) => (
                  <span key={i} className="h-[2.5px] w-[2.5px] rounded-full bg-current" />
                ))}
              </span>
            </button>
          ) : null}
          <div
            {...(rowDrag ? dragActivatorProps : {})}
            className={cn(
              "min-w-0 flex-1 touch-manipulation rounded-md px-0.5 py-0.5 -mx-0.5",
              rowDrag &&
                "cursor-grab active:cursor-grabbing touch-pan-y",
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
                  "line-clamp-2 font-medium text-[12px] leading-snug text-chalk",
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
              <span className="mt-0.5 block truncate font-mono text-[9px] tracking-wide text-chalk/40">
                {updatedLabel}
              </span>
              {searchSnippet ? (
                <span className="mt-0.5 line-clamp-2 font-mono text-[8px] leading-snug text-chalk/48">
                  {searchSnippet}
                </span>
              ) : null}
            </button>
          </div>
          <div
            className={cn(
              "flex shrink-0 flex-row gap-0.5 transition-opacity",
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
                className="touch-manipulation rounded-md p-1.5 text-chalk/40 transition hover:bg-white/[0.05] hover:text-amber-100/85 disabled:opacity-30 active:scale-[0.98]"
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
              className="touch-manipulation rounded-md p-1.5 text-chalk/40 transition hover:bg-white/[0.05] hover:text-chalk/80 disabled:opacity-30 active:scale-[0.98]"
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
                  "touch-manipulation rounded-md p-1.5 text-chalk/40 transition hover:bg-white/[0.05] hover:text-chalk/80 disabled:opacity-30 active:scale-[0.98]",
                  moveOpen && "bg-white/[0.05] text-chalk/70",
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
              className="touch-manipulation rounded-md p-1.5 text-chalk/40 transition hover:bg-rose-500/12 hover:text-rose-200/90 disabled:opacity-30 active:scale-[0.98]"
            >
              <Trash2 className="h-3 w-3" aria-hidden />
            </button>
          </div>
        </div>
        {showMove && moveOpen ? (
          <div
            className="pl-0.5"
            onPointerDown={(e) => e.stopPropagation()}
          >
            <label className="flex flex-col gap-0.5">
              <span className="font-mono text-[8px] font-semibold uppercase tracking-[0.18em] text-chalk/40">
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
                  "w-full max-w-full cursor-pointer rounded border border-[color:color-mix(in_oklab,var(--spirit-border)_45%,transparent)] bg-black/25 px-1.5 py-1 font-mono text-[9px] uppercase tracking-wide text-chalk/55 outline-none transition",
                  "hover:border-[color:color-mix(in_oklab,var(--spirit-accent)_35%,transparent)] hover:text-chalk/75",
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
    </div>
  );
});
