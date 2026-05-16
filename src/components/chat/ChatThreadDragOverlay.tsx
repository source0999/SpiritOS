"use client";

// ── ChatThreadDragOverlay - cursor follower; must read like the rail row, not a modal ──
import { memo } from "react";

import type { ChatThread } from "@/lib/chat-db.types";
import { cn } from "@/lib/cn";

export type ChatThreadDragOverlayProps = {
  thread: ChatThread;
};

export const ChatThreadDragOverlay = memo(function ChatThreadDragOverlay({
  thread,
}: ChatThreadDragOverlayProps) {
  return (
    <div
      className={cn(
        "pointer-events-none z-[10050] flex w-[var(--chat-thread-rail-width,260px)] max-w-[min(260px,calc(100vw-16px))] min-w-0 cursor-grabbing items-center gap-1.5 rounded-md border px-2 py-1",
        "border-[color:color-mix(in_oklab,var(--spirit-border)_45%,transparent)]",
        "bg-[color:color-mix(in_oklab,var(--spirit-bg)_88%,transparent)]",
      )}
    >
      <span
        className="h-8 w-0.5 shrink-0 rounded-full bg-[color:color-mix(in_oklab,var(--spirit-accent-strong)_28%,transparent)]"
        aria-hidden
      />
      <p className="min-w-0 flex-1 truncate text-left text-[12px] font-medium leading-tight text-chalk/90">
        {thread.title}
      </p>
    </div>
  );
});
