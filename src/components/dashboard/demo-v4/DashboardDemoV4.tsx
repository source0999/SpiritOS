"use client";

// ── DashboardDemoV4 - root scaffold for the new isolated dashboard ──────────
// > Mounted on `/` through SpiritDashboardHome.tsx.
// > <main> directly owns the dashboard surface — no fake outer glass wrapper.

import { useEffect, useMemo } from "react";
import { CheckCircle2, ListChecks } from "lucide-react";

import { useClusterTelemetry } from "@/hooks/useClusterTelemetry";
import { HomelabScoutIntelligenceWidget } from "@/components/dashboard/HomelabScoutIntelligenceWidget";
import { DashboardDemoV4Atmosphere } from "@/components/dashboard/demo-v4/DashboardDemoV4Atmosphere";
import { DashboardDemoV4Briefing } from "@/components/dashboard/demo-v4/DashboardDemoV4Briefing";
import { DashboardDemoV4Header } from "@/components/dashboard/demo-v4/DashboardDemoV4Header";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import { DashboardDemoV4OracleHero } from "@/components/dashboard/demo-v4/DashboardDemoV4OracleHero";
import { DashboardDemoV4Storage } from "@/components/dashboard/demo-v4/DashboardDemoV4Storage";
import { DashboardDemoV4SystemStats } from "@/components/dashboard/demo-v4/DashboardDemoV4SystemStats";

import "@/styles/dashboard-demo-v4.css";

type LiveStatus = {
  liveState: "live" | "loading" | "error";
  liveLabel: string;
  telemetryLine: string;
};

const PROJECT_TRACKER_ITEMS = [
  {
    label: "Dashboard glass",
    meta: "Surface pass",
    status: "Active",
    tone: "active",
  },
  {
    label: "Oracle widget",
    meta: "Compact mode",
    status: "Tuning",
    tone: "tuning",
  },
  {
    label: "Mobile safety",
    meta: "Next pass",
    status: "Queued",
    tone: "queued",
  },
] as const;

function deriveLiveStatus(
  state: "checking" | "loaded" | "error",
): LiveStatus {
  if (state === "checking") {
    return {
      liveState: "loading",
      liveLabel: "Syncing",
      telemetryLine: "Local time · Syncing",
    };
  }
  if (state === "error") {
    return {
      liveState: "error",
      liveLabel: "Telemetry Offline",
      telemetryLine: "Local time · Telemetry offline",
    };
  }
  return {
    liveState: "live",
    liveLabel: "Trinity Mesh Live",
    telemetryLine: "Local time · Node nominal",
  };
}

export function DashboardDemoV4() {
  const telemetry = useClusterTelemetry();
  const { data, state, error } = telemetry;

  const status = useMemo(() => deriveLiveStatus(state), [state]);

  useEffect(() => {
    const widgets = Array.from(
      document.querySelectorAll<HTMLElement>(
        ".dashboard-demo-v4-oracle-hero, .dashboard-demo-v4-project-tracker, .dashboard-demo-v4-card, .dashboard-demo-v4-briefing",
      ),
    );

    if (widgets.length === 0) return;

    widgets.forEach((widget) => {
      widget.classList.add("dashboard-demo-v4-scroll-reveal");
    });

    const isMobile =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(max-width: 767px)").matches;

    if (!isMobile || !("IntersectionObserver" in window)) {
      widgets.forEach((widget) => {
        widget.classList.add("dashboard-demo-v4-scroll-reveal-in");
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("dashboard-demo-v4-scroll-reveal-in");
          observer.unobserve(entry.target);
        });
      },
      {
        threshold: 0.18,
        rootMargin: "0px 0px -12% 0px",
      },
    );

    widgets.forEach((widget) => observer.observe(widget));

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <main className="dashboard-demo-v4-root">
      <DashboardDemoV4Atmosphere />

      <div className="dashboard-demo-v4-shell">
        <DashboardDemoV4Header
          telemetryLine={status.telemetryLine}
          liveLabel={status.liveLabel}
          liveState={status.liveState}
        />

        <section
          aria-label="Dashboard preview scaffold"
          className="grid grid-cols-1 gap-4 xl:grid-cols-12 xl:gap-5"
        >
          <div className="flex flex-col gap-4 xl:col-span-8 xl:gap-5">
            <div className="dashboard-demo-v4-focus-grid">
              <DashboardDemoV4OracleHero />
              <section
                aria-label="Project tracker"
                className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-project-tracker"
              >
                <div className="dashboard-demo-v4-card-header">
                  <div className="dashboard-demo-v4-card-title-row">
                    <span className="dashboard-demo-v4-icon-tile" aria-hidden>
                      <ListChecks className="h-5 w-5" />
                    </span>
                    <div>
                      <p className="dashboard-demo-v4-eyebrow">Project flow</p>
                      <h2>Project tracker</h2>
                    </div>
                  </div>
                  <span className="dashboard-demo-v4-demo-label">Demo</span>
                </div>

                <div className="dashboard-demo-v4-project-list">
                  {PROJECT_TRACKER_ITEMS.map((item) => (
                    <article key={item.label} className="dashboard-demo-v4-project-item">
                      <CheckCircle2 className="h-4 w-4" aria-hidden />
                      <div>
                        <strong>{item.label}</strong>
                        <span>{item.meta}</span>
                      </div>
                      <em data-tone={item.tone}>{item.status}</em>
                    </article>
                  ))}
                </div>
              </section>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:gap-5">
              <DashboardDemoV4SystemStats data={data} state={state} error={error} />
              <DashboardDemoV4Storage data={data} state={state} error={error} />
            </div>
          </div>
          <div className="flex flex-col gap-4 xl:col-span-4 xl:self-start xl:gap-5">
            <DashboardDemoV4Briefing />
            <HomelabScoutIntelligenceWidget />
          </div>
        </section>
      </div>

      <DashboardDemoV4FloatingNav />
    </main>
  );
}

export default DashboardDemoV4;
