"use client";

// ── ChatSidebarDndProvider - @dnd-kit shell; drawer uses longer touch delay (9F) ─
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragCancelEvent,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { memo, useCallback } from "react";

import { ChatThreadDragOverlay } from "@/components/chat/ChatThreadDragOverlay";
import { chatSidebarThreadCollisionDetection } from "@/lib/chat-sidebar-dnd";
import type { ChatThread } from "@/lib/chat-db.types";

export type TouchActivationOptions = {
  delay: number;
  tolerance: number;
};

/** PointerSensor `activationConstraint` — higher `distance` = fewer accidental drags + less post-drag doc click-capture (dnd-kit detaches listeners on a 50ms timer). */
export type PointerActivationOptions = {
  distance: number;
};

export type ChatSidebarDndProviderProps = {
  overlayThread: ChatThread | null;
  onDragStart?: (event: DragStartEvent) => void;
  onDragOver?: (event: DragOverEvent) => void;
  onDragEnd: (event: DragEndEvent) => void;
  /** dnd-kit fires this on Escape / sensor cancel — NOT `onDragEnd`. Clear overlay chrome here. */
  onDragCancel?: (event: DragCancelEvent) => void;
  children: React.ReactNode;
  /** Drawer vs desktop rail - tune iOS long-press vs scroll. */
  touchActivation?: TouchActivationOptions;
  /** Desktop rail: looser than drawer so trackpad jitter does not arm drag (and its ghost-click guard) as often. */
  pointerActivation?: PointerActivationOptions;
};

export const ChatSidebarDndProvider = memo(function ChatSidebarDndProvider({
  overlayThread,
  onDragStart,
  onDragOver,
  onDragEnd,
  onDragCancel,
  children,
  touchActivation = { delay: 150, tolerance: 6 },
  pointerActivation = { distance: 12 },
}: ChatSidebarDndProviderProps) {
  // PointerSensor arms a capture-phase document `click` stopper after activation; `detach()` clears
  // document listeners on a 50ms timer — looser `distance` on desktop reduces accidental arms.
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: pointerActivation.distance },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: touchActivation.delay,
        tolerance: touchActivation.tolerance,
      },
    }),
    useSensor(KeyboardSensor),
  );

  const handleEnd = useCallback(
    (e: DragEndEvent) => {
      onDragEnd(e);
    },
    [onDragEnd],
  );

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={chatSidebarThreadCollisionDetection}
      // Auto-scroll + animated sortable siblings = rects slide under a static pointer → pointerWithin
      // alternates targets (Spirit debug log: rapid overId flips while dragging down in Recent).
      autoScroll={false}
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDragEnd={handleEnd}
      onDragCancel={onDragCancel}
    >
      {children}
      <DragOverlay zIndex={10050} dropAnimation={null}>
        {overlayThread ? <ChatThreadDragOverlay thread={overlayThread} /> : null}
      </DragOverlay>
    </DndContext>
  );
});
