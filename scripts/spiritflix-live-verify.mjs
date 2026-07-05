#!/usr/bin/env node
import { chromium } from "playwright";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { performance } from "node:perf_hooks";

const ROOT = resolve(new URL("..", import.meta.url).pathname);
const JELLYFIN_URL = (process.env.SPIRITFLIX_VERIFY_JELLYFIN_URL ?? "http://127.0.0.1:8096").replace(/\/+$/, "");
const DB_PATH = process.env.SPIRITFLIX_VERIFY_DB_PATH ?? "/mnt/spirit-8tb/services/jellyfin/config/data/jellyfin.db";
const VERIFY_LATEST_ONLY = process.env.SPIRITFLIX_VERIFY_LATEST_ONLY === "1";
const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
const evidenceDir = join(ROOT, "docs", "evidence", `spiritflix-live-verify-${timestamp}`);
mkdirSync(evidenceDir, { recursive: true });

function run(command, { timeout = 120000, allowFail = false } = {}) {
  const result = spawnSync("bash", ["-lc", command], {
    cwd: ROOT,
    encoding: "utf8",
    timeout,
    maxBuffer: 1024 * 1024 * 20,
  });
  if (!allowFail && result.status !== 0) {
    throw new Error(`Command failed (${result.status}): ${command}\n${result.stdout}\n${result.stderr}`);
  }
  return result;
}

function toQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return query.toString();
}

function authHeader(token) {
  return `MediaBrowser Client="SpiritFlix", Device="SpiritFlix Live Verify", DeviceId="spiritflix-live-verify", Version="0.1.0", Token="${token}"`;
}

function getAuthCandidates() {
  const python = String.raw`
import json
import sqlite3
import sys
con = sqlite3.connect(sys.argv[1])
con.row_factory = sqlite3.Row
rows = con.execute("""
select d.AccessToken as accessToken, d.UserId as userId, u.Username as username, d.DeviceName as deviceName,
       d.DateLastActivity as dateLastActivity, d.DateModified as dateModified, d.DateCreated as dateCreated
from Devices d
join Users u on u.Id = d.UserId
where d.AccessToken is not null and length(d.AccessToken) > 10
order by coalesce(d.DateLastActivity, d.DateModified, d.DateCreated) desc
limit 25
""").fetchall()
print(json.dumps([dict(row) for row in rows]))
`;
  const result = spawnSync("python3", ["-c", python, DB_PATH], { encoding: "utf8", maxBuffer: 1024 * 1024 });
  if (result.status !== 0) throw new Error(`Could not read Jellyfin auth candidates: ${result.stderr || result.stdout}`);
  return JSON.parse(result.stdout || "[]");
}

async function jellyfinFetch(auth, apiPath) {
  const response = await fetch(`${auth.serverUrl}${apiPath}`, {
    headers: {
      Accept: "application/json",
      "X-Emby-Token": auth.accessToken,
      "X-Emby-Authorization": authHeader(auth.accessToken),
    },
  });
  const body = await response.json().catch(() => null);
  return { ok: response.ok, status: response.status, body };
}

async function resolveAuth() {
  for (const candidate of getAuthCandidates()) {
    const auth = { ...candidate, serverUrl: JELLYFIN_URL };
    const validation = await jellyfinFetch(auth, `/Users/${encodeURIComponent(auth.userId)}/Views`);
    if (validation.ok && Array.isArray(validation.body?.Items)) return auth;
  }
  throw new Error("No active Jellyfin DB token could access /Users/{id}/Views.");
}

function isHomeVideosShell(library) {
  const name = String(library.Name ?? "").trim().toLowerCase();
  return name === "home videos" || name === "home videos and photos" || String(library.CollectionType ?? "").toLowerCase() === "homevideos";
}

async function resolveDefaultFolder(auth) {
  const views = await jellyfinFetch(auth, `/Users/${encodeURIComponent(auth.userId)}/Views`);
  if (!views.ok) throw new Error(`Jellyfin views failed: ${views.status}`);
  const folderQuery = toQuery({
    Recursive: false,
    IncludeItemTypes: "Folder",
    Fields: "Path",
    ImageTypeLimit: 1,
    EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
    SortBy: "SortName",
    SortOrder: "Ascending",
    Limit: 100,
  });
  const folders = await jellyfinFetch(auth, `/Users/${encodeURIComponent(auth.userId)}/Items?${folderQuery}`);
  const libraries = [...(views.body?.Items ?? []), ...(folders.body?.Items ?? [])];
  const defaultNames = new Set(["yes", "media", "other"]);
  const defaultFolder = libraries.find((library) => defaultNames.has(String(library.Name ?? "").trim().toLowerCase()) && !isHomeVideosShell(library));
  const fallbackShell = libraries.find(isHomeVideosShell);
  if (!defaultFolder && !fallbackShell) {
    throw new Error(`No default media folder found. Libraries: ${libraries.map((library) => `${library.Name}:${library.Id}`).join(", ")}`);
  }
  return defaultFolder ?? fallbackShell;
}

function writeProxy(proxyPath) {
  const localKeyPath = join(ROOT, "certificates", "spirit-dev-key.pem");
  const localCertPath = join(ROOT, "certificates", "spirit-dev.pem");
  const keyPath = existsSync(localKeyPath) ? localKeyPath : "/home/source/SpiritOS/certificates/spirit-dev-key.pem";
  const certPath = existsSync(localCertPath) ? localCertPath : "/home/source/SpiritOS/certificates/spirit-dev.pem";
  writeFileSync(proxyPath, `
import http from "node:http";
import https from "node:https";
import { readFileSync } from "node:fs";
const key = readFileSync("${keyPath}");
const cert = readFileSync("${certPath}");
const server = https.createServer({ key, cert }, (req, res) => {
  const proxy = http.request({
    hostname: "127.0.0.1",
    port: 3002,
    method: req.method,
    path: req.url,
    headers: { ...req.headers, host: "127.0.0.1:3000", "x-forwarded-proto": "https" },
  }, (upstream) => {
    res.writeHead(upstream.statusCode ?? 502, upstream.headers);
    upstream.pipe(res);
  });
  proxy.on("error", (error) => {
    res.writeHead(502, { "content-type": "text/plain" });
    res.end(String(error?.message ?? error));
  });
  req.pipe(proxy);
});
server.listen(3000, "0.0.0.0", () => console.log("SpiritFlix verify HTTPS proxy listening on :3000 -> :3002"));
`);
}

async function restartProd() {
  const proxyPath = join(evidenceDir, "https-proxy.mjs");
  writeProxy(proxyPath);
  run("tmux kill-session -t spiritos-lan 2>/dev/null || true; pkill -f 'next dev .*3000' 2>/dev/null || true; pkill -f 'npm run dev:https:lan' 2>/dev/null || true; pkill -f 'npm exec next start.*3002|next start .*3002|next-server|spiritflix-restore-proxy|https-proxy.mjs' 2>/dev/null || true; fuser -k 3000/tcp 3002/tcp 2>/dev/null || true; sleep 2; fuser -k 3000/tcp 3002/tcp 2>/dev/null || true", { allowFail: true });
  run("npm run build", { timeout: 900000 });
  run(`nohup npm exec -- next start -H 0.0.0.0 -p 3002 > ${join(evidenceDir, "next-start-3002.log")} 2>&1 & echo $! > ${join(evidenceDir, "next-start-3002.pid")}`);
  run(`nohup node ${proxyPath} > ${join(evidenceDir, "https-proxy-3000.log")} 2>&1 & echo $! > ${join(evidenceDir, "https-proxy-3000.pid")}`);
  const expectedNextPid = readFileSync(join(evidenceDir, "next-start-3002.pid"), "utf8").trim();
  const expectedProxyPid = readFileSync(join(evidenceDir, "https-proxy-3000.pid"), "utf8").trim();
  const startedAt = Date.now();
  while (Date.now() - startedAt < 30000) {
    const probe = run("curl -k -s -o /dev/null -w '%{http_code}' https://127.0.0.1:3000/spiritflix", { allowFail: true, timeout: 10000 });
    const listeners = run("ss -ltnp '( sport = :3000 or sport = :3002 )' || true", { allowFail: true }).stdout;
    if (String(probe.stdout).trim() === "200" && listeners.includes(expectedProxyPid) && listeners.includes("3002")) return;
    await new Promise((resolveTimeout) => setTimeout(resolveTimeout, 1000));
  }
  const logs = [
    readFileSync(join(evidenceDir, "next-start-3002.log"), "utf8"),
    readFileSync(join(evidenceDir, "https-proxy-3000.log"), "utf8"),
  ].join("\n");
  if (!run(`ps -p ${expectedNextPid} -o pid= 2>/dev/null`, { allowFail: true }).stdout.trim()) {
    throw new Error(`next start process ${expectedNextPid} exited before health check.\n${logs}`);
  }
  if (!run(`ps -p ${expectedProxyPid} -o pid= 2>/dev/null`, { allowFail: true }).stdout.trim()) {
    throw new Error(`HTTPS proxy process ${expectedProxyPid} exited before health check.\n${logs}`);
  }
  throw new Error("Production HTTPS route did not become healthy on :3000.");
}

async function seedPage(page, auth) {
  await page.addInitScript((session) => {
    window.localStorage.setItem("spiritflix_private_gooner_session", JSON.stringify(session));
    window.sessionStorage.clear();
  }, {
    serverUrl: auth.serverUrl,
    accessToken: auth.accessToken,
    userId: auth.userId,
    username: auth.username,
  });
}

async function waitForReady(page) {
  const started = performance.now();
  await page.waitForSelector(".spiritflix-card, [data-spiritflix-rail='Latest Added']", { timeout: 20000 });
  const firstCardMs = Math.round(performance.now() - started);
  await page.waitForFunction(() => {
    const progress = document.querySelector(".spiritflix-load-progress");
    const restore = document.querySelector(".spiritflix-restore");
    return !progress && !restore;
  }, null, { timeout: 20000 });
  const readyMs = Math.round(performance.now() - started);
  return { firstCardMs, readyMs };
}

async function captureLatest(page) {
  const rail = page.locator('[data-spiritflix-rail="Latest Added"]').first();
  await rail.waitFor({ timeout: 10000 });
  const items = await rail.locator("[data-spiritflix-item-id]").evaluateAll((nodes) =>
    nodes.map((node) => ({
      id: node.getAttribute("data-spiritflix-item-id") ?? "",
      title: node.getAttribute("data-spiritflix-item-title") ?? "",
    })),
  );
  if (!items.length) throw new Error("Latest Added rail had no items.");
  return items;
}

async function captureModelCounts(page) {
  const read = async () =>
    page.locator("[data-spiritflix-model-card]").evaluateAll((nodes) =>
      nodes.map((node) => ({
        model: node.getAttribute("data-spiritflix-model-card") ?? "",
        count: node.getAttribute("data-spiritflix-model-count") ?? "",
        text: node.textContent?.replace(/\s+/g, " ").trim() ?? "",
      })),
    );
  const t0 = await read();
  if (!t0.length) throw new Error("No model-count badges were found after Ready.");
  await page.waitForTimeout(1500);
  const t1500 = await read();
  await page.waitForTimeout(1500);
  const t3000 = await read();
  return { t0, t1500, t3000 };
}

function assertSameLatest(home, library, label) {
  const homeIds = home.map((item) => item.id);
  const libraryIds = library.map((item) => item.id);
  if (homeIds.join("|") !== libraryIds.join("|")) {
    throw new Error(`${label}: Latest Added mismatch\nhome=${JSON.stringify(home, null, 2)}\nlibrary=${JSON.stringify(library, null, 2)}`);
  }
}

function assertStableCounts(samples, label) {
  for (const [sampleName, sample] of Object.entries(samples)) {
    const bad = sample.filter((entry) => /counting/i.test(entry.text) || !/\d+/.test(entry.text));
    if (bad.length) throw new Error(`${label}: bad model count sample ${sampleName}: ${JSON.stringify(bad, null, 2)}`);
  }
  if (JSON.stringify(samples.t0) !== JSON.stringify(samples.t1500) || JSON.stringify(samples.t0) !== JSON.stringify(samples.t3000)) {
    throw new Error(`${label}: model counts changed after Ready: ${JSON.stringify(samples, null, 2)}`);
  }
}

async function verifyViewport(browser, auth, defaultFolder, viewport) {
  const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: viewport.size, isMobile: viewport.mobile });
  const page = await context.newPage();
  await seedPage(page, auth);

  const homeUrl = "https://127.0.0.1:3000/spiritflix";
  const libraryUrl = `https://127.0.0.1:3000/spiritflix?library=${encodeURIComponent(defaultFolder.Id)}`;

  await page.goto(homeUrl, { waitUntil: "domcontentloaded" });
  const homeTimeline = await waitForReady(page);
  const homeLatest = await captureLatest(page);

  await page.goto(libraryUrl, { waitUntil: "domcontentloaded" });
  const libraryTimeline = await waitForReady(page);
  const libraryLatest = await captureLatest(page);
  assertSameLatest(homeLatest, libraryLatest, viewport.name);

  let modelCounts = null;
  if (!VERIFY_LATEST_ONLY) {
    modelCounts = await captureModelCounts(page);
    assertStableCounts(modelCounts, viewport.name);
  }

  await context.close();
  return {
    viewport: viewport.name,
    homeUrl,
    libraryUrl,
    defaultFolder: { id: defaultFolder.Id, name: defaultFolder.Name },
    latestAdded: { home: homeLatest, library: libraryLatest },
    modelCounts,
    timeline: {
      home: homeTimeline,
      library: {
        ...libraryTimeline,
        modelCountsStableMs: modelCounts ? libraryTimeline.readyMs + 3000 : null,
      },
    },
    pass: true,
  };
}

async function main() {
  const auth = await resolveAuth();
  const defaultFolder = await resolveDefaultFolder(auth);
  await restartProd();

  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const viewport of [
      { name: "mobile", size: { width: 375, height: 812 }, mobile: true },
      { name: "desktop", size: { width: 1440, height: 900 }, mobile: false },
    ]) {
      results.push(await verifyViewport(browser, auth, defaultFolder, viewport));
    }
  } finally {
    await browser.close();
  }

  const ps = run("ps -eo pid,cmd | grep -E 'next (start|dev)|https-proxy|3002|3000' | grep -v grep || true", { allowFail: true }).stdout;
  const payload = {
    generatedAt: new Date().toISOString(),
    latestOnly: VERIFY_LATEST_ONLY,
    auth: { serverUrl: auth.serverUrl, userId: auth.userId, username: auth.username, accessToken: "[redacted]" },
    ps,
    results,
  };
  writeFileSync(join(evidenceDir, "results.json"), JSON.stringify(payload, null, 2));
  console.log(JSON.stringify(payload, null, 2));
}

main().catch((error) => {
  const payload = { generatedAt: new Date().toISOString(), pass: false, error: error?.stack || String(error), evidenceDir };
  writeFileSync(join(evidenceDir, "failure.json"), JSON.stringify(payload, null, 2));
  console.error(payload.error);
  process.exit(1);
});
