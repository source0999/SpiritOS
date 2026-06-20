import {
  MAC_WORKER_NODE_ID,
  macWorkerJobTypes,
  type MacWorkerCapabilityDescriptor,
  type MacWorkerJobResult,
  type MacWorkerNodeStatus,
} from "./types";
import { macWorkerCapabilityDescriptor, summarizeMacWorkerResult } from "./contract";

let lastResult: MacWorkerJobResult | null = null;
let lastError: string | null = null;
let lastRepoPresent: boolean | null = null;

export function recordMacWorkerResult(result: MacWorkerJobResult) {
  lastResult = result;
  lastError = result.error;
  const repoPresent = boolResultValue(result, "repo_present");
  if (repoPresent !== null) {
    lastRepoPresent = repoPresent;
  }
}

export function recordMacWorkerError(error: string) {
  lastError = error;
}

function stringResultValue(result: MacWorkerJobResult | null, key: string): string | null {
  const value = result?.result?.[key];
  return typeof value === "string" ? value : null;
}

function boolResultValue(result: MacWorkerJobResult | null, key: string): boolean | null {
  const value = result?.result?.[key];
  return typeof value === "boolean" ? value : null;
}

function isTransportFailure(result: MacWorkerJobResult | null): boolean {
  if (!result || result.success) return false;
  const error = result.error || "";
  return (
    error.includes("Mac worker transport") ||
    error.includes("ssh") ||
    error.includes("spawn") ||
    error.includes("timed out") ||
    error.includes("exited ")
  );
}

export function getMacWorkerStatus(): MacWorkerNodeStatus {
  const transportFailed = isTransportFailure(lastResult);
  const lastReasonCode = stringResultValue(lastResult, "reason_code");
  const blockedCommand = stringResultValue(lastResult, "blocked_command");
  const safeChecksBlocked = lastReasonCode === "safe_check_command_not_allowlisted";
  const online = Boolean(lastResult) && !transportFailed;

  return {
    node_id: MAC_WORKER_NODE_ID,
    label: "Mac Mini",
    hostname: process.env.SPIRIT_MACMINI_HOST?.trim() || "spirit-mac-mini.local",
    ssh_alias: process.env.SPIRIT_MACMINI_SSH_ALIAS?.trim() || "spirit-mac-mini",
    role: "macos-worker",
    online,
    worker_available: online,
    repo_present: lastRepoPresent,
    supported_job_types: [...macWorkerJobTypes],
    last_job_type: lastResult?.job_type ?? null,
    last_used_at: lastResult?.completed_at ?? null,
    last_success: lastResult?.success ?? null,
    result_summary: lastResult ? summarizeMacWorkerResult(lastResult) : "No Mac worker job recorded in this server process",
    error: lastError,
    last_reason_code: lastReasonCode,
    blocked_command: blockedCommand,
    safe_checks_blocked: safeChecksBlocked,
    last_result: lastResult ?? undefined,
  };
}

export function getMacWorkerCapability(): MacWorkerCapabilityDescriptor {
  const status = lastResult
    ? isTransportFailure(lastResult)
      ? "BLOCKED_AUTH"
      : "AVAILABLE"
    : "UNKNOWN";
  return macWorkerCapabilityDescriptor(status, lastResult?.completed_at ?? null);
}
