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
  buildCartographerBranchPushPreview,
  buildCartographerCommitPreview,
  buildCartographerDirtyTreePreview,
  cartographerDefaultProjectCardPreviews,
} from "./map-information-architecture";
import { getReadOnlyMapData } from "./read-only-map-data";
import "@/styles/dashboard-demo-v4.css";

type Tone = "good" | "warn" | "stop" | "quiet";

const mapAdvisoryHelpers = [
  {
    blockedActions: "No repo scan beyond already-read map data, no file edits, no cleanup, no worker starts.",
    context: "Lane health, project cards, dirty tree groups, and protected-lane matches.",
    name: "Component Mapper",
    proposal: "Point Britton to the lanes and file families that need review before the next approved Proxy pass.",
  },
  {
    blockedActions: "No approval minting, approval-token consumption, safe write, queue execution, or action POST.",
    context: "NO-GO status, protected-lane warnings, dirty tree state, and authority boundary audit.",
    name: "Safety Reviewer",
    proposal: "Keep every map recommendation review-only until a separate approval gate exists.",
  },
  {
    blockedActions: "No test execution, shell command execution, package install, or broad build trigger.",
    context: "Missing verification cards, manual command text, and read-only endpoint status.",
    name: "Test Scribe",
    proposal: "Suggest focused verification commands for the next approved lane without running them from /map.",
  },
  {
    blockedActions: "No source writes, receipt writes, evidence-store writes, apply, commit, or push.",
    context: "Dirty tree groups, project tracker cards, and read-only Cartographer summaries.",
    name: "Change Scribe",
    proposal: "Summarize changed areas and review risks from the already displayed map state.",
  },
  {
    blockedActions: "No browser automation, check pass/fail claims, fabricated evidence, or stored acceptance.",
    context: "Manual checks, safe controls, and the next safe step.",
    name: "Runbook Scribe",
    proposal: "Keep browser verification guidance in chat and workflow commands in terminal blocks.",
  },
  {
    blockedActions: "No roadmap mutation outside approved docs lanes and no next-plan auto-start.",
    context: "Project tracker cards, dependency gates, and current plan status.",
    name: "Blueprint Scribe",
    proposal: "Map the next fleet gate without turning a recommendation into approval.",
  },
  {
    blockedActions: "No staging, commit, push, branch, merge, tag, checkout, reset, stash, or clean.",
    context: "Commit preview, blocked commit files, and missing verification.",
    name: "Commit Scribe",
    proposal: "Draft commit-language ideas only after Britton requests them; never touch git state.",
  },
  {
    blockedActions: "No tag, release, deploy, provider call, autonomy promotion, or final CSS start.",
    context: "Push readiness, release blockers, diagnostics, and NO-GO state.",
    name: "Release Steward",
    proposal: "Summarize readiness risks while keeping release and final polish gated.",
  },
] as const;

const manualCheck = [
  "cd /home/source/SpiritOS",
  "git status --branch --short",
  "git diff --check",
  "npm test -- run src/app/map/__tests__/map-information-architecture.test.ts src/app/map/__tests__/map-display-shell.test.ts",
  "npm run typecheck",
  "npm run build",
].join("\n");

const dailyDriverProofItems = [
  "10 supervised safe-task receipts require approval, verification, rollback guidance, kill-switch check, operator supervision, and human review.",
  "24-hour and 72-hour soak samples record drift, protected-lane state, queue state, false positives, false negatives, stop events, receipts, and operator review.",
  "Dirty tree and hidden mutation drills block unexpected files without cleanup, stash, checkout, or reset.",
  "Kill switch and rollback drills prove stop states and rollback guidance without executing rollback.",
  "Promotion decision remains a human record only; tests do not grant automatic full auto.",
] as const;

const trustTierGate = {
  currentTier: "tier-1",
  gateStatus: "human review required",
  nextDecisionGate: "Plan 10/10 trust-tier decision packet",
  blockedAuthorities: [
    "automatic tier advancement",
    "full auto",
    "push promotion",
    "queue execution",
    "branch/worktree creation",
    "commit or push",
  ],
} as const;

const laneOwnershipPreview = {
  activeLane: "cartographer",
  owner: "cartographer",
  registryState: "proposal-only",
  conflictState: "blocked until dirty overlaps are clear",
  allowedPaths: [
    "source_proxy/cartographer/",
    "source_proxy/tests/test_cartographer_",
    "src/app/map/",
  ],
  forbiddenPaths: [
    "src/app/coding/",
    "src/components/coding/",
    "source_proxy/agent_factory/",
    "public/media/",
    "package/config/env files",
  ],
  protectedZones: [
    "/coding",
    "media",
    "Agent Factory",
    "package/config/env",
    "generated/cache",
  ],
  blockedActions: [
    "No lock acquisition",
    "No lock release",
    "No active-lane mutation",
    "No worker dispatch",
    "No filesystem enforcement",
  ],
} as const;

const verificationRunnerPreview = {
  status: "verification-only",
  commandModel: "exact argv allowlist",
  shell: "blocked",
  timeout: "bounded",
  receipts: "pass/fail summaries required",
  authority: "no workflow, queue, git, worker, or shell authority",
  allowedCommands: [
    "git diff --check",
    ".venv/bin/python -m pytest <approved single test file>",
    "npm test -- <approved single frontend test file>",
  ],
  blockedCommands: [
    "shell strings and metacharacters",
    "package installs",
    "destructive git",
    "network/provider commands",
    "long-running commands",
  ],
} as const;

const workerControlPreview = {
  registryStatus: "model-only",
  dispatchStatus: "proposal-only",
  leaseStatus: "expires or stale-closeout required",
  fileZoneStatus: "exact non-overlapping zones only",
  staleCloseout: "operator review required",
  authority: "no hidden workers, provider calls, queue bypass, or source edits",
  identities: [
    "worker id",
    "role",
    "assigned task",
    "lane owner",
    "trust tier",
    "approval token",
  ],
  blockedActions: [
    "worker spawn",
    "worker dispatch",
    "provider calls",
    "uncontrolled file edits",
    "branch or worktree creation",
    "commit or push",
  ],
} as const;

const gitOperatorPreview = {
  plan: "Cartographer Integrated Control Master Plan 9/10",
  commitGate: "exact human-approved local commit only",
  staging: "exact file list only",
  branchWorktree: "proposal-only",
  push: "dedicated branch, exact sha, human approval required",
  autoPush: "blocked pending later promotion",
  rollback: "git revert guidance required before follow-up proposal",
  blockedActions: [
    "git add .",
    "broad staging",
    "auto-push",
    "force push",
    "tag push",
    "push to main/master/trunk",
    "merge or rebase",
    "branch/worktree creation from /map",
    "reset, stash, clean, or checkout",
  ],
} as const;

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

function Card({
  title,
  children,
  className = "",
}: {
  title: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-[#c8b89f] bg-[#fffaf1] p-4 shadow-[0_2px_0_rgba(72,52,32,0.06),0_12px_24px_rgba(72,52,32,0.11)] ${className}`}
    >
      <h2 className="text-lg font-semibold text-stone-950">{title}</h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function StatusPill({ children, tone }: { children: ReactNode; tone: Tone }) {
  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${toneClasses(
        tone,
      )}`}
    >
      {children}
    </span>
  );
}

function Fact({
  label,
  value,
  tone = "quiet",
}: {
  label: string;
  value: ReactNode;
  tone?: Tone;
}) {
  return (
    <div className="grid gap-1 border-b border-stone-100 py-2 last:border-b-0">
      <dt className="text-xs font-medium uppercase text-stone-500">{label}</dt>
      <dd
        className={`rounded-md border px-2 py-1 text-sm font-semibold leading-5 break-words ${toneClasses(
          tone,
        )}`}
      >
        {value}
      </dd>
    </div>
  );
}

function ControlLink({
  href,
  children,
}: {
  href: string;
  children: ReactNode;
}) {
  return (
    <a
      className="inline-flex min-h-11 items-center justify-center rounded-lg border border-stone-300 bg-white px-3 py-2 text-center text-sm font-semibold text-stone-900 shadow-sm"
      href={href}
    >
      {children}
    </a>
  );
}

function CommandBlock({ value }: { value: string }) {
  return (
    <div className="mt-3 overflow-x-auto rounded-lg border border-stone-200 bg-stone-950 p-3">
      <pre className="whitespace-pre-wrap break-words text-xs leading-5 text-stone-50">
        <code>{value}</code>
      </pre>
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

function shortHead(value: string | null): string {
  return value ? value.slice(0, 12) : "unknown";
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
  return isLocalDevHost(hostname) ? "https" : "http";
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
    liveState,
    approvalTokenStatus,
    queueStatus,
    workflowStatus,
    receiptEvidenceStatus,
  ] = await Promise.all([
    getReadOnlyMapData(origin),
    getCartographerLiveState(origin),
    getCartographerApprovalTokenStatus(origin),
    getCartographerQueueStatus(origin),
    getCartographerWorkflowStatus(origin),
    getCartographerReceiptEvidenceStatus(origin),
  ]);

  const dirtyFileCount =
    liveState.trackedDirtyFiles.length + liveState.untrackedFiles.length;
  const protectedLaneCount = liveState.protectedLaneMatches.length;
  const dirtyTreePreview = buildCartographerDirtyTreePreview({
    trackedDirtyFiles: liveState.trackedDirtyFiles,
    untrackedFiles: liveState.untrackedFiles,
    protectedLaneMatches: liveState.protectedLaneMatches,
  });
  const commitPreview = buildCartographerCommitPreview(dirtyTreePreview);
  const branchPushPreview = buildCartographerBranchPushPreview({
    currentBranch: liveState.currentBranch,
    currentHead: liveState.currentHead,
    dirtyTree: dirtyTreePreview,
  });
  const liveEndpointCount = readOnlyMapData.endpoints.filter(
    (endpoint) => endpoint.state === "live",
  ).length;
  const nextSafeStep =
    dirtyTreePreview.totalDirtyFiles > 0
      ? "Review the dirty tree groups and keep every action manual."
      : "Review project cards and keep Cartographer preview-only.";
  const blockerItems = [
    {
      label: "Dirty tree",
      tone: dirtyFileCount > 0 ? "warn" : "good",
      value:
        dirtyFileCount > 0
          ? `${dirtyFileCount} dirty file(s) need review`
          : "clear right now",
    },
    {
      label: "Protected lanes",
      tone: protectedLaneCount > 0 ? "warn" : "good",
      value:
        protectedLaneCount > 0
          ? `${protectedLaneCount} protected warning(s)`
          : "no reported matches",
    },
    {
      label: "Approval missing",
      tone: "stop",
      value: approvalTokenStatus.accepted
        ? "accepted preview still grants no authority"
        : "missing or rejected",
    },
    {
      label: "Queue/action blocked",
      tone: "stop",
      value:
        queueStatus.executionAvailable || workflowStatus.executionAvailable
          ? "reported by backend, blocked on /map"
          : "no execution authority",
    },
    {
      label: "Kill switch status",
      tone: cartographerStopControlStatus.killSwitchState.includes("unknown")
        ? "warn"
        : "quiet",
      value: cartographerStopControlStatus.killSwitchState,
    },
  ] satisfies { label: string; tone: Tone; value: ReactNode }[];
  const missingProof = Array.from(
    new Set([...commitPreview.missingVerification, ...branchPushPreview.proofNeeded]),
  );
  const commitReadiness =
    dirtyTreePreview.totalDirtyFiles > 0 ||
    dirtyTreePreview.protectedLaneCount > 0 ||
    commitPreview.filesThatShouldNotBeCommittedYet.length > 0
      ? "blocked"
      : "proof-needed";
  const truthPacket = liveState.truthPacket;
  const truthPacketAuthorityBlocked =
    !truthPacket.authority.authorityGranted &&
    !truthPacket.authority.writeActionsEnabled &&
    !truthPacket.authority.queueAuthorityGranted &&
    !truthPacket.authority.canMutate;
  const truthPacketTone: Tone =
    truthPacket.status === "clear"
      ? "warn"
      : truthPacket.status === "caution"
        ? "warn"
        : "stop";
  const approvalGateTone: Tone =
    approvalTokenStatus.approvalState === "valid" ? "warn" : "stop";
  const approvalReasonCodes = approvalTokenStatus.reasonCodes;
  const truthEvidenceLinks = truthPacket.evidenceLinks;
  const visibleReceiptItems = receiptEvidenceStatus.approvedDocsArtifacts.length
    ? receiptEvidenceStatus.approvedDocsArtifacts
    : receiptEvidenceStatus.evidenceItems;

  return (
    <div className="dashboard-demo-v4-route-shell dashboard-demo-v4-route-shell-map">
      <main className="dashboard-demo-v4-route-main min-h-screen bg-[#e6dccd] px-4 pb-[var(--shell-mobile-bottom-reserved-height)] pt-4 text-stone-950 sm:px-5 lg:!pl-[calc(var(--ddv4-app-rail-width,12.5rem)+1.25rem)] lg:pb-8 lg:pr-6 lg:pt-5">
        <div className="mx-auto grid w-full max-w-[92rem] gap-4">
          <header className="rounded-lg border border-[#c8b89f] bg-[#fffaf1] p-4 shadow-[0_2px_0_rgba(72,52,32,0.06),0_12px_24px_rgba(72,52,32,0.11)] sm:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h1 className="text-3xl font-semibold text-stone-950">
                  Cartographer
                </h1>
                <p className="mt-2 max-w-2xl text-base leading-7 text-stone-700">
                  Command center for repo status, blockers, dirty groups, and safe next steps.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <StatusPill tone="good">Live</StatusPill>
                <StatusPill tone="quiet">Read-only</StatusPill>
                <StatusPill tone="stop">NO-GO</StatusPill>
              </div>
            </div>
            <dl
              aria-label="Cartographer status strip"
              className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-6"
            >
              <Fact label="Cartographer status" tone="stop" value="Live, read-only, NO-GO" />
              <Fact label="Branch" value={liveState.currentBranch ?? "unknown"} />
              <Fact label="Short hash" value={shortHead(liveState.currentHead)} />
              <Fact
                label="Dirty count"
                tone={dirtyFileCount > 0 ? "warn" : "good"}
                value={dirtyFileCount}
              />
              <Fact
                label="Protected warnings"
                tone={protectedLaneCount > 0 ? "warn" : "good"}
                value={protectedLaneCount}
              />
              <Fact label="Next safe step" tone="warn" value={nextSafeStep} />
            </dl>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <ControlLink href="/map/raw">Open raw diagnostics</ControlLink>
              <p className="text-xs leading-5 text-stone-500">
                Read-only sources: {liveEndpointCount}/{readOnlyMapData.endpoints.length} live.
              </p>
            </div>
          </header>

          {readOnlyMapData.mode !== "read-only-live" || !liveState.available ? (
            <div className="rounded-lg border border-amber-500 bg-[#fff1b8] px-4 py-3 text-sm font-semibold text-amber-950">
              Live data is not fully available. Cartographer is showing the safe fallback view.
            </div>
          ) : null}

          <div className="grid gap-4 xl:grid-cols-[minmax(0,0.72fr)_minmax(0,0.8fr)_minmax(0,1.2fr)] xl:items-start">
            <Card title="Can Cartographer act?">
              <div className="rounded-lg border border-rose-500/35 bg-rose-50 p-4 text-rose-950">
                <p className="text-2xl font-semibold">No</p>
                <p className="mt-2 text-sm leading-6">
                  Cartographer is review-only. It can show what it sees, but cannot change files,
                  run queues, consume approvals, commit, push, or start workers.
                </p>
                <p className="mt-2 text-sm font-semibold">
                  Why: dirty-tree review, approval proof, queue/action authority, and runtime gates
                  are still blocked.
                </p>
              </div>
            </Card>

            <Card title="What Britton does next">
              <p
                className="text-base font-semibold leading-7 text-stone-950"
                id="next-safe-step"
              >
                {nextSafeStep}
              </p>
              <p className="mt-3 text-sm leading-6 text-stone-600">
                Start with the manual verification block, then decide whether to keep
                Cartographer parked or approve the next scoped plan. Real operator actions still need a separate plan and explicit approval.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <ControlLink href="#manual-check">Open manual check</ControlLink>
                <ControlLink href="#attention">Review blockers</ControlLink>
              </div>
            </Card>

            <Card title="Blockers" className="scroll-mt-4">
              <dl id="attention" className="grid gap-2 sm:grid-cols-2 2xl:grid-cols-3">
                {blockerItems.map((item) => (
                  <Fact
                    key={item.label}
                    label={item.label}
                    tone={item.tone}
                    value={item.value}
                  />
                ))}
              </dl>
              <p className="mt-3 text-sm leading-6 text-stone-600">
                Live packet state: {liveState.available ? "read-only data available" : "fallback is showing"}.
                Nothing on this page changes queue, approval, git, provider, or worker state.
              </p>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] lg:items-start">
            <Card title="Evidence links">
              <dl className="grid gap-2 sm:grid-cols-2">
                <Fact label="Truth Packet" tone={truthPacketTone} value={truthPacket.status} />
                <Fact label="Decision default" tone="stop" value={truthPacket.decisionDefault} />
                <Fact
                  label="Evidence links"
                  tone={truthEvidenceLinks.length > 0 ? "warn" : "stop"}
                  value={`${truthEvidenceLinks.length} review-only link(s)`}
                />
                <Fact
                  label="Receipt browser"
                  tone={receiptEvidenceStatus.available ? "warn" : "stop"}
                  value={
                    receiptEvidenceStatus.available
                      ? `${visibleReceiptItems.length} visible item(s)`
                      : "unavailable"
                  }
                />
                <Fact
                  label="Proof gates"
                  tone={receiptEvidenceStatus.proofGateRecordCount > 0 ? "warn" : "stop"}
                  value={`${receiptEvidenceStatus.proofGateRecordCount} record(s)`}
                />
                <Fact label="Raw diagnostics" tone="quiet" value="/map/raw" />
              </dl>
              <div className="mt-4 grid gap-4 lg:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold text-stone-950">
                    Truth packet links
                  </h3>
                  <div className="mt-2">
                    <ShortList
                      empty="No truth-packet evidence links reported."
                      items={truthEvidenceLinks.map(
                        (link) => `${link.label}: ${link.summary}`,
                      )}
                      limit={3}
                    />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-stone-950">
                    Receipt browser
                  </h3>
                  <div className="mt-2">
                    <ShortList
                      empty="No receipt/evidence items are visible."
                      items={visibleReceiptItems.map(
                        (item) => `${item.label}: ${item.paths.join(", ") || item.status}`,
                      )}
                      limit={4}
                    />
                  </div>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-stone-600">
                Evidence and receipts are linked for review. This browser does not
                create receipts, write evidence, activate queues, consume approvals,
                commit, push, start workers, or promote Cartographer.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <ControlLink href="/map/raw">Open raw diagnostics</ControlLink>
                <ControlLink href="#manual-check">Open manual check</ControlLink>
              </div>
            </Card>

            <Card title="Control cards">
              <dl className="grid gap-2 sm:grid-cols-2">
                <Fact label="Approval" tone="stop" value="disabled until scoped token authority exists" />
                <Fact label="Queue" tone="stop" value="disabled until supervised one-task authority exists" />
                <Fact label="Worker" tone="stop" value="disabled until leased worker authority exists" />
                <Fact label="Git" tone="stop" value="disabled until separate human approval exists" />
              </dl>
              <p className="mt-3 text-sm leading-6 text-stone-600">
                These are status cards only. There are no action buttons on /map.
              </p>
            </Card>
          </div>

          <details className="rounded-lg border border-[#c8b89f] bg-[#fffaf1] p-4 shadow-[0_2px_0_rgba(72,52,32,0.06),0_12px_24px_rgba(72,52,32,0.11)]">
            <summary className="cursor-pointer text-lg font-semibold text-stone-950">
              Show detailed diagnostics and proof
            </summary>
            <div className="mt-4 grid gap-4">
              <Card title="Truth Packet">
                <dl className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                  <Fact label="Packet status" tone={truthPacketTone} value={truthPacket.status} />
                  <Fact label="Decision default" tone="stop" value={truthPacket.decisionDefault} />
                  <Fact
                    label="Unknown fields"
                    tone={truthPacket.unknownFields.length > 0 ? "stop" : "good"}
                    value={truthPacket.unknownFields.length}
                  />
                  <Fact
                    label="Stale fields"
                    tone={truthPacket.staleFields.length > 0 ? "stop" : "good"}
                    value={truthPacket.staleFields.length}
                  />
                  <Fact
                    label="Authority"
                    tone="stop"
                    value={truthPacketAuthorityBlocked ? "false" : "reported; blocked here"}
                  />
                  <Fact
                    label="Confidence"
                    tone={truthPacket.recommendations.confidence === "high" ? "quiet" : "warn"}
                    value={truthPacket.recommendations.confidence}
                  />
                </dl>
                <p className="mt-3 text-sm leading-6 text-stone-600">
                  Unknown or stale packet fields keep /map at NO-GO. Clear facts still do not
                  grant apply, commit, push, queue, approval, or worker authority.
                </p>
              </Card>

          <Card title="Lane Ownership">
            <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              <Fact label="Active lane" tone="warn" value={laneOwnershipPreview.activeLane} />
              <Fact label="Owner" tone="quiet" value={laneOwnershipPreview.owner} />
              <Fact label="Registry state" tone="warn" value={laneOwnershipPreview.registryState} />
              <Fact label="Conflict state" tone="stop" value={laneOwnershipPreview.conflictState} />
            </dl>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Allowed paths
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No allowed path prefixes reported."
                    items={laneOwnershipPreview.allowedPaths}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Forbidden paths
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No forbidden path prefixes reported."
                    items={laneOwnershipPreview.forbiddenPaths}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Protected zones
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No protected zones reported."
                    items={laneOwnershipPreview.protectedZones}
                  />
                </div>
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-stone-950">
                Ownership blocked actions
              </h3>
              <div className="mt-2">
                <ShortList
                  empty="No blocked ownership actions reported."
                  items={laneOwnershipPreview.blockedActions}
                />
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-stone-600">
              Lane ownership is display-only. Lock proposals cannot acquire locks,
              release locks, change the active lane, enforce filesystem ownership,
              start workers, or mutate files from /map.
            </p>
          </Card>

          <Card title="Approval Gate">
            <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <Fact
                label="Approval status"
                tone={approvalGateTone}
                value={approvalTokenStatus.approvalState}
              />
              <Fact
                label="Validation"
                tone={approvalTokenStatus.accepted ? "warn" : "stop"}
                value={approvalTokenStatus.validationStatus}
              />
              <Fact
                label="Consumption preview"
                tone={approvalTokenStatus.consumptionEligible ? "warn" : "stop"}
                value={approvalTokenStatus.consumptionStatus}
              />
              <Fact
                label="Event preview"
                tone="quiet"
                value={approvalTokenStatus.eventPreviewType}
              />
              <Fact
                label="Self-approval"
                tone={approvalTokenStatus.selfApprovalBlocked ? "good" : "stop"}
                value={approvalTokenStatus.selfApprovalBlocked ? "blocked" : "reported; blocked here"}
              />
              <Fact
                label="Approval lane"
                tone="warn"
                value={approvalTokenStatus.laneId}
              />
              <Fact
                label="Single action"
                tone={approvalTokenStatus.singleAction ? "warn" : "stop"}
                value={approvalTokenStatus.singleAction ? "required" : "missing"}
              />
              <Fact
                label="Human issued"
                tone={approvalTokenStatus.issuedByHuman ? "warn" : "stop"}
                value={approvalTokenStatus.issuedByHuman ? "required" : "missing"}
              />
              <Fact
                label="Authority"
                tone="stop"
                value="validation only, no execution approval"
              />
            </dl>
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-stone-950">
                Reason codes
              </h3>
              <div className="mt-2">
                <ShortList
                  empty="No approval reason codes reported; authority still remains false."
                  items={approvalReasonCodes}
                  limit={8}
                />
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-stone-600">
              Approval validation is preview only. Tokens must be lane-scoped,
              single-action, human-issued, unexpired, and externally approved.
              Missing, invalid, stale, or self-approved tokens stay blocked;
              valid preview still grants no apply, commit, push, queue, worker,
              or execution authority.
            </p>
          </Card>

          <Card title="Verification Runner">
            <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <Fact label="Runner status" tone="warn" value={verificationRunnerPreview.status} />
              <Fact label="Command model" tone="warn" value={verificationRunnerPreview.commandModel} />
              <Fact label="Shell" tone="good" value={verificationRunnerPreview.shell} />
              <Fact label="Timeout" tone="quiet" value={verificationRunnerPreview.timeout} />
              <Fact label="Receipts" tone="warn" value={verificationRunnerPreview.receipts} />
              <Fact label="Authority" tone="stop" value={verificationRunnerPreview.authority} />
            </dl>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Exact allowed commands
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No exact commands approved."
                    items={verificationRunnerPreview.allowedCommands}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Blocked command classes
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No blocked command classes reported."
                    items={verificationRunnerPreview.blockedCommands}
                  />
                </div>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-stone-600">
              Verification status is display-only on /map. This page cannot run
              commands, POST to the runner, install packages, execute workflows,
              queue work, stage, commit, push, branch, reset, clean, or open a shell.
            </p>
          </Card>

          <Card title="Queue And Workflow Runtime">
            <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              <Fact label="Queue status" tone="warn" value={queueStatus.queueStatus} />
              <Fact label="Run-next" tone="warn" value={queueStatus.runNextStatus} />
              <Fact
                label="One task"
                tone={queueStatus.selectionAvailable ? "warn" : "quiet"}
                value={queueStatus.selectionAvailable ? "selection preview only" : "not selectable"}
              />
              <Fact
                label="Execution"
                tone={queueStatus.executionAvailable ? "stop" : "good"}
                value={queueStatus.executionAvailable ? "blocked on /map" : "not available"}
              />
              <Fact label="Workflow status" tone="warn" value={workflowStatus.workflowStatus} />
              <Fact label="Active runs" tone="quiet" value={workflowStatus.activeRunCount} />
              <Fact label="Blocked steps" tone="warn" value={workflowStatus.blockedStepCount} />
              <Fact
                label="Kill switch"
                tone="warn"
                value={cartographerStopControlStatus.killSwitchState}
              />
            </dl>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Queue facts
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No queue facts reported."
                    items={[
                      `${queueStatus.allowedTaskClassCount} allowed task class(es)`,
                      `${queueStatus.taskStatusCount} modeled status(es)`,
                      `trust tier: ${queueStatus.requiredTrustTier}`,
                      queueStatus.detail,
                    ]}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Workflow blockers
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No workflow blockers reported."
                    items={workflowStatus.blockers}
                    limit={5}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Stop controls
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No stop-control previews reported."
                    items={cartographerStopControlStatus.controls.map(
                      (control) => `${control.label}: ${control.status}`,
                    )}
                  />
                </div>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-stone-600">
              Queue and workflow state is display-only. /map can show one-task
              selection status, pause/resume/cancel/timeout previews, and kill-switch
              state, but cannot run queues, resume work, start background loops,
              dispatch workers, or perform git actions.
            </p>
          </Card>

          <Card title="Worker Control">
            <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <Fact label="Registry" tone="warn" value={workerControlPreview.registryStatus} />
              <Fact label="Dispatch" tone="warn" value={workerControlPreview.dispatchStatus} />
              <Fact label="Leases" tone="warn" value={workerControlPreview.leaseStatus} />
              <Fact label="File zones" tone="warn" value={workerControlPreview.fileZoneStatus} />
              <Fact label="Stale closeout" tone="warn" value={workerControlPreview.staleCloseout} />
              <Fact label="Authority" tone="stop" value={workerControlPreview.authority} />
            </dl>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Required identity fields
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No worker identity fields reported."
                    items={workerControlPreview.identities}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Worker blocked actions
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No worker blocked actions reported."
                    items={workerControlPreview.blockedActions}
                  />
                </div>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-stone-600">
              Worker state is display-only on /map. Workers need identity,
              leases, exact file zones, conflict checks, handoff packets, stale
              closeout proposals, and Cartographer-visible queue state before
              any later approved dispatch.
            </p>
          </Card>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.14fr)_minmax(0,0.86fr)] xl:items-start">
            <Card title="Dirty Tree Groups">
            <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              <Fact
                label="Total dirty files"
                tone={dirtyTreePreview.totalDirtyFiles > 0 ? "warn" : "good"}
                value={dirtyTreePreview.totalDirtyFiles}
              />
              <Fact label="Tracked" value={dirtyTreePreview.trackedCount} />
              <Fact label="Untracked" value={dirtyTreePreview.untrackedCount} />
              <Fact
                label="Protected lanes"
                tone={dirtyTreePreview.protectedLaneCount > 0 ? "warn" : "good"}
                value={dirtyTreePreview.protectedLaneCount}
              />
            </dl>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Likely safe docs files
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No docs-like dirty files reported."
                    items={dirtyTreePreview.likelySafeDocsFiles}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Risky source files
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No risky source files reported."
                    items={dirtyTreePreview.riskySourceFiles}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Generated/cache files
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No generated/cache files reported."
                    items={dirtyTreePreview.generatedCacheFiles}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Unknown files
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No unknown files reported."
                    items={dirtyTreePreview.unknownFiles}
                  />
                </div>
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-stone-950">
                Manual review notes
              </h3>
              <div className="mt-2">
                <ShortList
                  empty="No cleanup plan needed."
                  items={dirtyTreePreview.cleanupPlanPreview}
                />
              </div>
            </div>
            <div className="mt-4">
              <ControlLink href="/map/raw">Open raw dirty details</ControlLink>
            </div>
            </Card>

            <Card title="Commit And Push Readiness">
            <dl className="grid gap-2 sm:grid-cols-2">
              <Fact label="Plan" value={gitOperatorPreview.plan} />
              <Fact
                label="Commit readiness"
                tone={commitReadiness === "blocked" ? "stop" : "warn"}
                value={commitReadiness}
              />
              <Fact
                label="Commit gate"
                tone="warn"
                value={gitOperatorPreview.commitGate}
              />
              <Fact
                label="Staging"
                tone="warn"
                value={gitOperatorPreview.staging}
              />
              <Fact
                label="Branch/worktree"
                tone="warn"
                value={gitOperatorPreview.branchWorktree}
              />
              <Fact
                label="Push readiness"
                tone={
                  branchPushPreview.pushReadiness === "not-needed"
                    ? "quiet"
                    : branchPushPreview.pushReadiness === "proof-needed"
                      ? "warn"
                      : "stop"
                }
                value={branchPushPreview.pushReadiness}
              />
              <Fact label="Push boundary" tone="warn" value={gitOperatorPreview.push} />
              <Fact label="Auto push" tone="stop" value={gitOperatorPreview.autoPush} />
              <Fact label="Rollback" tone="warn" value={gitOperatorPreview.rollback} />
              <Fact
                label="Merge risk"
                tone={branchPushPreview.mergeRisk === "blocked" ? "stop" : "warn"}
                value={branchPushPreview.mergeRisk}
              />
              <Fact label="Authority" tone="stop" value="No git action controls" />
            </dl>
            <div className="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-1">
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Missing proof
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No proof gaps reported."
                    items={missingProof}
                    limit={5}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Commit blockers
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No blocked commit files reported."
                    items={commitPreview.filesThatShouldNotBeCommittedYet}
                    limit={5}
                  />
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-stone-950">
                  Push blockers
                </h3>
                <div className="mt-2">
                  <ShortList
                    empty="No push blockers reported, but /map still cannot push."
                    items={branchPushPreview.pushBlockers}
                    limit={5}
                  />
                </div>
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-stone-950">
                Git operator blocked actions
              </h3>
              <div className="mt-2">
                <ShortList
                  empty="No blocked git actions reported."
                  items={gitOperatorPreview.blockedActions}
                  limit={9}
                />
              </div>
            </div>
            <dl className="mt-4">
              <Fact
                label="Suggested message draft"
                value={commitPreview.suggestedCommitMessageDraft}
              />
            </dl>
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-stone-950">
                Changed areas
              </h3>
              <div className="mt-2">
                <ShortList
                  empty="No changed areas reported."
                  items={branchPushPreview.changedAreas}
                />
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-stone-600">
              Commit, push, branch, worktree, and rollback state is display-only
              on /map. Human approval previews do not grant broad staging,
              branch creation, auto-push, rollback execution, or cleanup
              authority.
            </p>
            </Card>
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.12fr)_minmax(0,0.88fr)] xl:items-start">
            <Card title="Project Tracker">
            <div className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
              {cartographerDefaultProjectCardPreviews.map((project) => (
                <article
                  className="rounded-lg border border-stone-200 bg-white p-3"
                  key={project.projectId}
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <h3 className="text-sm font-semibold text-stone-950">
                      {project.label}
                    </h3>
                    <StatusPill
                      tone={project.state === "blocked" ? "stop" : "quiet"}
                    >
                      {project.state}
                    </StatusPill>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-stone-600">
                    {project.previewNextStep}
                  </p>
                  <p className="mt-3 text-xs leading-5 text-stone-500">
                    Signals: {project.visibleRepoSignals.slice(0, 3).join(", ")}
                  </p>
                </article>
              ))}
            </div>
            </Card>

            <div className="grid gap-4">
              <Card title="Daily Driver Proof">
                <dl className="grid gap-2 sm:grid-cols-2">
                  <Fact label="Supervised proof" tone="warn" value="10-task receipt validation only" />
                  <Fact label="Soak proof" tone="warn" value="24h and 72h evidence, no self-promotion" />
                  <Fact label="Drills" tone="warn" value="dirty tree, kill switch, rollback" />
                  <Fact label="Promotion" tone="stop" value="human decision required" />
                </dl>
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-stone-950">
                    Daily-driver checklist
                  </h3>
                  <div className="mt-2">
                    <ShortList
                      empty="Daily-driver proof has not been summarized."
                      items={dailyDriverProofItems}
                      limit={5}
                    />
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-stone-600">
                  This checklist is display-only. Passing proof does not create full auto,
                  promote trust tier, execute queues, write files, commit, or push.
                </p>
              </Card>

              <Card title="Trust Tier Gate">
                <dl className="grid gap-2 sm:grid-cols-2">
                  <Fact label="Current tier" tone="warn" value={trustTierGate.currentTier} />
                  <Fact label="Gate status" tone="stop" value={trustTierGate.gateStatus} />
                  <Fact label="Next decision gate" tone="stop" value={trustTierGate.nextDecisionGate} />
                  <Fact label="Authority" tone="stop" value="blocked until separate human decision" />
                </dl>
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-stone-950">
                    Blocked authorities
                  </h3>
                  <div className="mt-2">
                    <ShortList
                      empty="No blocked authorities reported."
                      items={trustTierGate.blockedAuthorities}
                    />
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-stone-600">
                  Trust-tier status is display-only. The next gate can recommend
                  advance, hold, or demote, but it cannot record promotion or start
                  branch, worktree, queue, commit, push, or worker actions.
                </p>
              </Card>

              <Card title="Advisory Fleet">
                <p className="mb-3 text-sm leading-6 text-stone-600">
                  Agent Advisory Fleet is collapsed by default. Helpers can summarize map context, but cannot
                  mutate state, start workers, run queues, call providers, approve, apply, commit, or push.
                </p>
                <details className="rounded-lg border border-stone-200 bg-stone-50 p-3">
                  <summary className="cursor-pointer text-sm font-semibold text-stone-950">
                    Show advisory helper summaries
                  </summary>
                  <ul className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
                    {mapAdvisoryHelpers.map((agent) => (
                      <li
                        className="rounded-md border border-stone-200 bg-white p-3"
                        key={agent.name}
                      >
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <h3 className="text-sm font-semibold text-stone-950">
                            {agent.name}
                          </h3>
                          <StatusPill tone="quiet">advisory_only</StatusPill>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-stone-600">
                          {agent.proposal}
                        </p>
                        <p className="mt-2 text-xs leading-5 text-stone-500">
                          Watching: {agent.context}
                        </p>
                        <p className="mt-2 text-xs leading-5 text-stone-500">
                          Blocked: {agent.blockedActions}
                        </p>
                      </li>
                    ))}
                  </ul>
                </details>
              </Card>

          <Card title="Manual Check">
                <p className="text-sm leading-6 text-stone-600">
                  One copy-paste terminal block for human verification. The page does not run it.
                </p>
                <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-3">
                  <ControlLink href="/map/raw">Open raw diagnostics</ControlLink>
                  <ControlLink href="#attention">Review blockers</ControlLink>
                  <ControlLink href="#next-safe-step">Preview next step</ControlLink>
                </div>
                <div id="manual-check">
                  <CommandBlock value={manualCheck} />
                </div>
              </Card>
            </div>
          </div>
            </div>
          </details>
          </div>
      </main>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
