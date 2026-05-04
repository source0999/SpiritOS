"use client";

// ── SortableChatThreadItem — dnd-kit; drawer can use handle-only activator (9F) ──
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { DraggableAttributes, DraggableSyntheticListeners } from "@dnd-kit/core";
import { memo, type CSSProperties, type ReactNode } from "react";

import { THREAD_DND_PREFIX } from "@/lib/chat-sidebar-dnd";

export type DragActivatorProps = DraggableAttributes & DraggableSyntheticListeners;

export type SortableChatThreadItemProps = {
  threadId: string;
  disabled?: boolean;
  /** Mobile drawer: put drag listeners on handle only so list scrolls normally. */
  useDragHandle?: boolean;
  children: (p: {
    dragActivatorProps: DragActivatorProps;
    dragHandleProps?: DragActivatorProps;
    isDragging: boolean;
  }) => ReactNode;
};

export const SortableChatThreadItem = memo(function SortableChatThreadItem({
  threadId,
  disabled = false,
  useDragHandle = false,
  children,
}: SortableChatThreadItemProps) {
  const id = `${THREAD_DND_PREFIX}${threadId}`;
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id, disabled });

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? undefined,
    opacity: isDragging ? 0 : 1,
  };

  const merged = { ...attributes, ...listeners } as DragActivatorProps;

  return (
    <div ref={setNodeRef} style={style} className="min-w-0">
      {useDragHandle
        ? children({
            dragActivatorProps: {} as DragActivatorProps,
            dragHandleProps: merged,
            isDragging,
          })
        : children({
            dragActivatorProps: merged,
            dragHandleProps: undefined,
            isDragging,
          })}
    </div>
  );
});
