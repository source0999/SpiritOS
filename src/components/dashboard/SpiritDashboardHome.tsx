"use client";

import { DashboardDemoV4 } from "@/components/dashboard/demo-v4/DashboardDemoV4";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";

export default function SpiritDashboardHome() {
  return (
    <ClientFailSafe label="spirit-dashboard-home">
      <DashboardDemoV4 />
    </ClientFailSafe>
  );
}
