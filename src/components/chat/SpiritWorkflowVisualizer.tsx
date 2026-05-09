"use client";

// ── SpiritWorkflowVisualizer - route + web proof rail (no chain-of-thought cosplay) ─
// > Extracted so SpiritChat stops being a 2k-line monolith. Still one product surface.

import { X } from "lucide-react";
import { memo, useMemo } from "react";

import { cn } from "@/lib/cn";

export type SpiritSearchStatusUi = "used" | "skipped" | "failed" | "disabled" | "none";

export type SpiritWorkflowVisualizerProps = {
  visible: boolean;
  /** Idle one-liner instead of the full stepper */
  compact?: boolean;
  completedSummary?: string;
  onExpand?: () => void;
  busy: boolean;
  lane?: string;
  confidence?: string;
  provider?: string;
  /** From x-spirit-search-status (normalized); preferred over raw web header. */
  searchStatus?: SpiritSearchStatusUi;
  searchKind?: "researcher" | "teacher" | "none";
  searchQuery?: string;
  searchElapsedMs?: number;
  skipReason?: string;
  searchUsed?: boolean;
  sourceCount?: number;
  sources?: Array<{
    title?: string;
    url?: string;
    snippet?: string;
  }>;
  steps: Array<{
    id: string;
    label: string;
    detail?: string;
    status: "pending" | "active" | "done" | "error";
  }>;
  onDismiss?: () => void;
};

function hostFromUrl(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

export const SpiritWorkflowVisualizer = memo(function SpiritWorkflowVisualizer({
  visible,
  compact = false,
  completedSummary,
  onExpand,
  busy,
  lane,
  confidence,
  provider,
  searchStatus = "none",
  searchKind = "none",
  searchQuery,
  searchElapsedMs,
  skipReason,
  searchUsed,
  sourceCount,
  sources,
  steps,
  onDismiss,
}: SpiritWorkflowVisualizerProps) {
  const activeLabel = useMemo(() => {
    const a = steps.find((s) => s.status === "active");
    return a?.label ?? steps.find((s) => s.status === "pending")?.label;
  }, [steps]);

  if (!visible) return null;

  if (compact && !busy) {
    return (
      <section
        data-testid="spirit-workflow-visualizer-compact"
        aria-busy={busy}
        className={cn(
          "relative z-20 shrink-0 border-b border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)]",
          "bg-[color:color-mix(in_oklab,var(--spirit-bg)_92%,black)] px-2 py-1.5 sm:px-3",
        )}
      >
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-2">
          <p
            data-testid="spirit-workflow-compact-summary"
            className="min-w-0 font-mono text-[10px] text-chalk/70 sm:text-[11px]"
          >
            {completedSummary ?? "Local answer complete"}
          </p>
          {onExpand ? (
            <button
              type="button"
              data-testid="spirit-workflow-expand"
              onClick={onExpand}
              className="shrink-0 rounded-md border border-[color:var(--spirit-border)]/70 px-2 py-0.5 font-mono text-[9px] uppercase tracking-wide text-chalk/60 hover:bg-white/[0.06]"
            >
              Expand
            </button>
          ) : null}
        </div>
      </section>
    );
  }

  const routeLine =
    lane === "openai-web-search" && searchKind === "teacher"
      ? "Teacher web aids (OpenAI)"
      : lane === "openai-web-search"
        ? "OpenAI web search"
        : lane === "research-plan"
          ? "Research plan"
          : lane === "local-chat"
            ? "Local chat"
            : lane ?? "Local chat";

  const searchProofLine = (() => {
    const prov = provider ? ` · Provider: ${provider}` : "";
    const q = searchQuery?.trim() ? ` · Query: ${searchQuery.trim().slice(0, 140)}` : "";
    const t =
      typeof searchElapsedMs === "number" && Number.isFinite(searchElapsedMs)
        ? ` · Time: ${(searchElapsedMs / 1000).toFixed(1)}s`
        : "";
    const n = typeof sourceCount === "number" ? ` · Sources: ${sourceCount}` : "";
    if (searchStatus === "used") return `Search: used${prov}${n}${q}${t}`;
    if (searchStatus === "skipped") return `Search: skipped${skipReason ? ` (${skipReason})` : ""}${q}`;
    if (searchStatus === "disabled") return `Search: skipped (disabled)${q}`;
    if (searchStatus === "failed") {
      const human =
        skipReason === "missing_openai_key"
          ? "missing API key"
          : skipReason
            ? skipReason.replace(/_/g, " ")
            : "provider error";
      return `Search: failed - ${human}${prov}${q}${t}`;
    }
    if (searchUsed) return `Search: used${prov}${n}${q}${t}`;
    return null;
  })();

  return (
    <section
      data-testid="spirit-workflow-visualizer"
      aria-busy={busy}
      className={cn(
        "relative z-20 max-h-[min(220px,38dvh)] overflow-y-auto overscroll-y-contain border-b border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)]",
        "bg-[color:color-mix(in_oklab,var(--spirit-bg)_92%,black)] px-2 py-2 shadow-[inset_0_-1px_0_rgba(255,255,255,0.03)] sm:px-3 sm:py-2.5",
        "max-lg:text-[11px]",
      )}
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-1.5">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-chalk/50">
              {busy ? "Spirit is working" : "Spirit status"}
            </p>
            <p
              data-testid="spirit-workflow-route-line"
              className="mt-0.5 font-mono text-[11px] text-[color:var(--spirit-accent-strong)]/95 sm:text-xs"
            >
              Route: {routeLine}
              {confidence ? (
                <span className="text-chalk/45"> · confidence {confidence}</span>
              ) : null}
            </p>
            {busy && activeLabel ? (
              <p className="mt-0.5 font-mono text-[10px] text-chalk/70 sm:text-[11px]">{activeLabel}</p>
            ) : null}
            {searchProofLine ? (
              <p
                data-testid="spirit-workflow-search-proof"
                className="mt-0.5 font-mono text-[10px] text-chalk/65 sm:text-[11px]"
              >
                {searchProofLine}
              </p>
            ) : null}
            <p
              data-testid="spirit-workflow-no-cot"
              className="mt-1 font-mono text-[9px] leading-snug text-chalk/40 sm:text-[10px]"
            >
              No private chain-of-thought. High-level status only.
            </p>
          </div>
          {onDismiss ? (
            <button
              type="button"
              aria-label="Dismiss workflow panel"
              data-testid="spirit-workflow-dismiss"
              onClick={onDismiss}
              className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-[color:var(--spirit-border)]/70 text-chalk/55 hover:bg-white/[0.06] hover:text-chalk"
            >
              <X className="h-3.5 w-3.5" aria-hidden />
            </button>
          ) : null}
        </div>
        <ol className="sr-only" aria-hidden>
          {steps.map((s) => (
            <li key={s.id}>
              {s.label} {s.status}
            </li>
          ))}
        </ol>
        {sources && sources.length > 0 ? (
          <ul
            data-testid="spirit-workflow-source-cards"
            className="mt-1 grid gap-1.5 sm:grid-cols-2"
          >
            {sources.map((s, i) => {
              const url = s.url?.trim();
              const title = (s.title?.trim() || url || "Source").slice(0, 200);
              const domain = url ? hostFromUrl(url) : "";
              const sn = s.snippet?.trim().slice(0, 140);
              return (
                <li key={`${url ?? title}-${i}`}>
                  {url ? (
                    <a
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/25 px-2 py-1.5 transition hover:border-[color:color-mix(in_oklab,var(--spirit-accent)_40%,transparent)]"
                    >
                      <p className="font-mono text-[10px] font-semibold text-chalk">{title}</p>
                      {domain ? (
                        <p className="mt-0.5 font-mono text-[9px] text-[color:var(--spirit-accent-strong)]/85">
                          {domain}
                        </p>
                      ) : null}
                      {sn ? <p className="mt-1 font-mono text-[9px] leading-snug text-chalk/55">{sn}</p> : null}
                    </a>
                  ) : (
                    <div className="rounded-lg border border-white/[0.06] bg-black/20 px-2 py-1.5 font-mono text-[9px] text-chalk/50">
                      {title}
                      <span className="mt-1 block text-chalk/40">No URL - not clickable</span>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        ) : null}
      </div>
    </section>
  );
});
