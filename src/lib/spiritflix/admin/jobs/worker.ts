import crypto from "node:crypto";
import fs from "node:fs/promises";
import { scanOneSpiritFlixVideoEvidence } from "../smart/scanner";
import { runSpiritFlixFaceOrganizerDryRun } from "./face-organizer-bridge";
import { runSpiritFlixConversionBridge } from "./conversion-bridge";
import { createSpiritFlixPendingEnrollmentRecord, runSpiritFlixEnrollmentBridge } from "./enrollment-bridge";
import { createSpiritFlixOrganizeReceipt } from "./organize-bridge";
import { appendSpiritFlixDeadLetter, appendSpiritFlixJobState, getSpiritFlixJobHistory, isActiveSpiritFlixJobState, listSpiritFlixJobs } from "./store";
import type {
  SpiritFlixJobClaimResult,
  SpiritFlixJobRecord,
  SpiritFlixJobState,
  SpiritFlixJobStoreOptions,
  SpiritFlixJobWorkerFinalState,
  SpiritFlixJobWorkerMode,
  SpiritFlixJobWorkerPlaceholderState,
  SpiritFlixJobWorkerRunOptions,
  SpiritFlixJobWorkerRunResult,
} from "./types";
import type { SpiritFlixSmartAnalysis } from "../smart/types";
import type { SpiritFlixFaceOrganizerDryRunResult } from "./face-organizer-bridge";
import type { SpiritFlixConversionReceipt } from "./conversion-bridge";
import type { SpiritFlixOrganizeReceipt } from "./organize-bridge";
import type { SpiritFlixPendingEnrollmentRecord } from "./enrollment-bridge";

const DEFAULT_WORKER_ID = "spiritflix-safe-worker";
const DEFAULT_MODE: SpiritFlixJobWorkerMode = "no_media_mutation";
const HIGH_CONFIDENCE_THRESHOLD = 0.86;
const DEFAULT_MAX_ATTEMPTS = 3;
const SAFE_MOBILE_CODECS = new Set(["h264", "avc1"]);
const SAFE_MOBILE_CONTAINERS = ["mp4", "mov", "m4v", "quicktime"];

type ConversionDecision = {
  placeholderState: SpiritFlixJobWorkerPlaceholderState;
  decision: "skip" | "queue_later" | "review_only";
  reasonCode: "already_mobile_friendly" | "worker_conversion_required" | "missing_probe_metadata";
  reason: string;
};

function claimId(): string {
  return `sf-job-claim-${new Date().toISOString()}-${crypto.randomUUID().slice(0, 8)}`;
}

function controlDetails(
  phase: string,
  mode: SpiritFlixJobWorkerMode,
  extra: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    source: "spiritflix-job-worker",
    phase,
    mode,
    enqueueOnly: true,
    autoMove: false,
    autoDbEnrollment: false,
    mediaMutation: false,
    scanStarted: false,
    scanCompleted: false,
    conversionStarted: false,
    ...extra,
  };
}

function oldestQueued(jobs: SpiritFlixJobRecord[]): SpiritFlixJobRecord | undefined {
  return jobs
    .filter((job) => job.state === "queued")
    .sort((left, right) => left.createdAt.localeCompare(right.createdAt) || left.updatedAt.localeCompare(right.updatedAt))[0];
}

async function queuedCandidate(jobId: string | undefined, options?: SpiritFlixJobStoreOptions): Promise<SpiritFlixJobRecord | null> {
  if (jobId) {
    const history = await getSpiritFlixJobHistory(jobId, options);
    return history.job;
  }
  const active = await listSpiritFlixJobs({ ...options, activeOnly: true });
  return oldestQueued(active.jobs) ?? null;
}

export async function claimNextSpiritFlixQueuedJob(
  options: SpiritFlixJobStoreOptions & { jobId?: string; workerId?: string; mode?: SpiritFlixJobWorkerMode } = {},
): Promise<SpiritFlixJobClaimResult> {
  const workerId = options.workerId?.trim() || DEFAULT_WORKER_ID;
  const mode = options.mode ?? DEFAULT_MODE;
  const candidate = await queuedCandidate(options.jobId, options);
  if (!candidate) {
    return { schema: "spiritflix-admin-job-claim/v1", claimed: false, reasonCode: options.jobId ? "job_not_found" : "no_queued_jobs", workerId };
  }
  if (candidate.state !== "queued") {
    return { schema: "spiritflix-admin-job-claim/v1", claimed: false, reasonCode: "job_not_queued", workerId, job: candidate };
  }

  const id = claimId();
  const event = await appendSpiritFlixJobState(
    {
      videoPath: candidate.videoPath,
      fileSizeBytes: candidate.fileSizeBytes,
      mtimeMs: candidate.mtimeMs,
      jobId: candidate.jobId,
      fileName: candidate.fileName,
      state: "scanning",
      worker: workerId,
      details: controlDetails("claim", mode, { claimId: id, locked: true, workerConsumed: true, scanStarted: true }),
    },
    options,
  );
  return { schema: "spiritflix-admin-job-claim/v1", claimed: true, workerId, claimId: id, job: event, event };
}

async function sourceExists(job: SpiritFlixJobRecord): Promise<boolean> {
  try {
    const stat = await fs.stat(job.videoPath);
    return stat.isFile();
  } catch {
    return false;
  }
}

function normalize(value: string | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

function decideConversionBridge(analysis: SpiritFlixSmartAnalysis): ConversionDecision {
  const codec = normalize(analysis.media.codec);
  const container = normalize(analysis.media.container);
  if (!codec && !container) {
    return {
      placeholderState: "matching",
      decision: "review_only",
      reasonCode: "missing_probe_metadata",
      reason: "Probe metadata did not identify codec/container, so the worker leaves the item in review without conversion.",
    };
  }
  if (SAFE_MOBILE_CODECS.has(codec) && SAFE_MOBILE_CONTAINERS.some((candidate) => container.includes(candidate))) {
    return {
      placeholderState: "matching",
      decision: "skip",
      reasonCode: "already_mobile_friendly",
      reason: "Probe metadata is already compatible with the no-media-mutation mobile playback target.",
    };
  }
  return {
    placeholderState: "converting",
    decision: "queue_later",
    reasonCode: "worker_conversion_required",
    reason: "Probe metadata suggests a conversion is needed; the worker will create a conversion receipt and optionally execute ffmpeg.",
  };
}

function scanEvidenceDetails(
  analysis: SpiritFlixSmartAnalysis,
  decision: ConversionDecision,
): Record<string, unknown> {
  return {
    scanStarted: true,
    scanCompleted: true,
    analyzerVersion: analysis.analyzerVersion,
    analysisPathKey: analysis.pathKey,
    smartStatus: analysis.status,
    media: analysis.media,
    sampleCount: analysis.samples.length,
    frameSampleCount: analysis.samples.filter((sample) => Boolean(sample.cacheKey)).length,
    safety: analysis.safety,
    scanNotes: analysis.notes,
    conversionDecision: decision.decision,
    conversionReasonCode: decision.reasonCode,
    conversionReason: decision.reason,
    conversionStarted: false,
    conversionBridge: decision.decision === "queue_later" ? "worker_owned_conversion_bridge" : "not_required",
  };
}

function conversionReceiptDetails(receipt: SpiritFlixConversionReceipt | null): Record<string, unknown> {
  if (!receipt) return {};
  return {
    conversionStarted: receipt.mode === "execute",
    conversionBridge: "worker_owned_conversion_bridge",
    conversionReceipt: receipt,
    conversionStatus: receipt.status,
    conversionOutputPath: receipt.outputPath,
    conversionOriginalPreserved: receipt.originalPreserved,
    conversionRollback: receipt.rollback,
  };
}

function organizeAndEnrollmentDetails(
  organizeReceipt: SpiritFlixOrganizeReceipt | null,
  enrollmentRecord: SpiritFlixPendingEnrollmentRecord | null,
  extra: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    organizeReceipt: organizeReceipt ?? undefined,
    pendingEnrollment: enrollmentRecord ?? undefined,
    autoMove: Boolean(extra.autoMove),
    autoDbEnrollment: Boolean(extra.autoDbEnrollment),
    moveReceiptIds: extra.moveReceiptIds,
    enrollmentReceipt: extra.enrollmentReceipt,
  };
}

function faceOrganizerDetails(result: SpiritFlixFaceOrganizerDryRunResult): Record<string, unknown> {
  return {
    faceOrganizer: {
      schema: result.schema,
      command: result.command,
      args: result.args,
      code: result.code,
      timedOut: result.timedOut,
      ok: result.ok,
      stdout: result.stdout,
      stderr: result.stderr,
      safety: result.safety,
      match: {
        status: result.match.status,
        matchedModel: result.match.matchedModel,
        confidence: result.match.confidence,
        faceCount: result.match.faceCount,
        parsed: result.match.parsed,
        reasonCode: result.match.reasonCode,
      },
    },
    matchStatus: result.match.status,
    matchedModel: result.match.matchedModel,
    matchConfidence: result.match.confidence,
    faceOrganizerDryRun: true,
    autoDbEnrollment: false,
  };
}

function derivedFinalState(
  faceResult: SpiritFlixFaceOrganizerDryRunResult,
  decision: ConversionDecision,
  conversionReceipt: SpiritFlixConversionReceipt | null,
): SpiritFlixJobWorkerFinalState {
  if (faceResult.match.status !== "high_confidence_match") return "needs_review";
  if (decision.decision === "skip") return "ready";
  if (conversionReceipt?.status === "completed") return "ready";
  return "needs_review";
}

function finalDetails(
  state: SpiritFlixJobState,
  mode: SpiritFlixJobWorkerMode,
  placeholderState: SpiritFlixJobWorkerPlaceholderState,
  claimIdValue: string | undefined,
  analysis: SpiritFlixSmartAnalysis,
  decision: ConversionDecision,
  faceResult: SpiritFlixFaceOrganizerDryRunResult,
  conversionReceipt: SpiritFlixConversionReceipt | null,
  organizeReceipt: SpiritFlixOrganizeReceipt | null,
  enrollmentRecord: SpiritFlixPendingEnrollmentRecord | null,
  automationDetails: Record<string, unknown> = {},
): Record<string, unknown> {
  return controlDetails("complete", mode, {
    claimId: claimIdValue,
    placeholderState,
    finalState: state,
    workerConsumed: true,
    requiresReview: state === "needs_review",
    ...scanEvidenceDetails(analysis, decision),
    ...faceOrganizerDetails(faceResult),
    ...conversionReceiptDetails(conversionReceipt),
    ...organizeAndEnrollmentDetails(organizeReceipt, enrollmentRecord, automationDetails),
  });
}

function scanFailureMessage(error: unknown): string {
  return error instanceof Error && error.message.trim() ? error.message : "SpiritFlix smart scanner failed.";
}

export async function runSpiritFlixJobWorkerOnce(options: SpiritFlixJobWorkerRunOptions = {}): Promise<SpiritFlixJobWorkerRunResult> {
  const mode = options.mode ?? DEFAULT_MODE;
  const autoMove = options.autoMove ?? process.env.SPIRITFLIX_AUTO_MOVE === "1";
  const autoEnroll = options.autoEnroll ?? process.env.SPIRITFLIX_AUTO_ENROLL === "1";
  const maxAttempts = options.maxAttempts ?? DEFAULT_MAX_ATTEMPTS;
  if (mode !== "no_media_mutation") throw new Error("Only no_media_mutation worker mode is available in this lane.");

  const workerId = options.workerId?.trim() || DEFAULT_WORKER_ID;
  const claim = await claimNextSpiritFlixQueuedJob({ ...options, workerId, mode });
  const events = claim.event ? [claim.event] : [];
  if (!claim.claimed || !claim.job) {
    return {
      schema: "spiritflix-admin-job-worker-run/v1",
      mode,
      workerId,
      claimId: claim.claimId,
      claimed: false,
      completed: false,
      reasonCode: claim.reasonCode,
      job: claim.job,
      events,
    };
  }

  const claimedJob = claim.job;
  const shouldDeadLetter = claimedJob.attempt >= maxAttempts;
  if (!(await sourceExists(claimedJob))) {
    const failed = await appendSpiritFlixJobState(
      {
        videoPath: claimedJob.videoPath,
        fileSizeBytes: claimedJob.fileSizeBytes,
        mtimeMs: claimedJob.mtimeMs,
        jobId: claimedJob.jobId,
        fileName: claimedJob.fileName,
        state: "failed",
        errorReasonCode: "source_missing",
        errorReason: "Worker could not find the queued source video.",
        worker: workerId,
        details: controlDetails("fail", mode, { claimId: claim.claimId, workerConsumed: true, scanStarted: true }),
      },
      options,
    );
    events.push(failed);
    if (shouldDeadLetter) await appendSpiritFlixDeadLetter(failed, options);
    return { schema: "spiritflix-admin-job-worker-run/v1", mode, workerId, claimId: claim.claimId, claimed: true, completed: true, finalState: "failed", reasonCode: "source_missing", job: failed, events };
  }

  const scanVideo = options.scanVideo ?? scanOneSpiritFlixVideoEvidence;
  let analysis: SpiritFlixSmartAnalysis;
  try {
    analysis = await scanVideo(claimedJob.videoPath, {
      mediaRoot: options.mediaRoot,
      ffprobePath: options.ffprobePath,
      ffmpegPath: options.ffmpegPath,
      maxSamples: options.maxSamples,
      probeTimeoutMs: options.probeTimeoutMs,
      frameTimeoutMs: options.frameTimeoutMs,
    });
  } catch (error) {
    const failed = await appendSpiritFlixJobState(
      {
        videoPath: claimedJob.videoPath,
        fileSizeBytes: claimedJob.fileSizeBytes,
        mtimeMs: claimedJob.mtimeMs,
        jobId: claimedJob.jobId,
        fileName: claimedJob.fileName,
        state: "failed",
        errorReasonCode: options.failReasonCode?.trim() || "scan_failed",
        errorReason: options.failReason?.trim() || scanFailureMessage(error),
        worker: workerId,
        details: controlDetails("fail", mode, {
          claimId: claim.claimId,
          workerConsumed: true,
          scanStarted: true,
          scanCompleted: false,
          scannerError: scanFailureMessage(error),
        }),
      },
      options,
    );
    events.push(failed);
    if (shouldDeadLetter) await appendSpiritFlixDeadLetter(failed, options);
    return { schema: "spiritflix-admin-job-worker-run/v1", mode, workerId, claimId: claim.claimId, claimed: true, completed: true, finalState: "failed", reasonCode: failed.errorReasonCode, job: failed, events };
  }

  const faceOrganizer = options.faceOrganizer ?? runSpiritFlixFaceOrganizerDryRun;
  const faceResult = await faceOrganizer(claimedJob.videoPath, {
    sourceDir: options.mediaRoot,
    ...options.faceOrganizerDryRun,
  });
  if (!faceResult.ok || faceResult.match.status === "command_failed") {
    const failed = await appendSpiritFlixJobState(
      {
        videoPath: claimedJob.videoPath,
        fileSizeBytes: claimedJob.fileSizeBytes,
        mtimeMs: claimedJob.mtimeMs,
        jobId: claimedJob.jobId,
        fileName: claimedJob.fileName,
        state: "failed",
        errorReasonCode: faceResult.match.reasonCode || "face_organizer_failed",
        errorReason: faceResult.timedOut
          ? "Face organizer dry-run timed out."
          : "Face organizer dry-run failed after scanner evidence.",
        worker: workerId,
        details: controlDetails("fail", mode, {
          claimId: claim.claimId,
          workerConsumed: true,
          ...scanEvidenceDetails(analysis, decideConversionBridge(analysis)),
          ...faceOrganizerDetails(faceResult),
        }),
      },
      options,
    );
    events.push(failed);
    if (shouldDeadLetter) await appendSpiritFlixDeadLetter(failed, options);
    return { schema: "spiritflix-admin-job-worker-run/v1", mode, workerId, claimId: claim.claimId, claimed: true, completed: true, finalState: "failed", reasonCode: failed.errorReasonCode, job: failed, events };
  }

  const decision = decideConversionBridge(analysis);
  const conversionBridge = options.conversionBridge ?? runSpiritFlixConversionBridge;
  let conversionReceipt: SpiritFlixConversionReceipt | null = null;
  if (decision.decision === "queue_later") {
    conversionReceipt = await conversionBridge({
      mediaRoot: options.mediaRoot,
      jobId: claimedJob.jobId,
      videoPath: claimedJob.videoPath,
      fileSizeBytes: claimedJob.fileSizeBytes,
      mtimeMs: claimedJob.mtimeMs,
      outputRoot: options.conversionOutputRoot,
      mode: options.conversionMode ?? "enqueue",
      timeoutMs: options.conversionTimeoutMs,
    });
    if (conversionReceipt.status === "failed") {
      const failed = await appendSpiritFlixJobState(
        {
          videoPath: claimedJob.videoPath,
          fileSizeBytes: claimedJob.fileSizeBytes,
          mtimeMs: claimedJob.mtimeMs,
          jobId: claimedJob.jobId,
          fileName: claimedJob.fileName,
          state: "failed",
          errorReasonCode: "conversion_failed",
          errorReason: conversionReceipt.errorReason ?? "Worker-owned conversion failed.",
          worker: workerId,
          details: controlDetails("fail", mode, {
            claimId: claim.claimId,
            deadLetter: shouldDeadLetter,
            workerConsumed: true,
            ...scanEvidenceDetails(analysis, decision),
            ...faceOrganizerDetails(faceResult),
            ...conversionReceiptDetails(conversionReceipt),
          }),
        },
        options,
      );
      events.push(failed);
      if (shouldDeadLetter) await appendSpiritFlixDeadLetter(failed, options);
      return { schema: "spiritflix-admin-job-worker-run/v1", mode, workerId, claimId: claim.claimId, claimed: true, completed: true, finalState: "failed", reasonCode: failed.errorReasonCode, job: failed, events };
    }
  }
  const placeholderState = options.placeholderState ?? decision.placeholderState;
  const highConfidence = faceResult.match.status === "high_confidence_match" && Boolean(faceResult.match.matchedModel) && typeof faceResult.match.confidence === "number" && faceResult.match.confidence >= HIGH_CONFIDENCE_THRESHOLD;
  const requestedFinalState = options.finalState ?? derivedFinalState(faceResult, decision, conversionReceipt);
  const organizeReceipt =
    highConfidence && faceResult.match.matchedModel && typeof faceResult.match.confidence === "number"
      ? await createSpiritFlixOrganizeReceipt({
          mediaRoot: options.mediaRoot,
          videoPath: claimedJob.videoPath,
          matchedModel: faceResult.match.matchedModel,
          confidence: faceResult.match.confidence,
          mode: autoMove ? "execute" : "preview",
        })
      : null;
  const movedSourceVideo = organizeReceipt?.after?.targetExists ? organizeReceipt.targetPath : claimedJob.videoPath;
  const enrollmentRecord =
    highConfidence && faceResult.match.matchedModel && typeof faceResult.match.confidence === "number"
      ? createSpiritFlixPendingEnrollmentRecord({
          matchedModel: faceResult.match.matchedModel,
          confidence: faceResult.match.confidence,
          sourceVideo: movedSourceVideo,
        })
      : null;
  const enrollmentReceipt = autoEnroll && enrollmentRecord && faceResult.match.matchedModel && typeof faceResult.match.confidence === "number"
    ? await (options.enrollmentBridge ?? runSpiritFlixEnrollmentBridge)({
        matchedModel: faceResult.match.matchedModel,
        confidence: faceResult.match.confidence,
        sourceVideo: movedSourceVideo,
        sidecarPath: `${claimedJob.videoPath}.face-meta.json`,
        minFaceScore: HIGH_CONFIDENCE_THRESHOLD,
      })
    : undefined;
  const automationDetails = {
    autoMove: Boolean(autoMove && organizeReceipt?.after?.targetExists),
    autoDbEnrollment: Boolean(autoEnroll && enrollmentReceipt),
    moveReceiptIds: organizeReceipt ? { before: organizeReceipt.beforeReceiptId, after: organizeReceipt.afterReceiptId } : undefined,
    enrollmentReceipt,
  };
  const placeholder = await appendSpiritFlixJobState(
    {
      videoPath: claimedJob.videoPath,
      fileSizeBytes: claimedJob.fileSizeBytes,
      mtimeMs: claimedJob.mtimeMs,
      jobId: claimedJob.jobId,
      fileName: claimedJob.fileName,
      state: placeholderState,
      worker: workerId,
      details: controlDetails("scan", mode, {
        claimId: claim.claimId,
        placeholderState,
        workerConsumed: true,
        ...scanEvidenceDetails(analysis, decision),
        ...faceOrganizerDetails(faceResult),
        ...conversionReceiptDetails(conversionReceipt),
        ...organizeAndEnrollmentDetails(organizeReceipt, enrollmentRecord, automationDetails),
      }),
    },
    options,
  );
  events.push(placeholder);

  if (requestedFinalState === "failed") {
    const failed = await appendSpiritFlixJobState(
      {
        videoPath: claimedJob.videoPath,
        fileSizeBytes: claimedJob.fileSizeBytes,
        mtimeMs: claimedJob.mtimeMs,
        jobId: claimedJob.jobId,
        fileName: claimedJob.fileName,
        state: "failed",
        errorReasonCode: options.failReasonCode?.trim() || "worker_requested_failure",
        errorReason: options.failReason?.trim() || "No-media-mutation worker failed by request after scanner evidence.",
        worker: workerId,
        details: controlDetails("fail", mode, {
          claimId: claim.claimId,
          placeholderState,
          workerConsumed: true,
          ...scanEvidenceDetails(analysis, decision),
          ...faceOrganizerDetails(faceResult),
          ...conversionReceiptDetails(conversionReceipt),
          ...organizeAndEnrollmentDetails(organizeReceipt, enrollmentRecord, automationDetails),
        }),
      },
      options,
    );
    events.push(failed);
    if (shouldDeadLetter) await appendSpiritFlixDeadLetter(failed, options);
    return { schema: "spiritflix-admin-job-worker-run/v1", mode, workerId, claimId: claim.claimId, claimed: true, completed: true, finalState: "failed", reasonCode: failed.errorReasonCode, job: failed, events };
  }

  const completed = await appendSpiritFlixJobState(
    {
      videoPath: claimedJob.videoPath,
      fileSizeBytes: claimedJob.fileSizeBytes,
      mtimeMs: claimedJob.mtimeMs,
      jobId: claimedJob.jobId,
      fileName: claimedJob.fileName,
      state: requestedFinalState,
      worker: workerId,
      details: finalDetails(requestedFinalState, mode, placeholderState, claim.claimId, analysis, decision, faceResult, conversionReceipt, organizeReceipt, enrollmentRecord, automationDetails),
    },
    options,
  );
  events.push(completed);
  return { schema: "spiritflix-admin-job-worker-run/v1", mode, workerId, claimId: claim.claimId, claimed: true, completed: true, finalState: requestedFinalState, job: completed, events };
}

export async function hasActiveSpiritFlixWorkerClaim(jobId: string, options?: SpiritFlixJobStoreOptions): Promise<boolean> {
  const history = await getSpiritFlixJobHistory(jobId, options);
  return Boolean(history.job && isActiveSpiritFlixJobState(history.job.state) && history.job.state !== "queued");
}
