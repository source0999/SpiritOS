import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { SPIRITFLIX_MEDIA_ROOT } from "../constants";
import {
  createSmartAnalysisPathKey,
  assertSmartVideoPathCandidate,
  type SpiritFlixSmartPathOptions,
} from "../smart/analysis-paths";
import {
  SPIRITFLIX_JOB_SCHEMA,
  SPIRITFLIX_JOB_STATES,
  type AppendSpiritFlixJobStateInput,
  type FailSpiritFlixJobInput,
  type RequeueSpiritFlixJobInput,
  type SpiritFlixJobControlResult,
  type SpiritFlixJobEvent,
  type SpiritFlixJobHistoryResponse,
  type SpiritFlixJobListOptions,
  type SpiritFlixJobListResponse,
  type SpiritFlixJobRecord,
  type SpiritFlixJobState,
  type SpiritFlixJobStoreOptions,
  type SpiritFlixJobVideoIdentity,
} from "./types";

const SPIRITFLIX_JOBS_DIR = "jobs";
const SPIRITFLIX_JOBS_FILE = "events.jsonl";
const ACTIVE_STATES = new Set<SpiritFlixJobState>(["discovered", "queued", "scanning", "matching", "converting", "moving"]);

const ALLOWED_TRANSITIONS: Record<SpiritFlixJobState, SpiritFlixJobState[]> = {
  discovered: ["queued", "failed"],
  queued: ["scanning", "failed"],
  scanning: ["matching", "converting", "failed"],
  matching: ["converting", "moving", "ready", "needs_review", "failed"],
  converting: ["moving", "ready", "needs_review", "failed"],
  moving: ["ready", "needs_review", "failed"],
  ready: ["queued"],
  needs_review: ["queued", "failed"],
  failed: ["queued"],
};

function resolveMediaRoot(options?: SpiritFlixJobStoreOptions): string {
  return path.resolve(options?.mediaRoot ?? SPIRITFLIX_MEDIA_ROOT);
}

export function getSpiritFlixJobStoreRoot(options?: SpiritFlixJobStoreOptions): string {
  return path.resolve(options?.jobRoot ?? path.join(resolveMediaRoot(options), ".spiritflix-admin", SPIRITFLIX_JOBS_DIR));
}

export function getSpiritFlixJobEventsPath(options?: SpiritFlixJobStoreOptions): string {
  return path.join(getSpiritFlixJobStoreRoot(options), SPIRITFLIX_JOBS_FILE);
}

export function isActiveSpiritFlixJobState(state: SpiritFlixJobState): boolean {
  return ACTIVE_STATES.has(state);
}

export function createSpiritFlixJobVideoId(input: SpiritFlixJobVideoIdentity): string {
  return `video:${createSmartAnalysisPathKey(input)}`;
}

export function createSpiritFlixJobId(input: SpiritFlixJobVideoIdentity): string {
  return `sf-job-${createSmartAnalysisPathKey(input).slice(0, 24)}`;
}

function assertJobState(state: string): asserts state is SpiritFlixJobState {
  if (!SPIRITFLIX_JOB_STATES.includes(state as SpiritFlixJobState)) {
    throw new Error(`Unknown SpiritFlix job state: ${state}`);
  }
}

function assertTransition(previous: SpiritFlixJobState | undefined, next: SpiritFlixJobState): void {
  if (!previous) {
    if (next === "discovered" || next === "queued") return;
    throw new Error(`SpiritFlix job cannot start in ${next} state.`);
  }
  if (previous === next) return;
  if (!ALLOWED_TRANSITIONS[previous].includes(next)) {
    throw new Error(`Invalid SpiritFlix job transition: ${previous} -> ${next}.`);
  }
}

function assertJsonObject(value: unknown): asserts value is Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("SpiritFlix job event must be an object.");
  }
}

function parseJobEvent(line: string, lineNumber: number): SpiritFlixJobEvent {
  const parsed = JSON.parse(line) as unknown;
  assertJsonObject(parsed);

  const state = String(parsed.state ?? "");
  assertJobState(state);

  if (parsed.schema !== SPIRITFLIX_JOB_SCHEMA) {
    throw new Error(`SpiritFlix job event ${lineNumber} has an unsupported schema.`);
  }
  if (typeof parsed.jobId !== "string" || !parsed.jobId.trim()) throw new Error(`SpiritFlix job event ${lineNumber} is missing jobId.`);
  if (typeof parsed.videoId !== "string" || !parsed.videoId.trim()) throw new Error(`SpiritFlix job event ${lineNumber} is missing videoId.`);
  if (typeof parsed.videoPath !== "string" || !parsed.videoPath.trim()) throw new Error(`SpiritFlix job event ${lineNumber} is missing videoPath.`);
  if (typeof parsed.fileName !== "string" || !parsed.fileName.trim()) throw new Error(`SpiritFlix job event ${lineNumber} is missing fileName.`);
  if (typeof parsed.fileSizeBytes !== "number") throw new Error(`SpiritFlix job event ${lineNumber} is missing fileSizeBytes.`);
  if (typeof parsed.mtimeMs !== "number") throw new Error(`SpiritFlix job event ${lineNumber} is missing mtimeMs.`);
  if (typeof parsed.attempt !== "number") throw new Error(`SpiritFlix job event ${lineNumber} is missing attempt.`);
  if (typeof parsed.eventId !== "string" || !parsed.eventId.trim()) throw new Error(`SpiritFlix job event ${lineNumber} is missing eventId.`);
  if (typeof parsed.createdAt !== "string" || typeof parsed.updatedAt !== "string") {
    throw new Error(`SpiritFlix job event ${lineNumber} is missing timestamps.`);
  }
  let previousState: SpiritFlixJobState | undefined;
  if (typeof parsed.previousState === "string") {
    assertJobState(parsed.previousState);
    previousState = parsed.previousState;
  }
  if (parsed.details !== undefined && (typeof parsed.details !== "object" || parsed.details === null || Array.isArray(parsed.details))) {
    throw new Error(`SpiritFlix job event ${lineNumber} details must be an object.`);
  }

  return {
    schema: SPIRITFLIX_JOB_SCHEMA,
    eventId: parsed.eventId,
    jobId: parsed.jobId,
    videoId: parsed.videoId,
    videoPath: parsed.videoPath,
    fileName: parsed.fileName,
    fileSizeBytes: parsed.fileSizeBytes,
    mtimeMs: parsed.mtimeMs,
    state,
    previousState,
    attempt: parsed.attempt,
    createdAt: parsed.createdAt,
    updatedAt: parsed.updatedAt,
    errorReason: typeof parsed.errorReason === "string" ? parsed.errorReason : undefined,
    errorReasonCode: typeof parsed.errorReasonCode === "string" ? parsed.errorReasonCode : undefined,
    worker: typeof parsed.worker === "string" ? parsed.worker : undefined,
    details: parsed.details as Record<string, unknown> | undefined,
    eventCount: typeof parsed.eventCount === "number" ? parsed.eventCount : 1,
    lastEventId: typeof parsed.lastEventId === "string" ? parsed.lastEventId : parsed.eventId,
  };
}

export async function readSpiritFlixJobEvents(options?: SpiritFlixJobStoreOptions): Promise<SpiritFlixJobEvent[]> {
  try {
    const raw = await fs.readFile(getSpiritFlixJobEventsPath(options), "utf8");
    return raw
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line, index) => parseJobEvent(line, index + 1));
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw error;
  }
}

function latestRecordsFromEvents(events: SpiritFlixJobEvent[]): SpiritFlixJobRecord[] {
  const byJobId = new Map<string, SpiritFlixJobRecord>();
  const eventCounts = new Map<string, number>();
  for (const event of events) {
    const eventCount = (eventCounts.get(event.jobId) ?? 0) + 1;
    eventCounts.set(event.jobId, eventCount);
    byJobId.set(event.jobId, {
      schema: event.schema,
      jobId: event.jobId,
      videoId: event.videoId,
      videoPath: event.videoPath,
      fileName: event.fileName,
      fileSizeBytes: event.fileSizeBytes,
      mtimeMs: event.mtimeMs,
      state: event.state,
      attempt: event.attempt,
      createdAt: event.createdAt,
      updatedAt: event.updatedAt,
      errorReason: event.errorReason,
      errorReasonCode: event.errorReasonCode,
      worker: event.worker,
      details: event.details,
      eventCount,
      lastEventId: event.eventId,
    });
  }
  return [...byJobId.values()].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

export async function listSpiritFlixJobs(options?: SpiritFlixJobListOptions): Promise<SpiritFlixJobListResponse> {
  const events = await readSpiritFlixJobEvents(options);
  let jobs = latestRecordsFromEvents(events);

  if (options?.videoId) jobs = jobs.filter((job) => job.videoId === options.videoId);
  if (options?.activeOnly) jobs = jobs.filter((job) => isActiveSpiritFlixJobState(job.state));

  return {
    schema: "spiritflix-admin-jobs/v1",
    generatedAt: new Date().toISOString(),
    jobs,
    totalRecordCount: jobs.length,
    totalEventCount: events.length,
    query: {
      activeOnly: Boolean(options?.activeOnly),
      videoId: options?.videoId ?? "",
    },
  };
}

function normalizeJobInput(input: AppendSpiritFlixJobStateInput, options?: SpiritFlixJobStoreOptions) {
  assertJobState(input.state);
  if (input.state === "failed" && !input.errorReason?.trim()) {
    throw new Error("Failed SpiritFlix jobs must include an error reason.");
  }

  const smartOptions: SpiritFlixSmartPathOptions = { mediaRoot: options?.mediaRoot };
  const videoPath = assertSmartVideoPathCandidate(input.videoPath, smartOptions);
  const identity = {
    videoPath,
    fileSizeBytes: input.fileSizeBytes,
    mtimeMs: input.mtimeMs,
  };
  const videoId = createSpiritFlixJobVideoId(identity);
  const jobId = input.jobId ?? createSpiritFlixJobId(identity);

  return {
    ...input,
    ...identity,
    videoId,
    jobId,
    fileName: input.fileName?.trim() || path.basename(videoPath),
  };
}


function jobControlDetails(action: "fail" | "requeue", previous: SpiritFlixJobRecord): Record<string, unknown> {
  return {
    source: "admin-job-control",
    action,
    previousState: previous.state,
    enqueueOnly: true,
    autoMove: false,
    autoDbEnrollment: false,
    workerConsumed: false,
  };
}

async function latestJobById(jobId: string, options?: SpiritFlixJobStoreOptions): Promise<SpiritFlixJobRecord> {
  if (!jobId.trim()) throw new Error("jobId is required.");
  const history = await getSpiritFlixJobHistory(jobId, options);
  if (!history.job) throw new Error(`SpiritFlix job ${jobId} was not found.`);
  return history.job;
}

export async function getSpiritFlixJobHistory(jobId: string, options?: SpiritFlixJobStoreOptions): Promise<SpiritFlixJobHistoryResponse> {
  if (!jobId.trim()) throw new Error("jobId is required.");
  const events = (await readSpiritFlixJobEvents(options)).filter((event) => event.jobId === jobId);
  const [job = null] = latestRecordsFromEvents(events);
  return {
    schema: "spiritflix-admin-job-history/v1",
    generatedAt: new Date().toISOString(),
    jobId,
    job,
    events,
    totalEventCount: events.length,
  };
}

export async function failSpiritFlixJob(
  input: FailSpiritFlixJobInput,
  options?: SpiritFlixJobStoreOptions,
): Promise<SpiritFlixJobControlResult> {
  if (!input.reasonCode.trim()) throw new Error("reasonCode is required.");
  if (!input.reason.trim()) throw new Error("reason is required.");
  const previous = await latestJobById(input.jobId, options);
  const event = await appendSpiritFlixJobState(
    {
      videoPath: previous.videoPath,
      fileSizeBytes: previous.fileSizeBytes,
      mtimeMs: previous.mtimeMs,
      jobId: previous.jobId,
      fileName: previous.fileName,
      state: "failed",
      errorReasonCode: input.reasonCode,
      errorReason: input.reason,
      worker: input.worker?.trim() || "admin-job-control",
      details: jobControlDetails("fail", previous),
    },
    options,
  );
  return { schema: "spiritflix-admin-job-control/v1", action: "fail", job: event, event };
}

export async function requeueSpiritFlixJob(
  input: RequeueSpiritFlixJobInput,
  options?: SpiritFlixJobStoreOptions,
): Promise<SpiritFlixJobControlResult> {
  const previous = await latestJobById(input.jobId, options);
  if (isActiveSpiritFlixJobState(previous.state)) {
    throw new Error(`Active SpiritFlix job ${previous.jobId} cannot be requeued from ${previous.state}.`);
  }
  const event = await appendSpiritFlixJobState(
    {
      videoPath: previous.videoPath,
      fileSizeBytes: previous.fileSizeBytes,
      mtimeMs: previous.mtimeMs,
      jobId: previous.jobId,
      fileName: previous.fileName,
      state: "queued",
      worker: input.worker?.trim() || "admin-job-control",
      details: jobControlDetails("requeue", previous),
    },
    options,
  );
  return { schema: "spiritflix-admin-job-control/v1", action: "requeue", job: event, event };
}

export async function appendSpiritFlixJobState(
  input: AppendSpiritFlixJobStateInput,
  options?: SpiritFlixJobStoreOptions,
): Promise<SpiritFlixJobEvent> {
  const normalized = normalizeJobInput(input, options);
  const existing = latestRecordsFromEvents(await readSpiritFlixJobEvents(options));
  const previous = existing.find((job) => job.jobId === normalized.jobId);
  const activeConflict = existing.find(
    (job) =>
      job.videoId === normalized.videoId &&
      job.jobId !== normalized.jobId &&
      isActiveSpiritFlixJobState(job.state) &&
      isActiveSpiritFlixJobState(normalized.state),
  );

  if (activeConflict) {
    throw new Error(`Video already has active SpiritFlix job ${activeConflict.jobId}.`);
  }

  assertTransition(previous?.state, normalized.state);

  const now = (options?.now?.() ?? new Date()).toISOString();
  const retrying = previous && (previous.state === "failed" || previous.state === "needs_review" || previous.state === "ready") && normalized.state === "queued";
  const eventId = `sf-job-event-${now}-${crypto.randomUUID().slice(0, 8)}`;
  const event: SpiritFlixJobEvent = {
    schema: SPIRITFLIX_JOB_SCHEMA,
    eventId,
    jobId: normalized.jobId,
    videoId: normalized.videoId,
    videoPath: normalized.videoPath,
    fileName: normalized.fileName,
    fileSizeBytes: normalized.fileSizeBytes,
    mtimeMs: normalized.mtimeMs,
    state: normalized.state,
    previousState: previous?.state,
    attempt: previous ? previous.attempt + (retrying ? 1 : 0) : 1,
    createdAt: previous?.createdAt ?? now,
    updatedAt: now,
    errorReason: normalized.state === "failed" ? normalized.errorReason : undefined,
    errorReasonCode: normalized.state === "failed" ? normalized.errorReasonCode?.trim() || "unknown_failure" : undefined,
    worker: normalized.worker,
    details: normalized.details,
    eventCount: previous ? previous.eventCount + 1 : 1,
    lastEventId: eventId,
  };

  await fs.mkdir(getSpiritFlixJobStoreRoot(options), { recursive: true });
  await fs.appendFile(getSpiritFlixJobEventsPath(options), `${JSON.stringify(event)}\n`, "utf8");
  return event;
}
