#!/usr/bin/env node
import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const DEFAULT_OUTPUT_ROOT = "/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized";

export const PROFILES = {
  "remux-faststart-only": {
    kind: "remux",
    description: "Copy all streams into MP4 with +faststart. No quality loss.",
  },
  "audio-aac-only": {
    kind: "audio",
    audioBitrate: "128k",
    description: "Copy video and transcode audio to AAC with +faststart.",
  },
  "mobile-720p": {
    kind: "transcode",
    maxWidth: 1280,
    maxHeight: 720,
    videoBitrate: "2800k",
    maxrate: "4200k",
    bufsize: "8400k",
    audioBitrate: "128k",
    description: "H.264/AAC MP4, faststart, max 720p.",
  },
  "mobile-1080p": {
    kind: "transcode",
    maxWidth: 1920,
    maxHeight: 1080,
    videoBitrate: "4500k",
    maxrate: "6500k",
    bufsize: "13000k",
    audioBitrate: "160k",
    description: "H.264/AAC MP4, faststart, max 1080p.",
  },
};

const MAC_FFMPEG_CANDIDATES = [
  "/usr/local/bin/ffmpeg",
  "/opt/homebrew/bin/ffmpeg",
  "/opt/local/bin/ffmpeg",
  "ffmpeg",
];
const MAC_FFPROBE_CANDIDATES = [
  "/usr/local/bin/ffprobe",
  "/opt/homebrew/bin/ffprobe",
  "/opt/local/bin/ffprobe",
  "ffprobe",
];

function argValue(name, fallback = "") {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] ?? fallback : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

function parseCsvLine(line) {
  const cells = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"' && quoted && line[index + 1] === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      cells.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  cells.push(current);
  return cells;
}

async function readCsv(filePath) {
  const text = await fs.readFile(filePath, "utf8");
  const lines = text.split(/\r?\n/).filter((line) => line.trim());
  if (!lines.length) return [];
  const headers = parseCsvLine(lines[0]).map((header) => header.trim());
  return lines.slice(1).map((line) => {
    const cells = parseCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, cells[index] ?? ""]));
  });
}

export function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

async function sha256File(filePath) {
  const hash = crypto.createHash("sha256");
  const handle = await fs.open(filePath, "r");
  try {
    for await (const chunk of handle.createReadStream()) hash.update(chunk);
  } finally {
    await handle.close();
  }
  return hash.digest("hex");
}

function now() {
  return new Date().toISOString();
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

function run(command, args, options = {}) {
  const summary = [command, ...args];
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ["ignore", "pipe", "pipe"], ...options });
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
      const result = { code, stdout, stderr, summary };
      if (code === 0) resolve(result);
      else reject(Object.assign(new Error(`${summary.join(" ")} exited ${code}: ${stderr || stdout}`), result));
    });
  });
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, "'\\''")}'`;
}

async function firstWorkingRemoteBinary(macHost, candidates, versionArg = "-version") {
  for (const candidate of candidates) {
    const result = await run("ssh", [macHost, candidate, versionArg]).catch((error) => error);
    if (result.code === 0) return candidate;
  }
  return "";
}

async function ffprobeJsonLocal(filePath) {
  const result = await run("ffprobe", [
    "-v",
    "error",
    "-print_format",
    "json",
    "-show_format",
    "-show_streams",
    filePath,
  ]);
  return JSON.parse(result.stdout);
}

function getVideo(probe) {
  return probe.streams?.find((stream) => stream.codec_type === "video") ?? null;
}

function getAudio(probe) {
  return probe.streams?.find((stream) => stream.codec_type === "audio") ?? null;
}

export function summarizeProbe(probe) {
  const video = getVideo(probe);
  const audio = getAudio(probe);
  return {
    container: probe.format?.format_name,
    duration: Number(probe.format?.duration || 0),
    bitrate: Number(probe.format?.bit_rate || 0) || undefined,
    videoCodec: video?.codec_name,
    audioCodec: audio?.codec_name,
    width: video?.width,
    height: video?.height,
    videoBitDepth: video?.bits_per_raw_sample,
    pixelFormat: video?.pix_fmt,
    hasVideo: Boolean(video),
    hasAudio: Boolean(audio),
  };
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

export function selectProfile({ sourceProbe, faststartStatus, requestedProfile = "auto" }) {
  if (requestedProfile && requestedProfile !== "auto") {
    if (!PROFILES[requestedProfile]) throw new Error(`Unsupported profile: ${requestedProfile}`);
    return requestedProfile;
  }
  const video = sourceProbe.videoCodec;
  const audio = sourceProbe.audioCodec;
  const width = Number(sourceProbe.width || 0);
  const height = Number(sourceProbe.height || 0);
  const longEdge = Math.max(width, height);
  const h264 = video === "h264";
  const aac = audio === "aac" || !audio;
  if (h264 && aac && longEdge <= 1280) return "remux-faststart-only";
  if (h264 && !aac) return "audio-aac-only";
  if (longEdge > 1280 || sourceProbe.videoCodec !== "h264") return "mobile-720p";
  return "mobile-720p";
}

export function buildOutputPaths({ outputRoot = DEFAULT_OUTPUT_ROOT, sourcePath, itemId = "", createdAt = now() }) {
  const sourceKey = sha256(sourcePath);
  const day = createdAt.slice(0, 10).replace(/-/g, "");
  const outputDir = path.join(outputRoot, day);
  const outputKey = itemId || sourceKey;
  return {
    sourceKey,
    outputDir,
    outputKey,
    outputPath: path.join(outputDir, `${outputKey}.mp4`),
    receiptPath: path.join(outputDir, `${outputKey}.json`),
  };
}

function scaleFilter(profile) {
  return `scale='min(${profile.maxWidth},iw)':'min(${profile.maxHeight},ih)':force_original_aspect_ratio=decrease`;
}

export function buildFfmpegArgs({ ffmpegPath, profileName, encoderName, sourcePath, outputPath }) {
  const profile = PROFILES[profileName];
  if (!profile) throw new Error(`Unsupported profile: ${profileName}`);
  const base = [ffmpegPath, "-hide_banner", "-y", "-i", sourcePath, "-map", "0:v:0", "-map", "0:a:0?"];
  if (profile.kind === "remux") {
    return [...base, "-map", "0:s?", "-c", "copy", "-movflags", "+faststart", outputPath];
  }
  if (profile.kind === "audio") {
    return [...base, "-c:v", "copy", "-c:a", "aac", "-b:a", profile.audioBitrate, "-movflags", "+faststart", outputPath];
  }
  const videoArgs =
    encoderName === "h264_videotoolbox"
      ? ["-c:v", "h264_videotoolbox", "-b:v", profile.videoBitrate, "-maxrate", profile.maxrate, "-bufsize", profile.bufsize]
      : ["-c:v", "libx264", "-preset", "medium", "-crf", "23"];
  return [
    ...base,
    "-vf",
    scaleFilter(profile),
    ...videoArgs,
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-b:a",
    profile.audioBitrate,
    "-movflags",
    "+faststart",
    outputPath,
  ];
}

async function detectMac(macHost, ffmpegOverride = "", ffprobeOverride = "") {
  const ffmpegPath = ffmpegOverride || (await firstWorkingRemoteBinary(macHost, MAC_FFMPEG_CANDIDATES));
  const ffprobePath = ffprobeOverride || (await firstWorkingRemoteBinary(macHost, MAC_FFPROBE_CANDIDATES));
  if (!ffmpegPath) throw new Error(`ffmpeg not found on Mac host ${macHost}`);
  if (!ffprobePath) throw new Error(`ffprobe not found on Mac host ${macHost}`);
  const encoders = await run("ssh", [macHost, ffmpegPath, "-hide_banner", "-encoders"]);
  const encoderText = `${encoders.stdout}\n${encoders.stderr}`;
  const videotoolboxAvailable = encoderText.includes("h264_videotoolbox");
  const x264Available = encoderText.includes("libx264");
  if (!videotoolboxAvailable && !x264Available) {
    throw new Error(`No supported H.264 encoder found on Mac host ${macHost}`);
  }
  return {
    macHost,
    ffmpegPath,
    ffprobePath,
    videotoolboxAvailable,
    x264Available,
    preferredEncoder: videotoolboxAvailable ? "h264_videotoolbox" : "libx264",
  };
}

function commandSummary(args) {
  return args.map((value) => (/\s|[()$"'\\[\]{}?*]/.test(value) ? shellQuote(value) : value)).join(" ");
}

async function main() {
  const dryRun = hasFlag("--dry-run");
  const macHost = argValue("--mac-host", process.env.SPIRITFLIX_MAC_HOST || "spirit-mac-mini");
  const requestedProfile = argValue("--profile", process.env.SPIRITFLIX_MOBILE_PROFILE || "auto");
  const itemId = argValue("--item-id", "");
  const outputRoot = argValue("--output-root", process.env.SPIRITFLIX_MOBILE_OPTIMIZED_ROOT || DEFAULT_OUTPUT_ROOT);
  const sourcePath = argValue("--source");
  const ffmpegOverride = argValue("--mac-ffmpeg", process.env.SPIRITFLIX_MAC_FFMPEG || "");
  const ffprobeOverride = argValue("--mac-ffprobe", process.env.SPIRITFLIX_MAC_FFPROBE || "");
  if (!sourcePath) {
    throw new Error("Usage: node scripts/spiritflix-mobile-optimize.mjs --source /path/file.mp4 [--profile auto|mobile-720p|mobile-1080p|audio-aac-only|remux-faststart-only] [--dry-run]");
  }
  if (!(await exists(sourcePath))) throw new Error(`Source file does not exist: ${sourcePath}`);

  const startedAt = now();
  const started = Date.now();
  const sourceStat = await fs.stat(sourcePath);
  const sourceProbeRaw = await ffprobeJsonLocal(sourcePath);
  const sourceProbe = summarizeProbe(sourceProbeRaw);
  const faststartStatus = await checkFaststart(sourcePath);
  const profileName = selectProfile({ sourceProbe, faststartStatus, requestedProfile });
  const profile = PROFILES[profileName];
  const paths = buildOutputPaths({ outputRoot, sourcePath, itemId, createdAt: startedAt });
  const sourceIdentity = `${sourcePath}\0${sourceStat.size}\0${sourceProbe.duration || 0}\0${sourceStat.mtimeMs}`;
  const sourceIdentitySha256 = sha256(sourceIdentity);
  const sourceContentSha256 = hasFlag("--hash-source") ? await sha256File(sourcePath) : undefined;
  const mac = await detectMac(macHost, ffmpegOverride, ffprobeOverride);
  const encoderName = profile.kind === "transcode" ? mac.preferredEncoder : profile.kind;
  const macTempDir = `/tmp/spiritflix-mobile-${paths.sourceKey.slice(0, 12)}`;
  const macInputPath = `${macTempDir}/${path.basename(sourcePath)}`;
  const macOutputPath = `${macTempDir}/${path.basename(paths.outputPath)}`;
  const remoteArgs = buildFfmpegArgs({
    ffmpegPath: mac.ffmpegPath,
    profileName,
    encoderName: mac.preferredEncoder,
    sourcePath: macInputPath,
    outputPath: macOutputPath,
  });
  const receipt = {
    schema: "spiritflix-mobile-optimized/v2",
    itemId: itemId || undefined,
    sourcePath,
    sourceStableIdentity: {
      path: sourcePath,
      sizeBytes: sourceStat.size,
      durationSeconds: sourceProbe.duration,
      mtime: sourceStat.mtime.toISOString(),
    },
    sourcePathSha256: paths.sourceKey,
    sourceIdentitySha256,
    sourceContentSha256,
    sourceSize: sourceStat.size,
    sourceMtime: sourceStat.mtime.toISOString(),
    outputPath: paths.outputPath,
    outputKey: paths.outputKey,
    inputFfprobe: sourceProbe,
    commandSummary: [
      `ssh ${macHost} mkdir -p ${macTempDir}`,
      `scp ${sourcePath} ${macHost}:${macInputPath}`,
      `ssh ${macHost} ${commandSummary(remoteArgs)}`,
      `scp ${macHost}:${macOutputPath} ${paths.outputPath}`,
    ],
    encoder: encoderName,
    encoderPreference: "h264_videotoolbox, fallback libx264",
    workerHost: macHost,
    workerProof: {
      host: macHost,
      ffmpegPath: mac.ffmpegPath,
      ffprobePath: mac.ffprobePath,
      videotoolboxAvailable: mac.videotoolboxAvailable,
      x264Available: mac.x264Available,
      dellRole: "orchestration, ffprobe verification, scp only; no heavy ffmpeg encode",
    },
    sourceSize: sourceStat.size,
    profile: profileName,
    profileKind: profile.kind,
    created_at: startedAt,
    startedAt,
    status: dryRun ? "dry-run" : "failed",
    rollbackOriginalPreservationNote: "Source MP4 is never overwritten; optimized MP4 is a derivative cache output.",
  };

  await fs.mkdir(paths.outputDir, { recursive: true });

  if (dryRun) {
    await fs.writeFile(paths.receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);
    console.log(paths.receiptPath);
    return;
  }

  try {
    await run("ssh", [macHost, "mkdir", "-p", macTempDir]);
    await run("scp", [sourcePath, `${macHost}:${macInputPath}`]);
    await run("ssh", [macHost, "bash", "-lc", shellQuote(commandSummary(remoteArgs))]);
    await run("scp", [`${macHost}:${macOutputPath}`, paths.outputPath]);
    const outputProbeRaw = await ffprobeJsonLocal(paths.outputPath);
    const outputFfprobe = summarizeProbe(outputProbeRaw);
    const outputStat = await fs.stat(paths.outputPath);
    Object.assign(receipt, {
      completedAt: now(),
      durationMs: Date.now() - started,
      outputFfprobe,
      ffprobe: outputFfprobe,
      outputSize: outputStat.size,
      optimizedSize: outputStat.size,
      percentageSaved: sourceStat.size > 0 ? Number((((sourceStat.size - outputStat.size) / sourceStat.size) * 100).toFixed(2)) : 0,
      percentSaved: sourceStat.size > 0 ? Number((((sourceStat.size - outputStat.size) / sourceStat.size) * 100).toFixed(2)) : 0,
      duration: outputFfprobe.duration,
      status: "ok",
    });
  } catch (error) {
    receipt.completedAt = now();
    receipt.durationMs = Date.now() - started;
    receipt.error = error instanceof Error ? error.message : String(error);
    throw error;
  } finally {
    await fs.writeFile(paths.receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);
    console.log(paths.receiptPath);
  }
}

async function queueMain() {
  const queuePath = argValue("--queue");
  const dryRun = hasFlag("--dry-run");
  const skipExisting = hasFlag("--skip-existing");
  const smallestFirst = hasFlag("--smallest-first");
  const stopOnFailure = hasFlag("--stop-on-failure");
  const limit = Number(argValue("--limit", "0")) || 0;
  const maxSize = Number(argValue("--max-size", "0")) || 0;
  const workers = Number(argValue("--workers", "1")) || 1;
  const startAfter = argValue("--start-after", "");
  const profile = argValue("--profile", process.env.SPIRITFLIX_MOBILE_PROFILE || "auto");
  const macHost = argValue("--mac-host", process.env.SPIRITFLIX_MAC_HOST || "spirit-mac-mini");
  if (workers !== 1) throw new Error("Queue mode currently supports --workers 1 only.");
  const rows = await readCsv(queuePath);
  let candidates = rows
    .map((row) => ({
      ...row,
      source: row.source || row.source_path || row.path,
      outputKey: row.output_key || row.outputKey || "",
      sizeBytes: Number(row.size_bytes || row.sizeBytes || 0),
    }))
    .filter((row) => row.source);
  if (smallestFirst) candidates = candidates.sort((left, right) => left.sizeBytes - right.sizeBytes || left.source.localeCompare(right.source));
  if (startAfter) {
    const index = candidates.findIndex((row) => row.source === startAfter || row.outputKey === startAfter);
    if (index >= 0) candidates = candidates.slice(index + 1);
  }
  if (maxSize > 0) candidates = candidates.filter((row) => !row.sizeBytes || row.sizeBytes <= maxSize);
  if (limit > 0) candidates = candidates.slice(0, limit);
  const scriptPath = fileURLToPath(import.meta.url);
  const results = [];
  for (const row of candidates) {
    const outputKey = row.outputKey || sha256(row.source);
    const paths = buildOutputPaths({ sourcePath: row.source, itemId: outputKey });
    if (skipExisting && (await exists(paths.receiptPath)) && (await exists(paths.outputPath))) {
      results.push({ source: row.source, outputKey, status: "skipped-existing", receiptPath: paths.receiptPath, outputPath: paths.outputPath });
      continue;
    }
    const args = [scriptPath, "--source", row.source, "--mac-host", macHost, "--item-id", outputKey, "--profile", profile];
    if (dryRun) args.push("--dry-run");
    const result = await run(process.execPath, args).catch((error) => error);
    const ok = result.code === 0 || !("code" in result);
    results.push({
      source: row.source,
      outputKey,
      status: ok ? (dryRun ? "dry-run" : "ok") : "failed",
      stdout: result.stdout?.trim(),
      stderr: result.stderr?.trim(),
      receiptPath: paths.receiptPath,
      outputPath: paths.outputPath,
    });
    if (!ok && stopOnFailure) break;
  }
  console.log(JSON.stringify({ queue: queuePath, dryRun, count: results.length, results }, null, 2));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const entry = argValue("--queue") ? queueMain : main;
  entry().catch((error) => {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
  });
}
