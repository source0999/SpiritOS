import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import {
  handleDirectDevCommandRequest,
  parseDirectDevCommandRequest,
} from "../direct-dev-command-request";
import { runDevCommand } from "@/lib/spirit/tools/dev-command-tools";

vi.mock("@/lib/spirit/tools/dev-command-tools", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/spirit/tools/dev-command-tools")>();
  return {
    ...actual,
    runDevCommand: vi.fn(actual.runDevCommand),
  };
});

describe("parseDirectDevCommandRequest", () => {
  it('parses "check git status" as git_status', () => {
    expect(parseDirectDevCommandRequest("check git status")).toEqual({
      commandId: "git_status",
      confirm: undefined,
    });
  });

  it('parses "show git diff" as git_diff', () => {
    expect(parseDirectDevCommandRequest("show git diff")).toEqual({ commandId: "git_diff" });
  });

  it('parses "run typecheck" as npm_typecheck', () => {
    expect(parseDirectDevCommandRequest("run typecheck")).toEqual({ commandId: "npm_typecheck" });
  });

  it('parses "run npm test" as npm_test', () => {
    expect(parseDirectDevCommandRequest("run npm test")).toEqual({ commandId: "npm_test" });
  });

  it('parses "run npm test confirm true" as npm_test with confirm', () => {
    expect(parseDirectDevCommandRequest("run npm test confirm true")).toEqual({
      commandId: "npm_test",
      confirm: true,
    });
  });

  it('parses "run lint" as npm_lint', () => {
    expect(parseDirectDevCommandRequest("run lint")).toEqual({ commandId: "npm_lint" });
  });

  it('parses "run build" as npm_build', () => {
    expect(parseDirectDevCommandRequest("run build")).toEqual({ commandId: "npm_build" });
  });

  it('rejects "npm install lodash"', () => {
    expect(parseDirectDevCommandRequest("npm install lodash")).toBeNull();
  });

  it('rejects "rm -rf"', () => {
    expect(parseDirectDevCommandRequest("rm -rf /")).toBeNull();
  });

  it('rejects "print env"', () => {
    expect(parseDirectDevCommandRequest("print env")).toBeNull();
  });

  it('rejects vague can you run commands', () => {
    expect(parseDirectDevCommandRequest("can you run commands?")).toBeNull();
  });
});

describe("handleDirectDevCommandRequest", () => {
  beforeEach(() => {
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_PROJECT_PATH", "/home/source/SpiritOS");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.mocked(runDevCommand).mockReset();
  });

  it("returns null when SPIRIT_ENABLE_DEV_COMMAND_TOOLS is false", async () => {
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "false");
    await expect(handleDirectDevCommandRequest("check git status")).resolves.toBeNull();
  });

  it("npm_test without confirm returns confirmation required text", async () => {
    vi.mocked(runDevCommand).mockResolvedValue({
      ok: false,
      commandId: "npm_test",
      label: "npx vitest run",
      requiresConfirmation: true,
      message: "need confirm",
    });
    const out = await handleDirectDevCommandRequest("run npm test");
    expect(out).toMatch(/Confirmation required/);
    expect(out).toMatch(/Run npm test confirm true/);
  });

  it("git_status calls runDevCommand and formats output", async () => {
    vi.mocked(runDevCommand).mockResolvedValue({
      ok: true,
      commandId: "git_status",
      label: "git status",
      exitCode: 0,
      stdout: " M file.ts",
      stderr: "",
      output: " M file.ts",
    });
    const out = await handleDirectDevCommandRequest("git status");
    expect(runDevCommand).toHaveBeenCalledWith({ commandId: "git_status", confirm: undefined });
    expect(out).toMatch(/^Dev command: git status/);
    expect(out).toContain("```text");
    expect(out).toContain("M file.ts");
  });
});
