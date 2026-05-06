import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { streamText } from "ai";

import { POST } from "../route";
import type { CapabilityRegistryResponse } from "@/lib/server/capabilities/types";

vi.mock("@/lib/server/capabilities/get-capabilities", () => ({
  getCapabilityRegistry: vi.fn(),
}));

vi.mock("@/lib/server/ollama", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/server/ollama")>();
  return {
    ...actual,
    probeOllamaOpenAICompat: vi.fn().mockResolvedValue({ ok: true, status: "online" }),
  };
});

vi.mock("@/lib/server/spirit-diagnostics", () => ({
  getSpiritDiagnostics: vi.fn(() => ({
    engine: "Ollama",
    maxOutputTokens: 1024,
    maxOutputTokensSource: "default",
    oracleMaxOutputTokens: 768,
    oracleMaxOutputTokensSource: "test",
    chatModel: "chat-model-from-mock",
    oracleLaneModel: "oracle-model-from-mock",
    context: { label: "Host default", source: "unset" },
    tts: { provider: "Piper", voice: "fable", source: "mock" },
    stt: {
      provider: "Whisper",
      url: "http://localhost:8000",
      source: "mock",
      transcribePath: "/v1/audio/transcriptions",
    },
  })),
  getSpiritMaxOutputTokens: () => 1024,
  getOracleMaxOutputTokens: () => 768,
}));

vi.mock("ai", async (importOriginal) => {
  const actual = await importOriginal<typeof import("ai")>();
  return {
    ...actual,
    streamText: vi.fn(() => ({
      toUIMessageStreamResponse: vi.fn(() => new Response("mock-stream", { status: 200 })),
    })),
  };
});

function capabilityRegistry(label: string): CapabilityRegistryResponse {
  return {
    ok: true,
    collectedAt: "2026-05-04T12:00:00.000Z",
    host: { id: "local-host", label: "Local Host", source: "local" },
    nodes: [
      {
        id: "n-api-test",
        label,
        status: "online",
        source: "local",
        platform: "linux",
        capabilities: {
          telemetry: { enabled: true, readOnly: true },
          storageTelemetry: { enabled: false, readOnly: true },
          projects: { enabled: false, configured: false, readOnly: true },
          ssh: { enabled: false, status: "unverified", requiresApproval: true },
          remoteControl: { live: true, requiresApproval: true },
        },
        telemetrySnapshot: {
          cpu: { model: "Mock CPU", cores: 4, usagePct: 10, loadAvg: null },
          memory: {
            totalBytes: 8e9,
            freeBytes: 4e9,
            usedBytes: 4e9,
            usedPct: 50,
          },
          uptimeSec: 100,
          storage: {
            drives: [
              {
                id: "c",
                name: "C:",
                mount: "C:",
                fsType: "NTFS",
                type: "SSD",
                totalBytes: 500e9,
                usedBytes: 100e9,
                freeBytes: 400e9,
                usedPct: 20,
                tempC: null,
                smart: "Healthy",
              },
            ],
            collectedAt: "2026-05-04T12:00:00.000Z",
          },
        },
      },
    ],
    tools: [
      { name: "get_capabilities", enabled: true, readOnly: true, requiresApproval: false },
      { name: "list_nodes", enabled: true, readOnly: true, requiresApproval: false },
      { name: "get_node_status", enabled: true, readOnly: true, requiresApproval: false },
    ],
  };
}

function jsonBody(overrides: Record<string, unknown> = {}) {
  return {
    messages: [
      {
        role: "user",
        id: "u1",
        parts: [{ type: "text", text: "What hardware can you see right now?" }],
      },
    ],
    modelProfileId: "normal-peer",
    runtimeSurface: "chat",
    deepThinkEnabled: false,
    webSearchOptOut: false,
    teacherWebSearchEnabled: true,
    ...overrides,
  };
}

describe("POST /api/spirit capability bridge", () => {
  beforeEach(async () => {
    vi.stubEnv("WEB_SEARCH_ENABLED", "false");
    const { getCapabilityRegistry } = await import("@/lib/server/capabilities/get-capabilities");
    vi.mocked(getCapabilityRegistry).mockResolvedValue(
      capabilityRegistry("SPIRIT_ROUTE_TEST_NODE"),
    );
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it("hardware question returns concise summary with node label", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(jsonBody()),
    });
    const res = await POST(req);
    expect(res.ok).toBe(true);
    const raw = await res.text();
    expect(raw).toContain("SPIRIT_ROUTE_TEST_NODE");
    expect(raw).not.toMatch(/Here is what SpiritOS can see right now/i);
  });

  it("see C drive returns storage telemetry yes, not file-access denial", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u1",
              parts: [{ type: "text", text: "can you see my C drive?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    const raw = await res.text();
    expect(raw.toLowerCase()).toMatch(/yes|can see|storage telemetry|drive-level/i);
    expect(raw).not.toMatch(/^No - not yet/i);
    expect(raw).not.toContain("Mock CPU");
  });

  it("file question does not dump CPU/RAM", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u1",
              parts: [{ type: "text", text: "Can you browse or list my C drive yet?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    const raw = await res.text();
    expect(raw).toMatch(/not (yet|wired)/i);
    expect(raw.toLowerCase()).toMatch(/drive-level|telemetry|storage/);
    expect(raw).not.toContain("Mock CPU");
    expect(raw).not.toContain("uptime");
  });

  it("tool question mentions registry tools and file limits", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u1",
              parts: [{ type: "text", text: "What tools do you have?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    const raw = await res.text();
    expect(raw).toContain("get_capabilities");
    expect(raw).toMatch(/filesystem|files/i);
  });

  it("Oracle see C drive is concise storage yes", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          runtimeSurface: "oracle",
          messages: [
            {
              role: "user",
              id: "u-oracle-c",
              parts: [{ type: "text", text: "can you see my C drive?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    expect(res.headers.get("x-spirit-runtime-surface")).toBe("oracle");
    const raw = await res.text();
    expect(raw.length).toBeLessThan(500);
    expect(raw.toLowerCase()).toMatch(/storage telemetry|telemetry/);
    expect(raw).toMatch(/browse|list files|folders/i);
  });

  it("Oracle SSH reply mentions no in-app tool", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          runtimeSurface: "oracle",
          messages: [
            {
              role: "user",
              id: "u-oracle-ssh",
              parts: [{ type: "text", text: "can you ssh into my desktop?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    const raw = await res.text();
    expect(raw.length).toBeLessThan(900);
    expect(raw).toMatch(/SSH/i);
    expect(raw).toMatch(/not|yet|no|don’t|don't/i);
  });

  it("Oracle voice keeps capability reply short", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          runtimeSurface: "oracle",
          messages: [
            {
              role: "user",
              id: "u2",
              parts: [{ type: "text", text: "What hardware can you see?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    expect(res.headers.get("x-spirit-runtime-surface")).toBe("oracle");
    const raw = await res.text();
    const sentences = raw.split(/(?<=[.!?])\s+/).filter(Boolean);
    expect(sentences.length).toBeLessThanOrEqual(4);
  });

  it("ai_runtime surfaces model ids and calls probe", async () => {
    const { probeOllamaOpenAICompat } = await import("@/lib/server/ollama");
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u3",
              parts: [{ type: "text", text: "Are you running Hermes?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    const raw = await res.text();
    expect(raw).toContain("chat-model-from-mock");
    expect(vi.mocked(probeOllamaOpenAICompat)).toHaveBeenCalled();
  });

  it("typo capabilities question returns live overview, not LLM bypass", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u1",
              parts: [{ type: "text", text: "what are your capabilites?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    const raw = await res.text();
    expect(raw).toContain("get_capabilities");
    expect(raw).toContain("SPIRIT_ROUTE_TEST_NODE");
    expect(raw).not.toMatch(/project workspace/i);
  });

  it("correct spelling capabilities returns deterministic overview", async () => {
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u1",
              parts: [{ type: "text", text: "what are your capabilities?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    const raw = await res.text();
    expect(raw).toMatch(/live/i);
    expect(raw).toContain("list_nodes");
  });
});

describe("POST /api/spirit streamText tools wiring", () => {
  beforeEach(async () => {
    vi.stubEnv("WEB_SEARCH_ENABLED", "false");
    const { getCapabilityRegistry } = await import("@/lib/server/capabilities/get-capabilities");
    vi.mocked(getCapabilityRegistry).mockResolvedValue(
      capabilityRegistry("SPIRIT_ROUTE_TEST_NODE"),
    );
    vi.mocked(streamText).mockClear();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  function chatBody() {
    return jsonBody({
      messages: [
        {
          role: "user",
          id: "u-tools",
          parts: [{ type: "text", text: "Hello friend, please respond briefly." }],
        },
      ],
    });
  }

  it("does not attach tools when SPIRIT_ENABLE_LOCAL_TOOLS is false", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "false");
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(chatBody()),
    });
    await POST(req);
    const opts = vi.mocked(streamText).mock.calls[0]?.[0] as {
      tools?: unknown;
      stopWhen?: unknown;
    };
    expect(opts?.tools).toBeUndefined();
    expect(opts?.stopWhen).toBeUndefined();
  });

  it("attaches tools and stopWhen when SPIRIT_ENABLE_LOCAL_TOOLS is true", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(chatBody()),
    });
    await POST(req);
    const opts = vi.mocked(streamText).mock.calls[0]?.[0] as {
      tools?: Record<string, unknown>;
      stopWhen?: unknown;
    };
    expect(opts?.tools).toBeDefined();
    expect(Object.keys(opts!.tools!)).toHaveLength(4);
    expect(opts?.stopWhen).toBeDefined();
  });
});
