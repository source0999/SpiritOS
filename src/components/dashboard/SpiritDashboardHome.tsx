"use client";

import { DashboardDemoV4 } from "@/components/dashboard/demo-v4/DashboardDemoV4";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";
import type { ScoutOverview } from "@/lib/scout-overview";

export default function SpiritDashboardHome({
  initialTelemetry = null,
  initialScoutOverview = null,
}: {
  initialTelemetry?: ClusterTelemetryResponse | null;
  initialScoutOverview?: ScoutOverview | null;
}) {
  return (
    <ClientFailSafe label="spirit-dashboard-home">
      <DashboardDemoV4
        initialTelemetry={initialTelemetry}
        initialScoutOverview={initialScoutOverview}
      />
    </ClientFailSafe>
  );
}
