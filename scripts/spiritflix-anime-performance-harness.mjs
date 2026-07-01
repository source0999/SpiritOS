#!/usr/bin/env node
/**
 * SpiritFlix anime performance harness.
 *
 * Measures real authenticated SpiritFlix/Jellyfin routes, first-screen content,
 * first-screen thumbnails, API latency, playback readiness, source selection,
 * range usage, and Dell CPU/process state.
 */

import { chromium } from "@playwright/test";
import { Agent, setGlobalDispatcher } from "undici";
import fs from "node:fs/promises";
import path from "node:path";
import { performance } from "node:perf_hooks";
import { spawnSync } from "node:child_process";

if ((process.env.SPIRITFLIX_PERF_INSECURE_TLS ?? "1") === "1") {
  setGlobalDispatcher(new Agent({ connect: { rejectUnauthorized: false } }));
}

const ROOT = process.cwd();
const DEFAULT_BASE_URL = "https://spirit.tailb69ea6.ts.net:3000";
const DEFAULT_JELLYFIN_URL = "http://127.0.0.1:8096";
const DEFAULT_DB_PATH = "/mnt/spirit-8tb/services/jellyfin/config/data/jellyfin.db";
const DESKTOP_FIRST_SCREEN_LIMIT = 48;
const MOBILE_FIRST_SCREEN_LIMIT = 24;
const ANIME_FULL_PROBE_LIMIT = 500;
const PLAYBACK_STALL_WINDOW_MS = 10_000;

const VIEWPORTS = {
  desktop: {
    name: "desktop",
    label: "Desktop 1440x900",
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    isMobile: false,
    hasTouch: false,
    firstScreenLimit: DESKTOP_FIRST_SCREEN_LIMIT,
  },
  fold7: {
    name: "fold7",
    label: "Samsung Fold 7 main display emulation",
    viewport: { width: 656, height: 728 },
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true,
    firstScreenLimit: MOBILE_FIRST_SCREEN_LIMIT,
  },
};

function timestamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "-");
}

function argValue(name, fallback) {
  const prefixed = `--${name}=`;
  const withEquals = process.argv.find((arg) => arg.startsWith(prefixed));
  if (withEquals) return withEquals.slice(prefixed.length);
  const index = process.argv.indexOf(`--${name}`);
  if (index >= 0 && process.argv[index + 1]) return process.argv[index + 1];
  return fallback;
}

function parseArgs() {
  const selectedViewports = argValue("viewports", process.env.SPIRITFLIX_PERF_VIEWPORTS ?? "desktop,fold7")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .map((name) => {
      if (!VIEWPORTS[name]) throw new Error(`Unknown viewport '${name}'. Use one of: ${Object.keys(VIEWPORTS).join(", ")}`);
      return VIEWPORTS[name];
    });

  return {
    label: argValue("label", process.env.SPIRITFLIX_PERF_LABEL ?? "run").replace(/[^a-z0-9_.-]+/gi, "-").toLowerCase(),
    runs: Number(argValue("runs", process.env.SPIRITFLIX_PERF_RUNS ?? "3")),
    baseUrl: argValue("base-url", process.env.PLAYWRIGHT_BASE_URL ?? process.env.SPIRITFLIX_PERF_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/+$/, ""),
    jellyfinUrl: argValue("jellyfin-url", process.env.SPIRITFLIX_PERF_JELLYFIN_URL ?? DEFAULT_JELLYFIN_URL).replace(/\/+$/, ""),
    dbPath: argValue("db-path", process.env.SPIRITFLIX_PERF_DB_PATH ?? DEFAULT_DB_PATH),
    evidenceDir: path.resolve(argValue(
      "evidence-dir",
      process.env.SPIRITFLIX_PERF_EVIDENCE_DIR ?? path.join(ROOT, "docs", "evidence", `spiritflix-anime-perf-${timestamp()}`),
    )),
    viewports: selectedViewports,
    skipPlayback: process.argv.includes("--skip-playback"),
    stallWindowMs: Number(argValue("stall-window-ms", process.env.SPIRITFLIX_PERF_STALL_WINDOW_MS ?? String(PLAYBACK_STALL_WINDOW_MS))),
  };
}

function toQuery(params) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  }
  return query.toString();
}

function authHeader(token) {
  return [
    'MediaBrowser Client="SpiritFlixPerf"',
    'Device="Codex Harness"',
    'DeviceId="spiritflix-perf-harness"',
    'Version="1.0"',
    `Token="${token}"`,
  ].join(", ");
}

function redactValue(value) {
  return String(value)
    .replace(/(api_key=)[^&\s]+/gi, "$1[redacted]")
    .replace(/(token=)[^&\s]+/gi, "$1[redacted]")
    .replace(/(AccessToken=)[^&\s]+/gi, "$1[redacted]")
    .replace(/(--token\s+)\S+/gi, "$1[redacted]")
    .replace(/(Bearer\s+)[A-Za-z0-9._-]+/g, "$1[redacted]");
}

function redactUrl(value) {
  try {
    const url = new URL(value);
    for (const key of ["token", "api_key", "AccessToken", "X-Emby-Token"]) {
      if (url.searchParams.has(key)) url.searchParams.set(key, "[redacted]");
    }
    return url.toString();
  } catch {
    return redactValue(value);
  }
}

function sanitizeCpuOutput(stdout) {
  return redactValue(stdout)
    .split("\n")
    .filter((line) => !line.includes("cloudflared --no-autoupdate tunnel run"))
    .join("\n");
}

function collectCpuSnapshot(label) {
  const script = [
    "date -Iseconds",
    "printf '\\n--- top cpu ---\\n'",
    "ps -eo pid,ppid,pcpu,pmem,etime,cmd --sort=-pcpu | head -25",
    "printf '\\n--- media processes ---\\n'",
    "pgrep -af 'ffmpeg|jellyfin|next-server|media-ingest-worker|transcode' || true",
  ].join("; ");
  const result = spawnSync("bash", ["-lc", script], { encoding: "utf8", maxBuffer: 1024 * 1024 });
  return {
    label,
    at: new Date().toISOString(),
    ok: result.status === 0,
    stdout: sanitizeCpuOutput(result.stdout ?? ""),
    stderr: sanitizeCpuOutput(result.stderr ?? ""),
  };
}

function classifyFfmpegProcesses(cpuSnapshot) {
  const lines = `${cpuSnapshot.stdout}\n${cpuSnapshot.stderr}`.split("\n").filter((line) => /\bffmpeg\b/i.test(line));
  return lines.map((line) => ({
    line,
    pathClass: line.includes("/mnt/spirit-8tb/media-processing/")
      ? "media_processing"
      : line.includes("jellyfin") || line.includes("/transcodes/") || line.includes("/cache/transcodes/")
        ? "jellyfin_transcode"
        : "other",
  }));
}

function getAuthCandidates(dbPath) {
  const python = String.raw`
import json
import sqlite3
import sys

con = sqlite3.connect(sys.argv[1])
con.row_factory = sqlite3.Row
rows = con.execute("""
select
  d.AccessToken as accessToken,
  d.UserId as userId,
  u.Username as username,
  d.DeviceName as deviceName,
  d.DateLastActivity as dateLastActivity,
  d.DateModified as dateModified,
  d.DateCreated as dateCreated
from Devices d
join Users u on u.Id = d.UserId
where d.AccessToken is not null
  and length(d.AccessToken) > 10
order by coalesce(d.DateLastActivity, d.DateModified, d.DateCreated) desc
limit 25
""").fetchall()
print(json.dumps([dict(row) for row in rows]))
`;
  const result = spawnSync("python3", ["-c", python, dbPath], { encoding: "utf8", maxBuffer: 1024 * 1024 });
  if (result.status !== 0) {
    throw new Error(`Could not read Jellyfin auth candidates from DB: ${result.stderr || result.stdout}`);
  }
  return JSON.parse(result.stdout || "[]");
}

async function jellyfinFetchJson(auth, apiPath, options = {}) {
  const started = performance.now();
  const response = await fetch(`${auth.serverUrl}${apiPath}`, {
    method: options.method ?? "GET",
    headers: {
      Accept: "application/json",
      "X-Emby-Token": auth.accessToken,
      "X-Emby-Authorization": authHeader(auth.accessToken),
      ...(options.headers ?? {}),
    },
    body: options.body,
  });
  const elapsedMs = performance.now() - started;
  const text = await response.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { text };
  }
  return {
    ok: response.ok,
    status: response.status,
    elapsedMs,
    bytes: Buffer.byteLength(text),
    body,
  };
}

async function resolveAuth(config) {
  const candidates = getAuthCandidates(config.dbPath);
  for (const candidate of candidates) {
    const auth = {
      serverUrl: config.jellyfinUrl,
      accessToken: candidate.accessToken,
      userId: candidate.userId,
      username: candidate.username,
      deviceName: candidate.deviceName,
      dateLastActivity: candidate.dateLastActivity,
    };
    const validation = await jellyfinFetchJson(auth, `/Users/${encodeURIComponent(auth.userId)}/Views`);
    if (validation.ok && Array.isArray(validation.body?.Items)) return auth;
  }
  throw new Error("No active Jellyfin device token from the local DB could access /Users/{id}/Views.");
}

function redactedAuth(auth) {
  return {
    serverUrl: auth.serverUrl,
    userId: auth.userId,
    username: auth.username,
    deviceName: auth.deviceName,
    dateLastActivity: auth.dateLastActivity,
    accessToken: "[redacted]",
  };
}

function isMediaLibrary(library) {
  const name = String(library.Name ?? "").toLowerCase();
  const collectionType = String(library.CollectionType ?? "").toLowerCase();
  return (
    name === "anime" ||
    name === "other" ||
    ["movies", "tvshows", "homevideos", "musicvideos"].includes(collectionType)
  );
}

function isPlayable(item) {
  const type = String(item.Type ?? "").toLowerCase();
  const mediaType = String(item.MediaType ?? "").toLowerCase();
  return mediaType === "video" || ["movie", "episode", "video"].includes(type);
}

async function getLibraryItemsPage(auth, libraryId, { limit, startIndex = 0, playableOnly = false } = {}) {
  const query = toQuery({
    ParentId: libraryId,
    Recursive: true,
    IncludeItemTypes: playableOnly ? "Movie,Episode,Video" : "Movie,Series,Season,Episode,Video,Folder",
    Fields: "Path,SeriesName,DateCreated,IndexNumber,ParentIndexNumber,ProductionYear,RunTimeTicks,UserData,PrimaryImageAspectRatio,MediaStreams,MediaSources,ChildCount",
    ImageTypeLimit: 1,
    EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
    SortBy: "SortName",
    SortOrder: "Ascending",
    Limit: limit,
    StartIndex: startIndex,
  });
  const apiPath = `/Users/${encodeURIComponent(auth.userId)}/Items?${query}`;
  const result = await jellyfinFetchJson(auth, apiPath);
  return {
    ...result,
    apiPath,
    items: result.body?.Items ?? [],
    totalRecordCount: result.body?.TotalRecordCount ?? null,
  };
}

async function getLibrariesAndItems(auth) {
  const views = await jellyfinFetchJson(auth, `/Users/${encodeURIComponent(auth.userId)}/Views`);
  if (!views.ok) throw new Error(`Jellyfin library view request failed with ${views.status}.`);
  const libraries = (views.body?.Items ?? []).filter(isMediaLibrary);
  const animeLibrary = libraries.find((library) => String(library.Name ?? "").toLowerCase() === "anime") ?? null;
  const normalLibrary =
    libraries.find((library) => String(library.Name ?? "").toLowerCase() === "other") ??
    libraries.find((library) => String(library.Name ?? "").toLowerCase() !== "anime") ??
    null;

  if (!animeLibrary) throw new Error("No Anime Jellyfin library was found.");
  if (!normalLibrary) throw new Error("No non-anime Jellyfin media library was found.");

  const animePlayable = await getLibraryItemsPage(auth, animeLibrary.Id, { limit: 80, playableOnly: true });
  const normalPlayable = await getLibraryItemsPage(auth, normalLibrary.Id, { limit: 80, playableOnly: true });
  const animeItem = animePlayable.items.find(isPlayable) ?? null;
  const normalItem = normalPlayable.items.find(isPlayable) ?? null;

  return {
    libraries,
    animeLibrary,
    normalLibrary,
    animeItem,
    normalItem,
    animePlayableTotal: animePlayable.totalRecordCount,
    normalPlayableTotal: normalPlayable.totalRecordCount,
  };
}

function summarize(values) {
  const clean = values.filter((value) => Number.isFinite(value)).sort((left, right) => left - right);
  const pct = (p) => {
    if (!clean.length) return null;
    const index = Math.min(clean.length - 1, Math.max(0, Math.ceil((p / 100) * clean.length) - 1));
    return clean[index];
  };
  return {
    count: clean.length,
    p50: pct(50),
    p75: pct(75),
    p95: pct(95),
    min: clean.length ? clean[0] : null,
    max: clean.length ? clean.at(-1) : null,
    samples: clean,
  };
}

function formatMs(value) {
  return Number.isFinite(value) ? `${value.toFixed(1)} ms` : "n/a";
}

function attachNetworkMetrics(page) {
  const requests = new Map();
  const records = [];
  const failedRequests = [];

  page.on("request", (request) => {
    const startedAt = performance.now();
    requests.set(request, {
      url: request.url(),
      method: request.method(),
      resourceType: request.resourceType(),
      startedAt,
      range: request.headers().range ?? null,
    });
  });

  page.on("response", (response) => {
    const request = response.request();
    const record = requests.get(request);
    if (!record) return;
    const endedAt = performance.now();
    const length = Number(response.headers()["content-length"] ?? 0);
    records.push({
      ...record,
      url: redactUrl(record.url),
      status: response.status(),
      endedAt,
      durationMs: endedAt - record.startedAt,
      bytes: Number.isFinite(length) && length > 0 ? length : 0,
    });
  });

  page.on("requestfailed", (request) => {
    failedRequests.push({
      url: redactUrl(request.url()),
      method: request.method(),
      resourceType: request.resourceType(),
      failure: request.failure()?.errorText ?? "unknown",
    });
  });

  return {
    records,
    failedRequests,
    summarize({ since = 0, until = Number.POSITIVE_INFINITY } = {}) {
      const scoped = records.filter((record) => record.startedAt >= since && record.startedAt <= until);
      const beforeUntil = records.filter((record) => record.endedAt <= until);
      const apiRecords = scoped.filter((record) => record.url.includes("/api/"));
      const thumbnailRecords = scoped.filter((record) =>
        record.resourceType === "image" ||
        record.url.includes("/Images/") ||
        record.url.includes("/jellyfin-image")
      );
      const videoRecords = scoped.filter((record) =>
        record.resourceType === "media" ||
        record.url.includes("/api/spiritflix/stream") ||
        record.url.includes("/api/spiritflix/mobile-optimized?stream=1") ||
        record.url.includes("/master.m3u8") ||
        record.url.includes("/Videos/")
      );
      const rangeRecords = videoRecords.filter((record) => Boolean(record.range));
      return {
        requestCount: scoped.length,
        apiRequestCount: apiRecords.length,
        apiDurations: apiRecords.map((record) => record.durationMs),
        thumbnailRequests: thumbnailRecords.length,
        videoRequests: videoRecords.length,
        rangeRequests: rangeRecords.length,
        bytes: scoped.reduce((total, record) => total + record.bytes, 0),
        bytesBeforeUntil: beforeUntil.reduce((total, record) => total + record.bytes, 0),
        failedRequests: failedRequests.slice(),
        sampleRequests: scoped.slice(0, 80),
      };
    },
  };
}

async function addSessionInit(context, auth, selectedLibraryId = null) {
  await context.addInitScript(
    ({ authPayload, selectedLibraryId: initialLibraryId }) => {
      const session = {
        serverUrl: authPayload.serverUrl,
        accessToken: authPayload.accessToken,
        userId: authPayload.userId,
        username: authPayload.username,
      };
      window.localStorage.setItem("spiritflix_private_gooner_session", JSON.stringify(session));
      window.localStorage.setItem("spiritflix_player_muted", "true");
      window.localStorage.setItem("spiritflix_player_volume", "0");
      window.localStorage.setItem("spiritflix_caption_preference", "off");
      window.sessionStorage.removeItem("spiritflix_home_cache_v1");
      if (initialLibraryId) {
        window.localStorage.setItem(
          "spiritflix_library_ui_state",
          JSON.stringify({
            selectedLibraryId: initialLibraryId,
            viewMode: "grid",
            sortMode: "title",
            sortDirection: "asc",
            orientationFilter: "all",
            filtersOpen: false,
            pageIndex: 0,
          }),
        );
      } else {
        window.localStorage.removeItem("spiritflix_library_ui_state");
      }
    },
    {
      authPayload: {
        serverUrl: auth.serverUrl,
        accessToken: auth.accessToken,
        userId: auth.userId,
        username: auth.username,
      },
      selectedLibraryId,
    },
  );
}

async function waitForUsefulContent(page, routeName) {
  await page.waitForFunction(
    (name) => {
      const ready = document.querySelector('[data-spiritflix-useful-content="ready"]');
      if (!ready) return false;
      if (name === "anime") {
        return Boolean(document.querySelector(".spiritflix-anime-view")) &&
          document.querySelectorAll(".spiritflix-anime-episode, .spiritflix-anime-series-picker button").length > 0;
      }
      if (name === "library") {
        return Boolean(document.querySelector(".spiritflix-library-v2")) &&
          document.querySelectorAll(".spiritflix-feed-card, .spiritflix-library-row, .spiritflix-model-card").length > 0;
      }
      return document.querySelectorAll(".spiritflix-card, .spiritflix-feed-card, .spiritflix-rail-card, .spiritflix-library-row").length > 0 ||
        Boolean(document.querySelector(".spiritflix-hero"));
    },
    routeName,
    { timeout: 30_000 },
  );
}

async function waitForFirstThumbnail(page) {
  try {
    await page.waitForFunction(
      () => document.querySelectorAll('[data-spiritflix-image-state="loaded"] img, .spiritflix-gallery-card img').length > 0,
      { timeout: 8_000 },
    );
    return true;
  } catch {
    return false;
  }
}

async function collectDomSnapshot(page) {
  return page.evaluate(() => ({
    title: document.title,
    usefulState: document.querySelector("[data-spiritflix-useful-content]")?.getAttribute("data-spiritflix-useful-content") ?? null,
    animeEpisodeCount: document.querySelectorAll(".spiritflix-anime-episode").length,
    animeSeriesButtonCount: document.querySelectorAll(".spiritflix-anime-series-picker button").length,
    feedCardCount: document.querySelectorAll(".spiritflix-feed-card").length,
    libraryRowCount: document.querySelectorAll(".spiritflix-library-row").length,
    railCardCount: document.querySelectorAll(".spiritflix-card").length,
    loadedImageCount: document.querySelectorAll('[data-spiritflix-image-state="loaded"]').length,
    pendingImageCount: document.querySelectorAll('[data-spiritflix-image-state="pending"]').length,
    fallbackImageCount: document.querySelectorAll('[data-spiritflix-image-state="fallback"]').length,
    loginVisible: Boolean(document.querySelector("input[type='password'], form")),
    textSample: document.body.innerText.slice(0, 500),
  }));
}

async function newMeasuredPage(browser, viewportConfig, auth, selectedLibraryId) {
  const context = await browser.newContext({
    viewport: viewportConfig.viewport,
    deviceScaleFactor: viewportConfig.deviceScaleFactor,
    isMobile: viewportConfig.isMobile,
    hasTouch: viewportConfig.hasTouch,
    ignoreHTTPSErrors: true,
    serviceWorkers: "allow",
  });
  await addSessionInit(context, auth, selectedLibraryId);
  const page = await context.newPage();
  return { context, page };
}

async function measureRoute(browser, config, auth, viewportConfig, route) {
  const { context, page } = await newMeasuredPage(browser, viewportConfig, auth, route.libraryId ?? null);
  const network = attachNetworkMetrics(page);
  const cpuBefore = collectCpuSnapshot(`${route.name}-${viewportConfig.name}-route-before`);
  const started = performance.now();
  let usefulAt = null;
  let thumbnailAt = null;
  let error = null;
  let dom = null;
  let screenshotPath = null;

  try {
    await page.goto(`${config.baseUrl}${route.path}`, { waitUntil: "commit", timeout: 30_000 });
    await waitForUsefulContent(page, route.name);
    usefulAt = performance.now();
    const thumbnailLoaded = await waitForFirstThumbnail(page);
    thumbnailAt = thumbnailLoaded ? performance.now() : null;
    dom = await collectDomSnapshot(page);
    if (route.runIndex === 0) {
      screenshotPath = path.join(config.evidenceDir, "screenshots", `${config.label}-${viewportConfig.name}-${route.name}.png`);
      await fs.mkdir(path.dirname(screenshotPath), { recursive: true });
      await page.screenshot({ path: screenshotPath, fullPage: false });
    }
  } catch (caught) {
    error = caught instanceof Error ? caught.message : String(caught);
    dom = await collectDomSnapshot(page).catch(() => null);
  }

  const endedAt = performance.now();
  const cpuAfter = collectCpuSnapshot(`${route.name}-${viewportConfig.name}-route-after`);
  const usefulContentMs = usefulAt ? usefulAt - started : null;
  const thumbnailVisibleMs = thumbnailAt && usefulAt ? thumbnailAt - started : null;
  const networkSummary = network.summarize({ until: usefulAt ?? endedAt });
  await context.close();

  return {
    route: route.name,
    path: route.path,
    viewport: viewportConfig.name,
    usefulContentMs,
    thumbnailVisibleMs,
    elapsedMs: endedAt - started,
    network: networkSummary,
    dom,
    cpuBefore,
    cpuAfter,
    ffmpegBefore: classifyFfmpegProcesses(cpuBefore),
    ffmpegAfter: classifyFfmpegProcesses(cpuAfter),
    screenshotPath,
    error,
  };
}

function getMark(marks, name) {
  return marks.find((mark) => mark.name === name) ?? null;
}

function classifyPlaybackSource({ playbackSource, videoSrc, marks }) {
  const sourceMark = marks.find((mark) => mark.name === "source-chosen")?.detail?.source;
  const src = String(videoSrc ?? "").toLowerCase();
  const attr = String(playbackSource ?? "").toLowerCase();
  if (sourceMark === "mobileOptimized" || attr.includes("optimized") || src.includes("/mobile-optimized")) return "mobileOptimized";
  if (sourceMark === "hlsSelectedAudio" || attr.includes("hls") || src.includes("m3u8")) return "HLS";
  if (attr.includes("transcode")) return "Jellyfin transcode";
  if (attr.includes("canonical") || attr.includes("proxied") || src.includes("/api/spiritflix/stream") || src.includes("/videos/")) return "directMp4";
  return sourceMark ?? playbackSource ?? "unknown";
}

async function collectPlaybackState(page) {
  return page.evaluate(() => {
    const video = document.querySelector("video");
    const marks = window.__spiritflixPerf?.marks ?? [];
    const clickStartedAt = window.__spiritflixClickStartedAt ?? null;
    return {
      marks,
      clickStartedAt,
      videoSrc: video?.currentSrc || video?.getAttribute("src") || null,
      videoReadyState: video?.readyState ?? null,
      videoPaused: video?.paused ?? null,
      videoCurrentTime: video?.currentTime ?? null,
      playbackSource: video?.getAttribute("data-spiritflix-playback-source") ?? null,
    };
  });
}

async function measurePlayback(browser, config, auth, viewportConfig, playback) {
  const { context, page } = await newMeasuredPage(browser, viewportConfig, auth, playback.libraryId);
  let routeError = null;

  try {
    await page.goto(`${config.baseUrl}${playback.path}`, { waitUntil: "commit", timeout: 30_000 });
    await waitForUsefulContent(page, playback.routeName);
  } catch (caught) {
    routeError = caught instanceof Error ? caught.message : String(caught);
  }

  if (routeError) {
    await context.close();
    return { ...playback, viewport: viewportConfig.name, error: `Route setup failed: ${routeError}` };
  }

  await page.evaluate(() => {
    window.__spiritflixPerf = { marks: [] };
    window.__spiritflixClickStartedAt = performance.now();
  });

  const network = attachNetworkMetrics(page);
  const cpuBefore = collectCpuSnapshot(`${playback.name}-${viewportConfig.name}-playback-before`);
  const clickStarted = performance.now();
  let playerVisibleMs = null;
  let loadedMetadataMs = null;
  let canplayMs = null;
  let playingMs = null;
  let state = null;
  let cpuAtPlaying = null;
  let cpuAfterWindow = null;
  let systemDiagnostics = null;
  let error = null;

  try {
    const target = page.locator(playback.clickSelector).first();
    await target.waitFor({ state: "visible", timeout: 10_000 });
    if (viewportConfig.hasTouch) {
      await target.tap({ timeout: 10_000 });
    } else {
      await target.click({ timeout: 10_000 });
    }
    await page.locator(".spiritflix-player video").first().waitFor({ state: "attached", timeout: 15_000 });
    playerVisibleMs = performance.now() - clickStarted;

    await page.waitForFunction(() => window.__spiritflixPerf?.marks?.some((mark) => mark.name === "loadedmetadata"), { timeout: 25_000 });
    state = await collectPlaybackState(page);
    loadedMetadataMs = getMark(state.marks, "loadedmetadata")?.at - state.clickStartedAt;

    await page.waitForFunction(() => window.__spiritflixPerf?.marks?.some((mark) => mark.name === "canplay"), { timeout: 25_000 });
    state = await collectPlaybackState(page);
    canplayMs = getMark(state.marks, "canplay")?.at - state.clickStartedAt;

    await page.waitForFunction(
      () => {
        const video = document.querySelector("video");
        return window.__spiritflixPerf?.marks?.some((mark) => mark.name === "playing") ||
          Boolean(video && !video.paused && video.readyState >= 2);
      },
      { timeout: 25_000 },
    );
    state = await collectPlaybackState(page);
    const playingMark = getMark(state.marks, "playing");
    playingMs = playingMark ? playingMark.at - state.clickStartedAt : performance.now() - clickStarted;
    cpuAtPlaying = collectCpuSnapshot(`${playback.name}-${viewportConfig.name}-playback-playing`);

    try {
      const diagnosticsResponse = await fetch(`${config.baseUrl}/api/spiritflix/system-diagnostics`, { headers: { Accept: "application/json" } });
      systemDiagnostics = diagnosticsResponse.ok ? await diagnosticsResponse.json() : { status: diagnosticsResponse.status };
    } catch (caught) {
      systemDiagnostics = { error: caught instanceof Error ? caught.message : String(caught) };
    }

    await page.waitForTimeout(config.stallWindowMs);
    state = await collectPlaybackState(page);
    cpuAfterWindow = collectCpuSnapshot(`${playback.name}-${viewportConfig.name}-playback-after-window`);
  } catch (caught) {
    error = caught instanceof Error ? caught.message : String(caught);
    state = await collectPlaybackState(page).catch(() => null);
  }

  const endedAt = performance.now();
  const mediaMarks = state?.marks ?? [];
  const sourceClass = classifyPlaybackSource({
    playbackSource: state?.playbackSource,
    videoSrc: state?.videoSrc,
    marks: mediaMarks,
  });
  const playbackWindowNetwork = network.summarize({ since: clickStarted, until: endedAt });
  await context.close();

  return {
    ...playback,
    viewport: viewportConfig.name,
    playerVisibleMs,
    loadedMetadataMs: Number.isFinite(loadedMetadataMs) ? loadedMetadataMs : null,
    canplayMs: Number.isFinite(canplayMs) ? canplayMs : null,
    playingMs: Number.isFinite(playingMs) ? playingMs : null,
    elapsedMs: endedAt - clickStarted,
    playbackSource: state?.playbackSource ?? null,
    selectedSourceType: sourceClass,
    videoSrc: state?.videoSrc ? redactUrl(state.videoSrc) : null,
    videoReadyState: state?.videoReadyState ?? null,
    videoCurrentTime: state?.videoCurrentTime ?? null,
    marks: mediaMarks.map((mark) => ({ ...mark, detail: mark.detail ? JSON.parse(JSON.stringify(mark.detail, (_, value) => typeof value === "string" ? redactUrl(value) : value)) : undefined })),
    waitingCount: mediaMarks.filter((mark) => mark.name === "waiting").length,
    stalledCount: mediaMarks.filter((mark) => mark.name === "stalled").length,
    network: playbackWindowNetwork,
    rangeSupported: playbackWindowNetwork.rangeRequests > 0,
    cpuBefore,
    cpuAtPlaying,
    cpuAfterWindow,
    ffmpegBefore: classifyFfmpegProcesses(cpuBefore),
    ffmpegAtPlaying: cpuAtPlaying ? classifyFfmpegProcesses(cpuAtPlaying) : [],
    ffmpegAfterWindow: cpuAfterWindow ? classifyFfmpegProcesses(cpuAfterWindow) : [],
    systemDiagnostics,
    error,
  };
}

async function measureApiRuns(auth, viewportConfig, libraries, runs) {
  const records = {
    animeFirstScreen: [],
    normalFirstScreen: [],
    animeFullProbe: [],
  };
  for (let index = 0; index < runs; index += 1) {
    records.animeFirstScreen.push(await getLibraryItemsPage(auth, libraries.animeLibrary.Id, { limit: viewportConfig.firstScreenLimit }));
    records.normalFirstScreen.push(await getLibraryItemsPage(auth, libraries.normalLibrary.Id, { limit: viewportConfig.firstScreenLimit }));
    records.animeFullProbe.push(await getLibraryItemsPage(auth, libraries.animeLibrary.Id, { limit: ANIME_FULL_PROBE_LIMIT }));
  }
  return {
    viewport: viewportConfig.name,
    firstScreenLimit: viewportConfig.firstScreenLimit,
    animeFirstScreen: records.animeFirstScreen.map((entry) => ({
      elapsedMs: entry.elapsedMs,
      status: entry.status,
      itemCount: entry.items.length,
      totalRecordCount: entry.totalRecordCount,
      bytes: entry.bytes,
    })),
    normalFirstScreen: records.normalFirstScreen.map((entry) => ({
      elapsedMs: entry.elapsedMs,
      status: entry.status,
      itemCount: entry.items.length,
      totalRecordCount: entry.totalRecordCount,
      bytes: entry.bytes,
    })),
    animeFullProbe: records.animeFullProbe.map((entry) => ({
      elapsedMs: entry.elapsedMs,
      status: entry.status,
      itemCount: entry.items.length,
      totalRecordCount: entry.totalRecordCount,
      bytes: entry.bytes,
      limit: ANIME_FULL_PROBE_LIMIT,
    })),
  };
}

function routePath(libraryId) {
  return libraryId ? `/spiritflix?library=${encodeURIComponent(libraryId)}` : "/spiritflix";
}

function aggregate(payload) {
  const byViewport = {};
  for (const viewport of payload.config.viewports) {
    const routeFor = (name) => payload.routeRuns.filter((run) => run.viewport === viewport.name && run.route === name && !run.error);
    const playbackFor = (name) => payload.playbackRuns.filter((run) => run.viewport === viewport.name && run.name === name && !run.error);
    const apiFor = payload.apiRuns.find((entry) => entry.viewport === viewport.name);
    byViewport[viewport.name] = {
      label: viewport.label,
      routes: {
        home: {
          usefulContent: summarize(routeFor("home").map((run) => run.usefulContentMs)),
          thumbnailVisible: summarize(routeFor("home").map((run) => run.thumbnailVisibleMs)),
          apiLatency: summarize(routeFor("home").flatMap((run) => run.network.apiDurations)),
          requestCount: summarize(routeFor("home").map((run) => run.network.requestCount)),
          thumbnailRequests: summarize(routeFor("home").map((run) => run.network.thumbnailRequests)),
          bytesBeforeUseful: summarize(routeFor("home").map((run) => run.network.bytesBeforeUntil)),
        },
        library: {
          usefulContent: summarize(routeFor("library").map((run) => run.usefulContentMs)),
          thumbnailVisible: summarize(routeFor("library").map((run) => run.thumbnailVisibleMs)),
          apiLatency: summarize(routeFor("library").flatMap((run) => run.network.apiDurations)),
          requestCount: summarize(routeFor("library").map((run) => run.network.requestCount)),
          thumbnailRequests: summarize(routeFor("library").map((run) => run.network.thumbnailRequests)),
          bytesBeforeUseful: summarize(routeFor("library").map((run) => run.network.bytesBeforeUntil)),
        },
        anime: {
          usefulContent: summarize(routeFor("anime").map((run) => run.usefulContentMs)),
          thumbnailVisible: summarize(routeFor("anime").map((run) => run.thumbnailVisibleMs)),
          apiLatency: summarize(routeFor("anime").flatMap((run) => run.network.apiDurations)),
          requestCount: summarize(routeFor("anime").map((run) => run.network.requestCount)),
          thumbnailRequests: summarize(routeFor("anime").map((run) => run.network.thumbnailRequests)),
          bytesBeforeUseful: summarize(routeFor("anime").map((run) => run.network.bytesBeforeUntil)),
        },
      },
      api: apiFor
        ? {
            animeFirstScreen: summarize(apiFor.animeFirstScreen.map((entry) => entry.elapsedMs)),
            normalFirstScreen: summarize(apiFor.normalFirstScreen.map((entry) => entry.elapsedMs)),
            animeFullProbe: summarize(apiFor.animeFullProbe.map((entry) => entry.elapsedMs)),
          }
        : null,
      playback: {
        anime: {
          playerVisible: summarize(playbackFor("anime-playback").map((run) => run.playerVisibleMs)),
          loadedMetadata: summarize(playbackFor("anime-playback").map((run) => run.loadedMetadataMs)),
          canplay: summarize(playbackFor("anime-playback").map((run) => run.canplayMs)),
          playing: summarize(playbackFor("anime-playback").map((run) => run.playingMs)),
          selectedSources: playbackFor("anime-playback").map((run) => run.selectedSourceType),
          rangeSupported: playbackFor("anime-playback").some((run) => run.rangeSupported),
          waitingCount: playbackFor("anime-playback").reduce((total, run) => total + (run.waitingCount ?? 0), 0),
          stalledCount: playbackFor("anime-playback").reduce((total, run) => total + (run.stalledCount ?? 0), 0),
        },
        normal: {
          playerVisible: summarize(playbackFor("normal-playback").map((run) => run.playerVisibleMs)),
          loadedMetadata: summarize(playbackFor("normal-playback").map((run) => run.loadedMetadataMs)),
          canplay: summarize(playbackFor("normal-playback").map((run) => run.canplayMs)),
          playing: summarize(playbackFor("normal-playback").map((run) => run.playingMs)),
          selectedSources: playbackFor("normal-playback").map((run) => run.selectedSourceType),
          rangeSupported: playbackFor("normal-playback").some((run) => run.rangeSupported),
          waitingCount: playbackFor("normal-playback").reduce((total, run) => total + (run.waitingCount ?? 0), 0),
          stalledCount: playbackFor("normal-playback").reduce((total, run) => total + (run.stalledCount ?? 0), 0),
        },
      },
    };
  }
  return byViewport;
}

function buildMarkdown(payload) {
  const lines = [];
  lines.push(`# SpiritFlix Anime Performance ${payload.config.label}`);
  lines.push("");
  lines.push(`Generated: ${payload.generatedAt}`);
  lines.push(`Base URL: ${payload.config.baseUrl}`);
  lines.push(`Jellyfin URL: ${payload.config.jellyfinUrl}`);
  lines.push(`Runs: ${payload.config.runs}`);
  lines.push(`Auth source: Jellyfin local DB device token for ${payload.auth.username} (${payload.auth.deviceName ?? "unknown device"}), token redacted.`);
  lines.push("");
  lines.push("## Libraries");
  lines.push("");
  lines.push(`- Anime: ${payload.libraries.animeLibrary.Name} (${payload.libraries.animePlayableTotal ?? "unknown"} playable items)`);
  lines.push(`- Normal: ${payload.libraries.normalLibrary.Name} (${payload.libraries.normalPlayableTotal ?? "unknown"} playable items)`);
  lines.push(`- Anime playback item: ${payload.libraries.animeItem?.Name ?? "none"}`);
  lines.push(`- Normal playback item: ${payload.libraries.normalItem?.Name ?? "none"}`);
  lines.push("");
  lines.push("## Metrics");
  lines.push("");
  lines.push("| Viewport | Anime route P50/P95 | Normal route P50/P95 | Anime API P50/P95 | Normal API P50/P95 | Anime play to playing P50/P95 | Normal play to playing P50/P95 | Anime thumbnails P50 | Anime source | Normal source |");
  lines.push("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |");
  for (const viewport of payload.config.viewports) {
    const item = payload.summary[viewport.name];
    const animeRoute = item.routes.anime.usefulContent;
    const normalRoute = item.routes.library.usefulContent;
    const animeApi = item.api?.animeFirstScreen ?? { p50: null, p95: null };
    const normalApi = item.api?.normalFirstScreen ?? { p50: null, p95: null };
    const animePlayback = item.playback.anime.playing;
    const normalPlayback = item.playback.normal.playing;
    const animeThumb = item.routes.anime.thumbnailVisible;
    lines.push(
      `| ${item.label} | ${formatMs(animeRoute.p50)} / ${formatMs(animeRoute.p95)} | ${formatMs(normalRoute.p50)} / ${formatMs(normalRoute.p95)} | ${formatMs(animeApi.p50)} / ${formatMs(animeApi.p95)} | ${formatMs(normalApi.p50)} / ${formatMs(normalApi.p95)} | ${formatMs(animePlayback.p50)} / ${formatMs(animePlayback.p95)} | ${formatMs(normalPlayback.p50)} / ${formatMs(normalPlayback.p95)} | ${formatMs(animeThumb.p50)} | ${[...new Set(item.playback.anime.selectedSources)].join(", ") || "n/a"} | ${[...new Set(item.playback.normal.selectedSources)].join(", ") || "n/a"} |`,
    );
  }
  lines.push("");
  lines.push("## Route Detail");
  lines.push("");
  for (const viewport of payload.config.viewports) {
    const item = payload.summary[viewport.name];
    lines.push(`### ${item.label}`);
    for (const routeName of ["home", "library", "anime"]) {
      const route = item.routes[routeName];
      lines.push(
        `- ${routeName}: useful ${formatMs(route.usefulContent.p50)} P50 / ${formatMs(route.usefulContent.p95)} P95; API ${formatMs(route.apiLatency.p50)} P50 / ${formatMs(route.apiLatency.p95)} P95; requests ${route.requestCount.p50 ?? "n/a"} P50; thumbnails ${route.thumbnailRequests.p50 ?? "n/a"} P50; bytes-before-useful ${route.bytesBeforeUseful.p50 ?? "n/a"} P50.`,
      );
    }
  }
  lines.push("");
  lines.push("## Playback Detail");
  lines.push("");
  for (const viewport of payload.config.viewports) {
    const item = payload.summary[viewport.name];
    lines.push(`### ${item.label}`);
    for (const [name, playback] of Object.entries(item.playback)) {
      lines.push(
        `- ${name}: visible ${formatMs(playback.playerVisible.p50)} P50; metadata ${formatMs(playback.loadedMetadata.p50)} P50; canplay ${formatMs(playback.canplay.p50)} P50; playing ${formatMs(playback.playing.p50)} P50; range ${playback.rangeSupported ? "yes" : "no"}; waiting ${playback.waitingCount}; stalled ${playback.stalledCount}; source ${[...new Set(playback.selectedSources)].join(", ") || "n/a"}.`,
      );
    }
  }
  lines.push("");
  lines.push("## Commands");
  lines.push("");
  payload.commands.forEach((command) => lines.push(`- \`${command}\``));
  lines.push("");
  lines.push("## Errors");
  lines.push("");
  const errors = [
    ...payload.routeRuns.filter((run) => run.error).map((run) => `${run.viewport}/${run.route}: ${run.error}`),
    ...payload.playbackRuns.filter((run) => run.error).map((run) => `${run.viewport}/${run.name}: ${run.error}`),
  ];
  if (errors.length) errors.forEach((error) => lines.push(`- ${error}`));
  else lines.push("- None");
  lines.push("");
  lines.push("## Evidence");
  lines.push("");
  lines.push(`- JSON: ${payload.paths.json}`);
  lines.push(`- Screenshots: ${path.join(payload.config.evidenceDir, "screenshots")}`);
  return `${lines.join("\n")}\n`;
}

async function main() {
  const config = parseArgs();
  if (!Number.isFinite(config.runs) || config.runs < 1) throw new Error("--runs must be a positive number.");
  await fs.mkdir(config.evidenceDir, { recursive: true });

  const auth = await resolveAuth(config);
  const libraries = await getLibrariesAndItems(auth);
  const commands = [
    `node scripts/spiritflix-anime-performance-harness.mjs --label=${config.label} --runs=${config.runs} --evidence-dir=${config.evidenceDir}`,
  ];

  const payload = {
    generatedAt: new Date().toISOString(),
    config: {
      ...config,
      viewports: config.viewports.map((viewport) => ({
        name: viewport.name,
        label: viewport.label,
        viewport: viewport.viewport,
        deviceScaleFactor: viewport.deviceScaleFactor,
        isMobile: viewport.isMobile,
        hasTouch: viewport.hasTouch,
        firstScreenLimit: viewport.firstScreenLimit,
      })),
    },
    commands,
    auth: redactedAuth(auth),
    libraries: {
      animeLibrary: libraries.animeLibrary,
      normalLibrary: libraries.normalLibrary,
      animeItem: libraries.animeItem ? {
        Id: libraries.animeItem.Id,
        Name: libraries.animeItem.Name,
        Type: libraries.animeItem.Type,
        Path: libraries.animeItem.Path,
        MediaSources: libraries.animeItem.MediaSources?.map((source) => ({ Path: source.Path, Container: source.Container })),
        MediaStreams: libraries.animeItem.MediaStreams?.map((stream) => ({
          Type: stream.Type,
          Codec: stream.Codec,
          Width: stream.Width,
          Height: stream.Height,
          Language: stream.Language,
          DisplayTitle: stream.DisplayTitle,
        })),
      } : null,
      normalItem: libraries.normalItem ? {
        Id: libraries.normalItem.Id,
        Name: libraries.normalItem.Name,
        Type: libraries.normalItem.Type,
        Path: libraries.normalItem.Path,
        MediaSources: libraries.normalItem.MediaSources?.map((source) => ({ Path: source.Path, Container: source.Container })),
        MediaStreams: libraries.normalItem.MediaStreams?.map((stream) => ({
          Type: stream.Type,
          Codec: stream.Codec,
          Width: stream.Width,
          Height: stream.Height,
          Language: stream.Language,
          DisplayTitle: stream.DisplayTitle,
        })),
      } : null,
      animePlayableTotal: libraries.animePlayableTotal,
      normalPlayableTotal: libraries.normalPlayableTotal,
    },
    apiRuns: [],
    routeRuns: [],
    playbackRuns: [],
    summary: {},
    paths: {},
  };

  const browser = await chromium.launch({ headless: true });
  try {
    for (const viewport of config.viewports) {
      payload.apiRuns.push(await measureApiRuns(auth, viewport, libraries, config.runs));

      for (let runIndex = 0; runIndex < config.runs; runIndex += 1) {
        const routes = [
          { name: "home", path: "/spiritflix", runIndex },
          { name: "library", path: routePath(libraries.normalLibrary.Id), libraryId: libraries.normalLibrary.Id, runIndex },
          { name: "anime", path: routePath(libraries.animeLibrary.Id), libraryId: libraries.animeLibrary.Id, runIndex },
        ];
        for (const route of routes) {
          payload.routeRuns.push(await measureRoute(browser, config, auth, viewport, route));
        }
      }

      if (!config.skipPlayback) {
        for (let runIndex = 0; runIndex < config.runs; runIndex += 1) {
          const playbacks = [
            {
              name: "anime-playback",
              routeName: "anime",
              path: routePath(libraries.animeLibrary.Id),
              libraryId: libraries.animeLibrary.Id,
              itemId: libraries.animeItem?.Id ?? null,
              clickSelector: ".spiritflix-anime-now__play, .spiritflix-anime-episode",
              runIndex,
            },
            {
              name: "normal-playback",
              routeName: "library",
              path: routePath(libraries.normalLibrary.Id),
              libraryId: libraries.normalLibrary.Id,
              itemId: libraries.normalItem?.Id ?? null,
              clickSelector: ".spiritflix-feed-card__play, .spiritflix-library-row__play, .spiritflix-card__actions button[aria-label^='Play']",
              runIndex,
            },
          ];
          for (const playback of playbacks) {
            payload.playbackRuns.push(await measurePlayback(browser, config, auth, viewport, playback));
          }
        }
      }
    }
  } finally {
    await browser.close();
  }

  payload.summary = aggregate(payload);
  const jsonPath = path.join(config.evidenceDir, `${config.label}.json`);
  const mdPath = path.join(config.evidenceDir, `${config.label}-summary.md`);
  payload.paths = { json: jsonPath, markdown: mdPath };
  await fs.writeFile(jsonPath, `${JSON.stringify(payload, null, 2)}\n`);
  await fs.writeFile(mdPath, buildMarkdown(payload));

  console.log(JSON.stringify({
    evidenceDir: config.evidenceDir,
    label: config.label,
    json: jsonPath,
    markdown: mdPath,
    summary: payload.summary,
  }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exitCode = 1;
});
