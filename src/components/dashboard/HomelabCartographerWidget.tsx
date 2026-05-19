"use client";

import { useEffect, useMemo, useState } from "react";
import {
  FileText,
  Flag,
  Gauge,
  LockKeyhole,
  Map,
  RadioTower,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";

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

type CartographerLevelOneEvidence = {
  level?: number;
  mode?: string;
  authority_granted?: boolean;
  write_actions_enabled?: boolean;
  apply_enabled?: boolean;
  commit_enabled?: boolean;
  push_enabled?: boolean;
  docs_autopilot_daily_cap?: number;
  autopilot_kill_switch?: boolean;
  candidate_count?: number;
  blockers?: string[];
  rollback_hints?: string[];
  operator_review_required?: boolean;
  recommended_next_action?: string;
};

type CartographerLevelTwoContract = {
  level?: number;
  mode?: string;
  contract_version?: string;
  current_readiness?: {
    label?: string;
    docs_apply_enabled?: boolean;
    blocker_count?: number;
    blockers?: string[];
  };
  dirty_tree_summary?: {
    dirty_tree_block?: boolean;
    unclassified_blocker_count?: number;
    blocking_policy?: string;
  };
  required_apply_request_fields?: string[];
  required_receipt_fields?: string[];
  forbidden_actions?: string[];
  manual_checks?: string[];
  expected_output?: string[];
  next_increment?: string;
};

type FetchState = "loading" | "ready" | "error";

const emptyStatus: CartographerDashboard = {
  status: "unavailable",
  write_actions_enabled: false,
  authority_granted: false,
  actions_taken: false,
  dashboard_cards: [],
};

const emptyLevelOneEvidence: CartographerLevelOneEvidence = {
  level: 1,
  mode: "dry_run",
  authority_granted: false,
  write_actions_enabled: false,
  apply_enabled: false,
  commit_enabled: false,
  push_enabled: false,
  candidate_count: 0,
  blockers: [],
  rollback_hints: [],
  operator_review_required: true,
};

const emptyLevelTwoContract: CartographerLevelTwoContract = {
  level: 2,
  mode: "api_contract_review_packet",
  current_readiness: {
    label: "blocked",
    docs_apply_enabled: false,
    blocker_count: 0,
    blockers: [],
  },
  dirty_tree_summary: {
    dirty_tree_block: true,
    unclassified_blocker_count: 0,
  },
  required_apply_request_fields: [],
  required_receipt_fields: [],
  forbidden_actions: [],
  manual_checks: [],
  expected_output: [],
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
  if (cardId.includes("level")) return Gauge;
  if (cardId.includes("readiness")) return RadioTower;
  if (cardId.includes("evidence")) return FileText;
  if (cardId.includes("freeze")) return Flag;
  if (cardId.includes("review")) return ShieldCheck;
  return LockKeyhole;
}

function levelOneLabel(evidence: CartographerLevelOneEvidence): string {
  if (evidence.level !== 1) return "Disabled";
  if (evidence.authority_granted) return "Blocked";
  return "Level 1 candidate";
}

function modeLabel(mode: string | undefined): string {
  if (mode === "dry_run") return "Dry-run only";
  if (mode === "soak") return "Soak evidence";
  return "Dry-run only";
}

function disabledLabel(value: boolean | undefined): string {
  return value ? "Enabled" : "Disabled";
}

function sentencePrefix(value: string): string {
  return value.replace(/[.]\s*$/, "");
}

function blockerLabel(blocker: string | undefined): string {
  return blocker ?? "None";
}

function levelTwoLabel(contract: CartographerLevelTwoContract): string {
  const label = contract.current_readiness?.label ?? "blocked";
  if (label === "ready_for_review") return "Ready for review";
  if (label === "watch") return "Watch";
  return "Blocked";
}

function enabledLabel(value: boolean | undefined): string {
  return value ? "Enabled" : "Disabled";
}

export function HomelabCartographerWidget() {
  const [state, setState] = useState<FetchState>("loading");
  const [status, setStatus] = useState<CartographerDashboard>(emptyStatus);
  const [levelOneEvidence, setLevelOneEvidence] = useState<CartographerLevelOneEvidence>(
    emptyLevelOneEvidence,
  );
  const [levelTwoContract, setLevelTwoContract] = useState<CartographerLevelTwoContract>(
    emptyLevelTwoContract,
  );

  useEffect(() => {
    let cancelled = false;

    async function loadStatus() {
      try {
        const [response, levelOneResponse, levelTwoResponse] = await Promise.all([
          fetch("/v1/cartographer/v1-closeout-dashboard", {
            cache: "no-store",
          }),
          fetch("/v1/cartographer/docs-autopilot/dry-run", {
            cache: "no-store",
          }),
          fetch("/v1/cartographer/level-2-api-contract", {
            cache: "no-store",
          }),
        ]);
        const payload = (await response.json()) as CartographerDashboard;
        const levelOnePayload = (await levelOneResponse.json()) as CartographerLevelOneEvidence;
        const levelTwoPayload = (await levelTwoResponse.json()) as CartographerLevelTwoContract;
        if (cancelled) return;
        setStatus({
          ...emptyStatus,
          ...payload,
          dashboard_cards: Array.isArray(payload.dashboard_cards)
            ? payload.dashboard_cards
            : [],
        });
        setLevelOneEvidence({
          ...emptyLevelOneEvidence,
          ...levelOnePayload,
          blockers: Array.isArray(levelOnePayload.blockers) ? levelOnePayload.blockers : [],
          rollback_hints: Array.isArray(levelOnePayload.rollback_hints)
            ? levelOnePayload.rollback_hints
            : [],
        });
        setLevelTwoContract({
          ...emptyLevelTwoContract,
          ...levelTwoPayload,
          current_readiness: {
            ...emptyLevelTwoContract.current_readiness,
            ...levelTwoPayload.current_readiness,
            blockers: Array.isArray(levelTwoPayload.current_readiness?.blockers)
              ? levelTwoPayload.current_readiness.blockers
              : [],
          },
          dirty_tree_summary: {
            ...emptyLevelTwoContract.dirty_tree_summary,
            ...levelTwoPayload.dirty_tree_summary,
          },
          required_apply_request_fields: Array.isArray(levelTwoPayload.required_apply_request_fields)
            ? levelTwoPayload.required_apply_request_fields
            : [],
          required_receipt_fields: Array.isArray(levelTwoPayload.required_receipt_fields)
            ? levelTwoPayload.required_receipt_fields
            : [],
          forbidden_actions: Array.isArray(levelTwoPayload.forbidden_actions)
            ? levelTwoPayload.forbidden_actions
            : [],
          manual_checks: Array.isArray(levelTwoPayload.manual_checks)
            ? levelTwoPayload.manual_checks
            : [],
          expected_output: Array.isArray(levelTwoPayload.expected_output)
            ? levelTwoPayload.expected_output
            : [],
        });
        setState(response.ok && payload.status !== "unavailable" ? "ready" : "error");
      } catch {
        if (cancelled) return;
        setStatus(emptyStatus);
        setLevelOneEvidence(emptyLevelOneEvidence);
        setLevelTwoContract(emptyLevelTwoContract);
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
      [
        {
          label: "Autonomy level",
          value: levelOneLabel(levelOneEvidence),
          detail: modeLabel(levelOneEvidence.mode),
          icon: cardIcon("level-one"),
          rawValue: levelOneLabel(levelOneEvidence),
        },
        {
          label: "Kill switch",
          value: levelOneEvidence.autopilot_kill_switch ? "On" : "Off",
          detail: `Daily cap ${levelOneEvidence.docs_autopilot_daily_cap ?? 0}`,
          icon: cardIcon("authority"),
          rawValue: levelOneEvidence.autopilot_kill_switch ? "On" : "Off",
        },
        {
          label: "Review",
          value: levelOneEvidence.operator_review_required ? "Required" : "Missing",
          detail: `${levelOneEvidence.candidate_count ?? 0} proposals`,
          icon: cardIcon("review"),
          rawValue: levelOneEvidence.operator_review_required ? "Required" : "Missing",
        },
        {
          label: "Apply / commit / push",
          value: [
            disabledLabel(levelOneEvidence.apply_enabled),
            disabledLabel(levelOneEvidence.commit_enabled),
            disabledLabel(levelOneEvidence.push_enabled),
          ].join(" / "),
          detail: "No execution controls",
          icon: cardIcon("authority"),
          rawValue: "disabled",
        },
        ...status.dashboard_cards.map((card) => ({
          label: card.label,
          value: formatValue(card.value),
          detail: card.detail,
          icon: cardIcon(card.card_id),
          rawValue: card.value,
        })),
      ],
    [levelOneEvidence, status],
  );

  const latestBlocker = levelOneEvidence.blockers?.[0];
  const lastEvidence = levelOneEvidence.rollback_hints?.[0] ?? "No files written";
  const nextSafeAction = latestBlocker ?? levelOneEvidence.recommended_next_action ?? "operator_review_required";
  const levelTwoBlocker = levelTwoContract.current_readiness?.blockers?.[0];
  const dirtyBlockerCount = levelTwoContract.dirty_tree_summary?.unclassified_blocker_count ?? 0;
  const manualCheck = levelTwoContract.manual_checks?.[0] ?? "git status -sb";
  const receiptFieldCount = levelTwoContract.required_receipt_fields?.length ?? 0;

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
          <p>{nextSafeAction}</p>
        ) : (
          <p>{status.error ?? "The Cartographer dashboard rollup is unavailable."}</p>
        )}
        <p className="dashboard-demo-v4-empty-copy">
          {sentencePrefix(lastEvidence)}. Approve, apply, commit, and push controls stay hidden.
        </p>
      </div>

      <div
        className="dashboard-demo-v4-cartographer-level-two"
        aria-label="Level 2 human-approved docs apply"
      >
        <div className="dashboard-demo-v4-cartographer-level-two-heading">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <ShieldCheck className="h-4 w-4" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Level 2</p>
            <h3>Human-approved docs apply</h3>
          </div>
          <strong>{levelTwoLabel(levelTwoContract)}</strong>
        </div>
        <div className="dashboard-demo-v4-cartographer-level-two-grid">
          <div>
            <span>Status</span>
            <strong>{levelTwoContract.current_readiness?.label ?? "blocked"}</strong>
          </div>
          <div>
            <span>Apply</span>
            <strong>{enabledLabel(levelTwoContract.current_readiness?.docs_apply_enabled)}</strong>
          </div>
          <div>
            <span>Dirty blockers</span>
            <strong>{dirtyBlockerCount}</strong>
          </div>
          <div>
            <span>Receipt fields</span>
            <strong>{receiptFieldCount}</strong>
          </div>
        </div>
        <div className="dashboard-demo-v4-cartographer-level-two-lines">
          <p>
            <LockKeyhole className="h-4 w-4" aria-hidden />
            Commit disabled. Push disabled. Source edits disabled.
          </p>
          <p>
            <RotateCcw className="h-4 w-4" aria-hidden />
            Rollback instructions are required in every approved proposal.
          </p>
          <p>
            <FileText className="h-4 w-4" aria-hidden />
            Manual check: {manualCheck}
          </p>
        </div>
        <p className="dashboard-demo-v4-empty-copy">
          Blocker: {blockerLabel(levelTwoBlocker)}. No Level 2 execution control is exposed here.
        </p>
      </div>

      <div
        className="dashboard-demo-v4-cartographer-mobile-review"
        aria-label="Level 1 mobile review"
      >
        <div>
          <span>Status</span>
          <strong>{levelOneLabel(levelOneEvidence)}</strong>
        </div>
        <div>
          <span>Blocker</span>
          <strong>{blockerLabel(latestBlocker)}</strong>
        </div>
        <div>
          <span>Next</span>
          <strong>{nextSafeAction}</strong>
        </div>
        <div>
          <span>Evidence</span>
          <strong>{sentencePrefix(lastEvidence)}</strong>
        </div>
      </div>
    </section>
  );
}
