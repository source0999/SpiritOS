"use client";

// ── ChatSidebarDndProvider — @dnd-kit shell; drawer uses longer touch delay (9F) ─
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
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

export type ChatSidebarDndProviderProps = {
  overlayThread: ChatThread | null;
  onDragStart?: (event: DragStartEvent) => void;
  onDragOver?: (event: DragOverEvent) => void;
  onDragEnd: (event: DragEndEvent) => void;
  children: React.ReactNode;
  /** Drawer vs desktop rail — tune iOS long-press vs scroll. */
  touchActivation?: TouchActivationOptions;
};

export const ChatSidebarDndProvider = memo(function ChatSidebarDndProvider({
  overlayThread,
  onDragStart,
  onDragOver,
  onDragEnd,
  children,
  touchActivation = { delay: 150, tolerance: 6 },
}: ChatSidebarDndProviderProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
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
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDragEnd={handleEnd}
    >
      {children}
      <DragOverlay dropAnimation={{ duration: 150, easing: "ease" }}>
        {overlayThread ? <ChatThreadDragOverlay thread={overlayThread} /> : null}
      </DragOverlay>
    </DndContext>
  );
});
