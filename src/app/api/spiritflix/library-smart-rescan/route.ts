import { spawn } from "node:child_process";
import { closeSync, openSync } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

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

export async function POST() {
  try {
    const status = await startSmartRescan();
    return NextResponse.json(status, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to start SpiritFlix smart rescan.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
