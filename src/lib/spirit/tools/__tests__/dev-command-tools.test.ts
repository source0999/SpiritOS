import { EventEmitter } from "events";
import { Readable } from "stream";
import type { ChildProcess } from "child_process";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mockSpawnNoShell = vi.hoisted(() => vi.fn());

vi.mock("@/lib/spirit/tools/child-process-spawn", () => ({
  spawnNoShell: mockSpawnNoShell,
}));

import {
  clearPackageScriptsCacheForTests,
  runDevCommand,
  getAllowedDevCommandIds,
  isDevCommandToolsEnvEnabled,
} from "../dev-command-tools";
import { TOOL_MAX_OUTPUT_CHARS } from "../tool-safety";

function mockSpawnClosesSync(code: number | null) {
  mockSpawnNoShell.mockImplementation(() => {
    const child = new EventEmitter() as ChildProcess;
    child.stdout = new Readable({ read() {} });
    child.stderr = new Readable({ read() {} });
    (child as { kill?: (s: string) => boolean }).kill = () => {
      queueMicrotask(() => child.emit("close", code));
      return true;
    };
    queueMicrotask(() => child.emit("close", code));
    return child;
  });
}

describe("dev-command-tools", () => {
  beforeEach(() => {
    clearPackageScriptsCacheForTests();
    mockSpawnNoShell.mockReset();
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "true");
    vi.stubEnv("SPIRIT_PROJECT_PATH", "/home/source/SpiritOS");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.useRealTimers();
    clearPackageScriptsCacheForTests();
  });

  it("disabled env returns DEV_COMMAND_TOOLS_DISABLED", async () => {
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "false");
    const r = await runDevCommand({ commandId: "git_status" });
    expect(r.ok).toBe(false);
    expect(r.error?.code).toBe("DEV_COMMAND_TOOLS_DISABLED");
  });

  it("unknown command id rejected", async () => {
    const r = await runDevCommand({ commandId: "unknown" as "git_status" });
    expect(r.ok).toBe(false);
    expect(r.error?.code).toBe("UNKNOWN_COMMAND");
  });

  it("confirmation-required command rejects without confirm:true", async () => {
    const r = await runDevCommand({ commandId: "npm_test" });
    expect(r.ok).toBe(false);
    expect(r.requiresConfirmation).toBe(true);
    expect(r.message).toMatch(/confirm/i);
  });

  it("git_status runs with fixed args when enabled", async () => {
    mockSpawnClosesSync(0);
    await runDevCommand({ commandId: "git_status" });
    expect(mockSpawnNoShell).toHaveBeenCalledWith(
      "git",
      ["status", "--short"],
      expect.objectContaining({ cwd: expect.any(String) }),
    );
  });

  it("npm_typecheck uses fixed command array", async () => {
    mockSpawnClosesSync(0);
    const r = await runDevCommand({ commandId: "npm_typecheck" });
    expect(mockSpawnNoShell).toHaveBeenCalledWith(
      "npm",
      ["run", "typecheck"],
      expect.objectContaining({ cwd: expect.any(String) }),
    );
    expect(r.ok).toBe(true);
  });

  it("missing npm script returns SCRIPT_NOT_FOUND for npm_lint when unavailable", async () => {
    vi.stubEnv("SPIRIT_PROJECT_PATH", "/nonexistent/path/phase6-dev-tools-lint-missing");
    clearPackageScriptsCacheForTests();
    const r = await runDevCommand({ commandId: "npm_lint" });
    expect(r.ok).toBe(false);
    expect(r.error?.code).toBe("SCRIPT_NOT_FOUND");
  });

  it("timeout returns timedOut true", async () => {
    vi.useFakeTimers();
    mockSpawnNoShell.mockImplementation(() => {
      const child = new EventEmitter() as ChildProcess;
      child.stdout = new Readable({ read() {} });
      child.stderr = new Readable({ read() {} });
      (child as { kill?: (s: string) => boolean }).kill = () => {
        queueMicrotask(() => child.emit("close", null));
        return true;
      };
      return child;
    });

    const p = runDevCommand({ commandId: "git_status" });
    await vi.advanceTimersByTimeAsync(10_000);
    const r = await p;
    expect(r.timedOut).toBe(true);
    expect(r.ok).toBe(false);
  });

  it("output is truncated when oversized", async () => {
    const huge = "x".repeat(TOOL_MAX_OUTPUT_CHARS + 500);
    mockSpawnNoShell.mockImplementation(() => {
      const child = new EventEmitter() as ChildProcess;
      const stdout = new Readable({
        read() {
          this.push(huge);
          this.push(null);
        },
      });
      child.stdout = stdout;
      child.stderr = new Readable({ read() {} });
      (child as { kill?: (s: string) => boolean }).kill = () => {
        queueMicrotask(() => child.emit("close", 0));
        return true;
      };
      queueMicrotask(() => child.emit("close", 0));
      return child;
    });

    const r = await runDevCommand({ commandId: "git_status" });
    expect(r.ok).toBe(true);
    expect((r.stdout ?? "").length).toBeLessThanOrEqual(TOOL_MAX_OUTPUT_CHARS + 64);
  });

  it("result does not expose raw workspace root path", async () => {
    mockSpawnClosesSync(0);
    const r = await runDevCommand({ commandId: "git_status" });
    const blob = JSON.stringify(r);
    expect(blob).not.toContain("/home/source/SpiritOS");
    expect(blob).not.toContain("/nonexistent");
  });

  it("runDevCommand uses fixed ids only (no raw shell strings in API)", async () => {
    expect(isDevCommandToolsEnvEnabled()).toBe(true);
    const ids = getAllowedDevCommandIds();
    expect(ids.length).toBeGreaterThan(0);
    expect(ids.every((id) => /^[a-z0-9_]+$/.test(id))).toBe(true);
  });
});
