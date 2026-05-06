import { mkdtempSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import path from "path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  SpiritToolPathError,
  TOOL_MAX_OUTPUT_CHARS,
  createToolError,
  normalizeWorkspaceRelativePath,
  resolveSafeWorkspacePath,
  toolErrorFromUnknown,
  truncateToolOutput,
} from "../tool-safety";

describe("tool-safety", () => {
  let fixture: string;

  beforeEach(() => {
    fixture = mkdtempSync(path.join(tmpdir(), "spirit-safe-"));
    vi.stubEnv("SPIRIT_PROJECT_PATH", fixture);
  });

  afterEach(() => {
    rmSync(fixture, { recursive: true, force: true });
    vi.unstubAllEnvs();
  });

  it("rejects absolute paths", () => {
    expect(() => normalizeWorkspaceRelativePath("/etc/passwd")).toThrow(SpiritToolPathError);
  });

  it("rejects ../ traversal", () => {
    expect(() => normalizeWorkspaceRelativePath("foo/../../secret")).toThrow(SpiritToolPathError);
  });

  it("rejects .env and .env.local", () => {
    expect(() => normalizeWorkspaceRelativePath(".env")).toThrow(SpiritToolPathError);
    expect(() => normalizeWorkspaceRelativePath(".env.local")).toThrow(SpiritToolPathError);
  });

  it("rejects node_modules segment", () => {
    expect(() => normalizeWorkspaceRelativePath("node_modules/foo")).toThrow(SpiritToolPathError);
  });

  it("rejects .git segment", () => {
    expect(() => normalizeWorkspaceRelativePath(".git/config")).toThrow(SpiritToolPathError);
  });

  it("rejects key/private style basenames", () => {
    expect(() => normalizeWorkspaceRelativePath("secrets.yaml")).toThrow(SpiritToolPathError);
    expect(() => normalizeWorkspaceRelativePath("id_rsa")).toThrow(SpiritToolPathError);
    expect(() => normalizeWorkspaceRelativePath("cert.pem")).toThrow(SpiritToolPathError);
  });

  it("allows normal relative file paths", () => {
    writeFileSync(path.join(fixture, "readme.md"), "hi");
    const resolved = resolveSafeWorkspacePath("readme.md");
    expect(resolved).toBe(path.join(fixture, "readme.md"));
  });

  it("truncates long output", () => {
    const long = "x".repeat(TOOL_MAX_OUTPUT_CHARS + 50);
    const out = truncateToolOutput(long, TOOL_MAX_OUTPUT_CHARS);
    expect(out.truncated).toBe(true);
    expect(out.text.length).toBeLessThanOrEqual(TOOL_MAX_OUTPUT_CHARS + 40);
  });

  it("safe error shape does not expose stack traces", () => {
    const errObj = createToolError("X", "bad");
    const wrapped = toolErrorFromUnknown(new Error("nope"));
    expect(JSON.stringify(errObj)).not.toMatch(/\bat\b/);
    expect(JSON.stringify(wrapped)).not.toMatch(/\bat\b/);
    expect(JSON.stringify(wrapped)).not.toContain("nope");
  });
});
