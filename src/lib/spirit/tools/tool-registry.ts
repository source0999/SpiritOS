// ── tool-registry - AI SDK read-only tools gated by SPIRIT_ENABLE_LOCAL_TOOLS ──
// > Also requires SPIRIT_OLLAMA_SUPPORTS_TOOLS=true: Hermes4 and many registry pulls
// > reject requests with tools ("does not support tools"); opt in after switching models.

import { tool } from "ai";
import { z } from "zod";

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

export { isFileEditToolsEnvEnabled, isDevCommandToolsEnvEnabled };

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

export function getSpiritToolsForRuntime() {
  const readOnly = getSpiritReadOnlyTools();
  if (!readOnly) return undefined;
  return { ...readOnly, ...getSpiritFileEditTools(), ...getSpiritDevCommandTools() };
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
): Promise<ReturnType<typeof getSpiritToolsForRuntime>> {
  const tools = getSpiritToolsForRuntime();
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
