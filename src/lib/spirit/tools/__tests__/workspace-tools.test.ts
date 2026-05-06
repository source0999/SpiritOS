import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import path from "path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TOOL_MAX_FILE_BYTES } from "../tool-safety";
import {
  getSystemStatus,
  listWorkspaceFiles,
  readLogTail,
  readWorkspaceFile,
} from "../workspace-tools";

describe("workspace-tools", () => {
  let fixture: string;

  beforeEach(() => {
    fixture = mkdtempSync(path.join(tmpdir(), "spirit-ws-"));
    vi.stubEnv("SPIRIT_PROJECT_PATH", fixture);
    mkdirSync(path.join(fixture, "src"));
    writeFileSync(path.join(fixture, "src/hello.ts"), "export const x = 1;\n");
    mkdirSync(path.join(fixture, "node_modules"));
    writeFileSync(path.join(fixture, "node_modules/shadow.txt"), "no");
    writeFileSync(path.join(fixture, "blocked.pem"), "-----BEGIN");
    writeFileSync(path.join(fixture, ".env.local"), "SECRET=1");
  });

  afterEach(() => {
    rmSync(fixture, { recursive: true, force: true });
    vi.unstubAllEnvs();
  });

  it("listWorkspaceFiles lists safe files", async () => {
    const r = await listWorkspaceFiles({ directory: ".", maxEntries: 50 });
    expect(r.ok).toBe(true);
    if (!r.ok) throw new Error("expected ok");
    const names = r.entries.map((e) => e.name);
    expect(names).toContain("src");
    expect(names).not.toContain("node_modules");
  });

  it("listWorkspaceFiles hides blocked entries", async () => {
    const r = await listWorkspaceFiles({});
    expect(r.ok).toBe(true);
    if (!r.ok) throw new Error("expected ok");
    const names = r.entries.map((e) => e.name);
    expect(names).not.toContain("node_modules");
    expect(names).not.toContain(".env.local");
    expect(names).not.toContain("blocked.pem");
  });

  it("readWorkspaceFile reads safe text file", async () => {
    const r = await readWorkspaceFile({ filePath: "src/hello.ts" });
    expect(r.ok).toBe(true);
    if (!r.ok) throw new Error("expected ok");
    expect(r.content).toContain("export const x");
  });

  it("readWorkspaceFile rejects blocked files", async () => {
    const r = await readWorkspaceFile({ filePath: ".env.local" });
    expect(r.ok).toBe(false);
  });

  it("readWorkspaceFile rejects oversized file", async () => {
    const bigName = "big.txt";
    writeFileSync(path.join(fixture, bigName), Buffer.alloc(TOOL_MAX_FILE_BYTES + 1, 97));
    const r = await readWorkspaceFile({ filePath: bigName });
    expect(r.ok).toBe(false);
    if (r.ok) throw new Error("expected failure");
    expect(r.code).toBe("FILE_TOO_LARGE");
  });

  it("readLogTail returns last N lines", async () => {
    const lines = Array.from({ length: 120 }, (_, i) => `line ${i + 1}`);
    writeFileSync(path.join(fixture, "app.log"), `${lines.join("\n")}\n`);
    const r = await readLogTail({ filePath: "app.log", lineCount: 10 });
    expect(r.ok).toBe(true);
    if (!r.ok) throw new Error("expected ok");
    expect(r.lines[r.lines.length - 1]).toMatch(/line 120/);
    expect(r.lines.length).toBeLessThanOrEqual(11);
  });

  it("readLogTail caps lineCount", async () => {
    const lines = Array.from({ length: 400 }, (_, i) => `L${i}`);
    writeFileSync(path.join(fixture, "big.log"), lines.join("\n"));
    const r = await readLogTail({ filePath: "big.log", lineCount: 9999 });
    expect(r.ok).toBe(true);
    if (!r.ok) throw new Error("expected ok");
    expect(r.lines.length).toBeLessThanOrEqual(300);
  });

  it("getSystemStatus reports read-only tools available only when env enabled", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "false");
    let s = await getSystemStatus();
    expect(s.availableReadOnlyTools.length).toBe(0);
    expect(s.unavailableTools.join(",")).toContain("list_workspace_files");

    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    s = await getSystemStatus();
    expect(s.availableReadOnlyTools.sort()).toEqual(
      ["get_system_status", "list_workspace_files", "read_log_tail", "read_workspace_file"].sort(),
    );
    expect(s.unavailableTools).toContain("file_editing");
    expect(s.unavailableTools).toContain("terminal_execution");
    expect(s.unavailableTools).toContain("email_access");
    expect(s.unavailableTools).toContain("calendar_access");
    expect(JSON.stringify(s)).not.toMatch(/[/]home[/]/);
  });
});
