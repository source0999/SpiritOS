import path from "node:path";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";

const DEFAULT_FACE_ORGANIZER_TIMEOUT_MS = 30_000;
const MAX_CAPTURE_BYTES = 64_000;

export interface SpiritFlixFaceOrganizerDryRunOptions {
  command?: string;
  scriptPath?: string;
  sourceDir?: string;
  dbDir?: string;
  frameCount?: number;
  ctxId?: number;
  noOcrWatermarks?: boolean;
  extraArgs?: string[];
  timeoutMs?: number;
  cwd?: string;
}

export interface SpiritFlixFaceOrganizerDryRunResult {
  schema: "spiritflix-face-organizer-dry-run/v1";
  ok: boolean;
  command: string;
  args: string[];
  code: number | null;
  timedOut: boolean;
  stdout: string;
  stderr: string;
  safety: {
    dryRun: true;
    apply: false;
    mediaMutation: false;
  };
  match: SpiritFlixFaceOrganizerMatch;
}

export type SpiritFlixFaceOrganizerMatchStatus =
  | "high_confidence_match"
  | "low_confidence_match"
  | "no_faces"
  | "unknown"
  | "command_failed";

export interface SpiritFlixFaceOrganizerMatch {
  status: SpiritFlixFaceOrganizerMatchStatus;
  matchedModel?: string;
  confidence?: number;
  faceCount?: number;
  parsed: boolean;
  reasonCode: string;
  raw?: unknown;
}

function appendCaptured(current: string, chunk: Buffer): string {
  const next = current + chunk.toString("utf8");
  return next.length > MAX_CAPTURE_BYTES ? next.slice(-MAX_CAPTURE_BYTES) : next;
}

function firstFiniteNumber(...values: unknown[]): number | undefined {
  for (const value of values) {
    const parsed = typeof value === "number" ? value : typeof value === "string" ? Number(value) : Number.NaN;
    if (Number.isFinite(parsed)) return parsed;
  }
  return undefined;
}

function firstString(...values: unknown[]): string | undefined {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return undefined;
}

function firstArray(value: unknown): unknown[] | undefined {
  return Array.isArray(value) ? value : undefined;
}

function parseJsonCandidate(stdout: string): unknown | null {
  const trimmed = stdout.trim();
  if (!trimmed) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    const candidates: unknown[] = [];
    const starts: number[] = [];
    for (let index = 0; index < trimmed.length; index += 1) {
      if (trimmed[index] === "{") starts.push(index);
    }
    for (const start of starts) {
      for (let end = trimmed.lastIndexOf("}"); end > start; end = trimmed.lastIndexOf("}", end - 1)) {
        try {
          candidates.push(JSON.parse(trimmed.slice(start, end + 1)));
        } catch {
          // Keep looking; InsightFace logs Python-style dicts before the real JSON payload.
        }
      }
    }
    return candidates.find((candidate) => {
      if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) return false;
      const record = candidate as Record<string, unknown>;
      return "performers" in record || "video_path" in record || "matchedModel" in record || "matches" in record || "faces" in record;
    }) ?? candidates[0] ?? null;
  }
}

export function parseSpiritFlixFaceOrganizerMatch(
  result: Pick<SpiritFlixFaceOrganizerDryRunResult, "ok" | "stdout" | "stderr" | "code" | "timedOut">,
  highConfidenceThreshold = 0.86,
): SpiritFlixFaceOrganizerMatch {
  if (!result.ok) {
    return {
      status: "command_failed",
      parsed: false,
      reasonCode: result.timedOut ? "face_organizer_timed_out" : "face_organizer_failed",
    };
  }

  const parsed = parseJsonCandidate(result.stdout);
  if (parsed && typeof parsed === "object") {
    const record = parsed as Record<string, unknown>;
    const primary = typeof record.primary === "object" && record.primary ? record.primary as Record<string, unknown> : undefined;
    const match = typeof record.match === "object" && record.match ? record.match as Record<string, unknown> : undefined;
    const matches = firstArray(record.matches) ?? firstArray(record.videos) ?? firstArray(record.faces);
    const performers = firstArray(record.performers);
    const firstMatch = matches?.find((candidate) => candidate && typeof candidate === "object") as Record<string, unknown> | undefined;
    const firstPerformer = performers?.find((candidate) => candidate && typeof candidate === "object") as Record<string, unknown> | undefined;
    const confidence = firstFiniteNumber(
      record.confidence,
      record.score,
      primary?.confidence,
      primary?.score,
      match?.confidence,
      match?.score,
      firstMatch?.confidence,
      firstMatch?.score,
      firstPerformer?.confidence,
      firstPerformer?.similarity,
    );
    const matchedModel = firstString(
      record.matchedModel,
      record.modelName,
      record.primaryPerformer,
      record.performer,
      primary?.modelName,
      primary?.name,
      match?.modelName,
      match?.name,
      firstMatch?.modelName,
      firstMatch?.name,
      firstMatch?.primaryPerformer,
      firstPerformer?.name,
    );
    const faceCount =
      firstFiniteNumber(record.faceCount, record.facesDetected, record.detectedFaces, primary?.faceCount) ??
      (Array.isArray(record.faces) ? record.faces.length : undefined);
    const statusText = firstString(record.status, match?.status, primary?.status, firstPerformer?.status)?.toLowerCase();

    if (statusText === "no_faces" || statusText === "no_face" || faceCount === 0) {
      return { status: "no_faces", parsed: true, reasonCode: "no_faces_found", faceCount: 0, raw: parsed };
    }
    if (matchedModel && matchedModel.toLowerCase() !== "unknown performer" && confidence !== undefined) {
      return {
        status: confidence >= highConfidenceThreshold ? "high_confidence_match" : "low_confidence_match",
        matchedModel,
        confidence,
        faceCount,
        parsed: true,
        reasonCode: confidence >= highConfidenceThreshold ? "high_confidence_known_match" : "low_confidence_match",
        raw: parsed,
      };
    }
    if (performers?.length) {
      return { status: "unknown", parsed: true, reasonCode: "face_organizer_unknown_performer", faceCount, raw: parsed };
    }
    if (faceCount === 0 || statusText?.includes("no face")) {
      return { status: "no_faces", parsed: true, reasonCode: "no_faces_found", faceCount: 0, raw: parsed };
    }
    return { status: "unknown", parsed: true, reasonCode: "face_organizer_no_confident_match", faceCount, raw: parsed };
  }

  const text = `${result.stdout}\n${result.stderr}`.toLowerCase();
  if (text.includes("no face")) {
    return { status: "no_faces", parsed: false, reasonCode: "no_faces_found" };
  }
  return { status: "unknown", parsed: false, reasonCode: "face_organizer_unparsed_output" };
}

export function buildSpiritFlixFaceOrganizerDryRunArgs(
  videoPath: string,
  options: SpiritFlixFaceOrganizerDryRunOptions = {},
): string[] {
  const scriptPath = options.scriptPath ?? path.join("scripts", "media", "face_organizer.py");
  const args = [scriptPath, "--scan-video", videoPath, "--dry-run"];
  if (options.sourceDir) args.push("--source", options.sourceDir);
  if (options.dbDir) args.push("--db", options.dbDir);
  if (options.frameCount && Number.isFinite(options.frameCount)) args.push("--frame-count", String(Math.max(1, Math.trunc(options.frameCount))));
  if (typeof options.ctxId === "number" && Number.isFinite(options.ctxId)) args.push("--ctx-id", String(Math.trunc(options.ctxId)));
  if (options.noOcrWatermarks) args.push("--no-ocr-watermarks");
  if (options.extraArgs?.length) args.push(...options.extraArgs);
  return args;
}

function defaultFaceOrganizerCommand(): string {
  const envCommand = process.env.SPIRITFLIX_FACE_ORGANIZER_PYTHON?.trim();
  if (envCommand) return envCommand;
  const venvCommand = "/home/source/SpiritOS/.venv-face-organizer/bin/python";
  return existsSync(venvCommand) ? venvCommand : "python3";
}

export function runSpiritFlixFaceOrganizerDryRun(
  videoPath: string,
  options: SpiritFlixFaceOrganizerDryRunOptions = {},
): Promise<SpiritFlixFaceOrganizerDryRunResult> {
  const command = options.command ?? defaultFaceOrganizerCommand();
  const args = buildSpiritFlixFaceOrganizerDryRunArgs(videoPath, options);
  const timeoutMs = options.timeoutMs ?? DEFAULT_FACE_ORGANIZER_TIMEOUT_MS;

  return new Promise((resolve) => {
    const proc = spawn(command, args, { cwd: options.cwd ?? process.cwd(), shell: false });
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    let settled = false;

    const finish = (code: number | null) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      proc.stdout.removeAllListeners("data");
      proc.stderr.removeAllListeners("data");
      proc.removeAllListeners("error");
      proc.removeAllListeners("close");
      const base = {
        schema: "spiritflix-face-organizer-dry-run/v1",
        ok: code === 0 && !timedOut,
        command,
        args,
        code,
        timedOut,
        stdout,
        stderr,
        safety: {
          dryRun: true,
          apply: false,
          mediaMutation: false,
        },
      } satisfies Omit<SpiritFlixFaceOrganizerDryRunResult, "match">;
      resolve({
        ...base,
        match: parseSpiritFlixFaceOrganizerMatch(base),
      });
    };

    const timer = setTimeout(() => {
      timedOut = true;
      proc.kill("SIGKILL");
      finish(null);
    }, timeoutMs);

    proc.stdout.on("data", (chunk: Buffer) => {
      stdout = appendCaptured(stdout, chunk);
    });
    proc.stderr.on("data", (chunk: Buffer) => {
      stderr = appendCaptured(stderr, chunk);
    });
    proc.on("error", (error) => {
      stderr = appendCaptured(stderr, Buffer.from(error.message));
      finish(null);
    });
    proc.on("close", (code) => finish(code));
  });
}
