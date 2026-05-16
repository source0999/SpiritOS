"use client";

// ── SortableChatThreadItem - dnd-kit; drawer can use handle-only activator (9F) ──
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { DraggableAttributes, DraggableSyntheticListeners } from "@dnd-kit/core";
import { memo, type CSSProperties, type ReactNode } from "react";

import { THREAD_DND_PREFIX } from "@/lib/chat-sidebar-dnd";

/** Tight sidebar: long transitions read as laggy index shifts. */
const SORTABLE_LAYOUT_EASING = "cubic-bezier(0.2, 0, 0, 1)";
const SORTABLE_LAYOUT_MS = 115;

export type DragActivatorProps = DraggableAttributes & DraggableSyntheticListeners;

export type SortableChatThreadItemProps = {
  threadId: string;
  disabled?: boolean;
  /** Mobile drawer: put drag listeners on handle only so list scrolls normally. */
  useDragHandle?: boolean;
  children: (p: {
    dragActivatorProps: DragActivatorProps;
    dragHandleProps?: DragActivatorProps;
    /** Same node as `listeners` — required for handle / detached activator patterns (dnd-kit PR #748). */
    setDragActivatorRef: (element: HTMLElement | null) => void;
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
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id,
    disabled,
    // Live layout transitions while `over` thrashes = droppableRects dance under the pointer.
    // Runtime: debug log still flipped 3228658b ↔ 51bd47ce after vertical-midpoint pick (eafb6b L217–228).
    animateLayoutChanges: () => false,
    transition: {
      duration: SORTABLE_LAYOUT_MS,
      easing: SORTABLE_LAYOUT_EASING,
    },
  });

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? undefined,
    opacity: isDragging ? 0.5 : 1,
    // Invisible source row still hit-tests by default → blocks pointerWithin on targets below; kills snap/drop.
    pointerEvents: isDragging ? "none" : undefined,
    willChange: transform ? "transform" : undefined,
  };

  // ── attributes on the sortable node, listeners ONLY on the activator (bubble / row / grip).
  //    Merging both onto the title row used to park tabIndex on inner controls and eat first clicks.
  const dragListenersOnly = listeners as unknown as DragActivatorProps;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="min-w-0"
      {...attributes}
      // dnd-kit defaults attributes.role="button" + tabIndex=0 on the draggable node — fine for a
      // single-handle chip, lethal next to real <button> titles (first click focuses this div).
      role="group"
      tabIndex={-1}
    >
      {useDragHandle
        ? children({
            dragActivatorProps: {} as DragActivatorProps,
            dragHandleProps: dragListenersOnly,
            setDragActivatorRef: setActivatorNodeRef,
            isDragging,
          })
        : children({
            dragActivatorProps: dragListenersOnly,
            dragHandleProps: undefined,
            setDragActivatorRef: setActivatorNodeRef,
            isDragging,
          })}
    </div>
  );
});
