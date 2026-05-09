import { afterEach, describe, expect, it, vi } from "vitest";

import {
  isWindowsPathAllowlisted,
  listWindowsFiles,
  normalizeWindowsFsBaseUrl,
  normalizeWindowsRequestPath,
} from "../windows-workspace-tools";

describe("windows-workspace-tools", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("normalizes Windows drive paths and natural c/projects paths", () => {
    expect(normalizeWindowsRequestPath("C:/Projects")).toBe("C:\\Projects");
    expect(normalizeWindowsRequestPath("my c/projects folder")).toBe("C:\\projects");
    expect(normalizeWindowsRequestPath("src/lib")).toBeNull();
  });

  it("enforces the configured allowlist before contacting the bridge", () => {
    vi.stubEnv("SPIRIT_WINDOWS_FS_ALLOWLIST", "C:\\Projects");
    expect(isWindowsPathAllowlisted("C:\\Projects")).toBe(true);
    expect(isWindowsPathAllowlisted("C:\\Projects\\SpiritOS")).toBe(true);
    expect(isWindowsPathAllowlisted("C:\\Windows")).toBe(false);
  });

  it("normalizes copied LAN URLs with angle brackets", () => {
    expect(normalizeWindowsFsBaseUrl("http://<10.0.0.126>:3000")).toBe(
      "http://10.0.0.126:3000",
    );
    expect(normalizeWindowsFsBaseUrl("not a url")).toBeNull();
  });

  it("returns disabled deterministically when the bridge env is off", async () => {
    vi.stubEnv("SPIRIT_WINDOWS_FS_ENABLED", "false");
    const r = await listWindowsFiles({ path: "C:\\Projects" });
    expect(r.ok).toBe(false);
    if (r.ok) throw new Error("expected disabled");
    expect(r.code).toBe("WINDOWS_FS_DISABLED");
  });

  it("blocks non-allowlisted paths without fetch", async () => {
    vi.stubEnv("SPIRIT_WINDOWS_FS_ENABLED", "true");
    vi.stubEnv("SPIRIT_WINDOWS_FS_BASE_URL", "http://windows-host:3000");
    vi.stubEnv("SPIRIT_WINDOWS_FS_TOKEN", "3399");
    vi.stubEnv("SPIRIT_WINDOWS_FS_ALLOWLIST", "C:\\Projects");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const r = await listWindowsFiles({ path: "C:\\Windows" });
    expect(r.ok).toBe(false);
    if (r.ok) throw new Error("expected blocked");
    expect(r.code).toBe("PATH_NOT_ALLOWLISTED");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
