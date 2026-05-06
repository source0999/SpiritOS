import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getSpiritReadOnlyTools,
  getSpiritToolsForRuntime,
  isLocalToolsEnabled,
} from "../tool-registry";

describe("tool-registry", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("disabled env returns undefined or no tools", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "false");
    expect(isLocalToolsEnabled()).toBe(false);
    expect(getSpiritToolsForRuntime()).toBeUndefined();
    expect(getSpiritReadOnlyTools()).toBeUndefined();
  });

  it("SPIRIT_ENABLE_LOCAL_TOOLS=true returns exactly four tools", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    const tools = getSpiritToolsForRuntime();
    expect(tools).toBeDefined();
    if (!tools) throw new Error("tools");
    expect(Object.keys(tools).sort()).toEqual(
      [
        "get_system_status",
        "list_workspace_files",
        "read_log_tail",
        "read_workspace_file",
      ].sort(),
    );
  });

  it("includes expected tool keys and excludes forbidden keys", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    const tools = getSpiritReadOnlyTools();
    expect(tools).toBeDefined();
    if (!tools) throw new Error("tools");
    expect(tools).toHaveProperty("list_workspace_files");
    expect(tools).toHaveProperty("read_workspace_file");
    expect(tools).toHaveProperty("read_log_tail");
    expect(tools).toHaveProperty("get_system_status");
    expect(tools).not.toHaveProperty("file_editing");
    expect(tools).not.toHaveProperty("terminal_execution");
    expect(tools).not.toHaveProperty("email_access");
    expect(tools).not.toHaveProperty("calendar_access");
  });
});
