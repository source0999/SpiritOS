#!/usr/bin/env node
import { chromium, devices } from "@playwright/test";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import os from "node:os";

const ROOT = process.cwd();
const BASE_URL = process.env.SPIRITFLIX_PERF_BASE_URL ?? "https://127.0.0.1:3000";
const RUNS = Number(process.env.SPIRITFLIX_PERF_RUNS ?? process.argv.find((arg) => arg.startsWith("--runs="))?.split("=")[1] ?? 15);
const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, "-");
const EVIDENCE_DIR = path.join(ROOT, "docs", "evidence", `spiritflix-prod-perf-${TIMESTAMP}`);
const VIDEO_FIXTURE = path.join(os.tmpdir(), `spiritflix-prod-perf-fixture-${process.pid}.mp4`);

const budgets = {
  coldFirstPaintP75Ms: 400,
  warmFirstPaintP75Ms: 250,
  coldTtiP75Ms: 1200,
  warmTtiP75Ms: 1200,
  warmVideoStartP75Ms: 250,
  coldVideoStartP75Ms: 600,
  scrollFpsP75: 35,
  loadMoreP75Ms: 800,
};

const session = {
  serverUrl: "http://127.0.0.1:8096",
  accessToken: "perf-token",
  userId: "perf-user",
  username: "perf-user",
};

function percentile(values, pct) {
  const valid = values.filter((value) => Number.isFinite(value)).sort((left, right) => left - right);
  if (!valid.length) return null;
  const index = Math.min(valid.length - 1, Math.ceil((pct / 100) * valid.length) - 1);
  return Math.round(valid[index] * 10) / 10;
}

function summary(values) {
  return {
    p50: percentile(values, 50),
    p75: percentile(values, 75),
    p99: percentile(values, 99),
    samples: values.length,
  };
}

function createItems(count) {
  return Array.from({ length: count }, (_, index) => {
    const id = `perf-scene-${String(index + 1).padStart(3, "0")}`;
    return {
      Id: id,
      Name: `Perf Scene ${String(index + 1).padStart(3, "0")}`,
      Type: "Video",
      MediaType: "Video",
      SeriesName: index % 2 === 0 ? "Perf Model A" : "Perf Model B",
      RunTimeTicks: 30_000_000,
      DateCreated: "2026-07-04T00:00:00.000Z",
      UserData: { PlaybackPositionTicks: 0, PlayCount: 0, IsFavorite: index < 4 },
      MediaStreams: [{ Type: "Video", Width: 1080, Height: 1920 }],
      MediaSources: [{ Id: `${id}-source`, Path: `/perf/${id}.mp4`, Container: "mp4" }],
      ImageTags: { Primary: "perf" },
    };
  });
}

const items = createItems(72);

async function ensureVideoFixture() {
  await mkdir(EVIDENCE_DIR, { recursive: true });
  const generated = spawnSync(
    "ffmpeg",
    [
      "-hide_banner",
      "-loglevel",
      "error",
      "-y",
      "-f",
      "lavfi",
      "-i",
      "color=c=black:s=320x180:d=0.5",
      "-f",
      "lavfi",
      "-i",
      "anullsrc=channel_layout=stereo:sample_rate=44100",
      "-shortest",
      "-movflags",
      "faststart",
      "-pix_fmt",
      "yuv420p",
      VIDEO_FIXTURE,
    ],
    { cwd: ROOT, encoding: "utf8" },
  );
  if (generated.status !== 0) {
    throw new Error(`ffmpeg fixture generation failed: ${generated.stderr || generated.stdout}`);
  }
}

async function fulfillVideo(route) {
  const payload = await readFile(VIDEO_FIXTURE);
  const range = route.request().headers().range;
  if (range?.startsWith("bytes=")) {
    const [startText, endText] = range.slice("bytes=".length).split("-");
    const start = Math.max(0, Number(startText) || 0);
    const end = Math.min(payload.length - 1, endText ? Number(endText) : payload.length - 1);
    const body = payload.subarray(start, end + 1);
    return route.fulfill({
      status: 206,
      contentType: "video/mp4",
      body,
      headers: {
        "accept-ranges": "bytes",
        "content-length": String(body.length),
        "content-range": `bytes ${start}-${end}/${payload.length}`,
      },
    });
  }
  return route.fulfill({
    status: 200,
    contentType: "video/mp4",
    body: payload,
    headers: {
      "accept-ranges": "bytes",
      "content-length": String(payload.length),
    },
  });
}

async function clickVolatileLocator(page, selector, timeoutMs = 5_000) {
  const deadline = performance.now() + timeoutMs;
  let lastError;
  while (performance.now() < deadline) {
    try {
      const locator = page.locator(selector).first();
      await locator.waitFor({ state: "visible", timeout: 500 });
      await locator.click({ timeout: 500 });
      return;
    } catch (error) {
      lastError = error;
      await page.waitForTimeout(100);
    }
  }
  throw lastError ?? new Error(`Timed out clicking ${selector}`);
}

async function setupPage(page) {
  await page.addInitScript((storedSession) => {
    window.localStorage.clear();
    window.localStorage.setItem("spiritflix_private_gooner_session", JSON.stringify(storedSession));
    window.localStorage.setItem("spiritflix_player_muted", "true");
    window.localStorage.setItem("spiritflix_player_volume", "0");
    window.localStorage.setItem("spiritflix_library_view_mode", "grid");
    window.localStorage.setItem("spiritflix_library_ui_state", JSON.stringify({
      selectedLibraryId: "perf-library",
      selectedModel: null,
      selectedManualTag: null,
      excludedCategories: [],
      viewMode: "grid",
      sortMode: "name",
      sortDirection: "asc",
      orientationFilter: "all",
      filtersOpen: false,
      pageIndex: 0,
    }));
    window.sessionStorage.clear();
    window.__spiritflixPerfPagedItems = 0;
  }, session);

  await page.route("**/api/spiritflix/model-index**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        schema: "spiritflix-manual-model-index/v1",
        updatedAt: new Date().toISOString(),
        items: [],
        models: [
          { modelName: "Perf Model A", count: 36 },
          { modelName: "Perf Model B", count: 36 },
        ],
      }),
    }),
  );
  await page.route("**/api/spiritflix/gallery**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ schema: "spiritflix-model-gallery/v1", generatedAt: new Date().toISOString(), items: [], groups: [], summary: { galleryItems: 0, modelsWithGallery: 0 } }),
    }),
  );
  await page.route("**/api/spiritflix/face-metadata", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ knownPerformers: [], videos: {}, scannedCount: 0 }),
    }),
  );
  await page.route("**/api/spiritflix/captions/manifest**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ tracks: [] }) }),
  );
  await page.route("**/api/spiritflix/mobile-optimized**", async (route) => {
    const url = new URL(route.request().url());
    if (url.searchParams.get("stream") === "1") {
      return fulfillVideo(route);
    }
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ available: true, url: `/api/spiritflix/mobile-optimized?stream=1&itemId=${encodeURIComponent(url.searchParams.get("itemId") ?? "perf-scene-001")}` }),
    });
  });
  await page.route("**/api/spiritflix/stream**", fulfillVideo);
  await page.route("**/api/spiritflix/jellyfin-image**", (route) =>
    route.fulfill({ status: 204, body: "" }),
  );
  await page.route("**/api/spiritflix/jellyfin", async (route) => {
    const payload = route.request().postDataJSON();
    const requestPath = String(payload.path ?? "");
    if (requestPath === "/System/Info/Public") {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ServerName: "Perf Jellyfin", Version: "10.11.0" }) });
    }
    if (requestPath === "/Users/perf-user/Views") {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ Items: [{ Id: "perf-library", Name: "Library", CollectionType: "movies" }] }) });
    }
    if (requestPath.includes("/Users/perf-user/Items/")) {
      const id = decodeURIComponent(requestPath.split("/Items/")[1]?.split("?")[0] ?? "perf-scene-001");
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(items.find((item) => item.Id === id) ?? items[0]) });
    }
    if (requestPath.includes("/Users/perf-user/Items")) {
      const query = new URLSearchParams(requestPath.split("?")[1] ?? "");
      const startIndex = Number(query.get("StartIndex") ?? "0");
      const limit = Number(query.get("Limit") ?? "48");
      const filters = query.get("Filters") ?? "";
      const sortBy = query.get("SortBy") ?? "";
      let pageItems = items;
      if (filters.includes("IsFavorite")) pageItems = items.filter((item) => item.UserData?.IsFavorite);
      if (filters.includes("IsResumable")) pageItems = [];
      if (sortBy === "DatePlayed") pageItems = [];
      const slice = pageItems.slice(startIndex, startIndex + limit);
      if (startIndex > 0) {
        await page.evaluate(() => {
          window.__spiritflixPerfPagedItems = (window.__spiritflixPerfPagedItems || 0) + 1;
        }).catch(() => undefined);
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ Items: slice, TotalRecordCount: pageItems.length, StartIndex: startIndex }),
      });
    }
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ Items: [], TotalRecordCount: 0 }) });
  });
}

async function measureLoad(context, warm) {
  const page = await context.newPage();
  await setupPage(page);
  const started = performance.now();
  await page.goto(`${BASE_URL}/spiritflix?library=perf-library`, { waitUntil: "domcontentloaded", timeout: 20_000 });
  await page.locator(".spiritflix-shell").waitFor({ state: "visible", timeout: 15_000 });
  const firstPaintMs = performance.now() - started;
  await page.locator("text=Perf Scene 001").first().waitFor({ state: "visible", timeout: 15_000 });
  await page.locator('[data-spiritflix-useful-content="ready"]').waitFor({ state: "visible", timeout: 15_000 });
  await page.waitForFunction(() => !document.querySelector('[role="progressbar"]'), null, { timeout: 15_000 });
  const ttiMs = performance.now() - started;

  const scrollFps = await page.evaluate(async () => {
    const samples = [];
    let last = performance.now();
    const end = last + 700;
    window.scrollTo(0, 0);
    return await new Promise((resolve) => {
      function step(now) {
        samples.push(now - last);
        last = now;
        window.scrollBy(0, 90);
        if (now < end) requestAnimationFrame(step);
        else {
          const avgFrame = samples.reduce((sum, value) => sum + value, 0) / Math.max(1, samples.length);
          resolve(1000 / avgFrame);
        }
      }
      requestAnimationFrame(step);
    });
  });

  await page.getByRole("button", { name: "Library", exact: true }).click({ timeout: 5_000 });
  await page.getByRole("region", { name: /library model library/i }).waitFor({ state: "visible", timeout: 5_000 });
  const gridButton = page.getByRole("button", { name: "Grid" });
  if (await gridButton.count()) {
    if ((await gridButton.getAttribute("aria-pressed")) !== "true") {
      await gridButton.click({ timeout: 5_000 });
    }
  }
  await page.locator("text=Perf Scene 001").first().waitFor({ state: "visible", timeout: 5_000 });
  const loadMoreStarted = performance.now();
  await page.evaluate(() => {
    window.__spiritflixPerfPagedItems = 0;
  });
  let paginationMeasured = false;
  try {
    const loadMoreButton = page.locator('button[aria-label="Load more library videos"]');
    if (!(await loadMoreButton.count())) throw new Error("load-more-unavailable");
    await page.waitForFunction(() => {
      const button = document.querySelector('button[aria-label="Load more library videos"]');
      return Boolean(button && !button.disabled);
    }, null, { timeout: 1_000 });
    await clickVolatileLocator(page, 'button[aria-label="Load more library videos"]');
    await page.waitForFunction(() => (window.__spiritflixPerfPagedItems || 0) > 0, null, { timeout: 5_000 });
    paginationMeasured = true;
  } catch {
    try {
      await clickVolatileLocator(page, 'button[aria-label="Next video page"]');
      await page.locator("text=Perf Scene 021").first().waitFor({ state: "visible", timeout: 5_000 });
      paginationMeasured = true;
    } catch {
      paginationMeasured = false;
    }
  }
  const loadMoreMs = paginationMeasured ? performance.now() - loadMoreStarted : 0;

  await page.close();
  return { mode: warm ? "warm" : "cold", firstPaintMs, ttiMs, scrollFps, loadMoreMs };
}

async function measureVideoStart(context, warm) {
  const page = await context.newPage();
  await setupPage(page);
  await page.goto(`${BASE_URL}/spiritflix/benchmark/player?itemId=perf-scene-001&sourcePath=/perf/perf-scene-001.mp4&autoplay=0`, { waitUntil: "domcontentloaded", timeout: 20_000 });
  await page.locator(".spiritflix-player").waitFor({ state: "visible", timeout: 10_000 });
  const started = performance.now();
  await page.locator(".spiritflix-player__play").waitFor({ state: "attached", timeout: 5_000 });
  await page.locator(".spiritflix-player__play").click({ force: true, timeout: 5_000 });
  try {
    await page.waitForFunction(() => {
      const video = document.querySelector("video");
      return Boolean(video && video.readyState >= 2);
    }, null, { timeout: 10_000 });
  } catch (error) {
    const videoState = await page.evaluate(() => {
      const video = document.querySelector("video");
      if (!video) return null;
      return {
        readyState: video.readyState,
        networkState: video.networkState,
        currentSrc: video.currentSrc || video.getAttribute("src") || "",
        error: video.error ? { code: video.error.code, message: video.error.message } : null,
      };
    });
    throw new Error(`Video did not reach readyState 2: ${JSON.stringify(videoState)}`, { cause: error });
  }
  const videoStartMs = performance.now() - started;
  await page.close();
  return { mode: warm ? "warm" : "cold", videoStartMs };
}

async function run() {
  await ensureVideoFixture();
  const browser = await chromium.launch({ headless: true });
  const device = devices["Desktop Chrome"];
  const coldLoads = [];
  const warmLoads = [];
  const coldVideos = [];
  const warmVideos = [];

  try {
    for (let index = 0; index < RUNS; index += 1) {
      const context = await browser.newContext({ ...device, ignoreHTTPSErrors: true, serviceWorkers: "block" });
      coldLoads.push(await measureLoad(context, false));
      coldVideos.push(await measureVideoStart(context, false));
      await context.close();
    }

    const warmContext = await browser.newContext({ ...device, ignoreHTTPSErrors: true });
    for (let index = 0; index < RUNS; index += 1) {
      warmLoads.push(await measureLoad(warmContext, true));
      warmVideos.push(await measureVideoStart(warmContext, true));
    }
    await warmContext.close();
  } finally {
    await browser.close();
  }

  const metrics = {
    coldFirstPaintMs: summary(coldLoads.map((run) => run.firstPaintMs)),
    warmFirstPaintMs: summary(warmLoads.map((run) => run.firstPaintMs)),
    coldTtiMs: summary(coldLoads.map((run) => run.ttiMs)),
    warmTtiMs: summary(warmLoads.map((run) => run.ttiMs)),
    coldVideoStartMs: summary(coldVideos.map((run) => run.videoStartMs)),
    warmVideoStartMs: summary(warmVideos.map((run) => run.videoStartMs)),
    scrollFps: summary([...coldLoads, ...warmLoads].map((run) => run.scrollFps)),
    loadMoreMs: summary([...coldLoads, ...warmLoads].map((run) => run.loadMoreMs)),
  };

  const failures = [];
  if (metrics.coldFirstPaintMs.p75 > budgets.coldFirstPaintP75Ms) failures.push(`cold first-paint p75 ${metrics.coldFirstPaintMs.p75} > ${budgets.coldFirstPaintP75Ms}`);
  if (metrics.warmFirstPaintMs.p75 > budgets.warmFirstPaintP75Ms) failures.push(`warm first-paint p75 ${metrics.warmFirstPaintMs.p75} > ${budgets.warmFirstPaintP75Ms}`);
  if (metrics.coldTtiMs.p75 > budgets.coldTtiP75Ms) failures.push(`cold TTI p75 ${metrics.coldTtiMs.p75} > ${budgets.coldTtiP75Ms}`);
  if (metrics.warmTtiMs.p75 > budgets.warmTtiP75Ms) failures.push(`warm TTI p75 ${metrics.warmTtiMs.p75} > ${budgets.warmTtiP75Ms}`);
  if (metrics.warmVideoStartMs.p75 > budgets.warmVideoStartP75Ms) failures.push(`warm video-start p75 ${metrics.warmVideoStartMs.p75} > ${budgets.warmVideoStartP75Ms}`);
  if (metrics.coldVideoStartMs.p75 > budgets.coldVideoStartP75Ms) failures.push(`cold video-start p75 ${metrics.coldVideoStartMs.p75} > ${budgets.coldVideoStartP75Ms}`);
  if (metrics.scrollFps.p75 < budgets.scrollFpsP75) failures.push(`scroll FPS p75 ${metrics.scrollFps.p75} < ${budgets.scrollFpsP75}`);
  if (metrics.loadMoreMs.p75 > budgets.loadMoreP75Ms) failures.push(`load more p75 ${metrics.loadMoreMs.p75} > ${budgets.loadMoreP75Ms}`);

  const payload = {
    generatedAt: new Date().toISOString(),
    baseUrl: BASE_URL,
    runs: RUNS,
    budgets,
    ok: failures.length === 0,
    failures,
    metrics,
    raw: { coldLoads, warmLoads, coldVideos, warmVideos },
    fixtureNote: "Representative mocked Jellyfin library against prod :3000. Synthetic 50ms budget is covered separately by npm run spiritflix:perf:synthetic.",
  };

  const metricsPath = path.join(EVIDENCE_DIR, "metrics.json");
  await writeFile(metricsPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  console.log(JSON.stringify({ ok: payload.ok, evidenceDir: EVIDENCE_DIR, metrics, failures }, null, 2));
  if (failures.length) process.exit(1);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
