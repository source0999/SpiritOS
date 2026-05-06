import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buildSystemStateBlock,
  resolveSpiritSystemState,
} from "@/lib/spirit/system-state";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("resolveSpiritSystemState", () => {
  it("uses provided currentTimeIso", () => {
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      currentTimeIso: "2026-05-06T12:00:00.000Z",
    });
    expect(state.currentTimeIso).toBe("2026-05-06T12:00:00.000Z");
  });

  it("generates currentTimeIso when not provided", () => {
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.currentTimeIso).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
  });

  it("runtimeSurface is reflected", () => {
    expect(resolveSpiritSystemState({ runtimeSurface: "oracle" }).runtimeSurface).toBe("oracle");
    expect(resolveSpiritSystemState({ runtimeSurface: "chat" }).runtimeSurface).toBe("chat");
  });

  it("modelHint is reflected", () => {
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      modelHint: "hermes-3-llama3.1-8b",
    });
    expect(state.modelHint).toBe("hermes-3-llama3.1-8b");
  });

  it("modelHint defaults to null when not provided", () => {
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.modelHint).toBeNull();
  });

  it("modelProfileId is reflected", () => {
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      modelProfileId: "researcher",
    });
    expect(state.modelProfileId).toBe("researcher");
  });

  it("modelProfileLabel is reflected", () => {
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      modelProfileId: "researcher",
      modelProfileLabel: "Researcher",
    });
    expect(state.modelProfileLabel).toBe("Researcher");
  });

  it("hardwareProfile defaults to 'unknown' when env unset", () => {
    vi.stubEnv("SPIRIT_HARDWARE_PROFILE", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.hardwareProfile).toBe("unknown");
  });

  it("hardwareProfile reflects SPIRIT_HARDWARE_PROFILE env", () => {
    vi.stubEnv("SPIRIT_HARDWARE_PROFILE", "homelab-nuc");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.hardwareProfile).toBe("homelab-nuc");
  });

  it("projectPathConfigured is false when SPIRIT_PROJECT_PATH unset", () => {
    vi.stubEnv("SPIRIT_PROJECT_PATH", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.projectPathConfigured).toBe(false);
  });

  it("projectPathConfigured is true when SPIRIT_PROJECT_PATH set", () => {
    vi.stubEnv("SPIRIT_PROJECT_PATH", "/home/user/project");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.projectPathConfigured).toBe(true);
  });

  it("baseline capabilities always include chat, tts, stt, web_search_when_enabled", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "");
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.availableCapabilities).toContain("chat");
    expect(state.availableCapabilities).toContain("tts");
    expect(state.availableCapabilities).toContain("stt");
    expect(state.availableCapabilities).toContain("web_search_when_enabled");
  });

  it("workspace tools in unavailable when SPIRIT_ENABLE_LOCAL_TOOLS not set", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.unavailableCapabilities).toContain("workspace_file_read");
    expect(state.unavailableCapabilities).toContain("workspace_file_list");
    expect(state.unavailableCapabilities).toContain("log_tail_read");
    expect(state.unavailableCapabilities).toContain("system_status");
  });

  it("workspace tools move to available when SPIRIT_ENABLE_LOCAL_TOOLS=true", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.availableCapabilities).toContain("workspace_file_read");
    expect(state.availableCapabilities).toContain("workspace_file_list");
    expect(state.availableCapabilities).toContain("log_tail_read");
    expect(state.availableCapabilities).toContain("system_status");
    expect(state.unavailableCapabilities).not.toContain("workspace_file_read");
  });

  it("file_editing unavailable when SPIRIT_ENABLE_FILE_EDIT_TOOLS not set", () => {
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.unavailableCapabilities).toContain("file_editing");
    expect(state.availableCapabilities).not.toContain("file_editing");
  });

  it("file_editing moves to available when SPIRIT_ENABLE_FILE_EDIT_TOOLS=true", () => {
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "true");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.availableCapabilities).toContain("file_editing");
    expect(state.unavailableCapabilities).not.toContain("file_editing");
  });

  it("terminal_execution unavailable when SPIRIT_ENABLE_DEV_COMMAND_TOOLS not set", () => {
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.unavailableCapabilities).toContain("terminal_execution");
  });

  it("terminal_execution moves to available when SPIRIT_ENABLE_DEV_COMMAND_TOOLS=true", () => {
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "true");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.availableCapabilities).toContain("terminal_execution");
    expect(state.unavailableCapabilities).not.toContain("terminal_execution");
  });

  it("email_access unavailable by default", () => {
    vi.stubEnv("SPIRIT_ENABLE_EMAIL_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.unavailableCapabilities).toContain("email_access");
  });

  it("calendar_access unavailable by default", () => {
    vi.stubEnv("SPIRIT_ENABLE_CALENDAR_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(state.unavailableCapabilities).toContain("calendar_access");
  });
});

describe("buildSystemStateBlock", () => {
  it("includes [SYSTEM STATE] header", () => {
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(buildSystemStateBlock(state)).toContain("[SYSTEM STATE]");
  });

  it("includes current time ISO string", () => {
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      currentTimeIso: "2026-05-06T12:00:00.000Z",
    });
    expect(buildSystemStateBlock(state)).toContain("2026-05-06T12:00:00.000Z");
  });

  it("includes runtimeSurface", () => {
    const chatState = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const oracleState = resolveSpiritSystemState({ runtimeSurface: "oracle" });
    expect(buildSystemStateBlock(chatState)).toContain("chat");
    expect(buildSystemStateBlock(oracleState)).toContain("oracle");
  });

  it("includes modelHint when provided", () => {
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      modelHint: "hermes-3-llama3.1-8b",
    });
    expect(buildSystemStateBlock(state)).toContain("hermes-3-llama3.1-8b");
  });

  it("includes modelProfileId when provided", () => {
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      modelProfileId: "researcher",
    });
    expect(buildSystemStateBlock(state)).toContain("researcher");
  });

  it("includes modelProfileLabel in parentheses when provided", () => {
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      modelProfileId: "researcher",
      modelProfileLabel: "Researcher",
    });
    const block = buildSystemStateBlock(state);
    expect(block).toContain("researcher (Researcher)");
  });

  it("hardware profile 'unknown' appears when env unset", () => {
    vi.stubEnv("SPIRIT_HARDWARE_PROFILE", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(buildSystemStateBlock(state)).toContain("unknown");
  });

  it("hardware profile value appears in block", () => {
    vi.stubEnv("SPIRIT_HARDWARE_PROFILE", "homelab-nuc");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    expect(buildSystemStateBlock(state)).toContain("homelab-nuc");
  });

  it("shows project path configured as yes when env is set", () => {
    vi.stubEnv("SPIRIT_PROJECT_PATH", "/home/source/SpiritOS");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).toMatch(/[Pp]roject path configured:\s*yes/);
  });

  it("shows project path configured as no when env is unset", () => {
    vi.stubEnv("SPIRIT_PROJECT_PATH", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).toMatch(/[Pp]roject path configured:\s*no/);
  });

  it("does not expose the raw SPIRIT_PROJECT_PATH value in the block", () => {
    vi.stubEnv("SPIRIT_PROJECT_PATH", "/secret/path/to/project");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).not.toContain("/secret/path/to/project");
  });

  it("includes available capabilities in block", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).toContain("chat");
    expect(block).toContain("tts");
    expect(block).toContain("stt");
    expect(block).toContain("web_search_when_enabled");
  });

  it("includes unavailable capabilities in block", () => {
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).toContain("file_editing");
    expect(block).toContain("terminal_execution");
  });

  it("includes anti-hallucination rule", () => {
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).toMatch(/Do not claim you used a tool/i);
  });

  it("anti-hallucination rule covers file, command, email, and calendar", () => {
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).toMatch(/read a file|edited a file|ran a command/i);
    expect(block).toMatch(/checked email|accessed calendar/i);
  });

  it("includes instruction to say unavailable if asked for missing capability", () => {
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).toMatch(/unavailable/i);
    expect(block).toMatch(/manual alternative|what would be needed/i);
  });
});
