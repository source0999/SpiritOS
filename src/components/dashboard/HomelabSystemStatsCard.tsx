"use client";

import { useClusterTelemetry } from "@/hooks/useClusterTelemetry";
import { HomelabProgressBar } from "@/components/dashboard/HomelabProgressBar";
import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";
import { cn } from "@/lib/cn";
import type { ClusterNodeTelemetry } from "@/lib/server/telemetry/types";

function pct(val: number | null): string {
  return val !== null ? `${Math.round(val)}%` : "—";
}

function fmtMemory(used: number | null, total: number | null): string {
  if (used === null || total === null) return "—";
  const usedGB = (used / 1e9).toFixed(1);
  const totalGB = Math.round(total / 1e9);
  return `${usedGB} GB / ${totalGB} GB`;
}

function formatUptime(sec: number | null): string {
  if (sec === null) return "—";
  const d = Math.floor(sec / 86400);
  const h = Math.floor((sec % 86400) / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function cpuVariant(v: number | null): "default" | "good" | "warn" | "bad" {
  if (v === null) return "default";
  if (v >= 85) return "bad";
  if (v >= 65) return "warn";
  if (v < 40) return "good";
  return "default";
}

function ramVariant(v: number | null): "default" | "warn" | "bad" {
  if (v === null) return "default";
  if (v >= 85) return "bad";
  if (v >= 65) return "warn";
  return "default";
}

function NodeCard({ node }: { node: ClusterNodeTelemetry }) {
  const isOffline = node.status === "offline" || node.status === "unknown";
  const spec =
    [node.hostname, node.platform, node.arch].filter(Boolean).join(" · ") || "—";

  const badgeVariant =
    node.status === "online"
      ? "live"
      : node.status === "offline"
        ? "offline"
        : ("pending" as const);

  const badgeLabel =
    node.status === "online"
      ? "Live"
      : node.status === "degraded"
        ? "Degraded"
        : node.status === "offline"
          ? "Offline"
          : "Unknown";

  return (
    <div className="rounded-[14px] border border-white/[0.06] bg-white/[0.025] p-3">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-mono text-[11px] text-chalk">{node.label}</p>
          <p className="truncate font-mono text-[9.5px] text-chalk/36 mt-0.5">{spec}</p>
        </div>
        <HomelabStatusBadge variant={badgeVariant}>{badgeLabel}</HomelabStatusBadge>
      </div>

      {isOffline ? (
        <p className="mt-2 font-mono text-[9.5px] text-rose-400/70">
          Offline{node.error ? ` · ${node.error}` : ""}
        </p>
      ) : (
        <div className="mt-3 flex flex-col gap-2.5">
          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <span className="font-mono text-[10px] text-chalk/48">CPU</span>
              <span className="font-mono text-[10.5px] text-chalk/80">
                {node.cpu.usagePct !== null ? pct(node.cpu.usagePct) : "Unavailable"}
              </span>
            </div>
            {node.cpu.usagePct !== null ? (
              <HomelabProgressBar
                pct={node.cpu.usagePct}
                variant={cpuVariant(node.cpu.usagePct)}
                label={`${node.label} CPU`}
              />
            ) : null}
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <span className="font-mono text-[10px] text-chalk/48">RAM</span>
              <span className="font-mono text-[10.5px] text-chalk/80">
                {node.memory.usedPct !== null
                  ? fmtMemory(node.memory.usedBytes, node.memory.totalBytes)
                  : "Unavailable"}
              </span>
            </div>
            {node.memory.usedPct !== null ? (
              <HomelabProgressBar
                pct={node.memory.usedPct}
                variant={ramVariant(node.memory.usedPct)}
                label={`${node.label} RAM`}
              />
            ) : null}
          </div>

          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] text-chalk/48">Uptime</span>
            <span className="font-mono text-[10px] text-chalk/65">
              {formatUptime(node.uptimeSec)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

interface Props {
  className?: string;
}

export function HomelabSystemStatsCard({ className }: Props) {
  const { data, state, error } = useClusterTelemetry();
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
    <section aria-label="System Stats" className={cn("homelab-panel p-5", className)}>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-chalk/48">
            <span className={headerDotClass} aria-hidden />
            Node Vitals
          </p>
          <h2 className="mt-1 font-mono text-[15px] font-semibold uppercase tracking-tight text-chalk">
            System Stats
          </h2>
          <p className="mt-0.5 font-mono text-[10px] text-chalk/36">
            {state === "checking"
              ? "Polling…"
              : state === "error" && error
                ? error
                : syncTime
                  ? `Synced ${syncTime}`
                  : "Live telemetry"}
          </p>
        </div>
        <HomelabStatusBadge variant={headerBadgeVariant}>{headerBadgeLabel}</HomelabStatusBadge>
      </div>

      {state === "checking" && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1].map((i) => (
            <div
              key={i}
              className="h-[130px] animate-pulse rounded-[14px] border border-white/[0.06] bg-white/[0.025]"
            />
          ))}
        </div>
      )}

      {state !== "checking" && nodes.length === 0 && (
        <p className="font-mono text-[10px] text-chalk/35">
          {state === "error" ? error ?? "Cluster telemetry failed" : "Telemetry not configured"}
        </p>
      )}

      {nodes.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {nodes.map((node) => (
            <NodeCard key={node.id} node={node} />
          ))}
        </div>
      )}
    </section>
  );
}
