import { spawn } from "node:child_process";
import crypto from "node:crypto";
import { closeSync, openSync } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";
import { appendSpiritFlixJobState, createSpiritFlixJobVideoId, listSpiritFlixJobs } from "@/lib/spiritflix/admin/jobs";
import { resolveSpiritFlixAdminPath } from "@/lib/spiritflix/admin/paths";
import { isSpiritFlixSmartVideoExtension } from "@/lib/spiritflix/admin/smart/probe";
import type { SpiritFlixJobRecord, SpiritFlixJobVideoIdentity } from "@/lib/spiritflix/admin/jobs";

export const runtime = "nodejs";

const ENQUEUE_SCHEMA = "spiritflix-library-smart-rescan-enqueue/v1";

const STATUS_PATH = path.join(process.cwd(), "scripts", "media", "spiritflix_library_smart_rescan_status.json");
const SUMMARY_PATH = path.join(process.cwd(), "scripts", "media", "spiritflix_library_smart_rescan_summary.json");
const LOG_PATH = path.join(process.cwd(), "scripts", "media", "spiritflix_library_smart_rescan.log");
const SCRIPT_PATH = path.join(process.cwd(), "scripts", "media", "face_organizer.py");
const DEFAULT_PYTHON_PATH = process.platform === "win32" ? "python" : "/home/source/SpiritOS/.venv-face-organizer/bin/python";
const PYTHON_PATH = process.env.SPIRITFLIX_FACE_ORGANIZER_PYTHON ||
  DEFAULT_PYTHON_PATH;
const SMART_RESCAN_MODEL_LIMIT = Math.max(1, Number.parseInt(process.env.SPIRITFLIX_SMART_RESCAN_MODEL_LIMIT ?? "80", 10) || 80);
const SMART_RESCAN_VIDEO_LIMIT = Math.max(1, Number.parseInt(process.env.SPIRITFLIX_SMART_RESCAN_VIDEO_LIMIT ?? "120", 10) || 120);
const FACE_ORGANIZER_CTX_ID = process.env.SPIRITFLIX_FACE_ORGANIZER_CTX_ID ?? "-1";
const FACE_ORGANIZER_NICE = Number.parseInt(process.env.SPIRITFLIX_FACE_ORGANIZER_NICE ?? "15", 10);
const FACE_ORGANIZER_CPUSET = process.env.SPIRITFLIX_FACE_ORGANIZER_CPUSET ?? (process.platform === "linux" ? "6,7" : "");
const FACE_ORGANIZER_THREADS = Math.max(1, Number.parseInt(process.env.SPIRITFLIX_FACE_ORGANIZER_THREADS ?? "2", 10) || 2);
const SMART_RESCAN_SOURCE = process.env.SPIRITFLIX_SMART_RESCAN_SOURCE ?? "/mnt/spirit-8tb/media/yes";
const SMART_RESCAN_ENQUEUE_LIMIT = Math.max(1, Number.parseInt(process.env.SPIRITFLIX_SMART_RESCAN_ENQUEUE_LIMIT ?? "120", 10) || 120);

interface SmartRescanStatus {
  schema: "spiritflix-library-smart-rescan-status/v1";
  status: "idle" | "running" | "completed" | "failed";
  startedAt?: string;
  updatedAt?: string;
  completedAt?: string;
  pid?: number;
  exitCode?: number | null;
  error?: string;
  phase?: string;
  phaseLabel?: string;
  progress?: {
    total?: number;
    completed?: number;
    percent?: number;
  };
  modelProgress?: {
    total?: number;
    completed?: number;
    accepted?: number;
    skipped?: number;
  };
  currentItem?: {
    kind?: string;
    name?: string;
    path?: string;
    preview?: string;
  };
  summaryPath?: string;
  logPath?: string;
  summary?: unknown;
}

interface SmartRescanPostBody {
  mode?: string;
  path?: string;
  videoPath?: string;
  sourcePath?: string;
  paths?: unknown[];
  videos?: unknown[];
  recursive?: boolean;
  maxItems?: number;
}

interface EnqueueTarget {
  videoPath: string;
  mediaRoot: string;
}

interface EnqueueResult {
  schema: typeof ENQUEUE_SCHEMA;
  state: "queued";
  status: "running";
  phase: "queued";
  phaseLabel: string;
  generatedAt: string;
  accepted: number;
  duplicateExisting: number;
  skipped: number;
  jobId?: string;
  jobIds: string[];
  jobs: SpiritFlixJobRecord[];
  duplicates: Array<{
    reasonCode: "active_job_exists";
    job: SpiritFlixJobRecord;
    referencedJobId: string;
    referencedEventCount: number;
  }>;
  skippedItems: Array<{
    path: string;
    reasonCode: "invalid_target" | "unsupported_media" | "not_found" | "not_file_or_directory" | "enqueue_failed";
    reason: string;
    source: "library-smart-rescan";
    timestamp: string;
    targetHash?: string;
  }>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function safeErrorMessage(error: unknown, fallback = "SpiritFlix smart rescan enqueue failed."): string {
  return error instanceof Error ? error.message.split(/\n\s+at\s+/)[0].slice(0, 500) : fallback;
}

function boundedEnqueueLimit(value: number | undefined): number {
  if (!Number.isFinite(value ?? NaN)) return SMART_RESCAN_ENQUEUE_LIMIT;
  return Math.max(1, Math.min(SMART_RESCAN_ENQUEUE_LIMIT, Math.floor(value ?? SMART_RESCAN_ENQUEUE_LIMIT)));
}

function hiddenPathPart(name: string): boolean {
  return name.startsWith(".");
}

function targetHash(value: string): string {
  return crypto.createHash("sha256").update(value.replace(/\\/g, "/")).digest("hex").slice(0, 24);
}

function skippedDiagnostic(pathValue: string, reasonCode: EnqueueResult["skippedItems"][number]["reasonCode"], reason: string): EnqueueResult["skippedItems"][number] {
  return {
    path: pathValue,
    reasonCode,
    reason,
    source: "library-smart-rescan",
    timestamp: new Date().toISOString(),
    targetHash: targetHash(pathValue),
  };
}

async function readJson<T>(target: string): Promise<T | null> {
  try {
    return JSON.parse(await fs.readFile(target, "utf8")) as T;
  } catch {
    return null;
  }
}

async function readLatestLogPreview(): Promise<string> {
  try {
    const log = await fs.readFile(LOG_PATH, "utf8");
    return log
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .slice(-1)[0] ?? "";
  } catch {
    return "";
  }
}

async function writeStatus(status: SmartRescanStatus): Promise<void> {
  await fs.mkdir(path.dirname(STATUS_PATH), { recursive: true });
  await fs.writeFile(STATUS_PATH, `${JSON.stringify(status, null, 2)}\n`, "utf8");
}

async function readStatus(): Promise<SmartRescanStatus> {
  const current = await readJson<SmartRescanStatus>(STATUS_PATH);
  if (!current) {
    return {
      schema: "spiritflix-library-smart-rescan-status/v1",
      status: "idle",
      summaryPath: SUMMARY_PATH,
      logPath: LOG_PATH,
    };
  }
  if (current.status === "running" && current.pid && !isProbablyRunning(current.pid)) {
    const summary = await readJson(SUMMARY_PATH);
    const recovered: SmartRescanStatus = {
      ...current,
      status: summary ? "completed" : "failed",
      completedAt: current.completedAt ?? new Date().toISOString(),
      exitCode: current.exitCode,
      progress: summary ? { ...(current.progress ?? {}), percent: 100 } : current.progress,
      summary: summary ?? undefined,
      error: summary ? undefined : "Smart rescan process is no longer running and no summary was found.",
    };
    await writeStatus(recovered);
    return recovered;
  }
  if (current.status === "completed") {
    return { ...current, summary: await readJson(SUMMARY_PATH) };
  }
  if (current.status === "running" && !current.currentItem) {
    const preview = await readLatestLogPreview();
    if (preview) {
      return {
        ...current,
        phase: current.phase ?? "running",
        phaseLabel: current.phaseLabel ?? "Smart scan running",
        currentItem: {
          kind: "log",
          name: preview,
          preview,
        },
      };
    }
  }
  return current;
}

function isProbablyRunning(pid?: number): boolean {
  if (!pid) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function buildFaceOrganizerLaunch(baseCommand: string, args: string[]) {
  let command = baseCommand;
  let spawnArgs = args;
  let display = [baseCommand, ...args];

  if (FACE_ORGANIZER_CPUSET && process.platform === "linux") {
    command = "taskset";
    spawnArgs = ["-c", FACE_ORGANIZER_CPUSET, baseCommand, ...spawnArgs];
    display = ["taskset", "-c", FACE_ORGANIZER_CPUSET, ...display];
  }

  if (Number.isFinite(FACE_ORGANIZER_NICE) && FACE_ORGANIZER_NICE !== 0 && process.platform !== "win32") {
    spawnArgs = ["-n", String(FACE_ORGANIZER_NICE), command, ...spawnArgs];
    display = ["nice", "-n", String(FACE_ORGANIZER_NICE), ...display];
    command = "nice";
  }

  return { command, spawnArgs, display };
}

async function startSmartRescan(): Promise<SmartRescanStatus> {
  const current = await readStatus();
  if (current.status === "running" && isProbablyRunning(current.pid)) return current;

  await fs.mkdir(path.dirname(LOG_PATH), { recursive: true });
  const startedAt = new Date().toISOString();
  const status: SmartRescanStatus = {
    schema: "spiritflix-library-smart-rescan-status/v1",
    status: "running",
    startedAt,
    summaryPath: SUMMARY_PATH,
    logPath: LOG_PATH,
  };
  await writeStatus(status);

  const launch = buildFaceOrganizerLaunch(
    PYTHON_PATH,
    [
      SCRIPT_PATH,
      "--spiritflix-library-smart-rescan",
      "--apply",
      "--ctx-id",
      FACE_ORGANIZER_CTX_ID,
      "--smart-rescan-model-limit",
      String(SMART_RESCAN_MODEL_LIMIT),
      "--smart-rescan-video-limit",
      String(SMART_RESCAN_VIDEO_LIMIT),
      "--source",
      "/mnt/spirit-8tb/media/yes",
      "--report-path",
      path.join(process.cwd(), "scripts", "media", "face_verification_report.html"),
    ],
  );
  await fs.appendFile(LOG_PATH, `\n[launcher] starting smart rescan at ${startedAt}\n[launcher] command ${launch.display.join(" ")}\n`, "utf8");
  const logFd = openSync(LOG_PATH, "a");
  const child = spawn(
    launch.command,
    launch.spawnArgs,
    {
      cwd: process.cwd(),
      detached: true,
      env: {
        ...process.env,
        OMP_NUM_THREADS: String(FACE_ORGANIZER_THREADS),
        OPENBLAS_NUM_THREADS: String(FACE_ORGANIZER_THREADS),
        MKL_NUM_THREADS: String(FACE_ORGANIZER_THREADS),
        NUMEXPR_NUM_THREADS: String(FACE_ORGANIZER_THREADS),
        SPIRITFLIX_SMART_RESCAN_STATUS_PATH: STATUS_PATH,
        SPIRITFLIX_SMART_RESCAN_NO_VIDEO_BACKUPS: "1",
      },
      stdio: ["ignore", logFd, logFd],
    },
  );
  closeSync(logFd);

  const running = {
    ...status,
    pid: child.pid,
    progress: { total: 4, completed: 0, percent: 0 },
    phase: "starting",
    phaseLabel: `Starting smart model rescan (${SMART_RESCAN_MODEL_LIMIT} models, ${SMART_RESCAN_VIDEO_LIMIT} videos max)`,
  };
  await writeStatus(running);
  child.on("error", async (error) => {
    await fs.appendFile(LOG_PATH, `\n[launcher-error] ${error.message}\n`, "utf8");
    await writeStatus({
      ...running,
      status: "failed",
      completedAt: new Date().toISOString(),
      error: error.message,
    });
  });
  child.unref();

  return running;
}

export async function GET() {
  const status = await readStatus();
  return NextResponse.json(status, { headers: { "Cache-Control": "no-store" } });
}

async function readPostBody(request: Request): Promise<SmartRescanPostBody> {
  const raw = await request.text();
  if (!raw.trim()) return {};
  const parsed = JSON.parse(raw) as unknown;
  if (!isRecord(parsed)) throw new Error("Smart rescan request body must be a JSON object.");
  return parsed as SmartRescanPostBody;
}

function isLegacyRunMode(body: SmartRescanPostBody, request: NextRequest): boolean {
  const searchParams = request.nextUrl?.searchParams ?? new URL(request.url).searchParams;
  const queryMode = searchParams.get("mode")?.toLowerCase();
  const bodyMode = body.mode?.toLowerCase();
  return queryMode === "run" || queryMode === "legacy" || bodyMode === "run" || bodyMode === "legacy";
}

function pathFromVideoEntry(value: unknown): string | null {
  if (typeof value === "string") return value;
  if (!isRecord(value)) return null;
  const candidate = value.path ?? value.videoPath ?? value.sourcePath;
  return typeof candidate === "string" ? candidate : null;
}

function requestedPaths(body: SmartRescanPostBody): string[] {
  const paths = [body.path, body.videoPath, body.sourcePath].filter((value): value is string => typeof value === "string" && value.trim().length > 0);
  for (const value of body.paths ?? []) {
    if (typeof value === "string" && value.trim()) paths.push(value);
  }
  for (const value of body.videos ?? []) {
    const candidate = pathFromVideoEntry(value);
    if (candidate?.trim()) paths.push(candidate);
  }
  return [...new Set(paths.map((entry) => entry.trim()))];
}

async function enumerateVideoTargets(folderPath: string, mediaRoot: string, maxItems: number, recursive: boolean): Promise<EnqueueTarget[]> {
  const found: EnqueueTarget[] = [];
  const pending = [folderPath];

  while (pending.length > 0 && found.length < maxItems) {
    const current = pending.shift()!;
    const entries = await fs.readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      if (hiddenPathPart(entry.name)) continue;
      const childPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        if (recursive) pending.push(childPath);
        continue;
      }
      if (!entry.isFile()) continue;
      if (!isSpiritFlixSmartVideoExtension(path.extname(entry.name).toLowerCase())) continue;
      found.push({ videoPath: childPath, mediaRoot });
      if (found.length >= maxItems) break;
    }
  }

  return found;
}

async function resolveEnqueueTargets(candidate: string, maxItems: number, recursive: boolean): Promise<{ targets: EnqueueTarget[]; skippedItems: EnqueueResult["skippedItems"] }> {
  try {
    const { allowedRoot, realPath } = await resolveSpiritFlixAdminPath(candidate);
    const stat = await fs.stat(realPath);
    if (stat.isFile()) {
      if (!isSpiritFlixSmartVideoExtension(path.extname(realPath).toLowerCase())) {
        return {
          targets: [],
          skippedItems: [skippedDiagnostic(candidate, "unsupported_media", "Smart rescan enqueue only accepts video files.")],
        };
      }
      return { targets: [{ videoPath: realPath, mediaRoot: allowedRoot }], skippedItems: [] };
    }
    if (stat.isDirectory()) {
      return { targets: await enumerateVideoTargets(realPath, allowedRoot, maxItems, recursive), skippedItems: [] };
    }
    return {
      targets: [],
      skippedItems: [skippedDiagnostic(candidate, "not_file_or_directory", "Smart rescan enqueue requires a video file or folder.")],
    };
  } catch (error) {
    const message = safeErrorMessage(error, "Smart rescan target is invalid.");
    return {
      targets: [],
      skippedItems: [skippedDiagnostic(candidate, /not found|ENOENT/i.test(message) ? "not_found" : "invalid_target", message)],
    };
  }
}

async function enqueueTarget(target: EnqueueTarget): Promise<
  | { kind: "queued"; job: SpiritFlixJobRecord }
  | { kind: "duplicate"; job: SpiritFlixJobRecord }
  | { kind: "skipped"; item: EnqueueResult["skippedItems"][number] }
> {
  try {
    const stat = await fs.stat(target.videoPath);
    const identity: SpiritFlixJobVideoIdentity = {
      videoPath: target.videoPath,
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
    };
    const videoId = createSpiritFlixJobVideoId(identity);
    const active = await listSpiritFlixJobs({ mediaRoot: target.mediaRoot, activeOnly: true, videoId });
    const existing = active.jobs.find((job) => job.videoId === videoId);
    if (existing) return { kind: "duplicate", job: existing };

    const event = await appendSpiritFlixJobState(
      {
        ...identity,
        state: "queued",
        worker: "library-smart-rescan",
        details: {
          source: "library-smart-rescan",
          reasonCode: "enqueue_requested",
          lifecycleEvent: "queued",
          lifecycleTimestamp: new Date().toISOString(),
          enqueueOnly: true,
          autoMove: false,
          autoDbEnrollment: false,
          workerConsumed: false,
          targetHash: targetHash(target.videoPath),
        },
      },
      { mediaRoot: target.mediaRoot },
    );
    return { kind: "queued", job: event };
  } catch (error) {
    return {
      kind: "skipped",
      item: skippedDiagnostic(target.videoPath, "enqueue_failed", safeErrorMessage(error)),
    };
  }
}

async function enqueueSmartRescanJobs(body: SmartRescanPostBody): Promise<EnqueueResult> {
  const maxItems = boundedEnqueueLimit(body.maxItems);
  const sourcePaths = requestedPaths(body);
  const roots = sourcePaths.length > 0 ? sourcePaths : [SMART_RESCAN_SOURCE];
  const recursive = Boolean(body.recursive);
  const targets: EnqueueTarget[] = [];
  const skippedItems: EnqueueResult["skippedItems"] = [];

  for (const candidate of roots) {
    const remaining = maxItems - targets.length;
    if (remaining <= 0) break;
    const resolved = await resolveEnqueueTargets(candidate, remaining, recursive);
    targets.push(...resolved.targets);
    skippedItems.push(...resolved.skippedItems);
  }

  const dedupedTargets = [...new Map(targets.map((target) => [target.videoPath, target])).values()].slice(0, maxItems);
  const jobs: SpiritFlixJobRecord[] = [];
  const duplicates: EnqueueResult["duplicates"] = [];

  for (const target of dedupedTargets) {
    const result = await enqueueTarget(target);
    if (result.kind === "queued") jobs.push(result.job);
    if (result.kind === "duplicate") duplicates.push({
      reasonCode: "active_job_exists",
      job: result.job,
      referencedJobId: result.job.jobId,
      referencedEventCount: result.job.eventCount,
    });
    if (result.kind === "skipped") skippedItems.push(result.item);
  }

  return {
    schema: ENQUEUE_SCHEMA,
    state: "queued",
    status: "running",
    phase: "queued",
    phaseLabel: `Queued ${jobs.length} SpiritFlix smart rescan job${jobs.length === 1 ? "" : "s"}.`,
    generatedAt: new Date().toISOString(),
    accepted: jobs.length,
    duplicateExisting: duplicates.length,
    skipped: skippedItems.length,
    jobId: jobs.length === 1 ? jobs[0]?.jobId : undefined,
    jobIds: jobs.map((job) => job.jobId),
    jobs,
    duplicates,
    skippedItems,
  };
}

export async function POST(request: NextRequest) {
  try {
    const body = await readPostBody(request);
    if (isLegacyRunMode(body, request)) {
      const status = await startSmartRescan();
      return NextResponse.json(status, { headers: { "Cache-Control": "no-store" } });
    }
    const result = await enqueueSmartRescanJobs(body);
    const ok = result.accepted > 0 || result.duplicateExisting > 0;
    return NextResponse.json(result, { status: ok ? 202 : 400, headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to start SpiritFlix smart rescan.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
