import { describe, it, expect, vi, afterEach } from "vitest";
import { GET } from "../route";

vi.mock("@/lib/server/telemetry/collect-local-node", () => ({
  collectLocalNodeTelemetry: vi.fn().mockResolvedValue({
    id: "spirit-dell",
    label: "Spirit Dell",
    hostname: "source-server",
    status: "online",
    source: "local",
    platform: "linux",
    arch: "x64",
    cpu: { model: "Intel i7-6700", cores: 8, usagePct: 12.3, loadAvg: [0.1, 0.2, 0.3] },
    memory: { totalBytes: 16000000000, freeBytes: 8000000000, usedBytes: 8000000000, usedPct: 50 },
    uptimeSec: 100000,
    collectedAt: new Date().toISOString(),
  }),
}));

afterEach(() => {
  delete process.env.SPIRIT_TELEMETRY_TOKEN;
  vi.restoreAllMocks();
});

describe("GET /api/telemetry/self", () => {
  it("returns 200 with node telemetry", async () => {
    const req = new Request("http://localhost/api/telemetry/self");
    const res = await GET(req);
    expect(res.status).toBe(200);
    const json = await res.json() as Record<string, unknown>;
    expect(json.status).toBe("online");
    expect(json.source).toBe("local");
    expect(json.cpu).toBeDefined();
    expect(json.memory).toBeDefined();
  });

  it("returns Cache-Control: no-store", async () => {
    const req = new Request("http://localhost/api/telemetry/self");
    const res = await GET(req);
    expect(res.headers.get("Cache-Control")).toBe("no-store");
  });

  it("returns 401 when token is set and Authorization header is missing", async () => {
    process.env.SPIRIT_TELEMETRY_TOKEN = "secret";
    const req = new Request("http://localhost/api/telemetry/self");
    const res = await GET(req);
    expect(res.status).toBe(401);
  });

  it("returns 200 when correct token is provided", async () => {
    process.env.SPIRIT_TELEMETRY_TOKEN = "secret";
    const req = new Request("http://localhost/api/telemetry/self", {
      headers: { Authorization: "Bearer secret" },
    });
    const res = await GET(req);
    expect(res.status).toBe(200);
  });

  it("returns 200 (no token check) when SPIRIT_TELEMETRY_TOKEN is blank", async () => {
    process.env.SPIRIT_TELEMETRY_TOKEN = "";
    const req = new Request("http://localhost/api/telemetry/self");
    const res = await GET(req);
    expect(res.status).toBe(200);
  });
});
