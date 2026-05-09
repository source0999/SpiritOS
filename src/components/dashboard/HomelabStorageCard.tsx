"use client";

import { HardDrive } from "lucide-react";

import { useClusterTelemetry, type ClusterFetchState } from "@/hooks/useClusterTelemetry";
import { HomelabProgressBar } from "@/components/dashboard/HomelabProgressBar";
import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";
import { cn } from "@/lib/cn";
import type { ClusterNodeTelemetry, ClusterTelemetryResponse, NodeDrive, SmartStatus } from "@/lib/server/telemetry/types";

function fmtBytes(bytes: number | null): string {
  if (bytes === null || bytes <= 0) return " - ";
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
  if (type === "UNKNOWN") return "homelab-tag homelab-tag--unknown";
  return "homelab-tag homelab-tag--unknown";
}

function smartTone(s: SmartStatus): string {
  if (s === "Healthy") return "text-[oklch(0.74_0.16_160)]";
  if (s === "Warning") return "text-amber-400/80";
  if (s === "Critical") return "text-rose-400/80";
  return "text-chalk/40";
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

export interface HomelabStorageCardViewProps {
  className?: string;
  data: ClusterTelemetryResponse | null;
  state: ClusterFetchState;
  error: string | null;
}

export function HomelabStorageCardView({
  className,
  data,
  state,
  error,
}: HomelabStorageCardViewProps) {
  const nodes = data?.nodes ?? [];

  const syncTime = data?.collectedAt
    ? new Date(data.collectedAt).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : null;

  const headerDotClass =
    state === "error"
      ? "homelab-status-dot homelab-status-dot--offline"
      : state === "checking"
        ? "homelab-status-dot homelab-status-dot--pending"
        : "homelab-status-dot";

  const headerBadgeVariant = state === "error" ? "offline" : state === "checking" ? "pending" : "live";
  const headerBadgeLabel = state === "error" ? "Error" : state === "checking" ? "Checking" : "Live";

  return (
    <section
      aria-label="Storage"
      className={cn("spirit-dashboard-v2-glass p-5 sm:p-7", className)}
    >
      <span className="spirit-dashboard-v2-glass__shine-t" aria-hidden />
      <div className="mb-5 flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div
            className="hidden shrink-0 rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_65%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg-soft)_42%,transparent)] p-2.5 sm:block"
            aria-hidden
          >
            <HardDrive className="h-5 w-5 text-chalk/50" strokeWidth={2} />
          </div>
          <div className="min-w-0">
          <p className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-chalk/48">
            <span className={headerDotClass} aria-hidden />
            Local Drive Health
          </p>
          <h2 className="mt-1 font-mono text-[15px] font-semibold uppercase tracking-tight text-chalk">
            Storage
          </h2>
          <p className="mt-0.5 font-mono text-[10px] text-chalk/36">
            Cluster storage telemetry · grouped by node
          </p>
          {state === "error" && error ? (
            <p className="mt-1 font-mono text-[9.5px] text-rose-400/70">{error}</p>
          ) : state !== "checking" && syncTime ? (
            <p className="mt-1 font-mono text-[9.5px] text-chalk/30">Synced {syncTime}</p>
          ) : null}
          </div>
        </div>
        <HomelabStatusBadge variant={headerBadgeVariant}>{headerBadgeLabel}</HomelabStatusBadge>
      </div>

      {state === "checking" && (
        <div className="flex flex-col gap-3">
          {[0, 1].map((i) => (
            <div
              key={i}
              className="spirit-dashboard-v2-inner-card h-[100px] animate-pulse border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_45%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg-soft)_55%,transparent)]"
            />
          ))}
        </div>
      )}

      {state !== "checking" && nodes.length === 0 && (
        <p className="font-mono text-[10px] text-chalk/35">
          {state === "error" ? error ?? "Cluster telemetry failed" : "Telemetry not configured"}
        </p>
      )}

      {nodes.length > 0 && state !== "checking" && (
        <div className="flex flex-col gap-3.5">
          {nodes.map((node) => {
            const offline = node.status === "offline" || node.status === "unknown";
            const drives = node.storage?.drives ?? [];
            const hasDrives = drives.length > 0;

            return (
              <div key={node.id}>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className="truncate font-mono text-[10.5px] text-[color:var(--spirit-accent-strong)]">
                    {node.label}
                  </span>
                  <HomelabStatusBadge variant={nodeStorageBadge(node)}>
                    {nodeStorageBadgeLabel(node)}
                  </HomelabStatusBadge>
                </div>

                {offline ? (
                  <p className="spirit-dashboard-v2-inner-card border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_50%,transparent)] px-3 py-2 font-mono text-[9.5px] text-rose-400/70">
                    Offline{node.error ? ` · ${node.error}` : ""}
                  </p>
                ) : !hasDrives ? (
                  <div className="spirit-dashboard-v2-inner-card border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_50%,transparent)] px-3 py-2.5">
                    <p className="font-mono text-[10px] text-chalk/45">Storage telemetry unavailable</p>
                    {node.storage?.error ? (
                      <p className="mt-1 font-mono text-[9.5px] text-amber-400/75">{node.storage.error}</p>
                    ) : null}
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    {drives.map((drive) => (
                      <div
                        key={drive.id}
                        className="spirit-dashboard-v2-inner-card border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_48%,transparent)] p-3"
                      >
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <div className="flex min-w-0 items-center gap-2">
                            <span
                              className={driveTagClass(drive.type)}
                              aria-label={drive.type}
                            >
                              {drive.type}
                            </span>
                            <span className="truncate font-mono text-[12px] text-chalk/80">
                              {drive.name}
                            </span>
                          </div>
                          <span className="shrink-0 font-mono text-[10px] text-chalk/40">
                            <span className="text-chalk/80">{fmtBytes(drive.usedBytes)}</span>
                            {" / "}
                            {fmtBytes(drive.totalBytes)}
                          </span>
                        </div>

                        {(drive.mount || drive.fsType) && (
                          <p className="mb-2 truncate font-mono text-[9px] text-chalk/32">
                            {[drive.mount, drive.fsType].filter(Boolean).join(" · ")}
                          </p>
                        )}

                        <HomelabProgressBar
                          pct={drive.usedPct ?? 0}
                          variant={fillVariant(drive.usedPct)}
                          label={`${drive.name} usage`}
                        />

                        <div className="mt-2 flex items-center justify-between gap-2">
                          <span className={cn("font-mono text-[9.5px]", smartTone(drive.smart))}>
                            ● {drive.smart}
                          </span>
                          {drive.tempC !== null ? (
                            <span className="font-mono text-[9.5px] text-chalk/36">{drive.tempC}°C</span>
                          ) : null}
                        </div>
                      </div>
                    ))}
                    {node.storage?.error ? (
                      <p className="font-mono text-[9px] text-amber-400/70">{node.storage.error}</p>
                    ) : null}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export function HomelabStorageCard({ className }: { className?: string }) {
  const { data, state, error } = useClusterTelemetry();
  return <HomelabStorageCardView className={className} data={data} state={state} error={error} />;
}
