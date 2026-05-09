import "server-only";

import path from "path";

const WINDOWS_LIST_DEFAULT_MAX = 200;
const WINDOWS_LIST_HARD_CAP = 200;

export type WindowsFileEntry = {
  name: string;
  type: "file" | "directory";
  sizeBytes: number | null;
  modifiedAt: string | null;
};

export type ListWindowsFilesResult =
  | {
      ok: true;
      path: string;
      entries: WindowsFileEntry[];
      truncated: boolean;
    }
  | {
      ok: false;
      code:
        | "WINDOWS_FS_DISABLED"
        | "WINDOWS_FS_CONFIG_MISSING"
        | "PATH_NOT_ALLOWLISTED"
        | "PATH_BLOCKED"
        | "WINDOWS_AGENT_UNREACHABLE"
        | "TOKEN_REJECTED"
        | "WINDOWS_AGENT_FS_ENDPOINT_MISSING"
        | "WINDOWS_AGENT_ERROR";
      message: string;
    };

type WindowsAgentErrorBody = {
  ok?: false;
  code?: string;
  message?: string;
  error?: string;
};

const BLOCKED_WINDOWS_DIRS = new Set([
  "node_modules",
  ".git",
  ".next",
  "dist",
  "build",
  "coverage",
  ".turbo",
  ".cache",
]);

function matchesBlockedBasename(name: string): boolean {
  const lower = name.toLowerCase();
  if (lower.startsWith(".")) return true;
  if (lower === ".env" || lower.startsWith(".env.")) return true;
  if (lower.endsWith(".pem") || lower.endsWith(".key")) return true;
  if (lower === "id_rsa" || lower === "id_ed25519") return true;
  if (lower.startsWith("secrets.") || lower.startsWith("credentials.")) return true;
  return false;
}

export function isWindowsFsEnabled(): boolean {
  return process.env.SPIRIT_WINDOWS_FS_ENABLED === "true";
}

export function normalizeWindowsRequestPath(inputPath: string): string | null {
  if (typeof inputPath !== "string") return null;
  let s = inputPath.trim().replace(/^my\s+/i, "");
  s = s.replace(/^[`"']+/, "").replace(/[`"'.,;:!?]+$/, "").trim();
  s = s.replace(/\s+(folder|directory|dir)\s*$/i, "").trim();
  s = s.replace(/\//g, "\\");
  const driveSlash = s.match(/^([a-z])\\(.+)$/i);
  if (driveSlash) {
    s = `${driveSlash[1]!.toUpperCase()}:\\${driveSlash[2]}`;
  } else {
    s = s.replace(/^([a-z]):/i, (_, d: string) => `${d.toUpperCase()}:`);
  }
  if (!/^[A-Z]:\\/i.test(s)) return null;
  return path.win32.resolve(s);
}

function parseAllowlist(): string[] {
  const raw = process.env.SPIRIT_WINDOWS_FS_ALLOWLIST ?? "";
  return raw
    .split(/[,\n]+/)
    .map((p) => normalizeWindowsRequestPath(p))
    .filter((p): p is string => p != null && !/^[A-Z]:\\?$/i.test(p))
}

function isWithinRoot(child: string, root: string): boolean {
  const c = path.win32.normalize(child).toLowerCase();
  const r = path.win32.normalize(root).toLowerCase();
  const rWithSep = r.endsWith("\\") ? r : `${r}\\`;
  return c === r || c.startsWith(rWithSep);
}

export function isWindowsPathAllowlisted(inputPath: string): boolean {
  const normalized = normalizeWindowsRequestPath(inputPath);
  if (!normalized) return false;
  return parseAllowlist().some((root) => isWithinRoot(normalized, root));
}

function isBlockedWindowsPath(inputPath: string): boolean {
  const normalized = normalizeWindowsRequestPath(inputPath);
  if (!normalized) return true;
  const withoutDrive = normalized.replace(/^[A-Z]:\\/i, "");
  const parts = withoutDrive.split("\\").filter(Boolean);
  for (const part of parts) {
    if (BLOCKED_WINDOWS_DIRS.has(part.toLowerCase())) return true;
    if (matchesBlockedBasename(part)) return true;
  }
  return false;
}

function maxEntriesFromInput(maxEntries: number | undefined): number {
  if (!Number.isFinite(maxEntries) || maxEntries == null || maxEntries < 1) {
    return WINDOWS_LIST_DEFAULT_MAX;
  }
  return Math.min(Math.floor(maxEntries), WINDOWS_LIST_HARD_CAP);
}

export function normalizeWindowsFsBaseUrl(rawUrl: string): string | null {
  const trimmed = rawUrl.trim();
  if (!trimmed) return null;
  const withoutAngleBrackets = trimmed.replace(/<([^/?#]+)>/g, "$1");
  try {
    const parsed = new URL(withoutAngleBrackets);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return null;
    parsed.pathname = parsed.pathname.replace(/\/+$/, "");
    parsed.search = "";
    parsed.hash = "";
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

export async function listWindowsFiles(input: {
  path: string;
  maxEntries?: number;
}): Promise<ListWindowsFilesResult> {
  if (!isWindowsFsEnabled()) {
    return {
      ok: false,
      code: "WINDOWS_FS_DISABLED",
      message:
        "Windows folder access is disabled. Enable SPIRIT_WINDOWS_FS_ENABLED and configure SPIRIT_WINDOWS_FS_BASE_URL, SPIRIT_WINDOWS_FS_TOKEN, and SPIRIT_WINDOWS_FS_ALLOWLIST.",
    };
  }

  const baseUrl = normalizeWindowsFsBaseUrl(process.env.SPIRIT_WINDOWS_FS_BASE_URL ?? "");
  const token = process.env.SPIRIT_WINDOWS_FS_TOKEN?.trim();
  if (!baseUrl || !token) {
    return {
      ok: false,
      code: "WINDOWS_FS_CONFIG_MISSING",
      message:
        "Windows folder access is missing or has an invalid SPIRIT_WINDOWS_FS_BASE_URL or SPIRIT_WINDOWS_FS_TOKEN. Use a URL like http://10.0.0.126:3000 without angle brackets.",
    };
  }

  const requestedPath = normalizeWindowsRequestPath(input.path);
  if (!requestedPath) {
    return {
      ok: false,
      code: "PATH_BLOCKED",
      message: "That Windows path is not a supported absolute drive path.",
    };
  }

  if (isBlockedWindowsPath(requestedPath)) {
    return {
      ok: false,
      code: "PATH_BLOCKED",
      message: "That Windows path is blocked by the filesystem safety rules.",
    };
  }

  if (!isWindowsPathAllowlisted(requestedPath)) {
    return {
      ok: false,
      code: "PATH_NOT_ALLOWLISTED",
      message: "That path is outside the configured Windows filesystem allowlist.",
    };
  }

  const endpoint = new URL("/api/files/list", baseUrl).toString();
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        path: requestedPath,
        maxEntries: maxEntriesFromInput(input.maxEntries),
      }),
    });

    if (res.status === 401 || res.status === 403) {
      return {
        ok: false,
        code: "TOKEN_REJECTED",
        message: "The Windows agent rejected the bearer token.",
      };
    }

    const body = (await res.json().catch(() => null)) as
      | Extract<ListWindowsFilesResult, { ok: true }>
      | WindowsAgentErrorBody
      | null;

    if (res.status === 404) {
      return {
        ok: false,
        code: "WINDOWS_AGENT_FS_ENDPOINT_MISSING",
        message:
          "The Windows agent is reachable, but it does not expose /api/files/list. Copy the updated scripts/spiritdesktop-windows/agent.js to the Windows machine and restart node agent.js.",
      };
    }

    if (body && body.ok === false) {
      const errorBody = body as WindowsAgentErrorBody;
      const code =
        errorBody.code === "WINDOWS_FS_DISABLED" ||
        errorBody.code === "WINDOWS_FS_CONFIG_MISSING" ||
        errorBody.code === "PATH_NOT_ALLOWLISTED" ||
        errorBody.code === "PATH_BLOCKED"
          ? errorBody.code
          : "WINDOWS_AGENT_ERROR";
      return {
        ok: false,
        code,
        message:
          errorBody.message ??
          errorBody.error ??
          "The Windows agent blocked that filesystem request.",
      };
    }

    if (!res.ok || !body) {
      return {
        ok: false,
        code: "WINDOWS_AGENT_ERROR",
        message: `The Windows agent returned an invalid filesystem response (HTTP ${res.status}).`,
      };
    }

    if (body.ok === true) return body;

    return {
      ok: false,
      code: "WINDOWS_AGENT_ERROR",
      message: "The Windows agent returned a filesystem response without ok=true.",
    };
  } catch {
    return {
      ok: false,
      code: "WINDOWS_AGENT_UNREACHABLE",
      message: "The Windows agent is unreachable at SPIRIT_WINDOWS_FS_BASE_URL.",
    };
  }
}
