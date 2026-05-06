import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { streamText } from "ai";

import { detectCapabilityIntent } from "@/lib/spirit/capability-intent";

import { POST } from "../route";
import type { CapabilityRegistryResponse } from "@/lib/server/capabilities/types";
import { clearReadOnlyToolProbeCache } from "@/lib/spirit/tools/tool-registry";

vi.mock("@/lib/server/capabilities/get-capabilities", () => ({
  getCapabilityRegistry: vi.fn(),
}));

vi.mock("@/lib/server/ollama", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/server/ollama")>();
  return {
    ...actual,
    probeOllamaOpenAICompat: vi.fn().mockResolvedValue({ ok: true, status: "online" }),
    probeOllamaChatCompletionsAcceptsToolSchema: vi.fn().mockResolvedValue(true),
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
    const { probeOllamaChatCompletionsAcceptsToolSchema } = await import("@/lib/server/ollama");
    vi.mocked(probeOllamaChatCompletionsAcceptsToolSchema).mockResolvedValue(true);
    clearReadOnlyToolProbeCache();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
    clearReadOnlyToolProbeCache();
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
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
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

  it("attaches tools and stopWhen when local + Ollama tool transport flags are true", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
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

  it("does not attach tools when local tools on but Ollama tools transport off", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
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

  it("concrete workspace list when tool probe rejects returns direct listing (no streamText)", async () => {
    const { probeOllamaChatCompletionsAcceptsToolSchema } = await import("@/lib/server/ollama");
    vi.mocked(probeOllamaChatCompletionsAcceptsToolSchema).mockResolvedValue(false);
    clearReadOnlyToolProbeCache();
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.mocked(streamText).mockClear();
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u-probe-fail",
              parts: [{ type: "text", text: "List the files in src/lib/spirit" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    expect(vi.mocked(streamText)).not.toHaveBeenCalled();
    const raw = await res.text();
    expect(raw).toMatch(/Files in src\/lib\/spirit/i);
    expect(raw).toContain("- ");
    expect(raw).not.toMatch(/tool-call support probe/i);
  });

  it("skips deterministic file_access bridge when local tools enabled (falls through to LLM)", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.mocked(streamText).mockClear();
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u-file-local",
              parts: [
                {
                  type: "text",
                  text: "List the files in src/lib/spirit",
                },
              ],
            },
          ],
        }),
      ),
    });
    await POST(req);
    expect(vi.mocked(streamText)).toHaveBeenCalled();
    const opts = vi.mocked(streamText).mock.calls[0]?.[0] as {
      tools?: Record<string, unknown>;
    };
    expect(opts?.tools).toBeDefined();
    expect(Object.keys(opts!.tools!)).toHaveLength(4);
  });

  it("concrete workspace list with local tools off uses deterministic shortcut (no streamText)", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "false");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
    vi.mocked(streamText).mockClear();
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u-list-off",
              parts: [{ type: "text", text: "List the files in src/lib/spirit" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    expect(vi.mocked(streamText)).not.toHaveBeenCalled();
    const raw = await res.text();
    expect(raw).toMatch(/not wired|drive-level|telemetry/i);
  });

  it("concrete workspace list with local on but Ollama tools transport off uses direct listing (no streamText)", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
    vi.mocked(streamText).mockClear();
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u-list-ollama-off",
              parts: [{ type: "text", text: "List the files in src/lib/spirit" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    expect(vi.mocked(streamText)).not.toHaveBeenCalled();
    const raw = await res.text();
    expect(raw).toMatch(/Files in src\/lib\/spirit/i);
    expect(raw).not.toContain("SPIRIT_OLLAMA_SUPPORTS_TOOLS");
  });

  it("vague browse question with both flags on still uses deterministic shortcut", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.mocked(streamText).mockClear();
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u-browse-vague",
              parts: [{ type: "text", text: "Can you browse files?" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    expect(vi.mocked(streamText)).not.toHaveBeenCalled();
    const raw = await res.text();
    expect(raw).toMatch(/not wired|deterministic/i);
    expect(raw).not.toContain("will not attach OpenAI-style tool calls");
  });

  it("concrete read .env.local when probe rejects returns safe blocked-path error (no streamText)", async () => {
    const { probeOllamaChatCompletionsAcceptsToolSchema } = await import("@/lib/server/ollama");
    vi.mocked(probeOllamaChatCompletionsAcceptsToolSchema).mockResolvedValue(false);
    clearReadOnlyToolProbeCache();
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.mocked(streamText).mockClear();
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u-env-blocked",
              parts: [{ type: "text", text: "Read .env.local" }],
            },
          ],
        }),
      ),
    });
    const res = await POST(req);
    expect(vi.mocked(streamText)).not.toHaveBeenCalled();
    const raw = await res.text();
    expect(raw).toMatch(/I could not read that path/i);
    expect(raw).toMatch(/blocked|pattern/i);
  });

  it("concrete read .env.local with both flags on reaches streamText with tools", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.mocked(streamText).mockClear();
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u-read-env",
              parts: [{ type: "text", text: "Read .env.local" }],
            },
          ],
        }),
      ),
    });
    await POST(req);
    expect(vi.mocked(streamText)).toHaveBeenCalled();
    const opts = vi.mocked(streamText).mock.calls[0]?.[0] as {
      tools?: Record<string, unknown>;
    };
    expect(opts?.tools).toBeDefined();
  });

  it("Run npm test is not classified as file_access (no workspace-read shortcut)", () => {
    expect(detectCapabilityIntent("Run npm test")).not.toBe("file_access");
  });

  it("run npm test does not use direct workspace execution (concrete gate off)", async () => {
    const { probeOllamaChatCompletionsAcceptsToolSchema } = await import("@/lib/server/ollama");
    vi.mocked(probeOllamaChatCompletionsAcceptsToolSchema).mockResolvedValue(false);
    clearReadOnlyToolProbeCache();
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.mocked(streamText).mockClear();
    const req = new Request("http://localhost/api/spirit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        jsonBody({
          messages: [
            {
              role: "user",
              id: "u-npm",
              parts: [{ type: "text", text: "Run npm test" }],
            },
          ],
        }),
      ),
    });
    await POST(req);
    expect(vi.mocked(streamText)).toHaveBeenCalled();
  });
});
