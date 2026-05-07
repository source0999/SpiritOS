// ── capability-honesty.eval.test.ts - Phase 8 anti-hallucination eval harness ───────
// > Proves prompts + routing refuse fake tools; supplements route.test / system-state tests.

import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "fs";
import os from "os";
import path from "path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { buildModelRuntime } from "@/lib/spirit/model-runtime";
import {
  buildSystemStateBlock,
  resolveSpiritSystemState,
} from "@/lib/spirit/system-state";
import { isConcreteWorkspaceReadRequest } from "@/lib/spirit/concrete-workspace-read-request";
import {
  parseDirectWorkspaceRequest,
  handleDirectWorkspaceRequest,
} from "@/lib/spirit/tools/direct-workspace-request";
import {
  parseDirectDevCommandRequest,
  handleDirectDevCommandRequest,
} from "@/lib/spirit/tools/direct-dev-command-request";
import { runDevCommand } from "@/lib/spirit/tools/dev-command-tools";
import {
  proposeFileEdit,
  clearAllFileEditProposalsForTests,
} from "@/lib/spirit/tools/file-edit-tools";
import { createSpiritToolActivityCard } from "@/lib/spirit/spirit-activity-events";
import { mergeSpiritToolActivityCardsForMessage } from "@/lib/spirit/spirit-assistant-tool-activity";
import type { UIMessage } from "ai";

const WORKSPACE_CAPS = [
  "workspace_file_read",
  "workspace_file_list",
  "log_tail_read",
  "system_status",
] as const;

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("Phase 8 eval: system-state honesty", () => {
  it("default env keeps workspace read/list/tail/status, file_editing, terminal_execution unavailable", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "");
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "");
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    for (const c of WORKSPACE_CAPS) {
      expect(state.unavailableCapabilities).toContain(c);
      expect(state.availableCapabilities).not.toContain(c);
    }
    expect(state.unavailableCapabilities).toContain("file_editing");
    expect(state.unavailableCapabilities).toContain("terminal_execution");
    expect(state.availableCapabilities).not.toContain("file_editing");
    expect(state.availableCapabilities).not.toContain("terminal_execution");
  });

  it("SPIRIT_ENABLE_LOCAL_TOOLS=true + SPIRIT_OLLAMA_SUPPORTS_TOOLS=true but localToolsAttached=false keeps workspace caps unavailable", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      localToolsAttached: false,
    });
    for (const c of WORKSPACE_CAPS) {
      expect(state.unavailableCapabilities).toContain(c);
    }
  });

  it("localToolsAttached=true surfaces workspace caps when both env flags allow", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      localToolsAttached: true,
    });
    for (const c of WORKSPACE_CAPS) {
      expect(state.availableCapabilities).toContain(c);
    }
  });

  it("file edit env on but fileEditToolsAttached=false keeps file_editing unavailable", () => {
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "true");
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      fileEditToolsAttached: false,
    });
    expect(state.unavailableCapabilities).toContain("file_editing");
    expect(state.fileEditingAttachmentNote).toBeTruthy();
  });

  it("fileEditToolsAttached=true enables file_editing when env on", () => {
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "true");
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      fileEditToolsAttached: true,
    });
    expect(state.availableCapabilities).toContain("file_editing");
  });

  it("dev command env on but devCommandToolsAttached=false keeps terminal_execution unavailable", () => {
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "true");
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      devCommandToolsAttached: false,
    });
    expect(state.unavailableCapabilities).toContain("terminal_execution");
    expect(state.devCommandAttachmentNote).toBeTruthy();
  });

  it("devCommandToolsAttached=true enables terminal_execution when env on", () => {
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "true");
    const state = resolveSpiritSystemState({
      runtimeSurface: "chat",
      devCommandToolsAttached: true,
    });
    expect(state.availableCapabilities).toContain("terminal_execution");
  });

  it("anti-hallucination instruction requires actual tool results before claims", () => {
    const state = resolveSpiritSystemState({ runtimeSurface: "chat" });
    const block = buildSystemStateBlock(state);
    expect(block).toContain(
      "Do not claim you used a tool, read a file, edited a file, ran a command",
    );
    expect(block).toContain("checked email");
    expect(block).toContain("accessed calendar");
  });
});

describe("Phase 8 eval: model-runtime honesty", () => {
  it("includes [SYSTEM STATE] only when systemState is passed", () => {
    const withState = buildModelRuntime("normal-peer", {
      lastUserMessage: "x",
      systemState: resolveSpiritSystemState({ runtimeSurface: "chat" }),
    });
    expect(withState.systemPrompt).toMatch(/\[SYSTEM STATE\]\nTime:/);
    const without = buildModelRuntime("normal-peer", { lastUserMessage: "x" });
    expect(without.systemPrompt).not.toMatch(/\[SYSTEM STATE\]\nTime:/);
  });

  it("[SEMANTIC ROUTING] forbids claiming unavailable capabilities when system state exists", () => {
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "x",
      systemState: resolveSpiritSystemState({
        runtimeSurface: "chat",
        localToolsAttached: false,
      }),
    });
    expect(r.systemPrompt).toContain("[SEMANTIC ROUTING]");
    expect(r.systemPrompt).toMatch(/do not claim capabilities.*unavailable/i);
  });

  it("[ORACLE MEMORY CONTEXT] appears only when oracleMemoryContext is passed", () => {
    const base = buildModelRuntime("normal-peer", { lastUserMessage: "x" });
    expect(base.systemPrompt).not.toContain("[ORACLE MEMORY CONTEXT]");
    const withMem = buildModelRuntime("normal-peer", {
      lastUserMessage: "x",
      oracleMemoryContext: "[ORACLE MEMORY CONTEXT]\nTest slice.",
    });
    expect(withMem.systemPrompt).toContain("[ORACLE MEMORY CONTEXT]");
  });

  it("when workspace tools unavailable, system prompt lists them under Unavailable capabilities", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    const r = buildModelRuntime("normal-peer", {
      lastUserMessage: "list files",
      systemState: resolveSpiritSystemState({
        runtimeSurface: "chat",
        localToolsAttached: false,
      }),
    });
    expect(r.systemPrompt).toMatch(/Unavailable capabilities:[\s\S]*workspace_file_list/);
  });

  it("SPIRIT_CAPABILITY_CONTEXT_HINT clarifies project path does not mean files were read", () => {
    const r = buildModelRuntime("normal-peer", { lastUserMessage: "yo" });
    expect(r.systemPrompt).toMatch(/SPIRIT_PROJECT_PATH[\s\S]*not that files were inspected/);
  });
});

describe("Phase 8 eval: concrete workspace honesty", () => {
  let tmpRoot: string;

  afterEach(() => {
    if (tmpRoot) rmSync(tmpRoot, { recursive: true, force: true });
  });

  it("vague browse question is not a concrete workspace read (no accidental tool path)", () => {
    expect(isConcreteWorkspaceReadRequest("Can you browse files?")).toBe(false);
    expect(parseDirectWorkspaceRequest("Can you browse files?")).toBeNull();
  });

  it("direct list returns real filenames from workspace root", async () => {
    tmpRoot = mkdtempSync(path.join(os.tmpdir(), "spirit-honesty-ws-"));
    mkdirSync(path.join(tmpRoot, "src", "lib"), { recursive: true });
    writeFileSync(path.join(tmpRoot, "src", "lib", "marker.txt"), "x", "utf8");
    vi.stubEnv("SPIRIT_PROJECT_PATH", tmpRoot);
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    const out = await handleDirectWorkspaceRequest("list the files in src/lib");
    expect(out).not.toBeNull();
    expect(out!.markdown).toContain("marker.txt");
    expect(out!.toolActivity[0]?.kind).toBe("workspace_list");
    expect(JSON.stringify(out!.toolActivity)).not.toContain(tmpRoot);
  });

  it("read .env.local yields blocked message, not secret contents", async () => {
    tmpRoot = mkdtempSync(path.join(os.tmpdir(), "spirit-honesty-env-"));
    writeFileSync(path.join(tmpRoot, ".env.local"), "SECRET=42", "utf8");
    vi.stubEnv("SPIRIT_PROJECT_PATH", tmpRoot);
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    const out = await handleDirectWorkspaceRequest("read .env.local");
    expect(out).not.toBeNull();
    expect(out!.markdown).toMatch(/could not read/i);
    expect(out!.markdown).not.toContain("SECRET=42");
    expect(out!.toolActivity.some((c) => c.kind === "tool_blocked")).toBe(true);
  });

  it("path traversal read is rejected safely", async () => {
    tmpRoot = mkdtempSync(path.join(os.tmpdir(), "spirit-honesty-trav-"));
    vi.stubEnv("SPIRIT_PROJECT_PATH", tmpRoot);
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    const out = await handleDirectWorkspaceRequest("read ../../.ssh/id_rsa");
    expect(out).not.toBeNull();
    expect(out!.markdown).toMatch(/could not read/i);
    expect(out!.markdown).not.toContain("BEGIN OPENSSH");
    expect(JSON.stringify(out!.toolActivity)).not.toContain(tmpRoot);
  });
});

describe("Phase 8 eval: dev command honesty", () => {
  beforeEach(() => {
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_PROJECT_PATH", "/home/source/SpiritOS");
  });

  it("parseDirectDevCommandRequest rejects arbitrary shell phrases", () => {
    expect(parseDirectDevCommandRequest("run this command: echo hi")).toBeNull();
    expect(parseDirectDevCommandRequest("Run rm -rf node_modules")).toBeNull();
  });

  it("runDevCommand rejects unknown ids (no user-controlled shell)", async () => {
    const bad = await runDevCommand({ commandId: "echo_hi" as "git_status" });
    expect(bad.error?.code).toBe("UNKNOWN_COMMAND");
  });

  it("npm_test without confirm returns confirmation guidance from direct fallback", async () => {
    const out = await handleDirectDevCommandRequest("run npm test");
    expect(out).not.toBeNull();
    expect(out!.markdown).toMatch(/Confirmation required/i);
    expect(out!.toolActivity[0]?.status).toBe("confirmation_required");
  });
});

describe("Phase 8 eval: file edit honesty", () => {
  let tmpRoot: string;

  beforeEach(() => {
    tmpRoot = mkdtempSync(path.join(os.tmpdir(), "spirit-honesty-fe-"));
    vi.stubEnv("SPIRIT_PROJECT_PATH", tmpRoot);
    clearAllFileEditProposalsForTests();
  });

  afterEach(() => {
    rmSync(tmpRoot, { recursive: true, force: true });
    clearAllFileEditProposalsForTests();
  });

  it("file editing disabled returns FILE_EDIT_DISABLED without writing", async () => {
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "false");
    writeFileSync(path.join(tmpRoot, "z.txt"), "a", "utf8");
    const r = await proposeFileEdit({ filePath: "z.txt", nextContent: "b" });
    expect(r.ok === false && r.code === "FILE_EDIT_DISABLED").toBe(true);
    const { readFileSync } = await import("fs");
    expect(readFileSync(path.join(tmpRoot, "z.txt"), "utf8")).toBe("a");
  });

  it("propose does not mutate disk until apply with confirm", async () => {
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "true");
    writeFileSync(path.join(tmpRoot, "p.txt"), "old\n", "utf8");
    const p = await proposeFileEdit({ filePath: "p.txt", nextContent: "new\n" });
    expect(p.ok).toBe(true);
    if (!p.ok) throw new Error("propose");
    const { readFileSync } = await import("fs");
    expect(readFileSync(path.join(tmpRoot, "p.txt"), "utf8")).toBe("old\n");
  });
});

describe("Phase 8 eval: activity honesty", () => {
  it("metadata cards never embed absolute workspace root in JSON", () => {
    const secretRoot = "/this/should/not/appear/in/cards";
    const card = createSpiritToolActivityCard({
      kind: "workspace_list",
      label: "List workspace files",
      status: "completed",
      target: "src",
      summary: "ok",
    });
    const json = JSON.stringify([card]);
    expect(json).not.toContain(secretRoot);
    expect(json).not.toMatch(/\/home\/[^\s"]+\/SpiritOS/);
  });

  it("mergeSpiritToolActivityCardsForMessage preserves blocked semantics from metadata", () => {
    const msg = {
      id: "m",
      role: "assistant" as const,
      metadata: {
        spiritToolActivity: [
          createSpiritToolActivityCard({
            kind: "tool_unavailable",
            label: "Dev command",
            status: "failed",
            target: "npm_lint",
            safeMessage: "Script missing",
          }),
        ],
      },
      parts: [{ type: "text" as const, text: "x" }],
    } satisfies UIMessage;
    const cards = mergeSpiritToolActivityCardsForMessage(msg);
    expect(cards[0]?.safeMessage).toBe("Script missing");
    expect(JSON.stringify(cards)).not.toMatch(/at \w+ \(/);
  });
});
