// ── dev-command-tools - allowlisted spawn-only dev commands, workspace cwd ─
// > No shell, no user strings, no exec(). Phase 6.

import "server-only";

import { spawnNoShell } from "@/lib/spirit/tools/child-process-spawn";
import { readFileSync } from "fs";
import path from "path";

import { getWorkspaceRoot, TOOL_MAX_OUTPUT_CHARS, truncateToolOutput } from "@/lib/spirit/tools/tool-safety";

export type DevCommandId =
  | "git_status"
  | "git_diff"
  | "npm_typecheck"
  | "npm_test"
  | "npm_lint"
  | "npm_build";

export type RunDevCommandInput = {
  commandId: DevCommandId;
  confirm?: boolean;
};

export type DevCommandResult = {
  ok: boolean;
  commandId: DevCommandId;
  label: string;
  exitCode?: number | null;
  stdout?: string;
  stderr?: string;
  output?: string;
  timedOut?: boolean;
  durationMs?: number;
  requiresConfirmation?: boolean;
  message?: string;
  error?: {
    code: string;
    message: string;
  };
};

export const DEV_COMMANDS = {
  git_status: {
    label: "git status",
    cmd: "git",
    args: ["status", "--short"],
    timeoutMs: 10_000,
    requiresConfirmation: false,
  },
  git_diff: {
    label: "git diff",
    cmd: "git",
    args: ["diff", "--", "."],
    timeoutMs: 10_000,
    requiresConfirmation: false,
  },
  npm_typecheck: {
    label: "npm run typecheck",
    cmd: "npm",
    args: ["run", "typecheck"],
    timeoutMs: 120_000,
    requiresConfirmation: false,
  },
  npm_test: {
    label: "npx vitest run",
    cmd: "npx",
    args: ["vitest", "run"],
    timeoutMs: 180_000,
    requiresConfirmation: true,
  },
  npm_lint: {
    label: "npm run lint",
    cmd: "npm",
    args: ["run", "lint"],
    timeoutMs: 120_000,
    requiresConfirmation: false,
  },
  npm_build: {
    label: "npm run build",
    cmd: "npm",
    args: ["run", "build"],
    timeoutMs: 180_000,
    requiresConfirmation: true,
  },
} as const;

let cachedPackageScripts: Record<string, string> | null | undefined;

/** Tests only */
export function clearPackageScriptsCacheForTests(): void {
  cachedPackageScripts = undefined;
}

function loadPackageScripts(): Record<string, string> | null {
  if (cachedPackageScripts !== undefined) return cachedPackageScripts;
  try {
    const pj = path.join(getWorkspaceRoot(), "package.json");
    const raw = readFileSync(pj, "utf8");
    const j = JSON.parse(raw) as { scripts?: Record<string, string> };
    cachedPackageScripts = j.scripts ?? {};
    return cachedPackageScripts;
  } catch {
    cachedPackageScripts = null;
    return null;
  }
}

export function isDevCommandToolsEnvEnabled(): boolean {
  return process.env.SPIRIT_ENABLE_DEV_COMMAND_TOOLS === "true";
}

function npmScriptExists(scriptName: string): boolean {
  const scripts = loadPackageScripts();
  return Boolean(scripts && typeof scripts[scriptName] === "string");
}

/** IDs that are valid for this workspace (npm scripts must exist where applicable). */
export function getAllowedDevCommandIds(): DevCommandId[] {
  const out: DevCommandId[] = ["git_status", "git_diff", "npm_test"];

  if (npmScriptExists("typecheck")) out.push("npm_typecheck");
  if (npmScriptExists("lint")) out.push("npm_lint");
  if (npmScriptExists("build")) out.push("npm_build");

  return out;
}

function safeSpawnEnv(): NodeJS.ProcessEnv {
  const keys = ["PATH", "HOME", "NODE_ENV", "CI", "npm_config_cache"] as const;
  const env: Record<string, string> = {};
  for (const k of keys) {
    const v = process.env[k];
    if (v !== undefined) env[k] = v;
  }
  return env as NodeJS.ProcessEnv;
}

export async function runDevCommand(input: RunDevCommandInput): Promise<DevCommandResult> {
  const fail = (
    code: string,
    message: string,
    partial: Partial<DevCommandResult> = {},
  ): DevCommandResult => ({
    ok: false,
    commandId: input.commandId,
    label: DEV_COMMANDS[input.commandId]?.label ?? input.commandId,
    ...partial,
    error: { code, message },
  });

  if (!isDevCommandToolsEnvEnabled()) {
    return fail("DEV_COMMAND_TOOLS_DISABLED", "SPIRIT_ENABLE_DEV_COMMAND_TOOLS is not enabled.");
  }

  const spec = DEV_COMMANDS[input.commandId];
  if (!spec) {
    return fail("UNKNOWN_COMMAND", "Unknown command id.");
  }

  if (!getAllowedDevCommandIds().includes(input.commandId)) {
    return fail(
      "SCRIPT_NOT_FOUND",
      `Command "${input.commandId}" is not available (missing npm script or not allowlisted for this workspace).`,
    );
  }

  if (spec.requiresConfirmation && input.confirm !== true) {
    return {
      ok: false,
      commandId: input.commandId,
      label: spec.label,
      requiresConfirmation: true,
      message: `Run "${spec.label}" only after explicit approval: pass confirm: true.`,
    };
  }

  const cwd = getWorkspaceRoot();
  const t0 = Date.now();

  try {
    const { exitCode, stdout, stderr, timedOut } = await spawnCollect(
      spec.cmd,
      [...spec.args],
      cwd,
      spec.timeoutMs,
    );
    const dur = Date.now() - t0;
    const combined = truncateToolOutput(`${stdout}\n${stderr}`.trim(), TOOL_MAX_OUTPUT_CHARS);

    return {
      ok: exitCode === 0 && !timedOut,
      commandId: input.commandId,
      label: spec.label,
      exitCode,
      stdout: truncateToolOutput(stdout, TOOL_MAX_OUTPUT_CHARS).text,
      stderr: truncateToolOutput(stderr, TOOL_MAX_OUTPUT_CHARS).text,
      output: combined.text,
      timedOut,
      durationMs: dur,
      message: timedOut
        ? `Command timed out after ${spec.timeoutMs} ms.`
        : exitCode === 0
          ? "Command finished."
          : `Command exited with code ${exitCode}.`,
    };
  } catch (e) {
    const msg = e instanceof Error ? e.message : "spawn failed";
    return fail("SPAWN_ERROR", msg);
  }
}

function spawnCollect(
  cmd: string,
  args: string[],
  cwd: string,
  timeoutMs: number,
): Promise<{ exitCode: number | null; stdout: string; stderr: string; timedOut: boolean }> {
  return new Promise((resolve, reject) => {
    const child = spawnNoShell(cmd, args, {
      cwd,
      env: safeSpawnEnv(),
    });

    let out = "";
    let err = "";
    let timedOut = false;
    const to = setTimeout(() => {
      timedOut = true;
      child.kill("SIGKILL");
    }, timeoutMs);

    child.stdout?.on("data", (c: Buffer) => {
      out += c.toString("utf8");
    });
    child.stderr?.on("data", (c: Buffer) => {
      err += c.toString("utf8");
    });

    child.on("error", (e) => {
      clearTimeout(to);
      reject(e);
    });

    child.on("close", (code) => {
      clearTimeout(to);
      resolve({ exitCode: code, stdout: out, stderr: err, timedOut });
    });
  });
}
