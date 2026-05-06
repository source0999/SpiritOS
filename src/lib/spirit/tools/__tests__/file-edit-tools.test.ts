import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "fs";
import os from "os";
import path from "path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  FILE_EDIT_MAX_NEXT_BYTES,
  applyConfirmedFileEdit,
  clearAllFileEditProposalsForTests,
  getFileEditProposalForTest,
  proposeFileEdit,
  setFileEditProposalExpiryForTest,
} from "../file-edit-tools";
import { resolveSafeWorkspacePath } from "../tool-safety";

describe("file-edit-tools", () => {
  let tmpRoot: string;

  beforeEach(() => {
    tmpRoot = mkdtempSync(path.join(os.tmpdir(), "spirit-fe-"));
    vi.stubEnv("SPIRIT_PROJECT_PATH", tmpRoot);
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "true");
    clearAllFileEditProposalsForTests();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    clearAllFileEditProposalsForTests();
    rmSync(tmpRoot, { recursive: true, force: true });
  });

  it("returns FILE_EDIT_DISABLED when SPIRIT_ENABLE_FILE_EDIT_TOOLS is false", async () => {
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "false");
    writeFileSync(path.join(tmpRoot, "a.txt"), "hi", "utf8");
    const r = await proposeFileEdit({ filePath: "a.txt", nextContent: "bye" });
    expect(r.ok === false && r.code === "FILE_EDIT_DISABLED").toBe(true);
  });

  it("proposeFileEdit creates proposal and diff without writing", async () => {
    writeFileSync(path.join(tmpRoot, "edit-me.txt"), "alpha\n", "utf8");
    const r = await proposeFileEdit({
      filePath: "edit-me.txt",
      nextContent: "beta\n",
    });
    expect(r.ok).toBe(true);
    if (!r.ok) throw new Error("expected ok");
    expect(readFileSync(path.join(tmpRoot, "edit-me.txt"), "utf8")).toBe("alpha\n");
    expect(getFileEditProposalForTest(r.proposalId)).toBeDefined();
    expect(r.diff).toContain("--- edit-me.txt");
  });

  it("proposeFileEdit rejects .env.local", async () => {
    writeFileSync(path.join(tmpRoot, ".env.local"), "x", "utf8");
    const r = await proposeFileEdit({ filePath: ".env.local", nextContent: "y" });
    expect(r.ok === false && r.code === "BLOCKED_FILE_PATTERN").toBe(true);
  });

  it("proposeFileEdit rejects path traversal", async () => {
    const r = await proposeFileEdit({ filePath: "../outside.txt", nextContent: "x" });
    expect(r.ok === false && r.code === "PATH_TRAVERSAL").toBe(true);
  });

  it("proposeFileEdit rejects node_modules segment", async () => {
    const r = await proposeFileEdit({
      filePath: "node_modules/foo/package.json",
      nextContent: "{}",
    });
    expect(r.ok === false && r.code === "BLOCKED_SEGMENT").toBe(true);
  });

  it("proposeFileEdit rejects oversized nextContent", async () => {
    writeFileSync(path.join(tmpRoot, "small.txt"), "a", "utf8");
    const huge = "x".repeat(FILE_EDIT_MAX_NEXT_BYTES + 1);
    const r = await proposeFileEdit({ filePath: "small.txt", nextContent: huge });
    expect(r.ok === false && r.code === "NEXT_TOO_LARGE").toBe(true);
  });

  it("applyConfirmedFileEdit rejects missing proposal", async () => {
    const r = await applyConfirmedFileEdit({
      proposalId: "00000000-0000-4000-8000-000000000000",
      confirm: true,
    });
    expect(r.ok === false && r.code === "PROPOSAL_NOT_FOUND").toBe(true);
  });

  it("applyConfirmedFileEdit rejects expired proposal", async () => {
    writeFileSync(path.join(tmpRoot, "e.txt"), "old\n", "utf8");
    const p = await proposeFileEdit({ filePath: "e.txt", nextContent: "new\n" });
    expect(p.ok).toBe(true);
    if (!p.ok) throw new Error("propose");
    setFileEditProposalExpiryForTest(p.proposalId, Date.now() - 1000);
    const r = await applyConfirmedFileEdit({ proposalId: p.proposalId, confirm: true });
    expect(r.ok === false && r.code === "PROPOSAL_EXPIRED").toBe(true);
  });

  it("applyConfirmedFileEdit rejects confirm false", async () => {
    writeFileSync(path.join(tmpRoot, "c.txt"), "x", "utf8");
    const p = await proposeFileEdit({ filePath: "c.txt", nextContent: "y" });
    expect(p.ok).toBe(true);
    if (!p.ok) throw new Error("propose");
    const r = await applyConfirmedFileEdit({ proposalId: p.proposalId, confirm: false });
    expect(r.ok === false && r.code === "CONFIRMATION_REQUIRED").toBe(true);
  });

  it("applyConfirmedFileEdit writes when confirmed and creates backup", async () => {
    writeFileSync(path.join(tmpRoot, "w.txt"), "before\n", "utf8");
    const p = await proposeFileEdit({ filePath: "w.txt", nextContent: "after\n" });
    expect(p.ok).toBe(true);
    if (!p.ok) throw new Error("propose");
    const r = await applyConfirmedFileEdit({ proposalId: p.proposalId, confirm: true });
    expect(r.ok).toBe(true);
    if (!r.ok) throw new Error("apply");
    expect(readFileSync(path.join(tmpRoot, "w.txt"), "utf8")).toBe("after\n");
    expect(r.backupRelativePath.startsWith(".spirit-backups/")).toBe(true);
    expect(r.backupRelativePath.endsWith(".bak")).toBe(true);
    const backupAbs = resolveSafeWorkspacePath(r.backupRelativePath);
    expect(readFileSync(backupAbs, "utf8")).toBe("before\n");
  });

  it("applyConfirmedFileEdit rejects when file changed since proposal", async () => {
    writeFileSync(path.join(tmpRoot, "race.txt"), "v1\n", "utf8");
    const p = await proposeFileEdit({ filePath: "race.txt", nextContent: "v2\n" });
    expect(p.ok).toBe(true);
    if (!p.ok) throw new Error("propose");
    writeFileSync(path.join(tmpRoot, "race.txt"), "tampered\n", "utf8");
    const r = await applyConfirmedFileEdit({ proposalId: p.proposalId, confirm: true });
    expect(r.ok === false && r.code === "CONFLICT").toBe(true);
  });

  it("apply output does not expose raw workspace root path", async () => {
    writeFileSync(path.join(tmpRoot, "root-check.txt"), "a", "utf8");
    const p = await proposeFileEdit({ filePath: "root-check.txt", nextContent: "b" });
    expect(p.ok).toBe(true);
    if (!p.ok) throw new Error("propose");
    const r = await applyConfirmedFileEdit({ proposalId: p.proposalId, confirm: true });
    expect(r.ok).toBe(true);
    if (!r.ok) throw new Error("apply");
    expect(JSON.stringify(r)).not.toContain(tmpRoot);
  });
});
