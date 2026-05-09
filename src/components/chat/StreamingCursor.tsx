"use client";

// ── StreamingCursor - cyan blink on the tail of the in-flight assistant bubble ──
import { memo } from "react";

import { cn } from "@/lib/cn";

export type StreamingCursorProps = {
  className?: string;
};

export const StreamingCursor = memo(function StreamingCursor({
  className,
}: StreamingCursorProps) {
  return (
    <span
      aria-hidden
      className={cn(
        "ml-0.5 inline-block h-[0.65em] w-[0.35em] translate-y-px rounded-sm",
        "bg-[color:var(--spirit-accent-strong)] shadow-[0_0_10px_var(--spirit-glow)]",
        "animate-pulse align-baseline",
        className,
      )}
    />
  );
});
