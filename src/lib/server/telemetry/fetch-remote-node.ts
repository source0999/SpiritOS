import type { ClusterNodeTelemetry } from "./types";

/** Remote Windows agent runs synchronous PowerShell (multi-drive); sub-3s fetch timeouts falsely mark nodes offline. */
const REMOTE_TIMEOUT_MS = 12_000;

function offlineNode(
  id: string,
  label: string,
  telemetryUrl: string | undefined,
  error: string,
): ClusterNodeTelemetry {
  return {
    id,
    label,
    hostname: null,
    status: "offline",
    source: "remote",
    telemetryUrl,
    platform: null,
    arch: null,
    cpu: { model: null, cores: null, usagePct: null, loadAvg: null },
    memory: { totalBytes: null, freeBytes: null, usedBytes: null, usedPct: null },
    uptimeSec: null,
    collectedAt: new Date().toISOString(),
    error,
  };
}

/** Returns null if JSON matches minimal remote contract; otherwise a human-readable reason. */
function getRemoteTelemetryValidationError(data: unknown): string | null {
  if (!data || typeof data !== "object") {
    return "invalid response: body not a JSON object";
  }
  const d = data as Record<string, unknown>;
  const missing: string[] = [];
  if (typeof d.id !== "string") missing.push("id");
  if (typeof d.status !== "string") missing.push("status");
  if (typeof d.collectedAt !== "string") missing.push("collectedAt");
  if (missing.length > 0) {
    return `invalid response: missing ${missing.join(", ")}`;
  }
  return null;
}

export async function fetchRemoteNodeTelemetry(
  id: string,
  label: string,
  telemetryUrl: string | undefined,
): Promise<ClusterNodeTelemetry> {
  if (!telemetryUrl) {
    return offlineNode(id, label, undefined, "not configured");
  }

  // Mirror scripts/spiritdesktop-windows/agent.js default so Dell reaches auth without extra .env.
  const token = process.env.SPIRIT_TELEMETRY_TOKEN?.trim() || "3399";
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REMOTE_TIMEOUT_MS);

  try {
    const res = await fetch(telemetryUrl, {
      cache: "no-store",
      signal: controller.signal,
      headers: { Authorization: `Bearer ${token}` },
    });

    clearTimeout(timer);

    if (!res.ok) {
      return offlineNode(id, label, telemetryUrl, `HTTP ${res.status}`);
    }

    const data: unknown = await res.json();

    const validationErr = getRemoteTelemetryValidationError(data);
    if (validationErr) {
      return offlineNode(id, label, telemetryUrl, validationErr);
    }

    const node = data as ClusterNodeTelemetry;
    // Preserve optional fields (e.g. storage) - do not hand-rebuild the node without them.
    return {
      ...node,
      id: node.id || id,
      label: node.label || label,
      telemetryUrl,
      source: "remote",
      storage: node.storage,
    };
  } catch (err) {
    clearTimeout(timer);
    const name = err instanceof Error ? err.name : "";
    const message =
      name === "AbortError" ? "timeout" : "unreachable";
    return offlineNode(id, label, telemetryUrl, message);
  }
}
