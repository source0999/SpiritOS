"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowUp } from "lucide-react";

import { DashboardDemoV4Atmosphere } from "@/components/dashboard/demo-v4/DashboardDemoV4Atmosphere";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import { HomelabStatusBadge } from "@/components/dashboard/HomelabStatusBadge";
import { useScoutOverview } from "@/hooks/useScoutOverview";
import {
  buildScoutHumanReadModel,
  type ScoutActionInboxCard,
  type ScoutSourceCandidateGroup,
  humanizeScoutLabel,
  sourceDisplayName,
} from "@/lib/scout-human-readable";
import type {
  ScoutDiscoveryJob,
  ScoutDiscoveryBudget,
  ScoutOverview,
  ScoutPacket,
  ScoutPromotionItem,
  ScoutSourceCandidate,
  ScoutSourceSummary,
} from "@/lib/scout-overview";
import { ScoutIntelligenceCenterPanel } from "@/components/dashboard/HomelabScoutIntelligenceWidget";

function countValue(value: number | undefined | null): string {
  return typeof value === "number" ? value.toLocaleString() : "-";
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "Not recorded";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function packetTitle(packet: ScoutPacket): string {
  return packet.title ?? packet.summary ?? packet.packet_id ?? packet.id ?? "Untitled packet";
}

function packetSource(packet: ScoutPacket): string {
  return (
    packet.source_label ??
    packet.provenance?.source_label ??
    sourceDisplayName(packet.source_uri ?? packet.source_url ?? packet.uri ?? packet.provenance?.source_uri)
  );
}

function promotionTitle(promotion: ScoutPromotionItem): string {
  return promotion.packet?.title ?? promotion.summary ?? promotion.packet_id;
}

function promotionSourceLabel(promotion: ScoutPromotionItem): string {
  return promotion.source_label ?? promotion.packet?.source_label ?? "Source unknown";
}

function promotionTrustLabel(promotion: ScoutPromotionItem): string | null {
  return promotion.trust_label ?? promotion.packet?.trust_label ?? promotion.packet?.source_trust_label ?? null;
}

function promotionTags(promotion: ScoutPromotionItem): string[] {
  return (promotion.entity_tags ?? promotion.packet?.entity_tags ?? promotion.packet?.tags ?? [])
    .filter(Boolean)
    .slice(0, 5);
}

function sourceTitle(source: ScoutSourceSummary): string {
  return source.label ?? sourceDisplayName(source.display_uri ?? source.canonical_uri ?? source.source_uri);
}

function sourceUri(source: ScoutSourceSummary): string {
  return source.canonical_uri ?? source.source_uri ?? source.display_uri ?? "Unknown";
}

function sourceKindLabel(source: ScoutSourceSummary): string {
  return humanizeScoutLabel(source.source_kind ?? "source");
}

function sourceActivityText(source: ScoutSourceSummary): string {
  const packetText =
    typeof source.packets_surfaced === "number"
      ? `${countValue(source.packets_surfaced)} useful packets`
      : "Useful packet count not reported";
  return `${packetText} - Last checked ${formatDateTime(source.last_polled_at)}`;
}

function candidateTitle(candidate: ScoutSourceCandidate): string {
  const metadataTitle = typeof candidate.metadata?.title === "string" ? candidate.metadata.title : null;
  return metadataTitle ?? candidate.display_uri ?? candidate.canonical_uri ?? candidate.candidate_id;
}

function confidenceLabel(value: number | null | undefined): string {
  if (typeof value !== "number") return "Score unknown";
  return `${Math.round(value * 100)}% confidence`;
}

function latestReviewLabel(candidate: ScoutSourceCandidate): string | null {
  const latest = candidate.review_history?.[0];
  if (!latest) return null;
  const reviewer = latest.reviewed_by ?? "reviewer unknown";
  return `${humanizeScoutLabel(latest.action)} by ${reviewer} on ${formatDateTime(latest.created_at)}`;
}

function candidateGroupStatusSummary(group: ScoutSourceCandidateGroup): string {
  return Object.entries(group.statuses)
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([status, count]) => `${count} ${humanizeScoutLabel(status)}`)
    .join(", ");
}

function searchPlanLabel(job: ScoutDiscoveryJob): string {
  const haystack = [
    job.computed_status,
    job.attention_label,
    job.safe_next_action,
    job.error,
    typeof job.metadata?.reason === "string" ? job.metadata.reason : null,
    typeof job.metadata?.status_reason === "string" ? job.metadata.status_reason : null,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (haystack.includes("duplicate")) return "Duplicate queued search";
  if (haystack.includes("stale")) return "Stale queued search";
  if (haystack.includes("noisy")) return "Noisy test search";
  if (job.status === "queued") return "Normal queued search";
  return humanizeScoutLabel(job.computed_status ?? job.status);
}

function searchPlanManualOptions(job: ScoutDiscoveryJob, budget: ScoutDiscoveryBudget | undefined): string[] {
  const label = searchPlanLabel(job).toLowerCase();
  const safeAction = job.safe_next_action?.toLowerCase() ?? "";
  const options = ["Leave queued"];

  if (budget?.remaining_today === 0 || budget?.can_create_job === false) {
    options.push("Preview after budget reset");
  } else {
    options.push("Preview Search manually");
  }

  if (
    label.includes("duplicate") ||
    label.includes("stale") ||
    label.includes("noisy") ||
    safeAction.includes("cancel")
  ) {
    options.push("Mark for cleanup patch");
  } else {
    options.push("Extract candidates only after preview");
  }

  return options;
}

function budgetHelpText(budget: ScoutDiscoveryBudget | undefined): string {
  if (!budget) return "Daily search budget remaining.";
  if (budget.blocked_reason) return `${humanizeScoutLabel(budget.blocked_reason)}. Budget resets ${budget.next_reset_hint ?? "next UTC day"}.`;
  return "Daily search budget remaining.";
}

function SourceCandidateGroups({ groups }: { groups: ScoutSourceCandidateGroup[] }) {
  if (groups.length === 0) return null;

  return (
    <ul className="scout-center-list scout-center-source-groups">
      {groups.map((group) => (
        <li key={group.root}>
          <div className="scout-center-source-group-heading">
            <span className="scout-center-source-icon" data-kind={group.iconKind} aria-hidden>
              {group.iconKind === "github"
                ? "GH"
                : group.iconKind === "pydantic"
                  ? "P"
                  : group.iconKind === "python"
                    ? "PY"
                    : group.iconKind === "rss"
                      ? "RSS"
                      : "WEB"}
            </span>
            <div>
              <strong>{group.label}</strong>
              <span>
                {group.total} source suggestion{group.total === 1 ? "" : "s"} -{" "}
                {candidateGroupStatusSummary(group)}
              </span>
            </div>
          </div>
          <p>
            {group.highestTrustLabel ?? "Trust not labeled"} - grouped under {group.root}
          </p>
          <details>
            <summary>Expand source suggestions</summary>
            <ul className="scout-center-candidate-list">
              {group.candidates.map((candidate) => (
                <li key={candidate.candidate_id}>
                  <strong>{candidateTitle(candidate)}</strong>
                  <span>
                    {humanizeScoutLabel(candidate.status)} - {candidate.source_kind} -{" "}
                    {confidenceLabel(candidate.confidence_score)}
                  </span>
                  <p>
                    {candidate.trust_label ?? "Trust not labeled"} -{" "}
                    {candidate.recommendation ?? candidate.explanation ?? "Suggested source needs review."}
                  </p>
                  <dl>
                    <dt>URL</dt>
                    <dd>{candidate.canonical_uri}</dd>
                    <dt>Reason codes</dt>
                    <dd>{candidate.reason_codes?.join(", ") || "None provided"}</dd>
                    <dt>Reviewed by</dt>
                    <dd>{candidate.reviewed_by ?? "Not reviewed"}</dd>
                    <dt>Reviewed at</dt>
                    <dd>{formatDateTime(candidate.reviewed_at)}</dd>
                    <dt>Latest review</dt>
                    <dd>{latestReviewLabel(candidate) ?? "No review history"}</dd>
                    <dt>Poller support</dt>
                    <dd>{candidate.poller_supported === false ? "Needs poller support" : "Supported or unknown"}</dd>
                  </dl>
                </li>
              ))}
            </ul>
          </details>
        </li>
      ))}
    </ul>
  );
}

function Section({
  id,
  title,
  help,
  children,
}: {
  id?: string;
  title: string;
  help: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="scout-center-section" tabIndex={id ? -1 : undefined}>
      <div className="scout-center-section-heading">
        <h2>{title}</h2>
        <p>{help}</p>
      </div>
      {children}
    </section>
  );
}

function scrollToSection(targetId: string) {
  const target = document.getElementById(targetId);
  if (!target) return;

  target.scrollIntoView({ behavior: "smooth", block: "start" });
  target.focus({ preventScroll: true });
  target.classList.add("scout-center-section-active");
  window.setTimeout(() => target.classList.remove("scout-center-section-active"), 1400);
}

function scrollToScoutTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function cardTargetId(card: ScoutActionInboxCard): string {
  if (card.id === "stored-only") return "watching-now";
  return card.id;
}

function ActionInbox({ overview }: { overview: ScoutOverview }) {
  const model = buildScoutHumanReadModel(overview);

  return (
    <section className="scout-center-action-inbox" aria-labelledby="scout-action-inbox-title">
      <div className="scout-center-section-heading">
        <p>Action Inbox</p>
        <h2 id="scout-action-inbox-title">Review Inbox</h2>
        <span>Start with the safest next click. These cards only navigate the page.</span>
      </div>
      <div className="scout-center-action-grid">
        {model.actionInboxCards.map((card) => (
          <button
            key={card.id}
            type="button"
            className="scout-center-action-card"
            onClick={() => scrollToSection(cardTargetId(card))}
          >
            <strong>{typeof card.value === "number" ? countValue(card.value) : card.value}</strong>
            <span>{card.label}</span>
            <p>{card.help}</p>
          </button>
        ))}
      </div>
    </section>
  );
}

function Metric({ label, value, help }: { label: string; value: string; help: string }) {
  return (
    <div className="scout-center-metric">
      <strong>{value}</strong>
      <span>{label}</span>
      <p>{help}</p>
    </div>
  );
}

type BarDatum = {
  label: string;
  value: number;
};

function BarList({ items, ariaLabel }: { items: BarDatum[]; ariaLabel: string }) {
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className="scout-center-bars" aria-label={ariaLabel}>
      {items.map((item) => (
        <div key={item.label} className="scout-center-bar-row">
          <div className="scout-center-bar-label">
            <span>{item.label}</span>
            <strong>{countValue(item.value)}</strong>
          </div>
          <div className="scout-center-bar-track" aria-hidden>
            <span style={{ width: `${Math.max(4, (item.value / max) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function PipelineBars({ overview }: { overview: ScoutOverview }) {
  const model = buildScoutHumanReadModel(overview);
  const counts = model.pipelineCounts;

  return (
    <BarList
      ariaLabel="Scout pipeline counts"
      items={[
        { label: "Raw events", value: counts.rawEvents },
        { label: "Cleaned artifacts", value: counts.extractedArtifacts },
        { label: "Packets", value: counts.packets },
        { label: "Verdicts", value: counts.verdicts },
        { label: "Promoted", value: counts.promotedBriefings },
      ]}
    />
  );
}

function CandidateGroupBars({ overview }: { overview: ScoutOverview }) {
  const groups = buildScoutHumanReadModel(overview).sourceCandidateGroups;
  if (groups.length === 0) return null;

  return (
    <BarList
      ariaLabel="Source candidate groups"
      items={groups.map((group) => ({ label: group.root, value: group.total }))}
    />
  );
}

function SourceStatusBars({ overview }: { overview: ScoutOverview }) {
  const counts = buildScoutHumanReadModel(overview).sourceStatusCounts;
  const items = ["recommended", "needs_review", "approved", "rejected", "blocked"]
    .map((status) => ({ label: humanizeScoutLabel(status), value: counts[status] ?? 0 }))
    .filter((item) => item.value > 0);

  if (items.length === 0) return null;
  return <BarList ariaLabel="Source candidate statuses" items={items} />;
}

function SourceSplitBars({ overview }: { overview: ScoutOverview }) {
  const model = buildScoutHumanReadModel(overview);

  return (
    <BarList
      ariaLabel="Watching source split"
      items={[
        { label: "Watching now", value: model.pollableSourceCount },
        { label: "Stored only", value: model.storedOnlySourceCount },
      ]}
    />
  );
}

function DiscoveryBudgetBars({ overview }: { overview: ScoutOverview }) {
  const budget = buildScoutHumanReadModel(overview).discoveryBudgetSummary;
  const used = budget.usedToday ?? 0;
  const remaining = budget.remainingToday ?? 0;

  return (
    <BarList
      ariaLabel="Discovery budget"
      items={[
        { label: "Used today", value: used },
        { label: "Remaining", value: remaining },
      ]}
    />
  );
}

function Briefing({ overview }: { overview: ScoutOverview }) {
  const model = buildScoutHumanReadModel(overview);

  return (
    <Section
      title="Today's Scout Summary"
      help="Scout watches approved places and brings intelligence back for manual review."
    >
      <div className="scout-center-briefing">
        <p>{model.summarySentence}</p>
        <p>{model.queueSentence}</p>
        <p>
          {model.memoryWritesOff
            ? "Memory writes off means Scout is not changing proxy memory or coding context."
            : "Memory writes are not shown as off. Review Scout safety settings before trusting changes."}
        </p>
      </div>
      <div className="scout-center-metrics">
        <Metric
          label="Review Inbox"
          value={countValue(model.needsReview)}
          help="Source suggestions plus packet reviews waiting for approval."
        />
        <Metric
          label="Promoted Briefings"
          value={countValue(model.usefulFinds)}
          help="Promoted briefings saved for review."
        />
        <Metric
          label="Manual Search Plans"
          value={countValue(model.queuedJobs)}
          help="Saved searches waiting for preview or extraction."
        />
        <Metric
          label="Watching Now"
          value={countValue(model.pollableSourceCount)}
          help={
            model.storedOnlySourceCount > 0
              ? `${countValue(model.storedOnlySourceCount)} stored only`
              : "Sources Scout can watch for updates."
          }
        />
      </div>
      <PipelineBars overview={overview} />
    </Section>
  );
}

function Findings({ overview }: { overview: ScoutOverview }) {
  const promoted = overview.promotions?.approved ?? [];
  const saved = overview.recent?.promoted ?? overview.recent?.stored ?? [];
  const queued = overview.promotions?.queued ?? [];
  const reviewCount = queued.length || overview.human_summary?.promotion_status?.pending_review_count || 0;
  const model = buildScoutHumanReadModel(overview);

  return (
    <Section
      id="promoted-briefings"
      title="Promoted Briefings and Processed Packets"
      help="Scout can process many packets while only a few are promoted into the briefing lane."
    >
      <div className="scout-center-metrics">
        <Metric label="Promoted Briefings" value={countValue(model.promotedBriefingCount)} help="Items promoted into your briefing lane." />
        <Metric label="Processed Packets" value={countValue(model.processedPacketCount)} help="Scout intelligence packets checked by the pipeline." />
        <Metric label="Checked Verdicts" value={countValue(model.pipelineCounts.verdicts)} help="Packets that received a Scout verdict." />
        <Metric label="Review Inbox" value={countValue(reviewCount)} help="Manual packet review." />
      </div>
      <p className="scout-center-helper">
        Scout processed {countValue(model.processedPacketCount)} packets, but only{" "}
        {countValue(model.promotedBriefingCount)} has been promoted into your briefing lane. This is
        normal while promotion is manual.
      </p>
      <PipelineBars overview={overview} />
      <ul className="scout-center-list">
        {promoted.slice(0, 4).map((promotion) => (
          <li key={promotion.promotion_id}>
            <strong>{promotionTitle(promotion)}</strong>
            <span>
              {promotionSourceLabel(promotion)}
              {promotionTrustLabel(promotion) ? ` - ${promotionTrustLabel(promotion)}` : ""}
            </span>
            <p>{promotion.reason ?? promotion.packet?.summary ?? promotion.summary ?? "Saved to briefing."}</p>
            {promotionTags(promotion).length > 0 ? (
              <div className="scout-center-tags">
                {promotionTags(promotion).map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            ) : null}
          </li>
        ))}
        {promoted.length === 0
          ? saved.slice(0, 4).map((packet) => (
              <li key={packet.packet_id ?? packet.id ?? packetTitle(packet)}>
                <strong>{packetTitle(packet)}</strong>
                <span>{packetSource(packet)}</span>
                <p>{packet.summary ?? "Saved packet."}</p>
              </li>
            ))
          : null}
      </ul>
      {promoted.length === 0 && saved.length === 0 ? (
        <p className="scout-center-empty">No promoted briefings are saved yet.</p>
      ) : null}
    </Section>
  );
}

function SourceApprovals({ overview }: { overview: ScoutOverview }) {
  const candidates = overview.source_candidates?.candidates ?? [];
  const groups = buildScoutHumanReadModel(overview).sourceCandidateGroups;

  return (
    <Section
      id="sources-to-approve"
      title="Sources to Approve"
      help="Sources to Approve shows what Scout could watch after human review."
    >
      <p className="scout-center-helper">A source is something Scout can watch for updates.</p>
      <CandidateGroupBars overview={overview} />
      <SourceStatusBars overview={overview} />
      <SourceCandidateGroups groups={groups} />
      <ul className="scout-center-list scout-center-hidden-flat-list" aria-hidden="true">
        {candidates.slice(0, 8).map((candidate: ScoutSourceCandidate) => (
          <li key={candidate.candidate_id}>
            <strong>{sourceDisplayName(candidate.display_uri || candidate.canonical_uri)}</strong>
            <span>
              {candidate.trust_label ?? "Trust not labeled"} -{" "}
              {humanizeScoutLabel(candidate.suggested_action ?? candidate.status)}
            </span>
            <p>{candidate.explanation ?? candidate.recommendation ?? "Suggested source needs review."}</p>
            <details>
              <summary>Details</summary>
              <dl>
                <dt>URL</dt>
                <dd>{candidate.canonical_uri}</dd>
                <dt>Reason codes</dt>
                <dd>{candidate.reason_codes?.join(", ") || "None provided"}</dd>
                <dt>Poller support</dt>
                <dd>{candidate.poller_supported === false ? "Needs poller support" : "Supported or unknown"}</dd>
              </dl>
            </details>
          </li>
        ))}
      </ul>
      {candidates.length === 0 ? (
        <p className="scout-center-empty">No suggested sources need review.</p>
      ) : null}
    </Section>
  );
}

function SearchQueue({ overview }: { overview: ScoutOverview }) {
  const jobs = overview.discovery_jobs?.jobs ?? [];
  const budget = overview.discovery_jobs?.budget;
  const execution = overview.discovery_jobs?.execution;
  const queuedCount = budget?.queued_jobs ?? jobs.filter((job) => job.status === "queued").length;
  const runningCount = budget?.running_jobs ?? jobs.filter((job) => job.status === "running").length;

  return (
    <Section
      id="manual-search-plans"
      title="Manual Search Plans"
      help="These are saved search plans. They do not run automatically yet."
    >
      <div className="scout-center-metrics">
        <Metric label="Waiting for manual step" value={countValue(queuedCount)} help="Saved searches waiting for preview or extraction." />
        <Metric label="Running" value={countValue(runningCount)} help="Search jobs currently active." />
        <Metric label="Budget left" value={countValue(budget?.remaining_today)} help={budgetHelpText(budget)} />
      </div>
      <p className="scout-center-helper">
        {execution?.explanation ??
          "Search jobs are saved controlled plans. Scout does not run them automatically in the background."}
      </p>
      <p className="scout-center-helper">
        Preview Search shows possible results and does not activate sources. Extract Candidates turns
        results into source suggestions and does not approve sources.
      </p>
      <DiscoveryBudgetBars overview={overview} />
      <ul className="scout-center-list">
        {jobs.slice(0, 8).map((job: ScoutDiscoveryJob) => (
          <li key={job.job_id}>
            <strong>{job.query}</strong>
            <span>
              {humanizeScoutLabel(job.status)} -{" "}
              {job.attention_label ?? searchPlanLabel(job)}
            </span>
            <p>
              Topic: {job.topic_anchor ?? "None"} - Updated {formatDateTime(job.updated_at)}
            </p>
            <div className="scout-center-manual-options" aria-label={`Suggested next steps for ${job.query}`}>
              <span>Suggested next steps:</span>
              {searchPlanManualOptions(job, budget).map((option) => (
                <span key={option}>{option}</span>
              ))}
            </div>
            <details>
              <summary>Details</summary>
              <dl>
                <dt>Status</dt>
                <dd>{humanizeScoutLabel(job.status)}</dd>
                <dt>Plan label</dt>
                <dd>{searchPlanLabel(job)}</dd>
                <dt>Computed status</dt>
                <dd>{humanizeScoutLabel(job.computed_status)}</dd>
                <dt>Safe next action</dt>
                <dd>{job.safe_next_action ?? "No action suggested"}</dd>
                <dt>Budget</dt>
                <dd>{job.budget}</dd>
              </dl>
            </details>
          </li>
        ))}
      </ul>
      {jobs.length === 0 ? <p className="scout-center-empty">No search jobs are queued.</p> : null}
    </Section>
  );
}

function WatchedSources({ overview }: { overview: ScoutOverview }) {
  const sources = overview.sources ?? [];
  const model = buildScoutHumanReadModel(overview);
  const watchingNow = sources.filter((source) => source.poller_supported === true);
  const storedOnly = sources.filter((source) => source.poller_supported === false);
  const unknownSupport = sources.filter((source) => typeof source.poller_supported !== "boolean");

  return (
    <Section
      id="watching-now"
      title="Watching Now and Stored Sources"
      help="Watching sources can be checked by Scout; stored sources are approved but not pollable yet."
    >
      <div className="scout-center-metrics">
        <Metric label="Watching now" value={countValue(model.pollableSourceCount)} help="Active sources with poller support." />
        <Metric label="Stored only" value={countValue(model.storedOnlySourceCount)} help="Approved sources without poller support yet." />
      </div>
      <SourceSplitBars overview={overview} />
      <div className="scout-center-source-split">
        <div>
          <h3>Watching Now</h3>
          <SourceCards sources={watchingNow} stored={false} />
          {watchingNow.length === 0 ? <p className="scout-center-empty">No pollable sources are active.</p> : null}
        </div>
        <div>
          <h3>Stored Only</h3>
          <p className="scout-center-helper">
            Stored only means approved in the registry, but Scout does not have a poller for this source type yet.
          </p>
          <SourceCards sources={storedOnly} stored />
          {storedOnly.length === 0 ? <p className="scout-center-empty">No stored-only sources are active.</p> : null}
        </div>
      </div>
      {unknownSupport.length > 0 && watchingNow.length === 0 && storedOnly.length === 0 ? (
        <p className="scout-center-empty">
          {unknownSupport.length} source{unknownSupport.length === 1 ? "" : "s"} did not report poller support.
        </p>
      ) : null}
      <ul className="scout-center-list">
        {sources.slice(0, 10).map((source: ScoutSourceSummary) => (
          <li key={source.source_uri ?? source.label}>
            <strong>{source.label ?? sourceDisplayName(source.source_uri)}</strong>
            <span>
              {source.trust_label ?? "Trust not labeled"} -{" "}
              {source.health_label?.toLowerCase().includes("unsupported")
                ? "Needs poller support"
                : source.health_label ?? "Health unknown"}
            </span>
            <p>
              {countValue(source.packets_surfaced)} useful packets - Last checked{" "}
              {formatDateTime(source.last_polled_at)}
            </p>
            <details>
              <summary>Details</summary>
              <dl>
                <dt>URL</dt>
                <dd>{source.source_uri ?? "Unknown"}</dd>
                <dt>Trust tier</dt>
                <dd>{source.trust_tier ?? source.trust_category ?? "Unknown"}</dd>
                <dt>Consecutive failures</dt>
                <dd>{countValue(source.consecutive_failures)}</dd>
              </dl>
            </details>
          </li>
        ))}
      </ul>
      {sources.length === 0 ? <p className="scout-center-empty">No active sources are registered.</p> : null}
    </Section>
  );
}

function SourceCards({ sources, stored }: { sources: ScoutSourceSummary[]; stored: boolean }) {
  return (
    <ul className="scout-center-list">
      {sources.map((source: ScoutSourceSummary) => (
        <li key={source.source_uri ?? source.canonical_uri ?? source.label}>
          <strong>{sourceTitle(source)}</strong>
          <span>
            {sourceKindLabel(source)} - {source.source_origin ?? "origin unknown"} -{" "}
            {source.status ?? "status unknown"}
          </span>
          <p>
            {stored
              ? "Stored only means approved in the registry, but Scout does not have a poller for this source type yet."
              : sourceActivityText(source)}
          </p>
          <details>
            <summary>Details</summary>
            <dl>
              <dt>URL</dt>
              <dd>{sourceUri(source)}</dd>
              <dt>Source kind</dt>
              <dd>{sourceKindLabel(source)}</dd>
              <dt>Origin</dt>
              <dd>{source.source_origin ?? "Unknown"}</dd>
              <dt>Poller support</dt>
              <dd>{source.poller_supported === true ? "Watching now" : "Stored only"}</dd>
              <dt>Trust tier</dt>
              <dd>{source.trust_tier ?? source.trust_category ?? "Unknown"}</dd>
              <dt>Status</dt>
              <dd>{source.status ?? source.health_label ?? "Unknown"}</dd>
              <dt>Useful packets</dt>
              <dd>{countValue(source.packets_surfaced)}</dd>
              <dt>Consecutive failures</dt>
              <dd>{countValue(source.consecutive_failures)}</dd>
            </dl>
          </details>
        </li>
      ))}
    </ul>
  );
}

function HealthChecks({ overview }: { overview: ScoutOverview }) {
  const scheduler = overview.scheduler ?? {};
  const model = buildScoutHumanReadModel(overview);

  return (
    <Section
      id="safety-diagnostics"
      title="Safety and Diagnostics"
      help="Manual checks only. Scout safety gates stay human-controlled."
    >
      <div className="scout-center-metrics">
        <Metric
          label="Scheduler"
          value={scheduler.scheduler_running || scheduler.running ? "Running" : "Paused"}
          help="Background schedule state reported by Scout."
        />
        <Metric label="Safety checks" value="Manual" help="Smoke, source approvals, and soak snapshots stay deliberate." />
        <Metric
          label="Memory writes"
          value={model.memoryWritesOff ? "Off" : "Review"}
          help="Scout is not changing proxy memory or coding context when off."
        />
      </div>
      <details className="scout-center-advanced">
        <summary>Legacy Scout Workbench</summary>
        <p className="scout-center-helper">
          Raw packet and gate controls remain available here, but the command center above is the primary review surface.
        </p>
        <div className="scout-center-advanced-panel">
          <ScoutIntelligenceCenterPanel />
        </div>
      </details>
    </Section>
  );
}

export function ScoutIntelligenceCenter() {
  const { data, state, error } = useScoutOverview();

  return (
    <main className="dashboard-demo-v4-root scout-center-root">
      <DashboardDemoV4Atmosphere />
      <div className="dashboard-demo-v4-shell scout-center-shell">
        <header className="scout-center-header">
          <div>
            <p>Scout Intelligence</p>
            <h1>Intelligence Center</h1>
            <span>Readable review space for Scout briefings, source approvals, and safe search plans.</span>
          </div>
          <div className="scout-center-header-actions">
            <HomelabStatusBadge variant={state === "error" ? "offline" : state === "loading" ? "pending" : "live"}>
              {state === "error" ? "Offline" : state === "loading" ? "Loading" : "Online"}
            </HomelabStatusBadge>
            <Link href="/">Back to dashboard</Link>
          </div>
        </header>

        {state === "loading" ? (
          <section className="scout-center-section">
            <p className="scout-center-empty">Loading Scout overview.</p>
          </section>
        ) : null}

        {state === "error" ? (
          <section className="scout-center-section">
            <p className="scout-center-empty">{error ?? "Scout overview unavailable."}</p>
          </section>
        ) : null}

        {state === "loaded" && data ? (
          <>
            <ActionInbox overview={data} />
            <Briefing overview={data} />
            <Findings overview={data} />
            <SourceApprovals overview={data} />
            <SearchQueue overview={data} />
            <WatchedSources overview={data} />
            <HealthChecks overview={data} />
          </>
        ) : null}
      </div>
      <button type="button" className="scout-center-back-to-top" onClick={scrollToScoutTop} aria-label="Back to top">
        <ArrowUp aria-hidden="true" size={18} strokeWidth={2.4} />
      </button>
      <DashboardDemoV4FloatingNav />
    </main>
  );
}
