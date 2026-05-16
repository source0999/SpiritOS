"use client";

import { useEffect, useMemo, useState } from "react";
import { FileText, FolderGit2, LockKeyhole, Map, RadioTower } from "lucide-react";

type CartographerProject = {
  project_id: string;
  name: string;
  root: string;
  markers: string[];
  status: string;
  write_policy: string;
};

type CartographerStatus = {
  status: "observing" | "unavailable" | string;
  write_actions_enabled: boolean;
  configured_roots: unknown[];
  blocked_roots: unknown[];
  projects: CartographerProject[];
  blueprint_count: number;
  pending_proposals: number;
  error?: string;
};

type FetchState = "loading" | "ready" | "error";

const emptyStatus: CartographerStatus = {
  status: "unavailable",
  write_actions_enabled: false,
  configured_roots: [],
  blocked_roots: [],
  projects: [],
  blueprint_count: 0,
  pending_proposals: 0,
};

function formatNumber(value: number | undefined): string {
  return typeof value === "number" ? value.toLocaleString() : "0";
}

function statusLabel(state: FetchState, status: CartographerStatus): string {
  if (state === "loading") return "Loading";
  if (state === "error" || status.status === "unavailable") return "Unavailable";
  return "Observing";
}

export function HomelabCartographerWidget() {
  const [state, setState] = useState<FetchState>("loading");
  const [status, setStatus] = useState<CartographerStatus>(emptyStatus);

  useEffect(() => {
    let cancelled = false;

    async function loadStatus() {
      try {
        const response = await fetch("/v1/cartographer/status", {
          cache: "no-store",
        });
        const payload = (await response.json()) as CartographerStatus;
        if (cancelled) return;
        setStatus({
          ...emptyStatus,
          ...payload,
          projects: Array.isArray(payload.projects) ? payload.projects : [],
          configured_roots: Array.isArray(payload.configured_roots)
            ? payload.configured_roots
            : [],
          blocked_roots: Array.isArray(payload.blocked_roots) ? payload.blocked_roots : [],
        });
        setState(response.ok && payload.status !== "unavailable" ? "ready" : "error");
      } catch {
        if (cancelled) return;
        setStatus(emptyStatus);
        setState("error");
      }
    }

    void loadStatus();

    return () => {
      cancelled = true;
    };
  }, []);

  const metrics = useMemo(
    () => [
      {
        label: "Projects Detected",
        value: formatNumber(status.projects.length),
        icon: FolderGit2,
      },
      {
        label: "Blueprints Indexed",
        value: formatNumber(status.blueprint_count),
        icon: FileText,
      },
      {
        label: "Pending Proposals",
        value: formatNumber(status.pending_proposals),
        icon: RadioTower,
      },
      {
        label: "Write Mode",
        value: status.write_actions_enabled ? "Open" : "Locked",
        icon: LockKeyhole,
      },
    ],
    [status],
  );

  const primaryProject = status.projects[0];

  return (
    <section
      aria-label="Spirit Cartographer"
      className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-cartographer-card"
    >
      <div className="dashboard-demo-v4-card-header">
        <div className="dashboard-demo-v4-card-title-row">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <Map className="h-5 w-5" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Blueprint system</p>
            <h2>Spirit Cartographer</h2>
          </div>
        </div>
        <span className="dashboard-demo-v4-demo-label">
          {statusLabel(state, status)}
        </span>
      </div>

      <div className="dashboard-demo-v4-cartographer-grid" aria-label="Cartographer status">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <div key={metric.label} className="dashboard-demo-v4-cartographer-metric">
              <Icon className="h-4 w-4" aria-hidden />
              <strong>{metric.value}</strong>
              <span>{metric.label}</span>
            </div>
          );
        })}
      </div>

      <div className="dashboard-demo-v4-cartographer-summary">
        {state === "loading" ? (
          <p>Loading Cartographer state.</p>
        ) : primaryProject ? (
          <p>
            {primaryProject.name} is detected from{" "}
            {primaryProject.markers.slice(0, 4).join(", ")}.
          </p>
        ) : (
          <p>{status.error ?? "No allowlisted projects detected yet."}</p>
        )}
        <p className="dashboard-demo-v4-empty-copy">
          Reads only from allowlisted roots. Approve, apply, commit, and push controls stay hidden.
        </p>
      </div>
    </section>
  );
}
