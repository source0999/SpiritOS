"use client";

import { useState } from "react";
import { Ban, BrainCircuit, Check, Pause, Play, Plus, RefreshCw, Search, X } from "lucide-react";

import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";
import { useScoutOverview, type ScoutOverviewFetchState } from "@/hooks/useScoutOverview";
import type {
  ScoutOverview,
  ScoutDiscoveryJob,
  ScoutDiscoveryJobs,
  ScoutPacket,
  ScoutPromotionItem,
  ScoutSchedulerJob,
  ScoutSourceCandidate,
  ScoutSourceCandidates,
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
  | "sources";

const scoutFeedTabs: Array<{ id: ScoutFeedTab; label: string }> = [
  { id: "useful", label: "Useful Now" },
  { id: "saved", label: "Saved Later" },
  { id: "review", label: "Review Queue" },
  { id: "promoted", label: "Promoted" },
  { id: "sourceQueue", label: "Source Queue" },
  { id: "discovery", label: "Discovery" },
  { id: "sources", label: "Sources" },
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

function ScoutCounts({ overview }: { overview: ScoutOverview }) {
  const counts = overview.counts ?? {};
  const backlog = overview.backlog ?? {};
  const memory = overview.human_summary?.memory_status;
  const promotion = overview.human_summary?.promotion_status;
  const sources = overview.sources ?? [];
  const sourceCandidateCounts = overview.source_candidates?.counts ?? {};
  const sourceQueueCount =
    (sourceCandidateCounts.recommended ?? 0) + (sourceCandidateCounts.needs_review ?? 0);
  const discoveryJobCount = overview.discovery_jobs?.count ?? overview.discovery_jobs?.jobs?.length ?? 0;
  const scanFlow = overview.human_summary?.scan_flow;
  const stats =
    scanFlow && scanFlow.length > 0
      ? scanFlow.map((item) => [item.label, item.count] as const)
      : ([
          ["Scanned", counts.raw_event_index ?? counts.raw_events],
          ["Cleaned", counts.extracted_artifacts ?? counts.artifacts],
          ["Summarized", counts.packets],
          ["Checked", counts.verdicts],
        ] as const);
  const needsReview = backlog.debugger_pending_without_verdict ?? backlog.debugger_pending_packets;
  const metrics = [
    ...stats,
    ["Review Queue", needsReview] as const,
    [
      "Semantic Memory",
      memory?.active || (counts.packet_embeddings ?? 0) > 0 ? "Active" : "Inactive",
    ] as const,
    ["Promoted", promotion?.promoted_count] as const,
    ["Source Queue", sourceQueueCount] as const,
    ["Discovery Jobs", discoveryJobCount] as const,
    ["Sources", sources.length] as const,
  ];

  return (
    <div className="dashboard-demo-v4-scout-counts" aria-label="Scout counts">
      {metrics.map(([label, value]) => (
        <div key={label} className="dashboard-demo-v4-scout-count">
          <strong>{typeof value === "string" ? value : countValue(value)}</strong>
          <span>{label}</span>
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
        {memory?.label ?? "Semantic memory inactive"} {"\u00b7"} {promotedCount} promoted
      </p>
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
            ? "Queued"
            : promotionStatus === "approved"
              ? "Promoted"
              : promotionStatus === "rejected"
                ? "Queue again"
                : "Queue";
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
                aria-label={`Recheck ${packetTitle(packet)}`}
              >
                <RefreshCw className="h-3.5 w-3.5" aria-hidden />
                {busyPacketId === id ? "Rechecking" : "Recheck"}
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
                  Approve
                </button>
                <button type="button" onClick={() => onReject(promotion)} disabled={busy}>
                  <X className="h-3.5 w-3.5" aria-hidden />
                  Reject
                </button>
              </div>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
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
  onApprove,
  onReject,
  onBlock,
}: {
  candidates: ScoutSourceCandidate[];
  emptyLabel: string;
  busyCandidateId: string | null;
  onApprove: (candidate: ScoutSourceCandidate) => void;
  onReject: (candidate: ScoutSourceCandidate) => void;
  onBlock: (candidate: ScoutSourceCandidate) => void;
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
        const latestReviewTime = formatDateTime(latestReview?.created_at);
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
              </div>
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
            {latestReview ? (
              <p className="dashboard-demo-v4-scout-source-meta">
                {latestReview.action} by {latestReview.reviewed_by ?? "manual-review"}
                {latestReviewTime ? ` at ${latestReviewTime}` : ""}
                {latestReview.reason ? `: ${latestReview.reason}` : ""}
              </p>
            ) : null}
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
                  Approve
                </button>
                <button type="button" onClick={() => onReject(candidate)} disabled={busy}>
                  <X className="h-3.5 w-3.5" aria-hidden />
                  Reject
                </button>
                <button type="button" onClick={() => onBlock(candidate)} disabled={busy}>
                  <Ban className="h-3.5 w-3.5" aria-hidden />
                  Block
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

function ScoutDiscoveryJobCounts({ jobs }: { jobs: ScoutDiscoveryJobs }) {
  const items = [
    ["Queued", jobs.jobs?.filter((job) => job.status === "queued").length],
    ["Paused", jobs.jobs?.filter((job) => job.status === "paused").length],
    ["Running", jobs.jobs?.filter((job) => job.status === "running").length],
    ["Finished", jobs.jobs?.filter((job) => job.status === "completed").length],
  ] as const;

  return (
    <div className="dashboard-demo-v4-scout-counts" aria-label="Scout discovery job counts">
      {items.map(([label, value]) => (
        <div key={label} className="dashboard-demo-v4-scout-count">
          <strong>{countValue(value)}</strong>
          <span>{label}</span>
        </div>
      ))}
    </div>
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
        return (
          <li key={job.job_id}>
            <div className="dashboard-demo-v4-scout-packet-topline">
              <div className="dashboard-demo-v4-scout-packet-heading">
                <span>{job.topic_anchor ?? "Discovery job"}</span>
                <strong>{job.query}</strong>
              </div>
              <em className="dashboard-demo-v4-scout-status-chip">
                {job.status} {"\u00b7"} {job.max_results}/{job.budget}
              </em>
            </div>
            <p className="dashboard-demo-v4-scout-packet-summary">
              {created ? `Created ${created}` : "Discovery job queued for controlled search."}
            </p>
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
                Preview
              </button>
              <button type="button" onClick={() => onExtract(job)} disabled={!canRun || busy}>
                <Plus className="h-3.5 w-3.5" aria-hidden />
                Extract
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
  return (
    <>
      <ScoutDiscoveryJobCounts jobs={jobs} />
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
  onQueue,
  onRecheck,
  onApprove,
  onReject,
  onApproveSourceCandidate,
  onRejectSourceCandidate,
  onBlockSourceCandidate,
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
  onQueue: (packet: ScoutPacket) => void;
  onRecheck: (packet: ScoutPacket) => void;
  onApprove: (promotion: ScoutPromotionItem) => void;
  onReject: (promotion: ScoutPromotionItem) => void;
  onApproveSourceCandidate: (candidate: ScoutSourceCandidate) => void;
  onRejectSourceCandidate: (candidate: ScoutSourceCandidate) => void;
  onBlockSourceCandidate: (candidate: ScoutSourceCandidate) => void;
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
            <ScoutSourceCandidateCards
              candidates={sourceCandidates}
              emptyLabel={emptyLabels.sourceQueue}
              busyCandidateId={busySourceCandidateId}
              onApprove={onApproveSourceCandidate}
              onReject={onRejectSourceCandidate}
              onBlock={onBlockSourceCandidate}
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

export function HomelabScoutIntelligenceWidget() {
  const { data, state, refresh } = useScoutOverview();
  const [selectedTab, setSelectedTab] = useState<ScoutFeedTab>("useful");
  const [busyPacketId, setBusyPacketId] = useState<string | null>(null);
  const [busyPromotionId, setBusyPromotionId] = useState<string | null>(null);
  const [busySourceCandidateId, setBusySourceCandidateId] = useState<string | null>(null);
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
          ? "Queue this Scout packet for manual promotion review?"
          : "Recheck this Scout packet with the current debugger logic?",
      );
    if (!confirmed) return;
    setBusyPacketId(id);
    setActionError(null);
    try {
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
      setActionMessage(successMessage);
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
      action === "approve" || window.confirm("Reject this queued Scout promotion?");
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
        ? window.confirm("Approve this source for Scout polling?")
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
      const res = await fetch(
        `/api/scout/discovery-jobs/${encodeURIComponent(job.job_id)}/${action}`,
        { method: "POST" },
      );
      if (!res.ok) throw new Error("Could not update discovery job.");
      const body = await res.json().catch(() => null);
      if (action === "search-preview") {
        const count =
          body &&
          typeof body === "object" &&
          "result" in body &&
          body.result &&
          typeof body.result === "object" &&
          "sources" in body.result &&
          Array.isArray(body.result.sources)
            ? body.result.sources.length
            : 0;
        setActionMessage(`Discovery preview returned ${count} source${count === 1 ? "" : "s"}.`);
      } else if (action === "extract-candidates") {
        const created =
          body &&
          typeof body === "object" &&
          "extraction" in body &&
          body.extraction &&
          typeof body.extraction === "object" &&
          "candidates_created" in body.extraction &&
          typeof body.extraction.candidates_created === "number"
            ? body.extraction.candidates_created
            : 0;
        setActionMessage(
          `Discovery extraction created ${created} candidate${created === 1 ? "" : "s"}.`,
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
