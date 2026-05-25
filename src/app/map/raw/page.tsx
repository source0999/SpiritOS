import { headers } from "next/headers";
import type { ReactNode } from "react";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import { getCartographerApprovalTokenStatus } from "../cartographer-approval-token";
import { getCartographerLiveState } from "../cartographer-live-state";
import { getCartographerQueueStatus } from "../cartographer-queue-status";
import { getCartographerReceiptEvidenceStatus } from "../cartographer-receipt-evidence";
import { cartographerStopControlStatus } from "../cartographer-stop-controls";
import { getCartographerWorkflowStatus } from "../cartographer-workflow-status";
import {
  humanApprovalBlockedStates,
  humanApprovalFallbackProof,
  humanApprovalPacketShape,
  humanApprovalRequiredFields,
  humanApprovedOperatorForbiddenActions,
  humanApprovedOperatorRecommendationPacket,
  humanApprovedOperatorStatusChips,
} from "../human-approved-operator-data";
import {
  blockedActionClasses,
  getReadOnlyMapData,
} from "../read-only-map-data";
import "@/styles/dashboard-demo-v4.css";

const manualChecks = [
  "cd /home/source/SpiritOS",
  "npm test -- run src/app/map/__tests__/map-information-architecture.test.ts src/app/map/__tests__/map-display-shell.test.ts",
  "npm run typecheck",
  "npm run build",
  "git diff --check",
  "git status --branch --short -- src/app/map/page.tsx src/app/map/map-information-architecture.ts src/app/map/__tests__/map-information-architecture.test.ts src/app/map/__tests__/map-display-shell.test.ts",
] as const;

const closeoutAuthorityDenials = [
  "Full auto is not granted.",
  "Limited unattended operation is not granted.",
  "Approval creation and self-approval are blocked.",
  "Queue execution and workflow execution are blocked.",
  "Shell commands through Cartographer are blocked.",
  "Commit, push, merge, branch, worktree, stash, checkout, clean, and delete are blocked.",
  "/coding, Source Proxy runtime, package/config, Scout, and generated-file mutation are blocked.",
] as const;

const requiredProofItems = [
  "Exact current HEAD and dirty-tree state",
  "Protected-lane review",
  "Approval-token validation result",
  "Queue and workflow blocked-state review",
  "Kill switch state review",
  "Rollback and verification instructions",
] as const;

type Tone = "good" | "warn" | "stop" | "quiet";

function toneClasses(tone: Tone): string {
  if (tone === "good") {
    return "border-emerald-500/30 bg-emerald-50 text-emerald-950";
  }
  if (tone === "warn") {
    return "border-amber-500/35 bg-amber-50 text-amber-950";
  }
  if (tone === "stop") {
    return "border-rose-500/35 bg-rose-50 text-rose-950";
  }
  return "border-stone-300 bg-stone-50 text-stone-800";
}

function statusTone(value: string | null | undefined): Tone {
  if (!value || value === "unknown" || value === "unavailable") {
    return "quiet";
  }
  if (value === "clear" || value === "live" || value === "clean") {
    return "good";
  }
  if (value === "blocked") {
    return "stop";
  }
  return "warn";
}

function Card({
  title,
  kicker,
  children,
  className = "",
}: {
  title: string;
  kicker?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-[#b9aa94] bg-[#fff8ec] p-5 shadow-[0_2px_0_rgba(72,52,32,0.08),0_16px_34px_rgba(72,52,32,0.16)] ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          {kicker ? (
            <p className="mb-1 text-xs font-medium text-stone-500">{kicker}</p>
          ) : null}
          <h2 className="text-lg font-semibold text-stone-950">{title}</h2>
        </div>
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Pill({
  label,
  value,
  tone = "quiet",
}: {
  label: string;
  value: ReactNode;
  tone?: Tone;
}) {
  return (
    <div
      className={`min-w-0 rounded-lg border px-3 py-2 ${toneClasses(tone)}`}
    >
      <p className="text-xs font-medium opacity-70">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold leading-5">{value}</p>
    </div>
  );
}

function StatLine({
  label,
  value,
  tone = "quiet",
}: {
  label: string;
  value: ReactNode;
  tone?: Tone;
}) {
  return (
    <div className="flex flex-col gap-2 border-b border-stone-100 py-2 last:border-b-0 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
      <dt className="text-sm text-stone-600">{label}</dt>
      <dd
        className={`w-full rounded-md border px-2 py-1 text-left text-sm font-medium leading-5 break-words sm:w-auto sm:max-w-[65%] sm:text-right ${toneClasses(tone)}`}
      >
        {value}
      </dd>
    </div>
  );
}

function ShortList({
  items,
  empty,
  limit = 6,
}: {
  items: readonly string[];
  empty: string;
  limit?: number;
}) {
  const visibleItems = items.slice(0, limit);
  const hiddenCount = Math.max(items.length - visibleItems.length, 0);

  if (visibleItems.length === 0) {
    return <p className="text-sm leading-6 text-stone-600">{empty}</p>;
  }

  return (
    <div className="space-y-2">
      <ul className="space-y-2 text-sm leading-6 text-stone-700">
        {visibleItems.map((item) => (
          <li className="break-all rounded-md bg-stone-50 px-3 py-2" key={item}>
            {item}
          </li>
        ))}
      </ul>
      {hiddenCount > 0 ? (
        <p className="text-xs text-stone-500">+{hiddenCount} more not shown</p>
      ) : null}
    </div>
  );
}

function DisabledBadge({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex min-w-0 rounded-lg border border-stone-300 bg-stone-100 px-3 py-2 text-sm font-semibold leading-5 text-stone-700">
      {children}
    </span>
  );
}

function ReadinessCard({
  title,
  state,
  detail,
  tone = "warn",
}: {
  title: string;
  state: string;
  detail: string;
  tone?: Tone;
}) {
  return (
    <article className={`rounded-lg border p-4 ${toneClasses(tone)}`}>
      <p className="text-xs font-medium opacity-70">Review-only</p>
      <h3 className="mt-1 text-base font-semibold">{title}</h3>
      <p className="mt-3 text-sm font-semibold">{state}</p>
      <p className="mt-2 text-sm leading-6 opacity-80">{detail}</p>
    </article>
  );
}

function SectionGroup({
  title,
  summary,
  children,
}: {
  title: string;
  summary: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-xl font-semibold text-stone-950">{title}</h2>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-stone-600">
          {summary}
        </p>
      </div>
      {children}
    </section>
  );
}

function protocolForReadOnlyOrigin(
  host: string | null,
  forwardedProtocol: string | null,
): "http" | "https" {
  if (forwardedProtocol === "http" || forwardedProtocol === "https") {
    return forwardedProtocol;
  }

  if (!host) {
    return "https";
  }

  const hostname = host.split(":")[0] ?? host;
  if (isLocalDevHost(hostname)) {
    return "https";
  }

  return "http";
}

function isLocalDevHost(hostname: string): boolean {
  return (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "::1" ||
    hostname === "0.0.0.0" ||
    hostname.startsWith("10.") ||
    hostname.startsWith("192.168.") ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)
  );
}

export default async function CartographerMapPage() {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host");
  const forwardedProtocol = requestHeaders.get("x-forwarded-proto");
  const protocol = protocolForReadOnlyOrigin(host, forwardedProtocol);
  const origin = host ? `${protocol}://${host}` : null;
  const [
    readOnlyMapData,
    cartographerLiveState,
    cartographerApprovalTokenStatus,
    cartographerQueueStatus,
    cartographerWorkflowStatus,
    cartographerReceiptEvidenceStatus,
  ] = await Promise.all([
    getReadOnlyMapData(origin),
    getCartographerLiveState(origin),
    getCartographerApprovalTokenStatus(origin),
    getCartographerQueueStatus(origin),
    getCartographerWorkflowStatus(origin),
    getCartographerReceiptEvidenceStatus(origin),
  ]);

  const trackedDirtyCount = cartographerLiveState.trackedDirtyFiles.length;
  const untrackedCount = cartographerLiveState.untrackedFiles.length;
  const dirtyFileCount = trackedDirtyCount + untrackedCount;
  const liveCartographerDataAvailable =
    readOnlyMapData.mode === "read-only-live" && cartographerLiveState.available;
  const liveEndpointCount = readOnlyMapData.endpoints.filter(
    (endpoint) => endpoint.state === "live",
  ).length;
  const fallbackEndpointCount = readOnlyMapData.endpoints.length - liveEndpointCount;
  const repoMapSource = readOnlyMapData.endpoints.find(
    (endpoint) => endpoint.endpoint === "/v1/cartographer/repo-map",
  );
  const subCartographerSource = readOnlyMapData.endpoints.find(
    (endpoint) => endpoint.endpoint === "/v1/cartographer/sub-cartographers",
  );
  const trustScoreSource = readOnlyMapData.endpoints.find(
    (endpoint) => endpoint.endpoint === "/v1/cartographer/trust-score",
  );
  const auditTrailSource = readOnlyMapData.endpoints.find(
    (endpoint) => endpoint.endpoint === "/v1/cartographer/audit-trail",
  );
  const canCartAct =
    cartographerApprovalTokenStatus.authorityGranted ||
    cartographerQueueStatus.executionAvailable ||
    cartographerWorkflowStatus.executionAvailable;
  const protectedLaneSummary =
    cartographerLiveState.protectedLaneMatches.length > 0
      ? `${cartographerLiveState.protectedLaneMatches.length} match(es) need review`
      : "no protected-lane matches reported";
  const missingProofItems = [
    !cartographerApprovalTokenStatus.accepted
      ? "accepted human approval token"
      : null,
    "clear kill switch state",
    dirtyFileCount > 0 ? "clean or reviewed dirty-tree expectation" : null,
    cartographerWorkflowStatus.blockedStepCount > 0
      ? "resolved workflow blockers"
      : null,
  ].filter((item): item is string => item !== null);

  return (
    <div className="dashboard-demo-v4-route-shell dashboard-demo-v4-route-shell-map">
      <main className="dashboard-demo-v4-route-main min-h-screen bg-[#e5d8c5] px-4 pb-[var(--shell-mobile-bottom-reserved-height)] pt-4 text-stone-950 sm:px-5 lg:!pl-[calc(var(--ddv4-app-rail-width,12.5rem)+1.25rem)] lg:pb-8 lg:pr-6 lg:pt-5">
        <div className="mx-auto flex w-full max-w-none flex-col gap-4">
          <header className="rounded-lg border border-[#b9aa94] bg-[#fff8ec] p-5 shadow-[0_2px_0_rgba(72,52,32,0.08),0_12px_26px_rgba(72,52,32,0.13)]">
            <div className="grid gap-5 xl:grid-cols-[minmax(380px,1fr)_minmax(560px,1.55fr)] xl:items-end">
              <div>
                <p className="text-sm font-medium text-stone-500">/map/raw</p>
                <p className="mt-1 inline-flex rounded-full border border-stone-300 bg-stone-50 px-3 py-1 text-xs font-semibold text-stone-800">
                  Raw backend view
                </p>
                <h1 className="mt-1 text-3xl font-semibold text-stone-950 sm:text-4xl">
                  Cartographer Command Center
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600 sm:text-base">
                  Plain-English review surface for what Cartographer sees, what
                  is blocked, and what Britton must approve manually.
                </p>
                <a
                  className="mt-4 inline-flex rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm font-semibold text-stone-900"
                  href="/map"
                >
                  Back to simple controller
                </a>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
                <Pill
                  label="Default"
                  tone="stop"
                  value="NO-GO"
                />
                <Pill
                  label="Live state"
                  tone={statusTone(cartographerLiveState.recommendedSafetyState)}
                  value={cartographerLiveState.recommendedSafetyState}
                />
                <Pill
                  label="Dirty files"
                  tone={dirtyFileCount > 0 ? "warn" : "good"}
                  value={`${dirtyFileCount} total`}
                />
                <Pill
                  label="Approval"
                  tone={cartographerApprovalTokenStatus.accepted ? "warn" : "stop"}
                  value={cartographerApprovalTokenStatus.validationStatus}
                />
                <Pill
                  label="Authority"
                  tone={canCartAct ? "stop" : "quiet"}
                  value={canCartAct ? "reported; blocked here" : "display only"}
                />
                <Pill
                  label="Read-only"
                  tone={liveEndpointCount > 0 ? "good" : "warn"}
                  value={`${liveEndpointCount}/${readOnlyMapData.endpoints.length} live`}
                />
              </div>
            </div>
          </header>

          {!liveCartographerDataAvailable ? (
            <div className="rounded-lg border border-amber-500 bg-[#fff1b8] px-4 py-3 text-sm font-semibold text-amber-950 shadow-[0_8px_20px_rgba(120,78,0,0.14)]">
              Live Cartographer data is unavailable. Showing safe fallback
              state.
            </div>
          ) : null}

          <section className="grid gap-5 xl:grid-cols-[1fr_1fr_1.15fr]">
            <Card title="Today's Status" kicker="Default: no-go">
              <p className="text-base leading-7 text-stone-700">
                Cartographer is visible for review only. A green light must be
                explicit, scoped, dated, and manually approved by Britton.
              </p>
              <p className="mt-3 text-sm leading-6 text-stone-600">
                /map remains display-only, does not add runtime authority, and
                Cart can show status only.
              </p>
              <dl className="mt-4">
                <StatLine label="Default decision" tone="stop" value="NO-GO" />
                <StatLine
                  label="Green light"
                  tone="warn"
                  value="manual, scoped, dated"
                />
                <StatLine
                  label="Autonomy"
                  tone="stop"
                  value="not granted"
                />
              </dl>
            </Card>

            <Card title="What Cartographer Is Doing">
              <p className="text-base leading-7 text-stone-700">
                {cartographerLiveState.available
                  ? "Reading live repository state for display."
                  : "Live repository state is unavailable; fallback text is shown."}
              </p>
              <dl className="mt-4">
                <StatLine
                  label="Branch"
                  value={cartographerLiveState.currentBranch ?? "unknown"}
                />
                <StatLine
                  label="HEAD"
                  value={cartographerLiveState.currentHead ?? "unknown"}
                />
                <StatLine
                  label="Dirty state"
                  tone={dirtyFileCount > 0 ? "warn" : "good"}
                  value={`${trackedDirtyCount} tracked, ${untrackedCount} untracked`}
                />
                <StatLine
                  label="Repo map source"
                  tone={repoMapSource?.state === "live" ? "good" : "warn"}
                  value={repoMapSource?.state ?? "fallback"}
                />
                <StatLine
                  label="Protected lanes"
                  tone={
                    cartographerLiveState.protectedLaneMatches.length > 0
                      ? "warn"
                      : "quiet"
                  }
                  value={protectedLaneSummary}
                />
              </dl>
            </Card>

            <Card title="What Needs Britton">
              <p className="text-base leading-7 text-stone-700">
                Review blockers, confirm proof, and manually decide whether a
                later phase may proceed. This page cannot approve anything.
              </p>
              <dl>
                <StatLine
                  label="Approval token"
                  tone={cartographerApprovalTokenStatus.accepted ? "warn" : "stop"}
                  value={cartographerApprovalTokenStatus.validationStatus}
                />
                <StatLine
                  label="Queue execution"
                  tone={cartographerQueueStatus.executionAvailable ? "stop" : "quiet"}
                  value={cartographerQueueStatus.executionAvailable ? "reported available" : "blocked here"}
                />
                <StatLine
                  label="Safe next action"
                  tone="warn"
                  value="manual review"
                />
              </dl>
            </Card>
          </section>

          <SectionGroup
            title="Operational Review Lanes"
            summary="Read the blockers, approval token, queue, workflow, stop state, and evidence without running anything."
          >
            <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
              <Card title="Live Read-Only Packet" kicker="Phase 2 display wiring">
                <p className="text-base leading-7 text-stone-700">
                  {readOnlyMapData.summary}
                </p>
                <dl className="mt-4">
                  <StatLine
                    label="Packet mode"
                    tone={readOnlyMapData.mode === "read-only-live" ? "good" : "warn"}
                    value={readOnlyMapData.mode}
                  />
                  <StatLine
                    label="Fallback state"
                    tone={
                      readOnlyMapData.recommendationPacket.fallback_state === "none"
                        ? "good"
                        : "warn"
                    }
                    value={readOnlyMapData.recommendationPacket.fallback_state}
                  />
                  <StatLine
                    label="Live sources"
                    tone={liveEndpointCount > 0 ? "good" : "warn"}
                    value={`${liveEndpointCount} live, ${fallbackEndpointCount} fallback`}
                  />
                  <StatLine
                    label="Timeout"
                    value={`${readOnlyMapData.timeoutMs}ms per source`}
                  />
                </dl>
                <div className="mt-4">
                  <ShortList
                    empty="No fallback proof reported."
                    items={readOnlyMapData.fallbackProof}
                    limit={4}
                  />
                </div>
              </Card>

              <Card title="Read-Only Sources" kicker="Six endpoint status">
                <p className="text-base leading-7 text-stone-700">
                  These six sources are read with GET only. A live source can
                  inform the review cockpit, but it cannot approve, write, run,
                  queue, commit, push, or grant autonomy.
                </p>
                <div className="mt-4 grid gap-2">
                  {readOnlyMapData.endpoints.map((endpoint) => (
                    <div
                      className={`rounded-lg border px-3 py-2 ${toneClasses(
                        endpoint.state === "live" ? "good" : "warn",
                      )}`}
                      key={endpoint.endpoint}
                    >
                      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                        <p className="text-sm font-semibold">{endpoint.label}</p>
                        <p className="text-xs font-medium">
                          {endpoint.state === "live"
                            ? `HTTP ${endpoint.statusCode ?? "ok"}`
                            : endpoint.failureKind}
                        </p>
                      </div>
                      <p className="mt-1 text-xs leading-5 opacity-75">
                        {endpoint.displayPurpose}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
              <Card title="Sub-Agents / Sub-Cartographers" kicker="Read-only lane">
                <p className="text-base leading-7 text-stone-700">
                  Sub-cartographer data is shown only as a display lane. No
                  worker is started, selected, retried, paused, or assigned from
                  this page.
                </p>
                <dl className="mt-4">
                  <StatLine
                    label="Sub-cartographers"
                    tone={subCartographerSource?.state === "live" ? "good" : "warn"}
                    value={subCartographerSource?.state ?? "fallback"}
                  />
                  <StatLine
                    label="Trust signal"
                    tone={trustScoreSource?.state === "live" ? "good" : "warn"}
                    value={trustScoreSource?.state ?? "fallback"}
                  />
                  <StatLine
                    label="Audit trail"
                    tone={auditTrailSource?.state === "live" ? "warn" : "quiet"}
                    value={
                      auditTrailSource?.riskyReadOnly
                        ? `${auditTrailSource.state}; risky read-only`
                        : (auditTrailSource?.state ?? "fallback")
                    }
                  />
                </dl>
                <div className="mt-4">
                  <ShortList
                    empty="No sub-cartographer display summary is available."
                    items={
                      subCartographerSource?.sourceSummary ?? [
                        "Sub-cartographer source is unavailable; fallback remains active.",
                      ]
                    }
                    limit={8}
                  />
                </div>
              </Card>

              <Card title="Trust / Audit Summary" kicker="Display-only signals">
                <p className="text-base leading-7 text-stone-700">
                  Trust score and audit trail are advisory review signals. They
                  never change authority, approval, queue, or write state from
                  this page.
                </p>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div>
                    <h3 className="text-sm font-semibold text-stone-950">
                      Trust score
                    </h3>
                    <div className="mt-2">
                      <ShortList
                        empty="No trust-score display summary is available."
                        items={
                          trustScoreSource?.sourceSummary ?? [
                            "Trust source is unavailable; fallback remains active.",
                          ]
                        }
                        limit={6}
                      />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-stone-950">
                      Audit trail
                    </h3>
                    <div className="mt-2">
                      <ShortList
                        empty="No audit-trail display summary is available."
                        items={
                          auditTrailSource?.sourceSummary ?? [
                            "Audit source is unavailable; fallback remains active.",
                          ]
                        }
                        limit={6}
                      />
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr_1fr]">
              <Card title="What Is Blocked">
                <ShortList
                  empty="No blocked action classes reported."
                  items={blockedActionClasses}
                  limit={7}
                />
                <p className="mt-4 text-sm leading-6 text-stone-600">
                  Displaying a blocked action is not approval to perform it.
                </p>
              </Card>

              <Card title="Approval/Token State">
                <dl>
                  <StatLine
                    label="Runtime"
                    tone={cartographerApprovalTokenStatus.available ? "warn" : "stop"}
                    value={cartographerApprovalTokenStatus.runtimeStatus}
                  />
                  <StatLine
                    label="Validation"
                    tone={cartographerApprovalTokenStatus.accepted ? "warn" : "stop"}
                    value={cartographerApprovalTokenStatus.validationStatus}
                  />
                  <StatLine
                    label="Consumption preview"
                    tone={cartographerApprovalTokenStatus.consumptionEligible ? "warn" : "stop"}
                    value={cartographerApprovalTokenStatus.consumptionStatus}
                  />
                  <StatLine
                    label="Self-approval"
                    tone={cartographerApprovalTokenStatus.selfApprovalAllowed ? "stop" : "good"}
                    value={cartographerApprovalTokenStatus.selfApprovalAllowed ? "reported allowed" : "blocked"}
                  />
                </dl>
                <ShortList
                  empty="No token blocked reasons reported."
                  items={[
                    ...cartographerApprovalTokenStatus.reasons,
                    ...cartographerApprovalTokenStatus.consumptionReasons,
                  ]}
                  limit={4}
                />
              </Card>

              <Card title="Queue/Workflow State">
                <dl>
                  <StatLine label="Queue" value={cartographerQueueStatus.queueStatus} />
                  <StatLine label="Run-next" value={cartographerQueueStatus.runNextStatus} />
                  <StatLine
                    label="Workflow"
                    value={cartographerWorkflowStatus.workflowStatus}
                  />
                  <StatLine
                    label="Blocked steps"
                    tone={cartographerWorkflowStatus.blockedStepCount > 0 ? "warn" : "quiet"}
                    value={cartographerWorkflowStatus.blockedStepCount}
                  />
                </dl>
                <p className="mt-4 text-sm leading-6 text-stone-600">
                  Queue and workflow data are review-only. /map does not run the
                  next item, start a workflow, retry, pause, or cancel.
                </p>
              </Card>
            </div>

            <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
              <Card title="Kill Switch/Stop State">
                <dl>
                  <StatLine
                    label="Kill switch"
                    tone="stop"
                    value={cartographerStopControlStatus.killSwitchState}
                  />
                  <StatLine
                    label="Executable controls"
                    tone={cartographerStopControlStatus.executableControlsAvailable ? "stop" : "good"}
                    value={cartographerStopControlStatus.executableControlsAvailable ? "reported available" : "not wired"}
                  />
                  <StatLine
                    label="Durable writes"
                    tone={cartographerStopControlStatus.durableWriteAvailable ? "stop" : "good"}
                    value={cartographerStopControlStatus.durableWriteAvailable ? "reported available" : "blocked"}
                  />
                </dl>
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  {cartographerStopControlStatus.controls.map((control) => (
                    <DisabledBadge key={control.id}>
                      {control.label}: {control.status}
                    </DisabledBadge>
                  ))}
                </div>
              </Card>

              <Card title="Evidence/Receipts">
                <dl>
                  <StatLine
                    label="Receipt journal"
                    value={cartographerReceiptEvidenceStatus.receiptJournalStatus}
                  />
                  <StatLine
                    label="Evidence artifacts"
                    value={cartographerReceiptEvidenceStatus.evidenceArtifactCount}
                  />
                  <StatLine
                    label="Receipt writes"
                    tone={cartographerReceiptEvidenceStatus.receiptJournalWriteAllowed ? "stop" : "good"}
                    value={cartographerReceiptEvidenceStatus.receiptJournalWriteAllowed ? "reported allowed" : "blocked"}
                  />
                </dl>
                <ShortList
                  empty="No existing evidence items reported."
                  items={cartographerReceiptEvidenceStatus.evidenceItems.map(
                    (item) => `${item.label}: ${item.status}`,
                  )}
                  limit={5}
                />
              </Card>
            </div>
          </SectionGroup>

          <SectionGroup
            title="Decision Packet"
            summary="Everything here defaults to NO-GO until Britton makes an explicit, scoped manual decision."
          >
            <Card title="Review-Only Readiness">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <ReadinessCard
                  title="Commit readiness"
                  state={dirtyFileCount > 0 ? "needs manual review" : "no dirty files reported"}
                  detail="No commit button exists. A commit would require separate explicit approval."
                  tone={dirtyFileCount > 0 ? "warn" : "quiet"}
                />
                <ReadinessCard
                  title="Push readiness"
                  state="not wired yet"
                  detail="Remote/ahead/behind is not trusted here. Push remains separately blocked."
                />
                <ReadinessCard
                  title="Merge readiness"
                  state="not wired yet"
                  detail="No merge path, branch operation, or protected-lane mutation is available from /map."
                  tone="stop"
                />
                <ReadinessCard
                  title="Queue readiness"
                  state={cartographerQueueStatus.selectionAvailable ? "ready for manual review" : "blocked"}
                  detail="Selection can be displayed when reported; execution remains blocked here."
                />
                <ReadinessCard
                  title="Approval readiness"
                  state={cartographerApprovalTokenStatus.accepted ? "needs human confirmation" : "blocked"}
                  detail="Validation display cannot mint, record, consume, or self-approve a token."
                  tone={cartographerApprovalTokenStatus.accepted ? "warn" : "stop"}
                />
                <ReadinessCard
                  title="Preflight readiness"
                  state={cartographerLiveState.recommendedSafetyState}
                  detail={cartographerLiveState.safeNextAction}
                  tone={statusTone(cartographerLiveState.recommendedSafetyState)}
                />
                <ReadinessCard
                  title="Kill switch status"
                  state={cartographerStopControlStatus.killSwitchState}
                  detail={cartographerStopControlStatus.safeNextAction}
                  tone="stop"
                />
                <ReadinessCard
                  title="Autonomy readiness"
                  state="NO-GO"
                  detail="Limited unattended operation and full auto are not granted in this phase."
                  tone="stop"
                />
              </div>
            </Card>

            <Card title="Human-Approved Operator" kicker="Plan 2 display-only">
              <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
                <div>
                  <p className="text-base leading-7 text-stone-700">
                    Plan 2 can show what a human-approved operator packet would
                    require, but this page does not create, store, validate,
                    consume, or record approval tokens.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {humanApprovedOperatorStatusChips.map((chip) => (
                      <DisabledBadge key={chip}>{chip}</DisabledBadge>
                    ))}
                  </div>
                  <dl className="mt-4">
                    <StatLine
                      label="Approval state"
                      tone="stop"
                      value={humanApprovedOperatorRecommendationPacket.approval_state}
                    />
                    <StatLine
                      label="Packet kind"
                      value={humanApprovedOperatorRecommendationPacket.packet_kind}
                    />
                    <StatLine
                      label="Required fields"
                      tone="warn"
                      value={humanApprovalRequiredFields.length}
                    />
                    <StatLine
                      label="Forbidden executable fields"
                      tone="good"
                      value={humanApprovalPacketShape.forbidden_top_level_fields.length}
                    />
                  </dl>
                </div>
                <div className="rounded-lg border border-rose-200 bg-rose-50 p-4">
                  <h3 className="font-semibold text-rose-950">
                    Missing Approval Fields
                  </h3>
                  <ShortList
                    empty="No missing human approval fields reported."
                    items={humanApprovalRequiredFields.map(
                      (field) => `${field.label}: ${field.fallback}`,
                    )}
                    limit={8}
                  />
                </div>
              </div>
            </Card>

            <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
              <Card title="Operator Decision Packet" kicker="Display only">
                <p className="text-base leading-7 text-stone-700">
                  This packet is a human review summary, not approval. The default
                  decision remains NO-GO until Britton writes an explicit scoped
                  decision for a future phase.
                </p>
                <dl className="mt-4">
                  <StatLine label="Decision default" tone="stop" value="NO-GO" />
                  <StatLine
                    label="Current HEAD"
                    value={cartographerLiveState.currentHead ?? "unknown"}
                  />
                  <StatLine
                    label="Dirty tree"
                    tone={dirtyFileCount > 0 ? "warn" : "good"}
                    value={`${trackedDirtyCount} tracked, ${untrackedCount} untracked`}
                  />
                  <StatLine
                    label="Protected lanes"
                    tone={
                      cartographerLiveState.protectedLaneMatches.length > 0
                        ? "warn"
                        : "quiet"
                    }
                    value={protectedLaneSummary}
                  />
                  <StatLine
                    label="Kill switch"
                    tone="stop"
                    value={cartographerStopControlStatus.killSwitchState}
                  />
                  <StatLine
                    label="Manual decision"
                    tone="warn"
                    value="missing"
                  />
                </dl>
              </Card>

              <Card title="Proof Package Checklist">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
                  <div>
                    <h3 className="text-sm font-semibold text-stone-950">
                      Required proof
                    </h3>
                    <div className="mt-2">
                      <ShortList
                        empty="No required proof items listed."
                        items={requiredProofItems}
                        limit={6}
                      />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-stone-950">
                      Missing proof
                    </h3>
                    <div className="mt-2">
                      <ShortList
                        empty="No missing proof reported by the display summary."
                        items={
                          missingProofItems.length > 0
                            ? missingProofItems
                            : ["manual operator decision is still required"]
                        }
                        limit={6}
                      />
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-6 text-stone-600">
                  Missing proof keeps the decision at NO-GO. This page does not
                  create proof, write evidence, record receipts, or store
                  approvals.
                </p>
              </Card>
            </div>

            <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
              <Card title="Plan 2 Blocked States">
                <ShortList
                  empty="No Plan 2 blocked states reported."
                  items={humanApprovalBlockedStates.map(
                    (state) => `${state.label}: ${state.detail}`,
                  )}
                  limit={8}
                />
              </Card>

              <Card title="Plan 2 Authority Denials">
                <ShortList
                  empty="No Plan 2 authority denials reported."
                  items={[
                    ...humanApprovedOperatorRecommendationPacket.authority_denials,
                    ...humanApprovedOperatorForbiddenActions.slice(0, 6),
                  ]}
                  limit={8}
                />
                <p className="mt-4 text-sm leading-6 text-stone-600">
                  {humanApprovedOperatorRecommendationPacket.recommendation_summary}
                </p>
              </Card>
            </div>

            <Card title="Plan 2 Fallback Proof">
              <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
                <ShortList
                  empty="No Plan 2 fallback proof reported."
                  items={humanApprovalFallbackProof}
                  limit={5}
                />
                <div className="rounded-lg border border-stone-200 p-4">
                  <h3 className="font-semibold text-stone-950">
                    Manual operator next step
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-stone-600">
                    {humanApprovedOperatorRecommendationPacket.manual_next_step}
                  </p>
                </div>
              </div>
            </Card>

            <Card title="Human Approval Packet Shape">
              <div className="grid gap-4 xl:grid-cols-[0.8fr_1fr_1fr]">
                <div className="rounded-lg border border-stone-200 p-4">
                  <h3 className="font-semibold text-stone-950">
                    Packet kind
                  </h3>
                  <p className="mt-2 break-words font-mono text-xs leading-6 text-stone-600">
                    {humanApprovalPacketShape.packet_kind}
                  </p>
                  <h3 className="mt-4 font-semibold text-stone-950">
                    Fallback reason
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-stone-600">
                    {humanApprovedOperatorRecommendationPacket.fallback_reason}
                  </p>
                </div>
                <div className="rounded-lg border border-stone-200 p-4">
                  <h3 className="font-semibold text-stone-950">
                    Approval state enum
                  </h3>
                  <ShortList
                    empty="No approval states listed."
                    items={humanApprovalPacketShape.allowed_approval_states}
                    limit={4}
                  />
                </div>
                <div className="rounded-lg border border-stone-200 p-4">
                  <h3 className="font-semibold text-stone-950">
                    Forbidden packet fields
                  </h3>
                  <ShortList
                    empty="No forbidden packet fields listed."
                    items={humanApprovalPacketShape.forbidden_top_level_fields}
                    limit={6}
                  />
                </div>
              </div>
              <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
                <div className="rounded-lg border border-stone-200 p-4">
                  <h3 className="font-semibold text-stone-950">
                    Required packet fields
                  </h3>
                  <ShortList
                    empty="No required packet fields listed."
                    items={humanApprovalPacketShape.required_top_level_fields}
                    limit={8}
                  />
                </div>
                <div className="rounded-lg border border-stone-200 p-4">
                  <h3 className="font-semibold text-stone-950">
                    Human approval fallback proof
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-stone-600">
                    Missing or incomplete approval packet data renders as blocked
                    display state with forbidden executable fields visible.
                  </p>
                </div>
              </div>
            </Card>
          </SectionGroup>

          <SectionGroup
            title="Manual Closeout"
            summary="The only safe action from this page is human review followed by an explicit next-phase decision."
          >
            <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
              <Card title="Next Safe Action">
                <p className="text-lg font-semibold leading-8 text-stone-950">
                  {cartographerLiveState.safeNextAction}
                </p>
                <p className="mt-3 text-sm leading-6 text-stone-600">
                  Before the next phase, Britton should manually verify this
                  display and explicitly approve the next scoped phase. Silence
                  or dashboard presence is not approval.
                </p>
              </Card>

              <Card title="Authority Boundary Audit">
                <ShortList
                  empty="No authority denials listed."
                  items={closeoutAuthorityDenials}
                  limit={7}
                />
              </Card>
            </div>

            <div className="grid gap-4">
              <Card title="Manual Checks">
                <div className="overflow-x-auto rounded-lg border border-stone-200 bg-stone-950 p-4">
                  <pre className="whitespace-pre-wrap break-words text-sm leading-6 text-stone-50">
                    <code>{manualChecks.join("\n")}</code>
                  </pre>
                </div>
              </Card>
            </div>
          </SectionGroup>

          <details className="rounded-lg border border-[#b9aa94] bg-[#fff8ec] p-5 shadow-[0_2px_0_rgba(72,52,32,0.08),0_16px_34px_rgba(72,52,32,0.16)]">
            <summary className="cursor-pointer text-base font-semibold text-stone-950">
              Advanced safety/debug
            </summary>
            <div className="mt-5 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="space-y-4">
                <dl className="rounded-lg border border-stone-200 p-4">
                  <StatLine
                    label="Read-only endpoints live"
                    tone={liveEndpointCount > 0 ? "good" : "quiet"}
                    value={liveEndpointCount}
                  />
                  <StatLine
                    label="Fallback or blocked"
                    tone={fallbackEndpointCount > 0 ? "warn" : "good"}
                    value={fallbackEndpointCount}
                  />
                  <StatLine
                    label="Queue worker"
                    tone={cartographerQueueStatus.queueWorkerAvailable ? "warn" : "quiet"}
                    value={
                      cartographerQueueStatus.queueWorkerAvailable
                        ? "reported available"
                        : "not available"
                    }
                  />
                  <StatLine
                    label="Stop controls"
                    tone="stop"
                    value={cartographerStopControlStatus.killSwitchState}
                  />
                  <StatLine
                    label="Read-only origin"
                    value={origin ?? "unavailable"}
                  />
                </dl>
                <div className="rounded-lg border border-stone-200 p-4">
                  <h3 className="font-semibold text-stone-950">
                    Safety boundary
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-stone-600">
                    /map remains display-only. It does not approve, execute,
                    commit, push, start workers, mint tokens, or record
                    approvals.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="overflow-x-auto rounded-lg border border-stone-200">
                  <table className="w-full min-w-[720px] border-collapse text-left text-sm">
                    <thead className="bg-stone-50 text-stone-600">
                      <tr>
                        <th className="border-b border-stone-200 px-3 py-2 font-semibold">
                          Source
                        </th>
                        <th className="border-b border-stone-200 px-3 py-2 font-semibold">
                          State
                        </th>
                        <th className="border-b border-stone-200 px-3 py-2 font-semibold">
                          Endpoint
                        </th>
                        <th className="border-b border-stone-200 px-3 py-2 font-semibold">
                          Detail
                        </th>
                        <th className="border-b border-stone-200 px-3 py-2 font-semibold">
                          Diagnostics
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {readOnlyMapData.endpoints.map((endpoint) => (
                        <tr className="border-b border-stone-100" key={endpoint.endpoint}>
                          <td className="px-3 py-3 font-medium text-stone-900">
                            {endpoint.label}
                          </td>
                          <td className="px-3 py-3 text-stone-700">
                            {endpoint.state}
                          </td>
                          <td className="break-all px-3 py-3 font-mono text-xs text-stone-500">
                            {endpoint.endpoint}
                          </td>
                          <td className="px-3 py-3 text-stone-600">
                            {endpoint.detail}
                          </td>
                          <td className="px-3 py-3 text-stone-600">
                            {`HTTP ${endpoint.statusCode ?? "none"} / ${endpoint.failureKind} / ${endpoint.shapeSummary}`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="rounded-lg border border-rose-200 bg-rose-50 p-4">
                  <h3 className="font-semibold text-rose-950">
                    Blocked action classes
                  </h3>
                  <ShortList
                    empty="No blocked action classes reported."
                    items={blockedActionClasses}
                    limit={8}
                  />
                </div>

                {cartographerWorkflowStatus.blockers.length > 0 ? (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                    <h3 className="font-semibold text-amber-950">
                      Workflow blockers
                    </h3>
                    <ShortList
                      empty="No workflow blockers reported."
                      items={cartographerWorkflowStatus.blockers}
                      limit={5}
                    />
                  </div>
                ) : null}
              </div>
            </div>
          </details>
        </div>
      </main>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
