"use client";

// ── OracleStage - thin wrapper; stays eager (tiny CTA vs lazy neural/quarantine) ─
import { OracleStagePanel } from "@/components/dashboard/OracleStagePanel";

export function OracleStage() {
  return <OracleStagePanel />;
}
