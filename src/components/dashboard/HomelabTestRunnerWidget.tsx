"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  FileJson,
  Play,
  ShieldCheck,
  TimerReset,
} from "lucide-react";

type RunnerProfileId =
  | "proxy-smoke"
  | "proxy-regression"
  | "proxy-closeout"
  | "phase-4f-closeout"
  | "scout-smoke"
  | "scout-source-gate"
  | "scout-search-diagnostics"
  | "scout-search-smoke"
  | "scout-soak-snapshot";

type RunnerProfile = {
  id: RunnerProfileId;
  label: string;
  group: "Proxy" | "Scout";
  tone: "read_only" | "bounded" | "snapshot";
  confirm?: string;
};

type RunnerPayload = {
  applied_anything?: boolean;
  checks?: Record<string, { ok?: boolean } | boolean | unknown>;
  mode?: string;
  profile?: string;
  recommendation?: string;
  result?: string;
  timestamp?: string;
  summary?: Record<string, unknown>;
  smoke_harness?: {
    summary?: Record<string, unknown>;
  };
  snapshot_path?: string;
  snapshot?: string;
  mutation_boundary?: Record<string, unknown>;
  read_only_verdict?: Record<string, unknown>;
};

type RunState = "idle" | "running" | "ready" | "error";

const RUNNER_PROFILES: RunnerProfile[] = [
  { id: "proxy-smoke", label: "Proxy Smoke", group: "Proxy", tone: "read_only" },
  { id: "proxy-regression", label: "Proxy Regression", group: "Proxy", tone: "read_only" },
  { id: "proxy-closeout", label: "Proxy Closeout", group: "Proxy", tone: "read_only" },
  {
    id: "phase-4f-closeout",
    label: "4F Closeout",
    group: "Proxy",
    tone: "snapshot",
    confirm:
      "Run Phase 4F closeout? This runs reporting checks and may write one Scout soak snapshot, but it will not approve, apply, commit, or push.",
  },
  { id: "scout-smoke", label: "Scout Smoke", group: "Scout", tone: "read_only" },
  { id: "scout-source-gate", label: "Source Gate", group: "Scout", tone: "read_only" },
  {
    id: "scout-search-diagnostics",
    label: "Search Diagnostics",
    group: "Scout",
    tone: "read_only",
  },
  {
    id: "scout-search-smoke",
    label: "Search Smoke",
    group: "Scout",
    tone: "bounded",
    confirm:
      "Run Scout search smoke? It may create a bounded discovery job and candidate records, but it will not approve or change active sources.",
  },
  {
    id: "scout-soak-snapshot",
    label: "Soak Snapshot",
    group: "Scout",
    tone: "snapshot",
    confirm:
      "Write a Scout soak snapshot under scout/soak-logs? This does not change active sources.",
  },
];

function payloadSummary(payload: RunnerPayload | null): string {
  if (!payload) return "No run yet";
  const profile = payload.profile ?? "runner";
  const result = payload.result ?? "unknown";
  const recommendation = payload.recommendation ?? "no recommendation";
  return `${profile}: ${result} - ${recommendation}`;
}

function payloadMetric(payload: RunnerPayload | null, key: "passed" | "failed" | "skipped"): string {
  const value =
    payload?.summary?.[key] ??
    payload?.smoke_harness?.summary?.[key] ??
    payload?.smoke_harness?.summary?.[key.toUpperCase()];
  if (typeof value === "number") return value.toLocaleString();

  const checks = payload?.checks ? Object.values(payload.checks) : [];
  if (checks.length === 0) return "0";
  const passed = checks.filter(
    (check) =>
      check === true ||
      (typeof check === "object" && check !== null && "ok" in check && check.ok === true),
  ).length;
  const failed = checks.filter(
    (check) =>
      check === false ||
      (typeof check === "object" && check !== null && "ok" in check && check.ok === false),
  ).length;
  if (key === "passed") return passed.toLocaleString();
  if (key === "failed") return failed.toLocaleString();
  return Math.max(0, checks.length - passed - failed).toLocaleString();
}

function profileToneLabel(tone: RunnerProfile["tone"]): string {
  if (tone === "bounded") return "Bounded";
  if (tone === "snapshot") return "Snapshot";
  return "Read-only";
}

function extractError(payload: unknown, status: number): string {
  if (
    typeof payload === "object" &&
    payload !== null &&
    "error" in payload &&
    typeof payload.error === "string"
  ) {
    return payload.error;
  }
  if (
    typeof payload === "object" &&
    payload !== null &&
    "detail" in payload &&
    typeof payload.detail === "object" &&
    payload.detail !== null &&
    "error" in payload.detail &&
    typeof payload.detail.error === "string"
  ) {
    return payload.detail.error;
  }
  return `Runner failed with status ${status}.`;
}

export function HomelabTestRunnerWidget() {
  const [state, setState] = useState<RunState>("idle");
  const [activeProfile, setActiveProfile] = useState<RunnerProfileId | null>(null);
  const [payload, setPayload] = useState<RunnerPayload | null>(null);
  const [error, setError] = useState("");

  const statusLabel = useMemo(() => {
    if (state === "running") return "Running";
    if (state === "error") return "Needs review";
    if (payload?.result === "pass") return "Ready";
    if (payload?.result === "fail") return "Fix needed";
    return "Manual checks";
  }, [payload, state]);

  async function runProfile(profile: RunnerProfile) {
    if (profile.confirm && !window.confirm(profile.confirm)) return;

    setState("running");
    setActiveProfile(profile.id);
    setError("");

    try {
      const response = await fetch("/v1/coding/self-tests/run", {
        body: JSON.stringify({
          mode: "dry_run",
          profile: profile.id,
        }),
        headers: {
          "content-type": "application/json",
        },
        method: "POST",
      });
      const nextPayload = (await response.json()) as RunnerPayload;
      if (!response.ok) {
        throw new Error(extractError(nextPayload, response.status));
      }
      setPayload(nextPayload);
      setState("ready");
    } catch (runError) {
      setState("error");
      setError(runError instanceof Error ? runError.message : "Runner failed.");
    } finally {
      setActiveProfile(null);
    }
  }

  return (
    <section
      aria-label="Manual Checks"
      className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-card dashboard-demo-v4-test-runner-card"
    >
      <div className="dashboard-demo-v4-card-header">
        <div className="dashboard-demo-v4-card-title-row">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <ShieldCheck className="h-5 w-5" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Proxy runner</p>
            <h2>Manual Checks</h2>
          </div>
        </div>
        <span className="dashboard-demo-v4-demo-label">{statusLabel}</span>
      </div>

      <div className="dashboard-demo-v4-test-runner-grid" aria-label="Runner profiles">
        {RUNNER_PROFILES.map((profile) => {
          const isRunning = state === "running" && activeProfile === profile.id;
          return (
            <button
              key={profile.id}
              type="button"
              className="dashboard-demo-v4-test-runner-profile"
              data-tone={profile.tone}
              disabled={state === "running"}
              onClick={() => void runProfile(profile)}
            >
              {isRunning ? (
                <TimerReset className="h-4 w-4" aria-hidden />
              ) : (
                <Play className="h-4 w-4" aria-hidden />
              )}
              <span>
                <strong>{profile.label}</strong>
                <em>
                  {profile.group} / {profileToneLabel(profile.tone)}
                </em>
              </span>
            </button>
          );
        })}
      </div>

      <div className="dashboard-demo-v4-test-runner-summary">
        <div>
          <CheckCircle2 className="h-4 w-4" aria-hidden />
          <strong>{payloadMetric(payload, "passed")}</strong>
          <span>Passed</span>
        </div>
        <div>
          <AlertTriangle className="h-4 w-4" aria-hidden />
          <strong>{payloadMetric(payload, "failed")}</strong>
          <span>Failed</span>
        </div>
        <div>
          <FileJson className="h-4 w-4" aria-hidden />
          <strong>{payloadMetric(payload, "skipped")}</strong>
          <span>Skipped</span>
        </div>
      </div>

      {error ? (
        <p className="dashboard-demo-v4-scout-action-error">{error}</p>
      ) : (
        <p className="dashboard-demo-v4-scout-action-message">{payloadSummary(payload)}</p>
      )}

      {payload ? (
        <pre className="dashboard-demo-v4-test-runner-report" aria-label="Manual check report">
          <code>{JSON.stringify(payload, null, 2)}</code>
        </pre>
      ) : null}
    </section>
  );
}
