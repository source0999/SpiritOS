import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getSpiritDevCommandTools,
  getSpiritReadOnlyTools,
  getSpiritToolsForRuntime,
  isLocalToolsEnabled,
  spiritToolsetIncludesRunDevCommand,
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

  it("SPIRIT_ENABLE_LOCAL_TOOLS=true returns exactly four tools when dev commands off", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "false");
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
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "false");
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

  it("returns undefined when Ollama tool transport is not opted in", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
    expect(getSpiritToolsForRuntime()).toBeUndefined();
  });

  it("SPIRIT_ENABLE_FILE_EDIT_TOOLS=true adds propose_file_edit and apply_confirmed_file_edit", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "false");
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "true");
    const tools = getSpiritToolsForRuntime();
    expect(tools).toBeDefined();
    if (!tools) throw new Error("tools");
    expect(Object.keys(tools).sort()).toEqual(
      [
        "apply_confirmed_file_edit",
        "get_system_status",
        "list_workspace_files",
        "propose_file_edit",
        "read_log_tail",
        "read_workspace_file",
      ].sort(),
    );
    expect(tools).not.toHaveProperty("execute_bash");
    expect(tools).not.toHaveProperty("terminal_execution");
  });

  it("SPIRIT_ENABLE_DEV_COMMAND_TOOLS=true adds run_dev_command when local tools enabled", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "true");
    const tools = getSpiritToolsForRuntime();
    expect(tools).toBeDefined();
    if (!tools) throw new Error("tools");
    expect(Object.keys(tools)).toContain("run_dev_command");
    expect(spiritToolsetIncludesRunDevCommand(tools)).toBe(true);
    expect(tools).not.toHaveProperty("execute_bash");
    expect(tools).not.toHaveProperty("execute_shell");
  });

  it("SPIRIT_ENABLE_DEV_COMMAND_TOOLS=false does not include run_dev_command", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "false");
    const tools = getSpiritToolsForRuntime();
    expect(tools).toBeDefined();
    if (!tools) throw new Error("tools");
    expect(tools).not.toHaveProperty("run_dev_command");
    expect(getSpiritDevCommandTools()).toEqual({});
  });

  it("file edit tools still merge when dev commands also enabled", () => {
    vi.stubEnv("SPIRIT_ENABLE_LOCAL_TOOLS", "true");
    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_DEV_COMMAND_TOOLS", "true");
    vi.stubEnv("SPIRIT_ENABLE_FILE_EDIT_TOOLS", "true");
    const tools = getSpiritToolsForRuntime();
    expect(tools).toBeDefined();
    if (!tools) throw new Error("tools");
    expect(tools).toHaveProperty("propose_file_edit");
    expect(tools).toHaveProperty("run_dev_command");
  });
});
