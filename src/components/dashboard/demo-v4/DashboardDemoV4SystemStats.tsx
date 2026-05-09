"use client";

import { Activity } from "lucide-react";

import { HomelabProgressBar } from "@/components/dashboard/HomelabProgressBar";
import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";
import type { ClusterFetchState } from "@/hooks/useClusterTelemetry";
import type { ClusterNodeTelemetry, ClusterTelemetryResponse } from "@/lib/server/telemetry/types";

interface DashboardDemoV4SystemStatsProps {
  data: ClusterTelemetryResponse | null;
  state: ClusterFetchState;
  error: string | null;
}

function pct(val: number | null): string {
  return val !== null ? `${Math.round(val)}%` : "Unavailable";
}

function fmtMemory(used: number | null, total: number | null): string {
  if (used === null || total === null) return "Unavailable";
  const usedGB = (used / 1e9).toFixed(1);
  const totalGB = Math.round(total / 1e9);
  return `${usedGB} GB / ${totalGB} GB`;
}

function formatUptime(sec: number | null): string {
  if (sec === null) return "Unavailable";
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

function stateBadge(state: ClusterFetchState) {
  if (state === "error") return { variant: "offline" as const, label: "Error" };
  if (state === "checking") return { variant: "pending" as const, label: "Loading" };
  return { variant: "live" as const, label: "Synced" };
}

function NodeVitals({ node }: { node: ClusterNodeTelemetry }) {
  const offline = node.status === "offline" || node.status === "unknown";
  const spec = [node.hostname, node.platform, node.arch].filter(Boolean).join(" · ");
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
    <article className="dashboard-demo-v4-node-card">
      <div className="dashboard-demo-v4-node-card-header">
        <div className="min-w-0">
          <h3>{node.label}</h3>
          <p>{spec || "Node details unavailable"}</p>
        </div>
        <HomelabStatusBadge variant={badgeVariant}>{badgeLabel}</HomelabStatusBadge>
      </div>

      {offline ? (
        <p className="dashboard-demo-v4-empty-copy">
          Offline{node.error ? ` · ${node.error}` : ""}
        </p>
      ) : (
        <div className="dashboard-demo-v4-vitals-list">
          <div className="dashboard-demo-v4-meter">
            <div className="dashboard-demo-v4-meter-label">
              <span>CPU</span>
              <strong>{pct(node.cpu.usagePct)}</strong>
            </div>
            {node.cpu.usagePct !== null ? (
              <HomelabProgressBar
                pct={node.cpu.usagePct}
                variant={cpuVariant(node.cpu.usagePct)}
                label={`${node.label} CPU`}
              />
            ) : null}
          </div>

          <div className="dashboard-demo-v4-meter">
            <div className="dashboard-demo-v4-meter-label">
              <span>RAM</span>
              <strong>{fmtMemory(node.memory.usedBytes, node.memory.totalBytes)}</strong>
            </div>
            {node.memory.usedPct !== null ? (
              <HomelabProgressBar
                pct={node.memory.usedPct}
                variant={ramVariant(node.memory.usedPct)}
                label={`${node.label} RAM`}
              />
            ) : null}
          </div>

          <div className="dashboard-demo-v4-node-detail-row">
            <span>Uptime</span>
            <strong>{formatUptime(node.uptimeSec)}</strong>
          </div>
        </div>
      )}
    </article>
  );
}

export function DashboardDemoV4SystemStats({
  data,
  state,
  error,
}: DashboardDemoV4SystemStatsProps) {
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
    <section aria-label="System stats" className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-card">
      <div className="dashboard-demo-v4-card-header">
        <div className="dashboard-demo-v4-card-title-row">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <Activity className="h-5 w-5" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Node vitals</p>
            <h2>System vitals</h2>
            <p className="dashboard-demo-v4-card-subtitle">
              {state === "checking"
                ? "Polling cluster telemetry"
                : state === "error" && error
                  ? error
                  : syncTime
                    ? `Synced ${syncTime}`
                    : "Live telemetry"}
            </p>
          </div>
        </div>
        <HomelabStatusBadge variant={badge.variant}>{badge.label}</HomelabStatusBadge>
      </div>

      {state === "checking" ? (
        <div className="dashboard-demo-v4-skeleton-grid" aria-label="Loading system vitals">
          <div />
          <div />
        </div>
      ) : null}

      {state !== "checking" && nodes.length === 0 ? (
        <p className="dashboard-demo-v4-empty-copy">
          {state === "error" ? error ?? "Cluster telemetry failed" : "Telemetry not configured"}
        </p>
      ) : null}

      {nodes.length > 0 ? (
        <div className="dashboard-demo-v4-node-grid">
          {nodes.map((node) => (
            <NodeVitals key={node.id} node={node} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
