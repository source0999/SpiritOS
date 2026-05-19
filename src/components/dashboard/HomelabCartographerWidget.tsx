"use client";

import { useEffect, useMemo, useState } from "react";
import { FileText, Flag, LockKeyhole, Map, RadioTower } from "lucide-react";

type CartographerDashboardCard = {
  card_id: string;
  label: string;
  status: string;
  value: string | number | boolean | null;
  detail?: string;
  endpoint: string;
};

type CartographerDashboard = {
  status: "observing" | "unavailable" | string;
  write_actions_enabled: boolean;
  authority_granted?: boolean;
  actions_taken?: boolean;
  dashboard_mode?: string;
  primary_status?: string;
  primary_label?: string;
  v1_ready?: boolean;
  readiness?: string;
  blocker_count?: number;
  freeze_marker_status?: string;
  next_action?: string;
  dashboard_cards: CartographerDashboardCard[];
  error?: string;
};

type FetchState = "loading" | "ready" | "error";

const emptyStatus: CartographerDashboard = {
  status: "unavailable",
  write_actions_enabled: false,
  authority_granted: false,
  actions_taken: false,
  dashboard_cards: [],
};

function formatValue(value: CartographerDashboardCard["value"]): string {
  if (typeof value === "number") return value.toLocaleString();
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return value ? String(value) : "None";
}

function statusLabel(state: FetchState, status: CartographerDashboard): string {
  if (state === "loading") return "Loading";
  if (state === "error" || status.status === "unavailable") return "Unavailable";
  return status.primary_label ?? "Observing";
}

function cardIcon(cardId: string) {
  if (cardId.includes("readiness")) return RadioTower;
  if (cardId.includes("evidence")) return FileText;
  if (cardId.includes("freeze")) return Flag;
  return LockKeyhole;
}

export function HomelabCartographerWidget() {
  const [state, setState] = useState<FetchState>("loading");
  const [status, setStatus] = useState<CartographerDashboard>(emptyStatus);

  useEffect(() => {
    let cancelled = false;

    async function loadStatus() {
      try {
        const response = await fetch("/v1/cartographer/v1-closeout-dashboard", {
          cache: "no-store",
        });
        const payload = (await response.json()) as CartographerDashboard;
        if (cancelled) return;
        setStatus({
          ...emptyStatus,
          ...payload,
          dashboard_cards: Array.isArray(payload.dashboard_cards)
            ? payload.dashboard_cards
            : [],
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
    () =>
      status.dashboard_cards.map((card) => ({
        label: card.label,
        value: formatValue(card.value),
        detail: card.detail,
        icon: cardIcon(card.card_id),
        rawValue: card.value,
      })),
    [status],
  );

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
              <strong title={typeof metric.rawValue === "string" ? metric.rawValue : undefined}>
                {metric.value}
              </strong>
              <span className="dashboard-demo-v4-cartographer-metric-label">{metric.label}</span>
              {metric.detail ? (
                <span className="dashboard-demo-v4-cartographer-metric-detail">
                  {metric.detail}
                </span>
              ) : null}
            </div>
          );
        })}
      </div>

      <div className="dashboard-demo-v4-cartographer-summary">
        {state === "loading" ? (
          <p>Loading Cartographer state.</p>
        ) : state === "ready" ? (
          <p>{status.next_action ?? status.primary_label ?? "Cartographer is observing v1 closeout."}</p>
        ) : (
          <p>{status.error ?? "The Cartographer dashboard rollup is unavailable."}</p>
        )}
        <p className="dashboard-demo-v4-empty-copy">
          Reads the v1 closeout rollup only. Approve, apply, commit, and push controls stay hidden.
        </p>
      </div>
    </section>
  );
}
