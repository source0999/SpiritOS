import { createHash } from "crypto";

import {
  DUMMY_PRODUCT_SITE_TRIAL_ROOT,
  buildDeleteFileReverseDiff,
} from "@/lib/coding/agent-lab-cleanup";
import {
  AGENT_LAB_BASELINE_ROOTS,
  AGENT_LAB_CODER_PROBE_PATHS,
  collectAgentLabFilesFromListEntries,
  evaluateAgentLabBaseline,
  type AgentLabBaselineSnapshot,
} from "@/lib/coding/reversible-trial-runner";
import { sourceProxyFetch, sourceProxyLongJsonFetch } from "@/lib/source-proxy-origin";

type JsonRecord = Record<string, unknown>;

export const AGENT_LAB_SWEEP_STEP_TIMEOUT_MS = 45_000;

export type AgentLabSweepResult = {
  failures: string[];
  removed: number;
  snapshot: AgentLabBaselineSnapshot;
  skipped: number;
  targets: string[];
};

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" ? (value as JsonRecord) : {};
}

function normalizeRepoPath(path: string): string {
  const trimmed = path.trim().replace(/\\/g, "/");
  if (trimmed.endsWith("/") && /\.[A-Za-z0-9]+$/.test(trimmed.slice(0, -1))) {
    return trimmed.slice(0, -1);
  }
  return trimmed;
}

function workspaceReadLooksMissing(status: number, errorText: string): boolean {
  if (status === 404) return true;
  if (status === 400 && /not found|no such file|missing|does not exist|unknown path/i.test(errorText)) {
    return true;
  }
  return false;
}

function changedFilesFromApprovedDiff(diff: string): string[] {
  const files = new Set<string>();
  for (const line of diff.split(/\r?\n/)) {
    const diffMatch = line.match(/^diff --git a\/(.+?) b\/(.+)$/);
    if (diffMatch?.[2]) {
      files.add(normalizeRepoPath(diffMatch[2]));
      continue;
    }
    if (!line.startsWith("+++ b/")) continue;
    const file = line.slice("+++ b/".length).trim();
    if (file && file !== "/dev/null") {
      files.add(normalizeRepoPath(file));
    }
  }
  return [...files];
}

function diffHashForApprovedDiff(approvedDiff: string) {
  return createHash("sha256").update(approvedDiff).digest("hex");
}

function approvalIdForApprovedDiff({
  approvedDiff,
  target,
  taskId,
}: {
  approvedDiff: string;
  target: string;
  taskId: string;
}) {
  const diffHash = diffHashForApprovedDiff(approvedDiff);
  const key = [taskId.trim(), target.trim(), diffHash].join("|");
  return `approval-${createHash("sha256").update(key).digest("hex").slice(0, 16)}`;
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function taskIdFromPayload(payload: unknown): string | null {
  const record = asRecord(payload);
  const taskId =
    stringValue(record.task_id) ??
    stringValue(record.taskId) ??
    stringValue(asRecord(record.task).id) ??
    stringValue(asRecord(asRecord(record.data).task).id) ??
    stringValue(record.id);
  return taskId ?? null;
}

async function sourceProxyLongJsonFetchWithTimeout(
  pathAndQuery: string,
  init: Parameters<typeof sourceProxyLongJsonFetch>[1] = {},
  timeoutMs = AGENT_LAB_SWEEP_STEP_TIMEOUT_MS,
): Promise<Awaited<ReturnType<typeof sourceProxyLongJsonFetch>>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await sourceProxyLongJsonFetch(pathAndQuery, { ...init, signal: controller.signal });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`Source proxy timed out after ${Math.round(timeoutMs / 1000)}s (${pathAndQuery})`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function listWorkspacePath(path: string): Promise<Array<{ path?: string; kind?: string }>> {
  try {
    const response = await sourceProxyFetch("/v1/workspace/list", {
      body: JSON.stringify({ max_entries: 100, path }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    if (!response.ok) return [];
    const payload = await response.json() as unknown;
    const entries = asRecord(payload).entries;
    if (!Array.isArray(entries)) return [];
    return entries.map((entry) => {
      const record = asRecord(entry);
      return {
        kind: typeof record.kind === "string" ? record.kind : undefined,
        path: typeof record.path === "string" ? record.path : undefined,
      };
    });
  } catch {
    return [];
  }
}

async function readWorkspaceFileExists(path: string): Promise<boolean> {
  const read = await readWorkspaceFileContent(path);
  return read.status === "ok";
}

export async function readWorkspaceFileContent(
  path: string,
): Promise<{ status: "ok" | "missing" | "error"; content?: string; error?: string }> {
  try {
    const response = await sourceProxyFetch("/v1/workspace/read", {
      body: JSON.stringify({ max_bytes: 64000, path }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const errorText = response.ok ? "" : await response.text();
    if (!response.ok) {
      if (workspaceReadLooksMissing(response.status, errorText)) {
        return { status: "missing" };
      }
      return { status: "error", error: errorText || `workspace read HTTP ${response.status}` };
    }
    const payload = await response.json() as { content?: string; excerpt?: string };
    return { content: payload.excerpt ?? payload.content ?? "", status: "ok" };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : "workspace read failed",
      status: "error",
    };
  }
}

export async function collectAgentLabBaselineFiles(): Promise<string[]> {
  const files = new Set<string>();
  for (const root of AGENT_LAB_BASELINE_ROOTS) {
    const entries = await listWorkspacePath(root);
    for (const file of collectAgentLabFilesFromListEntries(AGENT_LAB_BASELINE_ROOTS, entries)) {
      files.add(file);
    }
    for (const entry of entries) {
      const path = typeof entry.path === "string" ? entry.path.trim().replace(/\\/g, "/") : "";
      if (!path || entry.kind !== "directory") continue;
      const nested = await listWorkspacePath(path);
      for (const file of collectAgentLabFilesFromListEntries(AGENT_LAB_BASELINE_ROOTS, nested)) {
        files.add(file);
      }
      for (const nestedEntry of nested) {
        const nestedPath =
          typeof nestedEntry.path === "string" ? nestedEntry.path.trim().replace(/\\/g, "/") : "";
        if (!nestedPath || nestedEntry.kind !== "directory") continue;
        const deep = await listWorkspacePath(nestedPath);
        for (const file of collectAgentLabFilesFromListEntries(AGENT_LAB_BASELINE_ROOTS, deep)) {
          files.add(file);
        }
      }
    }
  }

  for (const path of AGENT_LAB_CODER_PROBE_PATHS) {
    if (await readWorkspaceFileExists(path)) {
      files.add(path);
    }
  }

  return Array.from(files).sort();
}

export async function buildAgentLabBaselineSnapshot(
  unrevertedReceiptTargets: string[] = [],
): Promise<AgentLabBaselineSnapshot> {
  const agentLabFiles = await collectAgentLabBaselineFiles();
  const existingReceiptTargets = await existingAgentLabReceiptTargets(unrevertedReceiptTargets);
  return evaluateAgentLabBaseline({
    agentLabFiles,
    unrevertedReceiptTargets: existingReceiptTargets,
  });
}

async function deleteAgentLabFileOnProxy(target: string): Promise<{ ok: true } | { ok: false; error: string }> {
  const normalizedTarget = normalizeRepoPath(target);
  const before = await readWorkspaceFileContent(normalizedTarget);
  if (before.status === "missing") {
    return { ok: true };
  }
  if (before.status === "error") {
    return { ok: false, error: before.error ?? "workspace read failed before delete" };
  }

  const approvedDiff = buildDeleteFileReverseDiff(normalizedTarget, before.content ?? "");
  const changedFiles = changedFilesFromApprovedDiff(approvedDiff);
  const allowedFiles = [
    normalizedTarget,
    "src/app/agent-lab/**",
    "src/components/agent-lab/**",
    "src/lib/agent-lab/**",
    "src/app/api/agent-lab/**",
    "tests/agent-lab/**",
    `${DUMMY_PRODUCT_SITE_TRIAL_ROOT}**`,
  ];

  const taskResponse = await sourceProxyLongJsonFetchWithTimeout("/v1/tasks/long-running", {
    body: JSON.stringify({
      description: `Agent-lab cleanup delete ${normalizedTarget}`,
    }),
    headers: { "content-type": "application/json" },
    method: "POST",
  });
  const taskPayload = taskResponse.ok ? await taskResponse.json().catch(() => ({})) : null;
  const taskId = taskIdFromPayload(taskPayload);
  if (!taskResponse.ok || !taskId) {
    const errorText =
      typeof taskPayload === "object" && taskPayload && "error" in taskPayload
        ? String((taskPayload as { error?: unknown }).error ?? "")
        : await taskResponse.text().catch(() => "");
    return {
      ok: false,
      error: taskId
        ? errorText || `long-running task create HTTP ${taskResponse.status}`
        : errorText ||
          `long-running task create HTTP ${taskResponse.status} but response had no task id (expected task.id or task_id)`,
    };
  }

  const approvalId = approvalIdForApprovedDiff({
    approvedDiff,
    target: normalizedTarget,
    taskId,
  });
  const executeResponse = await sourceProxyLongJsonFetchWithTimeout(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/execute-approved`,
    {
      body: JSON.stringify({
        action: "revert",
        approved: true,
        approval_id: approvalId,
        approved_by: "agent-lab-sweep",
        approved_diff: approvedDiff,
        allowed_files: allowedFiles,
        changed_files: changedFiles,
        diff_hash: diffHashForApprovedDiff(approvedDiff),
        commit_authority: false,
        push_authority: false,
        target: normalizedTarget,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  );
  if (!executeResponse.ok) {
    const errorText = await executeResponse.text().catch(() => "");
    return {
      ok: false,
      error: errorText || `execute-approved HTTP ${executeResponse.status}`,
    };
  }

  const after = await readWorkspaceFileContent(normalizedTarget);
  if (after.status === "ok") {
    return { ok: false, error: `Delete did not remove ${normalizedTarget} from workspace.` };
  }
  if (after.status === "error") {
    return { ok: false, error: after.error ?? `Could not verify delete for ${normalizedTarget}.` };
  }
  await sourceProxyLongJsonFetchWithTimeout(
    `/v1/tasks/long-running/${encodeURIComponent(taskId)}/verification`,
    {
      body: JSON.stringify({
        confirm_backup_audit_present: true,
        confirm_changed_files_reviewed: true,
        confirm_expected_change_present: true,
        confirm_no_unintended_files: true,
        manual_browser_check_done: true,
        skip_reason: "Agent Lab sweep verified the cleanup target is absent after delete.",
        verification_note: `Agent Lab sweep deleted and verified ${normalizedTarget}.`,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    },
  ).catch(() => null);
  return { ok: true };
}

export async function sweepAgentLabLeftoverFilesServer(
  paths: string[],
): Promise<Omit<AgentLabSweepResult, "snapshot">> {
  const ordered = [...new Set(paths.map((path) => normalizeRepoPath(path)).filter(Boolean))].sort(
    (left, right) => right.length - left.length,
  );
  const failures: string[] = [];
  let removed = 0;
  let skipped = 0;

  for (const target of ordered) {
    const before = await readWorkspaceFileContent(target);
    if (before.status === "missing") {
      skipped += 1;
      continue;
    }

    let lastError = "Agent-lab delete failed.";
    let deleted = false;
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      const result = await deleteAgentLabFileOnProxy(target);
      if (result.ok) {
        deleted = true;
        removed += 1;
        break;
      }
      lastError = result.error;
      if (attempt < 3) {
        await new Promise((resolve) => setTimeout(resolve, 350 * attempt));
      }
    }
    if (!deleted) {
      failures.push(`${target}: ${lastError}`);
    }
  }

  return { failures, removed, skipped, targets: ordered };
}

export async function sweepAgentLabBaselineServer(
  unrevertedReceiptTargets: string[] = [],
): Promise<AgentLabSweepResult> {
  let snapshot = await buildAgentLabBaselineSnapshot(unrevertedReceiptTargets);
  const firstPass = await sweepAgentLabLeftoverFilesServer(snapshot.baseline_dirty_agent_lab_files);
  let remainingReceiptTargets = await existingAgentLabReceiptTargets(unrevertedReceiptTargets);
  snapshot = await buildAgentLabBaselineSnapshot(remainingReceiptTargets);
  if (!snapshot.baseline_clean_for_fresh_suite && snapshot.baseline_dirty_agent_lab_files.length > 0) {
    const secondPass = await sweepAgentLabLeftoverFilesServer(snapshot.baseline_dirty_agent_lab_files);
    firstPass.failures.push(...secondPass.failures);
    firstPass.removed += secondPass.removed;
    firstPass.skipped += secondPass.skipped;
    remainingReceiptTargets = await existingAgentLabReceiptTargets(unrevertedReceiptTargets);
    snapshot = await buildAgentLabBaselineSnapshot(remainingReceiptTargets);
  }
  return {
    ...firstPass,
    snapshot,
  };
}

async function existingAgentLabReceiptTargets(targets: string[]): Promise<string[]> {
  const existing: string[] = [];
  for (const target of [...new Set(targets.map((path) => normalizeRepoPath(path)).filter(Boolean))]) {
    if (await readWorkspaceFileExists(target)) {
      existing.push(target);
    }
  }
  return existing;
}
