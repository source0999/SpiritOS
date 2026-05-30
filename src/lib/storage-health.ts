import type { NodeDrive, SmartStatus } from "@/lib/server/telemetry/types";

export function inferSmartStatusFromUsage(usedPct: number | null): SmartStatus {
  if (usedPct === null) return "Unknown";
  if (usedPct >= 95) return "Critical";
  if (usedPct >= 85) return "Warning";
  return "Healthy";
}

export function visibleDriveSmartStatus(drive: Pick<NodeDrive, "smart" | "usedPct">): SmartStatus {
  return drive.smart === "Unknown" ? inferSmartStatusFromUsage(drive.usedPct) : drive.smart;
}
