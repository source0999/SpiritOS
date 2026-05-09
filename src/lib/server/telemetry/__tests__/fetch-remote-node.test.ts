import { describe, it, expect, vi, afterEach } from "vitest";
import { fetchRemoteNodeTelemetry } from "../fetch-remote-node";
import type { ClusterNodeTelemetry } from "../types";

const origFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = origFetch;
  delete process.env.SPIRIT_TELEMETRY_TOKEN;
  vi.restoreAllMocks();
});

const validNode: ClusterNodeTelemetry = {
  id: "spiritdesktop",
  label: "spiritdesktop",
  hostname: "spiritdesktop",
  status: "online",
  source: "local",
  platform: "linux",
  arch: "x64",
  cpu: { model: "AMD Ryzen", cores: 12, usagePct: 15, loadAvg: [0.5, 0.4, 0.3] },
  memory: { totalBytes: 16000, freeBytes: 8000, usedBytes: 8000, usedPct: 50 },
  uptimeSec: 86400,
  collectedAt: new Date().toISOString(),
};

function authHeaderFromTelemetryFetch(mockFetch: ReturnType<typeof vi.fn>): string | null {
  expect(mockFetch.mock.calls.length).toBeGreaterThan(0);
  const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
  const headers = new Headers(init?.headers as HeadersInit);
  return headers.get("Authorization");
}

describe("fetchRemoteNodeTelemetry", () => {
  it("returns offline with 'not configured' when telemetryUrl is undefined", async () => {
    const result = await fetchRemoteNodeTelemetry("spiritdesktop", "spiritdesktop", undefined);
    expect(result.status).toBe("offline");
    expect(result.error).toBe("not configured");
    expect(result.cpu.usagePct).toBeNull();
    expect(result.memory.usedPct).toBeNull();
  });

  it("returns data from a successful fetch", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(validNode), { status: 200 }),
    );
    const result = await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://spiritdesktop:3000/api/telemetry/self",
    );
    expect(result.status).toBe("online");
    expect(result.source).toBe("remote");
    expect(result.cpu.usagePct).toBe(15);
  });

  it("returns offline on non-2xx response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response("Internal Server Error", { status: 500 }),
    );
    const result = await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://spiritdesktop:3000/api/telemetry/self",
    );
    expect(result.status).toBe("offline");
    expect(result.error).toContain("500");
    expect(result.cpu.usagePct).toBeNull();
  });

  it("returns offline with 'unreachable' on network error", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));
    const result = await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://spiritdesktop:3000/api/telemetry/self",
    );
    expect(result.status).toBe("offline");
    expect(result.error).toBe("unreachable");
    expect(result.cpu.usagePct).toBeNull();
  });

  it("returns offline with 'timeout' on AbortError", async () => {
    const abortError = new Error("abort");
    abortError.name = "AbortError";
    globalThis.fetch = vi.fn().mockRejectedValue(abortError);
    const result = await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://spiritdesktop:3000/api/telemetry/self",
    );
    expect(result.status).toBe("offline");
    expect(result.error).toBe("timeout");
  });

  it("returns offline with field-level detail when response lacks required fields", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ foo: "bar" }), { status: 200 }),
    );
    const result = await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://spiritdesktop:3000/api/telemetry/self",
    );
    expect(result.status).toBe("offline");
    expect(result.error).toBe("invalid response: missing id, status, collectedAt");
  });

  it("rejects legacy Windows agent shape with explicit missing keys", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          cpuUsage: 1,
          ramUsage: 2,
          uptime: 3,
          hostname: "pc",
          platform: "win32",
        }),
        { status: 200 },
      ),
    );
    const result = await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://spiritdesktop:3000/api/telemetry/self",
    );
    expect(result.status).toBe("offline");
    expect(result.error).toBe("invalid response: missing id, status, collectedAt");
  });

  it("preserves storage.drives from remote ClusterNodeTelemetry JSON", async () => {
    const withStorage = {
      id: "spiritdesktop",
      label: "spiritdesktop",
      hostname: "Spirit",
      status: "online",
      source: "remote",
      platform: "win32",
      arch: "x64",
      cpu: { model: "AMD", cores: 12, usagePct: 10, loadAvg: null },
      memory: {
        totalBytes: 16_000_000_000,
        freeBytes: 8_000_000_000,
        usedBytes: 8_000_000_000,
        usedPct: 50,
      },
      storage: {
        drives: [
          {
            id: "C:",
            name: "C:",
            mount: "C:",
            fsType: "NTFS",
            type: "UNKNOWN",
            totalBytes: 500e9,
            usedBytes: 200e9,
            freeBytes: 300e9,
            usedPct: 40,
            tempC: null,
            smart: "Unknown",
          },
        ],
        collectedAt: new Date().toISOString(),
      },
      uptimeSec: 100,
      collectedAt: new Date().toISOString(),
    };
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(withStorage), { status: 200 }),
    );
    const result = await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://10.0.0.126:3000/api/telemetry/self",
    );
    expect(result.storage?.drives?.length).toBe(1);
    expect(result.storage?.drives?.[0]?.id).toBe("C:");
  });

  it("accepts Windows-agent-compatible ClusterNodeTelemetry JSON", async () => {
    const windowsLike = {
      id: "spiritdesktop",
      label: "spiritdesktop",
      hostname: "DESKTOP-ABC",
      status: "online",
      source: "remote",
      platform: "win32",
      arch: "x64",
      cpu: {
        model: "Intel Something",
        cores: 8,
        usagePct: 12.3,
        loadAvg: null,
      },
      memory: {
        totalBytes: 16_000_000_000,
        freeBytes: 8_000_000_000,
        usedBytes: 8_000_000_000,
        usedPct: 50,
      },
      uptimeSec: 3600,
      collectedAt: new Date().toISOString(),
    };
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(windowsLike), { status: 200 }),
    );
    const result = await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://10.0.0.50:3000/api/telemetry/self",
    );
    expect(result.status).toBe("online");
    expect(result.source).toBe("remote");
    expect(result.telemetryUrl).toBe("http://10.0.0.50:3000/api/telemetry/self");
    expect(result.cpu.cores).toBe(8);
    expect(result.memory.usedPct).toBe(50);
  });

  it("sends default Authorization (3399) when SPIRIT_TELEMETRY_TOKEN is unset", async () => {
    delete process.env.SPIRIT_TELEMETRY_TOKEN;
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(validNode), { status: 200 }),
    );
    globalThis.fetch = mockFetch;
    await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://spiritdesktop:3000/api/telemetry/self",
    );
    expect(authHeaderFromTelemetryFetch(mockFetch)).toBe("Bearer 3399");
  });

  it("sends Authorization header when SPIRIT_TELEMETRY_TOKEN is set", async () => {
    process.env.SPIRIT_TELEMETRY_TOKEN = "test-secret";
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(validNode), { status: 200 }),
    );
    globalThis.fetch = mockFetch;
    await fetchRemoteNodeTelemetry(
      "spiritdesktop",
      "spiritdesktop",
      "http://spiritdesktop:3000/api/telemetry/self",
    );
    expect(authHeaderFromTelemetryFetch(mockFetch)).toBe("Bearer test-secret");
  });
});
