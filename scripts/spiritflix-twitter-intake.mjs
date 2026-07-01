#!/usr/bin/env node
import crypto from "node:crypto";
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { pathToFileURL } from "node:url";
import { selectProfile, summarizeProbe } from "./spiritflix-mobile-optimize.mjs";

export const DEFAULT_TEMP_ROOT = "/mnt/spirit-8tb/media/tempTwitter";
export const DEFAULT_LIBRARY_DIR = "/mnt/spirit-8tb/media/yes/videos from x";
const DEFAULT_OPTIMIZED_ROOT = "/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized";
const SUPPORTED_INPUTS = new Set([".mp4", ".m4v", ".mov", ".ts", ".mkv"]);
const IGNORED_SUFFIXES = [".part", ".tmp", ".ytdl", ".download", ".frag", ".m3u8"];
const HLS_FRAGMENT_PATTERN = /\.fhls-(?:audio-[^.]+|[^.]+)\.mp4$/i;

function argValue(name, fallback = "") {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] ?? fallback : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

function now() {
  return new Date().toISOString();
}

function timestampSlug(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "-");
}

function csvCell(value) {
  const text = value == null ? "" : String(value);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

async function writeCsv(filePath, rows, headers) {
  const lines = [headers.join(",")];
  for (const row of rows) lines.push(headers.map((header) => csvCell(row[header])).join(","));
  await fs.writeFile(filePath, `${lines.join("\n")}\n`);
}

function run(command, args, options = {}) {
  return new Promise((resolve) => {
    const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"], ...options });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", (error) => resolve({ code: 127, stdout, stderr: `${stderr}${error.message}` }));
    child.on("close", (code) => resolve({ code, stdout, stderr }));
  });
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

export function isIgnoredTempFile(filePath) {
  const lower = filePath.toLowerCase();
  return IGNORED_SUFFIXES.some((suffix) => lower.endsWith(suffix)) || lower.includes(".part-") || HLS_FRAGMENT_PATTERN.test(filePath);
}

function isSupportedVideo(filePath) {
  return SUPPORTED_INPUTS.has(path.extname(filePath).toLowerCase()) && !isIgnoredTempFile(filePath);
}

async function walkFiles(root) {
  const entries = await fs.readdir(root, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(root, entry.name);
    if (entry.isDirectory()) files.push(...(await walkFiles(fullPath)));
    else if (entry.isFile()) files.push(fullPath);
  }
  return files;
}

async function ffprobeJson(filePath) {
  const result = await run("ffprobe", [
    "-v",
    "error",
    "-print_format",
    "json",
    "-show_format",
    "-show_streams",
    filePath,
  ]);
  if (result.code !== 0) throw new Error(result.stderr || result.stdout || `ffprobe failed for ${filePath}`);
  return JSON.parse(result.stdout);
}

async function checkFaststart(filePath) {
  const handle = await fs.open(filePath, "r");
  try {
    const stat = await handle.stat();
    const length = Math.min(stat.size, 1024 * 1024 * 4);
    const buffer = Buffer.alloc(length);
    await handle.read(buffer, 0, length, 0);
    const text = buffer.toString("latin1");
    const moov = text.indexOf("moov");
    const mdat = text.indexOf("mdat");
    if (moov < 0) return "unknown";
    if (mdat < 0) return "moov-before-mdat";
    return moov < mdat ? "moov-before-mdat" : "moov-after-mdat";
  } finally {
    await handle.close();
  }
}

export function sanitizeLibraryFilename(filename) {
  const parsed = path.parse(filename);
  const base = parsed.name
    .replace(/[<>:"/\\|?*\u0000-\u001F]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[. ]+$/g, "");
  const safeBase = base || crypto.createHash("sha256").update(filename).digest("hex").slice(0, 16);
  return `${safeBase}.mp4`;
}

export function extractTweetId(filename) {
  const match = String(filename).match(/\[(\d{15,25})\]/);
  return match ? match[1] : "";
}

async function buildExistingLibraryIndex(libraryDir) {
  const names = new Set();
  const tweetIds = new Set();
  const entries = await fs.readdir(libraryDir, { withFileTypes: true }).catch(() => []);
  for (const entry of entries) {
    if (!entry.isFile()) continue;
    names.add(entry.name.toLowerCase());
    const tweetId = extractTweetId(entry.name);
    if (tweetId) tweetIds.add(tweetId);
  }
  return { names, tweetIds };
}

function libraryDuplicateReason(plan, libraryIndex) {
  const finalName = sanitizeLibraryFilename(path.basename(plan.source_path));
  const tweetId = extractTweetId(finalName);
  if (tweetId && libraryIndex.tweetIds.has(tweetId)) return `tweet id already exists in library: ${tweetId}`;
  if (libraryIndex.names.has(finalName.toLowerCase())) return `filename already exists in library: ${finalName}`;
  return "";
}

async function conflictSafePath(directory, filename) {
  let candidate = path.join(directory, filename);
  if (!(await exists(candidate))) return candidate;
  const parsed = path.parse(filename);
  for (let index = 1; index < 10_000; index += 1) {
    candidate = path.join(directory, `${parsed.name} (${index})${parsed.ext}`);
    if (!(await exists(candidate))) return candidate;
  }
  throw new Error(`Could not find conflict-safe path for ${filename}`);
}

async function statSnapshot(filePath) {
  const stat = await fs.stat(filePath);
  return {
    path: filePath,
    sizeBytes: stat.size,
    modifiedTime: stat.mtime.toISOString(),
    modifiedMs: stat.mtimeMs,
  };
}

async function buildInventory(tempRoot, stableSeconds) {
  const allFiles = await walkFiles(tempRoot).catch(() => []);
  const nowMs = Date.now();
  const rows = [];
  for (const filePath of allFiles) {
    const stat = await statSnapshot(filePath).catch(() => null);
    if (!stat) continue;
    const extension = path.extname(filePath).toLowerCase();
    const ignored = isIgnoredTempFile(filePath);
    const supported = isSupportedVideo(filePath);
    const oldEnough = nowMs - stat.modifiedMs >= stableSeconds * 1000;
    rows.push({
      path: filePath,
      filename: path.basename(filePath),
      extension,
      size_bytes: stat.sizeBytes,
      modified_time: stat.modifiedTime,
      supported_video: supported ? "yes" : "no",
      ignored_incomplete: ignored ? "yes" : "no",
      old_enough: oldEnough ? "yes" : "no",
    });
  }
  return rows;
}

async function stableVideoPlans(tempRoot, stableSeconds) {
  const first = await buildInventory(tempRoot, stableSeconds);
  await new Promise((resolve) => setTimeout(resolve, 2000));
  const secondByPath = new Map((await buildInventory(tempRoot, stableSeconds)).map((row) => [row.path, row]));
  const plans = [];
  const skipped = [];
  for (const row of first) {
    const second = secondByPath.get(row.path);
    if (!second) continue;
    if (row.supported_video !== "yes") {
      skipped.push({ ...second, reason: row.ignored_incomplete === "yes" ? "incomplete/temp file" : "unsupported input" });
      continue;
    }
    if (String(row.size_bytes) !== String(second.size_bytes)) {
      skipped.push({ ...second, reason: "size changed between scans" });
      continue;
    }
    if (second.old_enough !== "yes") {
      skipped.push({ ...second, reason: `modified less than ${stableSeconds}s ago` });
      continue;
    }
    try {
      const sourceProbe = summarizeProbe(await ffprobeJson(second.path));
      const faststartStatus = await checkFaststart(second.path);
      if (!sourceProbe.hasVideo || !sourceProbe.duration) {
        skipped.push({ ...second, reason: "ffprobe has no video or zero duration" });
        continue;
      }
      const recommendedProfile = selectProfile({ sourceProbe, faststartStatus, requestedProfile: "auto" });
      plans.push({
        ...second,
        source_path: second.path,
        duration: sourceProbe.duration,
        container: sourceProbe.container,
        video_codec: sourceProbe.videoCodec,
        audio_codec: sourceProbe.audioCodec,
        width: sourceProbe.width,
        height: sourceProbe.height,
        bitrate: sourceProbe.bitrate,
        faststart_status: faststartStatus,
        recommended_profile: recommendedProfile,
        delete_after_verify: "yes",
      });
    } catch (error) {
      skipped.push({ ...second, reason: error instanceof Error ? error.message : String(error) });
    }
  }
  plans.sort((left, right) => Number(left.size_bytes) - Number(right.size_bytes) || left.path.localeCompare(right.path));
  return { plans, skipped, inventory: await buildInventory(tempRoot, stableSeconds) };
}

function closeEnoughDuration(sourceDuration, finalDuration) {
  if (!sourceDuration || !finalDuration) return false;
  return Math.abs(Number(sourceDuration) - Number(finalDuration)) <= Math.max(2, Number(sourceDuration) * 0.03);
}

async function processPlan({ plan, evidenceDir, libraryDir, optimizedRoot, macHost, profile, deleteSource }) {
  const scriptPath = path.join(path.dirname(fileURLToPath(import.meta.url)), "spiritflix-mobile-optimize.mjs");
  const itemId = `twitter-${crypto.createHash("sha256").update(plan.source_path).digest("hex").slice(0, 16)}`;
  const optimizerArgs = [
    scriptPath,
    "--source",
    plan.source_path,
    "--mac-host",
    macHost,
    "--item-id",
    itemId,
    "--profile",
    profile,
    "--output-root",
    optimizedRoot,
  ];
  const startedAt = now();
  const result = await run(process.execPath, optimizerArgs);
  const receiptPath = result.stdout.trim().split(/\r?\n/).pop();
  if (result.code !== 0) {
    return {
      status: "failed",
      tempSourcePath: plan.source_path,
      startedAt,
      completedAt: now(),
      error: result.stderr || result.stdout,
      optimizerReceiptPath: receiptPath,
    };
  }
  const optimizerReceipt = JSON.parse(await fs.readFile(receiptPath, "utf8"));
  if (optimizerReceipt.status !== "ok") throw new Error(`Optimizer receipt was not ok for ${plan.source_path}`);
  const outputPath = optimizerReceipt.outputPath;
  const outputProbe = summarizeProbe(await ffprobeJson(outputPath));
  if (!outputProbe.hasVideo || !outputPath.toLowerCase().endsWith(".mp4")) {
    throw new Error(`Optimized output failed MP4/video verification: ${outputPath}`);
  }
  if (!closeEnoughDuration(plan.duration, outputProbe.duration)) {
    throw new Error(`Duration mismatch for ${plan.source_path}: ${plan.duration} vs ${outputProbe.duration}`);
  }
  const finalName = sanitizeLibraryFilename(path.basename(plan.source_path));
  await fs.mkdir(libraryDir, { recursive: true });
  const finalPath = await conflictSafePath(libraryDir, finalName);
  await fs.copyFile(outputPath, finalPath);
  const finalProbe = summarizeProbe(await ffprobeJson(finalPath));
  const outputStat = await fs.stat(outputPath);
  const finalStat = await fs.stat(finalPath);
  if (outputStat.size !== finalStat.size) throw new Error(`Final size mismatch after copy: ${finalPath}`);
  if (!finalProbe.hasVideo || !finalPath.toLowerCase().endsWith(".mp4")) {
    throw new Error(`Final library file failed MP4/video verification: ${finalPath}`);
  }
  let sourceDeleted = false;
  let deletionError = "";
  if (deleteSource) {
    try {
      await fs.unlink(plan.source_path);
      sourceDeleted = true;
    } catch (error) {
      deletionError = error instanceof Error ? error.message : String(error);
    }
  }
  return {
    schema: "spiritflix-twitter-intake-import/v1",
    status: "ok",
    tempSourcePath: plan.source_path,
    optimizedOutputPath: outputPath,
    finalLibraryPath: finalPath,
    sourceFfprobe: {
      duration: plan.duration,
      container: plan.container,
      videoCodec: plan.video_codec,
      audioCodec: plan.audio_codec,
      width: plan.width,
      height: plan.height,
      bitrate: plan.bitrate,
    },
    outputFfprobe: outputProbe,
    finalFfprobe: finalProbe,
    workerHost: macHost,
    ffmpegCommandSummary: optimizerReceipt.commandSummary,
    encoderUsed: optimizerReceipt.encoder,
    sourceSize: Number(plan.size_bytes),
    optimizedSize: outputStat.size,
    percentSaved: Number((((Number(plan.size_bytes) - outputStat.size) / Number(plan.size_bytes)) * 100).toFixed(2)),
    finalSize: finalStat.size,
    sourceDeleted,
    deletionTimestamp: sourceDeleted ? now() : "",
    deletionError,
    optimizerReceiptPath: receiptPath,
    created_at: startedAt,
    completedAt: now(),
  };
}

async function main() {
  const started = new Date();
  const evidenceDir = argValue("--evidence-dir", path.join("docs/evidence", `spiritflix-twitter-intake-and-full-mac-batch-${timestampSlug(started)}`));
  const tempRoot = argValue("--temp-root", DEFAULT_TEMP_ROOT);
  const libraryDir = argValue("--library-dir", DEFAULT_LIBRARY_DIR);
  const macHost = argValue("--mac-host", process.env.SPIRITFLIX_MAC_HOST || "spirit-mac-mini");
  const stableSeconds = Number(argValue("--stable-seconds", "120")) || 120;
  const rescanPasses = Number(argValue("--rescan-passes", "2")) || 2;
  const limit = Number(argValue("--limit", "0")) || 0;
  const profile = argValue("--profile", "auto");
  const deleteSource = !hasFlag("--keep-source");
  const optimizedRoot = argValue("--optimized-root", path.join(DEFAULT_OPTIMIZED_ROOT, `twitter-intake-${timestampSlug(started)}`));
  await fs.mkdir(evidenceDir, { recursive: true });
  await fs.mkdir(libraryDir, { recursive: true });

  const before = await buildInventory(tempRoot, stableSeconds);
  await writeCsv(path.join(evidenceDir, "temp-twitter-inventory-before.csv"), before, [
    "path",
    "filename",
    "extension",
    "size_bytes",
    "modified_time",
    "supported_video",
    "ignored_incomplete",
    "old_enough",
  ]);

  const receipts = [];
  const failures = [];
  let consecutiveEmpty = 0;
  let round = 0;
  while (consecutiveEmpty < rescanPasses) {
    round += 1;
    const { plans, skipped } = await stableVideoPlans(tempRoot, stableSeconds);
    const libraryIndex = await buildExistingLibraryIndex(libraryDir);
    const freshPlans = [];
    for (const plan of plans) {
      const duplicateReason = libraryDuplicateReason(plan, libraryIndex);
      if (duplicateReason) {
        skipped.push({ ...plan, reason: duplicateReason });
      } else {
        freshPlans.push(plan);
      }
    }
    const remaining = limit > 0 ? Math.max(0, limit - receipts.filter((receipt) => receipt.status === "ok").length) : 0;
    const roundPlans = limit > 0 ? freshPlans.slice(0, remaining) : freshPlans;
    if (!roundPlans.length) {
      consecutiveEmpty += 1;
      if (round === 1) {
        await writeCsv(path.join(evidenceDir, "temp-twitter-optimization-plan.csv"), freshPlans, [
          "source_path",
          "size_bytes",
          "duration",
          "container",
          "video_codec",
          "audio_codec",
          "width",
          "height",
          "bitrate",
          "faststart_status",
          "recommended_profile",
          "delete_after_verify",
        ]);
      }
      if (limit > 0) break;
      continue;
    }
    consecutiveEmpty = 0;
    if (round === 1) {
      await writeCsv(path.join(evidenceDir, "temp-twitter-optimization-plan.csv"), freshPlans, [
        "source_path",
        "size_bytes",
        "duration",
        "container",
        "video_codec",
        "audio_codec",
        "width",
        "height",
        "bitrate",
        "faststart_status",
        "recommended_profile",
        "delete_after_verify",
      ]);
    }
    await writeCsv(path.join(evidenceDir, `temp-twitter-skipped-round-${round}.csv`), skipped, [
      "path",
      "filename",
      "extension",
      "size_bytes",
      "modified_time",
      "supported_video",
      "ignored_incomplete",
      "old_enough",
      "reason",
    ]);
    for (const plan of roundPlans) {
      try {
        const receipt = await processPlan({ plan, evidenceDir, libraryDir, optimizedRoot, macHost, profile, deleteSource });
        receipts.push(receipt);
      } catch (error) {
        const failure = {
          status: "failed",
          tempSourcePath: plan.source_path,
          error: error instanceof Error ? error.message : String(error),
          created_at: now(),
        };
        receipts.push(failure);
        failures.push(failure);
      }
      await fs.writeFile(path.join(evidenceDir, "temp-twitter-import-receipts.json"), `${JSON.stringify(receipts, null, 2)}\n`);
      if (limit > 0 && receipts.filter((receipt) => receipt.status === "ok").length >= limit) break;
    }
    if (limit > 0 && receipts.filter((receipt) => receipt.status === "ok").length >= limit) break;
  }

  const after = await buildInventory(tempRoot, stableSeconds);
  await writeCsv(path.join(evidenceDir, "temp-twitter-inventory-after.csv"), after, [
    "path",
    "filename",
    "extension",
    "size_bytes",
    "modified_time",
    "supported_video",
    "ignored_incomplete",
    "old_enough",
  ]);
  const imported = receipts.filter((receipt) => receipt.status === "ok");
  const totalSource = imported.reduce((sum, receipt) => sum + Number(receipt.sourceSize || 0), 0);
  const totalOptimized = imported.reduce((sum, receipt) => sum + Number(receipt.optimizedSize || 0), 0);
  const summary = {
    evidenceDir,
    tempRoot,
    libraryDir,
    macHost,
    stableSeconds,
    tempTwitterFilesFoundBefore: before.length,
    tempTwitterFilesFoundAfter: after.length,
    optimized: imported.length,
    imported: imported.length,
    sourceFilesDeletedAfterVerify: imported.filter((receipt) => receipt.sourceDeleted).length,
    failures: failures.length,
    totalSourceSize: totalSource,
    totalOptimizedSize: totalOptimized,
    totalSpaceSaved: totalSource - totalOptimized,
    fullLibraryBatchStarted: false,
    completedAt: now(),
  };
  await fs.writeFile(path.join(evidenceDir, "intake-summary.md"), [
    "# Twitter Intake Summary",
    "",
    `- Temp root: ${tempRoot}`,
    `- Library destination: ${libraryDir}`,
    `- Files found before: ${before.length}`,
    `- Optimized/imported: ${imported.length}`,
    `- Source files deleted after verify: ${summary.sourceFilesDeletedAfterVerify}`,
    `- Failures: ${failures.length}`,
    `- Total source size: ${totalSource}`,
    `- Total optimized size: ${totalOptimized}`,
    `- Total space saved: ${summary.totalSpaceSaved}`,
    "",
  ].join("\n"));
  await fs.writeFile(path.join(evidenceDir, "temp-twitter-failures.md"), failures.length ? failures.map((failure) => `- ${failure.tempSourcePath}: ${failure.error}`).join("\n") + "\n" : "No failures.\n");
  await fs.writeFile(path.join(evidenceDir, "library-import-verification.md"), [
    "# Library Import Verification",
    "",
    `- Destination exists: ${await exists(libraryDir) ? "yes" : "no"}`,
    `- Imported MP4 files verified: ${imported.length}`,
    "- No MKV/TS/HLS outputs are created by this intake script.",
    "",
  ].join("\n"));
  await fs.writeFile(path.join(evidenceDir, "full-library-batch-start.md"), [
    "# Full Library Batch",
    "",
    "The full-library batch was not started by the intake script.",
    "",
    "Start after tempTwitter is drained/stable and Britton gives GO:",
    "",
    "```bash",
    "node scripts/spiritflix-mobile-optimize.mjs --queue docs/evidence/spiritflix-phase7b-phase8-playback-order-20260620-211911/full-library-optimization-queue.csv --mac-host spirit-mac-mini --skip-existing --smallest-first --profile auto --workers 1 --stop-on-failure",
    "```",
    "",
  ].join("\n"));
  await writeCsv(path.join(evidenceDir, "full-library-batch-progress.csv"), [], ["source", "status", "receiptPath", "outputPath"]);
  await fs.writeFile(path.join(evidenceDir, "full-library-batch-receipts.json"), "[]\n");
  await fs.writeFile(path.join(evidenceDir, "full-library-batch-failures.md"), "Full-library batch not started yet.\n");
  await fs.writeFile(path.join(evidenceDir, "final-summary.md"), `${JSON.stringify(summary, null, 2)}\n`);
  console.log(JSON.stringify(summary, null, 2));
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack || error.message : error);
    process.exit(1);
  });
}
