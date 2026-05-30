"use client";

import { HardDrive } from "lucide-react";

import { HomelabProgressBar } from "@/components/dashboard/HomelabProgressBar";
import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";
import type { ClusterFetchState } from "@/hooks/useClusterTelemetry";
import { cn } from "@/lib/cn";
import { visibleDriveSmartStatus } from "@/lib/storage-health";
import type {
  ClusterNodeTelemetry,
  ClusterTelemetryResponse,
  NodeDrive,
  SmartStatus,
} from "@/lib/server/telemetry/types";

interface DashboardDemoV4StorageProps {
  data: ClusterTelemetryResponse | null;
  state: ClusterFetchState;
  error: string | null;
}

function fmtBytes(bytes: number | null): string {
  if (bytes === null || bytes <= 0) return "Unavailable";
  const tb = bytes / 1e12;
  if (tb >= 1) return `${tb.toFixed(2)} TB`;
  const gb = bytes / 1e9;
  if (gb >= 100) return `${Math.round(gb)} GB`;
  return `${gb.toFixed(1)} GB`;
}

function fillVariant(pct: number | null): "default" | "warn" | "bad" {
  if (pct === null) return "default";
  if (pct >= 85) return "bad";
  if (pct >= 65) return "warn";
  return "default";
}

function driveTagClass(type: NodeDrive["type"]): string {
  if (type === "HDD") return "homelab-tag homelab-tag--hdd";
  if (type === "SSD" || type === "NVME") return "homelab-tag homelab-tag--ssd";
  return "homelab-tag homelab-tag--unknown";
}

function smartTone(s: SmartStatus): string {
  if (s === "Healthy") return "dashboard-demo-v4-smart-healthy";
  if (s === "Warning") return "dashboard-demo-v4-smart-warning";
  if (s === "Critical") return "dashboard-demo-v4-smart-critical";
  return "dashboard-demo-v4-smart-unknown";
}

function nodeStorageBadge(node: ClusterNodeTelemetry): "live" | "pending" | "offline" {
  if (node.status === "offline" || node.status === "unknown") return "offline";
  const drives = node.storage?.drives;
  if (drives && drives.length > 0) return "live";
  return "pending";
}

function nodeStorageBadgeLabel(node: ClusterNodeTelemetry): string {
  if (node.status === "offline" || node.status === "unknown") return "Offline";
  const drives = node.storage?.drives;
  if (drives && drives.length > 0) return "Live";
  return "Pending";
}

function stateBadge(state: ClusterFetchState) {
  if (state === "error") return { variant: "offline" as const, label: "Error" };
  if (state === "checking") return { variant: "pending" as const, label: "Loading" };
  return { variant: "live" as const, label: "Synced" };
}

export function DashboardDemoV4Storage({ data, state, error }: DashboardDemoV4StorageProps) {
  const nodes = data?.nodes ?? [];
  const badge = stateBadge(state);
  const syncTime = data?.collectedAt
    ? new Date(data.collectedAt).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : null;

  return (
    <section aria-label="Storage pool" className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-card">
      <div className="dashboard-demo-v4-card-header">
        <div className="dashboard-demo-v4-card-title-row">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <HardDrive className="h-5 w-5" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Local drive health</p>
            <h2>Storage pool</h2>
            <p className="dashboard-demo-v4-card-subtitle">
              {state === "error" && error
                ? error
                : syncTime
                  ? `Synced ${syncTime}`
                  : "Cluster storage telemetry"}
            </p>
          </div>
        </div>
        <HomelabStatusBadge variant={badge.variant}>{badge.label}</HomelabStatusBadge>
      </div>

      {state === "checking" ? (
        <div className="dashboard-demo-v4-skeleton-list" aria-label="Loading storage telemetry">
          <div />
          <div />
        </div>
      ) : null}

      {state !== "checking" && nodes.length === 0 ? (
        <p className="dashboard-demo-v4-empty-copy">
          {state === "error" ? error ?? "Cluster telemetry failed" : "Telemetry not configured"}
        </p>
      ) : null}

      {nodes.length > 0 && state !== "checking" ? (
        <div className="dashboard-demo-v4-storage-list">
          {nodes.map((node) => {
            const offline = node.status === "offline" || node.status === "unknown";
            const drives = node.storage?.drives ?? [];

            return (
              <article key={node.id} className="dashboard-demo-v4-storage-node">
                <div className="dashboard-demo-v4-storage-node-header">
                  <span>{node.label}</span>
                  <HomelabStatusBadge variant={nodeStorageBadge(node)}>
                    {nodeStorageBadgeLabel(node)}
                  </HomelabStatusBadge>
                </div>

                {offline ? (
                  <p className="dashboard-demo-v4-empty-copy">
                    Offline{node.error ? ` · ${node.error}` : ""}
                  </p>
                ) : drives.length === 0 ? (
                  <div className="dashboard-demo-v4-drive-card">
                    <p className="dashboard-demo-v4-empty-copy">Storage telemetry unavailable</p>
                    {node.storage?.error ? (
                      <p className="dashboard-demo-v4-warning-copy">{node.storage.error}</p>
                    ) : null}
                  </div>
                ) : (
                  <div className="dashboard-demo-v4-drive-list">
                    {drives.map((drive) => {
                      const healthStatus = visibleDriveSmartStatus(drive);

                      return (
                        <div key={drive.id} className="dashboard-demo-v4-drive-card">
                          <div className="dashboard-demo-v4-drive-header">
                            <div className="dashboard-demo-v4-drive-name">
                              <span className={driveTagClass(drive.type)}>{drive.type}</span>
                              <strong>{drive.name}</strong>
                            </div>
                            <span className="dashboard-demo-v4-drive-capacity">
                              {fmtBytes(drive.usedBytes)} / {fmtBytes(drive.totalBytes)}
                            </span>
                          </div>

                          {(drive.mount || drive.fsType) && (
                            <p className="dashboard-demo-v4-drive-meta">
                              {[drive.mount, drive.fsType].filter(Boolean).join(" · ")}
                            </p>
                          )}

                          <HomelabProgressBar
                            pct={drive.usedPct ?? 0}
                            variant={fillVariant(drive.usedPct)}
                            label={`${drive.name} usage`}
                          />

                          <div className="dashboard-demo-v4-drive-footer">
                            <span className={cn("dashboard-demo-v4-smart", smartTone(healthStatus))}>
                              {healthStatus}
                            </span>
                            {drive.tempC !== null ? <span>{drive.tempC}°C</span> : null}
                          </div>
                        </div>
                      );
                    })}
                    {node.storage?.error ? (
                      <p className="dashboard-demo-v4-warning-copy">{node.storage.error}</p>
                    ) : null}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
