import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { SPIRITFLIX_MEDIA_ROOT } from "./admin/constants";
import { writeSpiritFlixAdminReceipt } from "./admin/receipts";
import type { FaceOrganizerPerformer, SpiritFlixFaceLearningRecord } from "@/lib/spiritflix-types";

export const SPIRITFLIX_FACE_LEARNING_SCHEMA = "spiritflix-face-learning-request/v1";
export const SPIRITFLIX_FACE_LEARNING_ROOT = path.join(SPIRITFLIX_MEDIA_ROOT, ".spiritflix-admin", "metadata", "face-learning");

const execFileAsync = promisify(execFile);
const FACE_ORGANIZER_SCRIPT_PATH = path.join(process.cwd(), "scripts", "media", "face_organizer.py");
const FACE_ORGANIZER_PYTHON = process.env.SPIRITFLIX_FACE_ORGANIZER_PYTHON ??
  (process.platform === "win32" ? "python" : "/home/source/SpiritOS/.venv-face-organizer/bin/python");
const FACE_ORGANIZER_TIMEOUT_MS = Math.max(10_000, Number.parseInt(process.env.SPIRITFLIX_FACE_LEARNING_TIMEOUT_MS ?? "120000", 10) || 120_000);

interface FaceLearningStoreOptions {
  rootDir?: string;
}

export interface RequestSpiritFlixFaceLearningInput {
  itemId: string;
  filePath?: string;
  modelName: string;
  sidecarPath?: string;
  faceGuess?: FaceOrganizerPerformer;
  relatedItems?: Array<{ itemId?: string; filePath?: string }>;
}

interface FaceSidecarWithCorrections {
  video_path?: string;
  assignment_decision?: { suggested_name?: string };
  performers?: Array<{ name?: unknown; face_crop_path?: unknown; original_frame_path?: unknown }>;
  manual_corrections?: unknown[];
  manual_correction_pending?: unknown;
}

interface FaceOrganizerCommandResult {
  ok: boolean;
  stdout?: string;
  stderr?: string;
  error?: string;
}

function getFaceLearningRoot(options: FaceLearningStoreOptions = {}): string {
  return options.rootDir ?? process.env.SPIRITFLIX_FACE_LEARNING_ROOT ?? SPIRITFLIX_FACE_LEARNING_ROOT;
}

function canonicalizeModelName(input: unknown): string {
  if (typeof input !== "string") return "";
  return input.trim().replace(/\s+/g, " ");
}

function assertItemId(input: string): string {
  const itemId = input.trim();
  if (!itemId) throw new Error("Face learning item id is required.");
  return itemId;
}

function requestPath(itemId: string, options: FaceLearningStoreOptions = {}): string {
  const hash = createHash("sha256").update(assertItemId(itemId)).digest("hex");
  return path.join(getFaceLearningRoot(options), "items", `${hash}.json`);
}

function indexPath(options: FaceLearningStoreOptions = {}): string {
  return path.join(getFaceLearningRoot(options), "index.json");
}

function isAllowedSidecarPath(sidecarPath?: string): boolean {
  if (!sidecarPath) return false;
  const normalized = path.normalize(sidecarPath).replaceAll("\\", "/");
  const mediaRoot = path.normalize(SPIRITFLIX_MEDIA_ROOT).replaceAll("\\", "/").replace(/\/$/, "");
  return normalized.startsWith(`${mediaRoot}/`) && normalized.endsWith(".face-meta.json");
}

async function readJsonFile<T>(filePath: string): Promise<T | null> {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8")) as T;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw error;
  }
}

async function writeJsonFile(filePath: string, value: unknown): Promise<void> {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function manualCorrectionFor(record: SpiritFlixFaceLearningRecord) {
  return {
    schema: "media-manual-correction/v1",
    status: "pending",
    corrected_by: "SpiritFlix player",
    corrected_at: record.requestedAt,
    source_file: record.filePath,
    sidecar_path: record.sidecarPath,
    previous_suggestion: record.faceGuess?.name,
    new_canonical_name: record.modelName,
    evidence_role: "user_confirmed_correction",
    belongs_to_existing: Boolean(record.faceGuess?.name && record.faceGuess.name.toLowerCase() === record.modelName.toLowerCase()),
    face_enrollment_performed: false,
    limitations: "Pending evidence only. Registry/model index and face embeddings are unchanged until face organizer confirmation/enrollment runs.",
  };
}

async function writePendingCorrection(record: SpiritFlixFaceLearningRecord): Promise<boolean> {
  if (!isAllowedSidecarPath(record.sidecarPath)) return false;
  const sidecar = await readJsonFile<FaceSidecarWithCorrections>(record.sidecarPath ?? "");
  if (!sidecar || typeof sidecar !== "object") return false;
  const correction = manualCorrectionFor(record);
  sidecar.manual_corrections = Array.isArray(sidecar.manual_corrections) ? sidecar.manual_corrections : [];
  sidecar.manual_corrections.push(correction);
  sidecar.manual_correction_pending = correction;
  await writeJsonFile(record.sidecarPath ?? "", sidecar);
  return true;
}

function enrollmentCandidatesFromSidecar(sidecar: FaceSidecarWithCorrections | null, faceGuess?: FaceOrganizerPerformer): string[] {
  const performers = Array.isArray(sidecar?.performers) ? sidecar.performers : [];
  const guessName = canonicalizeModelName(faceGuess?.name).toLowerCase();
  const byGuess = guessName
    ? performers.find((performer) => canonicalizeModelName(performer.name).toLowerCase() === guessName)
    : undefined;
  const ordered = [byGuess, ...performers].filter((performer): performer is NonNullable<typeof performer> => Boolean(performer));
  const candidates: string[] = [];
  ordered.forEach((performer) => {
    [performer.face_crop_path, performer.original_frame_path].forEach((value) => {
      if (typeof value === "string" && value && !candidates.includes(value)) candidates.push(value);
    });
  });
  return candidates;
}

async function runFaceOrganizer(args: string[]): Promise<FaceOrganizerCommandResult> {
  try {
    const { stdout, stderr } = await execFileAsync(FACE_ORGANIZER_PYTHON, [FACE_ORGANIZER_SCRIPT_PATH, ...args], {
      cwd: process.cwd(),
      timeout: FACE_ORGANIZER_TIMEOUT_MS,
      maxBuffer: 1024 * 1024 * 8,
      env: {
        ...process.env,
        OMP_NUM_THREADS: process.env.OMP_NUM_THREADS ?? "2",
        OPENBLAS_NUM_THREADS: process.env.OPENBLAS_NUM_THREADS ?? "2",
        MKL_NUM_THREADS: process.env.MKL_NUM_THREADS ?? "2",
        NUMEXPR_NUM_THREADS: process.env.NUMEXPR_NUM_THREADS ?? "2",
      },
      windowsHide: true,
    });
    return { ok: true, stdout, stderr };
  } catch (error) {
    const err = error as NodeJS.ErrnoException & { stdout?: string; stderr?: string };
    return {
      ok: false,
      stdout: err.stdout,
      stderr: err.stderr,
      error: err.message,
    };
  }
}

function parseOrganizerJson(stdout?: string): { no_enrollment_performed?: unknown; status?: unknown; embedding_row_indexes_added?: unknown } | null {
  if (!stdout) return null;
  const start = stdout.indexOf("{");
  const end = stdout.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  try {
    return JSON.parse(stdout.slice(start, end + 1)) as { no_enrollment_performed?: unknown; status?: unknown; embedding_row_indexes_added?: unknown };
  } catch {
    return null;
  }
}

function enrollmentSucceeded(result: FaceOrganizerCommandResult): boolean {
  const payload = parseOrganizerJson(result.stdout);
  if (!payload) return result.ok;
  if (payload.no_enrollment_performed) return false;
  if (payload.status === "SKIPPED_WEAK_CROPS") return false;
  return Array.isArray(payload.embedding_row_indexes_added) ? payload.embedding_row_indexes_added.length > 0 : result.ok;
}

async function confirmAndEnrollFace(record: SpiritFlixFaceLearningRecord): Promise<void> {
  if (!isAllowedSidecarPath(record.sidecarPath)) return;
  const sidecar = await readJsonFile<FaceSidecarWithCorrections>(record.sidecarPath ?? "");
  const candidates = enrollmentCandidatesFromSidecar(sidecar, record.faceGuess);
  if (!candidates.length) {
    record.actions.faceEnrollmentError = "No sidecar face crop was available to enroll.";
    return;
  }

  record.actions.faceEnrollmentAttempted = true;
  let lastEnroll: FaceOrganizerCommandResult | null = null;
  for (const candidate of candidates) {
    record.actions.enrolledCropPath = candidate;
    const enroll = await runFaceOrganizer([
      "--enroll-crop",
      record.modelName,
      "--face-image",
      candidate,
      "--confirmed-by",
      "SpiritFlix player",
      "--source",
      path.join(SPIRITFLIX_MEDIA_ROOT, "yes"),
      "--report-path",
      path.join(process.cwd(), "scripts", "media", "face_verification_report.html"),
      "--apply",
    ]);
    lastEnroll = enroll;
    if (enroll.ok && enrollmentSucceeded(enroll)) {
      record.actions.faceEnrollmentPerformed = true;
      break;
    }
  }

  if (!record.actions.faceEnrollmentPerformed) {
    record.actions.faceEnrollmentPerformed = false;
    const payload = parseOrganizerJson(lastEnroll?.stdout);
    record.actions.faceEnrollmentError = typeof payload?.status === "string"
      ? payload.status
      : lastEnroll?.error ?? lastEnroll?.stderr ?? "No sidecar face crop met enrollment quality.";
    return;
  }
  const confirm = await runFaceOrganizer([
    "--confirm-correction",
    "--sidecar",
    record.sidecarPath ?? "",
    "--confirmed-by",
    "SpiritFlix player",
    "--source",
    path.join(SPIRITFLIX_MEDIA_ROOT, "yes"),
    "--report-path",
    path.join(process.cwd(), "scripts", "media", "face_verification_report.html"),
    "--apply",
  ]);
  record.actions.organizerCorrectionConfirmed = confirm.ok;
  if (!confirm.ok) {
    record.actions.faceEnrollmentError = confirm.error ?? confirm.stderr ?? "Face correction confirmation failed.";
  }
}

async function writeIndex(record: SpiritFlixFaceLearningRecord, options: FaceLearningStoreOptions): Promise<void> {
  const current = await readJsonFile<{ schema: string; updatedAt: string; requests: SpiritFlixFaceLearningRecord[] }>(indexPath(options));
  const requests = (current?.requests ?? []).filter((item) => item.itemId !== record.itemId);
  requests.unshift(record);
  await writeJsonFile(indexPath(options), {
    schema: "spiritflix-face-learning-index/v1",
    updatedAt: new Date().toISOString(),
    requests: requests.slice(0, 500),
  });
}

export async function requestSpiritFlixFaceLearning(
  input: RequestSpiritFlixFaceLearningInput,
  options: FaceLearningStoreOptions = {},
): Promise<SpiritFlixFaceLearningRecord> {
  const itemId = assertItemId(input.itemId);
  const modelName = canonicalizeModelName(input.modelName);
  if (!modelName) throw new Error("Face learning model name is required.");
  const relatedItems = (input.relatedItems ?? [])
    .filter((item): item is { itemId: string; filePath?: string } => Boolean(item.itemId?.trim()))
    .map((item) => ({ itemId: item.itemId.trim(), filePath: item.filePath }));
  const requestedAt = new Date().toISOString();
  const record: SpiritFlixFaceLearningRecord = {
    schema: SPIRITFLIX_FACE_LEARNING_SCHEMA,
    itemId,
    filePath: input.filePath,
    modelName,
    sidecarPath: input.sidecarPath,
    faceGuess: input.faceGuess,
    relatedItems,
    requestedAt,
    status: "queued",
    actions: {
      pendingCorrectionWritten: false,
      scanCurrentVideoRequested: Boolean(input.filePath && !input.sidecarPath),
      scanLibraryMatchesRequested: relatedItems.length > 0,
    },
    source: "player-model-widget",
  };
  record.actions.pendingCorrectionWritten = await writePendingCorrection(record);
  if (record.actions.pendingCorrectionWritten && !options.rootDir && !process.env.SPIRITFLIX_FACE_LEARNING_ROOT) {
    await confirmAndEnrollFace(record);
  }
  await writeJsonFile(requestPath(itemId, options), record);
  await writeIndex(record, options);

  if (!options.rootDir && !process.env.SPIRITFLIX_FACE_LEARNING_ROOT) {
    try {
      await writeSpiritFlixAdminReceipt({
        action: "face-learning:request",
        status: "executed",
        sourcePath: record.filePath,
        jellyfinItemIds: [itemId, ...relatedItems.map((item) => item.itemId)],
        affectedPaths: [requestPath(itemId, options), indexPath(options), ...(record.sidecarPath ? [record.sidecarPath] : [])],
        reason: JSON.stringify({
          itemId,
          modelName,
          sidecarPath: record.sidecarPath,
          pendingCorrectionWritten: record.actions.pendingCorrectionWritten,
          scanLibraryMatchesRequested: record.actions.scanLibraryMatchesRequested,
        }),
        reversible: true,
        rollbackHint: "Remove the face-learning request and pending correction from the sidecar if needed.",
      });
    } catch {
      // The queue is the durable handoff; receipt logging should not block a player save.
    }
  }

  return record;
}
