// ─── Spirit OS · SortableThreadItem ──────────────────────────────────────────
//
// Wraps ThreadItem with @dnd-kit/sortable mechanics.
//
// Separation of concerns:
//   ThreadItem   — owns all CRUD UI state (rename/delete/menu) + display logic
//   SortableThreadItem — owns all drag-and-drop mechanics
//
// This split means ThreadItem's internal state machine never gets remounted
// during a drag operation. If we put useSortable inside ThreadItem directly,
// the component would remount on every SortableContext items array change,
// resetting any open rename/menu states.
//
// The dragHandleProps spread:
//   ThreadItem's idle-state root <div> accepts `dragHandleProps` and spreads
//   them directly. This means the ENTIRE idle row is the drag handle —
//   intentional, because a small dedicated handle on an 11px text row would
//   be unclickably small on mobile.
//
// When dragging (isDragging):
//   The original position renders a transparent placeholder (opacity-0) so
//   the list layout doesn't collapse while the DragOverlay is airborne.
//
// ─────────────────────────────────────────────────────────────────────────────

"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ThreadItem, type ThreadItemProps } from "./ThreadItem";

// Re-export so callers only need to import from this file.
export type { ThreadItemProps };

export function SortableThreadItem(props: ThreadItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: props.thread.id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? undefined,
    // Keep the layout slot visible but invisible while the DragOverlay flies.
    opacity: isDragging ? 0 : 1,
  };

  return (
    <div ref={setNodeRef} style={style}>
      <ThreadItem
        {...props}
        // Spread listeners + attributes as dragHandleProps so ThreadItem's
        // idle root <div> becomes the drag initiator.
        dragHandleProps={{ ...listeners, ...attributes }}
      />
    </div>
  );
}
