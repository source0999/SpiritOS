"use client";

import { useLayoutEffect, useMemo } from "react";
import Link from "next/link";
import { LayoutDashboard, MessageCircle, Sparkles } from "lucide-react";

import { HomelabSystemStatsCardView } from "@/components/dashboard/HomelabSystemStatsCard";
import { HomelabStorageCardView } from "@/components/dashboard/HomelabStorageCard";
import { HomelabOracleVoiceWidget } from "@/components/dashboard/HomelabOracleVoiceWidget";
import { HomelabDailyBriefingWidget } from "@/components/dashboard/HomelabDailyBriefingWidget";
import { SpiritDashboardWorkspaceRail } from "@/components/dashboard/SpiritDashboardWorkspaceRail";
import { ThemeStrip } from "@/components/dashboard/ThemeStrip";
import { Clock } from "@/components/dashboard/Clock";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import { useClusterTelemetry } from "@/hooks/useClusterTelemetry";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";
import { cn } from "@/lib/cn";

type LiveStatus = {
  label: string;
  subtitle: string;
  variant: "live" | "pending" | "warn" | "offline" | "idle";
};

function deriveLiveStatus(
  state: "checking" | "loaded" | "error",
  data: ClusterTelemetryResponse | null,
): LiveStatus {
  if (state === "checking") {
    return { label: "Syncing", subtitle: "Syncing…", variant: "pending" };
  }
  if (state === "error") {
    return { label: "Degraded", subtitle: "Unreachable", variant: "offline" };
  }
  const nodes = data?.nodes ?? [];
  if (nodes.length === 0) {
    return { label: "Idle", subtitle: "No telemetry", variant: "idle" };
  }
  const hasOffline = nodes.some(
    (n) => n.status === "offline" || n.status === "unknown",
  );
  const hasDegraded = nodes.some((n) => n.status === "degraded");
  if (hasOffline) {
    return { label: "Partial", subtitle: "Node offline", variant: "warn" };
  }
  if (hasDegraded) {
    return { label: "Degraded", subtitle: "Node degraded", variant: "warn" };
  }
  return { label: "Mesh Live", subtitle: "Node nominal", variant: "live" };
}

function SpiritDashboardHomeInner() {
  const { data, state, error } = useClusterTelemetry();

  const liveStatus = useMemo(
    () => deriveLiveStatus(state, data),
    [state, data],
  );

  // Phase 2.10: pearl route — before paint; strips legacy inline void fill from root layout
  useLayoutEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    html.classList.add("spirit-dashboard-route");
    body.classList.add("spirit-dashboard-route");
    html.style.removeProperty("background-color");
    body.style.removeProperty("background-color");
    return () => {
      html.classList.remove("spirit-dashboard-route");
      body.classList.remove("spirit-dashboard-route");
    };
  }, []);

  return (
    <>
      {/* Atmosphere layers — fixed behind the glass frame; owns dashboard palette scope */}
      <div data-layout="spirit-dashboard-home" className="spirit-dashboard-v2-atmos" aria-hidden>
        <div className="spirit-dashboard-v2-atmos__canvas" />
        <div className="spirit-dashboard-v2-atmos__wash" />
        <div className="spirit-dashboard-v2-atmos__blob spirit-dashboard-v2-atmos__blob--a" aria-hidden />
        <div className="spirit-dashboard-v2-atmos__blob spirit-dashboard-v2-atmos__blob--b" aria-hidden />
        <div className="spirit-dashboard-v2-atmos__accent" aria-hidden />
        <div className="spirit-dashboard-v2-atmos__grid" aria-hidden />
        <div className="spirit-dashboard-v2-atmos__grain" aria-hidden />
        <div className="spirit-dashboard-v2-atmos__vignette" aria-hidden />
      </div>

      {/* Single glass shell — gutter used to live on a pointless wrapper div */}
      <div
        data-layout="spirit-dashboard-home"
        className={cn(
          "dashboard-v2-glass-frame relative z-10 mx-auto box-border flex min-w-0 flex-col",
          /* overflow-x on this node clips backdrop-filter into useless mud — main owns horizontal clip */
          "my-3 min-h-[calc(100dvh-1.5rem)] w-[calc(100%-1.5rem)] max-w-[min(1760px,100vw)]",
          "sm:my-4 sm:min-h-[calc(100dvh-2rem)] sm:w-[calc(100%-2rem)]",
          "lg:my-5 lg:min-h-[calc(100dvh-2.5rem)] lg:w-[calc(100%-2.5rem)]",
        )}
      >
        <div className="flex shrink-0 items-start justify-end px-4 pt-3 sm:px-5 sm:pt-4 lg:px-6 lg:pt-5">
          <div className="flex items-center gap-3">
            {/* Clock + subtitle — desktop only */}
            <div className="hidden flex-col items-end gap-0.5 sm:flex">
              <Clock
                inline
                className="text-[1.0rem] font-bold tabular-nums tracking-tight text-[color:var(--dash-utility-fg)]"
              />
              <p className="font-mono text-[7.5px] uppercase tracking-[0.18em] text-[color:var(--dash-utility-muted)]">
                Local time · {liveStatus.subtitle}
              </p>
            </div>
            {/* Live status pill */}
            <div className={cn("dash-live-pill", `dash-live-pill--${liveStatus.variant}`)}>
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-80" aria-hidden />
              {liveStatus.label}
            </div>
          </div>
        </div>

        <main className="flex-1 overflow-x-hidden px-4 pb-[max(5.5rem,calc(4.5rem+env(safe-area-inset-bottom,0px)))] pt-3 sm:px-5 sm:pt-4 lg:px-6 lg:pt-4">
          <div className="mx-auto grid min-w-0 max-w-[1440px] grid-cols-1 items-start gap-5 xl:grid-cols-12 xl:gap-7 2xl:max-w-[1480px]">
            <div className="flex min-w-0 flex-col gap-5 xl:col-span-8 xl:self-start xl:gap-6">
              <HomelabOracleVoiceWidget className="w-full min-w-0" />

              <div className="grid min-w-0 grid-cols-1 items-start gap-5 md:grid-cols-2 md:gap-5 xl:grid-cols-1 xl:gap-6">
                <HomelabSystemStatsCardView className="min-w-0" data={data} state={state} error={error} />
                <HomelabStorageCardView className="min-w-0" data={data} state={state} error={error} />
              </div>
            </div>

            <div className="flex min-w-0 flex-col gap-5 xl:col-span-4 xl:self-start">
              <HomelabDailyBriefingWidget className="w-full" />
              <SpiritDashboardWorkspaceRail />
            </div>
          </div>
        </main>

      </div>

      {/* Fixed bottom nav bubble: Dashboard · Chat · Oracle | theme swatches */}
      <nav
        data-layout="spirit-dashboard-home"
        aria-label="Dashboard navigation"
        className={cn(
          "pointer-events-none fixed inset-x-0 z-50",
          "bottom-[var(--spirit-keyboard-inset,0px)]",
          "flex items-end justify-center",
          "pb-[max(1.25rem,env(safe-area-inset-bottom,0px))]",
        )}
      >
        <div
          className={cn(
            "pointer-events-auto flex items-center gap-1 rounded-full px-2.5 py-2.5",
            "dash-floating-nav-shell",
          )}
        >
          <Link
            href="/"
            aria-current="page"
            aria-label="Dashboard home"
            className="dash-nav-bubble-item dash-nav-bubble-item--active"
          >
            <LayoutDashboard className="h-[1.1rem] w-[1.1rem] shrink-0" aria-hidden strokeWidth={2} />
            <span className="hidden sm:inline">Dashboard</span>
          </Link>
          <Link
            href="/chat"
            aria-label="Chat"
            className="dash-nav-bubble-item"
          >
            <MessageCircle className="h-[1.1rem] w-[1.1rem] shrink-0" aria-hidden strokeWidth={2} />
            <span className="hidden sm:inline">Chat</span>
          </Link>
          <Link
            href="/oracle"
            aria-label="Oracle"
            className="dash-nav-bubble-item"
          >
            <Sparkles className="h-[1.1rem] w-[1.1rem] shrink-0" aria-hidden strokeWidth={2} />
            <span className="hidden sm:inline">Oracle</span>
          </Link>

          <div className="dash-nav-bubble-divider" aria-hidden />

          <ThemeStrip variant="bubble" />
        </div>
      </nav>
    </>
  );
}

export default function SpiritDashboardHome() {
  return (
    <ClientFailSafe label="spirit-dashboard-home">
      <SpiritDashboardHomeInner />
    </ClientFailSafe>
  );
}
