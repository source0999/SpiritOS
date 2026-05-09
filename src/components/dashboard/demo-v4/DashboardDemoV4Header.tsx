"use client";

// ── DashboardDemoV4Header - brand mark + title + clock + live status pill ───
// > Pure presentational. The page derives `liveLabel` / `liveState` from
// > `useClusterTelemetry` and forwards them in.

import { Clock3, Zap } from "lucide-react";

import { Clock } from "@/components/dashboard/Clock";

export type DashboardDemoV4HeaderProps = {
  telemetryLine: string;
  liveLabel: string;
  liveState: "live" | "loading" | "error";
};

export function DashboardDemoV4Header({
  telemetryLine,
  liveLabel,
  liveState,
}: DashboardDemoV4HeaderProps) {
  return (
    <header className="dashboard-demo-v4-header">
      <div className="flex items-center gap-4">
        <div className="dashboard-demo-v4-brand-mark" aria-hidden>
          <Zap className="h-6 w-6" strokeWidth={2} />
        </div>
        <div className="dashboard-demo-v4-brand-copy">
          <h1 className="dashboard-demo-v4-brand-title">
            SpiritOS{" "}
            <span>Trinity</span>
          </h1>
          <p className="dashboard-demo-v4-brand-subtitle">Homelab Dashboard v4.5</p>
        </div>
      </div>

      <div className="dashboard-demo-v4-header-status">
        <div className="dashboard-demo-v4-clock-stack">
          <Clock
            inline
            className="dashboard-demo-v4-clock-time"
          />
          <p className="dashboard-demo-v4-telemetry-line">
            <Clock3 className="h-3 w-3" aria-hidden />
            {telemetryLine}
          </p>
        </div>
        <div
          className="dashboard-demo-v4-live-pill"
          data-state={liveState}
          role="status"
          aria-live="polite"
        >
          <span className="dashboard-demo-v4-live-dot" aria-hidden />
          {liveLabel}
        </div>
      </div>
    </header>
  );
}
