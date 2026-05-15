export type ScoutCounts = Partial<{
  raw_event_index: number;
  raw_events: number;
  extracted_artifacts: number;
  artifacts: number;
  packets: number;
  verdicts: number;
  packet_embeddings: number;
  source_quality: number;
  promotion_queue: number;
  source_tracking: number;
}>;

export type ScoutBacklog = Partial<{
  unsynthesized_artifacts: number;
  pending_artifacts: number;
  debugger_pending_packets: number;
  debugger_pending_without_verdict: number;
}>;

export type ScoutSchedulerJob = {
  id?: string | null;
  next_run_time?: string | null;
};

export type ScoutScheduler = Partial<{
  scheduler_running: boolean;
  running: boolean;
  job_count: number;
  jobs: ScoutSchedulerJob[];
}>;

export type ScoutPacketVerdict = Partial<{
  decision: string | null;
  effective_status: string | null;
}>;

export type ScoutStatusExplanation = Partial<{
  raw_status: string | null;
  verdict_decision: string | null;
  effective_status: string | null;
  label: string | null;
  help: string | null;
}>;

export type ScoutPacket = {
  packet_id?: string | null;
  id?: string | null;
  summary?: string | null;
  title?: string | null;
  tags?: string[] | null;
  effective_status?: string | null;
  raw_status?: string | null;
  human_status_label?: string | null;
  status_explanation?: ScoutStatusExplanation | null;
  status?: string | null;
  source_label?: string | null;
  trust_label?: string | null;
  entity_tags?: string[] | null;
  source_uri?: string | null;
  promotion_status?: "queued" | "approved" | "rejected" | null;
  promotion_id?: string | null;
  promotion_label?: string | null;
  promotion_reason?: string | null;
  promotion_requested_at?: string | null;
  source_url?: string | null;
  uri?: string | null;
  provenance?: {
    source_label?: string | null;
    source_uri?: string | null;
    source_url?: string | null;
    uri?: string | null;
  } | null;
  _verdict?: ScoutPacketVerdict | null;
};

export type ScoutPromotionItem = {
  promotion_id: string;
  packet_id: string;
  requested_at: string;
  requested_by?: string | null;
  reason?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
  rejected_at?: string | null;
  rejected_reason?: string | null;
  status: "queued" | "approved" | "rejected";
  payload_sha256?: string | null;
  summary?: string | null;
  source_label?: string | null;
  trust_label?: string | null;
  human_status_label?: string | null;
  effective_status?: string | null;
  entity_tags?: string[] | null;
  packet?: ScoutPacket | null;
};

export type ScoutPromotions = Partial<{
  items: ScoutPromotionItem[];
  queued: ScoutPromotionItem[];
  approved: ScoutPromotionItem[];
  rejected: ScoutPromotionItem[];
  counts: Partial<Record<"pending" | "queued" | "approved" | "rejected" | "total", number>>;
}>;

export type ScoutHumanSummary = Partial<{
  pipeline_health: "healthy" | "needs_review" | "idle" | "error";
  headline: string;
  scan_flow: Array<{
    id: "scanned" | "cleaned" | "summarized" | "checked";
    label: string;
    count: number;
    help: string;
  }>;
  memory_status: {
    label: string;
    active: boolean;
    reason?: string;
  };
  promotion_status: {
    promoted_count: number;
    pending_review_count: number;
    rejected_count?: number;
    label: string;
  };
}>;

export type ScoutSourceSummary = Partial<{
  source_uri: string;
  label: string;
  trust_category: string;
  trust_label: string;
  trust_tier: string;
  last_polled_at: string | null;
  last_modified: string | null;
  consecutive_failures: number;
  rate_limit_remaining: number | null;
  health_label: string;
  packets_total: number;
  packets_surfaced: number;
  packets_stored: number;
  packets_ignored: number;
  source_quality_score: number | null;
}>;

export type ScoutSourceCandidateStatus =
  | "recommended"
  | "needs_review"
  | "stored"
  | "rejected"
  | "blocked"
  | "approved";

export type ScoutSourceCandidate = {
  candidate_id: string;
  canonical_uri: string;
  display_uri: string;
  source_kind: string;
  status: ScoutSourceCandidateStatus;
  confidence_score: number;
  trust_label?: string | null;
  trust_tier?: string | null;
  recommendation?: string | null;
  discovered_from_uri?: string | null;
  discovered_from_event_id?: string | null;
  discovered_from_packet_id?: string | null;
  reason_codes?: string[] | null;
  explanation?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  rejection_reason?: string | null;
  blocked_reason?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type ScoutSourceCandidates = Partial<{
  counts: Partial<Record<ScoutSourceCandidateStatus, number>>;
  candidates: ScoutSourceCandidate[];
}>;

export type ScoutOverview = Partial<{
  counts: ScoutCounts;
  backlog: ScoutBacklog;
  human_summary: ScoutHumanSummary;
  sources: ScoutSourceSummary[];
  recent: Partial<{
    surfaced: ScoutPacket[];
    stored: ScoutPacket[];
    pending: ScoutPacket[];
    promoted: ScoutPacket[];
  }>;
  scheduler: ScoutScheduler;
  promotions: ScoutPromotions;
  source_candidates: ScoutSourceCandidates;
}>;

export type ScoutOverviewRouteError = {
  ok: false;
  status: "unavailable";
  error: string;
};
