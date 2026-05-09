import { describe, expect, it, vi } from "vitest";

describe("Windows agent filesystem safety", () => {
  async function loadAgent(allowlist = "C:\\Projects") {
    vi.resetModules();
    vi.stubEnv("SPIRIT_DESKTOP_FS_ALLOWLIST", allowlist);
    const agent = await import("./agent.js");
    return agent.default ?? agent;
  }

  function blockedCode(result: { ok: boolean; body?: { code?: string } }): string | undefined {
    expect(result.ok).toBe(false);
    return result.body?.code;
  }

  it("normalizes C:/Projects and c/projects to Windows drive paths", async () => {
    const agent = await loadAgent();
    expect(agent.normalizeWindowsPath("C:/Projects")).toBe("C:\\Projects");
    expect(agent.normalizeWindowsPath("c/projects")).toBe("C:\\projects");
    vi.unstubAllEnvs();
  });

  it("allows only configured roots and children", async () => {
    const agent = await loadAgent("C:\\Projects");
    expect(agent.assertFsPathAllowed("C:\\Projects").ok).toBe(true);
    expect(agent.assertFsPathAllowed("C:\\Projects\\SpiritOS").ok).toBe(true);
    expect(blockedCode(agent.assertFsPathAllowed("C:\\Windows"))).toBe("PATH_NOT_ALLOWLISTED");
    vi.unstubAllEnvs();
  });

  it("blocks traversal into sensitive segments and secret basenames", async () => {
    const agent = await loadAgent("C:\\Projects");
    expect(blockedCode(agent.assertFsPathAllowed("C:\\Projects\\repo\\.git"))).toBe("PATH_BLOCKED");
    expect(blockedCode(agent.assertFsPathAllowed("C:\\Projects\\repo\\node_modules"))).toBe("PATH_BLOCKED");
    expect(blockedCode(agent.assertFsPathAllowed("C:\\Projects\\repo\\.env.local"))).toBe("PATH_BLOCKED");
    expect(blockedCode(agent.assertFsPathAllowed("C:\\Projects\\repo\\id_rsa"))).toBe("PATH_BLOCKED");
    vi.unstubAllEnvs();
  });
});
