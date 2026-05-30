// ── tool-registry - AI SDK read-only tools gated by SPIRIT_ENABLE_LOCAL_TOOLS ──
// > Also requires SPIRIT_OLLAMA_SUPPORTS_TOOLS=true. Schema acceptance only proves
// > transport compatibility; keep local tools off until an operator probe approves
// > the exact model/tool policy.

import { tool } from "ai";
import { z } from "zod";

import type { SpiritSwarmAgentRole } from "@/lib/spirit/spirit-reasoning-patterns";
import { toolErrorFromUnknown } from "@/lib/spirit/tools/tool-safety";
import { probeOllamaChatCompletionsAcceptsToolSchema } from "@/lib/server/ollama";
import {
  proposeFileEdit,
  applyConfirmedFileEdit,
  isFileEditToolsEnvEnabled,
} from "@/lib/spirit/tools/file-edit-tools";
import {
  getAllowedDevCommandIds,
  isDevCommandToolsEnvEnabled,
  runDevCommand,
  type DevCommandId,
} from "@/lib/spirit/tools/dev-command-tools";
import {
  getSystemStatus,
  listWorkspaceFiles,
  readLogTail,
  readWorkspaceFile,
} from "@/lib/spirit/tools/workspace-tools";
import { isWindowsFsEnabled, listWindowsFiles } from "@/lib/spirit/tools/windows-workspace-tools";
import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export { isFileEditToolsEnvEnabled, isDevCommandToolsEnvEnabled };

export type SpiritRuntimeToolset = Record<string, unknown>;

/** True when streamText received run_dev_command from resolveSpiritToolsForOllamaModel. */
export function spiritToolsetIncludesRunDevCommand(
  tools: Record<string, unknown> | undefined | null,
): boolean {
  return Boolean(tools && typeof tools === "object" && "run_dev_command" in tools);
}

export function isLocalToolsEnabled(): boolean {
  return process.env.SPIRIT_ENABLE_LOCAL_TOOLS === "true";
}

/** Ollama OpenAI-compat must accept tools on /v1/chat/completions (many models do not). */
export function isOllamaToolTransportReady(): boolean {
  return process.env.SPIRIT_OLLAMA_SUPPORTS_TOOLS === "true";
}

function isSandboxToolsEnvEnabled(): boolean {
  return process.env.SPIRIT_ENABLE_SANDBOX_TOOLS === "true";
}

export function getSpiritReadOnlyTools() {
  if (!isLocalToolsEnabled()) return undefined;
  if (!isOllamaToolTransportReady()) return undefined;

  return {
    list_workspace_files: tool({
      description:
        "List files and folders in a workspace-relative directory (non-recursive). Sensitive or blocked entries are omitted.",
      inputSchema: z.object({
        directory: z
          .string()
          .optional()
          .describe('Workspace-relative directory; default is ".".'),
        maxEntries: z
          .number()
          .optional()
          .describe("Maximum entries (default 80, hard cap 200)."),
      }),
      execute: async (input) => {
        try {
          return await listWorkspaceFiles(input);
        } catch (e) {
          return toolErrorFromUnknown(e);
        }
      },
    }),
    read_workspace_file: tool({
      description:
        "Read a UTF-8 text file from the workspace (max 120 KB file size on disk; tool output may truncate at 20 KB).",
      inputSchema: z.object({
        filePath: z.string().describe("Workspace-relative path to the file."),
      }),
      execute: async (input) => {
        try {
          return await readWorkspaceFile(input);
        } catch (e) {
          return toolErrorFromUnknown(e);
        }
      },
    }),
    read_log_tail: tool({
      description:
        "Return the last lines of a UTF-8 log file (default 80 lines, max 300; output capped at 20 KB characters).",
      inputSchema: z.object({
        filePath: z.string().describe("Workspace-relative path to the log file."),
        lineCount: z
          .number()
          .optional()
          .describe("How many trailing lines to return."),
      }),
      execute: async (input) => {
        try {
          return await readLogTail(input);
        } catch (e) {
          return toolErrorFromUnknown(e);
        }
      },
    }),
    get_system_status: tool({
      description:
        "Summarize whether local read-only Spirit tools are enabled and which capabilities remain unavailable. Never returns raw absolute filesystem paths.",
      inputSchema: z.object({}),
      execute: async () => {
        try {
          return await getSystemStatus();
        } catch (e) {
          return toolErrorFromUnknown(e);
        }
      },
    }),
    ...(isWindowsFsEnabled()
      ? {
          list_windows_files: tool({
            description:
              "List files and folders in an allowlisted Windows absolute path via the SpiritDesktop filesystem bridge. Read-only, non-recursive, and never browses arbitrary drives.",
            inputSchema: z.object({
              path: z.string().describe("Windows absolute path such as C:\\Projects."),
              maxEntries: z
                .number()
                .optional()
                .describe("Maximum entries (default 200, hard cap 200)."),
            }),
            execute: async (input) => {
              try {
                return await listWindowsFiles(input);
              } catch (e) {
                return toolErrorFromUnknown(e);
              }
            },
          }),
        }
      : {}),
  };
}

export function getSpiritDevCommandTools() {
  if (!isLocalToolsEnabled()) return {};
  if (!isOllamaToolTransportReady()) return {};
  if (!isDevCommandToolsEnvEnabled()) return {};

  const allowed = getAllowedDevCommandIds();
  if (allowed.length === 0) return {};

  const idsTuple = allowed as [DevCommandId, ...DevCommandId[]];

  return {
    run_dev_command: tool({
      description:
        "Runs only fixed allowlisted development commands by commandId. Does not accept shell strings. Does not install packages. Does not mutate workspace source files except typical build or test caches. npm_test and npm_build require confirm: true before execution.",
      inputSchema: z.object({
        commandId: z.enum(idsTuple),
        confirm: z
          .boolean()
          .optional()
          .describe("Must be true when the command requires explicit user confirmation."),
      }),
      execute: async (input) => {
        try {
          return await runDevCommand(input);
        } catch (e) {
          return toolErrorFromUnknown(e);
        }
      },
    }),
  };
}

function getSpiritFileEditTools() {
  if (!isFileEditToolsEnvEnabled()) return {};
  return {
    propose_file_edit: tool({
      description:
        "Stage a workspace file edit for review only. Computes a diff against the current file and stores a proposal. Never writes to disk. The user must approve; apply only via apply_confirmed_file_edit with confirm true.",
      inputSchema: z.object({
        filePath: z.string().describe("Workspace-relative path to the file."),
        nextContent: z.string().describe("Full replacement UTF-8 text for the file."),
        reason: z.string().optional().describe("Short note on why this edit is suggested."),
      }),
      execute: async (input) => {
        try {
          return await proposeFileEdit(input);
        } catch (e) {
          return toolErrorFromUnknown(e);
        }
      },
    }),
    apply_confirmed_file_edit: tool({
      description:
        "Apply a previously stored proposal only when confirm is true and the user explicitly approved this proposal id. Creates a backup before overwriting. Rejects if the file changed since proposal.",
      inputSchema: z.object({
        proposalId: z.string().describe("Id returned by propose_file_edit."),
        confirm: z
          .boolean()
          .describe("Must be true to apply; false is rejected."),
      }),
      execute: async (input) => {
        try {
          return await applyConfirmedFileEdit(input);
        } catch (e) {
          return toolErrorFromUnknown(e);
        }
      },
    }),
  };
}

function getSpiritSandboxTools() {
  if (!isLocalToolsEnabled()) return {};
  if (!isOllamaToolTransportReady()) return {};
  if (!isSandboxToolsEnvEnabled()) return {};

  return {
    sandbox_terminal_run: tool({
      description:
        "Run a bounded command through the Source proxy Bubblewrap sandbox for verification. Accepts argv arrays only, uses the read-only workspace mount, and returns stdout/stderr without granting arbitrary shell access.",
      inputSchema: z.object({
        command: z
          .array(z.string())
          .min(1)
          .max(32)
          .describe("Command argv to run in the Bubblewrap sandbox."),
        timeoutSeconds: z
          .number()
          .optional()
          .describe("Timeout in seconds, clamped by the proxy to 30 seconds."),
        networkPolicy: z
          .enum(["none", "trusted_command"])
          .optional()
          .describe("Network policy for the sandbox; default is none."),
      }),
      execute: async (input) => {
        try {
          return await runSandboxTerminalViaSourceProxy(input);
        } catch (e) {
          return toolErrorFromUnknown(e);
        }
      },
    }),
  };
}

export function getSpiritToolsForRuntime() {
  const readOnly = getSpiritReadOnlyTools();
  if (!readOnly) return undefined;
  return {
    ...readOnly,
    ...getSpiritFileEditTools(),
    ...getSpiritDevCommandTools(),
    ...getSpiritSandboxTools(),
  };
}

export function getSpiritToolsForSwarmRole(
  role?: SpiritSwarmAgentRole | string | null,
): SpiritRuntimeToolset | undefined {
  const normalizedRole = normalizeSwarmToolRole(role);
  if (!normalizedRole) {
    return getSpiritToolsForRuntime();
  }

  if (normalizedRole === "architect") {
    return getSpiritReadOnlyTools();
  }

  if (normalizedRole === "coder") {
    if (!isLocalToolsEnabled()) return undefined;
    if (!isOllamaToolTransportReady()) return undefined;
    const fileEditTools = getSpiritFileEditTools();
    return Object.keys(fileEditTools).length > 0 ? fileEditTools : undefined;
  }

  if (!isLocalToolsEnabled()) return undefined;
  if (!isOllamaToolTransportReady()) return undefined;
  const sandboxTools = getSpiritSandboxTools();
  return Object.keys(sandboxTools).length > 0 ? sandboxTools : undefined;
}

const modelToolSchemaSupported = new Map<string, boolean>();

/** Clears per-model probe cache (tests only). */
export function clearReadOnlyToolProbeCache(): void {
  modelToolSchemaSupported.clear();
}

/**
 * Returns read-only tools only when env flags allow and Ollama accepts a tools payload for this model.
 * Result is cached per model id for the lifetime of the Node process.
 */
export async function resolveSpiritToolsForOllamaModel(
  modelId: string,
  opts?: { swarmAgentRole?: SpiritSwarmAgentRole | string | null },
): Promise<SpiritRuntimeToolset | undefined> {
  const tools = getSpiritToolsForSwarmRole(opts?.swarmAgentRole);
  if (!tools) return undefined;

  const cached = modelToolSchemaSupported.get(modelId);
  if (cached === false) return undefined;
  if (cached === true) return tools;

  let supported = true;
  try {
    supported = await probeOllamaChatCompletionsAcceptsToolSchema(modelId);
  } catch {
    supported = true;
  }
  modelToolSchemaSupported.set(modelId, supported);
  return supported ? tools : undefined;
}

function normalizeSwarmToolRole(
  role?: SpiritSwarmAgentRole | string | null,
): SpiritSwarmAgentRole | null {
  const normalized = role?.trim().toLowerCase();
  if (
    normalized === "architect" ||
    normalized === "coder" ||
    normalized === "debugger"
  ) {
    return normalized;
  }
  return null;
}

async function runSandboxTerminalViaSourceProxy(input: {
  command: string[];
  timeoutSeconds?: number;
  networkPolicy?: "none" | "trusted_command";
}) {
  const response = await sourceProxyFetch("/v1/sandbox/terminal/run", {
    body: JSON.stringify({
      command: input.command,
      timeout_seconds: input.timeoutSeconds,
      network_policy: input.networkPolicy ?? "none",
    }),
    headers: { "content-type": "application/json" },
    method: "POST",
  });

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    return {
      ok: false,
      code: "SANDBOX_PROXY_ERROR",
      status: response.status,
      payload,
    };
  }
  return payload;
}
