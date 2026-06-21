#!/usr/bin/env node
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";

const ROOT = process.env.MEDIA_INGEST_ROOT || "/mnt/spirit-8tb";
const INBOX_ROOT = process.env.MEDIA_INGEST_INBOX || path.join(ROOT, "media-inbox");
const MEDIA_ROOT = process.env.MEDIA_INGEST_MEDIA || path.join(ROOT, "media");
const LIBRARY_WATCH_ROOTS = (process.env.MEDIA_INGEST_LIBRARY_WATCH_ROOTS || path.join(MEDIA_ROOT, "yes"))
  .split(path.delimiter)
  .map((entry) => entry.trim())
  .filter(Boolean);
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
const DELETE_LIBRARY_ORIGINALS = process.env.MEDIA_INGEST_DELETE_LIBRARY_ORIGINALS === "1";
const STOP_AFTER_DONE = Number(process.env.MEDIA_INGEST_STOP_AFTER_DONE || 0);
const MAX_QUEUED = Number(process.env.MEDIA_INGEST_MAX_QUEUED || 0);
const INCLUDE_REGEX = process.env.MEDIA_INGEST_INCLUDE_REGEX ? new RegExp(process.env.MEDIA_INGEST_INCLUDE_REGEX) : null;
const SORT_BY_SIZE = process.env.MEDIA_INGEST_SORT_BY_SIZE === "1";
const FACE_SCAN_ON_INGEST = process.env.MEDIA_INGEST_FACE_SCAN_ON_INGEST !== "0";
const FACE_ORGANIZER_PYTHON = process.env.MEDIA_INGEST_FACE_ORGANIZER_PYTHON || ".venv-face-organizer/bin/python";
const FACE_ORGANIZER_SCRIPT = process.env.MEDIA_INGEST_FACE_ORGANIZER_SCRIPT || "scripts/media/face_organizer.py";
const FACE_ORGANIZER_SOURCE = process.env.MEDIA_INGEST_FACE_ORGANIZER_SOURCE || LIBRARY_WATCH_ROOTS[0] || path.join(MEDIA_ROOT, "yes");
const FACE_ORGANIZER_CTX_ID = process.env.MEDIA_INGEST_FACE_ORGANIZER_CTX_ID || "0";
const FACE_ORGANIZER_FRAME_COUNT = process.env.MEDIA_INGEST_FACE_ORGANIZER_FRAME_COUNT || "12";
const CPU_ENCODER_THREADS = Math.max(1, Number(process.env.MEDIA_INGEST_CPU_THREADS || 2));
const CPU_ENCODER_NICE = Number(process.env.MEDIA_INGEST_CPU_NICE || 12);
const CPU_ENCODER_CPUSET = process.env.MEDIA_INGEST_CPUSET ?? (process.platform === "linux" ? "0,1" : "");
const POST_PROCESS_THREADS = String(Math.max(1, Number(process.env.MEDIA_INGEST_POST_THREADS || CPU_ENCODER_THREADS)));
const POST_PROCESS_NICE = Number(process.env.MEDIA_INGEST_POST_NICE || CPU_ENCODER_NICE);
const POST_PROCESS_CPUSET = process.env.MEDIA_INGEST_POST_CPUSET ?? CPU_ENCODER_CPUSET;

const state = {
  version: 2,
  queueState: "running",
  jobs: [],
};

class NotWorthConvertingError extends Error {
  constructor(message) {
    super(message);
    this.name = "NotWorthConvertingError";
  }
}

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
  for (const root of LIBRARY_WATCH_ROOTS) {
    await fs.mkdir(root, { recursive: true });
  }
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

function quoteCommandArg(arg) {
  return arg.includes(" ") ? JSON.stringify(arg) : arg;
}

function buildBackgroundCommand(baseCommand, args, options = {}) {
  const nice = options.nice ?? CPU_ENCODER_NICE;
  const cpuset = options.cpuset ?? CPU_ENCODER_CPUSET;
  let command = baseCommand;
  let spawnArgs = args;
  let display = [baseCommand, ...args];

  if (cpuset && process.platform === "linux") {
    command = "taskset";
    spawnArgs = ["-c", cpuset, baseCommand, ...spawnArgs];
    display = ["taskset", "-c", cpuset, ...display];
  }

  if (Number.isFinite(nice) && nice !== 0 && process.platform !== "win32") {
    spawnArgs = ["-n", String(nice), command, ...spawnArgs];
    display = ["nice", "-n", String(nice), ...display];
    command = "nice";
  }

  return { command, spawnArgs, display };
}

function buildCpuEncoderCommand(args) {
  return buildBackgroundCommand("ffmpeg", args, { nice: CPU_ENCODER_NICE, cpuset: CPU_ENCODER_CPUSET });
}

function runPostProcess(command, args) {
  return new Promise((resolve, reject) => {
    const background = buildBackgroundCommand(command, args, { nice: POST_PROCESS_NICE, cpuset: POST_PROCESS_CPUSET });
    const child = spawn(background.command, background.spawnArgs, {
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        OMP_NUM_THREADS: process.env.OMP_NUM_THREADS || POST_PROCESS_THREADS,
        OPENBLAS_NUM_THREADS: process.env.OPENBLAS_NUM_THREADS || POST_PROCESS_THREADS,
        MKL_NUM_THREADS: process.env.MKL_NUM_THREADS || POST_PROCESS_THREADS,
        NUMEXPR_NUM_THREADS: process.env.NUMEXPR_NUM_THREADS || POST_PROCESS_THREADS,
      },
    });
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
        resolve({ stdout, stderr, command: background.display });
      } else {
        reject(new Error(`${background.display.join(" ")} exited ${code}: ${stderr || stdout}`));
      }
    });
  });
}

async function runFaceOrganizerScan(finalPath) {
  const sidecarPath = `${finalPath}.face-meta.json`;
  const hasSidecar = await exists(sidecarPath);
  if (!FACE_SCAN_ON_INGEST && hasSidecar) {
    return {
      enabled: false,
      status: "skipped",
      reason: "sidecar already exists and MEDIA_INGEST_FACE_SCAN_ON_INGEST=0",
      at: now(),
      sidecarPath,
    };
  }
  const args = [
    FACE_ORGANIZER_SCRIPT,
    "--scan-video",
    finalPath,
    "--source",
    FACE_ORGANIZER_SOURCE,
    "--apply",
    "--force",
    "--frame-count",
    FACE_ORGANIZER_FRAME_COUNT,
    "--ctx-id",
    FACE_ORGANIZER_CTX_ID,
  ];
  try {
    const result = await runPostProcess(FACE_ORGANIZER_PYTHON, args);
    return {
      enabled: true,
      status: "ok",
      at: now(),
      command: result.command,
      stdout: result.stdout.slice(-4000),
      stderr: result.stderr.slice(-4000),
      sidecarPath: `${finalPath}.face-meta.json`,
    };
  } catch (error) {
    return {
      enabled: true,
      status: "failed",
      at: now(),
      command: buildBackgroundCommand(FACE_ORGANIZER_PYTHON, args, { nice: POST_PROCESS_NICE, cpuset: POST_PROCESS_CPUSET }).display,
      error: error instanceof Error ? error.message : String(error),
      sidecarPath: `${finalPath}.face-meta.json`,
    };
  }
}

async function refreshOrganizerPages() {
  if (process.env.MEDIA_INGEST_REFRESH_ORGANIZER_ON_INGEST === "0") {
    return {
      status: "skipped",
      reason: "MEDIA_INGEST_REFRESH_ORGANIZER_ON_INGEST=0",
      at: now(),
    };
  }
  const args = [
    FACE_ORGANIZER_SCRIPT,
    "--organizer-quick-refresh",
    "--source",
    FACE_ORGANIZER_SOURCE,
    "--ctx-id",
    FACE_ORGANIZER_CTX_ID,
    "--apply",
  ];
  try {
    const result = await runPostProcess(FACE_ORGANIZER_PYTHON, args);
    return {
      status: "ok",
      at: now(),
      command: result.command,
      stdout: result.stdout.slice(-2000),
      stderr: result.stderr.slice(-2000),
    };
  } catch (error) {
    return {
      status: "failed",
      at: now(),
      command: buildBackgroundCommand(FACE_ORGANIZER_PYTHON, args, { nice: POST_PROCESS_NICE, cpuset: POST_PROCESS_CPUSET }).display,
      error: error instanceof Error ? error.message : String(error),
    };
  }
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
  if (SORT_BY_SIZE) {
    const withSizes = await Promise.all(
      files.map(async (file) => ({ file, size: (await fs.stat(file)).size })),
    );
    return withSizes.sort((a, b) => a.size - b.size || a.file.localeCompare(b.file)).map((entry) => entry.file);
  }
  return files.sort();
}

function receiptPathFor(file) {
  return `${file}.media-ingest.json`;
}

function skipReceiptPathFor(file) {
  return `${file}.media-ingest-skip.json`;
}

async function exists(file) {
  return fs.access(file).then(() => true).catch(() => false);
}

async function movePath(source, target) {
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

async function hasIngestReceipt(file) {
  return (await exists(receiptPathFor(file))) || (await exists(skipReceiptPathFor(file)));
}

async function chooseFinalPath(relativeOutput, activePath) {
  const requested = path.join(MEDIA_ROOT, relativeOutput);
  const activeOriginalFinalPath = path.join(MEDIA_ROOT, relativeOutput.replace(/\.mkv$/, path.extname(activePath)));
  if (!(await exists(requested)) || requested === activeOriginalFinalPath) {
    return requested;
  }

  const parsed = path.parse(relativeOutput);
  for (let attempt = 1; attempt <= 100; attempt += 1) {
    const suffix = attempt === 1 ? ".optimized" : `.optimized-${attempt}`;
    const candidate = path.join(MEDIA_ROOT, parsed.dir, `${parsed.name}${suffix}${parsed.ext}`);
    if (!(await exists(candidate))) {
      return candidate;
    }
  }

  throw new Error(`Could not choose a non-conflicting final output path for ${relativeOutput}.`);
}

function libraryCategoryAndRelative(file, root) {
  const relativeToMedia = path.relative(MEDIA_ROOT, file);
  if (!relativeToMedia.startsWith("..") && !path.isAbsolute(relativeToMedia)) {
    const [category, ...rest] = relativeToMedia.split(path.sep);
    return {
      category: category || path.basename(root),
      relativeInCategory: rest.join(path.sep) || path.basename(file),
    };
  }

  const relativeToRoot = path.relative(root, file);
  return {
    category: path.basename(root) || "yes",
    relativeInCategory: relativeToRoot || path.basename(file),
  };
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

function makeInboxJob(file) {
  const rel = path.relative(INBOX_ROOT, file);
  const [category, ...rest] = rel.split(path.sep);
  const relativeInCategory = rest.join(path.sep);
  return makeJob({
    file,
    category: category || "other",
    relativeInCategory: relativeInCategory || path.basename(file),
    sourceKind: "inbox",
    deleteOriginalOnSuccess: false,
  });
}

function makeLibraryJob(file, root) {
  const { category, relativeInCategory } = libraryCategoryAndRelative(file, root);
  return makeJob({
    file,
    category,
    relativeInCategory,
    sourceKind: "library",
    deleteOriginalOnSuccess: DELETE_LIBRARY_ORIGINALS,
  });
}

function makeJob({ file, category, relativeInCategory, sourceKind, deleteOriginalOnSuccess }) {
  const id = `mi-${Date.now().toString(36)}-${Math.random().toString(16).slice(2, 10)}`;
  return {
    id,
    sourcePath: file,
    sourceKind,
    deleteOriginalOnSuccess,
    category,
    relativeInCategory,
    profile: "balanced_1080p",
    status: "queued",
    createdAt: now(),
    updatedAt: now(),
    logs: [{ at: now(), message: `Queued stable file ${file}` }],
  };
}

async function enqueueStableCandidates(files, makeCandidateJob) {
  for (const file of files) {
    if (INCLUDE_REGEX && !INCLUDE_REGEX.test(file)) {
      continue;
    }
    if (state.jobs.some((job) => job.sourcePath === file && job.status !== "failed")) {
      await log(`Skipped duplicate: ${file}`);
      continue;
    }
    if (await hasIngestReceipt(file)) {
      await log(`Skipped already-ingested output: ${file}`);
      continue;
    }
    await log(`Discovered candidate: ${file}`);
    await log(`Checking stability: ${file}`);
    if (!(await isStable(file))) {
      await log(`Not stable yet: ${file}`);
      continue;
    }
    await log(`Stable: ${file}`);
    const job = makeCandidateJob(file);
    state.jobs.push(job);
    await log(`Queued job ${job.id}: ${file}`);
    await writeState();
    if (MAX_QUEUED > 0 && state.jobs.filter((existingJob) => existingJob.status === "queued").length >= MAX_QUEUED) {
      await log(`Max queued target reached: ${MAX_QUEUED} queued job(s).`);
      break;
    }
  }
}

async function scan() {
  const inboxFiles = await walk(INBOX_ROOT);
  await log(`Polling scan found ${inboxFiles.length} filesystem entries under ${INBOX_ROOT}.`);
  await enqueueStableCandidates(inboxFiles, makeInboxJob);

  for (const root of LIBRARY_WATCH_ROOTS) {
    const libraryFiles = await walk(root);
    await log(`Polling scan found ${libraryFiles.length} filesystem entries under library watch root ${root}.`);
    await enqueueStableCandidates(libraryFiles, (file) => makeLibraryJob(file, root));
  }
}

async function processJob(job) {
  job.status = "running";
  job.startedAt = now();
  await jobLog(job, "Moving source into active processing.");

  const activeDir = path.join(ACTIVE_ROOT, job.id);
  await fs.mkdir(activeDir, { recursive: true });
  const activePath = path.join(activeDir, path.basename(job.relativeInCategory));
  await movePath(job.sourcePath, activePath);
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
      "-threads",
      String(CPU_ENCODER_THREADS),
      "-x265-params",
      `pools=${CPU_ENCODER_THREADS}`,
      "-c:a",
      "copy",
      "-c:s",
      "copy",
      tempOutputPath,
    ];
    const cpuEncoder = buildCpuEncoderCommand(args);
    job.command = cpuEncoder.display;
    await jobLog(job, cpuEncoder.display.map(quoteCommandArg).join(" "));

    await new Promise((resolve, reject) => {
      const child = spawn(cpuEncoder.command, cpuEncoder.spawnArgs, { stdio: ["ignore", "pipe", "pipe"] });
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
    job.notWorthConverting = true;
    job.skipReceiptPath = skipReceiptPathFor(job.sourcePath);
    job.skipReceipt = {
      at: now(),
      jobId: job.id,
      sourceKind: job.sourceKind,
      sourcePath: job.sourcePath,
      originalSize: job.originalSize,
      outputSize,
      savingsPercent: Number(savings.toFixed(2)),
      profile: job.profile,
      encoder: ENCODER,
      skipped: true,
      reason: "Converted output was not meaningfully smaller.",
    };
    throw new NotWorthConvertingError(`Converted output was not meaningfully smaller. Savings: ${savings.toFixed(2)}%.`);
  }
  await jobLog(job, `Accepted output. Savings: ${savings.toFixed(2)}%.`);

  const finalPath = await chooseFinalPath(path.join(job.category, outputRelative), activePath);
  const originalHoldingPath = path.join(ORIGINALS_ROOT, job.category, job.id, job.relativeInCategory);
  await fs.mkdir(path.dirname(finalPath), { recursive: true });
  await fs.mkdir(path.dirname(originalHoldingPath), { recursive: true });
  await jobLog(job, "Moving output and handling original.");
  await movePath(tempOutputPath, finalPath);
  const receipt = {
    at: now(),
    jobId: job.id,
    sourceKind: job.sourceKind,
    sourcePath: job.sourcePath,
    finalPath,
    originalSize: job.originalSize,
    outputSize,
    savingsPercent: Number(savings.toFixed(2)),
    profile: job.profile,
    encoder: ENCODER,
    deletedOriginal: Boolean(job.deleteOriginalOnSuccess),
  };
  await fs.writeFile(receiptPathFor(finalPath), `${JSON.stringify(receipt, null, 2)}\n`);
  await jobLog(job, "Running face organizer scan for uploaded video.");
  receipt.faceOrganizerScan = await runFaceOrganizerScan(finalPath);
  await fs.writeFile(receiptPathFor(finalPath), `${JSON.stringify(receipt, null, 2)}\n`);
  await jobLog(job, `Face organizer scan ${receipt.faceOrganizerScan.status}.`);
  await jobLog(job, "Refreshing organizer verification/enrollment HTML pages.");
  receipt.organizerPageRefresh = await refreshOrganizerPages();
  await fs.writeFile(receiptPathFor(finalPath), `${JSON.stringify(receipt, null, 2)}\n`);
  await jobLog(job, `Organizer page refresh ${receipt.organizerPageRefresh.status}.`);
  if (job.deleteOriginalOnSuccess) {
    await fs.rm(activePath, { force: true });
    job.originalDeleted = true;
  } else {
    await movePath(activePath, originalHoldingPath);
    job.originalHoldingPath = originalHoldingPath;
  }
  await fs.rm(activeDir, { recursive: true, force: true });
  job.finalPath = finalPath;
  job.receiptPath = receiptPathFor(finalPath);
  job.status = "done";
  job.progressPercent = 100;
  job.completedAt = now();
  await jobLog(
    job,
    job.deleteOriginalOnSuccess
      ? `Completed. Final: ${finalPath}. Original deleted after successful conversion.`
      : `Completed. Final: ${finalPath}. Original: ${originalHoldingPath}`,
  );
  await jobLog(job, "Jellyfin scan not triggered: set JELLYFIN_URL and JELLYFIN_API_KEY to enable it.");
}

async function failJob(job, error) {
  job.status = "failed";
  job.failedAt = now();
  job.error = error instanceof Error ? error.message : String(error);
  if (job.notWorthConverting && job.skipReceiptPath && job.skipReceipt) {
    await fs.mkdir(path.dirname(job.sourcePath), { recursive: true });
    if (job.activePath && !(await exists(job.sourcePath))) {
      await movePath(job.activePath, job.sourcePath);
    }
    await fs.writeFile(job.skipReceiptPath, `${JSON.stringify(job.skipReceipt, null, 2)}\n`);
    job.status = "skipped";
    await fs.rm(path.dirname(job.activePath), { recursive: true, force: true }).catch(() => {});
    await jobLog(job, `SKIPPED: ${job.error}. Original restored: ${job.sourcePath}`);
    return;
  }
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
  await log(`Library watch roots: ${LIBRARY_WATCH_ROOTS.join(", ") || "(none)"}`);
  if (STOP_AFTER_DONE > 0) {
    await log(`Stop-after mode enabled: worker exits after ${STOP_AFTER_DONE} completed job(s).`);
  }
  if (MAX_QUEUED > 0) {
    await log(`Max-queued mode enabled: scan queues up to ${MAX_QUEUED} job(s).`);
  }
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
      if (STOP_AFTER_DONE > 0 && state.jobs.filter((job) => job.status === "done").length >= STOP_AFTER_DONE) {
        await log(`Stop-after target reached: ${STOP_AFTER_DONE} completed job(s). Exiting.`);
        break;
      }
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
