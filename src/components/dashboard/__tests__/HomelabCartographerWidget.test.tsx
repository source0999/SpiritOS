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

  it("renders read-only project, blueprint, proposal, and lock metrics", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            status: "observing",
            write_actions_enabled: false,
            configured_roots: [{ path: "/home/source/SpiritOS" }],
            blocked_roots: [],
            projects: [
              {
                project_id: "spiritos",
                name: "SpiritOS",
                root: "/home/source/SpiritOS",
                markers: [".git", "package.json", "README.md", "_blueprints"],
                status: "detected",
                write_policy: "read_only",
              },
            ],
            blueprint_count: 15,
            pending_proposals: 0,
          }),
          { status: 200 },
        ),
      ),
    ) as typeof fetch;

    render(<HomelabCartographerWidget />);

    await waitFor(() => {
      expect(screen.getByText("Observing")).toBeInTheDocument();
    });

    expect(screen.getByText("Projects Detected")).toBeInTheDocument();
    expect(screen.getByText("Blueprints Indexed")).toBeInTheDocument();
    expect(screen.getByText("Pending Proposals")).toBeInTheDocument();
    expect(screen.getByText("Write Mode")).toBeInTheDocument();
    expect(screen.getByText("Locked")).toBeInTheDocument();
    expect(
      screen.getByText("SpiritOS is detected from .git, package.json, README.md, _blueprints."),
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
