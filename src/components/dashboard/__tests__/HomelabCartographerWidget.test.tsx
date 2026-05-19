/// <reference types="vitest" />

import { render, screen, waitFor } from "@testing-library/react";

import { HomelabCartographerWidget } from "../HomelabCartographerWidget";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("HomelabCartographerWidget", () => {
  it("shows a loading state before Cartographer responds", () => {
    globalThis.fetch = vi.fn(() => new Promise<Response>(() => {})) as typeof fetch;

    render(<HomelabCartographerWidget />);

    expect(screen.getByText("Spirit Cartographer")).toBeInTheDocument();
    expect(screen.getByText("Loading")).toBeInTheDocument();
    expect(screen.getByText("Loading Cartographer state.")).toBeInTheDocument();
  });

  it("renders read-only v1 closeout dashboard cards", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            status: "observing",
            write_actions_enabled: false,
            authority_granted: false,
            actions_taken: false,
            dashboard_mode: "read_only_v1_closeout_surface",
            docs_path: "docs/cartographer-v1-evidence-artifacts.md",
            docs_label: "Cartographer v1 evidence artifact contract",
            primary_status: "blocked_missing_evidence",
            primary_label: "Blocked by missing evidence",
            v1_ready: false,
            readiness: "not_ready",
            blocker_count: 8,
            freeze_marker_status: "missing",
            next_action: "Record three clean diagnostic or closeout proof artifacts with passing results.",
            dashboard_cards: [
              {
                card_id: "v1-readiness",
                label: "V1 readiness",
                status: "not_ready",
                value: "blocked",
                detail: "8 blockers",
                endpoint: "/v1/cartographer/v1-readiness",
              },
              {
                card_id: "v1-evidence",
                label: "Evidence",
                status: "blocked",
                value: 8,
                detail: "missing real proof artifacts",
                endpoint: "/v1/cartographer/v1-evidence",
              },
              {
                card_id: "v1-freeze-marker",
                label: "Freeze marker",
                status: "missing",
                value: "data/cartographer-v1-freeze/freeze-marker.json",
                detail: "external marker validation",
                endpoint: "/v1/cartographer/v1-freeze-marker-validation",
              },
              {
                card_id: "v1-authority",
                label: "Authority",
                status: "locked",
                value: "locked",
                detail: "passing checks do not grant authority",
                endpoint: "/v1/cartographer/v1-closeout-status",
              },
              {
                card_id: "v1-docs",
                label: "Evidence contract",
                status: "read_only",
                value: "docs/cartographer-v1-evidence-artifacts.md",
                detail: "human-recorded artifact shapes",
                endpoint: "/v1/cartographer/v1-closeout-dashboard",
              },
            ],
          }),
          { status: 200 },
        ),
      ),
    ) as typeof fetch;

    render(<HomelabCartographerWidget />);

    await waitFor(() => {
      expect(screen.getByText("Blocked by missing evidence")).toBeInTheDocument();
    });

    expect(globalThis.fetch).toHaveBeenCalledWith("/v1/cartographer/v1-closeout-dashboard", {
      cache: "no-store",
    });
    expect(screen.getByText("V1 readiness")).toBeInTheDocument();
    expect(screen.getByText("Evidence")).toBeInTheDocument();
    expect(screen.getByText("Freeze marker")).toBeInTheDocument();
    expect(screen.getByText("Authority")).toBeInTheDocument();
    expect(screen.getByText("Evidence contract")).toBeInTheDocument();
    expect(screen.getByText("locked")).toBeInTheDocument();
    expect(screen.getByText("docs/cartographer-v1-evidence-artifacts.md")).toHaveAttribute(
      "title",
      "docs/cartographer-v1-evidence-artifacts.md",
    );
    expect(screen.getByText("data/cartographer-v1-freeze/freeze-marker.json")).toHaveAttribute(
      "title",
      "data/cartographer-v1-freeze/freeze-marker.json",
    );
    expect(
      screen.getByText("Record three clean diagnostic or closeout proof artifacts with passing results."),
    ).toBeInTheDocument();
  });

  it("shows unavailable without exposing write controls when the bridge fails", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            status: "unavailable",
            write_actions_enabled: false,
            error: "The dashboard could not reach the Source Proxy Cartographer endpoint.",
            dashboard_cards: [],
          }),
          { status: 200 },
        ),
      ),
    ) as typeof fetch;

    render(<HomelabCartographerWidget />);

    await waitFor(() => {
      expect(screen.getByText("Unavailable")).toBeInTheDocument();
    });

    expect(
      screen.getByText("The dashboard could not reach the Source Proxy Cartographer endpoint."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve|apply|push|commit/i })).toBeNull();
  });
});
