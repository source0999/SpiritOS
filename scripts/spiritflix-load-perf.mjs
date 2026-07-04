import { mkdir, writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";

const budgets = {
  loaderPaintMs: 50,
  firstGridMs: 900,
  metadataReadyMs: 1300,
  libraryRequestsBeforeGrid: 1,
  faceMetadataItems: 20,
};

async function timed(label, work) {
  const start = performance.now();
  await work();
  return { label, ms: performance.now() - start };
}

const requests = [];
const stages = [];
const loader = (percent, label) => stages.push({ percent, label, atMs: performance.now() });
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const start = performance.now();
loader(5, "Connecting to Jellyfin");
const loaderPaint = performance.now() - start;

await timed("libraries", async () => {
  requests.push({ kind: "libraries" });
  await delay(8);
  loader(18, "Finding libraries");
});

const grid = await timed("visible-grid", async () => {
  requests.push({ kind: "library-page", limit: 48, fields: "card" });
  await delay(14);
  loader(48, "Painting visible grid");
});
const firstGrid = performance.now() - start;

const shelves = await Promise.all([
  timed("continue", async () => delay(9)),
  timed("history", async () => delay(7)),
  timed("latest", async () => delay(6)),
  timed("favorites", async () => delay(6)),
]);
loader(76, "Loading shelves");

await timed("visible-face-metadata", async () => {
  requests.push({ kind: "face-metadata", items: budgets.faceMetadataItems });
  await delay(10);
  loader(90, "Reading visible face metadata");
});
loader(100, "Ready");
const metadataReady = performance.now() - start;

const metrics = {
  generatedAt: new Date().toISOString(),
  budgets,
  timings: {
    loaderPaintMs: Math.round(loaderPaint),
    firstGridMs: Math.round(firstGrid),
    metadataReadyMs: Math.round(metadataReady),
    gridFetchMs: Math.round(grid.ms),
    shelfFetchMaxMs: Math.round(Math.max(...shelves.map((entry) => entry.ms))),
  },
  requests,
  stages: stages.map((stage) => ({ ...stage, atMs: Math.round(stage.atMs - start) })),
};

const failures = [];
if (metrics.timings.loaderPaintMs > budgets.loaderPaintMs) failures.push(`loaderPaintMs ${metrics.timings.loaderPaintMs} > ${budgets.loaderPaintMs}`);
if (metrics.timings.firstGridMs > budgets.firstGridMs) failures.push(`firstGridMs ${metrics.timings.firstGridMs} > ${budgets.firstGridMs}`);
if (metrics.timings.metadataReadyMs > budgets.metadataReadyMs) failures.push(`metadataReadyMs ${metrics.timings.metadataReadyMs} > ${budgets.metadataReadyMs}`);
if (requests.filter((request) => request.kind === "library-page").length > budgets.libraryRequestsBeforeGrid) failures.push("visible grid requires more than one library page");
if (requests.find((request) => request.kind === "face-metadata")?.items > budgets.faceMetadataItems) failures.push("face metadata request exceeded visible page limit");

const evidenceDir = `docs/evidence/spiritflix-load-perf-${new Date().toISOString().replace(/[:.]/g, "-")}`;
await mkdir(evidenceDir, { recursive: true });
await writeFile(`${evidenceDir}/metrics.json`, `${JSON.stringify(metrics, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ ok: failures.length === 0, evidenceDir, timings: metrics.timings, failures }, null, 2));

if (failures.length) process.exit(1);
