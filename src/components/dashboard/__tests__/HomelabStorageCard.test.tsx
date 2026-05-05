import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { HomelabStorageCard } from "../HomelabStorageCard";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";

const origFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = origFetch;
  vi.useRealTimers();
  vi.restoreAllMocks();
});

const driveFromApi = {
  id: "/dev/nvme0n1p2",
  name: "TEST_CLUSTER_DRIVE_ZZ9",
  mount: "/",
  fsType: "ext4",
  type: "NVME" as const,
  totalBytes: 500e9,
  usedBytes: 250e9,
  freeBytes: 250e9,
  usedPct: 50,
  tempC: null as number | null,
  smart: "Unknown" as const,
};

const withStorage: ClusterTelemetryResponse = {
  ok: true,
  collectedAt: new Date().toISOString(),
  nodes: [
    {
      id: "spirit-dell",
      label: "Spirit Dell",
      hostname: "srv",
      status: "online",
      source: "local",
      platform: "linux",
      arch: "x64",
      cpu: { model: "x", cores: 4, usagePct: 1, loadAvg: null },
      memory: { totalBytes: 8e9, freeBytes: 4e9, usedBytes: 4e9, usedPct: 50 },
      storage: { drives: [driveFromApi], collectedAt: new Date().toISOString() },
      uptimeSec: 1,
      collectedAt: new Date().toISOString(),
    },
  ],
  summary: { total: 1, online: 1, offline: 0, degraded: 0, unknown: 0 },
};

describe("HomelabStorageCard", () => {
  it("renders drive name from API", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(withStorage), { status: 200 }),
    );
    render(<HomelabStorageCard />);
    await waitFor(() =>
      expect(screen.getByText("TEST_CLUSTER_DRIVE_ZZ9")).toBeInTheDocument(),
    );
  });

  it("does not render legacy mock drive names unless present in API", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(withStorage), { status: 200 }),
    );
    render(<HomelabStorageCard />);
    await waitFor(() => expect(screen.getByText("Spirit Dell")).toBeInTheDocument());
    expect(screen.queryByText(/Samsung 980 Pro/i)).toBeNull();
    expect(screen.queryByText(/Media Vault/i)).toBeNull();
    expect(screen.queryByText(/^Archive$/i)).toBeNull();
  });

  it("shows Storage telemetry unavailable when drives list is empty", async () => {
    const empty: ClusterTelemetryResponse = {
      ...withStorage,
      nodes: [
        {
          ...withStorage.nodes[0]!,
          storage: { drives: [], collectedAt: new Date().toISOString() },
        },
      ],
    };
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(empty), { status: 200 }),
    );
    render(<HomelabStorageCard />);
    await waitFor(() =>
      expect(screen.getByText("Storage telemetry unavailable")).toBeInTheDocument(),
    );
  });

  it("shows storage error when node.storage.error is set", async () => {
    const err: ClusterTelemetryResponse = {
      ...withStorage,
      nodes: [
        {
          ...withStorage.nodes[0]!,
          storage: {
            drives: [],
            collectedAt: new Date().toISOString(),
            error: "df exploded",
          },
        },
      ],
    };
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(err), { status: 200 }),
    );
    render(<HomelabStorageCard />);
    await waitFor(() => expect(screen.getByText("df exploded")).toBeInTheDocument());
  });

  it("shows offline state for offline node (no fake drives)", async () => {
    const offline: ClusterTelemetryResponse = {
      ok: true,
      collectedAt: new Date().toISOString(),
      nodes: [
        {
          id: "n",
          label: "dead-node",
          hostname: null,
          status: "offline",
          source: "remote",
          platform: null,
          arch: null,
          cpu: { model: null, cores: null, usagePct: null, loadAvg: null },
          memory: { totalBytes: null, freeBytes: null, usedBytes: null, usedPct: null },
          uptimeSec: null,
          collectedAt: new Date().toISOString(),
          error: "not configured",
        },
      ],
      summary: { total: 1, online: 0, offline: 1, degraded: 0, unknown: 0 },
    };
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(offline), { status: 200 }),
    );
    render(<HomelabStorageCard />);
    await waitFor(() => expect(screen.getByText("dead-node")).toBeInTheDocument());
    expect(screen.getByText("Offline · not configured")).toBeInTheDocument();
    expect(screen.queryByText("TEST_CLUSTER_DRIVE_ZZ9")).toBeNull();
  });
});
