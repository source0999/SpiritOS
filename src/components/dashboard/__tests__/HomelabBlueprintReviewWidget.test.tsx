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
    expect(screen.getByText("Dashboard blueprint update")).toBeInTheDocument();
    expect(screen.getByText("_blueprints/current/dashboard_state.md")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Expand diff preview" }));

    expect(screen.getByText("+### Cartographer Review Note")).toBeInTheDocument();
  });

  it("stages approve and reject locally without calling write endpoints", async () => {
    mockProposalsFetch({
      status: "observing",
      write_actions_enabled: false,
      proposal_count: 1,
      pending_proposals: 1,
      actions_taken: false,
      proposals: [
        {
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
        },
      ],
    });

    const promptSpy = vi.spyOn(window, "prompt").mockReturnValue("Too broad.");

    render(<HomelabBlueprintReviewWidget />);

    await screen.findByText("dashboard blueprint update");

    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(screen.getByText("Approval staged for review. No apply, commit, or push ran.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reject" }));
    expect(promptSpy).toHaveBeenCalled();
    expect(screen.getByText("rejected staged: Too broad.")).toBeInTheDocument();

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
      ) as typeof fetch;

    render(<HomelabBlueprintReviewWidget />);

    await screen.findByRole("button", { name: "Apply approved docs" });
    fireEvent.click(screen.getByRole("button", { name: "Apply approved docs" }));

    await waitFor(() => {
      expect(
        screen.getByText("Proposal applied: _blueprints/current/dashboard_state.md"),
      ).toBeInTheDocument();
    });

    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    expect(globalThis.fetch).toHaveBeenLastCalledWith(
      "/v1/cartographer/proposals/bp-20260515-apply/apply-approved",
      expect.objectContaining({
        method: "POST",
      }),
    );
    expect(screen.queryByRole("button", { name: /commit|push/i })).toBeNull();
  });
});
