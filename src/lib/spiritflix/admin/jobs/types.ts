import type { SpiritFlixSmartAnalysis } from "../smart/types";
import type { SpiritFlixFaceOrganizerDryRunOptions, SpiritFlixFaceOrganizerDryRunResult } from "./face-organizer-bridge";
import type { SpiritFlixConversionBridgeOptions, SpiritFlixConversionReceipt, SpiritFlixConversionMode } from "./conversion-bridge";

export const SPIRITFLIX_JOB_SCHEMA = "spiritflix-admin-job/v1";

export const SPIRITFLIX_JOB_STATES = [
  "discovered",
  "queued",
  "scanning",
  "matching",
  "converting",
  "moving",
  "ready",
  "needs_review",
  "failed",
] as const;

export type SpiritFlixJobState = (typeof SPIRITFLIX_JOB_STATES)[number];

export interface SpiritFlixJobVideoIdentity {
  videoPath: string;
  fileSizeBytes: number;
  mtimeMs: number;
}

export interface SpiritFlixJobRecord extends SpiritFlixJobVideoIdentity {
  schema: typeof SPIRITFLIX_JOB_SCHEMA;
  jobId: string;
  videoId: string;
  fileName: string;
  state: SpiritFlixJobState;
  attempt: number;
  createdAt: string;
  updatedAt: string;
  errorReason?: string;
  errorReasonCode?: string;
  worker?: string;
  details?: Record<string, unknown>;
  eventCount: number;
  lastEventId: string;
}

export interface SpiritFlixJobEvent extends SpiritFlixJobRecord {
  eventId: string;
  previousState?: SpiritFlixJobState;
}

export interface AppendSpiritFlixJobStateInput extends SpiritFlixJobVideoIdentity {
  state: SpiritFlixJobState;
  jobId?: string;
  fileName?: string;
  errorReason?: string;
  errorReasonCode?: string;
  worker?: string;
  details?: Record<string, unknown>;
}

export interface SpiritFlixJobStoreOptions {
  mediaRoot?: string;
  jobRoot?: string;
  now?: () => Date;
}

export interface SpiritFlixJobListOptions extends SpiritFlixJobStoreOptions {
  activeOnly?: boolean;
  videoId?: string;
}

export interface SpiritFlixJobListResponse {
  schema: "spiritflix-admin-jobs/v1";
  generatedAt: string;
  jobs: SpiritFlixJobRecord[];
  totalRecordCount: number;
  totalEventCount: number;
  query: {
    activeOnly: boolean;
    videoId: string;
  };
}

export interface SpiritFlixJobHistoryResponse {
  schema: "spiritflix-admin-job-history/v1";
  generatedAt: string;
  jobId: string;
  job: SpiritFlixJobRecord | null;
  events: SpiritFlixJobEvent[];
  totalEventCount: number;
}

export interface FailSpiritFlixJobInput {
  jobId: string;
  reasonCode: string;
  reason: string;
  worker?: string;
}

export interface RequeueSpiritFlixJobInput {
  jobId: string;
  worker?: string;
}

export interface SpiritFlixJobControlResult {
  schema: "spiritflix-admin-job-control/v1";
  action: "fail" | "requeue";
  job: SpiritFlixJobRecord;
  event: SpiritFlixJobEvent;
}

export type SpiritFlixJobWorkerMode = "no_media_mutation";
export type SpiritFlixJobWorkerPlaceholderState = "matching" | "converting";
export type SpiritFlixJobWorkerFinalState = "ready" | "needs_review" | "failed";

export interface SpiritFlixJobClaimResult {
  schema: "spiritflix-admin-job-claim/v1";
  claimed: boolean;
  reasonCode?: "no_queued_jobs" | "job_not_queued" | "job_not_found";
  workerId: string;
  claimId?: string;
  job?: SpiritFlixJobRecord;
  event?: SpiritFlixJobEvent;
}

export interface SpiritFlixJobWorkerScanOptions {
  mediaRoot?: string;
  ffprobePath?: string;
  ffmpegPath?: string;
  maxSamples?: number;
  probeTimeoutMs?: number;
  frameTimeoutMs?: number;
}

export type SpiritFlixJobWorkerScanVideo = (
  videoPath: string,
  options?: SpiritFlixJobWorkerScanOptions,
) => Promise<SpiritFlixSmartAnalysis>;

export type SpiritFlixJobWorkerFaceOrganizer = (
  videoPath: string,
  options?: SpiritFlixFaceOrganizerDryRunOptions,
) => Promise<SpiritFlixFaceOrganizerDryRunResult>;

export type SpiritFlixJobWorkerConversionBridge = (
  options: SpiritFlixConversionBridgeOptions,
) => Promise<SpiritFlixConversionReceipt>;

export interface SpiritFlixJobWorkerRunOptions extends SpiritFlixJobStoreOptions {
  jobId?: string;
  workerId?: string;
  mode?: SpiritFlixJobWorkerMode;
  placeholderState?: SpiritFlixJobWorkerPlaceholderState;
  finalState?: SpiritFlixJobWorkerFinalState;
  failReasonCode?: string;
  failReason?: string;
  ffprobePath?: string;
  ffmpegPath?: string;
  maxSamples?: number;
  probeTimeoutMs?: number;
  frameTimeoutMs?: number;
  scanVideo?: SpiritFlixJobWorkerScanVideo;
  faceOrganizer?: SpiritFlixJobWorkerFaceOrganizer;
  faceOrganizerDryRun?: SpiritFlixFaceOrganizerDryRunOptions;
  faceConfidenceThreshold?: number;
  conversionBridge?: SpiritFlixJobWorkerConversionBridge;
  conversionMode?: SpiritFlixConversionMode;
  conversionOutputRoot?: string;
  conversionTimeoutMs?: number;
}

export interface SpiritFlixJobWorkerRunResult {
  schema: "spiritflix-admin-job-worker-run/v1";
  mode: SpiritFlixJobWorkerMode;
  workerId: string;
  claimId?: string;
  claimed: boolean;
  completed: boolean;
  finalState?: SpiritFlixJobWorkerFinalState;
  reasonCode?: string;
  job?: SpiritFlixJobRecord;
  events: SpiritFlixJobEvent[];
}
