"use client";

import { useMemo, useSyncExternalStore } from "react";
import Link from "next/link";
import { MessageSquare } from "lucide-react";

import { OracleOrbSprite } from "@/components/oracle/OracleOrbSprite";
import { OracleVoiceVisualizer } from "@/components/oracle/OracleVoiceVisualizer";
import "@/components/oracle/oracle-visuals.css";
import { getOracleBrowserCapabilityReport } from "@/lib/oracle/oracle-browser-capabilities";
import {
  getOracleVisualStateForHomelab,
  type HomelabOracleBadgeVariant,
} from "@/lib/oracle/oracle-visual-state";

const noop = () => () => {};

export function DashboardDemoV4OracleHero() {
  const mounted = useSyncExternalStore(noop, () => true, () => false);
  const capability = useMemo(() => getOracleBrowserCapabilityReport(mounted), [mounted]);

  const badgeVariant: HomelabOracleBadgeVariant =
    !mounted
      ? "pending"
      : capability.canUseMic
        ? "live"
        : capability.isSecureContext === false
          ? "offline"
          : "ready";

  const visualState = useMemo(
    () => getOracleVisualStateForHomelab({ mounted, capability, badgeVariant }),
    [mounted, capability, badgeVariant],
  );

  return (
    <section aria-label="Oracle hero" className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-oracle-hero">
      <div className="dashboard-demo-v4-oracle-visual" aria-hidden="false">
        <div className="dashboard-demo-v4-oracle-halo" aria-hidden />
        <div className="dashboard-demo-v4-oracle-wing dashboard-demo-v4-oracle-wing-left" aria-hidden />
        <div className="dashboard-demo-v4-oracle-wing dashboard-demo-v4-oracle-wing-right" aria-hidden />
        <OracleOrbSprite visualState={visualState} variant="widget" />
        <OracleVoiceVisualizer
          state={visualState}
          compact
          className="dashboard-demo-v4-oracle-visualizer"
        />
      </div>

      <div className="dashboard-demo-v4-action-row">
        <Link href="/oracle" className="dashboard-demo-v4-primary-action">
          <MessageSquare className="h-4 w-4" aria-hidden />
          Open Oracle
        </Link>
      </div>
    </section>
  );
}
