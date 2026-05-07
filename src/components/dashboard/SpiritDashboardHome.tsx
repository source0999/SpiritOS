"use client";

import { useMemo } from "react";
import { Zap } from "lucide-react";

import { Clock } from "@/components/dashboard/Clock";
import { ThemeStrip } from "@/components/dashboard/ThemeStrip";
import { HomelabSystemStatsCardView } from "@/components/dashboard/HomelabSystemStatsCard";
import { HomelabStorageCardView } from "@/components/dashboard/HomelabStorageCard";
import { HomelabOracleVoiceWidget } from "@/components/dashboard/HomelabOracleVoiceWidget";
import { HomelabDailyBriefingWidget } from "@/components/dashboard/HomelabDailyBriefingWidget";
import { SpiritDashboardWorkspaceRail } from "@/components/dashboard/SpiritDashboardWorkspaceRail";
import { WorkspacePrimarySidebar } from "@/components/dashboard/WorkspacePrimarySidebar";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import { useClusterTelemetry } from "@/hooks/useClusterTelemetry";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";
import { cn } from "@/lib/cn";

function formatDashboardTelemetryLine(
  state: "checking" | "loaded" | "error",
  data: ClusterTelemetryResponse | null,
  error: string | null,
): string {
  if (state === "checking") return "Telemetry syncing…";
  if (state === "error") {
    const msg = error?.trim();
    return msg ? msg : "Telemetry unreachable";
  }
  const nodes = data?.nodes ?? [];
  if (nodes.length === 0) {
    return "No nodes reported · configure cluster telemetry";
  }
  const s = data?.summary;
  if (s) {
    const bits = [`${s.online}/${s.total} nodes online`];
    if (s.degraded > 0) bits.push(`${s.degraded} degraded`);
    if (s.offline > 0) bits.push(`${s.offline} offline`);
    return bits.join(" · ");
  }
  const online = nodes.filter((n) => n.status === "online").length;
  return `${online}/${nodes.length} nodes online`;
}

function telemetryHeaderDotClass(
  state: "checking" | "loaded" | "error",
  data: ClusterTelemetryResponse | null,
): string {
  if (state === "checking") return "homelab-status-dot homelab-status-dot--pending";
  if (state === "error") return "homelab-status-dot homelab-status-dot--offline";
  const nodes = data?.nodes ?? [];
  if (nodes.length === 0) return "homelab-status-dot homelab-status-dot--pending";
  const bad = nodes.some((n) => n.status === "offline" || n.status === "unknown");
  if (bad) return "homelab-status-dot homelab-status-dot--offline";
  const degraded = nodes.some((n) => n.status === "degraded");
  if (degraded) return "homelab-status-dot homelab-status-dot--pending";
  return "homelab-status-dot";
}

function SpiritDashboardHomeInner() {
  const { data, state, error } = useClusterTelemetry();

  const telemetryLine = useMemo(
    () => formatDashboardTelemetryLine(state, data, error),
    [state, data, error],
  );

  const dotClass = useMemo(() => telemetryHeaderDotClass(state, data), [state, data]);

  return (
    <div
      data-layout="spirit-dashboard-home"
      className="spirit-dashboard-v2-root relative flex min-h-[100dvh] w-full max-w-[100vw] flex-row overflow-x-hidden bg-[color:var(--spirit-bg)] text-chalk"
    >
      <div className="spirit-dashboard-v2-atmos" aria-hidden>
        <div className="spirit-dashboard-v2-atmos__canvas" />
        <div className="spirit-dashboard-v2-atmos__wash" />
        <div
          className="spirit-dashboard-v2-atmos__blob spirit-dashboard-v2-atmos__blob--a"
          aria-hidden
        />
        <div
          className="spirit-dashboard-v2-atmos__blob spirit-dashboard-v2-atmos__blob--b"
          aria-hidden
        />
        <div className="spirit-dashboard-v2-atmos__accent" aria-hidden />
        <div className="spirit-dashboard-v2-atmos__grid" aria-hidden />
        <div className="spirit-dashboard-v2-atmos__grain" aria-hidden />
        <div className="spirit-dashboard-v2-atmos__vignette" aria-hidden />
      </div>

      <WorkspacePrimarySidebar />

      <div
        className={cn(
          "relative z-10 flex min-h-[100dvh] min-w-0 flex-1 flex-col overflow-x-hidden",
          "pb-[calc(4.5rem+env(safe-area-inset-bottom,0px))] lg:pb-0",
        )}
      >
        <header className="spirit-dashboard-v2-header-glass sticky top-0 z-20 shrink-0 backdrop-blur-xl">
          <div className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-5 sm:py-4">
            <div className="flex min-w-0 items-start gap-3 sm:gap-4">
              <div
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_90%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg-soft)_72%,transparent)] shadow-[0_10px_36px_-22px_rgba(0,0,0,0.55)] sm:h-12 sm:w-12 sm:rounded-3xl"
                aria-hidden
              >
                <Zap
                  className="h-6 w-6 text-[color:var(--spirit-accent-strong)] sm:h-6 sm:w-6"
                  strokeWidth={2}
                />
              </div>
              <div className="min-w-0 flex-1">
                <h1 className="truncate font-mono text-lg font-semibold uppercase tracking-tight text-chalk sm:text-xl">
                  SpiritOS <span className="font-light text-chalk/55">Homelab</span>
                </h1>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.28em] text-chalk/38">
                  Dashboard · telemetry · oracle voice
                </p>
                <p className="mt-2 font-mono text-[11px] leading-snug text-chalk/55">{telemetryLine}</p>
              </div>
            </div>

            <div className="flex min-w-0 shrink-0 flex-col items-stretch gap-1.5 sm:items-end">
              <ThemeStrip />
              <p className="flex flex-wrap items-center justify-end gap-x-2 gap-y-1 font-mono text-[9px] leading-tight text-chalk/42 sm:text-[9.5px]">
                <span className={dotClass} aria-hidden />
                <span className="text-chalk/55">Cluster pulse</span>
                <span className="text-chalk/18">·</span>
                <Clock inline className="text-[9px] text-chalk/42 sm:text-[9.5px]" />
              </p>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-x-hidden px-4 pb-[max(3rem,calc(5rem+env(safe-area-inset-bottom,0px)))] pt-5 sm:px-5 sm:pb-12 sm:pt-7 lg:pb-14 lg:pt-8">
          <div className="mx-auto grid min-w-0 max-w-[1440px] grid-cols-1 gap-5 xl:grid-cols-12 xl:gap-7 2xl:max-w-[1480px]">
            <div className="flex min-w-0 flex-col gap-5 xl:col-span-8 xl:gap-6">
              <HomelabOracleVoiceWidget className="w-full min-w-0" />

              {/* items-start: equal-height stretch was clipping glass overflow; xl stacks full-width rows */}
              <div className="grid min-w-0 grid-cols-1 items-start gap-5 md:grid-cols-2 md:gap-5 xl:grid-cols-1 xl:gap-6">
                <HomelabSystemStatsCardView className="min-w-0" data={data} state={state} error={error} />
                <HomelabStorageCardView className="min-w-0" data={data} state={state} error={error} />
              </div>
            </div>

            <div className="flex min-w-0 flex-col gap-5 xl:sticky xl:top-28 xl:z-[11] xl:col-span-4 xl:self-start">
              <HomelabDailyBriefingWidget className="w-full" />
              <SpiritDashboardWorkspaceRail />
            </div>
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
