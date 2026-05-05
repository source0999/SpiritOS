import { describe, it, expect, vi, afterEach } from "vitest";
import { collectLocalNodeTelemetry } from "../collect-local-node";

afterEach(() => {
  vi.restoreAllMocks();
  delete process.env.SPIRIT_CLUSTER_LOCAL_ID;
  delete process.env.SPIRIT_CLUSTER_LOCAL_LABEL;
});

describe("collectLocalNodeTelemetry", () => {
  it("returns the required shape", async () => {
    const result = await collectLocalNodeTelemetry();
    expect(result).toMatchObject({
      id: expect.any(String),
      label: expect.any(String),
      status: "online",
      source: "local",
      collectedAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
    });
  });

  it("uses id/label from options when provided", async () => {
    const result = await collectLocalNodeTelemetry({ id: "test-node", label: "Test Node" });
    expect(result.id).toBe("test-node");
    expect(result.label).toBe("Test Node");
  });

  it("falls back to env vars for id and label", async () => {
    process.env.SPIRIT_CLUSTER_LOCAL_ID = "env-node";
    process.env.SPIRIT_CLUSTER_LOCAL_LABEL = "Env Node";
    const result = await collectLocalNodeTelemetry();
    expect(result.id).toBe("env-node");
    expect(result.label).toBe("Env Node");
  });

  it("cpu.usagePct is null or clamped between 0 and 100", async () => {
    const result = await collectLocalNodeTelemetry();
    if (result.cpu.usagePct !== null) {
      expect(result.cpu.usagePct).toBeGreaterThanOrEqual(0);
      expect(result.cpu.usagePct).toBeLessThanOrEqual(100);
    }
  });

  it("memory.usedPct is null or clamped between 0 and 100", async () => {
    const result = await collectLocalNodeTelemetry();
    if (result.memory.usedPct !== null) {
      expect(result.memory.usedPct).toBeGreaterThanOrEqual(0);
      expect(result.memory.usedPct).toBeLessThanOrEqual(100);
    }
  });

  it("memory totals are consistent", async () => {
    const result = await collectLocalNodeTelemetry();
    const { totalBytes, freeBytes, usedBytes } = result.memory;
    if (totalBytes !== null && freeBytes !== null && usedBytes !== null) {
      expect(usedBytes).toBe(totalBytes - freeBytes);
      expect(totalBytes).toBeGreaterThan(0);
    }
  });

  it("uptimeSec is a non-negative integer", async () => {
    const result = await collectLocalNodeTelemetry();
    expect(result.uptimeSec).not.toBeNull();
    expect(result.uptimeSec).toBeGreaterThanOrEqual(0);
    expect(Number.isInteger(result.uptimeSec)).toBe(true);
  });

  it("cpu.cores is a positive integer", async () => {
    const result = await collectLocalNodeTelemetry();
    expect(result.cpu.cores).not.toBeNull();
    expect(result.cpu.cores).toBeGreaterThan(0);
  });

  it("platform and arch are non-empty strings", async () => {
    const result = await collectLocalNodeTelemetry();
    expect(typeof result.platform).toBe("string");
    expect(typeof result.arch).toBe("string");
    expect((result.platform ?? "").length).toBeGreaterThan(0);
    expect((result.arch ?? "").length).toBeGreaterThan(0);
  });

  it("returns null usagePct when os.cpus throws", async () => {
    const os = await import("node:os");
    vi.spyOn(os.default, "cpus").mockImplementation(() => {
      throw new Error("cpus unavailable");
    });
    const result = await collectLocalNodeTelemetry();
    expect(result.cpu.usagePct).toBeNull();
  });

  it("returns storage with drives array on local node", async () => {
    const result = await collectLocalNodeTelemetry();
    expect(result.storage).toBeDefined();
    expect(Array.isArray(result.storage?.drives)).toBe(true);
  });
});
