export const CONVERTER_ROOTS = {
  authorizedImports: "/mnt/spirit-8tb/converter/authorized-imports",
  audio: "/mnt/spirit-8tb/converter/audio",
  transcripts: "/mnt/spirit-8tb/converter/transcripts",
  knowledge: "/mnt/spirit-8tb/converter/knowledge",
  logs: "/mnt/spirit-8tb/converter/logs",
} as const;

export type ConverterOutputKey = keyof typeof CONVERTER_ROOTS;

export type ConverterJobKind =
  | "youtube"
  | "local_file"
  | "folder"
  | "manual_transcript";

export type ConverterJobState =
  | "queued"
  | "validating"
  | "fetching_metadata"
  | "downloading_authorized_media"
  | "extracting_audio"
  | "pending_transcription_engine"
  | "transcribing"
  | "summarizing"
  | "completed"
  | "failed"
  | "skipped"
  | "cancelled";

export type ConverterQueueState = "idle" | "running" | "paused" | "cancelled";

export type ConverterAuthorization = {
  affirmed: boolean;
  note?: string;
  proofPath?: string;
  recordedAt: string;
};

export type ConverterMetadataInput = {
  title?: string;
  creator?: string;
  project?: string;
  tags?: string[];
  licenseNote?: string;
};

export type ConverterSourceMetadata = {
  title?: string;
  channel?: string;
  creator?: string;
  thumbnailUrl?: string;
  durationSeconds?: number;
  uploadDate?: string;
  canonicalUrl?: string;
  videoId?: string;
};

export type ConverterJobOutput = {
  authorizationPath?: string;
  downloadedMediaPath?: string;
  audioPath?: string;
  transcriptPath?: string;
  summaryPath?: string;
  chunksPath?: string;
  metadataPath?: string;
  knowledgeRecordPath?: string;
  outputHashes?: Record<string, string>;
};

export type ConverterLogEntry = {
  at: string;
  state: ConverterJobState;
  message: string;
};

export type ConverterJob = {
  id: string;
  kind: ConverterJobKind;
  source: string;
  state: ConverterJobState;
  createdAt: string;
  updatedAt: string;
  authorization?: ConverterAuthorization;
  metadata: ConverterMetadataInput;
  sourceMetadata?: ConverterSourceMetadata;
  transcriptText?: string;
  output: ConverterJobOutput;
  logs: ConverterLogEntry[];
  error?: string;
  commandUsed?: string;
};

export type ConverterBatchInput = {
  pastedItems?: string;
  folderPath?: string;
  manualTranscript?: string;
  authorization: Omit<ConverterAuthorization, "recordedAt">;
  metadata?: ConverterMetadataInput;
};

export type ConverterQueueSnapshot = {
  state: ConverterQueueState;
  activeJobId?: string;
  jobs: ConverterJob[];
};

export type ConverterKnowledgeRecord = {
  id: string;
  source: string;
  sourceType: ConverterJobKind;
  authorization?: ConverterAuthorization;
  title?: string;
  creator?: string;
  project?: string;
  tags: string[];
  transcriptPath?: string;
  summaryPath?: string;
  audioPath?: string;
  createdAt: string;
  status: ConverterJobState;
};
