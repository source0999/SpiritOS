"use client";

// ── SpiritWorkspaceShell - `/chat` GPT workspace (+ diagnostics rail, locked viewport) ─
// DEPRECATED CONTEXT: DashboardClient StageId rails are archival only; Neural has no throne.
import { useState } from "react";
import { PanelLeftClose, PanelLeft } from "lucide-react";

import { SpiritChat } from "@/components/chat/SpiritChat";
import { Clock } from "@/components/dashboard/Clock";
import { ThemeStrip } from "@/components/dashboard/ThemeStrip";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import { WorkspaceDiagnosticsRail } from "@/components/dashboard/WorkspaceDiagnosticsRail";
import { WorkspacePrimarySidebar } from "@/components/dashboard/WorkspacePrimarySidebar";
import { cn } from "@/lib/cn";

export type SpiritWorkspaceShellProps = {
  chatTitle?: string;
  chatSubtitle?: string;
};

function SpiritWorkspaceShellInner({
  chatTitle = "Neural // Spirit",
  chatSubtitle = "/api/spirit · Dark Node surface",
}: SpiritWorkspaceShellProps) {
  const [threadsRailOpen, setThreadsRailOpen] = useState(false);

  return (
    <div
      data-layout="spirit-workspace"
      className="relative flex h-[100dvh] w-full overflow-hidden bg-[color:var(--spirit-bg)] text-chalk"
      style={{ transition: "background-color 320ms ease" }}
    >
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[color:var(--spirit-bg)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(ellipse_110%_75%_at_50%_-8%,color-mix(in_oklab,var(--spirit-accent)_16%,transparent),transparent_55%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-[0.2] [background-image:linear-gradient(rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px)] [background-size:52px_52px]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_50%_115%,rgba(0,0,0,0.42),transparent_52%)]"
        aria-hidden
      />

      <WorkspacePrimarySidebar />

      <div
        className={cn(
          "relative z-10 flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden",
          "pb-[calc(4.25rem+env(safe-area-inset-bottom,0px))] lg:pb-0",
        )}
      >
        <header className="hidden shrink-0 border-b border-[color:var(--spirit-border)] bg-white/[0.03] backdrop-blur-xl lg:flex">
          <div className="flex items-center gap-3 px-4 py-2 sm:px-5">
            <button
              type="button"
              aria-label={
                threadsRailOpen ? "Close saved threads" : "Open saved threads"
              }
              aria-expanded={threadsRailOpen}
              onClick={() => setThreadsRailOpen((o) => !o)}
              className={cn(
                "inline-flex min-h-[44px] shrink-0 touch-manipulation items-center justify-center gap-1.5 rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] px-2.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-chalk transition hover:bg-white/[0.07] lg:hidden",
                threadsRailOpen &&
                  "border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] text-[color:var(--spirit-accent-strong)]",
              )}
            >
              {threadsRailOpen ? (
                <PanelLeftClose className="h-5 w-5 shrink-0" aria-hidden />
              ) : (
                <PanelLeft className="h-5 w-5 shrink-0" aria-hidden />
              )}
              <span className="max-[380px]:sr-only">Threads</span>
            </button>

            <div className="min-w-0 flex-1">
              <h1 className="truncate text-sm font-semibold tracking-tight text-chalk sm:text-base lg:text-lg">
                Spirit OS · Chat
              </h1>
              <p className="hidden truncate font-mono text-[10px] leading-snug text-chalk/50 sm:block sm:text-[11px] lg:inline">
                Saved threads · Dexie · /api/spirit
              </p>
            </div>

            <div className="flex min-w-0 shrink-0 flex-wrap items-center justify-end gap-2 sm:gap-3">
              <div className="hidden lg:block">
                <ThemeStrip />
              </div>
              <Clock />
            </div>
          </div>
        </header>

        <div className="flex min-h-0 flex-1 flex-row overflow-hidden">
          <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden lg:pl-1 lg:pt-1 lg:pr-0">
            <SpiritChat
              persistence
              variant="workspace"
              showThreadSidebar
              title={chatTitle}
              subtitle={chatSubtitle}
              shellClassName="flex h-full min-h-0 flex-1 flex-col overflow-hidden"
              mobileThreadRail={{
                open: threadsRailOpen,
                onOpenChange: setThreadsRailOpen,
              }}
            />
          </div>

          <WorkspaceDiagnosticsRail />
        </div>
      </div>
    </div>
  );
}

export default function SpiritWorkspaceShell(props: SpiritWorkspaceShellProps) {
  return (
    <ClientFailSafe label="spirit-workspace">
      <SpiritWorkspaceShellInner {...props} />
    </ClientFailSafe>
  );
}
