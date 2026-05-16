/// <reference types="vitest" />

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { HomelabScoutIntelligenceWidget } from "../HomelabScoutIntelligenceWidget";
import type {
  ScoutDiscoveryJobs,
  ScoutOverview,
  ScoutPromotions,
  ScoutSourceCandidates,
} from "@/lib/scout-overview";

const origFetch = globalThis.fetch;
const origConfirm = window.confirm;
const origPrompt = window.prompt;

afterEach(() => {
  globalThis.fetch = origFetch;
  window.confirm = origConfirm;
  window.prompt = origPrompt;
  vi.useRealTimers();
  vi.restoreAllMocks();
});

const emptyOverview: ScoutOverview = {
  counts: {
    raw_event_index: 4,
    extracted_artifacts: 3,
    packets: 0,
    verdicts: 0,
  },
  backlog: {
    unsynthesized_artifacts: 3,
    debugger_pending_packets: 0,
    debugger_pending_without_verdict: 0,
  },
  human_summary: {
    pipeline_health: "needs_review",
    headline: "Scout scanned sources, but summaries have not been created yet.",
    scan_flow: [
      {
        id: "scanned",
        label: "Scanned",
        count: 4,
        help: "Unique source events Scout noticed from approved sources.",
      },
      {
        id: "cleaned",
        label: "Cleaned",
        count: 3,
        help: "Pages or commits converted into readable artifacts.",
      },
      {
        id: "summarized",
        label: "Summarized",
        count: 0,
        help: "Scout intelligence packets created.",
      },
      {
        id: "checked",
        label: "Checked",
        count: 0,
        help: "Packets reviewed by the Scout debugger.",
      },
    ],
    memory_status: {
      label: "Semantic memory inactive",
      active: false,
      reason: "No packet embeddings are stored.",
    },
    promotion_status: {
      promoted_count: 0,
      pending_review_count: 0,
      label: "No human-approved memory promotions yet",
    },
  },
  sources: [],
  recent: {
    surfaced: [],
    stored: [],
    pending: [],
  },
  scheduler: {
    scheduler_running: true,
    job_count: 2,
    jobs: [],
  },
};

function mockScoutFetch(
  overview: ScoutOverview,
  promotions: ScoutPromotions = {
    queued: [],
    approved: [],
    rejected: [],
    counts: { pending: 0, queued: 0, approved: 0, rejected: 0, total: 0 },
  },
  sourceCandidates: ScoutSourceCandidates = {
    counts: {
      recommended: 0,
      needs_review: 0,
      stored: 0,
      rejected: 0,
      blocked: 0,
      approved: 0,
    },
    candidates: [],
  },
  discoveryJobs: ScoutDiscoveryJobs = {
    count: 0,
    jobs: [],
  },
) {
  globalThis.fetch = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/scout/promotions") && !url.includes("/finalize")) {
      return Promise.resolve(new Response(JSON.stringify(promotions), { status: 200 }));
    }
    if (url.includes("/api/scout/source-candidates") && !url.match(/\/(approve|reject|block)$/)) {
      return Promise.resolve(new Response(JSON.stringify(sourceCandidates), { status: 200 }));
    }
    if (url.includes("/api/scout/discovery-jobs") && !url.match(/\/(pause|resume|search-preview|extract-candidates)$/)) {
      return Promise.resolve(new Response(JSON.stringify(discoveryJobs), { status: 200 }));
    }
    if (
      url.includes("/api/scout/packets/") ||
      url.includes("/api/scout/promotions/finalize") ||
      url.match(/\/api\/scout\/source-candidates\/[^/]+\/(approve|reject|block)$/) ||
      url.match(/\/api\/scout\/discovery-jobs\/[^/]+\/(pause|resume|search-preview|extract-candidates)$/)
    ) {
      return Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    }
    return Promise.resolve(new Response(JSON.stringify(overview), { status: 200 }));
  }) as typeof fetch;
}

describe("HomelabScoutIntelligenceWidget", () => {
  it("shows loading while the Scout overview request is pending", () => {
    globalThis.fetch = vi.fn(() => new Promise<Response>(() => {}));

    render(<HomelabScoutIntelligenceWidget />);

    expect(screen.getByText("Loading Scout overview")).toBeInTheDocument();
    expect(screen.getByLabelText("Loading Scout overview")).toBeInTheDocument();
  });

  it("shows unavailable when Scout overview cannot be fetched", async () => {
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

    await waitFor(() => {
      expect(screen.getAllByText("Scout overview unavailable.").length).toBeGreaterThan(0);
    });
  });

  it("renders the compact summary, metrics, and inactive memory state", async () => {
    mockScoutFetch(emptyOverview);

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(
        screen.getByText("Scout is running, but no useful-now intelligence yet."),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByText("Scout scanned sources, but summaries have not been created yet."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Unique scans are counted once. Idle runs after backlog drain are normal."),
    ).toBeInTheDocument();
    expect(screen.getByText("Semantic memory inactive \u00b7 0 promoted")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("Scanned")).toBeInTheDocument();
    expect(screen.getAllByText("Review Queue").length).toBeGreaterThan(1);
    expect(screen.queryByText("Needs Review")).not.toBeInTheDocument();
    expect(screen.getByText("Semantic Memory")).toBeInTheDocument();
    expect(screen.getByText("Discovery Jobs")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
    expect(screen.queryByText(/failure/i)).not.toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.getByText("Next Summary Run")).toBeInTheDocument();
    expect(screen.getByText("Next Safety Check")).toBeInTheDocument();
  });

  it("defaults to Useful Now and shows packet status, trust, source, and tags", async () => {
    const overview: ScoutOverview = {
      ...emptyOverview,
      counts: {
        raw_event_index: 12,
        extracted_artifacts: 9,
        packets: 2,
        verdicts: 1,
      },
      recent: {
        surfaced: [
          {
            packet_id: "pkt-1",
            title: "Python release notes",
            summary: "Python release notes mention a packaging regression.",
            entity_tags: ["Python", "GitHub", "Security"],
            human_status_label: "Useful Now",
            effective_status: "surfaced",
            source_label: "Python Blog",
            source_uri: "https://blog.python.org/release",
          },
        ],
      },
      sources: [
        {
          source_uri: "https://blog.python.org/release",
          label: "Python Blog",
          trust_label: "Official Project Blog",
          health_label: "Healthy",
        },
      ],
    };
    mockScoutFetch(overview);

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(
        screen.getByText("Python release notes mention a packaging regression."),
      ).toBeInTheDocument();
    });
    expect(screen.getByRole("tab", { name: "Useful Now" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("Python release notes")).toBeInTheDocument();
    expect(screen.getByText("Python Blog")).toBeInTheDocument();
    expect(screen.getByText("Official Project Blog")).toBeInTheDocument();
    expect(screen.getAllByText("Useful Now").length).toBeGreaterThan(1);
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("GitHub")).toBeInTheDocument();
    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Queue Python release notes/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Recheck Python release notes/i })).toBeInTheDocument();
  });

  it("shows source cards in the Sources tab", async () => {
    const overview: ScoutOverview = {
      ...emptyOverview,
      sources: [
        {
          source_uri: "https://github.com/fastapi/fastapi/commits/master",
          label: "FastAPI commits",
          trust_label: "Official GitHub Repo",
          health_label: "Healthy",
          packets_total: 1,
          packets_surfaced: 1,
          packets_stored: 0,
          packets_ignored: 0,
          last_polled_at: "2026-05-14T15:30:00Z",
        },
      ],
    };
    mockScoutFetch(overview);

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Sources" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("tab", { name: "Sources" }));

    expect(screen.getByText("FastAPI commits")).toBeInTheDocument();
    expect(screen.getByText("Official GitHub Repo")).toBeInTheDocument();
    expect(screen.getAllByText("Healthy").length).toBeGreaterThan(0);
    expect(screen.getByText("1 packet \u00b7 1 useful \u00b7 0 saved \u00b7 0 ignored")).toBeInTheDocument();
    expect(screen.getByText(/Last polled/)).toBeInTheDocument();
  });

  it("renders feed empty states safely", async () => {
    mockScoutFetch(emptyOverview);

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Saved Later" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("tab", { name: "Saved Later" }));
    expect(screen.getByText("No saved packets yet.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Review Queue" }));
    expect(screen.getByText("No packets waiting for review.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Promoted" }));
    expect(screen.getByText("No promoted packets yet.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Source Queue" }));
    expect(screen.getByText("No source candidates waiting for review.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Discovery" }));
    expect(screen.getByText("No discovery jobs yet.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Sources" }));
    expect(screen.getByText("No source data available yet.")).toBeInTheDocument();
  });

  it("shows discovery jobs and controls", async () => {
    mockScoutFetch(emptyOverview, undefined, undefined, {
      count: 1,
      jobs: [
        {
          job_id: "job-1",
          query: "official FastAPI release notes",
          topic_anchor: "FastAPI",
          status: "queued",
          max_results: 5,
          budget: 5,
          created_at: "2026-05-15T21:00:00Z",
          updated_at: "2026-05-15T21:00:00Z",
        },
      ],
    });

    render(<HomelabScoutIntelligenceWidget />);

    await screen.findByRole("tab", { name: "Discovery" });
    fireEvent.click(screen.getByRole("tab", { name: "Discovery" }));

    expect(screen.getByLabelText("Scout discovery job counts")).toBeInTheDocument();
    expect(screen.getByText("official FastAPI release notes")).toBeInTheDocument();
    expect(screen.getByText("queued \u00b7 5/5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pause" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Preview" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Extract" })).toBeInTheDocument();
  });

  it("creates a discovery job through the Scout route", async () => {
    mockScoutFetch(emptyOverview);

    render(<HomelabScoutIntelligenceWidget />);

    await screen.findByRole("tab", { name: "Discovery" });
    fireEvent.click(screen.getByRole("tab", { name: "Discovery" }));
    fireEvent.change(screen.getByLabelText("Discovery query"), {
      target: { value: "official Python release notes" },
    });
    fireEvent.change(screen.getByLabelText("Topic anchor"), {
      target: { value: "Python" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/discovery-jobs",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining('"query":"official Python release notes"'),
        }),
      );
    });
    expect(await screen.findByText("Discovery job created.")).toBeInTheDocument();
  });

  it("pauses and resumes discovery jobs through the Scout route", async () => {
    mockScoutFetch(emptyOverview, undefined, undefined, {
      count: 1,
      jobs: [
        {
          job_id: "job-control",
          query: "official FastAPI release notes",
          topic_anchor: "FastAPI",
          status: "queued",
          max_results: 5,
          budget: 5,
          created_at: "2026-05-15T21:00:00Z",
          updated_at: "2026-05-15T21:00:00Z",
        },
      ],
    });

    render(<HomelabScoutIntelligenceWidget />);

    await screen.findByRole("tab", { name: "Discovery" });
    fireEvent.click(screen.getByRole("tab", { name: "Discovery" }));
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/discovery-jobs/job-control/pause",
        { method: "POST" },
      );
    });
  });

  it("shows source candidates and review actions", async () => {
    mockScoutFetch(
      emptyOverview,
      undefined,
      {
        counts: {
          recommended: 1,
          needs_review: 0,
          stored: 0,
          rejected: 0,
          blocked: 0,
          approved: 0,
        },
        candidates: [
          {
            candidate_id: "candidate-1",
            canonical_uri: "https://blog.python.org/2024/10/python-3130-final-released",
            display_uri: "https://blog.python.org/2024/10/python-3130-final-released/",
            source_kind: "release_feed",
            status: "recommended",
            confidence_score: 0.97,
            trust_label: "Official project blog",
            recommendation: "Recommended for manual review before activation.",
            discovered_from_uri: "https://blog.python.org/feeds/posts/default",
            reason_codes: ["official_docs_pattern", "linked_from_active_source"],
            review_history: [
              {
                review_event_id: "event-1",
                candidate_id: "candidate-1",
                canonical_uri: "https://blog.python.org/2024/10/python-3130-final-released",
                action: "reject",
                previous_status: "recommended",
                new_status: "rejected",
                reviewed_by: "tester",
                reason: "duplicate",
                created_at: "2026-05-15T21:00:00Z",
              },
            ],
          },
        ],
      },
    );

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Source Queue" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Source Queue" }));

    expect(screen.getByLabelText("Scout source candidate counts")).toBeInTheDocument();
    expect(screen.getByText("Needs Review")).toBeInTheDocument();
    expect(screen.getByText("blog.python.org/2024/10/python-3130-final-released")).toBeInTheDocument();
    expect(screen.getByText("recommended \u00b7 97%")).toBeInTheDocument();
    expect(screen.getByText("Official project blog")).toBeInTheDocument();
    expect(screen.getByText(/reject by tester/)).toBeInTheDocument();
    expect(screen.getByText(/duplicate/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Block" })).toBeInTheDocument();
  });

  it("approves a source candidate through the Scout route", async () => {
    window.confirm = vi.fn(() => true);
    mockScoutFetch(
      emptyOverview,
      undefined,
      {
        counts: { recommended: 1 },
        candidates: [
          {
            candidate_id: "candidate-approve",
            canonical_uri: "github://fastapi/fastapi",
            display_uri: "https://github.com/fastapi/fastapi",
            source_kind: "github_repo",
            status: "recommended",
            confidence_score: 0.99,
            recommendation: "Recommended for manual review before activation.",
            reason_codes: ["official_repo_pattern"],
          },
        ],
      },
    );

    render(<HomelabScoutIntelligenceWidget />);

    await screen.findByRole("tab", { name: "Source Queue" });
    fireEvent.click(screen.getByRole("tab", { name: "Source Queue" }));
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/source-candidates/candidate-approve/approve",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining('"approved_by":"manual-review"'),
        }),
      );
    });
    expect(await screen.findByText("Source candidate approved.")).toBeInTheDocument();
  });

  it("queues a packet through the Scout route and refreshes", async () => {
    window.confirm = vi.fn(() => true);
    const overview: ScoutOverview = {
      ...emptyOverview,
      recent: {
        surfaced: [
          {
            packet_id: "pkt-queue",
            title: "Queue candidate",
            summary: "A useful Scout packet.",
            human_status_label: "Useful Now",
          },
        ],
      },
    };
    mockScoutFetch(overview);

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Queue Queue candidate/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /Queue Queue candidate/i }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/packets/pkt-queue/queue-promotion",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
    expect(await screen.findByText("Packet queued for promotion review.")).toBeInTheDocument();
  });

  it("shows Queue for a Saved Later packet", async () => {
    const overview: ScoutOverview = {
      ...emptyOverview,
      recent: {
        stored: [
          {
            packet_id: "pkt-stored",
            title: "Stored candidate",
            summary: "A saved packet.",
            human_status_label: "Saved Later",
          },
        ],
      },
    };
    mockScoutFetch(overview);

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Saved Later" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Saved Later" }));

    expect(screen.getByRole("button", { name: /Queue Stored candidate/i })).toBeInTheDocument();
  });

  it("allows queue again for a rejected packet", async () => {
    const overview: ScoutOverview = {
      ...emptyOverview,
      recent: {
        surfaced: [
          {
            packet_id: "pkt-rejected",
            title: "Rejected candidate",
            summary: "Previously rejected.",
            promotion_status: "rejected",
          },
        ],
      },
    };
    mockScoutFetch(overview);

    render(<HomelabScoutIntelligenceWidget />);

    expect(
      await screen.findByRole("button", { name: /Queue again Rejected candidate/i }),
    ).toBeInTheDocument();
  });

  it("shows queued state for an already queued packet", async () => {
    const overview: ScoutOverview = {
      ...emptyOverview,
      recent: {
        surfaced: [
          {
            packet_id: "pkt-queued",
            title: "Queued candidate",
            summary: "Already queued.",
            promotion_status: "queued",
            promotion_label: "Queued for review",
          },
        ],
      },
    };
    mockScoutFetch(overview);

    render(<HomelabScoutIntelligenceWidget />);

    const button = await screen.findByRole("button", { name: /Queued Queued candidate/i });
    expect(button).toBeDisabled();
  });

  it("shows review queue and approve/reject actions", async () => {
    mockScoutFetch(emptyOverview, {
      queued: [
        {
          promotion_id: "promo-1",
          packet_id: "pkt-1",
          requested_at: "2026-05-14T00:00:00Z",
          status: "queued",
          packet: { title: "Review me", summary: "Queued packet summary." },
        },
      ],
      approved: [],
      rejected: [],
      counts: { pending: 1, queued: 1, approved: 0, rejected: 0, total: 1 },
    });

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Review Queue" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Review Queue" }));

    expect(screen.getByText("Review me")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
  });

  it("shows approved promotions in the Promoted tab", async () => {
    mockScoutFetch(emptyOverview, {
      queued: [],
      approved: [
        {
          promotion_id: "promo-2",
          packet_id: "pkt-2",
          requested_at: "2026-05-14T00:00:00Z",
          approved_at: "2026-05-14T00:01:00Z",
          approved_by: "manual-review",
          status: "approved",
          packet: { title: "Promoted packet", summary: "Approved packet summary." },
        },
      ],
      rejected: [],
      counts: { pending: 0, queued: 0, approved: 1, rejected: 0, total: 1 },
    });

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: "Promoted" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("tab", { name: "Promoted" }));

    expect(screen.getByText("Promoted packet")).toBeInTheDocument();
    expect(screen.getAllByText("Promoted").length).toBeGreaterThan(1);
  });

  it("approve action calls the finalize route", async () => {
    mockScoutFetch(emptyOverview, {
      queued: [
        {
          promotion_id: "promo-approve",
          packet_id: "pkt-approve",
          requested_at: "2026-05-14T00:00:00Z",
          status: "queued",
          summary: "Approve me.",
        },
      ],
      approved: [],
      rejected: [],
      counts: { pending: 1, queued: 1, approved: 0, rejected: 0, total: 1 },
    });

    render(<HomelabScoutIntelligenceWidget />);

    await screen.findByRole("tab", { name: "Review Queue" });
    fireEvent.click(screen.getByRole("tab", { name: "Review Queue" }));
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/promotions/finalize",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining('"action":"approve"'),
        }),
      );
    });
  });

  it("reject action calls the finalize route", async () => {
    window.prompt = vi.fn(() => "Not relevant enough for memory.");
    window.confirm = vi.fn(() => true);
    mockScoutFetch(emptyOverview, {
      queued: [
        {
          promotion_id: "promo-reject",
          packet_id: "pkt-reject",
          requested_at: "2026-05-14T00:00:00Z",
          status: "queued",
          summary: "Reject me.",
        },
      ],
      approved: [],
      rejected: [],
      counts: { pending: 1, queued: 1, approved: 0, rejected: 0, total: 1 },
    });

    render(<HomelabScoutIntelligenceWidget />);

    await screen.findByRole("tab", { name: "Review Queue" });
    fireEvent.click(screen.getByRole("tab", { name: "Review Queue" }));
    fireEvent.click(screen.getByRole("button", { name: "Reject" }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/scout/promotions/finalize",
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining('"action":"reject"'),
        }),
      );
    });
  });

  it("renders action errors safely", async () => {
    window.confirm = vi.fn(() => true);
    const overview: ScoutOverview = {
      ...emptyOverview,
      recent: {
        surfaced: [{ packet_id: "pkt-error", title: "Error packet", summary: "Will fail." }],
      },
    };
    globalThis.fetch = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/queue-promotion")) {
        return Promise.resolve(new Response(JSON.stringify({ ok: false }), { status: 502 }));
      }
      if (url.includes("/api/scout/promotions")) {
        return Promise.resolve(new Response(JSON.stringify({ queued: [], approved: [] }), { status: 200 }));
      }
      return Promise.resolve(new Response(JSON.stringify(overview), { status: 200 }));
    }) as typeof fetch;

    render(<HomelabScoutIntelligenceWidget />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Queue Error packet/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /Queue Error packet/i }));

    expect(await screen.findByText("Could not queue packet.")).toBeInTheDocument();
  });
});
