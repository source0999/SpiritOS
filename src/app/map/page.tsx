import { headers } from "next/headers";
import type { ReactNode } from "react";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import { getCartographerApprovalTokenStatus } from "./cartographer-approval-token";
import { getCartographerLiveState } from "./cartographer-live-state";
import { getCartographerQueueStatus } from "./cartographer-queue-status";
import { getCartographerReceiptEvidenceStatus } from "./cartographer-receipt-evidence";
import { cartographerStopControlStatus } from "./cartographer-stop-controls";
import { getCartographerWorkflowStatus } from "./cartographer-workflow-status";
import {
  blockedActionClasses,
  getReadOnlyMapData,
} from "./read-only-map-data";
import {
  cartographerMapApprovalTokenFields,
  cartographerMapAuthorityDenials,
  cartographerMapLiveStateFields,
  cartographerMapOperationalSections,
  cartographerMapOperatorQuestions,
  cartographerMapQueuePanelFields,
  cartographerMapReceiptEvidenceFields,
  cartographerMapStopControlFields,
  cartographerMapWorkflowPanelFields,
} from "./map-information-architecture";
import "@/styles/dashboard-demo-v4.css";

function Section({
  id,
  title,
  purpose,
  children,
}: {
  id: string;
  title: string;
  purpose: string;
  children: ReactNode;
}) {
  return (
    <section className="scroll-mt-6 border-t border-slate-800 py-7" id={id}>
      <div className="max-w-3xl">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
          {id.replaceAll("-", " ")}
        </p>
        <h2 className="mt-1 text-xl font-semibold text-slate-50">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-slate-400">{purpose}</p>
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Metric({
  label,
  value,
  tone = "slate",
}: {
  label: string;
  value: ReactNode;
  tone?: "slate" | "green" | "amber" | "red";
}) {
  const toneClass =
    tone === "green"
      ? "text-emerald-100"
      : tone === "amber"
        ? "text-amber-100"
        : tone === "red"
          ? "text-rose-100"
          : "text-slate-100";

  return (
    <div className="border border-slate-800 bg-slate-950 p-3">
      <dt className="text-xs uppercase tracking-[0.12em] text-slate-500">
        {label}
      </dt>
      <dd className={`mt-1 break-words text-sm font-semibold ${toneClass}`}>
        {value}
      </dd>
    </div>
  );
}

function PlainList({ items }: { items: readonly string[] }) {
  return (
    <ul className="space-y-2 text-sm leading-6 text-slate-300">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function sourceLabel(state: "live" | "fallback" | "blocked") {
  if (state === "live") {
    return "live";
  }
  if (state === "blocked") {
    return "blocked";
  }
  return "fallback";
}

export default async function CartographerMapPage() {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host");
  const protocol = requestHeaders.get("x-forwarded-proto") ?? "http";
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

  const liveSources = readOnlyMapData.endpoints.filter(
    (endpoint) => endpoint.state === "live",
  ).length;
  const fallbackSources = readOnlyMapData.endpoints.filter(
    (endpoint) => endpoint.state === "fallback",
  ).length;
  const blockedSources = readOnlyMapData.endpoints.filter(
    (endpoint) => endpoint.state === "blocked",
  ).length;
  const oneTaskEligibility =
    cartographerQueueStatus.selectionAvailable &&
    !cartographerQueueStatus.executionAvailable
      ? "selection preview only"
      : "blocked";
  const dirtyFileCount =
    cartographerLiveState.trackedDirtyFiles.length +
    cartographerLiveState.untrackedFiles.length;
  const protectedLaneState =
    cartographerLiveState.protectedLaneMatches.length > 0
      ? "matches found"
      : "none reported";

  return (
    <div className="dashboard-demo-v4-route-shell">
      <main className="min-h-screen bg-slate-950 px-4 pb-24 pt-6 text-slate-100 sm:px-6 lg:px-8 lg:pb-8">
        <div className="mx-auto w-full max-w-5xl">
          <header className="border-b border-slate-800 pb-6">
            <p className="text-sm font-medium uppercase tracking-[0.14em] text-slate-400">
              /map
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">
              Cartographer Cockpit
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-slate-300">
              A simple operator view for what Cartographer is doing, what is
              blocked, what is approved, what ran, and what Britton needs to
              verify. Display does not grant authority.
            </p>
            <dl className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Metric label="Safety" value={cartographerLiveState.recommendedSafetyState} tone="amber" />
              <Metric label="Branch" value={cartographerLiveState.currentBranch ?? "unavailable"} />
              <Metric label="Tracked dirty" value={cartographerLiveState.trackedDirtyFiles.length} tone="amber" />
              <Metric label="Untracked" value={cartographerLiveState.untrackedFiles.length} tone="amber" />
            </dl>
          </header>

          <nav
            aria-label="Cartographer cockpit sections"
            className="mt-5 flex flex-wrap gap-2 border-b border-slate-800 pb-5"
          >
            {cartographerMapOperationalSections.map((section) => (
              <a
                className="border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:border-slate-500 hover:bg-slate-900"
                href={`#${section.id}`}
                key={section.id}
              >
                {section.label}
              </a>
            ))}
          </nav>

          <Section
            id="current-state"
            purpose="Live state, dirty state, protected lanes, and the safest next move."
            title="Current State"
          >
            <div className="mb-4 border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold text-slate-50">
                Live state panel contract
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {cartographerMapLiveStateFields.map((field) => (
                  <span
                    className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300"
                    key={field}
                  >
                    {field}
                  </span>
                ))}
              </div>
            </div>
            <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">Repo state</h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerLiveState.detail}
                </p>
                <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Metric label="Branch" value={cartographerLiveState.currentBranch ?? "unavailable"} />
                  <Metric label="HEAD" value={cartographerLiveState.currentHead ?? "unavailable"} />
                  <Metric label="Dirty state" value={`${dirtyFileCount} files`} tone={dirtyFileCount > 0 ? "amber" : "green"} />
                  <Metric label="Protected-lane state" value={protectedLaneState} tone={cartographerLiveState.protectedLaneMatches.length > 0 ? "red" : "green"} />
                  <Metric label="Collected" value={cartographerLiveState.collectedAt ?? "unavailable"} />
                  <Metric label="Recommendation" value={cartographerLiveState.recommendedSafetyState} tone={cartographerLiveState.recommendedSafetyState === "clear" ? "green" : cartographerLiveState.recommendedSafetyState === "caution" ? "amber" : "red"} />
                </dl>
              </div>
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">Safe next action</h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerLiveState.safeNextAction}
                </p>
                {cartographerLiveState.blockerReasons.length > 0 ? (
                  <div className="mt-4 border border-rose-300/20 bg-rose-950/20 p-3">
                    <h4 className="text-sm font-semibold text-rose-50">
                      Blockers
                    </h4>
                    <PlainList items={cartographerLiveState.blockerReasons} />
                  </div>
                ) : null}
                <div className="mt-4 border border-slate-800 bg-slate-950 p-3">
                  <h4 className="text-sm font-semibold text-slate-100">
                    Protected-lane matches
                  </h4>
                  {cartographerLiveState.protectedLaneMatches.length > 0 ? (
                    <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-400">
                      {cartographerLiveState.protectedLaneMatches
                        .slice(0, 8)
                        .map((match) => (
                          <li
                            className="break-all"
                            key={`${match.lane}:${match.path}`}
                          >
                            {match.lane}: {match.path}
                          </li>
                        ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      No protected-lane matches reported by the live state
                      endpoint.
                    </p>
                  )}
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="border border-slate-800 bg-slate-950 p-3">
                    <h4 className="text-sm font-semibold text-slate-100">
                      Tracked dirty files
                    </h4>
                    {cartographerLiveState.trackedDirtyFiles.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-400">
                        {cartographerLiveState.trackedDirtyFiles
                          .slice(0, 6)
                          .map((path) => (
                            <li className="break-all" key={path}>
                              {path}
                            </li>
                          ))}
                      </ul>
                    ) : (
                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        None reported.
                      </p>
                    )}
                  </div>
                  <div className="border border-slate-800 bg-slate-950 p-3">
                    <h4 className="text-sm font-semibold text-slate-100">
                      Untracked files
                    </h4>
                    {cartographerLiveState.untrackedFiles.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-400">
                        {cartographerLiveState.untrackedFiles
                          .slice(0, 6)
                          .map((path) => (
                            <li className="break-all" key={path}>
                              {path}
                            </li>
                          ))}
                      </ul>
                    ) : (
                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        None reported.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Section>

          <Section
            id="approvals"
            purpose="Approval token state and blocked authority, without minting or recording approvals."
            title="Approvals"
          >
            <div className="mb-4 border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold text-slate-50">
                Approval token panel contract
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {cartographerMapApprovalTokenFields.map((field) => (
                  <span
                    className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300"
                    key={field}
                  >
                    {field}
                  </span>
                ))}
              </div>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">
                  Approval token runtime
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerApprovalTokenStatus.detail}
                </p>
                <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Metric label="Runtime status" value={cartographerApprovalTokenStatus.runtimeStatus} />
                  <Metric label="Validation" value={cartographerApprovalTokenStatus.validationStatus} />
                  <Metric label="Consumption preview" value={cartographerApprovalTokenStatus.consumptionStatus} />
                  <Metric label="Validation only" value={cartographerApprovalTokenStatus.validationOnly ? "yes" : "no"} />
                  <Metric label="Self approval" value={cartographerApprovalTokenStatus.selfApprovalBlocked ? "blocked" : "review"} tone="red" />
                  <Metric label="Authority" value={cartographerApprovalTokenStatus.authorityGranted ? "review" : "not granted"} tone="red" />
                  <Metric label="Safe next action" value={cartographerApprovalTokenStatus.safeNextAction} tone="amber" />
                </dl>
                <div className="mt-4 grid gap-3 lg:grid-cols-2">
                  <div className="border border-slate-800 bg-slate-950 p-3">
                    <h4 className="text-sm font-semibold text-slate-100">
                      Validation blocked reasons
                    </h4>
                    {cartographerApprovalTokenStatus.reasons.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-400">
                        {cartographerApprovalTokenStatus.reasons.map((reason) => (
                          <li className="break-all" key={reason}>
                            {reason}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        None reported.
                      </p>
                    )}
                  </div>
                  <div className="border border-slate-800 bg-slate-950 p-3">
                    <h4 className="text-sm font-semibold text-slate-100">
                      Consumption blocked reasons
                    </h4>
                    {cartographerApprovalTokenStatus.consumptionReasons.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-400">
                        {cartographerApprovalTokenStatus.consumptionReasons.map((reason) => (
                          <li className="break-all" key={reason}>
                            {reason}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        None reported.
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <div className="border border-rose-300/20 bg-rose-950/20 p-4">
                <h3 className="font-semibold text-rose-50">
                  Authority not granted
                </h3>
                <PlainList items={cartographerMapAuthorityDenials} />
              </div>
            </div>
          </Section>

          <Section
            id="queue"
            purpose="Queue information is visible only as safe status and eligibility."
            title="Queue"
          >
            <div className="mb-4 border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold text-slate-50">
                Queue panel contract
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {cartographerMapQueuePanelFields.map((field) => (
                  <span
                    className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300"
                    key={field}
                  >
                    {field}
                  </span>
                ))}
              </div>
            </div>
            <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">
                  Run-next status
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerQueueStatus.detail}
                </p>
                <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Metric label="Queue status" value={cartographerQueueStatus.queueStatus} />
                  <Metric label="Run-next status" value={cartographerQueueStatus.runNextStatus} />
                  <Metric label="Method shown" value={cartographerQueueStatus.runNextMethod} />
                  <Metric label="One-task selection" value={oneTaskEligibility} tone="amber" />
                  <Metric label="Required trust tier" value={cartographerQueueStatus.requiredTrustTier} />
                  <Metric label="Safe next action" value={cartographerQueueStatus.safeNextAction} tone="amber" />
                </dl>
              </div>
              <div className="border border-rose-300/20 bg-rose-950/20 p-4">
                <h3 className="font-semibold text-rose-50">
                  Queue authority blocked
                </h3>
                <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Metric label="Queue authority" value={cartographerApprovalTokenStatus.queueAuthorityGranted ? "review" : "not granted"} tone="red" />
                  <Metric label="Write authority" value={cartographerApprovalTokenStatus.writeAuthorityGranted ? "review" : "not granted"} tone="red" />
                  <Metric label="Execution" value={cartographerQueueStatus.executionAvailable ? "review" : "blocked"} tone="red" />
                  <Metric label="Durable storage" value={cartographerQueueStatus.durableStorageAvailable ? "review" : "blocked"} tone="red" />
                  <Metric label="Queue worker" value={cartographerQueueStatus.queueWorkerAvailable ? "review" : "blocked"} tone="red" />
                  <Metric label="Background loop" value={cartographerQueueStatus.backgroundLoopAvailable ? "review" : "blocked"} tone="red" />
                  <Metric label="Task classes" value={cartographerQueueStatus.allowedTaskClassCount} />
                  <Metric label="Task statuses" value={cartographerQueueStatus.taskStatusCount} />
                </dl>
              </div>
            </div>
          </Section>

          <Section
            id="workflows"
            purpose="Workflow runs are summarized for operator review; no start, retry, pause, or cancel controls are added here."
            title="Workflows"
          >
            <div className="mb-4 border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold text-slate-50">
                Workflow run panel contract
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {cartographerMapWorkflowPanelFields.map((field) => (
                  <span
                    className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300"
                    key={field}
                  >
                    {field}
                  </span>
                ))}
              </div>
            </div>
            <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">
                  Workflow run status
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerWorkflowStatus.detail}
                </p>
                <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Metric label="Active runs" value={cartographerWorkflowStatus.activeRunCount} />
                  <Metric label="Recent runs" value={cartographerWorkflowStatus.recentRunCount} />
                  <Metric label="Workflow status" value={cartographerWorkflowStatus.workflowStatus} tone={cartographerWorkflowStatus.blockers.length > 0 ? "amber" : "green"} />
                  <Metric label="Blocked steps" value={`${cartographerWorkflowStatus.blockedStepCount} of ${cartographerWorkflowStatus.stepCount}`} tone={cartographerWorkflowStatus.blockedStepCount > 0 ? "amber" : "green"} />
                  <Metric label="Workflow id" value={cartographerWorkflowStatus.workflowId} />
                  <Metric label="Safe next action" value={cartographerWorkflowStatus.safeNextAction} tone="amber" />
                </dl>
                {cartographerWorkflowStatus.blockers.length > 0 ? (
                  <div className="mt-4 border border-rose-300/20 bg-rose-950/20 p-3">
                    <h4 className="text-sm font-semibold text-rose-50">
                      Workflow blocked reasons
                    </h4>
                    <PlainList items={cartographerWorkflowStatus.blockers} />
                  </div>
                ) : null}
              </div>
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">Step status</h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerWorkflowStatus.workflowTitle}
                </p>
                <div className="mt-4 space-y-3">
                  {cartographerWorkflowStatus.steps.length > 0 ? (
                    cartographerWorkflowStatus.steps.map((step) => (
                      <div
                        className="border border-slate-800 bg-slate-950 p-3"
                        key={step.stepId}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <h4 className="text-sm font-semibold text-slate-100">
                              {step.title}
                            </h4>
                            <p className="mt-1 break-all text-xs text-slate-500">
                              {step.source}
                            </p>
                          </div>
                          <span className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300">
                            {step.status}
                          </span>
                        </div>
                        {step.blockers.length > 0 ? (
                          <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-400">
                            {step.blockers.map((blocker) => (
                              <li className="break-all" key={blocker}>
                                {blocker}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm leading-6 text-slate-300">
                      No workflow steps reported.
                    </p>
                  )}
                </div>
              </div>
            </div>
            <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Metric label="Workflow authority" value={cartographerWorkflowStatus.authorityGranted ? "review" : "not granted"} tone="red" />
              <Metric label="Execution" value={cartographerWorkflowStatus.executionAvailable ? "review" : "blocked"} tone="red" />
              <Metric label="Background execution" value={cartographerWorkflowStatus.backgroundExecutionAllowed ? "review" : "blocked"} tone="red" />
              <Metric label="Autonomous retry" value={cartographerWorkflowStatus.autonomousRetryAllowed ? "review" : "blocked"} tone="red" />
            </dl>
          </Section>

          <Section
            id="receipts"
            purpose="Evidence and receipts are review material, not write targets."
            title="Receipts And Evidence"
          >
            <div className="mb-4 border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold text-slate-50">
                Kill switch and stop control contract
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {cartographerMapStopControlFields.map((field) => (
                  <span
                    className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300"
                    key={field}
                  >
                    {field}
                  </span>
                ))}
              </div>
            </div>
            <div className="mb-4 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="border border-rose-300/20 bg-rose-950/20 p-4">
                <h3 className="font-semibold text-rose-50">
                  Kill switch state
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerStopControlStatus.safeNextAction}
                </p>
                <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Metric label="State" value={cartographerStopControlStatus.killSwitchState} tone="red" />
                  <Metric label="Backend endpoint" value={cartographerStopControlStatus.backendEndpointAvailable ? "available" : "unavailable"} tone="red" />
                  <Metric label="Executable controls" value={cartographerStopControlStatus.executableControlsAvailable ? "review" : "blocked"} tone="red" />
                  <Metric label="Durable write" value={cartographerStopControlStatus.durableWriteAvailable ? "review" : "blocked"} tone="red" />
                </dl>
              </div>
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">
                  Stop control policy
                </h3>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {cartographerStopControlStatus.controls.map((control) => (
                    <div
                      className="border border-slate-800 bg-slate-950 p-3"
                      key={control.id}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <h4 className="text-sm font-semibold text-slate-100">
                          {control.label}
                        </h4>
                        <span className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300">
                          {control.status}
                        </span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-400">
                        Target: {control.modeledTarget}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        {control.blockedReason}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <dl className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Metric label="Workflow execution" value={cartographerStopControlStatus.workflowExecutionAuthorityGranted ? "review" : "blocked"} tone="red" />
              <Metric label="Queue authority" value={cartographerStopControlStatus.queueAuthorityGranted ? "review" : "blocked"} tone="red" />
              <Metric label="Command authority" value={cartographerStopControlStatus.commandAuthorityGranted ? "review" : "blocked"} tone="red" />
              <Metric label="Git mutation" value={cartographerStopControlStatus.gitMutationAuthorityGranted ? "review" : "blocked"} tone="red" />
            </dl>
            <div className="mb-4 border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold text-slate-50">
                Receipt/evidence browser contract
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {cartographerMapReceiptEvidenceFields.map((field) => (
                  <span
                    className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300"
                    key={field}
                  >
                    {field}
                  </span>
                ))}
              </div>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">
                  Receipt/evidence status
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerReceiptEvidenceStatus.detail}
                </p>
                <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Metric label="Receipt journal" value={cartographerReceiptEvidenceStatus.receiptJournalStatus} />
                  <Metric label="Evidence mode" value={cartographerReceiptEvidenceStatus.evidenceCollectionMode} />
                  <Metric label="Artifacts" value={cartographerReceiptEvidenceStatus.evidenceArtifactCount} />
                  <Metric label="Proof records" value={cartographerReceiptEvidenceStatus.proofGateRecordCount} />
                  <Metric label="Receipt writes" value={cartographerReceiptEvidenceStatus.receiptJournalWriteAllowed ? "review" : "blocked"} tone="red" />
                  <Metric label="Hidden writes" value={cartographerReceiptEvidenceStatus.hiddenReceiptWritesAllowed ? "review" : "blocked"} tone="red" />
                </dl>
                {cartographerReceiptEvidenceStatus.missingEvidence.length > 0 ? (
                  <div className="mt-4 border border-amber-300/20 bg-amber-950/20 p-3">
                    <h4 className="text-sm font-semibold text-amber-50">
                      Missing evidence
                    </h4>
                    <PlainList items={cartographerReceiptEvidenceStatus.missingEvidence} />
                  </div>
                ) : null}
              </div>
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">
                  Approved docs artifacts
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {cartographerReceiptEvidenceStatus.safeNextAction}
                </p>
                <div className="mt-4 space-y-3">
                  {cartographerReceiptEvidenceStatus.approvedDocsArtifacts.length > 0 ? (
                    cartographerReceiptEvidenceStatus.approvedDocsArtifacts.map((item) => (
                      <div
                        className="border border-slate-800 bg-slate-950 p-3"
                        key={item.id}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <h4 className="text-sm font-semibold text-slate-100">
                            {item.label}
                          </h4>
                          <span className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300">
                            {item.status}
                          </span>
                        </div>
                        {item.paths.length > 0 ? (
                          <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-400">
                            {item.paths.map((path) => (
                              <li className="break-all" key={path}>
                                {path}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm leading-6 text-slate-300">
                      No approved docs artifacts reported.
                    </p>
                  )}
                </div>
              </div>
            </div>
            <div className="mt-4 border border-slate-800 bg-slate-900 p-4">
              <h3 className="font-semibold text-slate-50">
                Evidence items
              </h3>
              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                {cartographerReceiptEvidenceStatus.evidenceItems.length > 0 ? (
                  cartographerReceiptEvidenceStatus.evidenceItems.map((item) => (
                    <div
                      className="border border-slate-800 bg-slate-950 p-3"
                      key={item.id}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <h4 className="text-sm font-semibold text-slate-100">
                          {item.label}
                        </h4>
                        <span className="border border-slate-700 px-2 py-1 text-xs font-semibold uppercase text-slate-300">
                          {item.status}
                        </span>
                      </div>
                      {item.paths.length > 0 ? (
                        <ul className="mt-2 space-y-1 text-xs leading-5 text-slate-400">
                          {item.paths.map((path) => (
                            <li className="break-all" key={path}>
                              {path}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <p className="text-sm leading-6 text-slate-300">
                    No receipt/evidence items reported.
                  </p>
                )}
              </div>
            </div>
          </Section>

          <Section
            id="verify"
            purpose="A compact checklist for Britton before trusting the page."
            title="What Britton Needs To Verify"
          >
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">
                  Operator questions
                </h3>
                <PlainList items={cartographerMapOperatorQuestions} />
              </div>
              <div className="border border-slate-800 bg-slate-900 p-4">
                <h3 className="font-semibold text-slate-50">
                  Manual next step
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {readOnlyMapData.recommendationPacket.manual_next_step}
                </p>
              </div>
            </div>
          </Section>

          <Section
            id="debug"
            purpose="Source health and fallback reasons stay visible instead of being hidden behind controls."
            title="Debug Source Health"
          >
            <dl className="grid gap-3 sm:grid-cols-3">
              <Metric label="Live sources" value={liveSources} tone="green" />
              <Metric label="Fallback sources" value={fallbackSources} tone="amber" />
              <Metric label="Blocked sources" value={blockedSources} tone="red" />
            </dl>
            <div className="mt-4 overflow-x-auto border border-slate-800 bg-slate-900">
              <table className="w-full min-w-[680px] border-collapse text-left text-sm">
                <thead className="text-xs uppercase tracking-[0.12em] text-slate-500">
                  <tr>
                    <th className="border-b border-slate-800 px-3 py-2">Source</th>
                    <th className="border-b border-slate-800 px-3 py-2">State</th>
                    <th className="border-b border-slate-800 px-3 py-2">Endpoint</th>
                    <th className="border-b border-slate-800 px-3 py-2">Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {readOnlyMapData.endpoints.map((endpoint) => (
                    <tr className="border-b border-slate-800" key={endpoint.endpoint}>
                      <td className="px-3 py-3 text-slate-100">{endpoint.label}</td>
                      <td className="px-3 py-3 text-slate-300">{sourceLabel(endpoint.state)}</td>
                      <td className="break-all px-3 py-3 font-mono text-xs text-slate-400">
                        {endpoint.endpoint}
                      </td>
                      <td className="px-3 py-3 text-slate-300">{endpoint.detail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 border border-rose-300/20 bg-rose-950/20 p-4">
              <h3 className="font-semibold text-rose-50">
                Blocked action classes
              </h3>
              <PlainList items={blockedActionClasses} />
            </div>
          </Section>
        </div>
      </main>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
