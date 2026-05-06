"use client";

// ── ChatActiveModeBadge - always know which mode is eating your tokens ─────────
import { memo } from "react";

import { getModelProfile } from "@/lib/spirit/model-profiles";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { cn } from "@/lib/cn";

const toneClass: Record<string, string> = {
  neutral: "border-chalk/20 bg-white/[0.04] text-chalk/85",
  cyan: "border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_10%,transparent)] text-chalk",
  amber: "border-amber-400/35 bg-amber-500/10 text-amber-100/95",
  rose: "border-rose-400/35 bg-rose-500/10 text-rose-100/95",
  violet: "border-violet-400/35 bg-violet-500/10 text-violet-100/95",
};

export type ChatActiveModeBadgeProps = {
  profileId: ModelProfileId;
  className?: string;
  /** Single-line / tighter for mobile sub-bar */
  compact?: boolean;
};

export const ChatActiveModeBadge = memo(function ChatActiveModeBadge({
  profileId,
  className,
  compact = false,
}: ChatActiveModeBadgeProps) {
  const p = getModelProfile(profileId);
  const tone = p.badgeTone ?? "neutral";
  return (
    <div
      className={cn(
        "min-w-0 rounded-lg border px-2 py-1 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]",
        toneClass[tone] ?? toneClass.neutral,
        compact && "max-w-full py-0.5",
        className,
      )}
      title={`${p.label} - ${p.responseStyleSummary}`}
    >
      <p className="truncate font-mono text-[9px] font-semibold uppercase tracking-[0.16em] text-chalk/50">
        Mode: {p.shortLabel}
      </p>
      {!compact ? (
        <p className="truncate font-mono text-[10px] leading-snug text-chalk/70">
          {p.responseStyleSummary}
        </p>
      ) : (
        <p className="truncate font-mono text-[9px] leading-snug text-chalk/60">
          {p.responseStyleSummary}
        </p>
      )}
    </div>
  );
});
