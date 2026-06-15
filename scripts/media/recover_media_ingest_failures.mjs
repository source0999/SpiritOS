#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";

const ROOT = process.env.MEDIA_INGEST_ROOT || "/mnt/spirit-8tb";
const MEDIA_ROOT = process.env.MEDIA_INGEST_MEDIA || path.join(ROOT, "media");
const PROCESSING_ROOT = process.env.MEDIA_INGEST_PROCESSING || path.join(ROOT, "media-processing");
const FAILED_ROOT = path.join(PROCESSING_ROOT, "failed");
const ACTIVE_ROOT = path.join(PROCESSING_ROOT, "active");
const LOG_ROOT = path.join(PROCESSING_ROOT, "logs");
const STATE_PATH = path.join(LOG_ROOT, "media-ingest-state.json");
const EXTENSIONS = new Set([".mkv", ".mp4", ".mov", ".m4v", ".webm"]);
const DRY_RUN = process.argv.includes("--dry-run");

function isMediaFile(file) {
  return EXTENSIONS.has(path.extname(file).toLowerCase()) && !file.endsWith(".tmp.mkv");
}

async function exists(file) {
  return fs.access(file).then(() => true).catch(() => false);
}

async function readJson(file, fallback) {
  try {
    return JSON.parse(await fs.readFile(file, "utf8"));
  } catch {
    return fallback;
  }
}

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true }).catch(() => []);
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walk(full)));
    } else if (entry.isFile()) {
      files.push(full);
    }
  }
  return files.sort();
}

async function movePath(source, target) {
  if (DRY_RUN) {
    return;
  }
  await fs.mkdir(path.dirname(target), { recursive: true });
  try {
    await fs.rename(source, target);
  } catch (error) {
    if (error?.code !== "EXDEV") {
      throw error;
    }
    await fs.copyFile(source, target);
    await fs.rm(source, { force: true });
  }
}

function indexJobs(state) {
  const byId = new Map();
  for (const job of state?.jobs || []) {
    if (job?.id) {
      byId.set(job.id, job);
    }
  }
  return byId;
}

function inferTarget(file, failedJobDir, job) {
  if (job?.sourcePath) {
    return job.sourcePath;
  }

  const rel = path.relative(failedJobDir, file);
  const parts = rel.split(path.sep);
  if (parts.length > 1) {
    return path.join(MEDIA_ROOT, "yes", ...parts);
  }

  return path.join(MEDIA_ROOT, "yes", path.basename(file));
}

async function collectReceipts() {
  const receipts = [];
  for (const file of await walk(MEDIA_ROOT)) {
    if (!file.endsWith(".media-ingest.json")) {
      continue;
    }
    const receipt = await readJson(file, null);
    if (receipt) {
      receipts.push({ receiptPath: file, ...receipt });
    }
  }
  return receipts;
}

async function main() {
  const state = await readJson(STATE_PATH, { jobs: [] });
  const jobsById = indexJobs(state);
  const restored = [];
  const unrecovered = [];
  const successfulDeletes = [];

  for (const receipt of await collectReceipts()) {
    if (receipt.deletedOriginal && receipt.sourcePath && !(await exists(receipt.sourcePath))) {
      successfulDeletes.push({
        sourcePath: receipt.sourcePath,
        finalPath: receipt.finalPath,
        savingsPercent: receipt.savingsPercent,
      });
    }
  }

  const failedEntries = await fs.readdir(FAILED_ROOT, { withFileTypes: true }).catch(() => []);
  for (const entry of failedEntries) {
    if (!entry.isDirectory()) {
      continue;
    }

    const failedJobDir = path.join(FAILED_ROOT, entry.name);
    const job = jobsById.get(entry.name);
    const mediaFiles = (await walk(failedJobDir)).filter(isMediaFile);

    if (mediaFiles.length === 0) {
      unrecovered.push({
        jobId: entry.name,
        reason: "No recoverable media file found in failed job directory.",
        sourcePath: job?.sourcePath,
      });
      continue;
    }

    for (const mediaFile of mediaFiles) {
      const target = inferTarget(mediaFile, failedJobDir, job);
      const finalCandidate = target.replace(/\.[^.]+$/, ".mkv");
      const finalReceipt = `${finalCandidate}.media-ingest.json`;

      if (await exists(target)) {
        unrecovered.push({
          jobId: entry.name,
          reason: "Original target already exists; leaving failed copy untouched.",
          sourcePath: target,
          recoveredFrom: mediaFile,
        });
        continue;
      }

      if ((await exists(finalCandidate)) && (await exists(finalReceipt))) {
        unrecovered.push({
          jobId: entry.name,
          reason: "Converted final output and receipt already exist; failed copy was not restored.",
          sourcePath: target,
          finalPath: finalCandidate,
          recoveredFrom: mediaFile,
        });
        continue;
      }

      await movePath(mediaFile, target);
      restored.push({
        jobId: entry.name,
        restoredTo: target,
        recoveredFrom: mediaFile,
      });
    }
  }

  const report = {
    at: new Date().toISOString(),
    dryRun: DRY_RUN,
    roots: {
      media: MEDIA_ROOT,
      processing: PROCESSING_ROOT,
      failed: FAILED_ROOT,
      active: ACTIVE_ROOT,
    },
    restored,
    unrecovered,
    successfulDeletes,
    reuploadNeeded: unrecovered.filter((item) => item.reason?.startsWith("No recoverable")),
  };

  const reportPath = path.join(LOG_ROOT, `media-ingest-recovery-${Date.now()}.json`);
  if (!DRY_RUN) {
    await fs.mkdir(LOG_ROOT, { recursive: true });
    await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  }

  console.log(JSON.stringify({ ...report, reportPath: DRY_RUN ? null : reportPath }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exitCode = 1;
});
