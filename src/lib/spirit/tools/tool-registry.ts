// ── tool-registry - AI SDK read-only tools gated by SPIRIT_ENABLE_LOCAL_TOOLS ──
// > Also requires SPIRIT_OLLAMA_SUPPORTS_TOOLS=true: Hermes4 and many registry pulls
// > reject requests with tools ("does not support tools"); opt in after switching models.

import { tool } from "ai";
import { z } from "zod";

import { toolErrorFromUnknown } from "@/lib/spirit/tools/tool-safety";
import { probeOllamaChatCompletionsAcceptsToolSchema } from "@/lib/server/ollama";
import {
  getSystemStatus,
  listWorkspaceFiles,
  readLogTail,
  readWorkspaceFile,
} from "@/lib/spirit/tools/workspace-tools";

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

export function getSpiritToolsForRuntime() {
  return getSpiritReadOnlyTools();
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
): Promise<ReturnType<typeof getSpiritReadOnlyTools>> {
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
