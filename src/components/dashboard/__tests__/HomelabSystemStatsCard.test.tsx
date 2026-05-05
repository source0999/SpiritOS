import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { HomelabSystemStatsCard } from "../HomelabSystemStatsCard";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";

const origFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = origFetch;
  vi.useRealTimers();
  vi.restoreAllMocks();
});

const liveTwoNode: ClusterTelemetryResponse = {
  ok: true,
  collectedAt: new Date().toISOString(),
  nodes: [
    {
      id: "spirit-dell",
      label: "Spirit Dell",
      hostname: "source-server",
      status: "online",
      source: "local",
      platform: "linux",
      arch: "x64",
      cpu: { model: "Intel i7-6700", cores: 8, usagePct: 22, loadAvg: [0.1, 0.2, 0.3] },
      memory: { totalBytes: 16e9, freeBytes: 8e9, usedBytes: 8e9, usedPct: 50 },
      uptimeSec: 3600,
      collectedAt: new Date().toISOString(),
    },
    {
      id: "spiritdesktop",
      label: "spiritdesktop",
      hostname: "win-box",
      status: "online",
      source: "remote",
      platform: "win32",
      arch: "x64",
      cpu: { model: "AMD", cores: 8, usagePct: 5, loadAvg: null },
      memory: { totalBytes: 32e9, freeBytes: 16e9, usedBytes: 16e9, usedPct: 50 },
      uptimeSec: 120,
      collectedAt: new Date().toISOString(),
    },
  ],
  summary: { total: 2, online: 2, offline: 0, degraded: 0, unknown: 0 },
};

describe("HomelabSystemStatsCard", () => {
  it("fetches /api/telemetry/cluster on mount", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(liveTwoNode), { status: 200 }),
    );
    globalThis.fetch = mockFetch;
    render(<HomelabSystemStatsCard />);
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/telemetry/cluster",
        expect.objectContaining({ cache: "no-store" }),
      );
    });
  });

  it("renders live node labels from API (Spirit Dell, spiritdesktop)", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(liveTwoNode), { status: 200 }),
    );
    render(<HomelabSystemStatsCard />);
    await waitFor(() => expect(screen.getByText("Spirit Dell")).toBeInTheDocument());
    expect(screen.getByText("spiritdesktop")).toBeInTheDocument();
  });

  it("does not show Ghost Node when API does not return it", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(liveTwoNode), { status: 200 }),
    );
    render(<HomelabSystemStatsCard />);
    await waitFor(() => expect(screen.getByText("Spirit Dell")).toBeInTheDocument());
    expect(screen.queryByText(/ghost node/i)).toBeNull();
  });

  it("does not show fake GPU copy", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(liveTwoNode), { status: 200 }),
    );
    render(<HomelabSystemStatsCard />);
    await waitFor(() => expect(screen.getByText("Spirit Dell")).toBeInTheDocument());
    const region = screen.getByRole("region", { name: /system stats/i });
    expect(region.textContent).not.toMatch(/tesla|p40|gpu/i);
  });

  it("shows Unavailable when CPU or RAM usage is null on an online node", async () => {
    const patch: ClusterTelemetryResponse = {
      ...liveTwoNode,
      nodes: [
        {
          ...liveTwoNode.nodes[0]!,
          cpu: { ...liveTwoNode.nodes[0]!.cpu, usagePct: null },
          memory: { ...liveTwoNode.nodes[0]!.memory, usedPct: null },
        },
      ],
    };
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(patch), { status: 200 }),
    );
    render(<HomelabSystemStatsCard />);
    await waitFor(() => expect(screen.getByText("Spirit Dell")).toBeInTheDocument());
    const unavailable = screen.getAllByText("Unavailable");
    expect(unavailable.length).toBeGreaterThanOrEqual(2);
  });

  it("shows offline error line for offline node", async () => {
    const withOffline: ClusterTelemetryResponse = {
      ...liveTwoNode,
      nodes: [
        liveTwoNode.nodes[0]!,
        {
          id: "gone",
          label: "gone-node",
          hostname: null,
          status: "offline",
          source: "remote",
          platform: null,
          arch: null,
          cpu: { model: null, cores: null, usagePct: null, loadAvg: null },
          memory: { totalBytes: null, freeBytes: null, usedBytes: null, usedPct: null },
          uptimeSec: null,
          collectedAt: new Date().toISOString(),
          error: "timeout",
        },
      ],
      summary: { total: 2, online: 1, offline: 1, degraded: 0, unknown: 0 },
    };
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(withOffline), { status: 200 }),
    );
    render(<HomelabSystemStatsCard />);
    await waitFor(() => expect(screen.getByText("gone-node")).toBeInTheDocument());
    expect(screen.getByText("Offline · timeout")).toBeInTheDocument();
  });
});
