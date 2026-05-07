"use client";

// ── MobileChatTopBar - Gemini-style strip: menu · title · actions (Prompt 9E-A rev) ─
// > Extracted from: spiritos-chat-demo.zip (visual hierarchy only)
// > Design language: calm surfaces, no stacked dashboard decks in one row
import { memo, type ReactNode } from "react";

import { cn } from "@/lib/cn";

export type MobileChatTopBarProps = {
  threadsSlot: ReactNode;
  /** Center title (thread name, “Spirit”, etc.) — truncate handled by slot. */
  titleSlot: ReactNode;
  /** Right cluster: new chat, overflow, voice, etc. */
  endSlot: ReactNode;
  className?: string;
};

export const MobileChatTopBar = memo(function MobileChatTopBar({
  threadsSlot,
  titleSlot,
  endSlot,
  className,
}: MobileChatTopBarProps) {
  return (
    <header
      className={cn(
        "flex min-h-[48px] shrink-0 items-center gap-2 overflow-hidden border-b border-[color:color-mix(in_oklab,var(--spirit-border)_38%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_96%,transparent)] px-2.5 py-1 backdrop-blur-md",
        className,
      )}
    >
      <div className="shrink-0">{threadsSlot}</div>
      <div className="min-w-0 flex-1 overflow-hidden px-0.5">{titleSlot}</div>
      <div className="flex shrink-0 items-center justify-end gap-1">{endSlot}</div>
    </header>
  );
});
