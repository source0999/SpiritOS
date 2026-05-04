"use client";

// ── SpiritDashboardHome — "/" command surface; GPT transcript lives only on /chat ──
import Link from "next/link";

import { Clock } from "@/components/dashboard/Clock";
import { DashboardWidgetCard } from "@/components/dashboard/DashboardWidgetCard";
import { ThemeStrip } from "@/components/dashboard/ThemeStrip";
import { DiagnosticsPanel } from "@/components/dashboard/DiagnosticsPanel";
import { WorkspaceDiagnosticsRail } from "@/components/dashboard/WorkspaceDiagnosticsRail";
import { WorkspacePrimarySidebar } from "@/components/dashboard/WorkspacePrimarySidebar";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import { cn } from "@/lib/cn";

function SpiritDashboardHomeInner() {
  const cta =
    "inline-flex touch-manipulation items-center justify-center rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_14%,transparent)] px-4 py-2 font-mono text-[11px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)] transition hover:brightness-110 active:scale-[0.98]";

  return (
    <div
      data-layout="spirit-dashboard-home"
      className="relative flex h-[100dvh] w-full overflow-hidden bg-[color:var(--spirit-bg)] text-chalk"
    >
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[color:var(--spirit-bg)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(ellipse_110%_75%_at_50%_-8%,color-mix(in_oklab,var(--spirit-accent)_14%,transparent),transparent_55%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-[0.18] [background-image:linear-gradient(rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px)] [background-size:52px_52px]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_50%_115%,rgba(0,0,0,0.4),transparent_52%)]"
        aria-hidden
      />

      <WorkspacePrimarySidebar />

      <div
        className={cn(
          "relative z-10 flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden",
          "pb-[calc(4.25rem+env(safe-area-inset-bottom,0px))] lg:pb-0",
        )}
      >
        <header className="shrink-0 border-b border-[color:var(--spirit-border)] bg-white/[0.03] backdrop-blur-xl">
          <div className="flex items-center gap-4 px-4 py-2.5 sm:px-6">
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-base font-semibold tracking-tight text-chalk sm:text-lg">
                Spirit OS
              </h1>
              <p className="truncate font-mono text-[10px] leading-snug text-chalk/48 sm:text-[11px]">
                Command surface · dashboards + lanes
              </p>
            </div>
            <div className="flex min-w-0 shrink-0 flex-wrap items-center justify-end gap-2 sm:gap-3">
              <ThemeStrip />
              <Clock />
            </div>
          </div>
        </header>

        <div className="flex min-h-0 flex-1 flex-row overflow-hidden">
          <main className="scrollbar-hide min-h-0 flex-1 overflow-y-auto px-3 pb-8 pt-4 sm:px-5 lg:pr-5">
            <div className="mx-auto grid max-w-6xl gap-4 sm:grid-cols-2 xl:grid-cols-12">
              <DashboardWidgetCard
                title="Quick Chat Core"
                subtitle="Saved threads, hydration, Dexie transcripts — canonical home is /chat."
                className="sm:col-span-2 xl:col-span-5"
              >
                <Link href="/chat" className={cta}>
                  Open chat
                </Link>
              </DashboardWidgetCard>

              <DashboardWidgetCard
                title="Quarantine Lab"
                subtitle="Voice and containment experiments · Oracle-adjacent noise stays here."
                className="sm:col-span-2 xl:col-span-5"
              >
                <Link href="/quarantine" className={cta}>
                  Open quarantine
                </Link>
              </DashboardWidgetCard>

              <DashboardWidgetCard
                title="Systems build queue"
                subtitle="Folders, drag sorting, and voice pipes are queued — no phantom green bars pretending otherwise."
                className="sm:col-span-2 xl:col-span-6"
              />

              <DashboardWidgetCard
                title="Project uplink"
                subtitle="Honest standby: scanner + fleet mesh routing is future work."
                className="sm:col-span-2 xl:col-span-6"
              />

              <div className="sm:col-span-2 xl:col-span-12 lg:hidden">
                <DiagnosticsPanel docked />
              </div>
            </div>
          </main>

          <WorkspaceDiagnosticsRail />
        </div>
      </div>
    </div>
  );
}

export default function SpiritDashboardHome() {
  return (
    <ClientFailSafe label="spirit-dashboard-home">
      <SpiritDashboardHomeInner />
    </ClientFailSafe>
  );
}
