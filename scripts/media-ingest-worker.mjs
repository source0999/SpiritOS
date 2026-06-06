#!/usr/bin/env node
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";

const ROOT = process.env.MEDIA_INGEST_ROOT || "/mnt/spirit-8tb";
const INBOX_ROOT = process.env.MEDIA_INGEST_INBOX || path.join(ROOT, "media-inbox");
const MEDIA_ROOT = process.env.MEDIA_INGEST_MEDIA || path.join(ROOT, "media");
const ORIGINALS_ROOT =
  process.env.MEDIA_INGEST_ORIGINALS || path.join(ROOT, "media-originals", "keep-for-30-days");
const PROCESSING_ROOT = process.env.MEDIA_INGEST_PROCESSING || path.join(ROOT, "media-processing");
const ACTIVE_ROOT = path.join(PROCESSING_ROOT, "active");
const FAILED_ROOT = path.join(PROCESSING_ROOT, "failed");
const LOG_ROOT = path.join(PROCESSING_ROOT, "logs");
const STATE_PATH = path.join(LOG_ROOT, "media-ingest-state.json");
const LOCK_PATH = path.join(LOG_ROOT, "media-ingest-worker.lock");
const POLL_MS = Number(process.env.MEDIA_INGEST_POLL_MS || 30000);
const STABLE_MS = Number(process.env.MEDIA_INGEST_STABLE_MS || 120000);
const EXTENSIONS = new Set([".mkv", ".mp4", ".mov", ".m4v", ".webm"]);
const ENCODER = process.env.MEDIA_INGEST_ENCODER || "cpu-x265";
const MAC_ENCODER_SCRIPT =
  process.env.MEDIA_INGEST_MAC_ENCODER_SCRIPT ||
  path.resolve("scripts/media/mac_videotoolbox_encode.py");
const MAC_VIDEO_BITRATE = process.env.MEDIA_INGEST_MAC_VIDEO_BITRATE || "500k";
const MAC_MAXRATE = process.env.MEDIA_INGEST_MAC_MAXRATE || "900k";
const MAC_BUFSIZE = process.env.MEDIA_INGEST_MAC_BUFSIZE || "1800k";
const MAC_PROFILE = process.env.MEDIA_INGEST_MAC_PROFILE || "main10";

const state = {
  version: 2,
  queueState: "running",
  jobs: [],
};

function now() {
  return new Date().toISOString();
}

function log(message) {
  const line = `[${now()}] ${message}`;
  console.log(line);
  return fs.appendFile(path.join(LOG_ROOT, "worker.log"), `${line}\n`).catch(() => {});
}

function jobLog(job, message) {
  job.logs.push({ at: now(), message });
  job.updatedAt = now();
  return log(`Job ${job.id}: ${message}`);
}

async function ensureDirs() {
  await fs.mkdir(INBOX_ROOT, { recursive: true });
  await fs.mkdir(MEDIA_ROOT, { recursive: true });
  await fs.mkdir(ORIGINALS_ROOT, { recursive: true });
  await fs.mkdir(ACTIVE_ROOT, { recursive: true });
  await fs.mkdir(FAILED_ROOT, { recursive: true });
  await fs.mkdir(LOG_ROOT, { recursive: true });
}

async function writeState() {
  await fs.writeFile(STATE_PATH, `${JSON.stringify(state, null, 2)}\n`);
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(`${command} exited ${code}: ${stderr || stdout}`));
      }
    });
  });
}

async function ffprobe(file) {
  const { stdout } = await run("ffprobe", [
    "-v",
    "error",
    "-print_format",
    "json",
    "-show_format",
    "-show_streams",
    file,
  ]);
  return JSON.parse(stdout);
}

function videoCodec(probe) {
  return probe.streams?.find((stream) => stream.codec_type === "video")?.codec_name || "unknown";
}

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true }).catch(() => []);
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await walk(full)));
    } else if (entry.isFile() && EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
      files.push(full);
    }
  }
  return files.sort();
}

async function isStable(file) {
  const first = await fs.stat(file);
  const age = Date.now() - first.mtimeMs;
  if (age < STABLE_MS) {
    await log(`Not stable: ${file}; age ${(age / 1000).toFixed(1)}s is below ${STABLE_MS / 1000}s.`);
    return false;
  }
  await new Promise((resolve) => setTimeout(resolve, 1000));
  const second = await fs.stat(file);
  return first.size === second.size && first.mtimeMs === second.mtimeMs;
}

function makeJob(file) {
  const rel = path.relative(INBOX_ROOT, file);
  const [category, ...rest] = rel.split(path.sep);
  const relativeInCategory = rest.join(path.sep);
  const id = `mi-${Date.now().toString(36)}-${Math.random().toString(16).slice(2, 10)}`;
  return {
    id,
    sourcePath: file,
    category: category || "other",
    relativeInCategory: relativeInCategory || path.basename(file),
    profile: "balanced_1080p",
    status: "queued",
    createdAt: now(),
    updatedAt: now(),
    logs: [{ at: now(), message: `Queued stable file ${file}` }],
  };
}

async function scan() {
  const files = await walk(INBOX_ROOT);
  await log(`Polling scan found ${files.length} filesystem entries under ${INBOX_ROOT}.`);
  for (const file of files) {
    if (state.jobs.some((job) => job.sourcePath === file && job.status !== "failed")) {
      await log(`Skipped duplicate: ${file}`);
      continue;
    }
    await log(`Discovered candidate: ${file}`);
    await log(`Checking stability: ${file}`);
    if (!(await isStable(file))) {
      await log(`Not stable yet: ${file}`);
      continue;
    }
    await log(`Stable: ${file}`);
    const job = makeJob(file);
    state.jobs.push(job);
    await log(`Queued job ${job.id}: ${file}`);
    await writeState();
  }
}

async function processJob(job) {
  job.status = "running";
  job.startedAt = now();
  await jobLog(job, "Moving source into active processing.");

  const activeDir = path.join(ACTIVE_ROOT, job.id);
  await fs.mkdir(activeDir, { recursive: true });
  const activePath = path.join(activeDir, path.basename(job.relativeInCategory));
  await fs.rename(job.sourcePath, activePath);
  job.activePath = activePath;
  await jobLog(job, `Moved to active: ${activePath}`);

  await jobLog(job, "Running ffprobe on source.");
  job.probe = await ffprobe(activePath);
  job.originalSize = Number(job.probe.format?.size || (await fs.stat(activePath)).size);
  await jobLog(job, `Source codec: ${videoCodec(job.probe)}`);

  const outputRelative = job.relativeInCategory.replace(/\.[^.]+$/, ".mkv");
  const tempOutputPath = path.join(activeDir, path.basename(outputRelative).replace(/\.mkv$/, ".tmp.mkv"));
  job.tempOutputPath = tempOutputPath;
  if (ENCODER === "mac-videotoolbox-hevc") {
    await jobLog(job, `Encoding with Mac VideoToolbox HEVC. bitrate=${MAC_VIDEO_BITRATE}`);
    const args = [
      MAC_ENCODER_SCRIPT,
      "--source",
      activePath,
      "--output",
      tempOutputPath,
      "--video-bitrate",
      MAC_VIDEO_BITRATE,
      "--maxrate",
      MAC_MAXRATE,
      "--bufsize",
      MAC_BUFSIZE,
      "--profile",
      MAC_PROFILE,
      "--force",
    ];
    job.command = ["python3", ...args];
    await jobLog(job, `python3 ${args.map((arg) => (arg.includes(" ") ? JSON.stringify(arg) : arg)).join(" ")}`);
    const { stdout } = await run("python3", args);
    try {
      job.macEncode = JSON.parse(stdout);
      await jobLog(job, `Mac encode completed in ${job.macEncode.elapsedSeconds}s.`);
    } catch {
      await jobLog(job, "Mac encode completed; receipt JSON could not be parsed.");
    }
    job.progressPercent = 90;
  } else {
    await jobLog(job, "Encoding with profile balanced_1080p.");

    const args = [
      "-y",
      "-hide_banner",
      "-progress",
      "pipe:1",
      "-nostats",
      "-i",
      activePath,
      "-map",
      "0",
      "-c:v",
      "libx265",
      "-preset",
      "medium",
      "-crf",
      "22",
      "-pix_fmt",
      "yuv420p10le",
      "-c:a",
      "copy",
      "-c:s",
      "copy",
      tempOutputPath,
    ];
    job.command = ["ffmpeg", ...args];
    await jobLog(job, `ffmpeg ${args.map((arg) => (arg.includes(" ") ? JSON.stringify(arg) : arg)).join(" ")}`);

    await new Promise((resolve, reject) => {
      const child = spawn("ffmpeg", args, { stdio: ["ignore", "pipe", "pipe"] });
      let progress = 0;
      child.stdout.on("data", (chunk) => {
        const text = chunk.toString();
        const timeMatch = text.match(/out_time_ms=(\d+)/);
        const duration = Number(job.probe.format?.duration || 0);
        if (timeMatch && duration > 0) {
          const next = Math.max(10, Math.min(90, Math.round(Number(timeMatch[1]) / 1000000 / duration * 100)));
          if (next > progress) {
            progress = next;
            job.progressPercent = next;
            void jobLog(job, `Encoding progress ${next}%`).then(writeState);
          }
        }
      });
      child.stderr.on("data", () => {});
      child.on("error", reject);
      child.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code}`))));
    });
  }

  await jobLog(job, "FFmpeg completed.");
  await jobLog(job, "Verifying encoded output.");
  await ffprobe(tempOutputPath);
  const outputSize = (await fs.stat(tempOutputPath)).size;
  const savings = job.originalSize ? (1 - outputSize / job.originalSize) * 100 : 0;
  if (savings < 5) {
    throw new Error(`Converted output was not meaningfully smaller. Savings: ${savings.toFixed(2)}%.`);
  }
  await jobLog(job, `Accepted output. Savings: ${savings.toFixed(2)}%.`);

  const finalPath = path.join(MEDIA_ROOT, job.category, outputRelative);
  const originalHoldingPath = path.join(ORIGINALS_ROOT, job.category, job.id, job.relativeInCategory);
  await fs.mkdir(path.dirname(finalPath), { recursive: true });
  await fs.mkdir(path.dirname(originalHoldingPath), { recursive: true });
  await jobLog(job, "Moving output and original into final locations.");
  await fs.rename(tempOutputPath, finalPath);
  await fs.rename(activePath, originalHoldingPath);
  await fs.rm(activeDir, { recursive: true, force: true });
  job.finalPath = finalPath;
  job.originalHoldingPath = originalHoldingPath;
  job.status = "done";
  job.progressPercent = 100;
  job.completedAt = now();
  await jobLog(job, `Completed. Final: ${finalPath}. Original: ${originalHoldingPath}`);
  await jobLog(job, "Jellyfin scan not triggered: set JELLYFIN_URL and JELLYFIN_API_KEY to enable it.");
}

async function failJob(job, error) {
  job.status = "failed";
  job.failedAt = now();
  job.error = error instanceof Error ? error.message : String(error);
  if (job.activePath) {
    const failedDir = path.join(FAILED_ROOT, job.id);
    await fs.mkdir(failedDir, { recursive: true });
    await fs.rename(path.dirname(job.activePath), failedDir).catch(() => {});
  }
  await jobLog(job, `FAILED: ${job.error}`);
}

async function main() {
  await ensureDirs();
  await fs.writeFile(LOCK_PATH, `${process.pid}\n`, { flag: "wx" }).catch((error) => {
    throw new Error(`Worker lock exists at ${LOCK_PATH}: ${error.message}`);
  });
  process.on("exit", () => {
    fs.rm(LOCK_PATH, { force: true }).catch(() => {});
  });

  await log(`Media ingest worker started. inbox=${INBOX_ROOT}`);
  while (true) {
    await scan();
    const next = state.jobs.find((job) => job.status === "queued");
    if (next) {
      try {
        await processJob(next);
      } catch (error) {
        await failJob(next, error);
      }
      await writeState();
      continue;
    }
    await writeState();
    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
  }
}

main().catch(async (error) => {
  await log(`FATAL: ${error instanceof Error ? error.stack || error.message : String(error)}`);
  process.exitCode = 1;
});
