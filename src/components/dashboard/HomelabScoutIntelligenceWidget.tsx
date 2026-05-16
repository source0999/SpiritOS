"use client";

import { useState } from "react";
import { Ban, BrainCircuit, Check, Pause, Play, Plus, RefreshCw, Search, X } from "lucide-react";
import Link from "next/link";

import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";
import { useScoutOverview, type ScoutOverviewFetchState } from "@/hooks/useScoutOverview";
import { buildScoutHumanReadModel } from "@/lib/scout-human-readable";
import type {
  ScoutOverview,
  ScoutDiscoveryJob,
  ScoutDiscoveryJobs,
  ScoutPacket,
  ScoutPromotionItem,
  ScoutSchedulerJob,
  ScoutSourceCandidate,
  ScoutSourceCandidates,
  ScoutSourceReviewEvent,
  ScoutSourceActionResult,
  ScoutSourceSummary,
} from "@/lib/scout-overview";

type ScoutFeedTab =
  | "useful"
  | "saved"
  | "review"
  | "promoted"
  | "sourceQueue"
  | "discovery"
  | "sources"
  | "diagnostics";

const scoutFeedTabs: Array<{ id: ScoutFeedTab; label: string }> = [
  { id: "useful", label: "Overview" },
  { id: "saved", label: "Saved Packets" },
  { id: "review", label: "Packet Gate" },
  { id: "promoted", label: "Promoted" },
  { id: "sourceQueue", label: "Source Gate" },
  { id: "discovery", label: "Discovery Gate" },
  { id: "sources", label: "Sources" },
  { id: "diagnostics", label: "Diagnostics" },
];

function countValue(value: number | undefined): string {
  return typeof value === "number" ? value.toLocaleString() : "-";
}

function packetSummary(packet: ScoutPacket): string {
  return packet.summary ?? packet.title ?? "Untitled Scout packet";
}

function packetId(packet: ScoutPacket): string | null {
  return packet.packet_id ?? packet.id ?? null;
}

function packetTitle(packet: ScoutPacket): string {
  return packet.title ?? sourceLabel(packet);
}

function packetStatus(packet: ScoutPacket): string {
  return (
    packet.human_status_label ??
    packet.status_explanation?.label ??
    packet.effective_status ??
    packet._verdict?.effective_status ??
    packet._verdict?.decision ??
    packet.status ??
    "unknown"
  );
}

function sourceLabel(packet: ScoutPacket): string {
  const label = packet.source_label ?? packet.provenance?.source_label;
  if (label) return label;

  const uri =
    packet.source_uri ??
    packet.source_url ??
    packet.uri ??
    packet.provenance?.source_uri ??
    packet.provenance?.source_url ??
    packet.provenance?.uri;

  if (!uri) return "source unknown";

  try {
    return new URL(uri).host || uri;
  } catch {
    return uri;
  }
}

function trustLabel(packet: ScoutPacket): string | null {
  return packet.trust_label ?? null;
}

function sourceTrustLabel(packet: ScoutPacket, sources: ScoutSourceSummary[]): string | null {
  if (packet.source_trust_label) return packet.source_trust_label;
  const packetTrust = trustLabel(packet);
  if (packetTrust) return packetTrust;

  const packetSourceUri =
    packet.source_uri ??
    packet.source_url ??
    packet.uri ??
    packet.provenance?.source_uri ??
    packet.provenance?.source_url ??
    packet.provenance?.uri;
  const packetSourceLabel = sourceLabel(packet);

  const source = sources.find((item) => {
    const sourceUri = item.source_uri;
    const sourceLabel = item.label;
    return (
      (packetSourceUri && sourceUri === packetSourceUri) ||
      (packetSourceLabel && sourceLabel === packetSourceLabel)
    );
  });

  return source?.trust_label ?? null;
}

function packetUsefulnessReason(packet: ScoutPacket): string | null {
  return packet.usefulness_reason ?? packet.status_explanation?.help ?? null;
}

function packetRecommendedAction(packet: ScoutPacket): string | null {
  return packet.recommended_action ? humanizeScoutLabel(packet.recommended_action) : null;
}

function formatDateTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function humanizeScoutLabel(value: string | null | undefined): string {
  if (!value) return "-";
  return value.replaceAll("_", " ");
}

function humanScoutMetricLabel(label: string): string {
  const labels: Record<string, string> = {
    Scanned: "Items found",
    Cleaned: "Cleaned up",
    Summarized: "Summaries made",
    Checked: "Verified",
    "Packet Gate": "Packet review",
    "Source Gate": "Sources to Approve",
    "Discovery Jobs": "Manual Search Plans",
    Sources: "Watching Now",
    "Stored Only": "Stored Only",
    "Semantic Memory": "Memory writes",
    Promoted: "Promoted briefings",
  };
  return labels[label] ?? label;
}

type ScoutSafetySnapshot = {
  candidateCount: number | null;
  approvedCount: number | null;
  sourceCount: number | null;
};

function sumCandidateCounts(counts: ScoutSourceCandidates["counts"] | undefined): number | null {
  if (!counts) return null;
  return Object.values(counts).reduce<number>(
    (total, value) => total + (typeof value === "number" ? value : 0),
    0,
  );
}

async function readScoutSafetySnapshot(fallback: ScoutOverview): Promise<ScoutSafetySnapshot> {
  let candidateCounts = fallback.source_candidates?.counts;
  let sourceCount = fallback.sources?.length ?? null;

  try {
    const [candidateRes, overviewRes] = await Promise.all([
      fetch("/api/scout/source-candidates?limit=1", { cache: "no-store" }),
      fetch("/api/scout/overview?limit=1", { cache: "no-store" }),
    ]);
    if (candidateRes.ok) {
      const candidateJson = (await candidateRes.json().catch(() => null)) as ScoutSourceCandidates | null;
      candidateCounts = candidateJson?.counts ?? candidateCounts;
    }
    if (overviewRes.ok) {
      const overviewJson = (await overviewRes.json().catch(() => null)) as ScoutOverview | null;
      sourceCount = overviewJson?.sources?.length ?? sourceCount;
    }
  } catch {
    // Keep the last loaded dashboard data as the fallback safety snapshot.
  }

  return {
    candidateCount: sumCandidateCounts(candidateCounts),
    approvedCount: candidateCounts?.approved ?? null,
    sourceCount,
  };
}

function deltaText(before: number | null, after: number | null): string {
  if (before === null || after === null) return "unknown";
  const delta = after - before;
  return `${delta >= 0 ? "+" : ""}${delta}`;
}

function discoveryResultCount(body: unknown): number {
  if (
    body &&
    typeof body === "object" &&
    "result" in body &&
    body.result &&
    typeof body.result === "object" &&
    "sources" in body.result &&
    Array.isArray(body.result.sources)
  ) {
    return body.result.sources.length;
  }
  return 0;
}

function extractionCreatedCount(body: unknown): number {
  if (
    body &&
    typeof body === "object" &&
    "extraction" in body &&
    body.extraction &&
    typeof body.extraction === "object" &&
    "candidates_created" in body.extraction &&
    typeof body.extraction.candidates_created === "number"
  ) {
    return body.extraction.candidates_created;
  }
  return 0;
}

function recheckStatus(value: unknown, key: "previous" | "new"): string {
  if (!value || typeof value !== "object") return "unknown";
  const body = value as Record<"previous" | "new", unknown>;
  const state = body[key];
  if (!state || typeof state !== "object") return "unknown";
  const status = (state as { status?: unknown }).status;
  if (typeof status === "string") return humanizeScoutLabel(status);
  return "unknown";
}

function recheckFindingCount(value: unknown): number {
  if (
    value &&
    typeof value === "object" &&
    "findings" in value &&
    Array.isArray(value.findings)
  ) {
    return value.findings.length;
  }
  return 0;
}

function schedulerJobTime(jobs: ScoutSchedulerJob[] | undefined, needle: string): string | null {
  const job = jobs?.find((item) => item.id?.toLowerCase().includes(needle));
  if (!job?.next_run_time) return null;
  const date = new Date(job.next_run_time);
  if (Number.isNaN(date.getTime())) return job.next_run_time;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function badgeForState(state: ScoutOverviewFetchState) {
  if (state === "loading") return { variant: "pending" as const, label: "Loading" };
  if (state === "error") return { variant: "offline" as const, label: "Unavailable" };
  return { variant: "live" as const, label: "Online" };
}

function scoutSummaryBadge(
  state: ScoutOverviewFetchState,
  needsReview: number,
  hasQueueClutter: boolean,
) {
  if (state === "loading") return { variant: "pending" as const, label: "Loading" };
  if (state === "error") return { variant: "offline" as const, label: "Offline" };
  if (needsReview > 0 || hasQueueClutter) {
    return { variant: "pending" as const, label: "Needs attention" };
  }
  return { variant: "live" as const, label: "Online" };
}

function ScoutPriorityCard({
  label,
  value,
  help,
}: {
  label: string;
  value: string;
  help: string;
}) {
  return (
    <div className="dashboard-demo-v4-scout-count">
      <strong>{value}</strong>
      <span>{label}</span>
      <span>{help}</span>
    </div>
  );
}

export function HomelabScoutIntelligenceWidget() {
  const { data, state } = useScoutOverview();
  const model = data ? buildScoutHumanReadModel(data) : null;
  const badge = scoutSummaryBadge(
    state,
    model?.needsReview ?? 0,
    Boolean(model && (model.staleJobs > 0 || model.duplicateJobs > 0 || model.noisyJobs > 0)),
  );
  const memoryLine = model?.memoryWritesOff ? "Memory writes off" : "Memory writes need review";
  const summary =
    state === "loading"
      ? "Checking whether Scout is online."
      : state === "error"
        ? "Scout is offline or the overview route is unavailable."
        : model?.summarySentence ?? "Scout is online. Nothing needs approval right now.";

  return (
    <section
      aria-label="Scout intelligence"
      className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-card dashboard-demo-v4-scout-card"
    >
      <div className="dashboard-demo-v4-card-header">
        <div className="dashboard-demo-v4-card-title-row">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <BrainCircuit className="h-5 w-5" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Scout Intelligence</p>
            <h2>Scout Intelligence</h2>
            <p className="dashboard-demo-v4-card-subtitle">
              Watches trusted sources and brings useful intelligence for review.
            </p>
          </div>
        </div>
        <HomelabStatusBadge variant={badge.variant}>{badge.label}</HomelabStatusBadge>
      </div>

      {state === "loading" ? (
        <div className="dashboard-demo-v4-skeleton-list" aria-label="Loading Scout overview">
          <div />
          <div />
        </div>
      ) : null}

      {state !== "loading" ? (
        <div className="dashboard-demo-v4-scout-body">
          <div className="dashboard-demo-v4-scout-summary" aria-label="Scout status summary">
            <p>{summary}</p>
            <p className="dashboard-demo-v4-empty-copy">
              {model?.queueSentence ?? "Queued searches are saved manual plans, not active forever."}
            </p>
          </div>

          {model ? (
            <div className="dashboard-demo-v4-scout-counts" aria-label="Scout priority summary">
              <ScoutPriorityCard
                label="Review Inbox"
                value={countValue(model.needsReview)}
                help={`${countValue(model.sourceSuggestions)} source suggestions, ${countValue(
                  model.packetReviews,
                )} packet reviews`}
              />
              <ScoutPriorityCard
                label="Promoted Briefings"
                value={countValue(model.usefulFinds)}
                help="Promoted briefings"
              />
              <ScoutPriorityCard
                label="Manual Search Plans"
                value={countValue(model.queuedJobs)}
                help={model.queueSentence}
              />
              <ScoutPriorityCard
                label="Watching Now"
                value={countValue(model.pollableSourceCount)}
                help={
                  model.storedOnlySourceCount > 0
                    ? `${countValue(model.storedOnlySourceCount)} stored only`
                    : "Active pollable sources"
                }
              />
              <ScoutPriorityCard
                label="Safety"
                value={memoryLine}
                help="Manual approval required"
              />
            </div>
          ) : null}

          <div className="dashboard-demo-v4-scout-actions">
            <Link href="/intelligence" className="dashboard-demo-v4-scout-link-button">
              Open Intelligence Center
            </Link>
            <Link href="/intelligence#safety-diagnostics" className="dashboard-demo-v4-scout-link-button-secondary">
              Safety and Diagnostics
            </Link>
          </div>

          {data ? (
            <details className="dashboard-demo-v4-scout-details">
              <summary>Pipeline details</summary>
              <ScoutCounts overview={data} />
            </details>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function ScoutCounts({ overview }: { overview: ScoutOverview }) {
  const counts = overview.counts ?? {};
  const backlog = overview.backlog ?? {};
  const memory = overview.human_summary?.memory_status;
  const promotion = overview.human_summary?.promotion_status;
  const model = buildScoutHumanReadModel(overview);
  const sourceCandidateCounts = overview.source_candidates?.counts ?? {};
  const sourceQueueCount =
    (sourceCandidateCounts.recommended ?? 0) + (sourceCandidateCounts.needs_review ?? 0);
  const discoveryJobCount = overview.discovery_jobs?.count ?? overview.discovery_jobs?.jobs?.length ?? 0;
  const discoveryBudget = overview.discovery_jobs?.budget;
  const scanFlow = overview.human_summary?.scan_flow;
  const stats =
    scanFlow && scanFlow.length > 0
      ? scanFlow.map((item) => [item.label, item.count] as const)
      : ([
          ["Items found", counts.raw_event_index ?? counts.raw_events],
          ["Cleaned up", counts.extracted_artifacts ?? counts.artifacts],
          ["Summaries made", counts.packets],
          ["Verified", counts.verdicts],
        ] as const);
  const needsReview = backlog.debugger_pending_without_verdict ?? backlog.debugger_pending_packets;
  const metrics = [
    ...stats,
    ["Packet Gate", needsReview] as const,
    [
      "Semantic Memory",
      memory?.active || (counts.packet_embeddings ?? 0) > 0 ? "Active" : "Inactive",
    ] as const,
    ["Promoted", promotion?.promoted_count] as const,
    ["Source Gate", sourceQueueCount] as const,
    ["Discovery Jobs", discoveryJobCount] as const,
    ["Budget Left", discoveryBudget?.remaining_today] as const,
    ["Sources", model.pollableSourceCount] as const,
    ["Stored Only", model.storedOnlySourceCount] as const,
  ];

  return (
    <div className="dashboard-demo-v4-scout-counts" aria-label="Scout counts">
      {metrics.map(([label, value]) => (
        <div key={label} className="dashboard-demo-v4-scout-count">
          <strong>{typeof value === "string" ? value : countValue(value)}</strong>
          <span>{humanScoutMetricLabel(label)}</span>
        </div>
      ))}
    </div>
  );
}

function ScoutScheduler({ overview }: { overview: ScoutOverview }) {
  const scheduler = overview.scheduler ?? {};
  const running = scheduler.scheduler_running ?? scheduler.running ?? false;
  const jobCount = scheduler.job_count ?? scheduler.jobs?.length ?? 0;
  const synthesis = schedulerJobTime(scheduler.jobs, "synth");
  const debuggerJob = schedulerJobTime(scheduler.jobs, "debug");

  return (
    <div className="dashboard-demo-v4-scout-scheduler" aria-label="Scout scheduler summary">
      <div>
        <span>Scheduler</span>
        <strong>{running ? "Running" : "Paused"}</strong>
      </div>
      <div>
        <span>Jobs</span>
        <strong>{jobCount}</strong>
      </div>
      <div>
        <span>Next Summary Run</span>
        <strong>{synthesis ?? "-"}</strong>
      </div>
      <div>
        <span>Next Safety Check</span>
        <strong>{debuggerJob ?? "-"}</strong>
      </div>
    </div>
  );
}

function ScoutNotes({ overview }: { overview: ScoutOverview }) {
  const headline = overview.human_summary?.headline;
  const memory = overview.human_summary?.memory_status;
  const promotion = overview.human_summary?.promotion_status;
  const promotedCount = countValue(promotion?.promoted_count);

  return (
    <div className="dashboard-demo-v4-scout-summary" aria-label="Scout status summary">
      <p>{headline ?? "Scout is running in read-only inspection mode."}</p>
      <p className="dashboard-demo-v4-empty-copy">
        Unique scans are counted once. Idle runs after backlog drain are normal.
      </p>
      <p className="dashboard-demo-v4-empty-copy">
        {memory?.label ?? "Semantic memory inactive"} {"\u00b7"}{" "}
        {memory?.mode_label ?? (memory?.active ? "Read-only context" : "Inactive")} {"\u00b7"}{" "}
        {memory?.write_enabled ? "Memory writes enabled" : "No automatic memory writes"} {"\u00b7"}{" "}
        {promotedCount} promoted
      </p>
      <p className="dashboard-demo-v4-empty-copy">
        {memory?.reason ??
          "Scout is storing packets and source decisions, but it is not writing into proxy memory or coding context automatically."}
      </p>
      {memory?.safety_label ? (
        <p className="dashboard-demo-v4-empty-copy">{memory.safety_label}</p>
      ) : null}
    </div>
  );
}

function ScoutPackets({
  packets,
  sources,
  emptyLabel,
  busyPacketId,
  onQueue,
  onRecheck,
}: {
  packets: ScoutPacket[];
  sources: ScoutSourceSummary[];
  emptyLabel: string;
  busyPacketId: string | null;
  onQueue: (packet: ScoutPacket) => void;
  onRecheck: (packet: ScoutPacket) => void;
}) {
  if (packets.length === 0) {
    return <p className="dashboard-demo-v4-scout-empty">{emptyLabel}</p>;
  }

  return (
    <ul className="dashboard-demo-v4-scout-packet-list">
      {packets.map((packet, index) => {
        const tags = (packet.entity_tags ?? packet.tags)?.filter(Boolean).slice(0, 3) ?? [];
        const trust = sourceTrustLabel(packet, sources);
        const id = packetId(packet);
        const promotionStatus = packet.promotion_status;
        const queueDisabled =
          !id || promotionStatus === "queued" || promotionStatus === "approved" || busyPacketId === id;
        const recheckDisabled = !id || busyPacketId === id;
        const queueLabel =
          promotionStatus === "queued"
            ? "Packet Queued"
            : promotionStatus === "approved"
              ? "Packet Promoted"
              : promotionStatus === "rejected"
                ? "Queue Packet Again"
                : "Queue Packet";
        return (
          <li key={packet.packet_id ?? packet.id ?? `${packetSummary(packet)}-${index}`}>
            <div className="dashboard-demo-v4-scout-packet-topline">
              <div className="dashboard-demo-v4-scout-packet-heading">
                <span>{sourceLabel(packet)}</span>
                <strong>{packetTitle(packet)}</strong>
              </div>
              <em className="dashboard-demo-v4-scout-status-chip">{packetStatus(packet)}</em>
            </div>
            {trust ? (
              <div className="dashboard-demo-v4-scout-trust-row">
                <span className="dashboard-demo-v4-scout-trust-chip">{trust}</span>
              </div>
            ) : null}
            <p className="dashboard-demo-v4-scout-packet-summary">{packetSummary(packet)}</p>
            {packetUsefulnessReason(packet) ? (
              <p className="dashboard-demo-v4-scout-source-meta">
                {packet.usefulness_label ?? packetStatus(packet)}: {packetUsefulnessReason(packet)}
              </p>
            ) : null}
            {packetRecommendedAction(packet) || packet.confidence_label ? (
              <div className="dashboard-demo-v4-scout-tags">
                {packetRecommendedAction(packet) ? (
                  <span>Action: {packetRecommendedAction(packet)}</span>
                ) : null}
                {packet.confidence_label ? <span>Confidence: {packet.confidence_label}</span> : null}
              </div>
            ) : null}
            {tags.length > 0 ? (
              <div className="dashboard-demo-v4-scout-tags">
                {tags.map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            ) : null}
            <div className="dashboard-demo-v4-scout-actions">
              <button
                type="button"
                onClick={() => onQueue(packet)}
                disabled={queueDisabled}
                aria-label={`${queueLabel} ${packetTitle(packet)}`}
              >
                {queueLabel}
              </button>
              <button
                type="button"
                onClick={() => onRecheck(packet)}
                disabled={recheckDisabled}
                aria-label={`Recheck Packet ${packetTitle(packet)}`}
              >
                <RefreshCw className="h-3.5 w-3.5" aria-hidden />
                {busyPacketId === id ? "Rechecking Packet" : "Recheck Packet"}
              </button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function ScoutPromotionCards({
  promotions,
  emptyLabel,
  busyPromotionId,
  onApprove,
  onReject,
}: {
  promotions: ScoutPromotionItem[];
  emptyLabel: string;
  busyPromotionId: string | null;
  onApprove: (promotion: ScoutPromotionItem) => void;
  onReject: (promotion: ScoutPromotionItem) => void;
}) {
  if (promotions.length === 0) {
    return <p className="dashboard-demo-v4-scout-empty">{emptyLabel}</p>;
  }

  return (
    <ul className="dashboard-demo-v4-scout-packet-list">
      {promotions.map((promotion) => {
        const packet = {
          ...(promotion.packet ?? {}),
          title: promotion.packet?.title ?? promotion.summary ?? promotion.packet_id,
          summary: promotion.packet?.summary ?? promotion.summary,
          source_label: promotion.packet?.source_label ?? promotion.source_label,
          trust_label: promotion.packet?.trust_label ?? promotion.trust_label,
          human_status_label:
            promotion.packet?.human_status_label ?? promotion.human_status_label,
          effective_status: promotion.packet?.effective_status ?? promotion.effective_status,
          entity_tags: promotion.packet?.entity_tags ?? promotion.entity_tags,
        } as ScoutPacket;
        const title = packetTitle(packet);
        const tags = (packet.entity_tags ?? packet.tags)?.filter(Boolean).slice(0, 3) ?? [];
        const isQueued = promotion.status === "queued";
        const busy = busyPromotionId === promotion.promotion_id;
        const promotionEvidence = promotionEvidenceRows(promotion);
        return (
          <li key={promotion.promotion_id}>
            <div className="dashboard-demo-v4-scout-packet-topline">
              <div className="dashboard-demo-v4-scout-packet-heading">
                <span>{sourceLabel(packet)}</span>
                <strong>{title}</strong>
              </div>
              <em className="dashboard-demo-v4-scout-status-chip">
                {promotion.status === "approved"
                  ? "Promoted"
                  : promotion.status === "rejected"
                    ? "Rejected"
                    : "Queued"}
              </em>
            </div>
            {packet.trust_label ? (
              <div className="dashboard-demo-v4-scout-trust-row">
                <span className="dashboard-demo-v4-scout-trust-chip">{packet.trust_label}</span>
              </div>
            ) : null}
            <p className="dashboard-demo-v4-scout-packet-summary">{packetSummary(packet)}</p>
            {promotion.rejected_reason ? (
              <p className="dashboard-demo-v4-scout-source-meta">{promotion.rejected_reason}</p>
            ) : null}
            {promotion.reason ? (
              <p className="dashboard-demo-v4-scout-source-meta">{promotion.reason}</p>
            ) : null}
            {promotionEvidence.length > 0 ? (
              <dl
                className="dashboard-demo-v4-scout-evidence-grid"
                aria-label={`${title} promotion evidence`}
              >
                {promotionEvidence.map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            ) : null}
            {tags.length > 0 ? (
              <div className="dashboard-demo-v4-scout-tags">
                {tags.map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            ) : null}
            {isQueued ? (
              <div className="dashboard-demo-v4-scout-actions">
                <button type="button" onClick={() => onApprove(promotion)} disabled={busy}>
                  <Check className="h-3.5 w-3.5" aria-hidden />
                  Promote Packet
                </button>
                <button type="button" onClick={() => onReject(promotion)} disabled={busy}>
                  <X className="h-3.5 w-3.5" aria-hidden />
                  Reject Packet
                </button>
              </div>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

function promotionEvidenceRows(promotion: ScoutPromotionItem): Array<[string, string]> {
  const rows: Array<[string, string | null | undefined]> = [
    ["Queued By", promotion.requested_by],
    ["Queued At", formatDateTime(promotion.requested_at)],
    ["Promotion Reason", promotion.reason],
  ];

  if (promotion.status === "approved") {
    rows.push(["Promoted By", promotion.approved_by]);
    rows.push(["Promoted At", formatDateTime(promotion.approved_at)]);
  }

  if (promotion.status === "rejected") {
    rows.push(["Rejected At", formatDateTime(promotion.rejected_at)]);
    rows.push(["Rejected Reason", promotion.rejected_reason]);
  }

  return rows.filter((row): row is [string, string] => Boolean(row[1]));
}

function ScoutSourceCards({ sources }: { sources: ScoutSourceSummary[] }) {
  if (sources.length === 0) {
    return <p className="dashboard-demo-v4-scout-empty">No source data available yet.</p>;
  }

  return (
    <ul className="dashboard-demo-v4-scout-packet-list dashboard-demo-v4-scout-source-list">
      {sources.map((source, index) => {
        const label = source.label ?? source.source_uri ?? `Source ${index + 1}`;
        const lastPolled = formatDateTime(source.last_polled_at);

        return (
          <li key={source.source_uri ?? label}>
            <div className="dashboard-demo-v4-scout-packet-topline">
              <div className="dashboard-demo-v4-scout-packet-heading">
                <span>Source</span>
                <strong>{label}</strong>
              </div>
              <em className="dashboard-demo-v4-scout-status-chip">
                {source.health_label ?? "Health unknown"}
              </em>
            </div>
            {source.trust_label ? (
              <div className="dashboard-demo-v4-scout-trust-row">
                <span className="dashboard-demo-v4-scout-trust-chip">{source.trust_label}</span>
              </div>
            ) : null}
            <p className="dashboard-demo-v4-scout-packet-summary">
              {countValue(source.packets_total)} packet
              {source.packets_total === 1 ? "" : "s"} {"\u00b7"}{" "}
              {countValue(source.packets_surfaced)} useful {"\u00b7"}{" "}
              {countValue(source.packets_stored)} saved {"\u00b7"}{" "}
              {countValue(source.packets_ignored)} ignored
            </p>
            {lastPolled ? (
              <p className="dashboard-demo-v4-scout-source-meta">Last polled {lastPolled}</p>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

function percentScore(value: number | null | undefined): string {
  if (typeof value !== "number") return "-";
  return `${Math.round(value * 100)}%`;
}

function sourceCandidateTitle(candidate: ScoutSourceCandidate): string {
  try {
    if (candidate.canonical_uri.startsWith("github://")) return candidate.canonical_uri;
    const url = new URL(candidate.canonical_uri);
    return `${url.host}${url.pathname}`.replace(/\/$/, "");
  } catch {
    return candidate.canonical_uri;
  }
}

function candidatePollerSupport(candidate: ScoutSourceCandidate): string {
  if (typeof candidate.poller_supported === "boolean") {
    return candidate.poller_supported ? "supported" : "not supported";
  }
  if (candidate.source_kind === "github_repo" || candidate.source_kind === "rss_feed") {
    return "supported";
  }
  if (candidate.source_kind === "web_page") return "not supported";
  return "unknown";
}

function candidateEvidenceRows(
  candidate: ScoutSourceCandidate,
  latestReview: ScoutSourceReviewEvent | null,
): Array<[string, string]> {
  const rows: Array<[string, string | null | undefined]> = [
    ["Trust Tier", candidate.trust_tier ? humanizeScoutLabel(candidate.trust_tier) : null],
    ["Confidence", percentScore(candidate.confidence_score)],
    ["Auto Rank", candidate.automation_label ?? humanizeScoutLabel(candidate.automation_tier)],
    ["Suggested Action", candidate.suggested_action ? humanizeScoutLabel(candidate.suggested_action) : null],
    [
      "Auto Approval Dry Run",
      candidate.auto_approval_dry_run
        ? (candidate.auto_approval_dry_run_label ?? "Would be eligible")
        : candidate.auto_approval_dry_run_reason
          ? `No: ${humanizeScoutLabel(candidate.auto_approval_dry_run_reason)}`
          : null,
    ],
    ["Source Kind", humanizeScoutLabel(candidate.source_kind)],
    ["Poller", candidatePollerSupport(candidate)],
    ["Provenance", candidate.discovered_from_uri],
    ["Discovery Event", candidate.discovered_from_event_id],
    ["Packet Link", candidate.discovered_from_packet_id],
    [
      "Review History",
      candidate.review_history?.length
        ? `${candidate.review_history.length} event${candidate.review_history.length === 1 ? "" : "s"}`
        : "none",
    ],
    [
      "Latest Review",
      latestReview
        ? `${humanizeScoutLabel(latestReview.action)} by ${
            latestReview.reviewed_by ?? "manual-review"
          }`
        : null,
    ],
  ];

  return rows.filter((row): row is [string, string] => Boolean(row[1]));
}

function isBatchApprovableCandidate(candidate: ScoutSourceCandidate): boolean {
  return (
    candidate.automation_tier === "low_risk_recommended" &&
    !["approved", "rejected", "blocked"].includes(candidate.status)
  );
}

function ScoutSourceReviewTimeline({
  events,
}: {
  events: ScoutSourceReviewEvent[] | null | undefined;
}) {
  const visibleEvents = (events ?? []).slice(0, 3);
  if (visibleEvents.length === 0) return null;

  return (
    <div className="dashboard-demo-v4-scout-review-timeline" aria-label="Source review history">
      <span>Review History</span>
      <ol>
        {visibleEvents.map((event) => {
          const created = formatDateTime(event.created_at);
          return (
            <li key={event.review_event_id}>
              <strong>{humanizeScoutLabel(event.action)}</strong>
              <p>
                {event.reviewed_by ?? "manual-review"}
                {created ? ` - ${created}` : ""}
              </p>
              <p>
                {(event.previous_status ? humanizeScoutLabel(event.previous_status) : "new")}
                {" -> "}
                {humanizeScoutLabel(event.new_status)}
              </p>
              {event.reason ? <p>{event.reason}</p> : null}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function isScoutSourceActionResult(value: unknown): value is ScoutSourceActionResult {
  return (
    value !== null &&
    typeof value === "object" &&
    "ok" in value &&
    (value as { ok?: unknown }).ok === true &&
    "action" in value &&
    "message" in value
  );
}

function ScoutSourceCandidateCards({
  candidates,
  emptyLabel,
  busyCandidateId,
  selectedCandidateIds,
  onApprove,
  onReject,
  onBlock,
  onToggleBatchCandidate,
}: {
  candidates: ScoutSourceCandidate[];
  emptyLabel: string;
  busyCandidateId: string | null;
  selectedCandidateIds: Set<string>;
  onApprove: (candidate: ScoutSourceCandidate) => void;
  onReject: (candidate: ScoutSourceCandidate) => void;
  onBlock: (candidate: ScoutSourceCandidate) => void;
  onToggleBatchCandidate: (candidate: ScoutSourceCandidate) => void;
}) {
  if (candidates.length === 0) {
    return <p className="dashboard-demo-v4-scout-empty">{emptyLabel}</p>;
  }

  return (
    <ul className="dashboard-demo-v4-scout-packet-list dashboard-demo-v4-scout-source-list">
      {candidates.map((candidate) => {
        const title = sourceCandidateTitle(candidate);
        const busy = busyCandidateId === candidate.candidate_id;
        const reasonCodes = (candidate.reason_codes ?? []).slice(0, 4);
        const latestReview = candidate.review_history?.[0] ?? null;
        const evidenceRows = candidateEvidenceRows(candidate, latestReview);
        const canBatchApprove = isBatchApprovableCandidate(candidate);
        const selectedForBatch = selectedCandidateIds.has(candidate.candidate_id);
        const canReview =
          candidate.status !== "approved" &&
          candidate.status !== "rejected" &&
          candidate.status !== "blocked";

        return (
          <li key={candidate.candidate_id}>
            <div className="dashboard-demo-v4-scout-packet-topline">
              <div className="dashboard-demo-v4-scout-packet-heading">
                <span>{candidate.source_kind.replaceAll("_", " ")}</span>
                <strong>{title}</strong>
              </div>
              <em className="dashboard-demo-v4-scout-status-chip">
                {candidate.status.replaceAll("_", " ")} {"\u00b7"}{" "}
                {percentScore(candidate.confidence_score)}
              </em>
            </div>
            {candidate.trust_label ? (
              <div className="dashboard-demo-v4-scout-trust-row">
                <span className="dashboard-demo-v4-scout-trust-chip">
                  {candidate.trust_label}
                </span>
                {canBatchApprove ? (
                  <label className="dashboard-demo-v4-scout-source-meta">
                    <input
                      type="checkbox"
                      checked={selectedForBatch}
                      onChange={() => onToggleBatchCandidate(candidate)}
                    />{" "}
                    Select for batch approval
                  </label>
                ) : null}
              </div>
            ) : null}
            {evidenceRows.length > 0 ? (
              <dl className="dashboard-demo-v4-scout-evidence-grid" aria-label={`${title} source evidence`}>
                {evidenceRows.map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            ) : null}
            <p className="dashboard-demo-v4-scout-packet-summary">
              {candidate.recommendation ?? "Review before activation."}
            </p>
            {candidate.discovered_from_uri ? (
              <p className="dashboard-demo-v4-scout-source-meta">
                From {candidate.discovered_from_uri}
              </p>
            ) : null}
            {candidate.rejection_reason ? (
              <p className="dashboard-demo-v4-scout-source-meta">
                Rejected: {candidate.rejection_reason}
              </p>
            ) : null}
            {candidate.blocked_reason ? (
              <p className="dashboard-demo-v4-scout-source-meta">
                Blocked: {candidate.blocked_reason}
              </p>
            ) : null}
            <ScoutSourceReviewTimeline events={candidate.review_history} />
            {reasonCodes.length > 0 ? (
              <div className="dashboard-demo-v4-scout-tags">
                {reasonCodes.map((reason) => (
                  <span key={reason}>{reason.replaceAll("_", " ")}</span>
                ))}
              </div>
            ) : null}
            {canReview ? (
              <div className="dashboard-demo-v4-scout-actions">
                <button type="button" onClick={() => onApprove(candidate)} disabled={busy}>
                  <Check className="h-3.5 w-3.5" aria-hidden />
                  Approve Source
                </button>
                <button type="button" onClick={() => onReject(candidate)} disabled={busy}>
                  <X className="h-3.5 w-3.5" aria-hidden />
                  Reject Source
                </button>
                <button type="button" onClick={() => onBlock(candidate)} disabled={busy}>
                  <Ban className="h-3.5 w-3.5" aria-hidden />
                  Block Source
                </button>
              </div>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

function ScoutSourceCandidateCounts({
  counts,
}: {
  counts: ScoutSourceCandidates["counts"];
}) {
  const items = [
    ["Recommended", counts?.recommended],
    ["Needs Review", counts?.needs_review],
    ["Stored", counts?.stored],
    ["Rejected", counts?.rejected],
    ["Blocked", counts?.blocked],
    ["Approved", counts?.approved],
  ] as const;

  return (
    <div className="dashboard-demo-v4-scout-counts" aria-label="Scout source candidate counts">
      {items.map(([label, value]) => (
        <div key={label} className="dashboard-demo-v4-scout-count">
          <strong>{countValue(value)}</strong>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

function ScoutSourceReviewBundles({
  bundles,
}: {
  bundles: ScoutSourceCandidates["review_bundles"];
}) {
  const visibleBundles = bundles ?? [];
  if (visibleBundles.length === 0) return null;

  return (
    <div className="dashboard-demo-v4-scout-counts" aria-label="Scout source review bundles">
      {visibleBundles.map((bundle) => (
        <div key={bundle.key} className="dashboard-demo-v4-scout-count">
          <strong>{countValue(bundle.count)}</strong>
          <span>{bundle.label}</span>
        </div>
      ))}
    </div>
  );
}

function ScoutBatchApprovalPanel({
  selectedCandidates,
  sourceCount,
  busy,
  onApproveSelected,
}: {
  selectedCandidates: ScoutSourceCandidate[];
  sourceCount: number;
  busy: boolean;
  onApproveSelected: () => void;
}) {
  if (selectedCandidates.length === 0) {
    return (
      <p className="dashboard-demo-v4-scout-source-meta">
        Select low-risk recommended sources to enable manual batch approval.
      </p>
    );
  }

  return (
    <div className="dashboard-demo-v4-scout-summary" aria-label="Scout batch approval preview">
      <p>
        Selected {selectedCandidates.length} low-risk source
        {selectedCandidates.length === 1 ? "" : "s"} for manual approval.
      </p>
      <p className="dashboard-demo-v4-empty-copy">
        Source count estimate: {sourceCount} {"->"} {sourceCount + selectedCandidates.length}
      </p>
      <ul className="dashboard-demo-v4-scout-tags">
        {selectedCandidates.map((candidate) => (
          <li key={candidate.candidate_id}>
            {candidate.canonical_uri} {"\u00b7"} Poller {candidatePollerSupport(candidate)}
          </li>
        ))}
      </ul>
      <div className="dashboard-demo-v4-scout-actions">
        <button type="button" onClick={onApproveSelected} disabled={busy}>
          <Check className="h-3.5 w-3.5" aria-hidden />
          Approve Selected Sources
        </button>
      </div>
    </div>
  );
}

function ScoutDiscoveryJobCounts({ jobs }: { jobs: ScoutDiscoveryJobs }) {
  const budget = jobs.budget ?? {};
  const items = [
    ["Daily Limit", budget.daily_limit],
    ["Used Today", budget.used_today],
    ["Remaining", budget.remaining_today],
    ["Manual Step", budget.queued_jobs ?? jobs.jobs?.filter((job) => job.status === "queued").length],
    ["Running", budget.running_jobs ?? jobs.jobs?.filter((job) => job.status === "running").length],
    ["Finished", budget.completed_jobs ?? jobs.jobs?.filter((job) => job.status === "completed").length],
  ] as const;

  return (
    <>
      <div className="dashboard-demo-v4-scout-counts" aria-label="Scout discovery budget">
        {items.map(([label, value]) => (
          <div key={label} className="dashboard-demo-v4-scout-count">
            <strong>{countValue(value)}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <p className="dashboard-demo-v4-scout-source-meta">
        {budget.can_create_job === false
          ? `Discovery budget blocked: ${humanizeScoutLabel(budget.blocked_reason)}. Reset: ${
              budget.next_reset_hint ?? "next UTC day"
            }.`
          : "Discovery budget can create a bounded manual search plan."}
      </p>
      <p className="dashboard-demo-v4-scout-source-meta">
        Preview Search does not activate sources. Extract Candidates creates source suggestions; it
        does not approve sources.
      </p>
    </>
  );
}

function ScoutDiscoveryJobs({
  jobs,
  emptyLabel,
  busyJobId,
  onPause,
  onResume,
  onPreview,
  onExtract,
}: {
  jobs: ScoutDiscoveryJob[];
  emptyLabel: string;
  busyJobId: string | null;
  onPause: (job: ScoutDiscoveryJob) => void;
  onResume: (job: ScoutDiscoveryJob) => void;
  onPreview: (job: ScoutDiscoveryJob) => void;
  onExtract: (job: ScoutDiscoveryJob) => void;
}) {
  if (jobs.length === 0) {
    return <p className="dashboard-demo-v4-scout-empty">{emptyLabel}</p>;
  }

  return (
    <ul className="dashboard-demo-v4-scout-packet-list dashboard-demo-v4-scout-source-list">
      {jobs.map((job) => {
        const busy = busyJobId === job.job_id;
        const created = formatDateTime(job.created_at);
        const canRun = job.status === "queued";
        const canPause = job.status === "queued" || job.status === "running";
        const canResume = job.status === "paused";
        const statusLabel = humanizeScoutLabel(job.computed_status ?? job.status);
        return (
          <li key={job.job_id}>
            <div className="dashboard-demo-v4-scout-packet-topline">
              <div className="dashboard-demo-v4-scout-packet-heading">
                <span>{job.topic_anchor ?? "Discovery job"}</span>
                <strong>{job.query}</strong>
              </div>
              <em className="dashboard-demo-v4-scout-status-chip">
                {statusLabel} {"\u00b7"} {job.max_results}/{job.budget}
              </em>
            </div>
            <p className="dashboard-demo-v4-scout-packet-summary">
              {created ? `Created ${created}` : "Manual search plan saved for controlled search."}
            </p>
            {job.attention_label ? (
              <p className="dashboard-demo-v4-scout-source-meta">{job.attention_label}</p>
            ) : null}
            {job.safe_next_action ? (
              <p className="dashboard-demo-v4-scout-source-meta">
                Next: {humanizeScoutLabel(job.safe_next_action)}
              </p>
            ) : null}
            {job.error ? (
              <p className="dashboard-demo-v4-scout-source-meta">{job.error}</p>
            ) : null}
            <div className="dashboard-demo-v4-scout-actions">
              {canPause ? (
                <button type="button" onClick={() => onPause(job)} disabled={busy}>
                  <Pause className="h-3.5 w-3.5" aria-hidden />
                  Pause
                </button>
              ) : null}
              {canResume ? (
                <button type="button" onClick={() => onResume(job)} disabled={busy}>
                  <Play className="h-3.5 w-3.5" aria-hidden />
                  Resume
                </button>
              ) : null}
              <button type="button" onClick={() => onPreview(job)} disabled={!canRun || busy}>
                <Search className="h-3.5 w-3.5" aria-hidden />
                Preview Search
              </button>
              <button type="button" onClick={() => onExtract(job)} disabled={!canRun || busy}>
                <Plus className="h-3.5 w-3.5" aria-hidden />
                Extract Candidates
              </button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function ScoutDiscoveryPanel({
  jobs,
  query,
  topicAnchor,
  busyJobId,
  onQueryChange,
  onTopicAnchorChange,
  onCreate,
  onPause,
  onResume,
  onPreview,
  onExtract,
}: {
  jobs: ScoutDiscoveryJobs;
  query: string;
  topicAnchor: string;
  busyJobId: string | null;
  onQueryChange: (value: string) => void;
  onTopicAnchorChange: (value: string) => void;
  onCreate: () => void;
  onPause: (job: ScoutDiscoveryJob) => void;
  onResume: (job: ScoutDiscoveryJob) => void;
  onPreview: (job: ScoutDiscoveryJob) => void;
  onExtract: (job: ScoutDiscoveryJob) => void;
}) {
  const execution = jobs.execution;
  return (
    <>
      <ScoutDiscoveryJobCounts jobs={jobs} />
      {execution?.explanation ? (
        <p className="dashboard-demo-v4-scout-source-meta">{execution.explanation}</p>
      ) : null}
      <div className="dashboard-demo-v4-scout-actions">
        <input
          aria-label="Discovery query"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="official FastAPI release notes"
        />
        <input
          aria-label="Topic anchor"
          value={topicAnchor}
          onChange={(event) => onTopicAnchorChange(event.target.value)}
          placeholder="FastAPI"
        />
        <button type="button" onClick={onCreate} disabled={!query.trim()}>
          <Plus className="h-3.5 w-3.5" aria-hidden />
          Create
        </button>
      </div>
      <ScoutDiscoveryJobs
        jobs={jobs.jobs ?? []}
        emptyLabel="No discovery jobs yet."
        busyJobId={busyJobId}
        onPause={onPause}
        onResume={onResume}
        onPreview={onPreview}
        onExtract={onExtract}
      />
    </>
  );
}

function ScoutFeed({
  overview,
  selectedTab,
  onSelectedTabChange,
  busyPacketId,
  busyPromotionId,
  busySourceCandidateId,
  busyBatchApproval,
  selectedSourceCandidateIds,
  onQueue,
  onRecheck,
  onApprove,
  onReject,
  onApproveSourceCandidate,
  onRejectSourceCandidate,
  onBlockSourceCandidate,
  onToggleBatchSourceCandidate,
  onBatchApproveSourceCandidates,
  discoveryQuery,
  discoveryTopicAnchor,
  busyDiscoveryJobId,
  onDiscoveryQueryChange,
  onDiscoveryTopicAnchorChange,
  onCreateDiscoveryJob,
  onPauseDiscoveryJob,
  onResumeDiscoveryJob,
  onPreviewDiscoveryJob,
  onExtractDiscoveryJob,
}: {
  overview: ScoutOverview;
  selectedTab: ScoutFeedTab;
  onSelectedTabChange: (tab: ScoutFeedTab) => void;
  busyPacketId: string | null;
  busyPromotionId: string | null;
  busySourceCandidateId: string | null;
  busyBatchApproval: boolean;
  selectedSourceCandidateIds?: Set<string>;
  onQueue: (packet: ScoutPacket) => void;
  onRecheck: (packet: ScoutPacket) => void;
  onApprove: (promotion: ScoutPromotionItem) => void;
  onReject: (promotion: ScoutPromotionItem) => void;
  onApproveSourceCandidate: (candidate: ScoutSourceCandidate) => void;
  onRejectSourceCandidate: (candidate: ScoutSourceCandidate) => void;
  onBlockSourceCandidate: (candidate: ScoutSourceCandidate) => void;
  onToggleBatchSourceCandidate: (candidate: ScoutSourceCandidate) => void;
  onBatchApproveSourceCandidates: () => void;
  discoveryQuery: string;
  discoveryTopicAnchor: string;
  busyDiscoveryJobId: string | null;
  onDiscoveryQueryChange: (value: string) => void;
  onDiscoveryTopicAnchorChange: (value: string) => void;
  onCreateDiscoveryJob: () => void;
  onPauseDiscoveryJob: (job: ScoutDiscoveryJob) => void;
  onResumeDiscoveryJob: (job: ScoutDiscoveryJob) => void;
  onPreviewDiscoveryJob: (job: ScoutDiscoveryJob) => void;
  onExtractDiscoveryJob: (job: ScoutDiscoveryJob) => void;
}) {
  const recent = overview.recent ?? {};
  const sources = overview.sources ?? [];
  const promotions = overview.promotions ?? {};
  const sourceCandidates = overview.source_candidates?.candidates ?? [];
  const selectedCandidateIds = selectedSourceCandidateIds ?? new Set<string>();
  const selectedBatchCandidates = sourceCandidates.filter((candidate) =>
    selectedCandidateIds.has(candidate.candidate_id),
  );
  const packetsByTab: Record<"useful" | "saved", ScoutPacket[]> = {
    useful: recent.surfaced ?? [],
    saved: recent.stored ?? [],
  };
  const emptyLabels: Record<ScoutFeedTab, string> = {
    useful: "Scout is running, but no useful-now intelligence yet.",
    saved: "No saved packets yet.",
    review: "No packets waiting for review.",
    promoted: "No promoted packets yet.",
    sourceQueue: "No source candidates waiting for review.",
    discovery: "No discovery jobs yet.",
    sources: "No source data available yet.",
    diagnostics: "Use the Manual Checks runner to run Scout smoke, source gate, search diagnostics, search smoke, and soak snapshot checks.",
  };

  return (
    <div className="dashboard-demo-v4-scout-feed">
      <div className="dashboard-demo-v4-scout-tabs" role="tablist" aria-label="Scout feed filters">
        {scoutFeedTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={selectedTab === tab.id}
            onClick={() => onSelectedTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="dashboard-demo-v4-scout-feed-scroll">
        {selectedTab === "sources" ? (
          <ScoutSourceCards sources={sources} />
        ) : selectedTab === "diagnostics" ? (
          <p className="dashboard-demo-v4-scout-empty">{emptyLabels.diagnostics}</p>
        ) : selectedTab === "discovery" ? (
          <ScoutDiscoveryPanel
            jobs={overview.discovery_jobs ?? {}}
            query={discoveryQuery}
            topicAnchor={discoveryTopicAnchor}
            busyJobId={busyDiscoveryJobId}
            onQueryChange={onDiscoveryQueryChange}
            onTopicAnchorChange={onDiscoveryTopicAnchorChange}
            onCreate={onCreateDiscoveryJob}
            onPause={onPauseDiscoveryJob}
            onResume={onResumeDiscoveryJob}
            onPreview={onPreviewDiscoveryJob}
            onExtract={onExtractDiscoveryJob}
          />
        ) : selectedTab === "sourceQueue" ? (
          <>
            <ScoutSourceCandidateCounts counts={overview.source_candidates?.counts} />
            <ScoutSourceReviewBundles bundles={overview.source_candidates?.review_bundles} />
            <ScoutBatchApprovalPanel
              selectedCandidates={selectedBatchCandidates}
              sourceCount={sources.length}
              busy={busyBatchApproval}
              onApproveSelected={onBatchApproveSourceCandidates}
            />
            <ScoutSourceCandidateCards
              candidates={sourceCandidates}
              emptyLabel={emptyLabels.sourceQueue}
              busyCandidateId={busySourceCandidateId}
              selectedCandidateIds={selectedCandidateIds}
              onApprove={onApproveSourceCandidate}
              onReject={onRejectSourceCandidate}
              onBlock={onBlockSourceCandidate}
              onToggleBatchCandidate={onToggleBatchSourceCandidate}
            />
          </>
        ) : selectedTab === "review" ? (
          <ScoutPromotionCards
            promotions={promotions.queued ?? []}
            emptyLabel={emptyLabels.review}
            busyPromotionId={busyPromotionId}
            onApprove={onApprove}
            onReject={onReject}
          />
        ) : selectedTab === "promoted" ? (
          <ScoutPromotionCards
            promotions={promotions.approved ?? []}
            emptyLabel={emptyLabels.promoted}
            busyPromotionId={busyPromotionId}
            onApprove={onApprove}
            onReject={onReject}
          />
        ) : (
          <ScoutPackets
            packets={packetsByTab[selectedTab]}
            sources={sources}
            emptyLabel={emptyLabels[selectedTab]}
            busyPacketId={busyPacketId}
            onQueue={onQueue}
            onRecheck={onRecheck}
          />
        )}
      </div>
    </div>
  );
}

export function ScoutIntelligenceCenterPanel() {
  const { data, state, refresh } = useScoutOverview();
  const [selectedTab, setSelectedTab] = useState<ScoutFeedTab>("useful");
  const [busyPacketId, setBusyPacketId] = useState<string | null>(null);
  const [busyPromotionId, setBusyPromotionId] = useState<string | null>(null);
  const [busySourceCandidateId, setBusySourceCandidateId] = useState<string | null>(null);
  const [busyBatchApproval, setBusyBatchApproval] = useState(false);
  const [selectedSourceCandidateIds, setSelectedSourceCandidateIds] = useState<Set<string>>(
    () => new Set(),
  );
  const [busyDiscoveryJobId, setBusyDiscoveryJobId] = useState<string | null>(null);
  const [discoveryQuery, setDiscoveryQuery] = useState("official FastAPI release notes");
  const [discoveryTopicAnchor, setDiscoveryTopicAnchor] = useState("FastAPI");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const badge = badgeForState(state);

  async function runPacketAction(
    packet: ScoutPacket,
    action: "queue-promotion" | "recheck",
    successMessage: string,
    errorMessage: string,
  ) {
    const id = packetId(packet);
    if (!id) return;
    const confirmed =
      typeof window === "undefined" ||
      window.confirm(
        action === "queue-promotion"
          ? "Queue this Scout packet for manual promotion review? This does not approve a source."
          : "Recheck this Scout packet with the current debugger logic? This does not change active sources.",
      );
    if (!confirmed) return;
    setBusyPacketId(id);
    setActionError(null);
    try {
      const beforeSnapshot = action === "recheck" ? await readScoutSafetySnapshot(data ?? {}) : null;
      const res = await fetch(`/api/scout/packets/${encodeURIComponent(id)}/${action}`, {
        method: "POST",
        headers: action === "queue-promotion" ? { "Content-Type": "application/json" } : undefined,
        body:
          action === "queue-promotion"
            ? JSON.stringify({
                requested_by: "manual-review",
                reason: "Queued from Scout dashboard.",
              })
            : undefined,
      });
      if (!res.ok) throw new Error(errorMessage);
      const body = await res.json().catch(() => null);
      if (action === "recheck") {
        const afterSnapshot = await readScoutSafetySnapshot(data ?? {});
        setActionMessage(
          `Packet rechecked. Status ${recheckStatus(body, "previous")} -> ${recheckStatus(body, "new")}. ` +
            `Findings ${recheckFindingCount(body)}. ` +
            `Candidate delta ${deltaText(beforeSnapshot?.candidateCount ?? null, afterSnapshot.candidateCount)}. ` +
            `Source delta ${deltaText(beforeSnapshot?.sourceCount ?? null, afterSnapshot.sourceCount)}. ` +
            `Approved delta ${deltaText(beforeSnapshot?.approvedCount ?? null, afterSnapshot.approvedCount)}.`,
        );
      } else {
        setActionMessage(successMessage);
      }
      await refresh();
    } catch {
      setActionError(errorMessage);
    } finally {
      setBusyPacketId(null);
    }
  }

  async function finalizePromotion(promotion: ScoutPromotionItem, action: "approve" | "reject") {
    const reason =
      action === "reject"
        ? window.prompt("Reason for rejecting this Scout promotion?", "Not relevant enough for memory.")
        : null;
    if (action === "reject" && reason === null) return;
    const confirmed =
      action === "approve" || window.confirm("Reject this queued Scout packet promotion?");
    if (!confirmed) return;
    setBusyPromotionId(promotion.promotion_id);
    setActionError(null);
    try {
      const res = await fetch("/api/scout/promotions/finalize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          promotion_id: promotion.promotion_id,
          action,
          approved_by: "manual-review",
          rejected_reason: reason || "Rejected during manual Scout review.",
        }),
      });
      if (!res.ok) throw new Error("Could not finalize promotion.");
      setActionMessage(action === "approve" ? "Promotion approved." : "Promotion rejected.");
      await refresh();
    } catch {
      setActionError("Could not finalize promotion.");
    } finally {
      setBusyPromotionId(null);
    }
  }

  async function reviewSourceCandidate(
    candidate: ScoutSourceCandidate,
    action: "approve" | "reject" | "block",
  ) {
    const reason =
      action === "approve"
        ? null
        : window.prompt(
            action === "block"
              ? "Reason for blocking this source?"
              : "Reason for rejecting this source?",
            action === "block" ? "Unsafe or noisy source." : "Not relevant enough.",
          );
    if (action !== "approve" && reason === null) return;
    const confirmed =
      action === "approve"
        ? window.confirm("Approve this source for Scout polling? This activates the source.")
        : window.confirm(`${action === "block" ? "Block" : "Reject"} this source candidate?`);
    if (!confirmed) return;

    setBusySourceCandidateId(candidate.candidate_id);
    setActionError(null);
    try {
      const body =
        action === "approve"
          ? { approved_by: "manual-review" }
          : { reason: reason || undefined, reviewed_by: "manual-review" };
      const res = await fetch(
        `/api/scout/source-candidates/${encodeURIComponent(candidate.candidate_id)}/${action}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );
      if (!res.ok) throw new Error("Could not review source candidate.");
      const result = (await res.json().catch(() => null)) as unknown;
      if (isScoutSourceActionResult(result)) {
        const warnings = result.warnings.length > 0 ? ` ${result.warnings.join(" ")}` : "";
        setActionMessage(`${result.message}${warnings}`);
      } else {
        setActionMessage(
          action === "approve"
            ? "Source candidate approved."
            : action === "block"
              ? "Source candidate blocked."
              : "Source candidate rejected.",
        );
      }
      await refresh();
    } catch {
      setActionError("Could not review source candidate.");
    } finally {
      setBusySourceCandidateId(null);
    }
  }

  function toggleBatchSourceCandidate(candidate: ScoutSourceCandidate) {
    if (!isBatchApprovableCandidate(candidate)) return;
    setSelectedSourceCandidateIds((current) => {
      const next = new Set(current);
      if (next.has(candidate.candidate_id)) {
        next.delete(candidate.candidate_id);
      } else {
        next.add(candidate.candidate_id);
      }
      return next;
    });
  }

  async function batchApproveSourceCandidates() {
    const sourceCandidates = data?.source_candidates?.candidates ?? [];
    const selected = sourceCandidates.filter((candidate) =>
      selectedSourceCandidateIds.has(candidate.candidate_id),
    );
    if (selected.length === 0) return;
    const unsafe = selected.filter((candidate) => !isBatchApprovableCandidate(candidate));
    if (unsafe.length > 0) {
      setActionError("Only low-risk recommended source candidates can be batch approved.");
      return;
    }
    const uriList = selected.map((candidate) => candidate.canonical_uri).join("\n");
    const confirmed =
      typeof window === "undefined" ||
      window.confirm(
        `Approve these ${selected.length} exact Scout sources?\n\n${uriList}\n\nThis activates only the selected sources and writes review history for each candidate.`,
      );
    if (!confirmed) return;

    setBusyBatchApproval(true);
    setActionError(null);
    try {
      const res = await fetch("/api/scout/source-candidates/batch-approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_ids: selected.map((candidate) => candidate.candidate_id),
          approved_by: "manual-review",
        }),
      });
      if (!res.ok) throw new Error("Could not batch approve source candidates.");
      const result = (await res.json().catch(() => null)) as { approved_count?: number; message?: string; warnings?: string[] } | null;
      const warnings = result?.warnings?.length ? ` ${result.warnings.join(" ")}` : "";
      setActionMessage(result?.message ? `${result.message}${warnings}` : "Selected source candidates approved.");
      setSelectedSourceCandidateIds(new Set());
      await refresh();
    } catch {
      setActionError("Could not batch approve source candidates.");
    } finally {
      setBusyBatchApproval(false);
    }
  }

  async function createDiscoveryJob() {
    const query = discoveryQuery.trim();
    if (!query) return;
    setActionError(null);
    try {
      const res = await fetch("/api/scout/discovery-jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          topic_anchor: discoveryTopicAnchor.trim() || null,
          max_results: 5,
          budget: 5,
        }),
      });
      if (!res.ok) throw new Error("Could not create discovery job.");
      setActionMessage("Discovery job created.");
      await refresh();
    } catch {
      setActionError("Could not create discovery job.");
    }
  }

  async function runDiscoveryJobAction(
    job: ScoutDiscoveryJob,
    action: "pause" | "resume" | "search-preview" | "extract-candidates",
  ) {
    const confirmed =
      action === "search-preview"
        ? true
        : action === "extract-candidates"
          ? window.confirm("Extract source candidates from this discovery job?")
          : true;
    if (!confirmed) return;

    setBusyDiscoveryJobId(job.job_id);
    setActionError(null);
    try {
      const beforeSnapshot =
        action === "search-preview" || action === "extract-candidates"
          ? await readScoutSafetySnapshot(data ?? {})
          : null;
      const res = await fetch(
        `/api/scout/discovery-jobs/${encodeURIComponent(job.job_id)}/${action}`,
        { method: "POST" },
      );
      if (!res.ok) throw new Error("Could not update discovery job.");
      const body = await res.json().catch(() => null);
      if (action === "search-preview") {
        const count = discoveryResultCount(body);
        const afterSnapshot = await readScoutSafetySnapshot(data ?? {});
        setActionMessage(
          `Discovery preview returned ${count} source${count === 1 ? "" : "s"}. ` +
            `Candidate delta ${deltaText(beforeSnapshot?.candidateCount ?? null, afterSnapshot.candidateCount)}. ` +
            `Source delta ${deltaText(beforeSnapshot?.sourceCount ?? null, afterSnapshot.sourceCount)}. ` +
            `Approved delta ${deltaText(beforeSnapshot?.approvedCount ?? null, afterSnapshot.approvedCount)}.`,
        );
      } else if (action === "extract-candidates") {
        const created = extractionCreatedCount(body);
        const afterSnapshot = await readScoutSafetySnapshot(data ?? {});
        setActionMessage(
          `Discovery extraction created ${created} candidate${created === 1 ? "" : "s"}. ` +
            `Candidate delta ${deltaText(beforeSnapshot?.candidateCount ?? null, afterSnapshot.candidateCount)}. ` +
            `Source delta ${deltaText(beforeSnapshot?.sourceCount ?? null, afterSnapshot.sourceCount)}. ` +
            `Approved delta ${deltaText(beforeSnapshot?.approvedCount ?? null, afterSnapshot.approvedCount)}.`,
        );
      } else {
        setActionMessage(action === "pause" ? "Discovery job paused." : "Discovery job resumed.");
      }
      await refresh();
    } catch {
      setActionError("Could not update discovery job.");
    } finally {
      setBusyDiscoveryJobId(null);
    }
  }

  return (
    <section
      aria-label="Scout intelligence"
      className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-card dashboard-demo-v4-scout-card"
    >
      <div className="dashboard-demo-v4-card-header">
        <div className="dashboard-demo-v4-card-title-row">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <BrainCircuit className="h-5 w-5" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Scout learning</p>
            <h2>Intelligence feed</h2>
            <p className="dashboard-demo-v4-card-subtitle">
              {state === "loading"
                ? "Loading Scout overview"
                : state === "error"
                  ? "Scout overview unavailable."
                  : "Read-only Scout status, sources, and packets"}
            </p>
          </div>
        </div>
        <HomelabStatusBadge variant={badge.variant}>{badge.label}</HomelabStatusBadge>
      </div>

      {state === "loading" ? (
        <div className="dashboard-demo-v4-skeleton-list" aria-label="Loading Scout overview">
          <div />
          <div />
        </div>
      ) : null}

      {state === "error" ? (
        <p className="dashboard-demo-v4-empty-copy">Scout overview unavailable.</p>
      ) : null}

      {state === "loaded" && data ? (
        <div className="dashboard-demo-v4-scout-body">
          <ScoutNotes overview={data} />
          <ScoutCounts overview={data} />
          {actionMessage ? (
            <p className="dashboard-demo-v4-scout-action-message">{actionMessage}</p>
          ) : null}
          {actionError ? (
            <p className="dashboard-demo-v4-scout-action-error">{actionError}</p>
          ) : null}
          <ScoutFeed
            overview={data}
            selectedTab={selectedTab}
            onSelectedTabChange={setSelectedTab}
            busyPacketId={busyPacketId}
            busyPromotionId={busyPromotionId}
            busySourceCandidateId={busySourceCandidateId}
            busyBatchApproval={busyBatchApproval}
            selectedSourceCandidateIds={selectedSourceCandidateIds}
            onQueue={(packet) =>
              void runPacketAction(
                packet,
                "queue-promotion",
                "Packet queued for promotion review.",
                "Could not queue packet.",
              )
            }
            onRecheck={(packet) =>
              void runPacketAction(
                packet,
                "recheck",
                "Packet rechecked.",
                "Could not recheck packet.",
              )
            }
            onApprove={(promotion) => void finalizePromotion(promotion, "approve")}
            onReject={(promotion) => void finalizePromotion(promotion, "reject")}
            onApproveSourceCandidate={(candidate) =>
              void reviewSourceCandidate(candidate, "approve")
            }
            onRejectSourceCandidate={(candidate) => void reviewSourceCandidate(candidate, "reject")}
            onBlockSourceCandidate={(candidate) => void reviewSourceCandidate(candidate, "block")}
            onToggleBatchSourceCandidate={toggleBatchSourceCandidate}
            onBatchApproveSourceCandidates={() => void batchApproveSourceCandidates()}
            discoveryQuery={discoveryQuery}
            discoveryTopicAnchor={discoveryTopicAnchor}
            busyDiscoveryJobId={busyDiscoveryJobId}
            onDiscoveryQueryChange={setDiscoveryQuery}
            onDiscoveryTopicAnchorChange={setDiscoveryTopicAnchor}
            onCreateDiscoveryJob={() => void createDiscoveryJob()}
            onPauseDiscoveryJob={(job) => void runDiscoveryJobAction(job, "pause")}
            onResumeDiscoveryJob={(job) => void runDiscoveryJobAction(job, "resume")}
            onPreviewDiscoveryJob={(job) => void runDiscoveryJobAction(job, "search-preview")}
            onExtractDiscoveryJob={(job) =>
              void runDiscoveryJobAction(job, "extract-candidates")
            }
          />
          <ScoutScheduler overview={data} />
        </div>
      ) : null}
    </section>
  );
}
