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
