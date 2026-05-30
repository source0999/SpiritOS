import { spawn } from "node:child_process";
import path from "node:path";
import { createMacWorkerJob, normalizeMacWorkerResult } from "./contract";
import { recordMacWorkerError, recordMacWorkerResult } from "./registry";
import type { MacWorkerJob, MacWorkerJobInput, MacWorkerJobResult, MacWorkerJobType } from "./types";

const DEFAULT_TIMEOUT_MS = 30_000;

export type RunMacWorkerJobOptions = {
  timeoutMs?: number;
  repoRoot?: string;
};

function macSshAlias() {
  return process.env.SPIRIT_MACMINI_SSH_ALIAS?.trim() || "spirit-mac-mini";
}

function remoteRepoPath() {
  return process.env.SPIRIT_MACMINI_REPO_PATH?.trim() || "$HOME/spiritos-worker/SpiritOS";
}

function remoteWorkerCommand() {
  const repoPath = remoteRepoPath();
  return `cd ${repoPath} && python3 scripts/mac-worker/spirit_mac_worker.py`;
}

function parseJsonFromStdout(stdout: string) {
  const trimmed = stdout.trim();
  if (!trimmed) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    const lastLine = trimmed.split(/\r?\n/).reverse().find((line) => line.trim().startsWith("{"));
    return lastLine ? JSON.parse(lastLine) : null;
  }
}

function failedResult(job: MacWorkerJob, error: string, stdout = "", stderr = "", startedAt = new Date().toISOString()): MacWorkerJobResult {
  const completedAt = new Date().toISOString();
  return {
    job_id: job.job_id,
    job_type: job.job_type,
    input: job.input,
    node_id: job.node_id,
    started_at: startedAt,
    completed_at: completedAt,
    success: false,
    result: null,
    stdout,
    stderr,
    error,
    duration_ms: Math.max(0, Date.parse(completedAt) - Date.parse(startedAt)),
    artifacts: [],
    candidate_files: [],
    recommended_checks: [],
  };
}

export async function runMacWorkerJob(
  jobType: MacWorkerJobType,
  input: MacWorkerJobInput = {},
  options: RunMacWorkerJobOptions = {},
): Promise<MacWorkerJobResult> {
  const job = createMacWorkerJob(jobType, input);
  const startedAt = new Date().toISOString();
  const payload = JSON.stringify(job);
  const localRepoRoot = options.repoRoot ?? process.cwd();
  const localWorkerPath = path.join(localRepoRoot, "scripts/mac-worker/spirit-mac-worker.mjs");
  const useLocal = process.env.SPIRIT_MAC_WORKER_TRANSPORT === "local";

  try {
    const command = useLocal
      ? { file: "python3", args: [path.join(localRepoRoot, "scripts/mac-worker/spirit_mac_worker.py")] }
      : { file: "ssh", args: ["-o", "BatchMode=yes", "-o", "ConnectTimeout=8", macSshAlias(), remoteWorkerCommand()] };
    const { stdout, stderr } = await spawnWithInput(command.file, command.args, payload, options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
    const parsed = parseJsonFromStdout(stdout);
    const result = normalizeMacWorkerResult(parsed, job);
    if (!parsed) {
      result.stdout = stdout;
      result.stderr = stderr;
    }
    recordMacWorkerResult(result);
    return result;
  } catch (err) {
    const anyErr = err as { message?: string; stdout?: string; stderr?: string };
    const result = failedResult(
      job,
      anyErr.message || "Mac worker transport failed",
      anyErr.stdout || "",
      anyErr.stderr || "",
      startedAt,
    );
    recordMacWorkerError(result.error || "Mac worker transport failed");
    recordMacWorkerResult(result);
    return result;
  }
}

function spawnWithInput(
  file: string,
  args: string[],
  input: string,
  timeoutMs: number,
): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(file, args, { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      reject(Object.assign(new Error("Mac worker transport timed out"), { stdout, stderr }));
    }, timeoutMs);

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(Object.assign(error, { stdout, stderr }));
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(Object.assign(new Error(`Mac worker transport exited ${code}`), { stdout, stderr }));
      }
    });
    child.stdin.end(input);
  });
}
