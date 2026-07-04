import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { SPIRITFLIX_MEDIA_ROOT } from "../constants";

const DEFAULT_CONVERSION_TIMEOUT_MS = 10 * 60_000;
const MAX_CAPTURE_BYTES = 64_000;

export type SpiritFlixConversionMode = "enqueue" | "execute";
export type SpiritFlixConversionStatus = "queued" | "completed" | "failed";

export interface SpiritFlixConversionBridgeOptions {
  mediaRoot?: string;
  jobId: string;
  videoPath: string;
  fileSizeBytes: number;
  mtimeMs: number;
  outputRoot?: string;
  mode?: SpiritFlixConversionMode;
  command?: string;
  timeoutMs?: number;
}

export interface SpiritFlixConversionReceipt {
  schema: "spiritflix-conversion-receipt/v1";
  receiptId: string;
  jobId: string;
  status: SpiritFlixConversionStatus;
  mode: SpiritFlixConversionMode;
  sourcePath: string;
  outputPath: string;
  originalPreserved: true;
  sourceBefore: {
    fileSizeBytes: number;
    mtimeMs: number;
    sha256?: string;
  };
  outputAfter?: {
    fileSizeBytes: number;
    mtimeMs: number;
    sha256: string;
  };
  command: string;
  args: string[];
  code: number | null;
  timedOut: boolean;
  stdout: string;
  stderr: string;
  rollback: {
    deleteOutputPath: string;
    sourceUntouched: true;
  };
  errorReason?: string;
}

function appendCaptured(current: string, chunk: Buffer): string {
  const next = current + chunk.toString("utf8");
  return next.length > MAX_CAPTURE_BYTES ? next.slice(-MAX_CAPTURE_BYTES) : next;
}

async function sha256File(filePath: string): Promise<string> {
  const hash = crypto.createHash("sha256");
  const file = await fs.open(filePath, "r");
  try {
    for await (const chunk of file.createReadStream()) {
      hash.update(chunk);
    }
  } finally {
    await file.close();
  }
  return hash.digest("hex");
}

function defaultOutputRoot(mediaRoot?: string, outputRoot?: string): string {
  if (outputRoot) return path.resolve(outputRoot);
  return path.join(path.resolve(mediaRoot ?? SPIRITFLIX_MEDIA_ROOT), ".spiritflix-admin", "conversions");
}

export function planSpiritFlixConversionOutput(options: Pick<SpiritFlixConversionBridgeOptions, "mediaRoot" | "outputRoot" | "jobId">): string {
  const root = defaultOutputRoot(options.mediaRoot, options.outputRoot);
  return path.join(root, `${options.jobId}-mobile.mp4`);
}

function buildFfmpegArgs(inputPath: string, outputPath: string): string[] {
  return [
    "-hide_banner",
    "-loglevel",
    "error",
    "-y",
    "-i",
    inputPath,
    "-map",
    "0:v:0",
    "-map",
    "0:a?",
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-crf",
    "23",
    "-c:a",
    "aac",
    "-movflags",
    "+faststart",
    outputPath,
  ];
}

function runFfmpeg(command: string, args: string[], timeoutMs: number): Promise<{ code: number | null; timedOut: boolean; stdout: string; stderr: string; spawnError?: Error }> {
  return new Promise((resolve) => {
    const proc = spawn(command, args, { shell: false });
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    let settled = false;

    const finish = (result: { code: number | null; timedOut: boolean; stdout: string; stderr: string; spawnError?: Error }) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      proc.stdout.removeAllListeners("data");
      proc.stderr.removeAllListeners("data");
      proc.removeAllListeners("error");
      proc.removeAllListeners("close");
      resolve(result);
    };

    const timer = setTimeout(() => {
      timedOut = true;
      proc.kill("SIGKILL");
      finish({ code: null, timedOut, stdout, stderr });
    }, timeoutMs);

    proc.stdout.on("data", (chunk: Buffer) => {
      stdout = appendCaptured(stdout, chunk);
    });
    proc.stderr.on("data", (chunk: Buffer) => {
      stderr = appendCaptured(stderr, chunk);
    });
    proc.on("error", (error) => {
      finish({ code: null, timedOut, stdout, stderr, spawnError: error });
    });
    proc.on("close", (code) => {
      finish({ code, timedOut, stdout, stderr });
    });
  });
}

export async function runSpiritFlixConversionBridge(options: SpiritFlixConversionBridgeOptions): Promise<SpiritFlixConversionReceipt> {
  const mode = options.mode ?? "enqueue";
  const command = options.command ?? "ffmpeg";
  const outputPath = planSpiritFlixConversionOutput(options);
  const args = buildFfmpegArgs(options.videoPath, outputPath);
  const sourceBefore = {
    fileSizeBytes: options.fileSizeBytes,
    mtimeMs: options.mtimeMs,
    sha256: mode === "execute" ? await sha256File(options.videoPath) : undefined,
  };
  const base = {
    schema: "spiritflix-conversion-receipt/v1" as const,
    receiptId: `sf-conversion-${new Date().toISOString()}-${crypto.randomUUID().slice(0, 8)}`,
    jobId: options.jobId,
    mode,
    sourcePath: options.videoPath,
    outputPath,
    originalPreserved: true as const,
    sourceBefore,
    command,
    args,
    rollback: {
      deleteOutputPath: outputPath,
      sourceUntouched: true as const,
    },
  };

  if (mode === "enqueue") {
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    return {
      ...base,
      status: "queued",
      code: null,
      timedOut: false,
      stdout: "",
      stderr: "",
    };
  }

  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  const result = await runFfmpeg(command, args, options.timeoutMs ?? DEFAULT_CONVERSION_TIMEOUT_MS);
  if (result.code !== 0 || result.timedOut || result.spawnError) {
    return {
      ...base,
      status: "failed",
      code: result.code,
      timedOut: result.timedOut,
      stdout: result.stdout,
      stderr: result.spawnError ? appendCaptured(result.stderr, Buffer.from(result.spawnError.message)) : result.stderr,
      errorReason: result.timedOut ? "ffmpeg timed out" : result.spawnError ? result.spawnError.message : "ffmpeg exited with an error",
    };
  }
  const outputStat = await fs.stat(outputPath);
  return {
    ...base,
    status: "completed",
    code: result.code,
    timedOut: result.timedOut,
    stdout: result.stdout,
    stderr: result.stderr,
    outputAfter: {
      fileSizeBytes: outputStat.size,
      mtimeMs: outputStat.mtimeMs,
      sha256: await sha256File(outputPath),
    },
  };
}
