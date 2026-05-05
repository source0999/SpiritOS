import { describe, it, expect, vi, afterEach } from "vitest";
import { GET } from "../route";
import type { ClusterTelemetryResponse } from "@/lib/server/telemetry/types";

const { onlineLocal, offlineRemote } = vi.hoisted(() => {
  const now = new Date().toISOString();
  return {
    onlineLocal: {
      id: "spirit-dell",
      label: "Spirit Dell",
      hostname: "source-server",
      status: "online" as const,
      source: "local" as const,
      platform: "linux",
      arch: "x64",
      cpu: { model: "Intel i7-6700", cores: 8, usagePct: 34.1, loadAvg: [0.5, 0.4, 0.3] },
      memory: { totalBytes: 16000000000, freeBytes: 7000000000, usedBytes: 9000000000, usedPct: 56.2 },
      storage: {
        drives: [
          {
            id: "/dev/sda1",
            name: "/ (root)",
            mount: "/",
            fsType: null,
            type: "SSD" as const,
            totalBytes: 500e9,
            usedBytes: 100e9,
            freeBytes: 400e9,
            usedPct: 20,
            tempC: null as null,
            smart: "Unknown" as const,
          },
        ],
        collectedAt: now,
      },
      uptimeSec: 86400,
      collectedAt: now,
    },
    offlineRemote: {
      id: "spiritdesktop",
      label: "spiritdesktop",
      hostname: null as null,
      status: "offline" as const,
      source: "remote" as const,
      telemetryUrl: undefined as undefined,
      platform: null as null,
      arch: null as null,
      cpu: { model: null as null, cores: null as null, usagePct: null as null, loadAvg: null as null },
      memory: { totalBytes: null as null, freeBytes: null as null, usedBytes: null as null, usedPct: null as null },
      uptimeSec: null as null,
      collectedAt: now,
      error: "not configured",
    },
  };
});

vi.mock("@/lib/server/telemetry/collect-local-node", () => ({
  collectLocalNodeTelemetry: vi.fn().mockResolvedValue(onlineLocal),
}));

vi.mock("@/lib/server/telemetry/fetch-remote-node", () => ({
  fetchRemoteNodeTelemetry: vi.fn().mockResolvedValue(offlineRemote),
}));

vi.mock("@/lib/server/telemetry/cluster-config", () => ({
  getClusterConfig: vi.fn().mockReturnValue([
    { id: "spirit-dell", label: "Spirit Dell", source: "local" },
    { id: "spiritdesktop", label: "spiritdesktop", source: "remote", telemetryUrl: undefined },
  ]),
}));

afterEach(() => {
  vi.restoreAllMocks();
});

describe("GET /api/telemetry/cluster", () => {
  it("returns 200 with ClusterTelemetryResponse shape", async () => {
    const res = await GET();
    expect(res.status).toBe(200);
    const json = (await res.json()) as ClusterTelemetryResponse;
    expect(json.nodes).toBeInstanceOf(Array);
    expect(json.summary).toBeDefined();
    expect(typeof json.collectedAt).toBe("string");
  });

  it("returns Cache-Control: no-store", async () => {
    const res = await GET();
    expect(res.headers.get("Cache-Control")).toBe("no-store");
  });

  it("returns correct summary counts", async () => {
    const res = await GET();
    const json = (await res.json()) as ClusterTelemetryResponse;
    expect(json.summary.total).toBe(2);
    expect(json.summary.online).toBe(1);
    expect(json.summary.offline).toBe(1);
  });

  it("online node has real CPU/RAM values", async () => {
    const res = await GET();
    const json = (await res.json()) as ClusterTelemetryResponse;
    const dell = json.nodes.find((n) => n.id === "spirit-dell");
    expect(dell?.cpu.usagePct).toBe(34.1);
    expect(dell?.memory.usedPct).toBe(56.2);
  });

  it("passes storage through on online local node", async () => {
    const res = await GET();
    const json = (await res.json()) as ClusterTelemetryResponse;
    const dell = json.nodes.find((n) => n.id === "spirit-dell");
    expect(dell?.storage?.drives?.length).toBe(1);
    expect(dell?.storage?.drives?.[0]?.id).toBe("/dev/sda1");
  });

  it("offline node has null CPU/RAM", async () => {
    const res = await GET();
    const json = (await res.json()) as ClusterTelemetryResponse;
    const desktop = json.nodes.find((n) => n.id === "spiritdesktop");
    expect(desktop?.status).toBe("offline");
    expect(desktop?.cpu.usagePct).toBeNull();
    expect(desktop?.memory.usedPct).toBeNull();
  });

  it("does not throw when one node collection fails", async () => {
    const { collectLocalNodeTelemetry } = await import("@/lib/server/telemetry/collect-local-node");
    vi.mocked(collectLocalNodeTelemetry).mockRejectedValueOnce(new Error("collector crash"));
    const res = await GET();
    expect(res.status).toBe(200);
    const json = (await res.json()) as ClusterTelemetryResponse;
    const dell = json.nodes.find((n) => n.id === "spirit-dell");
    expect(dell?.status).toBe("offline");
  });
});
