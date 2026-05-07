// ── direct-workspace-request - Phase 4B: read-only workspace without LLM tool calls ─
// > Same path discipline as tools; never leaks workspace root; uses workspace-tools only.

import "server-only";

import { pathFragmentLooksConcrete } from "@/lib/spirit/concrete-workspace-read-request";
import {
  createSpiritToolActivityCard,
  type SpiritToolActivityCard,
} from "@/lib/spirit/spirit-activity-events";
import {
  listWorkspaceFiles,
  readLogTail,
  readWorkspaceFile,
} from "@/lib/spirit/tools/workspace-tools";
import { isLocalToolsEnabled } from "@/lib/spirit/tools/tool-registry";

function trimPathFragment(fragment: string): string {
  return fragment.replace(/^[`"'“”]+/, "").replace(/[`"'“”.,;:!?]+$/, "").trim();
}

export type DirectWorkspaceRequest =
  | { kind: "list"; directory: string }
  | { kind: "read"; filePath: string }
  | { kind: "tail"; filePath: string; lineCount?: number };

export type DirectWorkspaceHandleResult = {
  markdown: string;
  toolActivity: SpiritToolActivityCard[];
};

function fenceLang(filePath: string): string {
  const lower = filePath.toLowerCase();
  if (lower.endsWith(".json")) return "json";
  if (/\.(ts|tsx|mts|cts)$/.test(lower)) return "typescript";
  if (/\.(js|jsx|mjs|cjs)$/.test(lower)) return "javascript";
  if (/\.(md|mdx)$/.test(lower)) return "markdown";
  if (/\.(ya?ml|toml)$/.test(lower)) return "yaml";
  if (/\.(css|html|svg)$/.test(lower)) return "text";
  if (lower.endsWith(".log") || lower.endsWith(".txt")) return "text";
  return "text";
}

/**
 * Parse a concrete list/read/tail request; returns null for vague asks or blocked intents.
 * Mirrors `isConcreteWorkspaceReadRequest` extraction logic.
 */
export function parseDirectWorkspaceRequest(text: string): DirectWorkspaceRequest | null {
  const raw = text.trim();
  if (raw.length < 6) return null;
  const lower = raw.toLowerCase();

  if (
    /\b(run|execute|exec|bash|shell|terminal|sudo|npm\s+(test|run|install|ci|start|dev|exec)|pnpm\s|yarn\s+(test|install|add))\b/i.test(
      lower,
    )
  ) {
    return null;
  }

  if (/\b(edit|delete|write|create|mkdir|rm\s|mv\s|cp\s)\s+/i.test(lower)) return null;

  const lastLines = raw.match(
    /\bshow\s+(the\s+)?(last|past)\s+(\d+)\s+lines\s+of\s+([^\s?!,]+)/i,
  );
  if (lastLines?.[4]) {
    const pathPart = trimPathFragment(lastLines[4]);
    if (!pathFragmentLooksConcrete(pathPart)) return null;
    const n = Number.parseInt(lastLines[3] ?? "", 10);
    const lineCount = Number.isFinite(n) && n > 0 ? n : undefined;
    return { kind: "tail", filePath: pathPart, lineCount };
  }

  const tailM = raw.match(/\btail\s+([^\s?!,]+)/i);
  if (tailM?.[1]) {
    const pathPart = trimPathFragment(tailM[1]);
    if (!pathFragmentLooksConcrete(pathPart)) return null;
    return { kind: "tail", filePath: pathPart };
  }

  const listFilesIn = raw.match(/\blist\s+(the\s+)?files?\s+in\s+([^\s?!,]+)/i);
  if (listFilesIn?.[2]) {
    const pathPart = trimPathFragment(listFilesIn[2]);
    if (!pathFragmentLooksConcrete(pathPart)) return null;
    return { kind: "list", directory: pathPart };
  }

  const listDir = raw.match(/\blist\s+(the\s+)?(directory|dir)\s+([^\s?!,]+)/i);
  if (listDir?.[3]) {
    const pathPart = trimPathFragment(listDir[3]);
    if (!pathFragmentLooksConcrete(pathPart)) return null;
    return { kind: "list", directory: pathPart };
  }

  const showFilesIn = raw.match(/\bshow\s+(the\s+)?files?\s+in\s+([^\s?!,]+)/i);
  if (showFilesIn?.[2]) {
    const pathPart = trimPathFragment(showFilesIn[2]);
    if (!pathFragmentLooksConcrete(pathPart)) return null;
    return { kind: "list", directory: pathPart };
  }

  const showContents = raw.match(/\bshow\s+(the\s+)?contents\s+of\s+([^\s?!,]+)/i);
  if (showContents?.[2]) {
    const pathPart = trimPathFragment(showContents[2]);
    if (!pathFragmentLooksConcrete(pathPart)) return null;
    return { kind: "read", filePath: pathPart };
  }

  const readFile = raw.match(/\bread\s+([^\s?!,]+)/i);
  if (readFile?.[1] && !/^(files?|folders?|directories?)$/i.test(readFile[1])) {
    const pathPart = trimPathFragment(readFile[1]);
    if (!pathFragmentLooksConcrete(pathPart)) return null;
    return { kind: "read", filePath: pathPart };
  }

  const openFile = raw.match(/\bopen\s+([^\s?!,]+)/i);
  if (openFile?.[1]) {
    const pathPart = trimPathFragment(openFile[1]);
    if (!pathFragmentLooksConcrete(pathPart)) return null;
    return { kind: "read", filePath: pathPart };
  }

  return null;
}

function formatListSuccess(
  directory: string,
  r: Extract<Awaited<ReturnType<typeof listWorkspaceFiles>>, { ok: true }>,
): string {
  const header = `Files in ${directory}:`;
  const lines = r.entries.map((e) => {
    const suffix = e.type === "directory" ? "/" : "";
    return `- ${e.name}${suffix}`;
  });
  const trunc = r.truncated ? "\n\n(listing truncated to cap)" : "";
  return [header, ...lines].join("\n") + trunc;
}

function formatReadSuccess(
  labelPath: string,
  content: string,
  truncated: boolean,
): string {
  const lang = fenceLang(labelPath);
  const fence = "```" + lang + "\n" + content + "\n```";
  const trunc = truncated ? "\n\n(Output was truncated to the tool character cap.)" : "";
  return `Contents of ${labelPath}:\n${fence}${trunc}`;
}

function formatTailSuccess(
  filePath: string,
  lines: string[],
  requestedLines: number | undefined,
  truncated: boolean,
): string {
  const header =
    requestedLines != null
      ? `Last ${requestedLines} lines of ${filePath}:`
      : `Tail of ${filePath} (${lines.length} lines shown):`;
  const body = lines.join("\n");
  const fence = "```text\n" + body + "\n```";
  const trunc = truncated ? "\n\n(Output was truncated to the tool character cap.)" : "";
  return `${header}\n${fence}${trunc}`;
}

function formatToolError(message: string): string {
  return `I could not read that path: ${message}`;
}

/**
 * Execute a parsed concrete read-only workspace operation and return assistant markdown,
 * or null when this text does not map to a direct request or local tools are disabled.
 */
export async function handleDirectWorkspaceRequest(
  text: string,
): Promise<DirectWorkspaceHandleResult | null> {
  if (!isLocalToolsEnabled()) return null;

  const parsed = parseDirectWorkspaceRequest(text);
  if (!parsed) return null;

  if (parsed.kind === "list") {
    const r = await listWorkspaceFiles({ directory: parsed.directory });
    if (!r.ok) {
      return {
        markdown: formatToolError(r.message),
        toolActivity: [
          createSpiritToolActivityCard({
            kind: "tool_blocked",
            label: "List workspace files",
            status: "blocked",
            target: parsed.directory,
            safeMessage: r.message,
          }),
        ],
      };
    }
    return {
      markdown: formatListSuccess(parsed.directory, r),
      toolActivity: [
        createSpiritToolActivityCard({
          kind: "workspace_list",
          label: "List workspace files",
          status: "completed",
          target: parsed.directory,
          summary: `${r.entries.length} entr${r.entries.length === 1 ? "y" : "ies"}${r.truncated ? ", truncated" : ""}`,
        }),
      ],
    };
  }

  if (parsed.kind === "read") {
    const r = await readWorkspaceFile({ filePath: parsed.filePath });
    if (!r.ok) {
      return {
        markdown: formatToolError(r.message),
        toolActivity: [
          createSpiritToolActivityCard({
            kind: "tool_blocked",
            label: "Read workspace file",
            status: "blocked",
            target: parsed.filePath,
            safeMessage: r.message,
          }),
        ],
      };
    }
    const label = r.filePath;
    return {
      markdown: formatReadSuccess(label, r.content, r.truncated),
      toolActivity: [
        createSpiritToolActivityCard({
          kind: "workspace_read",
          label: "Read workspace file",
          status: "completed",
          target: label,
          summary: r.truncated ? "Content truncated in output" : "Read OK",
        }),
      ],
    };
  }

  const r = await readLogTail({
    filePath: parsed.filePath,
    lineCount: parsed.lineCount,
  });
  if (!r.ok) {
    return {
      markdown: formatToolError(r.message),
      toolActivity: [
        createSpiritToolActivityCard({
          kind: "tool_blocked",
          label: "Tail log file",
          status: "blocked",
          target: parsed.filePath,
          safeMessage: r.message,
        }),
      ],
    };
  }
  return {
    markdown: formatTailSuccess(r.filePath, r.lines, parsed.lineCount, r.truncated),
    toolActivity: [
      createSpiritToolActivityCard({
        kind: "workspace_tail",
        label: "Tail log file",
        status: "completed",
        target: r.filePath,
        summary: `${r.lines.length} lines${r.truncated ? ", truncated" : ""}`,
      }),
    ],
  };
}
