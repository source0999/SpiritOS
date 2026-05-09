#!/usr/bin/env node
/* eslint-disable @typescript-eslint/no-require-imports -- shipped as plain Node CJS for Windows */
// ── Spirit Desktop - LAN telemetry stub ─────────────────────────────────────
// Drop-in for Windows: exposes GET /api/telemetry/self matching ClusterNodeTelemetry.
// Dell Next calls this server-side - use the desktop LAN IP in SPIRITDESKTOP_TELEMETRY_URL,
// not localhost on the Dell. Plain HTTP + bearer token is intentional for trusted LAN.
//
// ── DEPLOYMENT (read this before opening another “storage missing” ticket) ──
// Editing scripts/spiritdesktop-windows/agent.js in the SpiritOS repo does NOTHING to a
// machine that is already running an old copy. You must copy agent.js **and**
// windows-drive-type.js (same folder—agent requires it) onto spiritdesktop
// (or whatever path you launch from) and **restart** the Node process (`node agent.js`).
// Sanity check from the Dell: curl -H "Authorization: Bearer <token>"
//   http://<spiritdesktop-lan-ip>:3000/api/telemetry/self
// The JSON must include a top-level `storage` object. If it does not, you are still on
// legacy agent code or a different file is being executed.

const http = require("node:http");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { normalizeWindowsPhysicalDiskType } = require(path.join(__dirname, "windows-drive-type.js"));

const PORT = Number.parseInt(process.env.PORT || "3000", 10);
const TOKEN = (process.env.SPIRIT_TELEMETRY_TOKEN || "3399").trim();
const FS_ENABLED = process.env.SPIRIT_DESKTOP_FS_ENABLED === "true";
const FS_ALLOWLIST = (process.env.SPIRIT_DESKTOP_FS_ALLOWLIST || "C:\\Projects").trim();
const FS_MAX_ENTRIES = Number.parseInt(process.env.SPIRIT_DESKTOP_FS_MAX_ENTRIES || "200", 10);
const FS_MAX_READ_BYTES = Number.parseInt(process.env.SPIRIT_DESKTOP_FS_MAX_READ_BYTES || "120000", 10);
const NODE_ID = "spiritdesktop";
const NODE_LABEL = "spiritdesktop";

// ── CPU ───────────────────────────────────────────────────────────────────────

function snapshotCpuTimes() {
  let idle = 0;
  let total = 0;
  for (const cpu of os.cpus()) {
    const t = cpu.times;
    idle += t.idle;
    total += t.user + t.nice + t.sys + t.idle + t.irq;
  }
  return { idle, total };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function measureCpuUsage() {
  try {
    const before = snapshotCpuTimes();
    await sleep(150);
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

// ── Storage (Windows) ─────────────────────────────────────────────────────────
// Win32_LogicalDisk for sizes + mount; Get-PhysicalDisk per drive letter for Bus/Media.
// WMI fallback: LogicalDisk→DiskPartition→DiskDrive PNPDeviceID for NVMe when cmdlets lie.
// CIM UInt64 → JSON strings sometimes — coerce with num().

function num(v) {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "bigint") return Number(v);
  if (typeof v === "string" && v.trim() !== "") {
    const n = Number(v.trim());
    if (Number.isFinite(n)) return n;
  }
  return null;
}

function normalizeWindowsSmartStatus(v) {
  const s = String(v ?? "").trim().toLowerCase();
  if (!s) return "Unknown";
  if (s === "healthy" || s === "ok") return "Healthy";
  if (s === "warning" || s === "degraded" || s === "lost communication") return "Warning";
  if (s === "critical" || s === "unhealthy" || s === "failed" || s === "pred fail") return "Critical";
  return "Unknown";
}

/** Multi-line PS: logical disks + PhysicalDisk enrichment + WMI NVMe hint. */
const WINDOWS_STORAGE_PS = `
$ErrorActionPreference = 'SilentlyContinue'
$out = New-Object System.Collections.ArrayList
$physicalDisks = @()
try { $physicalDisks = @(Get-PhysicalDisk) } catch {}
function Find-PhysicalDiskForDisk($disk, $diskNumber) {
  if ($physicalDisks.Count -eq 0) { return $null }
  $diskNumberText = [string]$diskNumber
  $match = $physicalDisks | Where-Object { [string]$_.DeviceId -eq $diskNumberText } | Select-Object -First 1
  if ($match) { return $match }
  if ($disk) {
    $diskSerial = [string]$disk.SerialNumber
    $diskSerial = $diskSerial.Trim()
    if ($diskSerial) {
      $match = $physicalDisks | Where-Object { ([string]$_.SerialNumber).Trim() -eq $diskSerial } | Select-Object -First 1
      if ($match) { return $match }
    }
    $diskName = [string]$disk.FriendlyName
    $diskName = $diskName.Trim()
    if ($diskName) {
      $match = $physicalDisks | Where-Object { ([string]$_.FriendlyName).Trim() -eq $diskName } | Select-Object -First 1
      if ($match) { return $match }
    }
    try {
      $diskSize = [uint64]$disk.Size
      $match = $physicalDisks | Where-Object {
        try {
          $pdSize = [uint64]$_.Size
          $diff = if ($pdSize -gt $diskSize) { $pdSize - $diskSize } else { $diskSize - $pdSize }
          $diff -lt 104857600
        } catch { $false }
      } | Select-Object -First 1
      if ($match) { return $match }
    } catch {}
  }
  return $null
}
$virtualDiskByDiskNumber = @{}
try {
  Get-VirtualDisk | ForEach-Object {
    $vd = $_
    try {
      $vd | Get-Disk | ForEach-Object {
        if ($null -ne $_.Number) {
          $virtualDiskByDiskNumber[[int]$_.Number] = $vd
        }
      }
    } catch {}
  }
} catch {}
Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
  $row = $_
  $devId = $row.DeviceID
  $letter = if ($devId -match '^([A-Za-z]):') { $Matches[1] } else { $null }
  $bus = $null
  $media = $null
  $spindleSpeed = $null
  $health = $null
  if ($letter) {
    try {
      $part = Get-Partition -DriveLetter $letter -ErrorAction Stop | Select-Object -First 1
      if ($part -and $null -ne $part.DiskNumber) {
        $disk = $null
        try {
          $disk = Get-Disk -Number $part.DiskNumber -ErrorAction Stop
          if ($disk) {
            try { $bus = $disk.BusType.ToString() } catch {}
            try { $health = $disk.HealthStatus.ToString() } catch {}
          }
        } catch {}

        if ($virtualDiskByDiskNumber.ContainsKey([int]$part.DiskNumber)) {
          $vd = $virtualDiskByDiskNumber[[int]$part.DiskNumber]
          if ($vd) {
            if (-not $bus -or $bus -eq 'Spaces') { $bus = 'Spaces' }
            try {
              $vdMedia = $vd.MediaType.ToString()
              if ($vdMedia -and $vdMedia -ne 'Unspecified') { $media = $vdMedia }
            } catch {}
            try {
              $vdHealth = $vd.HealthStatus.ToString()
              if ($vdHealth) { $health = $vdHealth }
            } catch {}
            if (-not $media -or $media -eq 'Unspecified') {
              try {
                $poolMedia = @($vd | Get-StoragePool | Get-PhysicalDisk | ForEach-Object {
                  try { $_.MediaType.ToString() } catch {}
                } | Where-Object { $_ -and $_ -ne 'Unspecified' } | Select-Object -Unique)
                if ($poolMedia.Count -eq 1) { $media = $poolMedia[0] }
              } catch {}
            }
            if (-not $health) {
              try {
                $poolHealth = @($vd | Get-StoragePool | Get-PhysicalDisk | ForEach-Object {
                  try { $_.HealthStatus.ToString() } catch {}
                } | Where-Object { $_ } | Select-Object -Unique)
                if ($poolHealth.Count -eq 1) { $health = $poolHealth[0] }
              } catch {}
            }
          }
        }

        if (-not $media -or $media -eq 'Unspecified' -or -not $health) {
          try {
            $pd = Find-PhysicalDiskForDisk $disk $part.DiskNumber
            if ($pd) {
              if (-not $bus) { $bus = $pd.BusType.ToString() }
              if (-not $media -or $media -eq 'Unspecified') { $media = $pd.MediaType.ToString() }
              if (-not $health) { try { $health = $pd.HealthStatus.ToString() } catch {} }
              try { $spindleSpeed = [uint64]$pd.SpindleSpeed } catch {}
            }
          } catch {}
        }
      }
    } catch {}
  }
  if (-not $bus) {
    try {
      $parts = Get-CimAssociatedInstance -InputObject $row -ResultClassName Win32_DiskPartition
      foreach ($p in $parts) {
        $dds = Get-CimAssociatedInstance -InputObject $p -ResultClassName Win32_DiskDrive
        foreach ($dd in $dds) {
          if ($dd.PNPDeviceID -match '(?i)NVMe') { $bus = 'NVMe'; break }
          if ($dd.InterfaceType -match '(?i)NVMe') { $bus = 'NVMe'; break }
        }
        if ($bus) { break }
      }
    } catch {}
  }
  [void]$out.Add([PSCustomObject]@{
    DeviceID = $devId
    VolumeName = $row.VolumeName
    Size = $row.Size
    FreeSpace = $row.FreeSpace
    FileSystem = $row.FileSystem
    PhysicalBusType = $bus
    PhysicalMediaType = $media
    PhysicalSpindleSpeed = $spindleSpeed
    PhysicalHealthStatus = $health
  })
}
ConvertTo-Json -Depth 6 -Compress -InputObject @($out.ToArray())
`.trim();

function collectWindowsStorage() {
  const now = new Date().toISOString();
  try {
    const output = execFileSync("powershell", ["-NoProfile", "-NonInteractive", "-Command", WINDOWS_STORAGE_PS], {
      timeout: 8000,
      encoding: "utf8",
      maxBuffer: 4 * 1024 * 1024,
    });
    const trimmed = output.replace(/^\uFEFF/, "").trim();
    const raw = JSON.parse(trimmed);
    // PowerShell returns an object (not array) for a single drive
    const disks = Array.isArray(raw) ? raw : raw != null ? [raw] : [];
    const drives = disks
      .filter((d) => d && d.DeviceID && num(d.Size) != null && num(d.Size) > 0)
      .map((d) => {
        const totalBytes = num(d.Size);
        const freeBytes = Math.max(0, num(d.FreeSpace) ?? 0);
        const usedBytes = Math.max(0, totalBytes - freeBytes);
        const usedPct = Math.round((usedBytes / totalBytes) * 100 * 10) / 10;
        const type = normalizeWindowsPhysicalDiskType(d.PhysicalBusType, d.PhysicalMediaType, d.PhysicalSpindleSpeed);
        const smart = normalizeWindowsSmartStatus(d.PhysicalHealthStatus);
        return {
          id: d.DeviceID,
          name: d.VolumeName ? `${d.DeviceID} (${d.VolumeName})` : d.DeviceID,
          mount: d.DeviceID,
          fsType: d.FileSystem || null,
          type,
          totalBytes,
          usedBytes,
          freeBytes,
          usedPct,
          tempC: null,
          smart,
        };
      });
    return { drives, collectedAt: now };
  } catch (err) {
    return {
      drives: [],
      collectedAt: now,
      error: err instanceof Error ? err.message : "windows storage collection failed",
    };
  }
}

// ── Auth ──────────────────────────────────────────────────────────────────────

function unauthorized(res) {
  res.writeHead(401, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "unauthorized" }));
}

function bearerMatches(req) {
  const want = `Bearer ${TOKEN}`;
  const auth = req.headers.authorization;
  return typeof auth === "string" && auth.trim() === want;
}

function sendJson(res, status, body) {
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
  });
  res.end(JSON.stringify(body));
}

async function readJsonBody(req, maxBytes) {
  let body = "";
  for await (const chunk of req) {
    body += chunk;
    if (Buffer.byteLength(body, "utf8") > maxBytes) {
      throw new Error("body too large");
    }
  }
  if (!body.trim()) return {};
  return JSON.parse(body);
}

const BLOCKED_FS_DIRS = new Set([
  ".git",
  "node_modules",
  ".next",
  "dist",
  "build",
  "coverage",
  ".turbo",
  ".cache",
]);

function blockedFsBasename(name) {
  const lower = String(name || "").toLowerCase();
  if (!lower) return true;
  if (lower.startsWith(".")) return true;
  if (lower === ".env" || lower.startsWith(".env.")) return true;
  if (lower.endsWith(".pem") || lower.endsWith(".key")) return true;
  if (lower === "id_rsa" || lower === "id_ed25519") return true;
  if (lower.startsWith("secrets.") || lower.startsWith("credentials.")) return true;
  return false;
}

function normalizeWindowsPath(inputPath) {
  if (typeof inputPath !== "string") return null;
  let s = inputPath.trim().replace(/^[`"']+/, "").replace(/[`"'.,;:!?]+$/, "");
  s = s.replace(/\//g, "\\");
  const driveSlash = s.match(/^([a-z])\\(.+)$/i);
  if (driveSlash) {
    s = `${driveSlash[1].toUpperCase()}:\\${driveSlash[2]}`;
  } else {
    s = s.replace(/^([a-z]):/i, (_m, d) => `${d.toUpperCase()}:`);
  }
  if (!/^[A-Z]:\\/i.test(s)) return null;
  return path.win32.resolve(s);
}

function allowlistRoots() {
  return FS_ALLOWLIST.split(/[,\n]+/)
    .map((p) => normalizeWindowsPath(p))
    .filter((p) => p && !/^[A-Z]:\\?$/i.test(p));
}

function pathWithinRoot(child, root) {
  const c = path.win32.normalize(child).toLowerCase();
  const r = path.win32.normalize(root).toLowerCase();
  const rWithSep = r.endsWith("\\") ? r : `${r}\\`;
  return c === r || c.startsWith(rWithSep);
}

function assertFsPathAllowed(inputPath) {
  const normalized = normalizeWindowsPath(inputPath);
  if (!normalized) {
    return {
      ok: false,
      status: 400,
      body: { ok: false, code: "PATH_BLOCKED", message: "Only absolute Windows drive paths are allowed." },
    };
  }

  const roots = allowlistRoots();
  if (roots.length === 0 || !roots.some((root) => pathWithinRoot(normalized, root))) {
    return {
      ok: false,
      status: 403,
      body: {
        ok: false,
        code: "PATH_NOT_ALLOWLISTED",
        message: "That path is outside the configured Windows filesystem allowlist.",
      },
    };
  }

  const parts = normalized.replace(/^[A-Z]:\\/i, "").split("\\").filter(Boolean);
  for (const part of parts) {
    if (BLOCKED_FS_DIRS.has(part.toLowerCase()) || blockedFsBasename(part)) {
      return {
        ok: false,
        status: 403,
        body: { ok: false, code: "PATH_BLOCKED", message: "That path is blocked by filesystem safety rules." },
      };
    }
  }

  return { ok: true, path: normalized, roots };
}

async function listAllowedWindowsFiles(inputPath, maxEntries) {
  if (!FS_ENABLED) {
    return {
      status: 403,
      body: {
        ok: false,
        code: "WINDOWS_FS_DISABLED",
        message: "Windows filesystem access is disabled on this agent.",
      },
    };
  }

  const allowed = assertFsPathAllowed(inputPath);
  if (!allowed.ok) return { status: allowed.status, body: allowed.body };

  const realDir = await fs.realpath(allowed.path);
  if (!allowed.roots.some((root) => pathWithinRoot(realDir, root))) {
    return {
      status: 403,
      body: { ok: false, code: "PATH_NOT_ALLOWLISTED", message: "Resolved path escaped the configured allowlist." },
    };
  }

  const st = await fs.lstat(realDir);
  if (!st.isDirectory()) {
    return {
      status: 400,
      body: { ok: false, code: "NOT_A_DIRECTORY", message: "Path is not a directory." },
    };
  }

  const hardMax = Number.isFinite(FS_MAX_ENTRIES) && FS_MAX_ENTRIES > 0 ? FS_MAX_ENTRIES : 200;
  const wantMax = Number.isFinite(maxEntries) && maxEntries > 0 ? Math.floor(maxEntries) : hardMax;
  const cap = Math.min(wantMax, hardMax, 200);
  const dirents = await fs.readdir(realDir, { withFileTypes: true });
  const entries = [];
  for (const d of dirents.sort((a, b) => a.name.localeCompare(b.name))) {
    if (entries.length >= cap) break;
    if (blockedFsBasename(d.name) || BLOCKED_FS_DIRS.has(d.name.toLowerCase())) continue;
    if (!d.isDirectory() && !d.isFile()) continue;
    const childPath = path.win32.join(realDir, d.name);
    const realChild = await fs.realpath(childPath).catch(() => null);
    if (!realChild || !allowed.roots.some((root) => pathWithinRoot(realChild, root))) continue;
    const childStat = await fs.lstat(childPath).catch(() => null);
    if (!childStat || childStat.isSymbolicLink()) continue;
    entries.push({
      name: d.name,
      type: d.isDirectory() ? "directory" : "file",
      sizeBytes: d.isFile() ? childStat.size : null,
      modifiedAt: childStat.mtime ? childStat.mtime.toISOString() : null,
    });
  }

  return {
    status: 200,
    body: {
      ok: true,
      path: allowed.path,
      entries,
      truncated: dirents.length > entries.length && entries.length >= cap,
    },
  };
}

// ── Telemetry payload ─────────────────────────────────────────────────────────

async function buildTelemetryPayload() {
  const hostname = os.hostname();
  let cpuModel = null;
  let cores = null;
  try {
    const cpus = os.cpus();
    cpuModel = cpus[0]?.model?.trim() || null;
    cores = cpus.length || null;
  } catch {
    // ignore
  }

  const usagePct = await measureCpuUsage();
  const rawLoadAvg = os.loadavg();
  const loadAvg =
    rawLoadAvg.length === 3 && rawLoadAvg.some((v) => v > 0) ? rawLoadAvg : null;

  const totalBytes = os.totalmem();
  const freeBytes = os.freemem();
  const usedBytes = totalBytes - freeBytes;
  const usedPct = totalBytes > 0 ? (usedBytes / totalBytes) * 100 : null;

  const storage = collectWindowsStorage();

  return {
    id: NODE_ID,
    label: NODE_LABEL,
    hostname,
    status: "online",
    source: "remote",
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

// ── HTTP server ───────────────────────────────────────────────────────────────

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);

  if (!bearerMatches(req)) {
    unauthorized(res);
    return;
  }

  if (url.pathname === "/api/files/list" && req.method === "POST") {
    try {
      const body = await readJsonBody(req, 64 * 1024);
      const result = await listAllowedWindowsFiles(body.path, Number(body.maxEntries));
      sendJson(res, result.status, result.body);
    } catch {
      sendJson(res, 400, {
        ok: false,
        code: "BAD_REQUEST",
        message: "Invalid filesystem list request.",
      });
    }
    return;
  }

  if (url.pathname !== "/api/telemetry/self" || req.method !== "GET") {
    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "not found" }));
    return;
  }

  try {
    const body = await buildTelemetryPayload();
    sendJson(res, 200, body);
  } catch (err) {
    sendJson(res, 500, { error: err instanceof Error ? err.message : "internal error" });
  }
});

if (require.main === module) {
  server.listen(PORT, "0.0.0.0", () => {
    console.log(
      `[spiritdesktop-agent] listening on http://0.0.0.0:${PORT}/api/telemetry/self (plain HTTP, not HTTPS). TOKEN len=${TOKEN.length} FS enabled=${FS_ENABLED}`,
    );
  });
}

module.exports = {
  normalizeWindowsPath,
  assertFsPathAllowed,
  listAllowedWindowsFiles,
  server,
  _config: {
    FS_MAX_READ_BYTES,
  },
};
