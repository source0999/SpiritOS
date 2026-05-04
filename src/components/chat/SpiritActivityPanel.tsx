"use client";

// ── SpiritActivityPanel — high-level signals only (no chain-of-thought) ─────────
import { Activity, X } from "lucide-react";
import { memo } from "react";

import type { SpiritActivityEvent } from "@/lib/spirit/spirit-activity-events";
import { cn } from "@/lib/cn";

export type SpiritActivityPanelProps = {
  open: boolean;
  onClose: () => void;
  /** Mobile = bottom sheet */
  variant: "popover" | "sheet";
  /** Optional extra classes on the anchored panel surface */
  anchorClassName?: string;
  modeLabel: string;
  runtimeLabel: string;
  voiceLabel: string;
  searchLabel: string;
  memoryLabel: string;
  researchNote: string;
  /** Optional lines for /api/spirit web search diagnostics (no secrets). */
  webSearchDiagnosticLines?: string[];
  events: SpiritActivityEvent[];
};

function kindLabel(k: SpiritActivityEvent["kind"]): string {
  switch (k) {
    case "message_submitted":
      return "msg";
    case "assistant_finished":
      return "done";
    case "mode_changed":
      return "mode";
    case "voice_played":
      return "tts";
    case "voice_error":
      return "err";
    case "workflow_step":
      return "flow";
    case "copy_feedback":
      return "cpy";
    default:
      return "evt";
  }
}

export const SpiritActivityPanel = memo(function SpiritActivityPanel({
  open,
  onClose,
  variant,
  modeLabel,
  runtimeLabel,
  voiceLabel,
  searchLabel,
  memoryLabel,
  researchNote,
  webSearchDiagnosticLines,
  events,
  anchorClassName = "",
}: SpiritActivityPanelProps) {
  if (!open) return null;

  const sheet = variant === "sheet";

  return (
    <>
      <button
        type="button"
        aria-label="Close activity panel"
        className={cn("fixed inset-0 z-[140] bg-black/55 backdrop-blur-[2px]", !sheet && "lg:bg-black/40")}
        onClick={onClose}
      />
      <div
        className={cn(
          "fixed z-[150] flex max-h-[min(520px,82dvh)] w-[min(100vw-1.5rem,22rem)] flex-col overflow-hidden rounded-xl border border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_94%,black)] shadow-[0_24px_80px_-24px_rgba(0,0,0,0.75)]",
          sheet
            ? "inset-x-0 bottom-0 mx-auto max-h-[70dvh] w-full max-w-lg rounded-b-none rounded-t-2xl border-b-0 pb-[env(safe-area-inset-bottom,0px)]"
            : "right-3 top-[3.25rem] max-lg:right-2 max-lg:top-[6.5rem]",
          anchorClassName,
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="spirit-activity-heading"
      >
        <div className="flex items-center justify-between gap-2 border-b border-[color:var(--spirit-border)] px-3 py-2">
          <div className="flex min-w-0 items-center gap-2">
            <Activity className="h-4 w-4 shrink-0 text-[color:var(--spirit-accent-strong)]" aria-hidden />
            <h2 id="spirit-activity-heading" className="truncate font-mono text-[11px] font-semibold uppercase tracking-wider text-chalk">
              Activity
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-transparent text-chalk/60 transition hover:bg-white/[0.06] hover:text-chalk"
            aria-label="Close"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
        <div className="scrollbar-hide min-h-0 flex-1 space-y-2 overflow-y-auto px-3 py-2">
          <ul className="space-y-1.5 font-mono text-[10px] leading-relaxed text-chalk/75">
            <li>
              <span className="text-chalk/45">Mode · </span>
              {modeLabel}
            </li>
            <li>
              <span className="text-chalk/45">Runtime · </span>
              {runtimeLabel}
            </li>
            <li>
              <span className="text-chalk/45">Voice · </span>
              {voiceLabel}
            </li>
            <li>
              <span className="text-chalk/45">Search · </span>
              {searchLabel}
            </li>
            <li>
              <span className="text-chalk/45">Memory · </span>
              {memoryLabel}
            </li>
            <li>
              <span className="text-chalk/45">Research tools · </span>
              {researchNote}
            </li>
          </ul>
          {webSearchDiagnosticLines && webSearchDiagnosticLines.length > 0 ? (
            <div
              data-testid="spirit-web-search-diagnostics"
              className="rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] bg-black/20 px-2 py-1.5"
            >
              <p className="font-mono text-[9px] font-semibold uppercase tracking-wider text-chalk/40">
                Web search diagnostics
              </p>
              <ul className="mt-1 space-y-0.5 font-mono text-[10px] leading-relaxed text-chalk/70">
                {webSearchDiagnosticLines.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className="border-t border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] pt-2">
            <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.18em] text-chalk/40">
              Recent events
            </p>
            {events.length === 0 ? (
              <p className="mt-1 font-mono text-[10px] text-chalk/45">No events yet this session.</p>
            ) : (
              <ol className="mt-1 space-y-1">
                {events
                  .slice()
                  .reverse()
                  .map((e) => (
                    <li
                      key={e.id}
                      className="flex gap-2 font-mono text-[10px] text-chalk/70"
                    >
                      <span className="shrink-0 text-chalk/35">{kindLabel(e.kind)}</span>
                      <span className="min-w-0 flex-1 break-words">{e.label}</span>
                    </li>
                  ))}
              </ol>
            )}
          </div>
        </div>
      </div>
    </>
  );
});
