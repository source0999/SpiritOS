import { afterEach, describe, expect, it, vi } from "vitest";

import {
  handleDirectWorkspaceRequest,
  parseDirectWorkspaceRequest,
} from "../direct-workspace-request";

describe("parseDirectWorkspaceRequest", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("parses list the files in src/lib/spirit", () => {
    expect(parseDirectWorkspaceRequest("List the files in src/lib/spirit")).toEqual({
      kind: "list",
      source: "workspace",
      directory: "src/lib/spirit",
    });
  });

  it("parses show files in src/lib", () => {
    expect(parseDirectWorkspaceRequest("show files in src/lib")).toEqual({
      kind: "list",
      source: "workspace",
      directory: "src/lib",
    });
  });

  it("parses natural workspace list requests", () => {
    expect(parseDirectWorkspaceRequest("whats in src/lib?")).toEqual({
      kind: "list",
      source: "workspace",
      directory: "src/lib",
    });
    expect(parseDirectWorkspaceRequest("what's in src/lib/spirit folder?")).toEqual({
      kind: "list",
      source: "workspace",
      directory: "src/lib/spirit",
    });
  });

  it("parses Windows absolute list requests separately", () => {
    const win = parseDirectWorkspaceRequest("what files are in C:/Projects?");
    expect(win).toMatchObject({
      kind: "list",
      source: "windows",
    });
    expect(win?.kind === "list" ? win.directory : "").toMatch(/^C:\\Projects/i);

    const natural = parseDirectWorkspaceRequest("what's in my c/projects folder?");
    expect(natural).toMatchObject({
      kind: "list",
      source: "windows",
    });
    expect(natural?.kind === "list" ? natural.directory : "").toMatch(/^C:\\projects/i);
  });

  it("parses read package.json", () => {
    expect(parseDirectWorkspaceRequest("read package.json")).toEqual({
      kind: "read",
      filePath: "package.json",
    });
  });

  it("parses open src/lib/spirit/model-runtime.ts", () => {
    expect(parseDirectWorkspaceRequest("open src/lib/spirit/model-runtime.ts")).toEqual({
      kind: "read",
      filePath: "src/lib/spirit/model-runtime.ts",
    });
  });

  it("parses tail nohup.out", () => {
    expect(parseDirectWorkspaceRequest("tail nohup.out")).toEqual({
      kind: "tail",
      filePath: "nohup.out",
    });
  });

  it("parses show last 50 lines of app.log", () => {
    expect(parseDirectWorkspaceRequest("show last 50 lines of app.log")).toEqual({
      kind: "tail",
      filePath: "app.log",
      lineCount: 50,
    });
  });

  it("rejects can you browse files", () => {
    expect(parseDirectWorkspaceRequest("Can you browse files?")).toBeNull();
  });

  it("rejects run npm test", () => {
    expect(parseDirectWorkspaceRequest("Run npm test")).toBeNull();
  });

  it("rejects edit src/app/page.tsx", () => {
    expect(parseDirectWorkspaceRequest("edit src/app/page.tsx")).toBeNull();
  });
});

describe("handleDirectWorkspaceRequest", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns null when SPIRIT_ENABLE_LOCAL_TOOLS is not true", async () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "false");
    await expect(handleDirectWorkspaceRequest("read package.json")).resolves.toBeNull();
  });
});
