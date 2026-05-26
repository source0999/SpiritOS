import type { ClusterNodeTelemetry, DriveType, NodeDrive, NodeStorage, SmartStatus } from "./types";

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

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function nullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function nullableString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function normalizeDriveType(value: unknown): DriveType {
  return value === "SSD" || value === "HDD" || value === "NVME" || value === "UNKNOWN"
    ? value
    : "UNKNOWN";
}

function inferRemoteDriveType(
  value: unknown,
  platform: string | null,
  drive: Record<string, unknown>,
): DriveType {
  const explicit = normalizeDriveType(value);
  if (explicit !== "UNKNOWN") return explicit;

  const id = nullableString(drive.id);
  const mount = nullableString(drive.mount) ?? nullableString(drive.mountPoint);
  if (platform === "darwin" && id === "mac-root" && mount === "/") {
    return "SSD";
  }

  return "UNKNOWN";
}

function normalizeSmartStatus(value: unknown): SmartStatus {
  return value === "Healthy" || value === "Warning" || value === "Critical" || value === "Unknown"
    ? value
    : "Unknown";
}

function clampPct(value: number): number {
  return Math.min(100, Math.max(0, Math.round(value * 10) / 10));
}

function usagePctFromLoadAvg(loadAvg: number[] | null, cores: number | null): number | null {
  if (!loadAvg || loadAvg.length === 0 || cores === null || cores <= 0) return null;
  return clampPct((loadAvg[0]! / cores) * 100);
}

function normalizeRemoteCpu(cpu: unknown): ClusterNodeTelemetry["cpu"] {
  const c = isRecord(cpu) ? cpu : {};
  const cores = nullableNumber(c.cores);
  const loadAvg = Array.isArray(c.loadAvg) ? c.loadAvg.filter((v): v is number => typeof v === "number") : null;
  const usagePct = nullableNumber(c.usagePct) ?? usagePctFromLoadAvg(loadAvg, cores);

  return {
    ...c,
    model: nullableString(c.model),
    cores,
    usagePct,
    loadAvg,
  };
}

function normalizeRemoteMemory(memory: unknown): ClusterNodeTelemetry["memory"] {
  const m = isRecord(memory) ? memory : {};
  return {
    ...m,
    totalBytes: nullableNumber(m.totalBytes),
    freeBytes: nullableNumber(m.freeBytes),
    usedBytes: nullableNumber(m.usedBytes),
    usedPct: nullableNumber(m.usedPct),
  };
}

function normalizeRemoteDrive(rawDrive: unknown, platform: string | null): NodeDrive {
  const drive = isRecord(rawDrive) ? rawDrive : {};
  const id = nullableString(drive.id) ?? nullableString(drive.name) ?? "unknown-drive";
  const name = nullableString(drive.name) ?? id;

  return {
    ...drive,
    id,
    name,
    mount: nullableString(drive.mount) ?? nullableString(drive.mountPoint),
    fsType: nullableString(drive.fsType) ?? nullableString(drive.filesystem),
    type: inferRemoteDriveType(drive.type, platform, drive),
    totalBytes: nullableNumber(drive.totalBytes),
    usedBytes: nullableNumber(drive.usedBytes),
    freeBytes: nullableNumber(drive.freeBytes),
    usedPct: nullableNumber(drive.usedPct),
    tempC: nullableNumber(drive.tempC),
    smart: normalizeSmartStatus(drive.smart),
  };
}

function normalizeRemoteStorage(
  storage: unknown,
  collectedAt: string,
  platform: string | null,
): NodeStorage | undefined {
  if (!isRecord(storage)) return undefined;
  const drives = Array.isArray(storage.drives)
    ? storage.drives.map((drive) => normalizeRemoteDrive(drive, platform))
    : [];

  return {
    ...storage,
    drives,
    collectedAt: nullableString(storage.collectedAt) ?? collectedAt,
    error: nullableString(storage.error) ?? undefined,
  };
}

function normalizeRemoteNodeTelemetry(
  data: ClusterNodeTelemetry,
  id: string,
  label: string,
  telemetryUrl: string,
): ClusterNodeTelemetry {
  const platform = data.platform ?? null;

  return {
    ...data,
    id: data.id || id,
    label: data.label || label,
    hostname: data.hostname ?? null,
    source: "remote",
    telemetryUrl,
    platform,
    arch: data.arch ?? null,
    cpu: normalizeRemoteCpu(data.cpu),
    memory: normalizeRemoteMemory(data.memory),
    storage: normalizeRemoteStorage(data.storage, data.collectedAt, platform),
    uptimeSec: data.uptimeSec ?? null,
  };
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
    return normalizeRemoteNodeTelemetry(node, id, label, telemetryUrl);
  } catch (err) {
    clearTimeout(timer);
    const name = err instanceof Error ? err.name : "";
    const message =
      name === "AbortError" ? "timeout" : "unreachable";
    return offlineNode(id, label, telemetryUrl, message);
  }
}
