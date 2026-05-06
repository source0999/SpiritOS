#!/usr/bin/env node
/* eslint-disable @typescript-eslint/no-require-imports -- shipped as plain Node CJS for Windows */
// ── Spirit Desktop - LAN telemetry stub ─────────────────────────────────────
// Drop-in for Windows: exposes GET /api/telemetry/self matching ClusterNodeTelemetry.
// Dell Next calls this server-side - use the desktop LAN IP in SPIRITDESKTOP_TELEMETRY_URL,
// not localhost on the Dell. Plain HTTP + bearer token is intentional for trusted LAN.
//
// ── DEPLOYMENT (read this before opening another “storage missing” ticket) ──
// Editing scripts/spiritdesktop-windows/agent.js in the SpiritOS repo does NOTHING to a
// machine that is already running an old copy. You must copy this file onto spiritdesktop
// (or whatever path you launch from) and **restart** the Node process (`node agent.js`).
// Sanity check from the Dell: curl -H "Authorization: Bearer <token>"
//   http://<spiritdesktop-lan-ip>:3000/api/telemetry/self
// The JSON must include a top-level `storage` object. If it does not, you are still on
// legacy agent code or a different file is being executed.

const http = require("node:http");
const os = require("node:os");
const { execSync } = require("node:child_process");

const PORT = Number.parseInt(process.env.PORT || "3000", 10);
const TOKEN = (process.env.SPIRIT_TELEMETRY_TOKEN || "3399").trim();
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

// ── Storage (Windows - Win32_LogicalDisk) ─────────────────────────────────────
// CIM properties are UInt64; ConvertTo-Json often emits Size/FreeSpace as **strings**.
// If we only accept typeof === "number", every drive is dropped and the UI shows empty
// storage with no JSON error - brutal to debug. Coerce with num().

function num(v) {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "bigint") return Number(v);
  if (typeof v === "string" && v.trim() !== "") {
    const n = Number(v.trim());
    if (Number.isFinite(n)) return n;
  }
  return null;
}

function collectWindowsStorage() {
  const now = new Date().toISOString();
  try {
    const output = execSync(
      "powershell -NoProfile -NonInteractive -Command \"Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,VolumeName,Size,FreeSpace,FileSystem | ConvertTo-Json -Depth 2\"",
      { timeout: 3000, encoding: "utf8" },
    );
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
        return {
          id: d.DeviceID,
          name: d.VolumeName ? `${d.DeviceID} (${d.VolumeName})` : d.DeviceID,
          mount: d.DeviceID,
          fsType: d.FileSystem || null,
          type: "UNKNOWN",
          totalBytes,
          usedBytes,
          freeBytes,
          usedPct,
          tempC: null,
          smart: "Unknown",
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

  if (url.pathname !== "/api/telemetry/self" || req.method !== "GET") {
    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "not found" }));
    return;
  }

  if (!bearerMatches(req)) {
    unauthorized(res);
    return;
  }

  try {
    const body = await buildTelemetryPayload();
    res.writeHead(200, {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(body));
  } catch (err) {
    res.writeHead(500, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: err instanceof Error ? err.message : "internal error" }));
  }
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(
    `[spiritdesktop-agent] listening on http://0.0.0.0:${PORT}/api/telemetry/self (plain HTTP, not HTTPS). TOKEN len=${TOKEN.length}`,
  );
});
