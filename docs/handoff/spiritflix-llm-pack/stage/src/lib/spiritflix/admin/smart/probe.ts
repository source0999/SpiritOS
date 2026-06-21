import path from "node:path";
import { assertSmartVideoPathCandidate, type SpiritFlixSmartPathOptions } from "./analysis-paths";
import { SpiritFlixSmartProbeError } from "./errors";
import { spawn } from "./process";

export const SPIRITFLIX_SMART_VIDEO_EXTENSIONS = new Set([".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"]);

const DEFAULT_PROBE_TIMEOUT_MS = 10_000;
const MAX_FFPROBE_OUTPUT_BYTES = 512_000;

export interface SpiritFlixProbeResult {
  durationSeconds?: number;
  width?: number;
  height?: number;
  codec?: string;
  container?: string;
  formatName?: string;
  bitRate?: number;
  frameRate?: number;
}

export interface SpiritFlixProbeOptions {
  timeoutMs?: number;
  ffprobePath?: string;
  mediaRoot?: string;
}

export function isSpiritFlixSmartVideoExtension(extension: string): boolean {
  return SPIRITFLIX_SMART_VIDEO_EXTENSIONS.has(extension.toLowerCase());
}

export function parseRationalFrameRate(value: string | undefined): number | undefined {
  if (!value || value === "0/0" || value === "N/A") return undefined;
  if (!value.includes("/")) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
  }
  const [numRaw, denRaw] = value.split("/");
  const num = Number(numRaw);
  const den = Number(denRaw);
  if (!Number.isFinite(num) || !Number.isFinite(den) || den === 0) return undefined;
  const rate = num / den;
  return rate > 0 ? rate : undefined;
}

export function parseFfprobeJson(payload: unknown): SpiritFlixProbeResult {
  if (!payload || typeof payload !== "object") {
    throw new SpiritFlixSmartProbeError("ffprobe returned invalid JSON.");
  }

  const record = payload as {
    format?: { duration?: string; format_name?: string; bit_rate?: string };
    streams?: Array<{
      codec_type?: string;
      codec_name?: string;
      width?: number;
      height?: number;
      duration?: string;
      avg_frame_rate?: string;
      r_frame_rate?: string;
    }>;
  };

  const format = record.format ?? {};
  const videoStream = record.streams?.find((stream) => stream.codec_type === "video");

  const durationSeconds = parsePositiveNumber(format.duration) ?? parsePositiveNumber(videoStream?.duration);
  const width = parsePositiveInt(videoStream?.width);
  const height = parsePositiveInt(videoStream?.height);
  const codec = videoStream?.codec_name?.trim() || undefined;
  const formatName = format.format_name?.trim() || undefined;
  const bitRate = parsePositiveInt(format.bit_rate);
  const frameRate =
    parseRationalFrameRate(videoStream?.avg_frame_rate) ?? parseRationalFrameRate(videoStream?.r_frame_rate);

  if (!durationSeconds && !width && !height && !codec && !formatName) {
    throw new SpiritFlixSmartProbeError("ffprobe did not return usable video metadata.");
  }

  return {
    durationSeconds,
    width,
    height,
    codec,
    container: formatName,
    formatName,
    bitRate,
    frameRate,
  };
}

function parsePositiveNumber(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
}

function parsePositiveInt(value: number | string | undefined): number | undefined {
  if (value === undefined) return undefined;
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) return undefined;
  return Math.trunc(parsed);
}

function runFfprobe(
  ffprobePath: string,
  videoPath: string,
  timeoutMs: number,
): Promise<{ stdout: string; stderr: string; code: number | null; timedOut: boolean; spawnError?: Error }> {
  return new Promise((resolve) => {
    const args = ["-v", "error", "-print_format", "json", "-show_format", "-show_streams", videoPath];
    const proc = spawn(ffprobePath, args, { shell: false });
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    let settled = false;

    const finish = (result: { stdout: string; stderr: string; code: number | null; timedOut: boolean; spawnError?: Error }) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(result);
    };

    const timer = setTimeout(() => {
      timedOut = true;
      proc.kill("SIGKILL");
      finish({ stdout, stderr, code: null, timedOut });
    }, timeoutMs);

    proc.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf8");
      if (stdout.length > MAX_FFPROBE_OUTPUT_BYTES) {
        proc.kill("SIGKILL");
      }
    });
    proc.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString("utf8");
      if (stderr.length > 8_192) stderr = stderr.slice(-8_192);
    });

    proc.on("error", (error) => {
      finish({ stdout, stderr, code: null, timedOut, spawnError: error });
    });

    proc.on("close", (code) => {
      finish({ stdout, stderr, code, timedOut });
    });
  });
}

export async function probeSpiritFlixVideo(
  videoPath: string,
  options?: SpiritFlixProbeOptions,
): Promise<SpiritFlixProbeResult> {
  const pathOptions: SpiritFlixSmartPathOptions | undefined = options?.mediaRoot
    ? { mediaRoot: options.mediaRoot }
    : undefined;
  const resolvedPath = assertSmartVideoPathCandidate(videoPath, pathOptions);
  const extension = path.extname(resolvedPath).toLowerCase();
  if (!isSpiritFlixSmartVideoExtension(extension)) {
    throw new SpiritFlixSmartProbeError("SpiritFlix smart probe only supports video files.");
  }

  const ffprobePath = options?.ffprobePath ?? "ffprobe";
  const timeoutMs = options?.timeoutMs ?? DEFAULT_PROBE_TIMEOUT_MS;
  const result = await runFfprobe(ffprobePath, resolvedPath, timeoutMs);

  if (result.spawnError) {
    if ((result.spawnError as NodeJS.ErrnoException).code === "ENOENT") {
      throw new SpiritFlixSmartProbeError("ffprobe is not available on this host.");
    }
    throw new SpiritFlixSmartProbeError("ffprobe failed to start.");
  }
  if (result.timedOut) {
    throw new SpiritFlixSmartProbeError("ffprobe timed out.");
  }
  if (result.code !== 0) {
    throw new SpiritFlixSmartProbeError("ffprobe exited with an error.");
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(result.stdout);
  } catch {
    throw new SpiritFlixSmartProbeError("ffprobe returned invalid JSON.");
  }

  return parseFfprobeJson(parsed);
}
