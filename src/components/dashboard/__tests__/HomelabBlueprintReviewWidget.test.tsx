/// <reference types="vitest" />

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { HomelabBlueprintReviewWidget } from "../HomelabBlueprintReviewWidget";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

function mockProposalsFetch(payload: object) {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve(
      new Response(JSON.stringify(payload), {
        status: 200,
      }),
    ),
  ) as typeof fetch;
}

describe("HomelabBlueprintReviewWidget", () => {
  it("shows loading state before proposal data arrives", () => {
    globalThis.fetch = vi.fn(() => new Promise<Response>(() => {})) as typeof fetch;

    render(<HomelabBlueprintReviewWidget />);

    expect(screen.getByText("Blueprint Review")).toBeInTheDocument();
    expect(screen.getByText("Loading")).toBeInTheDocument();
    expect(screen.getByText("Loading blueprint proposals.")).toBeInTheDocument();
  });

  it("renders proposal counts and expands diff preview", async () => {
    mockProposalsFetch({
      status: "observing",
      write_actions_enabled: false,
      proposal_count: 1,
      pending_proposals: 1,
      actions_taken: false,
      deduped: true,
      duplicate_proposals_present: 0,
      duplicate_proposals_suppressed: 0,
      proposals: [
        {
          proposal_id: "bp-20260515-001",
          project_id: "spiritos",
          status: "drafted",
          type: "blueprint_update",
          component: "dashboard",
          requires_approval: true,
          title: "Dashboard blueprint update",
          affected_blueprints: ["dashboard-state"],
          changed_files: ["src/components/dashboard/HomelabCartographerWidget.tsx"],
          proposed_files: ["_blueprints/current/dashboard_state.md"],
          diff_preview: "+### Cartographer Review Note",
          confidence: "medium",
          rationale: "Dashboard changed; blueprint review suggested.",
          generated: true,
          persisted: false,
          applied: false,
          action_taken: false,
        },
        {
          proposal_id: "bp-20260515-002",
          project_id: "spiritos",
          status: "drafted",
          type: "blueprint_update",
          component: "source-proxy",
          requires_approval: true,
          title: "Source proxy blueprint update",
          affected_blueprints: ["system-state"],
          changed_files: ["source_proxy/cartographer/apply.py"],
          proposed_files: ["_blueprints/current/system_state.md"],
          diff_preview: "+### Source Proxy Review Note",
          confidence: "medium",
          rationale: "Safety code changed; blueprint review suggested.",
          generated: true,
          persisted: false,
          applied: false,
          action_taken: false,
        },
      ],
    });

    render(<HomelabBlueprintReviewWidget />);

    await waitFor(() => {
      expect(screen.getByText("Review")).toBeInTheDocument();
    });

    expect(screen.getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(screen.getByText("Rejected")).toBeInTheDocument();
    expect(screen.getByText("Applied")).toBeInTheDocument();
    expect(screen.getByText("Push pending")).toBeInTheDocument();
    expect(screen.getByText("Review lane only")).toBeInTheDocument();
    expect(screen.getByText("Stable proposal queue")).toBeInTheDocument();
    expect(screen.getByText("Commit and push approvals are separate")).toBeInTheDocument();
    expect(screen.getAllByText("Dashboard blueprint update").length).toBeGreaterThan(0);
    expect(screen.getByText("bp-20260515-002")).toBeInTheDocument();
    expect(screen.getByText("medium risk")).toBeInTheDocument();
    expect(screen.getByText("generated draft")).toBeInTheDocument();
    expect(screen.getByText("Manual check")).toBeInTheDocument();
    expect(screen.getByText("Expected outcome")).toBeInTheDocument();
    expect(screen.getByText("Next step")).toBeInTheDocument();
    expect(screen.getByText("npx vitest run src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx")).toBeInTheDocument();
    expect(screen.getByText("Review records a decision only; apply, commit, and push remain blocked until separately approved.")).toBeInTheDocument();
    expect(screen.getByText("Approve, reject, or request edit after the manual check passes.")).toBeInTheDocument();
    expect(screen.getByText("_blueprints/current/dashboard_state.md")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Expand diff preview" }));

    expect(screen.getByText("+### Cartographer Review Note")).toBeInTheDocument();
  });

  it("records approve and reject decisions without applying docs", async () => {
    const baseProposal = {
      proposal_id: "bp-20260515-001",
      project_id: "spiritos",
      status: "pending_review",
      type: "blueprint_update",
      component: "dashboard",
      requires_approval: true,
      affected_blueprints: ["dashboard-state"],
      changed_files: ["src/components/dashboard/HomelabCartographerWidget.tsx"],
      proposed_files: ["_blueprints/current/dashboard_state.md"],
      diff_preview: "+ review",
    };
    globalThis.fetch = vi.fn((input, init) => {
      const url = String(input);
      if (url.endsWith("/review")) {
        const body = JSON.parse(String(init?.body ?? "{}")) as {
          decision: "approve" | "reject" | "request_edit";
          reason?: string;
        };
        const status =
          body.decision === "approve"
            ? "approved"
            : body.decision === "reject"
              ? "rejected"
              : "drafted";
        return Promise.resolve(
          new Response(
            JSON.stringify({
              status: "review_recorded",
              write_actions_enabled: false,
              actions_taken: false,
              apply_ran: false,
              commit_ran: false,
              push_ran: false,
              proposal: {
                ...baseProposal,
                status,
                rejection_reason: body.reason,
                transitions: [
                  {
                    actor: "dashboard-blueprint-review",
                    status,
                    timestamp: "2026-05-16T12:00:00Z",
                  },
                ],
              },
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(
        new Response(
          JSON.stringify({
            status: "observing",
            write_actions_enabled: false,
            proposal_count: 1,
            pending_proposals: 1,
            actions_taken: false,
            proposals: [baseProposal],
          }),
          { status: 200 },
        ),
      );
    }) as typeof fetch;

    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("Too broad.");

    render(<HomelabBlueprintReviewWidget />);

    await screen.findAllByText("dashboard blueprint update");

    fireEvent.click(screen.getByRole("button", { name: "Reject" }));
    await screen.findByText("rejected staged: Too broad.");
    expect(promptSpy).toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    await screen.findByText("Proposal approved from Dashboard. No apply, commit, or push ran.");

    expect(globalThis.fetch).toHaveBeenCalledTimes(5);
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      2,
      "/v1/cartographer/proposals/bp-20260515-001/review",
      expect.objectContaining({
        body: JSON.stringify({ decision: "reject", reason: "Too broad." }),
        method: "POST",
      }),
    );
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      4,
      "/v1/cartographer/proposals/bp-20260515-001/review",
      expect.objectContaining({
        body: JSON.stringify({ decision: "approve" }),
        method: "POST",
      }),
    );
  });

  it("requests edits through the review route", async () => {
    const proposal = {
      proposal_id: "bp-20260515-001",
      project_id: "spiritos",
      status: "pending_review",
      type: "blueprint_update",
      component: "dashboard",
      requires_approval: true,
      affected_blueprints: ["dashboard-state"],
      changed_files: ["src/components/dashboard/HomelabCartographerWidget.tsx"],
      proposed_files: ["_blueprints/current/dashboard_state.md"],
      diff_preview: "+ review",
    };
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "observing",
            write_actions_enabled: false,
            proposal_count: 1,
            pending_proposals: 1,
            actions_taken: false,
            proposals: [proposal],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "review_recorded",
            proposal: {
              ...proposal,
              status: "drafted",
            },
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "observing",
            write_actions_enabled: false,
            proposal_count: 1,
            pending_proposals: 1,
            actions_taken: false,
            proposals: [proposal],
          }),
          { status: 200 },
        ),
      ) as typeof fetch;
    vi.spyOn(window, "prompt").mockReturnValue("Clarify the changed file evidence.");

    render(<HomelabBlueprintReviewWidget />);

    await screen.findAllByText("dashboard blueprint update");
    fireEvent.click(screen.getByRole("button", { name: "Request edit" }));

    await screen.findByText("edit requested staged: Clarify the changed file evidence.");
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      2,
      "/v1/cartographer/proposals/bp-20260515-001/review",
      expect.objectContaining({
        body: expect.stringContaining('"decision":"request_edit"'),
        method: "POST",
      }),
    );
  });

  it("does not show review controls while no proposal exists", async () => {
    mockProposalsFetch({
      status: "observing",
      write_actions_enabled: false,
      proposal_count: 0,
      pending_proposals: 0,
      actions_taken: false,
      proposals: [],
    });

    render(<HomelabBlueprintReviewWidget />);

    await screen.findByText("No blueprint proposals waiting for review.");

    expect(screen.queryByRole("button", { name: "Approve" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Reject" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Request edit" })).toBeNull();
  });

  it("keeps apply unavailable until a proposal is already approved", async () => {
    const proposal = {
      proposal_id: "bp-20260515-pending",
      project_id: "spiritos",
      status: "pending_review",
      type: "blueprint_update",
      component: "dashboard",
      requires_approval: true,
      affected_blueprints: ["dashboard-state"],
      changed_files: ["src/components/dashboard/HomelabBlueprintReviewWidget.tsx"],
      proposed_files: ["_blueprints/current/dashboard_state.md"],
      diff_preview: "+ pending docs",
    };
    mockProposalsFetch({
      status: "observing",
      write_actions_enabled: false,
      proposal_count: 1,
      pending_proposals: 1,
      actions_taken: false,
      proposals: [proposal],
    });

    render(<HomelabBlueprintReviewWidget />);

    await screen.findAllByText("dashboard blueprint update");

    expect(screen.getByRole("button", { name: "Approve" })).toHaveAttribute("type", "button");
    expect(screen.getByRole("button", { name: "Reject" })).toHaveAttribute("type", "button");
    expect(screen.getByRole("button", { name: "Request edit" })).toHaveAttribute("type", "button");
    expect(screen.queryByRole("button", { name: "Apply approved docs" })).toBeNull();
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("shows an empty review queue without exposing apply commit or push buttons", async () => {
    mockProposalsFetch({
      status: "observing",
      write_actions_enabled: false,
      proposal_count: 0,
      pending_proposals: 0,
      actions_taken: false,
      proposals: [],
    });

    render(<HomelabBlueprintReviewWidget />);

    await waitFor(() => {
      expect(screen.getByText("No blueprint proposals waiting for review.")).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: /apply|commit|push/i })).toBeNull();
  });

  it("applies approved docs through the Cartographer route", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "observing",
            write_actions_enabled: false,
            proposal_count: 1,
            pending_proposals: 0,
            actions_taken: false,
            proposals: [
              {
                proposal_id: "bp-20260515-apply",
                project_id: "spiritos",
                status: "approved",
                type: "blueprint_update",
                component: "dashboard",
                requires_approval: true,
                affected_blueprints: ["dashboard-state"],
                changed_files: ["src/components/dashboard/HomelabBlueprintReviewWidget.tsx"],
                proposed_files: ["_blueprints/current/dashboard_state.md"],
                diff_preview: "+ approved docs",
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "applied",
            applied_files: ["_blueprints/current/dashboard_state.md"],
            verification: { status: "verified" },
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "observing",
            write_actions_enabled: false,
            proposal_count: 1,
            pending_proposals: 0,
            actions_taken: false,
            proposals: [
              {
                proposal_id: "bp-20260515-apply",
                project_id: "spiritos",
                status: "applied",
                type: "blueprint_update",
                component: "dashboard",
                requires_approval: true,
                affected_blueprints: ["dashboard-state"],
                changed_files: ["src/components/dashboard/HomelabBlueprintReviewWidget.tsx"],
                proposed_files: ["_blueprints/current/dashboard_state.md"],
                diff_preview: "+ approved docs",
                applied: true,
                action_taken: true,
              },
            ],
          }),
          { status: 200 },
        ),
      ) as typeof fetch;

    render(<HomelabBlueprintReviewWidget />);

    await screen.findByRole("button", { name: "Apply approved docs" });
    fireEvent.click(screen.getByRole("button", { name: "Apply approved docs" }));

    await waitFor(() => {
      expect(
        screen.getByText("Proposal applied: _blueprints/current/dashboard_state.md"),
      ).toBeInTheDocument();
    });

    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
    expect(globalThis.fetch).toHaveBeenNthCalledWith(
      2,
      "/v1/cartographer/proposals/bp-20260515-apply/apply-approved",
      expect.objectContaining({
        method: "POST",
      }),
    );
    expect(screen.queryByRole("button", { name: /commit|push/i })).toBeNull();
  });
});
