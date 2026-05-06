// ── workspace-tools - read-only listings and file reads for Hermes Phase 4 ──
// > fs/promises only. No shell. Paths go through tool-safety first.

import { promises as fs } from "fs";
import path from "path";

import {
  TOOL_MAX_FILE_BYTES,
  TOOL_MAX_OUTPUT_CHARS,
  SpiritToolPathError,
  isBlockedPathSegment,
  matchesBlockedFileBasename,
  normalizeWorkspaceRelativePath,
  resolveSafeWorkspacePath,
  truncateToolOutput,
} from "@/lib/spirit/tools/tool-safety";

const LIST_DEFAULT_MAX = 80;
const LIST_HARD_CAP = 200;
const LOG_TAIL_DEFAULT_LINES = 80;
const LOG_TAIL_MAX_LINES = 300;
/** Bytes read from disk when tailing logs (tail extraction only). */
const LOG_TAIL_READ_MAX_BYTES = 512 * 1024;

function isBlockedWorkspaceEntryName(name: string): boolean {
  if (name === "." || name === "..") return true;
  if (isBlockedPathSegment(name)) return true;
  if (matchesBlockedFileBasename(name)) return true;
  return false;
}

function assertUtf8TextBuffer(buf: Buffer): void {
  if (buf.includes(0)) {
    throw new SpiritToolPathError("NOT_TEXT_FILE", "Only UTF-8 text files are allowed.");
  }
}

export type ListWorkspaceFilesInput = {
  directory?: string;
  maxEntries?: number;
};

export async function listWorkspaceFiles(
  input: ListWorkspaceFilesInput,
): Promise<
  | {
      ok: true;
      directory: string;
      entries: Array<{
        name: string;
        type: "file" | "directory" | "symlink" | "other";
        size?: number;
        modifiedAt?: string;
      }>;
      truncated: boolean;
    }
  | { ok: false; code: string; message: string }
> {
  try {
    const dirRel = normalizeWorkspaceRelativePath(input.directory ?? ".");
    const dirAbs = resolveSafeWorkspacePath(dirRel);

    const stat = await fs.stat(dirAbs);
    if (!stat.isDirectory()) {
      return { ok: false, code: "NOT_A_DIRECTORY", message: "Path is not a directory." };
    }

    let maxEntries = input.maxEntries ?? LIST_DEFAULT_MAX;
    if (!Number.isFinite(maxEntries) || maxEntries < 1) {
      maxEntries = LIST_DEFAULT_MAX;
    }
    maxEntries = Math.min(Math.floor(maxEntries), LIST_HARD_CAP);

    const dirents = await fs.readdir(dirAbs, { withFileTypes: true });
    const safe: typeof dirents = [];
    for (const d of dirents) {
      if (isBlockedWorkspaceEntryName(d.name)) continue;
      const childRel = dirRel === "." ? d.name : `${dirRel}${path.sep}${d.name}`;
      try {
        resolveSafeWorkspacePath(childRel);
        safe.push(d);
      } catch {
        // Symlink escape or odd entry: skip rather than leak errors.
        continue;
      }
    }

    safe.sort((a, b) => a.name.localeCompare(b.name));
    const truncated = safe.length > maxEntries;
    const slice = safe.slice(0, maxEntries);

    const entries: Array<{
      name: string;
      type: "file" | "directory" | "symlink" | "other";
      size?: number;
      modifiedAt?: string;
    }> = [];

    for (const d of slice) {
      const childPath = path.join(dirAbs, d.name);
      let type: "file" | "directory" | "symlink" | "other" = "other";
      if (d.isDirectory()) type = "directory";
      else if (d.isFile()) type = "file";
      else if (d.isSymbolicLink()) type = "symlink";

      let size: number | undefined;
      let modifiedAt: string | undefined;
      try {
        const st = await fs.stat(childPath);
        size = st.size;
        modifiedAt = st.mtime.toISOString();
      } catch {
        /* optional metadata */
      }

      entries.push({ name: d.name, type, size, modifiedAt });
    }

    return {
      ok: true,
      directory: dirRel === "." ? "." : dirRel.split(path.sep).join("/"),
      entries,
      truncated,
    };
  } catch (e) {
    if (e instanceof SpiritToolPathError) {
      return { ok: false, code: e.code, message: e.message };
    }
    return { ok: false, code: "LIST_FAILED", message: "Could not list directory." };
  }
}

export type ReadWorkspaceFileInput = {
  filePath: string;
};

export async function readWorkspaceFile(
  input: ReadWorkspaceFileInput,
): Promise<
  | {
      ok: true;
      filePath: string;
      content: string;
      size: number;
      truncated: boolean;
    }
  | { ok: false; code: string; message: string }
> {
  try {
    const rel = normalizeWorkspaceRelativePath(input.filePath);
    const abs = resolveSafeWorkspacePath(rel);

    const stat = await fs.stat(abs);
    if (!stat.isFile()) {
      return { ok: false, code: "NOT_A_FILE", message: "Path is not a file." };
    }
    if (stat.size > TOOL_MAX_FILE_BYTES) {
      return {
        ok: false,
        code: "FILE_TOO_LARGE",
        message: `File exceeds maximum size of ${TOOL_MAX_FILE_BYTES} bytes.`,
      };
    }

    const buf = await fs.readFile(abs);
    assertUtf8TextBuffer(buf);
    const raw = buf.toString("utf8");
    const out = truncateToolOutput(raw, TOOL_MAX_OUTPUT_CHARS);

    return {
      ok: true,
      filePath: rel.split(path.sep).join("/"),
      content: out.text,
      size: stat.size,
      truncated: out.truncated,
    };
  } catch (e) {
    if (e instanceof SpiritToolPathError) {
      return { ok: false, code: e.code, message: e.message };
    }
    return { ok: false, code: "READ_FAILED", message: "Could not read file." };
  }
}

export type ReadLogTailInput = {
  filePath: string;
  lineCount?: number;
};

export async function readLogTail(
  input: ReadLogTailInput,
): Promise<
  | {
      ok: true;
      filePath: string;
      lines: string[];
      lineCount: number;
      truncated: boolean;
    }
  | { ok: false; code: string; message: string }
> {
  try {
    const rel = normalizeWorkspaceRelativePath(input.filePath);
    const abs = resolveSafeWorkspacePath(rel);

    const stat = await fs.stat(abs);
    if (!stat.isFile()) {
      return { ok: false, code: "NOT_A_FILE", message: "Path is not a file." };
    }

    let wantLines = input.lineCount ?? LOG_TAIL_DEFAULT_LINES;
    if (!Number.isFinite(wantLines) || wantLines < 1) {
      wantLines = LOG_TAIL_DEFAULT_LINES;
    }
    wantLines = Math.min(Math.floor(wantLines), LOG_TAIL_MAX_LINES);

    const buf =
      stat.size <= LOG_TAIL_READ_MAX_BYTES
        ? await fs.readFile(abs)
        : await (async () => {
            const fh = await fs.open(abs, "r");
            try {
              const readSize = Math.min(stat.size, LOG_TAIL_READ_MAX_BYTES);
              const pos = stat.size - readSize;
              const b = Buffer.alloc(readSize);
              await fh.read(b, 0, readSize, pos);
              return b;
            } finally {
              await fh.close();
            }
          })();

    assertUtf8TextBuffer(buf);
    const text = buf.toString("utf8");
    const rawLines = text.split(/\r?\n/);
    while (rawLines.length > 0 && rawLines[rawLines.length - 1] === "") {
      rawLines.pop();
    }
    const tailLines = rawLines.slice(-wantLines);
    const joined = tailLines.join("\n");
    const capped = truncateToolOutput(joined, TOOL_MAX_OUTPUT_CHARS);
    const outLines = capped.text.split("\n");

    return {
      ok: true,
      filePath: rel.split(path.sep).join("/"),
      lines: outLines,
      lineCount: outLines.length,
      truncated: capped.truncated || stat.size > LOG_TAIL_READ_MAX_BYTES,
    };
  } catch (e) {
    if (e instanceof SpiritToolPathError) {
      return { ok: false, code: e.code, message: e.message };
    }
    return { ok: false, code: "READ_FAILED", message: "Could not read log file." };
  }
}

const READ_ONLY_TOOL_NAMES = [
  "list_workspace_files",
  "read_workspace_file",
  "read_log_tail",
  "get_system_status",
] as const;

function isEnvTrue(name: string): boolean {
  return process.env[name] === "true";
}

export async function getSystemStatus(): Promise<{
  ok: true;
  localToolsEnabled: boolean;
  workspaceRootConfigured: boolean;
  workspaceRootSource: string;
  availableReadOnlyTools: string[];
  unavailableTools: string[];
  note: string;
}> {
  const localToolsEnabled = isEnvTrue("SPIRIT_ENABLE_LOCAL_TOOLS");
  const ollamaToolsTransport = isEnvTrue("SPIRIT_OLLAMA_SUPPORTS_TOOLS");
  const readOnlyToolsAttached = localToolsEnabled && ollamaToolsTransport;
  const workspaceRootConfigured = Boolean(process.env.SPIRIT_PROJECT_PATH?.trim());

  const unavailableTools: string[] = [];
  if (!isEnvTrue("SPIRIT_ENABLE_FILE_EDIT_TOOLS")) unavailableTools.push("file_editing");
  if (!isEnvTrue("SPIRIT_ENABLE_DEV_COMMAND_TOOLS")) unavailableTools.push("terminal_execution");
  if (!isEnvTrue("SPIRIT_ENABLE_EMAIL_TOOLS")) unavailableTools.push("email_access");
  if (!isEnvTrue("SPIRIT_ENABLE_CALENDAR_TOOLS")) unavailableTools.push("calendar_access");

  if (!readOnlyToolsAttached) {
    unavailableTools.push(...READ_ONLY_TOOL_NAMES);
  }

  const availableReadOnlyTools = readOnlyToolsAttached ? [...READ_ONLY_TOOL_NAMES] : [];

  return {
    ok: true,
    localToolsEnabled,
    workspaceRootConfigured,
    workspaceRootSource: workspaceRootConfigured ? "SPIRIT_PROJECT_PATH" : "default_process_cwd",
    availableReadOnlyTools,
    unavailableTools: [...new Set(unavailableTools)].sort(),
    note:
      "Read-only tools attach only when SPIRIT_ENABLE_LOCAL_TOOLS and SPIRIT_OLLAMA_SUPPORTS_TOOLS are true (Ollama must accept tools for your model). Paths are workspace-relative only.",
  };
}
