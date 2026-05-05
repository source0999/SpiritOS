import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getCapabilityRegistry, isSpiritProjectPathConfigured } from "../get-capabilities";
import type { ClusterNodeTelemetry } from "@/lib/server/telemetry/types";

const { collectClusterNodes, getClusterConfig } = vi.hoisted(() => ({
  collectClusterNodes: vi.fn(),
  getClusterConfig: vi.fn(),
}));

vi.mock("@/lib/server/telemetry/collect-cluster-nodes", () => ({
  collectClusterNodes,
}));

vi.mock("@/lib/server/telemetry/cluster-config", () => ({
  getClusterConfig,
}));

describe("isSpiritProjectPathConfigured", () => {
  it("is false for empty/undefined", () => {
    expect(isSpiritProjectPathConfigured(undefined)).toBe(false);
    expect(isSpiritProjectPathConfigured("")).toBe(false);
    expect(isSpiritProjectPathConfigured("  ,  , ")).toBe(false);
  });

  it("is true when at least one comma-separated path is non-empty", () => {
    expect(isSpiritProjectPathConfigured("/a/b")).toBe(true);
    expect(isSpiritProjectPathConfigured(" /x , ")).toBe(true);
  });
});

describe("getCapabilityRegistry", () => {
  const now = "2026-05-04T12:00:00.000Z";

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(now));
    vi.stubEnv("SPIRIT_PROJECT_PATH", "");
    vi.stubEnv("SPIRIT_TELEMETRY_TOKEN", "super-secret-do-not-leak");
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it("builds nodes from mocked cluster config without hardcoded homelab names", async () => {
    const n1: ClusterNodeTelemetry = {
      id: "alpha-workstation",
      label: "Alpha",
      hostname: "alpha",
      status: "online",
      source: "local",
      platform: "linux",
      arch: "x64",
      cpu: { model: "x", cores: 4, usagePct: 1, loadAvg: [0, 0, 0] },
      memory: { totalBytes: 1, freeBytes: 1, usedBytes: 0, usedPct: 0 },
      uptimeSec: 1,
      collectedAt: now,
    };
    const n2: ClusterNodeTelemetry = {
      id: "beta-remote",
      label: "Beta",
      hostname: null,
      status: "offline",
      source: "remote",
      telemetryUrl: "http://10.0.0.1:3000/api/telemetry/self",
      platform: null,
      arch: null,
      cpu: { model: null, cores: null, usagePct: null, loadAvg: null },
      memory: { totalBytes: null, freeBytes: null, usedBytes: null, usedPct: null },
      uptimeSec: null,
      collectedAt: now,
      error: "timeout",
    };

    getClusterConfig.mockReturnValue([
      { id: "alpha-workstation", label: "Alpha", source: "local" },
      { id: "beta-remote", label: "Beta", source: "remote", telemetryUrl: "http://10.0.0.1:3000/api/telemetry/self" },
    ]);
    collectClusterNodes.mockResolvedValue([n1, n2]);

    const reg = await getCapabilityRegistry();

    expect(reg.host).toEqual({ id: "alpha-workstation", label: "Alpha", source: "local" });
    expect(reg.nodes.map((x) => x.id)).toEqual(["alpha-workstation", "beta-remote"]);

    const offline = reg.nodes.find((x) => x.id === "beta-remote")!;
    expect(offline.status).toBe("offline");
    expect(offline.capabilities.telemetry.enabled).toBe(false);
    expect(offline.capabilities.remoteControl.live).toBe(false);

    const online = reg.nodes.find((x) => x.id === "alpha-workstation")!;
    expect(online.capabilities.telemetry.enabled).toBe(true);
    expect(online.capabilities.remoteControl.live).toBe(true);
    expect(online.capabilities.ssh.enabled).toBe(false);
    expect(online.capabilities.ssh.status).toBe("unverified");
  });

  it("marks storageTelemetry when drives exist on a live node", async () => {
    const n: ClusterNodeTelemetry = {
      id: "gamma",
      label: "Gamma",
      hostname: "g",
      status: "online",
      source: "local",
      platform: "linux",
      arch: "x64",
      cpu: { model: "x", cores: 2, usagePct: 1, loadAvg: null },
      memory: { totalBytes: 1, freeBytes: 1, usedBytes: 0, usedPct: 0 },
      storage: { drives: [], collectedAt: now },
      uptimeSec: 1,
      collectedAt: now,
    };
    getClusterConfig.mockReturnValue([{ id: "gamma", label: "Gamma", source: "local" }]);
    collectClusterNodes.mockResolvedValue([n]);
    const emptyDrives = await getCapabilityRegistry();
    expect(emptyDrives.nodes[0]!.capabilities.storageTelemetry.enabled).toBe(false);

    const withDrive: ClusterNodeTelemetry = {
      ...n,
      storage: {
        drives: [
          {
            id: "/dev/sda1",
            name: "root",
            mount: "/",
            fsType: "ext4",
            type: "SSD",
            totalBytes: 1,
            usedBytes: 0,
            freeBytes: 1,
            usedPct: 0,
            tempC: null,
            smart: "Unknown",
          },
        ],
        collectedAt: now,
      },
    };
    collectClusterNodes.mockResolvedValue([withDrive]);
    const withStorage = await getCapabilityRegistry();
    expect(withStorage.nodes[0]!.capabilities.storageTelemetry.enabled).toBe(true);
  });

  it("reports SPIRIT_PROJECT_PATH configured without filesystem access", async () => {
    vi.stubEnv("SPIRIT_PROJECT_PATH", "/mnt/projects/a,/mnt/projects/b");
    getClusterConfig.mockReturnValue([{ id: "gamma", label: "Gamma", source: "local" }]);
    collectClusterNodes.mockResolvedValue([
      {
        id: "gamma",
        label: "Gamma",
        hostname: "g",
        status: "online",
        source: "local",
        platform: "linux",
        arch: "x64",
        cpu: { model: "x", cores: 2, usagePct: 1, loadAvg: null },
        memory: { totalBytes: 1, freeBytes: 1, usedBytes: 0, usedPct: 0 },
        uptimeSec: 1,
        collectedAt: now,
      },
    ]);
    const reg = await getCapabilityRegistry();
    expect(reg.nodes[0]!.capabilities.projects.configured).toBe(true);
    expect(reg.nodes[0]!.capabilities.projects.enabled).toBe(false);
  });

  it("does not expose telemetry token in serialized output", async () => {
    getClusterConfig.mockReturnValue([{ id: "gamma", label: "Gamma", source: "local" }]);
    collectClusterNodes.mockResolvedValue([
      {
        id: "gamma",
        label: "Gamma",
        hostname: "g",
        status: "online",
        source: "local",
        platform: "linux",
        arch: "x64",
        cpu: { model: "x", cores: 2, usagePct: 1, loadAvg: null },
        memory: { totalBytes: 1, freeBytes: 1, usedBytes: 0, usedPct: 0 },
        uptimeSec: 1,
        collectedAt: now,
      },
    ]);
    const reg = await getCapabilityRegistry();
    const json = JSON.stringify(reg);
    expect(json).not.toContain("super-secret");
    expect(json).not.toContain("SPIRIT_TELEMETRY_TOKEN");
  });
});
