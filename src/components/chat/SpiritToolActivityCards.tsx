// ── SpiritToolActivityCards - compact Hermes / local tool telemetry (Phase 7) ─
"use client";

import { memo } from "react";

import { cn } from "@/lib/cn";
import type { SpiritToolActivityCard } from "@/lib/spirit/spirit-activity-events";

import { statusLabel } from "@/lib/spirit/spirit-assistant-tool-activity";

function statusPillClass(status: SpiritToolActivityCard["status"]): string {
  switch (status) {
    case "completed":
      return "border-emerald-500/35 text-emerald-200/90";
    case "failed":
      return "border-rose-500/40 text-rose-200/90";
    case "blocked":
      return "border-amber-500/40 text-amber-200/90";
    case "confirmation_required":
      return "border-cyan-500/40 text-cyan-200/90";
    case "pending":
    default:
      return "border-chalk/20 text-chalk/75";
  }
}

export const SpiritToolActivityCards = memo(function SpiritToolActivityCards({
  cards,
  className,
}: {
  cards: SpiritToolActivityCard[];
  className?: string;
}) {
  if (cards.length === 0) return null;

  return (
    <div
      data-testid="spirit-tool-activity-cards"
      className={cn("mt-2 space-y-1.5 pl-0.5", className)}
      aria-label="Tool activity"
    >
      {cards.map((c) => (
        <div
          key={c.id}
          data-testid={`spirit-tool-activity-card-${c.kind}`}
          className="rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/25 px-2.5 py-2 font-mono text-[10px] leading-snug text-chalk/80"
        >
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <span className="font-semibold text-chalk/92">{c.label}</span>
            <span
              className={cn(
                "rounded border px-1.5 py-px text-[9px] uppercase tracking-wide",
                statusPillClass(c.status),
              )}
            >
              {statusLabel(c.status)}
            </span>
          </div>
          {c.target ? (
            <p className="mt-1 text-chalk/70">
              <span className="text-chalk/45">Target · </span>
              {c.target}
            </p>
          ) : null}
          {c.summary ? (
            <p className="mt-0.5 text-chalk/65">
              <span className="text-chalk/45">Summary · </span>
              {c.summary}
            </p>
          ) : null}
          {c.safeMessage ? (
            <p className="mt-0.5 text-amber-200/75">
              <span className="text-chalk/45">Reason · </span>
              {c.safeMessage}
            </p>
          ) : null}
        </div>
      ))}
    </div>
  );
});
