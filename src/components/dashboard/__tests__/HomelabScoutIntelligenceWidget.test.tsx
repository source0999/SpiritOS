/// <reference types="vitest" />

import { render, screen, waitFor, within } from "@testing-library/react";

import { HomelabScoutIntelligenceWidget } from "../HomelabScoutIntelligenceWidget";
import { buildScoutHumanReadModel } from "@/lib/scout-human-readable";
import type {
  ScoutDiscoveryJobs,
  ScoutOverview,
  ScoutPromotions,
  ScoutSourceCandidates,
} from "@/lib/scout-overview";

const origFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = origFetch;
  vi.useRealTimers();
  vi.restoreAllMocks();
});

const overview: ScoutOverview = {
  counts: {
    raw_event_index: 4,
    extracted_artifacts: 3,
    packets: 2,
    verdicts: 1,
  },
  backlog: {
    debugger_pending_packets: 1,
    debugger_pending_without_verdict: 1,
  },
  human_summary: {
    pipeline_health: "needs_review",
    headline: "Scout scanned sources, but summaries have not been created yet.",
    memory_status: {
      label: "Semantic memory inactive",
      active: false,
      state: "inactive",
      mode_label: "Inactive",
      write_enabled: false,
      reason:
        "Scout is storing packets and source decisions, but it is not writing into proxy memory or coding context automatically.",
      safety_label: "Scout is not writing to proxy memory or coding context automatically.",
    },
    promotion_status: {
      promoted_count: 1,
      pending_review_count: 1,
      label: "1 promoted briefing",
    },
  },
  sources: [
    {
      source_uri: "https://example.com/releases",
      label: "Example releases",
      trust_label: "Trusted",
      health_label: "Healthy",
      poller_supported: true,
    },
    {
      source_uri: "https://example.com/about",
      label: "Example about",
      trust_label: "Trusted",
      health_label: "Stored only",
      poller_supported: false,
    },
  ],
  recent: {
    surfaced: [],
    stored: [],
    pending: [],
    promoted: [],
  },
  scheduler: {
    scheduler_running: true,
    job_count: 2,
    jobs: [],
  },
};

function mockScoutFetch(
  scoutOverview: ScoutOverview,
  promotions: ScoutPromotions = {
    queued: [],
    approved: [
      {
        promotion_id: "promotion-1",
        packet_id: "packet-1",
        requested_at: "2026-05-16T12:00:00Z",
        status: "approved",
        summary: "Useful briefing.",
      },
    ],
    rejected: [],
    counts: { pending: 0, queued: 0, approved: 1, rejected: 0, total: 1 },
  },
  sourceCandidates: ScoutSourceCandidates = {
    counts: {
      recommended: 2,
      needs_review: 1,
      stored: 0,
      rejected: 0,
      blocked: 0,
      approved: 0,
    },
    candidates: [
      {
        candidate_id: "candidate-python-blog-1",
        canonical_uri: "https://blog.python.org/2026/05/release.html",
        display_uri: "https://blog.python.org/2026/05/release.html",
        source_kind: "web_page",
        status: "recommended",
        confidence_score: 0.91,
        trust_label: "Official",
        reason_codes: ["official_project_blog"],
      },
      {
        candidate_id: "candidate-python-blog-2",
        canonical_uri: "https://blog.python.org/2026/05/security.html",
        display_uri: "https://blog.python.org/2026/05/security.html",
        source_kind: "web_page",
        status: "needs_review",
        confidence_score: 0.72,
        trust_label: "Trusted",
        reason_codes: ["python_release"],
      },
      {
        candidate_id: "candidate-pydantic-github",
        canonical_uri: "github://pydantic/pydantic-ai",
        display_uri: "github://pydantic/pydantic-ai",
        source_kind: "repository",
        status: "recommended",
        confidence_score: 0.88,
        trust_label: "Trusted",
        reason_codes: ["project_repository"],
      },
    ],
  },
  discoveryJobs: ScoutDiscoveryJobs = {
    count: 2,
    budget: {
      daily_limit: 3,
      used_today: 1,
      remaining_today: 2,
      can_create_job: true,
      blocked_reason: null,
      next_reset_hint: "next UTC day",
      queued_jobs: 2,
      running_jobs: 0,
      completed_jobs: 0,
      failed_jobs: 0,
    },
    execution: {
      mode: "manual_controlled",
      automatic_execution: false,
      worker_registered: false,
      queued_job_meaning: "saved_search_plan",
      advance_actions: ["search-preview", "extract-candidates"],
      explanation:
        "Discovery jobs are saved controlled search plans. Scout does not run them in the background.",
    },
    jobs: [
      {
        job_id: "job-1",
        query: "official release notes",
        status: "queued",
        max_results: 5,
        budget: 5,
        created_at: "2026-05-16T12:00:00Z",
        updated_at: "2026-05-16T12:00:00Z",
      },
      {
        job_id: "job-2",
        query: "duplicate docs",
        status: "queued",
        computed_status: "duplicate",
        attention_label: "Duplicate search",
        max_results: 5,
        budget: 5,
        created_at: "2026-05-16T12:00:00Z",
        updated_at: "2026-05-16T12:00:00Z",
      },
    ],
  },
) {
  globalThis.fetch = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/scout/promotions")) {
      return Promise.resolve(new Response(JSON.stringify(promotions), { status: 200 }));
    }
    if (url.includes("/api/scout/source-candidates")) {
      return Promise.resolve(new Response(JSON.stringify(sourceCandidates), { status: 200 }));
    }
    if (url.includes("/api/scout/discovery-jobs")) {
      return Promise.resolve(new Response(JSON.stringify(discoveryJobs), { status: 200 }));
    }
    if (url.includes("/api/scout/sources")) {
      return Promise.resolve(
        new Response(JSON.stringify({ count: scoutOverview.sources?.length ?? 0, sources: scoutOverview.sources ?? [] }), {
          status: 200,
        }),
      );
    }
    return Promise.resolve(new Response(JSON.stringify(scoutOverview), { status: 200 }));
  }) as typeof fetch;
}

describe("HomelabScoutIntelligenceWidget", () => {
  it("shows loading while the Scout overview request is pending", () => {
    globalThis.fetch = vi.fn(() => new Promise<Response>(() => {}));

    render(<HomelabScoutIntelligenceWidget />);

    expect(screen.getByText("Loading")).toBeInTheDocument();
    expect(screen.getByLabelText("Loading Scout overview")).toBeInTheDocument();
  });

  it("shows offline when Scout overview cannot be fetched", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ok: false,
          status: "unavailable",
          error: "Scout overview unavailable.",
        }),
        { status: 200 },
      ),
    );

    render(<HomelabScoutIntelligenceWidget />);

    expect(await screen.findByText("Offline")).toBeInTheDocument();
    expect(
      screen.getByText("Scout is offline or the overview route is unavailable."),
    ).toBeInTheDocument();
  });

  it("renders a calm dashboard summary with human labels and an Intelligence Center link", async () => {
    mockScoutFetch(overview);

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByText("Needs attention")).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "Scout Intelligence" })).toBeInTheDocument();
    expect(
      screen.getByText("Watches trusted sources and brings useful intelligence for review."),
    ).toBeInTheDocument();
    expect(screen.getByText(/Scout is online\. 1 promoted briefing ready\./)).toBeInTheDocument();
    const prioritySummary = within(screen.getByLabelText("Scout priority summary"));
    expect(prioritySummary.getByText("Review Inbox")).toBeInTheDocument();
    expect(prioritySummary.getByText("Promoted Briefings")).toBeInTheDocument();
    expect(prioritySummary.getByText("Manual Search Plans")).toBeInTheDocument();
    expect(prioritySummary.getByText("Watching Now")).toBeInTheDocument();
    expect(prioritySummary.getByText("Safety")).toBeInTheDocument();
    expect(screen.getByText("Memory writes off")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Intelligence Center" })).toHaveAttribute(
      "href",
      "/intelligence",
    );
    expect(screen.getByRole("link", { name: "Safety and Diagnostics" })).toHaveAttribute(
      "href",
      "/intelligence#safety-diagnostics",
    );
    expect(screen.queryByText("Packet Gate")).not.toBeInTheDocument();
    expect(screen.queryByText("Semantic Memory")).not.toBeInTheDocument();

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/sources",
        expect.objectContaining({ cache: "no-store" }),
      );
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/source-candidates?limit=200",
        expect.objectContaining({ cache: "no-store" }),
      );
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/discovery-jobs?limit=50",
        expect.objectContaining({ cache: "no-store" }),
      );
    });
  });

  it("builds the Scout Command Center read model from existing overview data", () => {
    const scoutOverview: ScoutOverview = {
      ...overview,
      promotions: {
        approved: [
          {
            promotion_id: "promotion-1",
            packet_id: "packet-1",
            requested_at: "2026-05-16T12:00:00Z",
            status: "approved",
            summary: "Useful briefing.",
          },
        ],
        counts: { approved: 1, queued: 0, pending: 0, rejected: 0, total: 1 },
      },
      source_candidates: {
        counts: {
          recommended: 2,
          needs_review: 1,
          stored: 0,
          rejected: 0,
          blocked: 0,
          approved: 0,
        },
        candidates: [
          {
            candidate_id: "candidate-python-blog-1",
            canonical_uri: "https://blog.python.org/2026/05/release.html",
            display_uri: "https://blog.python.org/2026/05/release.html",
            source_kind: "web_page",
            status: "recommended",
            confidence_score: 0.91,
            trust_label: "Official",
          },
          {
            candidate_id: "candidate-python-blog-2",
            canonical_uri: "https://blog.python.org/2026/05/security.html",
            display_uri: "https://blog.python.org/2026/05/security.html",
            source_kind: "web_page",
            status: "needs_review",
            confidence_score: 0.72,
            trust_label: "Trusted",
          },
          {
            candidate_id: "candidate-pydantic-github",
            canonical_uri: "github://pydantic/pydantic-ai",
            display_uri: "github://pydantic/pydantic-ai",
            source_kind: "repository",
            status: "recommended",
            confidence_score: 0.88,
            trust_label: "Trusted",
          },
        ],
      },
      discovery_jobs: {
        count: 2,
        budget: {
          daily_limit: 3,
          used_today: 1,
          remaining_today: 2,
          can_create_job: true,
          blocked_reason: null,
          queued_jobs: 2,
          running_jobs: 0,
        },
        jobs: [],
      },
    };

    const model = buildScoutHumanReadModel(scoutOverview);

    expect(model.promotedBriefingCount).toBe(1);
    expect(model.processedPacketCount).toBe(2);
    expect(model.pollableSourceCount).toBe(1);
    expect(model.storedOnlySourceCount).toBe(1);
    expect(model.reviewInboxCount).toBe(4);
    expect(model.pipelineCounts).toEqual({
      rawEvents: 4,
      extractedArtifacts: 3,
      packets: 2,
      verdicts: 1,
      promotedBriefings: 1,
    });
    expect(model.discoveryBudgetSummary).toMatchObject({
      dailyLimit: 3,
      usedToday: 1,
      remainingToday: 2,
      canCreateJob: true,
      blockedReason: null,
      queuedJobs: 2,
      runningJobs: 0,
    });
    expect(model.sourceStatusCounts).toMatchObject({
      recommended: 2,
      needs_review: 1,
    });
    expect(model.sourceCandidateGroups.map((group) => group.root)).toEqual([
      "blog.python.org",
      "github://pydantic",
    ]);
    expect(model.sourceCandidateGroups[0]).toMatchObject({
      label: "Python Blog",
      iconKind: "python",
      total: 2,
      highestTrustLabel: "Official",
      statuses: {
        recommended: 1,
        needs_review: 1,
      },
    });
    expect(model.actionInboxCards.map((card) => card.label)).toEqual([
      "Sources to Approve",
      "Promoted Briefings",
      "Manual Search Plans",
      "Watching Now",
      "Stored Only",
      "Safety State",
    ]);
  });

  it("keeps pipeline counts secondary behind details", async () => {
    mockScoutFetch(overview);

    render(<HomelabScoutIntelligenceWidget />);

    expect(await screen.findByText("Pipeline details")).toBeInTheDocument();
    expect(screen.getByText("Items found")).toBeInTheDocument();
    expect(screen.getByText("Cleaned up")).toBeInTheDocument();
    expect(screen.getByText("Summaries made")).toBeInTheDocument();
    expect(screen.getByText("Verified")).toBeInTheDocument();
  });
});
