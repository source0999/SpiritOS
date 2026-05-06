// ── direct-dev-command-request - Phase 6B: allowlisted dev commands without LLM tools ─
// > Same safety as runDevCommand; fixed phrases only; never shell or user strings.

import "server-only";

import {
  runDevCommand,
  type DevCommandResult,
  isDevCommandToolsEnvEnabled,
} from "@/lib/spirit/tools/dev-command-tools";
import { isLocalToolsEnabled } from "@/lib/spirit/tools/tool-registry";

export type DirectDevCommandRequest =
  | { commandId: "git_status"; confirm?: boolean }
  | { commandId: "git_diff"; confirm?: boolean }
  | { commandId: "npm_typecheck"; confirm?: boolean }
  | { commandId: "npm_test"; confirm?: boolean }
  | { commandId: "npm_lint"; confirm?: boolean }
  | { commandId: "npm_build"; confirm?: boolean };

function normalizeDirectPhrase(raw: string): string {
  return raw
    .trim()
    .replace(/\s+/g, " ")
    .replace(/^please\s+/i, "")
    .replace(/[?.!]+$/g, "")
    .trim();
}

function parseConfirmFlag(raw: string): boolean {
  return /\bconfirm\s+true\b/i.test(raw) || /\byes\s+confirm\b/i.test(raw);
}

/**
 * Concrete allowlisted phrases only. Returns null when vague or unsafe.
 */
export function parseDirectDevCommandRequest(text: string): DirectDevCommandRequest | null {
  const raw = text.trim();
  if (raw.length < 4) return null;
  const lower = raw.toLowerCase();

  if (/\bnpm\s+install\b/i.test(lower)) return null;
  if (/\brm\s+-\s*rf\b/i.test(lower) || /\brm\s+-rf\b/i.test(lower)) return null;
  if (/\bcurl\b/i.test(lower)) return null;
  if (/\bprint\s+env\b/i.test(lower)) return null;
  if (/\bshow\s+secrets\b/i.test(lower)) return null;
  if (/\brun\s+this\s+command\b/i.test(lower)) return null;
  if (/^can\s+you\s+run\s+commands?\s*$/i.test(normalizeDirectPhrase(raw))) return null;
  if (/\bopen\s+terminal\b/i.test(lower)) return null;

  const confirm = parseConfirmFlag(raw);
  let work = normalizeDirectPhrase(raw).toLowerCase();
  work = work
    .replace(/\bconfirm\s+true\b/g, "")
    .replace(/\byes\s+confirm\b/g, "")
    .replace(/\s+/g, " ")
    .trim();

  if (work === "npm run build" || work === "run build") {
    return { commandId: "npm_build", ...(confirm ? { confirm: true } : {}) };
  }
  if (work === "npm run lint" || work === "run lint") {
    return { commandId: "npm_lint", ...(confirm ? { confirm: true } : {}) };
  }
  if (
    work === "npm run typecheck" ||
    work === "run npm typecheck" ||
    work === "run typecheck" ||
    work === "check types"
  ) {
    return { commandId: "npm_typecheck", ...(confirm ? { confirm: true } : {}) };
  }
  if (
    work === "run npm test" ||
    work === "run tests" ||
    work === "npx vitest run" ||
    work === "run vitest"
  ) {
    return { commandId: "npm_test", ...(confirm ? { confirm: true } : {}) };
  }
  if (
    work === "check git status" ||
    work === "show git status" ||
    work === "git status" ||
    work === "what changed in git"
  ) {
    return { commandId: "git_status", ...(confirm ? { confirm: true } : {}) };
  }
  if (work === "show git diff" || work === "git diff" || work === "show the diff") {
    return { commandId: "git_diff", ...(confirm ? { confirm: true } : {}) };
  }

  return null;
}

function formatDirectDevReply(result: DevCommandResult): string {
  if (result.requiresConfirmation) {
    const hint =
      result.commandId === "npm_test"
        ? "Run npm test confirm true"
        : result.commandId === "npm_build"
          ? "Run build confirm true"
          : "confirm true";
    return `Confirmation required before running ${result.commandId}. Reply with: ${hint}`;
  }

  if (result.error) {
    const safe =
      result.error.code === "SCRIPT_NOT_FOUND" ||
      result.error.code === "UNKNOWN_COMMAND" ||
      result.error.code === "DEV_COMMAND_TOOLS_DISABLED"
        ? result.error.message
        : "That command could not be run from this shortcut.";
    return safe;
  }

  const body = (result.output ?? "").trim();
  const label = result.label;

  if (result.timedOut || result.ok === false) {
    const exit = result.exitCode ?? "unknown";
    return [
      `Dev command failed: ${label}`,
      `Exit code: ${exit}`,
      "",
      "```text",
      body || result.message || "(no output)",
      "```",
    ].join("\n");
  }

  return [`Dev command: ${label}`, "", "```text", body || "(no output)", "```"].join("\n");
}

export async function handleDirectDevCommandRequest(text: string): Promise<string | null> {
  if (!isDevCommandToolsEnvEnabled()) return null;
  if (!isLocalToolsEnabled()) return null;

  const parsed = parseDirectDevCommandRequest(text);
  if (!parsed) return null;

  const result = await runDevCommand({
    commandId: parsed.commandId,
    ...(parsed.confirm === true ? { confirm: true } : {}),
  });

  return formatDirectDevReply(result);
}
