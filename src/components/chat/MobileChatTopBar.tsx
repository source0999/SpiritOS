"use client";

// ── MobileChatTopBar - 48px strip; conversation stays visible (Prompt 9E-A) ───────
import { memo, type ReactNode } from "react";

import { cn } from "@/lib/cn";

export type MobileChatTopBarProps = {
  threadsSlot: ReactNode;
  modeSlot: ReactNode;
  voiceSlot: ReactNode;
  /** Tiny wordmark so the bar still reads “Spirit” without stealing width. */
  showSpiritMark?: boolean;
  className?: string;
};

export const MobileChatTopBar = memo(function MobileChatTopBar({
  threadsSlot,
  modeSlot,
  voiceSlot,
  showSpiritMark = true,
  className,
}: MobileChatTopBarProps) {
  return (
    <header
      className={cn(
        "flex min-h-[44px] shrink-0 items-center gap-1 overflow-hidden border-b border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_94%,transparent)] px-2 py-1 backdrop-blur-md",
        className,
      )}
    >
      <div className="shrink-0">{threadsSlot}</div>
      <div className="min-w-0 flex-1 overflow-hidden">{modeSlot}</div>
      {showSpiritMark ? (
        <span className="max-[380px]:sr-only shrink-0 font-mono text-[8px] font-semibold uppercase tracking-[0.2em] text-chalk/35">
          Spirit
        </span>
      ) : null}
      <div className="shrink-0">{voiceSlot}</div>
    </header>
  );
});
