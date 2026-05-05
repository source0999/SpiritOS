import { describe, expect, it } from "vitest";

import { formatCapabilityAnswer } from "../format-capability-answer";
import type { CapabilityRegistryResponse } from "../types";
import type { SpiritDiagnosticsPayload } from "@/lib/server/spirit-diagnostics";

const baseRegistry = (
  overrides?: Partial<CapabilityRegistryResponse>,
): CapabilityRegistryResponse => ({
  ok: true,
  collectedAt: "2026-05-04T12:00:00.000Z",
  host: { id: "host-z", label: "Host Z", source: "local" },
  nodes: [
    {
      id: "spiritdesktop",
      label: "spiritdesktop",
      status: "online",
      source: "remote",
      platform: "win32",
      capabilities: {
        telemetry: { enabled: true, readOnly: true },
        storageTelemetry: { enabled: true, readOnly: true },
        projects: { enabled: false, configured: false, readOnly: true },
        ssh: { enabled: false, status: "unverified", requiresApproval: true },
        remoteControl: { live: true, requiresApproval: true },
      },
      telemetrySnapshot: {
        cpu: { model: "AMD X", cores: 8, usagePct: 12, loadAvg: null },
        memory: {
          totalBytes: 32e9,
          freeBytes: 16e9,
          usedBytes: 16e9,
          usedPct: 50,
        },
        uptimeSec: 3600,
        storage: {
          drives: [
            {
              id: "c",
              name: "C:",
              mount: "C:",
              fsType: "NTFS",
              type: "SSD",
              totalBytes: 500e9,
              usedBytes: 200e9,
              freeBytes: 300e9,
              usedPct: 40,
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
  ...overrides,
});

const diagnosticsFixture = (): SpiritDiagnosticsPayload => ({
  engine: "Ollama",
  maxOutputTokens: 1024,
  maxOutputTokensSource: "default",
  oracleMaxOutputTokens: 768,
  oracleMaxOutputTokensSource: "test",
  chatModel: "hermes4-test",
  oracleLaneModel: "oracle-test",
  context: { label: "8192", source: "OLLAMA_NUM_CTX" },
  tts: { provider: "Piper", voice: "fable", source: "test" },
  stt: {
    provider: "Whisper",
    url: "http://localhost:8000",
    source: "test",
    transcribePath: "/v1/audio/transcriptions",
  },
});

const fmt = (
  intentKind: Parameters<typeof formatCapabilityAnswer>[0]["intentKind"],
  extra?: Partial<Parameters<typeof formatCapabilityAnswer>[0]>,
) =>
  formatCapabilityAnswer({
    registry: baseRegistry(),
    diagnostics: diagnosticsFixture(),
    webSearchEnabled: false,
    runtimeSurface: "chat",
    activeResolvedModelId: "hermes4-test",
    intentKind,
    ...extra,
  });

describe("formatCapabilityAnswer", () => {
  it("general_capabilities / SpiritOs overview: labels, tools, limits; no scripted opener", () => {
    const text = fmt("general_capabilities");
    expect(text).toContain("spiritdesktop");
    expect(text).toContain("`get_capabilities`");
    expect(text).toMatch(/browse|folders|arbitrary/i);
    expect(text).toMatch(/SSH/i);
    expect(text).not.toMatch(/Here is what SpiritOS can see right now/i);
    expect(text).not.toMatch(/Mock CPU|AMD X|12%/);
  });

  it("tool_inventory uses same overview body as general_capabilities", () => {
    const g = fmt("general_capabilities");
    const t = fmt("tool_inventory");
    expect(g).toBe(t);
  });

  it("file_access: direct no, drive telemetry yes, no CPU dump", () => {
    const text = fmt("file_access", {
      userMessage: "can you browse or list my C drive yet?",
    });
    expect(text).toMatch(/not (yet|wired)/i);
    expect(text.toLowerCase()).toMatch(/drive-level|telemetry|storage/);
    expect(text.toLowerCase()).toMatch(/browse|listing|folders/);
    expect(text).not.toContain("AMD X");
    expect(text).not.toMatch(/Here is what SpiritOS can see right now/i);
  });

  it("storage_status see C: yes when C: present in telemetry", () => {
    const text = fmt("storage_status", { userMessage: "can you see my C drive?" });
    expect(text).toMatch(/^Yes/i);
    expect(text.toLowerCase()).toMatch(/storage telemetry|telemetry/);
    expect(text).toMatch(/browse|list files|folders/i);
    expect(text).not.toMatch(/^No — not yet/i);
    expect(text).not.toContain("AMD X");
    expect(text).not.toMatch(/uptime|RAM:/i);
  });

  it("oracle storage_status see C is short voice-sized", () => {
    const text = formatCapabilityAnswer({
      registry: baseRegistry(),
      diagnostics: diagnosticsFixture(),
      webSearchEnabled: false,
      runtimeSurface: "oracle",
      activeResolvedModelId: "hermes4-test",
      intentKind: "storage_status",
      userMessage: "can you see my C drive?",
    });
    expect(text.length).toBeLessThan(420);
    expect(text).toMatch(/Yes|storage telemetry/i);
  });

  it("oracle file_access is short", () => {
    const text = formatCapabilityAnswer({
      registry: baseRegistry(),
      diagnostics: diagnosticsFixture(),
      webSearchEnabled: false,
      runtimeSurface: "oracle",
      activeResolvedModelId: "hermes4-test",
      intentKind: "file_access",
      userMessage: "can you browse my C drive?",
    });
    expect(text.length).toBeLessThan(350);
    expect(text).toMatch(/not yet|wired|browse/i);
  });

  it("oracle desktop_control mentions manual SSH outside app", () => {
    const text = formatCapabilityAnswer({
      registry: baseRegistry(),
      diagnostics: diagnosticsFixture(),
      webSearchEnabled: false,
      runtimeSurface: "oracle",
      activeResolvedModelId: "hermes4-test",
      intentKind: "desktop_control",
      userMessage: "can you ssh into my desktop?",
    });
    expect(text.length).toBeLessThan(400);
    expect(text).toMatch(/SSH/i);
    expect(text.toLowerCase()).toMatch(/manual|outside|machine/);
  });

  it("hardware_summary: includes CPU detail when asked", () => {
    const text = fmt("hardware_summary");
    expect(text).toContain("spiritdesktop");
    expect(text).toMatch(/RAM|CPU/i);
    expect(text).not.toMatch(/Here is what SpiritOS can see right now/i);
  });

  it("ai_runtime: models only, not node telemetry wall", () => {
    const text = fmt("ai_runtime", { ollamaReachable: true });
    expect(text).toContain("hermes4-test");
    expect(text).not.toContain("spiritdesktop");
    expect(text).not.toMatch(/RAM:/);
  });

  it("does not leak token-like secrets", () => {
    const text = fmt("general_capabilities");
    expect(text).not.toMatch(/SPIRIT_TELEMETRY_TOKEN|Bearer\s+[a-zA-Z0-9]{20,}/);
  });

  it("oracle overview stays concise", () => {
    const text = formatCapabilityAnswer({
      registry: baseRegistry(),
      diagnostics: diagnosticsFixture(),
      webSearchEnabled: false,
      runtimeSurface: "oracle",
      activeResolvedModelId: "hermes4-test",
      intentKind: "general_capabilities",
    });
    expect(text.length).toBeLessThan(900);
    expect(text).toContain("live read-only");
  });
});
