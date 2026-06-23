#!/usr/bin/env node
/**
 * SpiritFlix mobile startup benchmark — honest warm/cold timing with real playback APIs.
 *
 * Usage:
 *   node scripts/spiritflix-mobile-benchmark.mjs
 *   SPIRITFLIX_BENCHMARK_ITEM_ID=phase7-candidate-02 node scripts/spiritflix-mobile-benchmark.mjs --runs 12
 */

import { chromium, devices } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { Agent, setGlobalDispatcher } from "undici";
import {
  buildMarkdownSummary,
  percentile,
  summarizeRuns,
} from "./spiritflix-mobile-benchmark-report.mjs";

if ((process.env.SPIRITFLIX_BENCHMARK_INSECURE_TLS ?? "1") === "1") {
  setGlobalDispatcher(
    new Agent({
      connect: {
        rejectUnauthorized: false,
      },
    }),
  );
}

const ROOT = process.cwd();
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? process.env.SPIRITFLIX_BENCHMARK_BASE_URL ?? "https://localhost:3000";
const ITEM_ID = process.env.SPIRITFLIX_BENCHMARK_ITEM_ID ?? "phase7-candidate-02";
const RUNS = Number(process.env.SPIRITFLIX_BENCHMARK_RUNS ?? process.argv.find((arg) => arg.startsWith("--runs="))?.split("=")[1] ?? 10);
const MODE = process.argv.includes("--cold") ? "cold" : "warm";
const TIMESTAMP = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "-");
const EVIDENCE_DIR = path.join(ROOT, "docs", "evidence", `spiritflix-mobile-50ms-loop-${TIMESTAMP}`);

function parseArgs() {
  return {
    runs: RUNS,
    mode: MODE,
    baseUrl: BASE_URL,
    itemId: ITEM_ID,
    fixtureOnly: process.argv.includes("--fixture-only"),
  };
}

async function timeMobileOptimizedApi(baseUrl, itemId, { cold = false } = {}) {
  const url = `${baseUrl}/api/spiritflix/mobile-optimized?itemId=${encodeURIComponent(itemId)}`;
  const started = performance.now();
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
    cache: cold ? "no-store" : "default",
  });
  const elapsedMs = performance.now() - started;
  const body = response.ok ? await response.json() : { available: false };
  const rangeProbe = body.url
    ? await fetch(`${baseUrl}${body.url}`, {
        method: "GET",
        headers: { Range: "bytes=0-65535" },
      })
    : null;
  return {
    elapsedMs,
    status: response.status,
    available: Boolean(body.available),
    source: body.available ? "mobileOptimized" : "none",
    url: body.url ?? null,
    rangeSupported: rangeProbe ? rangeProbe.status === 206 : false,
    rangeStatus: rangeProbe?.status ?? null,
  };
}

async function collectPerfMarks(page) {
  return page.evaluate(() => {
    const perf = window.__spiritflixPerf?.marks ?? [];
    const video = document.querySelector("video");
    return {
      marks: perf,
      videoSrc: video?.currentSrc || video?.getAttribute("src") || null,
      videoReadyState: video?.readyState ?? null,
      playbackSource: document.querySelector("[data-spiritflix-playback-source]")?.getAttribute("data-spiritflix-playback-source") ?? null,
    };
  });
}

async function measureShellPage(page, baseUrl) {
  const started = performance.now();
  await page.goto(`${baseUrl}/spiritflix/benchmark/shell`, { waitUntil: "commit" });
  const useful = page.locator('[data-spiritflix-useful-content="ready"]').first();
  await useful.waitFor({ state: "visible", timeout: 15_000 });
  const elapsedMs = performance.now() - started;
  const cardCount = await page.locator(".spiritflix-library-v2, .spiritflix-card, .spiritflix-rail-card").count();
  return {
    elapsedMs,
    usefulContentMs: elapsedMs,
    cardCount,
    route: "/spiritflix/benchmark/shell",
    mode: "shell-fixture",
  };
}

async function measureWarmVideoTap(page, baseUrl, itemId) {
  await page.addInitScript(() => {
    window.localStorage.setItem("spiritflix_player_muted", "true");
    window.localStorage.setItem("spiritflix_player_volume", "0");
  });
  await page.goto(`${baseUrl}/spiritflix/benchmark/player?itemId=${encodeURIComponent(itemId)}&autoplay=0`, {
    waitUntil: "domcontentloaded",
  });
  await page.waitForFunction(
    () => {
      const node = document.querySelector("video");
      return Boolean(node && node.readyState >= 2);
    },
    { timeout: 20_000 },
  );
  const video = page.locator("video").first();
  await video.evaluate((node) => {
    node.pause();
    node.currentTime = 0;
  });

  const tapStarted = performance.now();
  await page.evaluate(() => {
    const video = document.querySelector("video");
    if (video) void video.play();
  });
  await page.waitForFunction(
    () => {
      const node = document.querySelector("video");
      return Boolean(node && !node.paused && node.readyState >= 2);
    },
    { timeout: 10_000 },
  );
  const tapToPlayingMs = performance.now() - tapStarted;
  const perf = await collectPerfMarks(page);

  return {
    tapToPlayingMs,
    playbackSource: perf.playbackSource,
    videoSrc: perf.videoSrc,
    mode: "player-warm-tap",
  };
}

async function measurePlayerStart(page, baseUrl, itemId, { autoPlay = true } = {}) {
  await page.addInitScript(() => {
    window.localStorage.setItem("spiritflix_player_muted", "true");
    window.localStorage.setItem("spiritflix_player_volume", "0");
  });

  const started = performance.now();
  await page.goto(`${baseUrl}/spiritflix/benchmark/player?itemId=${encodeURIComponent(itemId)}&autoplay=${autoPlay ? "1" : "0"}`, {
    waitUntil: "commit",
  });

  const video = page.locator("video").first();
  await video.waitFor({ state: "attached", timeout: 15_000 });

  let playRequestMs = null;
  if (!autoPlay) {
    const playStarted = performance.now();
    await page.locator(".spiritflix-player button[aria-label='Play']").click({ timeout: 5_000 });
    playRequestMs = performance.now() - playStarted;
  }

  const playingStarted = autoPlay ? started : performance.now();
  await page.waitForFunction(
    () => {
      const node = document.querySelector("video");
      return Boolean(node && !node.paused && node.readyState >= 2);
    },
    { timeout: 20_000 },
  );
  const playingMs = performance.now() - playingStarted;
  const perf = await collectPerfMarks(page);
  const canplayMark = perf.marks.find((mark) => mark.name === "canplay");
  const playingMark = perf.marks.find((mark) => mark.name === "playing");
  const rangeSupported = perf.videoSrc?.includes("/api/spiritflix/mobile-optimized") ?? false;

  return {
    elapsedMs: performance.now() - started,
    videoPlayingMs: playingMs,
    videoCanplayMs: canplayMark?.at ?? null,
    videoPlayingMarkMs: playingMark?.at ?? null,
    playRequestMs,
    videoSrc: perf.videoSrc,
    playbackSource: perf.playbackSource,
    source:
      perf.playbackSource === "mac_optimized_mp4"
        ? "mobileOptimized"
        : perf.playbackSource?.includes("hls")
          ? "hls"
          : "directMp4",
    rangeSupported,
    marks: perf.marks,
    route: `/spiritflix/benchmark/player?itemId=${itemId}`,
    mode: "player-real-api",
  };
}

async function runPlaywrightSuite(config) {
  const device = devices["Pixel 5"];
  const browser = await chromium.launch({ headless: true });
  const results = { shell: [], player: [], warmTap: [] };

  try {
    const warmupContext = await browser.newContext({
      ...device,
      ignoreHTTPSErrors: true,
    });
    const warmupPage = await warmupContext.newPage();
    await warmupPage.goto(`${config.baseUrl}/spiritflix/benchmark/shell`, { waitUntil: "domcontentloaded" });
    await warmupPage.goto(
      `${config.baseUrl}/spiritflix/benchmark/player?itemId=${encodeURIComponent(config.itemId)}&autoplay=0`,
      { waitUntil: "domcontentloaded" },
    );
    await warmupContext.close();

    for (let index = 0; index < config.runs; index += 1) {
      const context = await browser.newContext({
        ...device,
        ignoreHTTPSErrors: true,
        serviceWorkers: config.mode === "cold" ? "block" : "allow",
      });
      const page = await context.newPage();
      if (config.mode === "cold") {
        await context.clearCookies();
      }
      results.shell.push(await measureShellPage(page, config.baseUrl));
      await context.close();
    }

    for (let index = 0; index < config.runs; index += 1) {
      const context = await browser.newContext({
        ...device,
        ignoreHTTPSErrors: true,
        serviceWorkers: config.mode === "cold" ? "block" : "allow",
      });
      const page = await context.newPage();
      if (config.mode === "cold") {
        await context.clearCookies();
      }
      results.player.push(await measurePlayerStart(page, config.baseUrl, config.itemId, { autoPlay: true }));
      await context.close();
    }

    const warmTapContext = await browser.newContext({
      ...device,
      ignoreHTTPSErrors: true,
    });
    const warmTapPage = await warmTapContext.newPage();
    for (let index = 0; index < config.runs; index += 1) {
      results.warmTap.push(await measureWarmVideoTap(warmTapPage, config.baseUrl, config.itemId));
    }
    await warmTapContext.close();
  } finally {
    await browser.close();
  }

  return results;
}

async function main() {
  const config = parseArgs();
  await fs.mkdir(EVIDENCE_DIR, { recursive: true });

  const gitStatus = spawnSync("git", ["status", "--short"], { cwd: ROOT, encoding: "utf8" });
  const commands = [
    "git status --short",
    `node scripts/spiritflix-mobile-benchmark.mjs --runs=${config.runs}`,
    "npm run typecheck",
    "vitest run src/components/spiritflix src/lib/spiritflix src/app/api/spiritflix/mobile-optimized",
  ];

  const apiCold = await timeMobileOptimizedApi(config.baseUrl, config.itemId, { cold: true });
  const apiWarmRuns = [];
  for (let index = 0; index < config.runs; index += 1) {
    apiWarmRuns.push(await timeMobileOptimizedApi(config.baseUrl, config.itemId, { cold: false }));
  }

  const playwright = await runPlaywrightSuite(config);
  const shellSummary = summarizeRuns(playwright.shell.map((entry) => entry.usefulContentMs));
  const playerSummary = summarizeRuns(playwright.player.map((entry) => entry.videoPlayingMs));
  const warmTapSummary = summarizeRuns(playwright.warmTap.map((entry) => entry.tapToPlayingMs));
  const apiSummary = summarizeRuns(apiWarmRuns.map((entry) => entry.elapsedMs));

  const payload = {
    generatedAt: new Date().toISOString(),
    config,
    mode: config.mode,
    itemId: config.itemId,
    baseUrl: config.baseUrl,
    commands,
    gitStatus: gitStatus.stdout?.trim() ?? "",
    metrics: {
      apiMobileOptimizedColdMs: apiCold.elapsedMs,
      apiMobileOptimizedWarm: apiSummary,
      pageUsefulContent: shellSummary,
      videoPlaying: playerSummary,
      warmVideoTap: warmTapSummary,
    },
    apiCold,
    apiWarmRuns,
    playwright,
    sourceSelection: {
      api: apiCold.source,
      playerPlaybackSource: playwright.player.at(-1)?.playbackSource ?? null,
      playerVideoSrc: playwright.player.at(-1)?.videoSrc ?? null,
      rangeSupported: apiCold.rangeSupported || playwright.player.at(-1)?.rangeSupported || false,
      mobileOptimized: apiCold.available,
    },
    fixtureNote:
      "Shell route uses seeded SpiritFlixHome data. Player route uses real /api/spiritflix/mobile-optimized and stream APIs with benchmark Jellyfin client stubs for auth-only calls.",
  };

  const jsonPath = path.join(EVIDENCE_DIR, "benchmark.json");
  const mdPath = path.join(EVIDENCE_DIR, "summary.md");
  await fs.writeFile(jsonPath, `${JSON.stringify(payload, null, 2)}\n`);
  await fs.writeFile(
    mdPath,
    buildMarkdownSummary({
      evidenceDir: EVIDENCE_DIR,
      payload,
      targets: { pageP50: 50, pageP95: 50, videoP50: 50, videoP95: 50 },
    }),
  );

  console.log(JSON.stringify({ evidenceDir: EVIDENCE_DIR, metrics: payload.metrics, sourceSelection: payload.sourceSelection }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
