"use client";

// ── ChatThreadDragOverlay - ghost card under cursor (oldSpiritOS ThreadDragOverlay) ─
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
        "flex w-[min(232px,72vw)] max-w-[240px] items-center rounded-xl px-3 py-2.5",
        "border border-[color:color-mix(in_oklab,var(--spirit-accent-strong)_38%,transparent)]",
        "bg-[color:color-mix(in_oklab,var(--spirit-bg)_94%,transparent)]",
        "shadow-[0_8px_32px_-8px_var(--spirit-glow)] backdrop-blur-md",
        "cursor-grabbing",
      )}
    >
      <div className="min-w-0 flex-1">
        <p className="truncate text-[12px] font-medium text-chalk">{thread.title}</p>
        <p className="mt-0.5 truncate font-mono text-[10px] text-chalk/45">
          Moving thread…
        </p>
      </div>
    </div>
  );
});
