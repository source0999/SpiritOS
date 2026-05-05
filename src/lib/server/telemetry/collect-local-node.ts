import os from "node:os";
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import type { ClusterNodeTelemetry, NodeDrive, NodeStorage } from "./types";

// ── CPU sampling ─────────────────────────────────────────────────────────────

function snapshotCpuTimes(): { idle: number; total: number } {
  let idle = 0;
  let total = 0;
  for (const cpu of os.cpus()) {
    const t = cpu.times;
    idle += t.idle;
    total += t.user + t.nice + t.sys + t.idle + t.irq;
  }
  return { idle, total };
}

async function measureCpuUsage(): Promise<number | null> {
  try {
    const before = snapshotCpuTimes();
    await new Promise<void>((resolve) => setTimeout(resolve, 150));
    const after = snapshotCpuTimes();
    const deltaIdle = after.idle - before.idle;
    const deltaTotal = after.total - before.total;
    if (deltaTotal === 0) return null;
    const pct = 100 - (deltaIdle / deltaTotal) * 100;
    return Math.min(100, Math.max(0, pct));
  } catch {
    return null;
  }
}

// ── Storage collection ────────────────────────────────────────────────────────

function getBaseDevice(device: string): string {
  const dev = device.replace(/^\/dev\//, "");
  if (/^nvme\d+n\d+p\d+/.test(dev)) return dev.replace(/p\d+$/, "");
  if (/^mmcblk\d+p\d+/.test(dev)) return dev.replace(/p\d+$/, "");
  return dev.replace(/\d+$/, "");
}

function inferDriveType(device: string): NodeDrive["type"] {
  const dev = device.replace(/^\/dev\//, "");
  if (dev.startsWith("nvme")) return "NVME";
  if (dev.startsWith("mmcblk")) return "SSD";
  if (dev.startsWith("sd") || dev.startsWith("hd") || dev.startsWith("vd")) {
    try {
      const baseDev = getBaseDevice(device);
      const rotational = readFileSync(`/sys/block/${baseDev}/queue/rotational`, "utf8").trim();
      return rotational === "0" ? "SSD" : "HDD";
    } catch {
      return "HDD";
    }
  }
  return "UNKNOWN";
}

async function collectLocalStorage(): Promise<NodeStorage> {
  const now = new Date().toISOString();
  try {
    // -P: POSIX format (no line wrapping), -l: local filesystems only (avoids stale NFS hangs)
    const output = execSync("df -Pl", { timeout: 3000, encoding: "utf8" });
    const lines = output.trim().split("\n").slice(1); // skip header

    const seen = new Set<string>();
    const drives: NodeDrive[] = [];

    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      // Filesystem  1024-blocks  Used  Available  Capacity%  Mounted on
      if (parts.length < 6) continue;
      const device = parts[0]!;
      const mount = parts[5]!;

      if (!device.startsWith("/dev/")) continue;
      // Snap/loop mounts masquerade as block devices — not useful homelab “drives”.
      if (device.startsWith("/dev/loop")) continue;
      if (seen.has(device)) continue;
      seen.add(device);

      const totalBlocks = parseInt(parts[1]!, 10);
      const usedBlocks = parseInt(parts[2]!, 10);
      const availBlocks = parseInt(parts[3]!, 10);
      if (isNaN(totalBlocks) || totalBlocks === 0) continue;

      const totalBytes = totalBlocks * 1024;
      const usedBytes = usedBlocks * 1024;
      const freeBytes = availBlocks * 1024;
      const usedPct = Math.round((usedBytes / totalBytes) * 100 * 10) / 10;

      drives.push({
        id: device,
        name: mount === "/" ? "/ (root)" : mount,
        mount,
        fsType: null,
        type: inferDriveType(device),
        totalBytes,
        usedBytes,
        freeBytes,
        usedPct,
        tempC: null,
        smart: "Unknown",
      });
    }

    return { drives, collectedAt: now };
  } catch (err) {
    return {
      drives: [],
      collectedAt: now,
      error: err instanceof Error ? err.message : "storage collection failed",
    };
  }
}

// ── Main collector ────────────────────────────────────────────────────────────

export async function collectLocalNodeTelemetry(options?: {
  id?: string;
  label?: string;
}): Promise<ClusterNodeTelemetry> {
  const hostname = os.hostname();
  const id = options?.id || process.env.SPIRIT_CLUSTER_LOCAL_ID?.trim() || hostname;
  const label = options?.label || process.env.SPIRIT_CLUSTER_LOCAL_LABEL?.trim() || hostname;

  let cpuModel: string | null = null;
  let cores: number | null = null;
  try {
    const cpus = os.cpus();
    cpuModel = cpus[0]?.model?.trim() || null;
    cores = cpus.length || null;
  } catch {
    // os.cpus unavailable on this platform
  }

  const [usagePct, storage] = await Promise.all([
    measureCpuUsage(),
    collectLocalStorage(),
  ]);

  const rawLoadAvg = os.loadavg();
  const loadAvg =
    rawLoadAvg.length === 3 && rawLoadAvg.some((v) => v > 0) ? rawLoadAvg : null;

  const totalBytes = os.totalmem();
  const freeBytes = os.freemem();
  const usedBytes = totalBytes - freeBytes;
  const usedPct = totalBytes > 0 ? (usedBytes / totalBytes) * 100 : null;

  return {
    id,
    label,
    hostname,
    status: "online",
    source: "local",
    platform: os.platform(),
    arch: os.arch(),
    cpu: {
      model: cpuModel,
      cores,
      usagePct: usagePct !== null ? Math.round(usagePct * 10) / 10 : null,
      loadAvg,
    },
    memory: {
      totalBytes,
      freeBytes,
      usedBytes,
      usedPct: usedPct !== null ? Math.round(usedPct * 10) / 10 : null,
    },
    storage,
    uptimeSec: Math.floor(os.uptime()),
    collectedAt: new Date().toISOString(),
  };
}
