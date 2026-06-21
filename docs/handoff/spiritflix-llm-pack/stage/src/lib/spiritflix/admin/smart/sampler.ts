import fs from "node:fs/promises";
import path from "node:path";
import {
  assertSmartVideoPathCandidate,
  createSmartAnalysisPathKey,
  getSmartAnalysisCacheRoot,
  type SpiritFlixSmartPathInput,
  type SpiritFlixSmartPathOptions,
} from "./analysis-paths";
import { SpiritFlixSmartSamplerError } from "./errors";
import { isSpiritFlixSmartVideoExtension } from "./probe";
import { spawn } from "./process";

const DEFAULT_FRAME_TIMEOUT_MS = 15_000;
const FRAME_CACHE_VERSION = "v1";
const DEFAULT_SCALE_WIDTH = 480;

export interface SpiritFlixSamplePlanOptions {
  maxSamples?: number;
  minSamples?: number;
  avoidStartSeconds?: number;
  avoidEndSeconds?: number;
}

export interface SpiritFlixFrameSample {
  timestampSeconds: number;
  timestampLabel: string;
  cacheKey: string;
  framePath: string;
  width?: number;
  height?: number;
}

export interface SpiritFlixFrameExtractionOptions {
  timeoutMs?: number;
  ffmpegPath?: string;
  mediaRoot?: string;
  scaleWidth?: number;
  analysisKey?: string;
}

function pathOptions(mediaRoot?: string): SpiritFlixSmartPathOptions | undefined {
  return mediaRoot ? { mediaRoot } : undefined;
}

function clampTimestamp(seconds: number, durationSeconds: number): number {
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) return 0;
  const max = Math.max(0, durationSeconds - 0.05);
  return Math.min(Math.max(0, seconds), max);
}

function roundTimestamp(seconds: number): number {
  return Math.round(seconds * 1000) / 1000;
}

function formatTimestampLabel(seconds: number): string {
  return `${roundTimestamp(seconds)}s`;
}

function defaultSampleCap(durationSeconds: number, maxSamples?: number): number {
  const cap =
    maxSamples ??
    (durationSeconds < 30 ? 3 : durationSeconds < 300 ? 6 : durationSeconds < 1_800 ? 12 : 16);
  return Math.max(1, cap);
}

export function planSpiritFlixSampleTimestamps(
  durationSeconds: number,
  options?: SpiritFlixSamplePlanOptions,
): number[] {
  if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) {
    throw new SpiritFlixSmartSamplerError("durationSeconds must be a positive number.");
  }

  const avoidStart = options?.avoidStartSeconds ?? (durationSeconds >= 12 ? 5 : 1);
  const avoidEnd = options?.avoidEndSeconds ?? (durationSeconds >= 12 ? 5 : 1);
  const minSamples = Math.max(1, options?.minSamples ?? 1);
  const maxSamples = Math.max(minSamples, defaultSampleCap(durationSeconds, options?.maxSamples));

  const start = clampTimestamp(avoidStart, durationSeconds);
  const end = clampTimestamp(durationSeconds - avoidEnd, durationSeconds);

  const timestamps: number[] = [];

  if (durationSeconds < 3 || end <= start) {
    timestamps.push(roundTimestamp(durationSeconds / 2));
  } else if (maxSamples === 1) {
    timestamps.push(roundTimestamp((start + end) / 2));
  } else {
    const step = (end - start) / (maxSamples - 1);
    for (let index = 0; index < maxSamples; index += 1) {
      timestamps.push(roundTimestamp(start + step * index));
    }
  }

  const unique = [...new Set(timestamps.map((value) => roundTimestamp(clampTimestamp(value, durationSeconds))))];
  unique.sort((left, right) => left - right);
  return unique.slice(0, maxSamples);
}

export function buildSpiritFlixFrameCacheFileName(analysisKey: string, timestampMs: number): string {
  if (!/^[a-f0-9]{64}$/.test(analysisKey)) {
    throw new SpiritFlixSmartSamplerError("analysisKey must be a sha256 hex digest.");
  }
  if (!Number.isFinite(timestampMs) || timestampMs < 0) {
    throw new SpiritFlixSmartSamplerError("timestampMs must be a non-negative number.");
  }
  return `${analysisKey}-t${Math.trunc(timestampMs)}-${FRAME_CACHE_VERSION}.jpg`;
}

export function getSpiritFlixFrameCachePath(
  analysisKey: string,
  timestampMs: number,
  options?: SpiritFlixSmartPathOptions,
): string {
  const framesRoot = path.join(getSmartAnalysisCacheRoot(options), "frames");
  const fileName = buildSpiritFlixFrameCacheFileName(analysisKey, timestampMs);
  const framePath = path.join(framesRoot, fileName);
  const resolvedRoot = path.resolve(framesRoot);
  const resolvedFrame = path.resolve(framePath);
  if (!resolvedFrame.startsWith(resolvedRoot + path.sep) && resolvedFrame !== resolvedRoot) {
    throw new SpiritFlixSmartSamplerError("Frame cache path escaped the frames root.");
  }
  return resolvedFrame;
}

function formatSeek(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  const wholeSecs = Math.floor(secs);
  const millis = Math.round((secs - wholeSecs) * 1000);
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(wholeSecs).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
}

function runFfmpegFrame(
  ffmpegPath: string,
  videoPath: string,
  timestampSeconds: number,
  outputPath: string,
  scaleWidth: number,
  timeoutMs: number,
): Promise<{ ok: boolean; timedOut: boolean; spawnError?: Error }> {
  return new Promise((resolve) => {
    const args = [
      "-hide_banner",
      "-loglevel",
      "error",
      "-ss",
      formatSeek(timestampSeconds),
      "-i",
      videoPath,
      "-frames:v",
      "1",
      "-vf",
      `scale=${scaleWidth}:-1`,
      "-q:v",
      "5",
      "-y",
      outputPath,
    ];
    const proc = spawn(ffmpegPath, args, { shell: false });
    let timedOut = false;
    let settled = false;

    const finish = (result: { ok: boolean; timedOut: boolean; spawnError?: Error }) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(result);
    };

    const timer = setTimeout(() => {
      timedOut = true;
      proc.kill("SIGKILL");
      finish({ ok: false, timedOut });
    }, timeoutMs);

    proc.on("error", (error) => {
      finish({ ok: false, timedOut, spawnError: error });
    });
    proc.on("close", (code) => {
      finish({ ok: code === 0, timedOut });
    });
  });
}

export async function extractSpiritFlixFrameSample(
  videoPath: string,
  timestampSeconds: number,
  options?: SpiritFlixFrameExtractionOptions,
): Promise<SpiritFlixFrameSample> {
  const mediaRoot = options?.mediaRoot;
  const pathOpts = pathOptions(mediaRoot);
  const resolvedPath = assertSmartVideoPathCandidate(videoPath, pathOpts);
  const extension = path.extname(resolvedPath).toLowerCase();
  if (!isSpiritFlixSmartVideoExtension(extension)) {
    throw new SpiritFlixSmartSamplerError("SpiritFlix frame sampler only supports video files.");
  }
  if (!Number.isFinite(timestampSeconds) || timestampSeconds < 0) {
    throw new SpiritFlixSmartSamplerError("timestampSeconds must be a non-negative number.");
  }

  const stat = await fs.stat(resolvedPath);
  const pathInput: SpiritFlixSmartPathInput = {
    videoPath: resolvedPath,
    fileSizeBytes: stat.size,
    mtimeMs: stat.mtimeMs,
  };
  const analysisKey = options?.analysisKey ?? createSmartAnalysisPathKey(pathInput);
  const timestampMs = Math.trunc(timestampSeconds * 1000);
  const framePath = getSpiritFlixFrameCachePath(analysisKey, timestampMs, pathOpts);
  const cacheKey = path.basename(framePath, ".jpg");

  try {
    const existing = await fs.stat(framePath);
    if (existing.isFile() && existing.size > 0) {
      return {
        timestampSeconds: roundTimestamp(timestampSeconds),
        timestampLabel: formatTimestampLabel(timestampSeconds),
        cacheKey,
        framePath,
        width: options?.scaleWidth ?? DEFAULT_SCALE_WIDTH,
      };
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }

  const framesRoot = path.dirname(framePath);
  await fs.mkdir(framesRoot, { recursive: true });
  const tempPath = path.join(framesRoot, `.${cacheKey}.tmp.jpg`);

  const ffmpegPath = options?.ffmpegPath ?? "ffmpeg";
  const timeoutMs = options?.timeoutMs ?? DEFAULT_FRAME_TIMEOUT_MS;
  const scaleWidth = options?.scaleWidth ?? DEFAULT_SCALE_WIDTH;
  const result = await runFfmpegFrame(ffmpegPath, resolvedPath, timestampSeconds, tempPath, scaleWidth, timeoutMs);

  if (result.spawnError) {
    await fs.rm(tempPath, { force: true }).catch(() => undefined);
    if ((result.spawnError as NodeJS.ErrnoException).code === "ENOENT") {
      throw new SpiritFlixSmartSamplerError("ffmpeg is not available on this host.");
    }
    throw new SpiritFlixSmartSamplerError("ffmpeg failed to start.");
  }
  if (result.timedOut) {
    await fs.rm(tempPath, { force: true }).catch(() => undefined);
    throw new SpiritFlixSmartSamplerError("ffmpeg frame extraction timed out.");
  }
  if (!result.ok) {
    await fs.rm(tempPath, { force: true }).catch(() => undefined);
    throw new SpiritFlixSmartSamplerError("ffmpeg frame extraction failed.");
  }

  try {
    await fs.rename(tempPath, framePath);
  } catch {
    await fs.rm(tempPath, { force: true }).catch(() => undefined);
    throw new SpiritFlixSmartSamplerError("Failed to finalize frame cache file.");
  }

  return {
    timestampSeconds: roundTimestamp(timestampSeconds),
    timestampLabel: formatTimestampLabel(timestampSeconds),
    cacheKey,
    framePath,
    width: scaleWidth,
  };
}
