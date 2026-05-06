// ── tool-safety - path + output guards for read-only Spirit workspace tools ──
// > No shell, no writes, no leaking cwd paths into model-facing JSON.

import path from "path";

export const TOOL_MAX_FILE_BYTES = 120 * 1024;
export const TOOL_MAX_OUTPUT_CHARS = 20 * 1024;

export const BLOCKED_WORKSPACE_DIRS = [
  "node_modules",
  ".git",
  ".next",
  "dist",
  "build",
  "coverage",
  ".turbo",
  ".vercel",
  ".cache",
] as const;

/** Human-readable patterns; matching logic is in matchesBlockedFileBasename. */
export const BLOCKED_WORKSPACE_FILE_PATTERNS = [
  ".env",
  ".env.*",
  "*.pem",
  "*.key",
  "id_rsa",
  "id_ed25519",
  "secrets.*",
  "credentials.*",
  "service-account*.json",
] as const;

export type ToolSafeError = {
  ok: false;
  code: string;
  message: string;
};

export class SpiritToolPathError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "SpiritToolPathError";
    this.code = code;
  }
}

export function createToolError(code: string, message: string): ToolSafeError {
  return { ok: false, code, message };
}

export function getWorkspaceRoot(): string {
  const raw = process.env.SPIRIT_PROJECT_PATH?.trim();
  const base = raw && raw.length > 0 ? raw : process.cwd();
  return path.resolve(base);
}

function workspaceRootForChecks(): string {
  return path.normalize(getWorkspaceRoot());
}

export function isBlockedPathSegment(segment: string): boolean {
  return (BLOCKED_WORKSPACE_DIRS as readonly string[]).includes(segment);
}

export function matchesBlockedFileBasename(basename: string): boolean {
  const lower = basename.toLowerCase();
  if (lower === ".env") return true;
  if (lower.startsWith(".env.")) return true;
  if (lower.endsWith(".pem")) return true;
  if (lower.endsWith(".key")) return true;
  if (basename === "id_rsa" || basename === "id_ed25519") return true;
  if (lower.startsWith("secrets.")) return true;
  if (lower.startsWith("credentials.")) return true;
  if (/^service-account.*\.json$/i.test(basename)) return true;
  return false;
}

/**
 * Returns a workspace-relative path using forward slashes for stable tool output.
 * Throws SpiritToolPathError when input is not a safe relative path.
 */
export function normalizeWorkspaceRelativePath(inputPath: string): string {
  if (typeof inputPath !== "string") {
    throw new SpiritToolPathError("INVALID_PATH", "Path must be a string.");
  }

  const trimmed = inputPath.trim();
  if (trimmed === "") {
    throw new SpiritToolPathError("INVALID_PATH", "Path cannot be empty.");
  }

  if (path.isAbsolute(trimmed)) {
    throw new SpiritToolPathError("ABSOLUTE_PATH_NOT_ALLOWED", "Absolute paths are not allowed.");
  }

  const cleaned = trimmed.replace(/^[/\\]+/, "");
  const segments = cleaned.split(/[/\\]+/).filter((s) => s !== "." && s !== "");
  for (const seg of segments) {
    if (seg === "..") {
      throw new SpiritToolPathError("PATH_TRAVERSAL", "Path traversal is not allowed.");
    }
  }

  const normalized = segments.length === 0 ? "." : segments.join(path.sep);

  const relParts = normalized === "." ? [] : normalized.split(path.sep);
  for (const part of relParts) {
    if (part !== "." && isBlockedPathSegment(part)) {
      throw new SpiritToolPathError("BLOCKED_SEGMENT", `Blocked path segment: ${part}`);
    }
    if (matchesBlockedFileBasename(part)) {
      throw new SpiritToolPathError("BLOCKED_FILE_PATTERN", "That file pattern is blocked.");
    }
  }

  return normalized;
}

export function resolveSafeWorkspacePath(inputPath: string): string {
  const relative = normalizeWorkspaceRelativePath(inputPath);
  const root = workspaceRootForChecks();
  const full =
    relative === "."
      ? root
      : path.resolve(path.join(root, relative));

  const rootWithSep = root.endsWith(path.sep) ? root : `${root}${path.sep}`;
  const normalizedFull = path.normalize(full);
  if (normalizedFull !== root && !normalizedFull.startsWith(rootWithSep)) {
    throw new SpiritToolPathError("OUTSIDE_WORKSPACE", "Path resolves outside the workspace root.");
  }

  return normalizedFull;
}

export function assertSafeWorkspacePath(inputPath: string): void {
  resolveSafeWorkspacePath(inputPath);
}

export function truncateToolOutput(text: string, maxChars: number): { text: string; truncated: boolean } {
  if (text.length <= maxChars) {
    return { text, truncated: false };
  }
  return {
    text: text.slice(0, maxChars) + "\n... [truncated]",
    truncated: true,
  };
}

export function isSpiritToolPathError(err: unknown): err is SpiritToolPathError {
  return err instanceof SpiritToolPathError;
}

export function toolErrorFromUnknown(err: unknown): ToolSafeError {
  if (err && typeof err === "object" && "ok" in err && (err as ToolSafeError).ok === false) {
    const e = err as ToolSafeError;
    return createToolError(e.code, e.message);
  }
  if (isSpiritToolPathError(err)) {
    return createToolError(err.code, err.message);
  }
  return createToolError("TOOL_ERROR", "The tool could not complete safely.");
}
