// SpiritFlix smart batch analysis (S7)
// Folder/selection orchestration only. Writes analysis sidecars; never renames or moves media.

import fs from "node:fs/promises";
import path from "node:path";
import { resolveSpiritFlixAdminPath } from "../paths";
import { readSmartAnalysis } from "./analysis-store";
import { buildSmartRenamePreviewDraft } from "./rename-preview";
import {
  markSpiritFlixSmartAnalysisReviewed,
  runSpiritFlixSmartReviewPipeline,
  saveSpiritFlixSmartAnalysisReview,
  type SpiritFlixSmartReviewOptions,
} from "./review";
import { isSpiritFlixSmartVideoExtension } from "./probe";
import { projectApprovedSmartMetadata } from "./metadata-bridge";
import type { SpiritFlixSmartAnalysis, SpiritFlixSmartReviewInput } from "./types";

export type SpiritFlixSmartBatchItemStatus =
  | "candidate"
  | "analyzed"
  | "skipped"
  | "already_current"
  | "failed";

export interface SpiritFlixSmartBatchItem {
  path: string;
  name: string;
  parentPath: string;
  extension?: string;
  status: SpiritFlixSmartBatchItemStatus;
  reason?: string;
  analysisStatus?: SpiritFlixSmartAnalysis["status"];
  reviewStatus?: string;
  sidecarCurrent: boolean;
  needsReview: boolean;
  suggestedTagCount: number;
  renamePreviewAvailable: boolean;
  analyzedAt?: string;
}

export interface SpiritFlixSmartBatchCounts {
  candidates: number;
  analyzed: number;
  skipped: number;
  already_current: number;
  failed: number;
  needs_review: number;
  rename_preview_available: number;
}

export interface SpiritFlixSmartBatchPreview {
  schema: "spiritflix-smart-batch/v1";
  generatedAt: string;
  mode: "preview" | "run";
  rootPath: string;
  recursive: boolean;
  maxItems: number;
  items: SpiritFlixSmartBatchItem[];
  counts: SpiritFlixSmartBatchCounts;
}

export interface SpiritFlixSmartBatchOptions extends SpiritFlixSmartReviewOptions {
  path?: string;
  paths?: string[];
  recursive?: boolean;
  maxItems?: number;
  force?: boolean;
}

export type SpiritFlixSmartBatchReviewMode =
  | "approve_all_tags"
  | "reject_all_tags"
  | "mark_reviewed";

export interface SpiritFlixSmartBatchReviewOptions extends SpiritFlixSmartBatchOptions {
  reviewMode: SpiritFlixSmartBatchReviewMode;
}

type AnalyzeVideo = typeof runSpiritFlixSmartReviewPipeline;

interface InternalBatchOptions extends SpiritFlixSmartBatchOptions {
  analyzeVideo?: AnalyzeVideo;
}

interface BatchTarget {
  videoPath: string;
  mediaRoot?: string;
}

const DEFAULT_BATCH_LIMIT = 12;
const MAX_BATCH_LIMIT = 50;

function boundedLimit(value: number | undefined): number {
  if (!Number.isFinite(value ?? NaN)) return DEFAULT_BATCH_LIMIT;
  return Math.max(1, Math.min(MAX_BATCH_LIMIT, Math.floor(value ?? DEFAULT_BATCH_LIMIT)));
}

function emptyCounts(): SpiritFlixSmartBatchCounts {
  return {
    candidates: 0,
    analyzed: 0,
    skipped: 0,
    already_current: 0,
    failed: 0,
    needs_review: 0,
    rename_preview_available: 0,
  };
}

function bump(counts: SpiritFlixSmartBatchCounts, item: SpiritFlixSmartBatchItem) {
  if (item.status === "candidate") counts.candidates += 1;
  if (item.status === "analyzed") counts.analyzed += 1;
  if (item.status === "skipped") counts.skipped += 1;
  if (item.status === "already_current") counts.already_current += 1;
  if (item.status === "failed") counts.failed += 1;
  if (item.needsReview) counts.needs_review += 1;
  if (item.renamePreviewAvailable) counts.rename_preview_available += 1;
}

function summarize(items: SpiritFlixSmartBatchItem[]): SpiritFlixSmartBatchCounts {
  const counts = emptyCounts();
  for (const item of items) bump(counts, item);
  return counts;
}

function safeMessage(error: unknown): string {
  if (!(error instanceof Error)) return "Smart batch item failed.";
  return error.message.split(/\n\s+at\s+/)[0].slice(0, 500);
}

function isHiddenPathPart(name: string): boolean {
  return name.startsWith(".");
}

async function enumerateFolder(folderPath: string, recursive: boolean, maxItems: number, mediaRoot?: string): Promise<BatchTarget[]> {
  const found: BatchTarget[] = [];
  const pending = [folderPath];

  while (pending.length > 0 && found.length < maxItems) {
    const current = pending.shift()!;
    const entries = await fs.readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      if (isHiddenPathPart(entry.name)) continue;
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

async function resolveBatchTargets(options: SpiritFlixSmartBatchOptions): Promise<{ rootPath: string; targets: BatchTarget[] }> {
  const maxItems = boundedLimit(options.maxItems);
  const requestedPaths = (options.paths ?? []).map((entry) => entry.trim()).filter(Boolean);

  if (requestedPaths.length > 0) {
    const targets: BatchTarget[] = [];
    for (const requested of requestedPaths.slice(0, maxItems)) {
      const { allowedRoot, realPath } = await resolveSpiritFlixAdminPath(requested);
      const stat = await fs.stat(realPath);
      if (stat.isFile() && isSpiritFlixSmartVideoExtension(path.extname(realPath).toLowerCase())) {
        targets.push({ videoPath: realPath, mediaRoot: options.mediaRoot ?? allowedRoot });
      }
    }
    return { rootPath: path.dirname(targets[0]?.videoPath ?? requestedPaths[0]), targets };
  }

  const { allowedRoot, realPath } = await resolveSpiritFlixAdminPath(options.path);
  const mediaRoot = options.mediaRoot ?? allowedRoot;
  const stat = await fs.stat(realPath);
  if (stat.isFile()) {
    return {
      rootPath: path.dirname(realPath),
      targets: isSpiritFlixSmartVideoExtension(path.extname(realPath).toLowerCase()) ? [{ videoPath: realPath, mediaRoot }] : [],
    };
  }
  if (!stat.isDirectory()) {
    throw new Error("Smart batch analysis requires a folder or video selection.");
  }
  return {
    rootPath: realPath,
    targets: await enumerateFolder(realPath, Boolean(options.recursive), maxItems, mediaRoot),
  };
}

async function itemFromAnalysis(videoPath: string, analysis: SpiritFlixSmartAnalysis | null, status: SpiritFlixSmartBatchItemStatus, reason?: string): Promise<SpiritFlixSmartBatchItem> {
  const stat = await fs.stat(videoPath);
  const reviewed = analysis?.reviewedMetadata;
  let renamePreviewAvailable = false;
  if (analysis && reviewed && reviewed.reviewStatus !== "unreviewed") {
    const projection = projectApprovedSmartMetadata(analysis);
    if (projection.filenameSuggestion) {
      renamePreviewAvailable = buildSmartRenamePreviewDraft({
        sourcePath: videoPath,
        filenameSuggestion: projection.filenameSuggestion,
      }).readyForLevel2Preview;
    }
  }

  return {
    path: videoPath,
    name: path.basename(videoPath),
    parentPath: path.dirname(videoPath),
    extension: path.extname(videoPath).toLowerCase(),
    status,
    reason,
    analysisStatus: analysis?.status,
    reviewStatus: reviewed?.reviewStatus ?? "unreviewed",
    sidecarCurrent: Boolean(analysis),
    needsReview: Boolean(analysis?.safety.requiresHumanReview || analysis?.status === "needs_review"),
    suggestedTagCount: analysis?.suggestedTags.length ?? 0,
    renamePreviewAvailable,
    analyzedAt: analysis?.analyzedAt,
  };
}

async function loadCurrentAnalysis(videoPath: string, mediaRoot?: string): Promise<SpiritFlixSmartAnalysis | null> {
  const stat = await fs.stat(videoPath);
  return readSmartAnalysis(
    {
      videoPath,
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
    },
    mediaRoot ? { mediaRoot } : undefined,
  );
}

export async function previewSpiritFlixSmartBatch(options: SpiritFlixSmartBatchOptions = {}): Promise<SpiritFlixSmartBatchPreview> {
  const maxItems = boundedLimit(options.maxItems);
  const { rootPath, targets } = await resolveBatchTargets({ ...options, maxItems });
  const items: SpiritFlixSmartBatchItem[] = [];

  for (const { videoPath, mediaRoot } of targets) {
    try {
      const analysis = await loadCurrentAnalysis(videoPath, mediaRoot);
      items.push(await itemFromAnalysis(videoPath, analysis, analysis ? "already_current" : "candidate"));
    } catch (error) {
      items.push({
        path: videoPath,
        name: path.basename(videoPath),
        parentPath: path.dirname(videoPath),
        extension: path.extname(videoPath).toLowerCase(),
        status: "failed",
        reason: safeMessage(error),
        sidecarCurrent: false,
        needsReview: false,
        suggestedTagCount: 0,
        renamePreviewAvailable: false,
      });
    }
  }

  return {
    schema: "spiritflix-smart-batch/v1",
    generatedAt: new Date().toISOString(),
    mode: "preview",
    rootPath,
    recursive: Boolean(options.recursive),
    maxItems,
    items,
    counts: summarize(items),
  };
}

export async function runSpiritFlixSmartBatch(options: InternalBatchOptions = {}): Promise<SpiritFlixSmartBatchPreview> {
  const maxItems = boundedLimit(options.maxItems);
  const { rootPath, targets } = await resolveBatchTargets({ ...options, maxItems });
  const analyzeVideo = options.analyzeVideo ?? runSpiritFlixSmartReviewPipeline;
  const items: SpiritFlixSmartBatchItem[] = [];

  for (const { videoPath, mediaRoot } of targets) {
    try {
      const current = await loadCurrentAnalysis(videoPath, mediaRoot);
      if (current && !options.force) {
        items.push(await itemFromAnalysis(videoPath, current, "already_current", "Current analysis sidecar already exists."));
        continue;
      }

      const beforeReview = current?.reviewedMetadata;
      const analysis = await analyzeVideo(videoPath, {
        mediaRoot,
        ffprobePath: options.ffprobePath,
        ffmpegPath: options.ffmpegPath,
        maxSamples: options.maxSamples,
        probeTimeoutMs: options.probeTimeoutMs,
        frameTimeoutMs: options.frameTimeoutMs,
      });
      const preservedReview = beforeReview && analysis.reviewedMetadata?.reviewedAt === beforeReview.reviewedAt;
      const reason = beforeReview && !preservedReview ? "Analysis refreshed; review metadata changed." : undefined;
      items.push(await itemFromAnalysis(videoPath, analysis, "analyzed", reason));
    } catch (error) {
      items.push({
        path: videoPath,
        name: path.basename(videoPath),
        parentPath: path.dirname(videoPath),
        extension: path.extname(videoPath).toLowerCase(),
        status: "failed",
        reason: safeMessage(error),
        sidecarCurrent: false,
        needsReview: false,
        suggestedTagCount: 0,
        renamePreviewAvailable: false,
      });
    }
  }

  return {
    schema: "spiritflix-smart-batch/v1",
    generatedAt: new Date().toISOString(),
    mode: "run",
    rootPath,
    recursive: Boolean(options.recursive),
    maxItems,
    items,
    counts: summarize(items),
  };
}

function batchReviewInput(
  analysis: SpiritFlixSmartAnalysis,
  reviewMode: Exclude<SpiritFlixSmartBatchReviewMode, "mark_reviewed">,
): SpiritFlixSmartReviewInput {
  const reviewed = analysis.reviewedMetadata;
  const preservedEdits = {
    editedDisplayTitle: reviewed?.editedDisplayTitle,
    editedFilenameSuggestion: reviewed?.editedFilenameSuggestion,
    editedCategory: reviewed?.editedCategory,
    editedCollections: reviewed?.editedCollections,
    notes: reviewed?.notes,
  };
  const suggestedIds = analysis.suggestedTags.map((tag) => tag.id);
  if (reviewMode === "approve_all_tags") {
    return {
      ...preservedEdits,
      approvedTagIds: suggestedIds,
      rejectedTagIds: [],
    };
  }

  return {
    ...preservedEdits,
    approvedTagIds: [],
    rejectedTagIds: suggestedIds,
  };
}

export async function reviewSpiritFlixSmartBatch(
  options: SpiritFlixSmartBatchReviewOptions,
): Promise<SpiritFlixSmartBatchPreview> {
  const maxItems = boundedLimit(options.maxItems);
  const { rootPath, targets } = await resolveBatchTargets({ ...options, maxItems });
  const items: SpiritFlixSmartBatchItem[] = [];

  for (const { videoPath, mediaRoot } of targets) {
    try {
      const current = await loadCurrentAnalysis(videoPath, mediaRoot);
      if (!current) {
        items.push(await itemFromAnalysis(videoPath, null, "skipped", "No smart analysis sidecar exists to review."));
        continue;
      }

      const analysis = options.reviewMode === "mark_reviewed"
        ? await markSpiritFlixSmartAnalysisReviewed(videoPath, { mediaRoot })
        : await saveSpiritFlixSmartAnalysisReview(
            videoPath,
            batchReviewInput(current, options.reviewMode),
            { mediaRoot },
          );

      items.push(await itemFromAnalysis(videoPath, analysis, "analyzed", `Batch ${options.reviewMode.replace(/_/g, " ")} saved.`));
    } catch (error) {
      items.push({
        path: videoPath,
        name: path.basename(videoPath),
        parentPath: path.dirname(videoPath),
        extension: path.extname(videoPath).toLowerCase(),
        status: "failed",
        reason: safeMessage(error),
        sidecarCurrent: false,
        needsReview: false,
        suggestedTagCount: 0,
        renamePreviewAvailable: false,
      });
    }
  }

  return {
    schema: "spiritflix-smart-batch/v1",
    generatedAt: new Date().toISOString(),
    mode: "run",
    rootPath,
    recursive: Boolean(options.recursive),
    maxItems,
    items,
    counts: summarize(items),
  };
}
