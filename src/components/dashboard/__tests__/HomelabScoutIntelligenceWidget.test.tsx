/// <reference types="vitest" />

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";

import { HomelabScoutIntelligenceWidget } from "../HomelabScoutIntelligenceWidget";
import { ScoutIntelligenceCenter } from "../ScoutIntelligenceCenter";
import { buildScoutHumanReadModel } from "@/lib/scout-human-readable";
import type {
  ScoutDiscoveryJobs,
  ScoutOverview,
  ScoutPromotions,
  ScoutSourceCandidates,
} from "@/lib/scout-overview";

type ImportDryRunMock = {
  status?: number;
  body?: unknown;
};

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
        recommended_review_order: 1,
        why_this_first: "Recommended source with official trust signals should be reviewed first.",
        risk_reason: "Stored-only source kind may not have poller support.",
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
  importDryRun: ImportDryRunMock = {},
) {
  globalThis.fetch = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/scout/promotions/import-dry-run")) {
      const status = importDryRun.status ?? 200;
      return Promise.resolve(
        new Response(
          JSON.stringify(
            importDryRun.body ?? {
              dry_run: true,
              import_ready: true,
              read_only: true,
              mutation_allowed: false,
              would_call_proxy_intake: false,
              would_write_proxy_memory: false,
              would_write_coding_context: false,
              would_finalize_promotion: false,
              receipt_preview: {
                event: "scout_manual_import_receipt_preview",
                imported: false,
                applied: false,
                approved_proxy_action: false,
                writes: {
                  append_only_evidence: false,
                  proxy_memory: false,
                  coding_context: false,
                  active_context: false,
                },
                rollback: {
                  tombstone_event: "scout_manual_import_tombstone",
                  delete_allowed: false,
                },
              },
            },
          ),
          { status },
        ),
      );
    }
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
    expect(screen.getByText(/Live Scout API refresh every 30 seconds/)).toBeInTheDocument();
    expect(screen.getByText(/Scout is online\. 1 promoted briefing ready\./)).toBeInTheDocument();
    expect(screen.getByText(/1 item open/)).toBeInTheDocument();
    expect(screen.getByText(/Manual-Controlled/)).toBeInTheDocument();
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

  it("labels the Intelligence Center as a live Scout API view", async () => {
    mockScoutFetch(overview);

    render(<ScoutIntelligenceCenter />);

    expect(await screen.findByText(/Live Scout API view/)).toBeInTheDocument();
    expect(screen.getByText(/Refreshes every 30 seconds/)).toBeInTheDocument();
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

  it("shows packet review evidence on useful packet cards", async () => {
    mockScoutFetch({
      ...overview,
      recent: {
        surfaced: [
          {
            packet_id: "packet-evidence",
            title: "FastAPI release packet",
            summary: "FastAPI release notes changed in a way worth reviewing.",
            source_uri: "https://example.com/releases",
            human_status_label: "Useful now",
            usefulness_label: "Useful now",
            usefulness_reason: "packet validates against IntelligencePacket",
            recommended_action: "inspect_now",
            confidence_label: "high",
            source_quality_score: 0.75,
            evaluated_at: "2026-05-14T00:00:00+00:00",
            recommended_review_order: 1,
            why_this_first: "Surfaced packet is likely useful for manual packet review.",
            risk_reason: "No automatic packet promotion is allowed.",
            provenance: {
              source_uri: "https://example.com/releases",
              extracted_artifact_path: "extracted/example/packet.md",
              synthesized_at: "2026-05-14T00:01:00+00:00",
            },
            findings: [
              {
                check_id: "schema_completeness",
                tier: 1,
                status: "passed",
                detail: "packet validates",
              },
            ],
          },
        ],
        stored: [],
        pending: [],
        promoted: [],
      },
    });

    render(<ScoutIntelligenceCenter />);

    expect(await screen.findByText("FastAPI release packet")).toBeInTheDocument();
    expect(screen.getByText("Source Trust")).toBeInTheDocument();
    expect(screen.getAllByText("Recommended Review Order").length).toBeGreaterThan(0);
    expect(screen.getAllByText("#1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Why This First").length).toBeGreaterThan(0);
    expect(screen.getByText("Surfaced packet is likely useful for manual packet review.")).toBeInTheDocument();
    expect(screen.getAllByText("Risk Reason").length).toBeGreaterThan(0);
    expect(screen.getByText("No automatic packet promotion is allowed.")).toBeInTheDocument();
    expect(screen.getByText("Quality")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("Artifact")).toBeInTheDocument();
    expect(screen.getByText("extracted/example/packet.md")).toBeInTheDocument();
    expect(screen.getByText("schema completeness: passed")).toBeInTheDocument();
  });

  it("shows source auto-rank labels as passive review evidence", async () => {
    mockScoutFetch(overview);

    render(<ScoutIntelligenceCenter />);

    expect((await screen.findAllByText("Recommended Review Order")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("#1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Why This First").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Recommended source with official trust signals should be reviewed first.").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Risk Reason").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Stored-only source kind may not have poller support.").length).toBeGreaterThan(0);
    expect(screen.queryByText("Auto Approve")).not.toBeInTheDocument();
  });

  it("wires Manual Search Plan preview controls to the discovery preview endpoint", async () => {
    mockScoutFetch(overview);

    render(<ScoutIntelligenceCenter />);

    fireEvent.click(await screen.findByRole("tab", { name: "Discovery Gate" }));
    const previewButtons = await screen.findAllByRole("button", { name: /Manual Preview Search/i });
    fireEvent.click(previewButtons[0]);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/discovery-jobs/job-1/search-preview",
        expect.objectContaining({ method: "POST" }),
      );
    });
    expect(await screen.findByText(/Discovery preview returned/)).toBeInTheDocument();
    expect(screen.getByText(/Approved delta \+0/)).toBeInTheDocument();
  });

  it("labels mutation-capable Scout gates as manual operator actions", async () => {
    mockScoutFetch(overview, {
      queued: [
        {
          promotion_id: "promotion-queued-1",
          packet_id: "packet-queued-1",
          requested_at: "2026-05-16T12:00:00Z",
          status: "queued",
          summary: "Queued briefing.",
        },
      ],
      approved: [],
      rejected: [],
      counts: { pending: 0, queued: 1, approved: 0, rejected: 0, total: 1 },
    });

    render(<ScoutIntelligenceCenter />);

    fireEvent.click(await screen.findByRole("tab", { name: "Source Gate" }));
    expect((await screen.findAllByRole("button", { name: "Manual Approve Source" })).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Manual Reject Source" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Manual Block Source" }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "Approve Source" })).not.toBeInTheDocument();

    fireEvent.click(await screen.findByRole("tab", { name: "Discovery Gate" }));
    expect(await screen.findByRole("button", { name: "Save Manual Plan" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Manual Preview Search" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Manual Extract Candidates" }).length).toBeGreaterThan(0);

    fireEvent.click(await screen.findByRole("tab", { name: "Packet Gate" }));
    expect(await screen.findByRole("button", { name: "Manual Promote Packet" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Manual Reject Packet" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Promote Packet" })).not.toBeInTheDocument();
  });

  it("shows mobile-scannable diagnostics summary copy on the Scout page", async () => {
    mockScoutFetch(overview);

    render(<ScoutIntelligenceCenter />);

    const diagnosticsSection = (await screen.findByRole("heading", {
      name: "Safety and Diagnostics",
    })).closest("section");
    expect(diagnosticsSection).not.toBeNull();
    const diagnostics = within(diagnosticsSection as HTMLElement);
    expect(diagnostics.getByText("Packet backlog")).toBeInTheDocument();
    expect(diagnostics.getByText("1 item open")).toBeInTheDocument();
    expect(diagnostics.getByText("Discovery execution")).toBeInTheDocument();
    expect(diagnostics.getByText("Manual-Controlled")).toBeInTheDocument();
    expect(diagnostics.getAllByText("Memory writes").length).toBeGreaterThan(0);
  });

  it("wires approved promotion import dry run without finalizing promotion", async () => {
    mockScoutFetch(overview);

    render(<ScoutIntelligenceCenter />);

    fireEvent.click(await screen.findByRole("tab", { name: "Promoted" }));
    fireEvent.click(await screen.findByRole("button", { name: "Dry Run Import" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/promotions/import-dry-run",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            promotion_id: "promotion-1",
            requested_by: "manual-review",
          }),
        }),
      );
    });
    expect(await screen.findByText(/Import dry run passed/)).toBeInTheDocument();
    expect(screen.getByText(/Proxy memory write: false/)).toBeInTheDocument();
    const receipt = within(screen.getByLabelText("Scout import receipt preview"));
    expect(receipt.getByText("Receipt Preview Event")).toBeInTheDocument();
    expect(receipt.getByText("scout_manual_import_receipt_preview")).toBeInTheDocument();
    expect(receipt.getByText("Imported In Dry Run")).toBeInTheDocument();
    expect(receipt.getByText("Applied In Dry Run")).toBeInTheDocument();
    expect(receipt.getByText("Proxy Memory Write")).toBeInTheDocument();
    expect(receipt.getByText("Coding Context Write")).toBeInTheDocument();
    expect(receipt.getAllByText("false").length).toBeGreaterThan(0);
    expect(receipt.getByText("Rollback Tombstone Preview")).toBeInTheDocument();
    expect(receipt.getByText("scout_manual_import_tombstone")).toBeInTheDocument();
    expect(globalThis.fetch).not.toHaveBeenCalledWith(
      "/api/scout/promotions/finalize",
      expect.anything(),
    );
  });

  it("explains blocked import dry run without overclaiming writes", async () => {
    mockScoutFetch(overview, undefined, undefined, undefined, {
      status: 409,
      body: { detail: "SCOUT_PROMOTION_SIGNING_KEY is required" },
    });

    render(<ScoutIntelligenceCenter />);

    fireEvent.click(await screen.findByRole("tab", { name: "Promoted" }));
    fireEvent.click(await screen.findByRole("button", { name: "Dry Run Import" }));

    expect(
      await screen.findByText(
        /Scout remains dry-run-only\. No proxy intake call, proxy memory write, coding context write, or promotion finalization occurred\./,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Scout import receipt preview")).not.toBeInTheDocument();
    expect(globalThis.fetch).not.toHaveBeenCalledWith(
      "/api/scout/promotions/finalize",
      expect.anything(),
    );
  });
});
