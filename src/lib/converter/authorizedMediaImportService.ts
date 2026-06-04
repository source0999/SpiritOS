import fs from "fs/promises";
import path from "path";
import { execFile } from "child_process";
import { promisify } from "util";

import {
  CONVERTER_ROOTS,
  type ConverterAuthorization,
  type ConverterBatchInput,
  type ConverterJob,
  type ConverterJobKind,
  type ConverterJobState,
  type ConverterKnowledgeRecord,
  type ConverterMetadataInput,
  type ConverterSourceMetadata,
} from "@/lib/converter/converterTypes";
import {
  converterPath,
  ensureConverterRoots,
  redactDiagnostics,
  sanitizeFilename,
  sha256File,
  writeJsonFile,
  writeTextFile,
  type ConverterRootMap,
} from "@/lib/converter/converterStorageService";

const execFileAsync = promisify(execFile);

const MEDIA_EXTENSIONS = new Set([".mp4", ".mov", ".m4a", ".mp3", ".wav", ".flac"]);

export type ConverterCommandRunner = (
  command: string,
  args: string[],
) => Promise<{ stdout?: string; stderr?: string }>;

export type ConverterToolAvailability = {
  ffmpeg?: boolean;
  ytdlp?: boolean;
  speechToText?: boolean;
};

export type AuthorizedMediaImportOptions = {
  roots?: ConverterRootMap;
  now?: () => Date;
  commandRunner?: ConverterCommandRunner;
  tools?: ConverterToolAvailability;
};

export type ProcessJobOptions = AuthorizedMediaImportOptions & {
  shouldCancel?: () => boolean;
};

function nowIso(now: () => Date = () => new Date()): string {
  return now().toISOString();
}

function makeJobId(kind: ConverterJobKind, source: string, now: () => Date): string {
  const entropy = Buffer.from(`${kind}:${source}:${now().toISOString()}`)
    .toString("base64url")
    .slice(0, 12);
  return `${kind}-${Date.now().toString(36)}-${entropy}`;
}

export function isYouTubeUrl(value: string): boolean {
  try {
    const url = new URL(value);
    const host = url.hostname.replace(/^www\./, "");
    return host === "youtube.com" || host === "youtu.be" || host === "m.youtube.com";
  } catch {
    return false;
  }
}

export function extractYouTubeVideoId(value: string): string | undefined {
  try {
    const url = new URL(value);
    const host = url.hostname.replace(/^www\./, "");

    if (host === "youtu.be") {
      return url.pathname.split("/").filter(Boolean)[0];
    }

    if (url.pathname === "/watch") {
      return url.searchParams.get("v") ?? undefined;
    }

    const match = url.pathname.match(/\/(?:shorts|embed|live)\/([^/?#]+)/);
    return match?.[1];
  } catch {
    return undefined;
  }
}

export function classifyConverterInput(value: string): ConverterJobKind {
  const trimmed = value.trim();
  if (isYouTubeUrl(trimmed)) {
    return "youtube";
  }

  return "local_file";
}

export function parseConverterBatch(input: ConverterBatchInput, options: AuthorizedMediaImportOptions = {}): ConverterJob[] {
  const now = options.now ?? (() => new Date());
  const createdAt = nowIso(now);
  const metadata = normalizeMetadata(input.metadata);
  const authorization: ConverterAuthorization | undefined = input.authorization.affirmed
    ? {
        affirmed: true,
        note: input.authorization.note?.trim() || metadata.licenseNote,
        proofPath: input.authorization.proofPath?.trim() || undefined,
        recordedAt: createdAt,
      }
    : undefined;

  const rawItems = [
    ...(input.pastedItems ?? "")
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean),
    ...(input.folderPath?.trim() ? [input.folderPath.trim()] : []),
  ];

  const jobs = rawItems.map((source) => {
    const kind = input.folderPath?.trim() === source ? "folder" : classifyConverterInput(source);
    return createConverterJob({ kind, source, authorization, metadata, now });
  });

  if (input.manualTranscript?.trim()) {
    jobs.push(
      createConverterJob({
        kind: "manual_transcript",
        source: metadata.title || "manual transcript",
        authorization,
        metadata,
        transcriptText: input.manualTranscript.trim(),
        now,
      }),
    );
  }

  return jobs;
}

export function validateConverterJob(job: ConverterJob): ConverterJob {
  if (job.kind === "youtube" && !job.authorization?.affirmed) {
    return failJob(
      job,
      "YouTube imports require confirmation that the content is owned or licensed and an authorization record can be stored.",
      "validating",
    );
  }

  if (job.kind === "youtube" && !extractYouTubeVideoId(job.source)) {
    return failJob(job, "Could not extract a YouTube video ID from this URL.", "validating");
  }

  if ((job.kind === "local_file" || job.kind === "folder") && job.source.includes("\0")) {
    return failJob(job, "Source path contains invalid characters.", "validating");
  }

  return appendLog({ ...job, state: "queued" }, "queued", "Validated and queued.");
}

export async function processConverterJob(
  job: ConverterJob,
  options: ProcessJobOptions = {},
): Promise<ConverterJob> {
  const roots = options.roots ?? CONVERTER_ROOTS;
  const now = options.now ?? (() => new Date());
  const tools = options.tools ?? {};
  const run = options.commandRunner ?? runCommand;

  let working = touch(appendLog(job, "validating", "Starting validation."), "validating", now);
  working = validateConverterJob(working);
  if (working.state === "failed") {
    return persistJobArtifacts(working, roots, now);
  }

  if (options.shouldCancel?.()) {
    return touch(appendLog(working, "cancelled", "Cancelled before processing."), "cancelled", now);
  }

  await ensureConverterRoots(roots);
  await persistAuthorization(working, roots, now);

  if (working.kind === "manual_transcript") {
    return processTranscriptJob(working, roots, now);
  }

  if (working.kind === "youtube") {
    working = await processYouTubeJob(working, roots, now, run, tools);
  } else {
    working = await processLocalJob(working, roots, now, run, tools);
  }

  if (working.state === "failed" || working.state === "cancelled") {
    return persistJobArtifacts(working, roots, now);
  }

  if (!working.output.transcriptPath) {
    working = tools.speechToText
      ? touch(appendLog(working, "transcribing", "Speech-to-text engine configured; transcription step reserved."), "transcribing", now)
      : touch(
          appendLog(working, "pending_transcription_engine", "No speech-to-text engine is configured yet."),
          "pending_transcription_engine",
          now,
        );
  }

  return persistJobArtifacts(working, roots, now);
}

export function createDiagnosticsSnapshot(job: ConverterJob): string {
  return redactDiagnostics(
    JSON.stringify(
      {
        id: job.id,
        kind: job.kind,
        source: job.source,
        state: job.state,
        authorization: job.authorization
          ? {
              affirmed: job.authorization.affirmed,
              hasNote: Boolean(job.authorization.note),
              hasProofPath: Boolean(job.authorization.proofPath),
              recordedAt: job.authorization.recordedAt,
            }
          : undefined,
        sourceMetadata: job.sourceMetadata,
        output: job.output,
        commandUsed: job.commandUsed,
        error: job.error,
        logs: job.logs,
      },
      null,
      2,
    ),
  );
}

function normalizeMetadata(metadata: ConverterMetadataInput = {}): ConverterMetadataInput {
  return {
    title: metadata.title?.trim() || undefined,
    creator: metadata.creator?.trim() || undefined,
    project: metadata.project?.trim() || undefined,
    tags: metadata.tags?.map((tag) => tag.trim()).filter(Boolean) ?? [],
    licenseNote: metadata.licenseNote?.trim() || undefined,
  };
}

function createConverterJob({
  kind,
  source,
  authorization,
  metadata,
  transcriptText,
  now,
}: {
  kind: ConverterJobKind;
  source: string;
  authorization?: ConverterAuthorization;
  metadata: ConverterMetadataInput;
  transcriptText?: string;
  now: () => Date;
}): ConverterJob {
  const createdAt = nowIso(now);
  return {
    id: makeJobId(kind, source, now),
    kind,
    source,
    state: "queued",
    createdAt,
    updatedAt: createdAt,
    authorization,
    metadata,
    transcriptText,
    output: {},
    logs: [{ at: createdAt, state: "queued", message: "Job created." }],
  };
}

function appendLog(job: ConverterJob, state: ConverterJobState, message: string): ConverterJob {
  return {
    ...job,
    logs: [...job.logs, { at: new Date().toISOString(), state, message: redactDiagnostics(message) }],
  };
}

function touch(job: ConverterJob, state: ConverterJobState, now: () => Date): ConverterJob {
  return { ...job, state, updatedAt: nowIso(now) };
}

function failJob(job: ConverterJob, error: string, state: ConverterJobState = "failed"): ConverterJob {
  return {
    ...appendLog(job, "failed", error),
    state: "failed",
    error,
    updatedAt: new Date().toISOString(),
  };
}

async function persistAuthorization(job: ConverterJob, roots: ConverterRootMap, now: () => Date): Promise<void> {
  if (!job.authorization) {
    return;
  }

  const target = converterPath(roots, "authorizedImports", job.id, "authorization.json");
  await writeJsonFile(target, {
    jobId: job.id,
    source: job.source,
    kind: job.kind,
    authorization: job.authorization,
    metadata: job.metadata,
    recordedAt: nowIso(now),
  });
  job.output.authorizationPath = target;
}

async function processYouTubeJob(
  job: ConverterJob,
  roots: ConverterRootMap,
  now: () => Date,
  run: ConverterCommandRunner,
  tools: ConverterToolAvailability,
): Promise<ConverterJob> {
  const videoId = extractYouTubeVideoId(job.source);
  let working = touch(appendLog(job, "fetching_metadata", "Fetching authorized YouTube metadata where available."), "fetching_metadata", now);
  const canonicalUrl = videoId ? `https://www.youtube.com/watch?v=${videoId}` : job.source;

  working.sourceMetadata = {
    ...working.sourceMetadata,
    videoId,
    canonicalUrl,
    title: working.metadata.title,
    channel: working.metadata.creator,
  };

  if (!tools.ytdlp) {
    return failJob(
      working,
      "yt-dlp is not available. Install yt-dlp to fetch metadata/download authorized YouTube media.",
    );
  }

  try {
    const metadataResult = await run("yt-dlp", ["--dump-single-json", "--no-playlist", canonicalUrl]);
    const parsed = JSON.parse(metadataResult.stdout || "{}") as Record<string, unknown>;
    working.sourceMetadata = normalizeYouTubeMetadata(parsed, videoId, canonicalUrl, working.metadata);
  } catch (error) {
    working = appendLog(working, "fetching_metadata", `Metadata fetch skipped: ${String(error)}`);
  }

  const baseName = sanitizeFilename(working.sourceMetadata?.title || videoId || "youtube-import");
  const outputTemplate = converterPath(roots, "audio", working.id, `${baseName}.%(ext)s`);
  const args = [
    "--no-playlist",
    "-x",
    "--audio-format",
    "mp3",
    "-o",
    outputTemplate,
    canonicalUrl,
  ];
  const commandUsed = `yt-dlp ${args.map((arg) => (arg.includes(" ") ? JSON.stringify(arg) : arg)).join(" ")}`;
  working = touch(appendLog(working, "downloading_authorized_media", "Downloading authorized media and extracting audio."), "downloading_authorized_media", now);
  working.commandUsed = redactDiagnostics(commandUsed);

  try {
    await run("yt-dlp", args);
    working.output.audioPath = outputTemplate.replace("%(ext)s", "mp3");
    working = touch(appendLog(working, "extracting_audio", "Audio extraction command completed."), "extracting_audio", now);
  } catch (error) {
    return failJob(working, `Authorized YouTube import failed: ${String(error)}`);
  }

  return working;
}

async function processLocalJob(
  job: ConverterJob,
  roots: ConverterRootMap,
  now: () => Date,
  run: ConverterCommandRunner,
  tools: ConverterToolAvailability,
): Promise<ConverterJob> {
  let working = touch(appendLog(job, "extracting_audio", "Preparing local media audio extraction."), "extracting_audio", now);

  if (job.kind === "folder") {
    return touch(
      appendLog(working, "skipped", "Folder expansion is reserved for the batch UI; add files or pasted paths for this pass."),
      "skipped",
      now,
    );
  }

  const ext = path.extname(job.source).toLowerCase();
  if (!MEDIA_EXTENSIONS.has(ext)) {
    return failJob(working, `Unsupported local media extension: ${ext || "none"}`);
  }

  if (!tools.ffmpeg) {
    return failJob(working, "ffmpeg is not available. Install ffmpeg to extract or convert local media audio.");
  }

  const baseName = sanitizeFilename(path.basename(job.source, ext));
  const audioPath = converterPath(roots, "audio", working.id, `${baseName}.mp3`);
  const args = ["-y", "-i", job.source, "-vn", "-codec:a", "libmp3lame", "-q:a", "2", audioPath];
  working.commandUsed = redactDiagnostics(`ffmpeg ${args.map((arg) => (arg.includes(" ") ? JSON.stringify(arg) : arg)).join(" ")}`);

  try {
    await run("ffmpeg", args);
    working.output.audioPath = audioPath;
    working.sourceMetadata = {
      title: working.metadata.title || baseName,
      creator: working.metadata.creator,
    };
    working = touch(appendLog(working, "extracting_audio", "Local audio extraction completed."), "extracting_audio", now);
  } catch (error) {
    return failJob(working, `Local audio extraction failed: ${String(error)}`);
  }

  return working;
}

async function processTranscriptJob(
  job: ConverterJob,
  roots: ConverterRootMap,
  now: () => Date,
): Promise<ConverterJob> {
  const title = sanitizeFilename(job.metadata.title || "manual-transcript");
  const transcriptPath = converterPath(roots, "transcripts", job.id, `${title}.txt`);
  await writeTextFile(transcriptPath, `${job.transcriptText ?? ""}\n`);
  const working = touch(
    {
      ...appendLog(job, "summarizing", "Stored pasted transcript and prepared knowledge record."),
      sourceMetadata: {
        title: job.metadata.title,
        creator: job.metadata.creator,
      },
      output: { ...job.output, transcriptPath },
    },
    "summarizing",
    now,
  );

  return persistJobArtifacts(working, roots, now, "completed");
}

async function persistJobArtifacts(
  job: ConverterJob,
  roots: ConverterRootMap,
  now: () => Date,
  finalState?: ConverterJobState,
): Promise<ConverterJob> {
  let working = finalState ? touch(job, finalState, now) : job;
  const safeTitle = sanitizeFilename(working.sourceMetadata?.title || working.metadata.title || working.id);

  if (working.transcriptText && !working.output.transcriptPath) {
    const transcriptPath = converterPath(roots, "transcripts", working.id, `${safeTitle}.txt`);
    await writeTextFile(transcriptPath, `${working.transcriptText}\n`);
    working.output.transcriptPath = transcriptPath;
  }

  const summaryPath = converterPath(roots, "knowledge", working.id, `${safeTitle}-summary.md`);
  const metadataPath = converterPath(roots, "knowledge", working.id, `${safeTitle}-metadata.json`);
  const chunksPath = converterPath(roots, "knowledge", working.id, `${safeTitle}-chunks.json`);
  const knowledgeRecordPath = converterPath(roots, "knowledge", working.id, `${safeTitle}-knowledge.json`);
  const logPath = converterPath(roots, "logs", working.id, "job-log.json");

  await writeTextFile(summaryPath, buildSummary(working));
  await writeJsonFile(chunksPath, buildChunks(working));
  await writeJsonFile(metadataPath, {
    id: working.id,
    source: working.source,
    sourceType: working.kind,
    sourceMetadata: working.sourceMetadata,
    metadata: working.metadata,
    authorization: working.authorization,
    commandUsed: working.commandUsed,
    output: working.output,
    status: working.state,
    createdAt: working.createdAt,
    updatedAt: nowIso(now),
  });

  const knowledgeRecord: ConverterKnowledgeRecord = {
    id: working.id,
    source: working.source,
    sourceType: working.kind,
    authorization: working.authorization,
    title: working.sourceMetadata?.title || working.metadata.title,
    creator: working.sourceMetadata?.creator || working.sourceMetadata?.channel || working.metadata.creator,
    project: working.metadata.project,
    tags: working.metadata.tags ?? [],
    transcriptPath: working.output.transcriptPath,
    summaryPath,
    audioPath: working.output.audioPath,
    createdAt: working.createdAt,
    status: working.state,
  };

  await writeJsonFile(knowledgeRecordPath, knowledgeRecord);
  await writeJsonFile(logPath, working.logs);

  const hashEntries = await Promise.all(
    [working.output.audioPath, working.output.transcriptPath, summaryPath, metadataPath, chunksPath, knowledgeRecordPath]
      .filter(Boolean)
      .map(async (filePath) => [filePath as string, await optionalHash(filePath as string)] as const),
  );

  working = {
    ...working,
    output: {
      ...working.output,
      summaryPath,
      metadataPath,
      chunksPath,
      knowledgeRecordPath,
      outputHashes: Object.fromEntries(hashEntries.filter(([, hash]) => Boolean(hash))),
    },
    updatedAt: nowIso(now),
  };

  if (working.state !== "failed" && working.state !== "pending_transcription_engine" && working.state !== "skipped") {
    working = touch(appendLog(working, "completed", "Converter artifacts written."), "completed", now);
  }

  return working;
}

async function optionalHash(filePath: string): Promise<string> {
  try {
    return await sha256File(filePath);
  } catch {
    return "";
  }
}

function buildSummary(job: ConverterJob): string {
  const title = job.sourceMetadata?.title || job.metadata.title || job.source;
  return [
    `# ${title}`,
    "",
    `Status: ${job.state}`,
    `Source: ${job.source}`,
    job.output.transcriptPath
      ? `Transcript: ${job.output.transcriptPath}`
      : "Transcript: pending transcription engine",
    job.output.audioPath ? `Audio: ${job.output.audioPath}` : undefined,
    "",
  ]
    .filter(Boolean)
    .join("\n");
}

function buildChunks(job: ConverterJob): Array<{ index: number; text: string; source: string }> {
  const text = job.transcriptText?.trim();
  if (!text) {
    return [];
  }

  const chunks: Array<{ index: number; text: string; source: string }> = [];
  for (let index = 0; index < text.length; index += 1600) {
    chunks.push({
      index: chunks.length,
      text: text.slice(index, index + 1600),
      source: job.source,
    });
  }
  return chunks;
}

function normalizeYouTubeMetadata(
  parsed: Record<string, unknown>,
  videoId: string | undefined,
  canonicalUrl: string,
  metadata: ConverterMetadataInput,
): ConverterSourceMetadata {
  return {
    videoId,
    canonicalUrl,
    title: typeof parsed.title === "string" ? parsed.title : metadata.title,
    channel: typeof parsed.channel === "string" ? parsed.channel : metadata.creator,
    creator: typeof parsed.uploader === "string" ? parsed.uploader : metadata.creator,
    thumbnailUrl: typeof parsed.thumbnail === "string" ? parsed.thumbnail : undefined,
    durationSeconds: typeof parsed.duration === "number" ? parsed.duration : undefined,
    uploadDate: typeof parsed.upload_date === "string" ? parsed.upload_date : undefined,
  };
}

async function runCommand(command: string, args: string[]): Promise<{ stdout?: string; stderr?: string }> {
  const result = await execFileAsync(command, args, { windowsHide: true, maxBuffer: 1024 * 1024 * 10 });
  return {
    stdout: result.stdout,
    stderr: result.stderr,
  };
}

export async function detectConverterTools(
  run: ConverterCommandRunner = runCommand,
): Promise<ConverterToolAvailability> {
  const [ffmpeg, ytdlp] = await Promise.all([
    toolExists("ffmpeg", ["-version"], run),
    toolExists("yt-dlp", ["--version"], run),
  ]);

  return { ffmpeg, ytdlp, speechToText: false };
}

async function toolExists(command: string, args: string[], run: ConverterCommandRunner): Promise<boolean> {
  try {
    await run(command, args);
    return true;
  } catch {
    return false;
  }
}

export async function expandLocalFolder(folderPath: string): Promise<string[]> {
  const entries = await fs.readdir(folderPath, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && MEDIA_EXTENSIONS.has(path.extname(entry.name).toLowerCase()))
    .map((entry) => path.join(folderPath, entry.name));
}
