import type {
  ScoutDiscoveryJob,
  ScoutOverview,
  ScoutSourceCandidate,
  ScoutSourceCandidateStatus,
} from "@/lib/scout-overview";

export type ScoutSourceIconKind = "github" | "python" | "pydantic" | "rss" | "web";

export type ScoutSourceCandidateGroup = {
  root: string;
  label: string;
  iconKind: ScoutSourceIconKind;
  total: number;
  statuses: Record<string, number>;
  highestTrustLabel: string | null;
  candidates: ScoutSourceCandidate[];
};

export type ScoutDiscoveryBudgetSummary = {
  dailyLimit: number | null;
  usedToday: number | null;
  remainingToday: number | null;
  canCreateJob: boolean | null;
  blockedReason: string | null;
  queuedJobs: number;
  runningJobs: number;
};

export type ScoutPipelineCounts = {
  rawEvents: number;
  extractedArtifacts: number;
  packets: number;
  verdicts: number;
  promotedBriefings: number;
};

export type ScoutPacketSynthesisSummary = {
  label: string;
  state: string;
  routeConfigured: boolean;
  pendingArtifacts: number;
  model: string | null;
  apiBase: string | null;
  timeoutSeconds: number | null;
};

export type ScoutActionInboxCard = {
  id:
    | "sources-to-approve"
    | "promoted-briefings"
    | "manual-search-plans"
    | "watching-now"
    | "stored-only"
    | "safety-diagnostics";
  label: string;
  value: number | string;
  help: string;
};

export type ScoutHumanReadModel = {
  sourceSuggestions: number;
  packetReviews: number;
  needsReview: number;
  usefulFinds: number;
  promotedBriefingCount: number;
  processedPacketCount: number;
  pollableSourceCount: number;
  storedOnlySourceCount: number;
  sourceCandidateGroups: ScoutSourceCandidateGroup[];
  sourceStatusCounts: Record<string, number>;
  discoveryBudgetSummary: ScoutDiscoveryBudgetSummary;
  packetSynthesisSummary: ScoutPacketSynthesisSummary;
  pipelineCounts: ScoutPipelineCounts;
  reviewInboxCount: number;
  actionInboxCards: ScoutActionInboxCard[];
  queuedJobs: number;
  runningJobs: number;
  staleJobs: number;
  duplicateJobs: number;
  noisyJobs: number;
  activeSources: number;
  unsupportedSources: number;
  memoryWritesOff: boolean;
  manualApprovalRequired: boolean;
  budgetLeft: number | null;
  summarySentence: string;
  queueSentence: string;
};

export type ScoutDiagnosticsCopy = {
  packetBacklogLabel: string;
  packetBacklogHelp: string;
  packetSynthesisLabel: string;
  packetSynthesisHelp: string;
  discoveryExecutionLabel: string;
  discoveryExecutionHelp: string;
  memorySafetyLabel: string;
  memorySafetyHelp: string;
};

function valueOrZero(value: number | null | undefined): number {
  return typeof value === "number" ? value : 0;
}

function plural(count: number, singular: string, pluralLabel = `${singular}s`): string {
  return `${count.toLocaleString()} ${count === 1 ? singular : pluralLabel}`;
}

function manualModeLabel(mode: string | null | undefined): string {
  if (!mode) return "Manual-controlled";
  return mode
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("-");
}

function jobMatches(job: ScoutDiscoveryJob, needle: string): boolean {
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

  return haystack.includes(needle);
}

function statusCountsFromCandidates(
  candidates: ScoutSourceCandidate[],
  counts: Partial<Record<ScoutSourceCandidateStatus, number>> | undefined,
): Record<string, number> {
  const statusCounts: Record<string, number> = {};

  for (const [status, count] of Object.entries(counts ?? {})) {
    if (typeof count === "number") statusCounts[status] = count;
  }

  for (const candidate of candidates) {
    if (statusCounts[candidate.status] === undefined) {
      statusCounts[candidate.status] = 0;
    }
  }

  return statusCounts;
}

function candidateUri(candidate: ScoutSourceCandidate): string | null {
  return (
    candidate.canonical_uri ||
    candidate.display_uri ||
    candidate.discovered_from_uri ||
    (typeof candidate.metadata?.source_uri === "string" ? candidate.metadata.source_uri : null) ||
    (typeof candidate.metadata?.uri === "string" ? candidate.metadata.uri : null) ||
    null
  );
}

function rootFromUri(uri: string | null): string | null {
  if (!uri) return null;
  if (uri.startsWith("github://")) {
    const owner = uri
      .slice("github://".length)
      .split("/")
      .filter(Boolean)[0];
    return owner ? `github://${owner}` : "github://unknown";
  }

  try {
    const parsed = new URL(uri);
    return parsed.hostname || null;
  } catch {
    const [scheme, rest] = uri.split("://");
    if (scheme && rest) {
      return rest.split("/").filter(Boolean)[0] ?? uri;
    }
    return uri.split("/").filter(Boolean)[0] ?? null;
  }
}

function rootFromCandidate(candidate: ScoutSourceCandidate): string {
  const uriRoot = rootFromUri(candidateUri(candidate));
  if (uriRoot) return uriRoot;
  const topicAnchor =
    typeof candidate.metadata?.topic_anchor === "string" ? candidate.metadata.topic_anchor : null;
  return topicAnchor?.trim() || "unknown";
}

function iconKindForRoot(root: string, sourceKind: string | null | undefined): ScoutSourceIconKind {
  const normalizedRoot = root.toLowerCase();
  const normalizedKind = sourceKind?.toLowerCase() ?? "";
  if (normalizedRoot.startsWith("github://")) return "github";
  if (normalizedRoot.includes("pydantic")) return "pydantic";
  if (normalizedRoot.includes("python.org")) return "python";
  if (normalizedKind.includes("rss")) return "rss";
  return "web";
}

function labelForRoot(root: string): string {
  if (root === "blog.python.org") return "Python Blog";
  if (root === "www.python.org") return "Python.org";
  if (root === "pydantic.dev") return "Pydantic";
  if (root.startsWith("github://")) return root;
  if (root === "unknown") return "Unknown source family";
  return root;
}

function trustScore(label: string | null | undefined): number {
  const normalized = label?.toLowerCase() ?? "";
  if (normalized.includes("official")) return 5;
  if (normalized.includes("trusted")) return 4;
  if (normalized.includes("high")) return 3;
  if (normalized.includes("medium")) return 2;
  if (normalized.includes("low")) return 1;
  return 0;
}

function chooseHighestTrustLabel(candidates: ScoutSourceCandidate[]): string | null {
  let best: string | null = null;
  let bestScore = -1;

  for (const candidate of candidates) {
    const label = candidate.trust_label ?? candidate.trust_tier ?? null;
    const score = trustScore(label);
    if (label && score > bestScore) {
      best = label;
      bestScore = score;
    }
  }

  return best;
}

function buildSourceCandidateGroups(candidates: ScoutSourceCandidate[]): ScoutSourceCandidateGroup[] {
  const groups = new Map<string, ScoutSourceCandidate[]>();

  for (const candidate of candidates) {
    const root = rootFromCandidate(candidate);
    groups.set(root, [...(groups.get(root) ?? []), candidate]);
  }

  return Array.from(groups.entries())
    .map(([root, groupCandidates]) => {
      const statuses = groupCandidates.reduce<Record<string, number>>((acc, candidate) => {
        acc[candidate.status] = (acc[candidate.status] ?? 0) + 1;
        return acc;
      }, {});
      const sortedCandidates = [...groupCandidates].sort((a, b) => {
        const confidenceDelta = valueOrZero(b.confidence_score) - valueOrZero(a.confidence_score);
        if (confidenceDelta !== 0) return confidenceDelta;
        return candidateUri(a)?.localeCompare(candidateUri(b) ?? "") ?? 0;
      });

      return {
        root,
        label: labelForRoot(root),
        iconKind: iconKindForRoot(root, sortedCandidates[0]?.source_kind),
        total: sortedCandidates.length,
        statuses,
        highestTrustLabel: chooseHighestTrustLabel(sortedCandidates),
        candidates: sortedCandidates,
      };
    })
    .sort((a, b) => b.total - a.total || a.label.localeCompare(b.label));
}

export function sourceDisplayName(uri: string | null | undefined): string {
  if (!uri) return "Unknown source";
  if (uri.startsWith("github://")) return uri;
  try {
    return new URL(uri).host || uri;
  } catch {
    return uri;
  }
}

export function humanizeScoutLabel(value: string | null | undefined): string {
  if (!value) return "-";
  return value.replaceAll("_", " ");
}

export function buildScoutHumanReadModel(overview: ScoutOverview): ScoutHumanReadModel {
  const sourceCounts = overview.source_candidates?.counts ?? {};
  const sourceCandidates = overview.source_candidates?.candidates ?? [];
  const sourceStatusCounts = statusCountsFromCandidates(sourceCandidates, sourceCounts);
  const sourceCandidateGroups = buildSourceCandidateGroups(sourceCandidates);
  const sourceSuggestions = valueOrZero(sourceCounts.recommended) + valueOrZero(sourceCounts.needs_review);
  const queuedPromotions =
    valueOrZero(overview.promotions?.counts?.queued) ||
    valueOrZero(overview.promotions?.counts?.pending) ||
    (overview.promotions?.queued ?? []).length;
  const pendingPackets =
    valueOrZero(overview.backlog?.debugger_pending_without_verdict) ||
    valueOrZero(overview.backlog?.debugger_pending_packets);
  const packetReviews = queuedPromotions + pendingPackets;
  const usefulFinds =
    valueOrZero(overview.human_summary?.promotion_status?.promoted_count) ||
    valueOrZero(overview.promotions?.counts?.approved) ||
    (overview.promotions?.approved ?? []).length ||
    (overview.recent?.promoted ?? []).length;
  const promotedBriefingCount = usefulFinds;
  const jobs = overview.discovery_jobs?.jobs ?? [];
  const budget = overview.discovery_jobs?.budget;
  const queuedJobs =
    valueOrZero(budget?.queued_jobs) || jobs.filter((job) => job.status === "queued").length;
  const runningJobs =
    valueOrZero(budget?.running_jobs) || jobs.filter((job) => job.status === "running").length;
  const staleJobs = jobs.filter((job) => jobMatches(job, "stale")).length;
  const duplicateJobs = jobs.filter((job) => jobMatches(job, "duplicate")).length;
  const noisyJobs = jobs.filter((job) => jobMatches(job, "noisy")).length;
  const activeSources = overview.sources?.length ?? 0;
  const pollableSourceCount = (overview.sources ?? []).filter(
    (source) => source.poller_supported === true,
  ).length;
  const storedOnlySourceCount = (overview.sources ?? []).filter(
    (source) => source.poller_supported === false,
  ).length;
  const unsupportedSources = (overview.sources ?? []).filter(
    (source) => source.health_label?.toLowerCase().includes("unsupported"),
  ).length;
  const memoryStatus = overview.human_summary?.memory_status;
  const packetSynthesis =
    overview.packet_synthesis ?? overview.human_summary?.packet_synthesis_status ?? {};
  const packetSynthesisSummary = {
    label: packetSynthesis.label ?? "Packet synthesis unknown",
    state: packetSynthesis.state ?? "unknown",
    routeConfigured: packetSynthesis.route_configured === true,
    pendingArtifacts: valueOrZero(packetSynthesis.pending_artifacts),
    model: packetSynthesis.model ?? null,
    apiBase: packetSynthesis.api_base ?? null,
    timeoutSeconds:
      typeof packetSynthesis.timeout_seconds === "number"
        ? packetSynthesis.timeout_seconds
        : null,
  };
  const memoryWritesOff = memoryStatus?.write_enabled !== true;
  const manualApprovalRequired = true;
  const needsReview = sourceSuggestions + packetReviews;
  const reviewInboxCount = needsReview;
  const pipelineCounts = {
    rawEvents: valueOrZero(overview.counts?.raw_event_index) || valueOrZero(overview.counts?.raw_events),
    extractedArtifacts:
      valueOrZero(overview.counts?.extracted_artifacts) || valueOrZero(overview.counts?.artifacts),
    packets: valueOrZero(overview.counts?.packets),
    verdicts: valueOrZero(overview.counts?.verdicts),
    promotedBriefings: promotedBriefingCount,
  };
  const processedPacketCount = pipelineCounts.packets;
  const discoveryBudgetSummary = {
    dailyLimit: typeof budget?.daily_limit === "number" ? budget.daily_limit : null,
    usedToday: typeof budget?.used_today === "number" ? budget.used_today : null,
    remainingToday: typeof budget?.remaining_today === "number" ? budget.remaining_today : null,
    canCreateJob: typeof budget?.can_create_job === "boolean" ? budget.can_create_job : null,
    blockedReason: budget?.blocked_reason ?? null,
    queuedJobs,
    runningJobs,
  };
  const clutterParts = [
    staleJobs > 0 ? plural(staleJobs, "stale job") : null,
    duplicateJobs > 0 ? plural(duplicateJobs, "duplicate job") : null,
    noisyJobs > 0 ? plural(noisyJobs, "noisy job") : null,
  ].filter(Boolean);

  const summarySentence = [
    "Scout is online.",
    packetSynthesisSummary.state === "route_missing"
      ? "Packet model route needs repair."
      : packetSynthesisSummary.state === "pending"
        ? `${plural(packetSynthesisSummary.pendingArtifacts, "artifact")} waiting for packet synthesis.`
        : null,
    usefulFinds > 0
      ? `${plural(usefulFinds, "promoted briefing")} ready.`
      : "No promoted briefings yet.",
    needsReview > 0 ? `${plural(needsReview, "item")} need review.` : "Nothing needs approval right now.",
    queuedJobs > 0 ? `${plural(queuedJobs, "search job")} queued.` : "No search jobs are queued.",
  ]
    .filter(Boolean)
    .join(" ");

  const queueSentence =
    clutterParts.length > 0
      ? `The search queue has ${clutterParts.join(", ")}.`
      : queuedJobs > 0
        ? "Manual search plans are saved, not running automatically."
        : "The search queue is clear.";
  const actionInboxCards: ScoutActionInboxCard[] = [
    {
      id: "sources-to-approve",
      label: "Sources to Approve",
      value: sourceSuggestions,
      help: "Source suggestions waiting for human review.",
    },
    {
      id: "promoted-briefings",
      label: "Promoted Briefings",
      value: promotedBriefingCount,
      help: "Briefings promoted into the useful lane.",
    },
    {
      id: "manual-search-plans",
      label: "Manual Search Plans",
      value: queuedJobs,
      help: "Saved search plans waiting for preview or extraction.",
    },
    {
      id: "watching-now",
      label: "Watching Now",
      value: pollableSourceCount,
      help: "Active sources with poller support.",
    },
    {
      id: "stored-only",
      label: "Stored Only",
      value: storedOnlySourceCount,
      help: "Approved sources without poller support yet.",
    },
    {
      id: "safety-diagnostics",
      label: "Safety State",
      value: memoryWritesOff ? "Manual" : "Review",
      help: "Manual approval remains required.",
    },
  ];

  return {
    sourceSuggestions,
    packetReviews,
    needsReview,
    usefulFinds,
    promotedBriefingCount,
    processedPacketCount,
    pollableSourceCount,
    storedOnlySourceCount,
    sourceCandidateGroups,
    sourceStatusCounts,
    discoveryBudgetSummary,
    packetSynthesisSummary,
    pipelineCounts,
    reviewInboxCount,
    actionInboxCards,
    queuedJobs,
    runningJobs,
    staleJobs,
    duplicateJobs,
    noisyJobs,
    activeSources,
    unsupportedSources,
    memoryWritesOff,
    manualApprovalRequired,
    budgetLeft: typeof budget?.remaining_today === "number" ? budget.remaining_today : null,
    summarySentence,
    queueSentence,
  };
}

export function buildScoutDiagnosticsCopy(overview: ScoutOverview): ScoutDiagnosticsCopy {
  const backlog = overview.backlog ?? {};
  const unsynthesized = valueOrZero(backlog.unsynthesized_artifacts ?? backlog.pending_artifacts);
  const debuggerPending = valueOrZero(
    backlog.debugger_pending_without_verdict ?? backlog.debugger_pending_packets,
  );
  const totalBacklog = unsynthesized + debuggerPending;
  const synthesis = overview.packet_synthesis ?? overview.human_summary?.packet_synthesis_status;
  const execution = overview.discovery_jobs?.execution ?? {};
  const automaticExecution = execution.automatic_execution === true;
  const workerRegistered = execution.worker_registered === true;
  const memory = overview.human_summary?.memory_status;

  return {
    packetBacklogLabel: totalBacklog === 0 ? "Backlog clear" : `${plural(totalBacklog, "item")} open`,
    packetBacklogHelp:
      totalBacklog === 0
        ? "No packet synthesis or debugger backlog is reported by the live Scout API."
        : `${plural(unsynthesized, "artifact")} waiting for synthesis; ${plural(debuggerPending, "packet")} waiting for debugger verdict.`,
    packetSynthesisLabel: synthesis?.label ?? "Packet synthesis unknown",
    packetSynthesisHelp:
      synthesis?.state === "ready"
        ? "Model route is configured and no extracted artifacts are waiting."
        : (synthesis?.help ?? "Packet synthesis status was not reported."),
    discoveryExecutionLabel:
      automaticExecution || workerRegistered ? "Review discovery execution" : manualModeLabel(execution.mode),
    discoveryExecutionHelp:
      automaticExecution || workerRegistered
        ? "Scout reported automatic discovery execution or a registered worker."
        : "Discovery jobs remain saved manual search plans. No automatic execution worker is registered.",
    memorySafetyLabel: memory?.write_enabled ? "Review memory writes" : "Memory writes off",
    memorySafetyHelp:
      memory?.reason ??
      "Scout is not writing into proxy memory or coding context automatically.",
  };
}
