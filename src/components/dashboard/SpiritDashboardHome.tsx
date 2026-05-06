"use client";

import { Clock } from "@/components/dashboard/Clock";
import { ThemeStrip } from "@/components/dashboard/ThemeStrip";
import { HomelabSystemStatsCard } from "@/components/dashboard/HomelabSystemStatsCard";
import { HomelabStorageCard } from "@/components/dashboard/HomelabStorageCard";
import { HomelabOracleVoiceWidget } from "@/components/dashboard/HomelabOracleVoiceWidget";
import { HomelabDailyBriefingWidget } from "@/components/dashboard/HomelabDailyBriefingWidget";
import { WorkspacePrimarySidebar } from "@/components/dashboard/WorkspacePrimarySidebar";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import { cn } from "@/lib/cn";

function SpiritDashboardHomeInner() {
  return (
    <div
      data-layout="spirit-dashboard-home"
      className="relative flex h-[100dvh] w-full overflow-hidden bg-[color:var(--spirit-bg)] text-chalk"
    >
      {/* Ambient background layers */}
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[color:var(--spirit-bg)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(ellipse_110%_70%_at_50%_-10%,color-mix(in_oklab,var(--spirit-accent)_14%,transparent),transparent_55%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(ellipse_60%_50%_at_90%_30%,color-mix(in_oklab,var(--spirit-secondary-mix)_8%,transparent),transparent_60%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-[0.14] [background-image:linear-gradient(rgba(255,255,255,0.028)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.028)_1px,transparent_1px)] [background-size:48px_48px]"
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
        {/* Header */}
        <header className="shrink-0 border-b border-[color:var(--spirit-border)] bg-white/[0.03] backdrop-blur-xl">
          <div className="flex items-center gap-4 px-4 py-2.5 sm:px-6">
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-base font-semibold tracking-tight text-chalk sm:text-lg">
                SpiritOS Homelab
              </h1>
              <p className="truncate font-mono text-[10px] leading-snug text-chalk/48">
                Trinity Cluster · Sovereign
              </p>
            </div>
            {/* Theme + micro-status - stacked so the strip owns the corner, copy doesn’t elbow the title */}
            <div className="flex shrink-0 flex-col items-end gap-0.5 sm:gap-1">
              <ThemeStrip />
              <p className="flex flex-wrap items-center justify-end gap-x-1 gap-y-0.5 text-right font-mono text-[9px] leading-tight text-chalk/40 sm:text-[9.5px]">
                <span className="homelab-status-dot" aria-hidden />
                <span>All nodes nominal</span>
                <span className="text-chalk/20">·</span>
                <Clock
                  inline
                  className="text-[9px] text-chalk/40 sm:text-[9.5px]"
                />
                <span className="text-chalk/20">·</span>
                <span>Cluster uptime 14d 06h</span>
              </p>
            </div>
          </div>
        </header>

        <main className="scrollbar-hide min-h-0 flex-1 overflow-y-auto px-3 pb-10 pt-5 sm:px-5">
          {/* Dashboard grid - 1 col mobile, 2 col sm, 12 col xl */}
          <div className="mx-auto grid max-w-[1400px] grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-12">

            {/* Oracle Voice - left of main row */}
            <HomelabOracleVoiceWidget className="col-span-1 sm:col-span-1 xl:col-span-5" />

            {/* Daily Briefing - right of main row */}
            <HomelabDailyBriefingWidget className="col-span-1 sm:col-span-1 xl:col-span-7" />

            {/* System Stats */}
            <HomelabSystemStatsCard className="col-span-1 sm:col-span-1 xl:col-span-7" />

            {/* Storage */}
            <HomelabStorageCard className="col-span-1 sm:col-span-1 xl:col-span-5" />
          </div>
        </main>
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
