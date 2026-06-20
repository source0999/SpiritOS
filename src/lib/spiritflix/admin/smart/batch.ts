// SpiritFlix smart batch analysis (S7)
// Folder/selection orchestration only. Writes analysis sidecars; never renames or moves media.

import fs from "node:fs/promises";
import path from "node:path";
import { resolveSpiritFlixAdminPath } from "../paths";
import { readSmartAnalysis, writeSmartAnalysis } from "./analysis-store";
import { buildSmartRenamePreviewDraft } from "./rename-preview";
import {
  markSpiritFlixSmartAnalysisReviewed,
  runSpiritFlixSmartReviewPipeline,
  saveSpiritFlixSmartAnalysisReview,
  type SpiritFlixSmartReviewOptions,
} from "./review";
import { isSpiritFlixSmartVideoExtension } from "./probe";
import { projectApprovedSmartMetadata } from "./metadata-bridge";
import {
  inferFormatTags,
  inferQualityTags,
  isPrimarySmartContentTag,
  isTechnicalOrStatusTag,
  modelIdentityFromPath,
  unknownModelIdentity,
} from "./heuristics";
import type { SpiritFlixSmartAnalysis, SpiritFlixSmartReviewInput, SpiritFlixSmartTag } from "./types";

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
  tags: SpiritFlixSmartBatchTagSummary[];
  qualityBadges: SpiritFlixSmartBatchTagSummary[];
  modelName: string;
  modelSource: string;
  nameReason?: string;
  visualTaggingAvailable: boolean;
  approvedTagCount: number;
  rejectedTagCount: number;
  pendingTagCount: number;
  renamePreviewAvailable: boolean;
  renamePreviewStatus: SpiritFlixSmartBatchRenamePreviewStatus;
  proposedFilename?: string;
  proposedTargetPath?: string;
  renameBlocker?: string;
  renameWarnings: string[];
  sidecarRef?: string;
  analyzedAt?: string;
}

export type SpiritFlixSmartBatchRenamePreviewStatus =
  | "ready"
  | "provisional"
  | "needs_review"
  | "missing_suggestion"
  | "blocked"
  | "unavailable";

export interface SpiritFlixSmartBatchTagSummary {
  id: string;
  label: string;
  group: string;
  confidence: number;
  reviewRequired: boolean;
  reviewState: "approved" | "rejected" | "pending";
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
  visualContentTaggingEnabled: boolean;
  visualContentTaggingMessage: string;
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

function isLegacyVisualSidecar(analysis: SpiritFlixSmartAnalysis | null): boolean {
  return Boolean(analysis && analysis.visualAnalysis === undefined);
}

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

function reviewStateForTag(
  tagId: string,
  reviewed: SpiritFlixSmartAnalysis["reviewedMetadata"],
): SpiritFlixSmartBatchTagSummary["reviewState"] {
  if (reviewed?.approvedTagIds.includes(tagId)) return "approved";
  if (reviewed?.rejectedTagIds.includes(tagId)) return "rejected";
  return "pending";
}

function summarizeTag(
  tag: SpiritFlixSmartTag,
  reviewed: SpiritFlixSmartAnalysis["reviewedMetadata"],
): SpiritFlixSmartBatchTagSummary {
  return {
    id: tag.id,
    label: tag.label,
    group: tag.group,
    confidence: tag.confidence,
    reviewRequired: tag.reviewRequired,
    reviewState: reviewStateForTag(tag.id, reviewed),
  };
}

function dedupeBatchTags(tags: SpiritFlixSmartBatchTagSummary[]): SpiritFlixSmartBatchTagSummary[] {
  const byId = new Map<string, SpiritFlixSmartBatchTagSummary>();
  for (const tag of tags) {
    const existing = byId.get(tag.id);
    if (!existing || tag.confidence > existing.confidence) byId.set(tag.id, tag);
  }
  return [...byId.values()].sort((left, right) => left.label.localeCompare(right.label));
}

function stripExtensionForDisplay(value: string, sourcePath: string): string {
  const sourceExtension = path.extname(sourcePath).toLowerCase();
  const suggestedExtension = path.extname(value).toLowerCase();
  if (sourceExtension && suggestedExtension === sourceExtension) {
    return value.slice(0, -suggestedExtension.length).trim();
  }
  return value.trim();
}

function analysisVisualTagsAvailable(analysis: SpiritFlixSmartAnalysis | null): boolean {
  return Boolean(
    analysis?.contentTagEvidence?.some(
      (entry) => ["face_rec", "frame_sample", "ocr", "vlm"].includes(entry.source) && entry.tags.length > 0,
    ),
  );
}

function summarizeTechnicalBadges(
  videoPath: string,
  analysis: SpiritFlixSmartAnalysis | null,
): SpiritFlixSmartBatchTagSummary[] {
  const reviewed = analysis?.reviewedMetadata;
  const input = {
    videoPath,
    fileName: path.basename(videoPath),
    parentPath: path.dirname(videoPath),
    media: analysis?.media,
  };
  const derived = [...inferQualityTags(input), ...inferFormatTags(input)];
  const stored = (analysis?.suggestedTags ?? []).filter(isTechnicalOrStatusTag);
  return dedupeBatchTags([...stored, ...derived].map((tag) => summarizeTag(tag, reviewed)));
}

function modelIdentityForItem(videoPath: string, analysis: SpiritFlixSmartAnalysis | null) {
  return analysis?.performerIdentity ?? modelIdentityFromPath({
    videoPath,
    fileName: path.basename(videoPath),
    parentPath: path.dirname(videoPath),
    media: analysis?.media,
  }) ?? unknownModelIdentity();
}

function nameReasonForItem(analysis: SpiritFlixSmartAnalysis | null, identityName: string): string | undefined {
  if (!analysis) return undefined;
  const notes = analysis.notes?.split("|").map((entry) => entry.trim()).filter(Boolean) ?? [];
  return notes.find((note) => /extension is kept|fallback uses|Readable title preserved/i.test(note)) ??
    `Recommended name uses ${identityName} identity/title hints; extension is kept only for target-path preview.`;
}

async function targetExists(targetPath: string, sourcePath: string): Promise<boolean> {
  if (path.resolve(targetPath) === path.resolve(sourcePath)) return false;
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
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
  const tags = (analysis?.suggestedTags ?? []).filter(isPrimarySmartContentTag).map((tag) => summarizeTag(tag, reviewed));
  const qualityBadges = summarizeTechnicalBadges(videoPath, analysis);
  const modelIdentity = modelIdentityForItem(videoPath, analysis);
  const approvedTagCount = tags.filter((tag) => tag.reviewState === "approved").length;
  const rejectedTagCount = tags.filter((tag) => tag.reviewState === "rejected").length;
  const pendingTagCount = tags.filter((tag) => tag.reviewState === "pending").length;
  let renamePreviewAvailable = false;
  let renamePreviewStatus: SpiritFlixSmartBatchRenamePreviewStatus = analysis ? "missing_suggestion" : "unavailable";
  let proposedFilename: string | undefined;
  let proposedTargetPath: string | undefined;
  let renameBlocker: string | undefined;
  let renameWarnings: string[] = [];

  if (!analysis) {
    renameBlocker = "Run analysis before rename preview is available.";
  } else if (!reviewed || reviewed.reviewStatus === "unreviewed") {
    const provisionalSuggestion = analysis.suggestedFilename ?? analysis.suggestedDisplayTitle;
    if (provisionalSuggestion) {
      const draft = buildSmartRenamePreviewDraft({ sourcePath: videoPath, filenameSuggestion: provisionalSuggestion });
      proposedFilename = draft.suggestedName ? stripExtensionForDisplay(draft.suggestedName, videoPath) : undefined;
      proposedTargetPath = draft.targetPath;
      renameWarnings = [...draft.warnings, "Provisional preview, not eligible for apply until reviewed."];
      renamePreviewStatus = "provisional";
      renameBlocker = "Review or approve tags/metadata to unlock rename preview.";
    } else {
      renamePreviewStatus = "needs_review";
      renameBlocker = "Review required, and no filename suggestion exists yet.";
    }
  } else {
    const projection = projectApprovedSmartMetadata(analysis);
    const filenameSuggestion = projection.filenameSuggestion;
    if (!filenameSuggestion || projection.reviewStatus === "rejected") {
      renamePreviewStatus = "missing_suggestion";
      renameBlocker = "Reviewed metadata does not contain an approved filename proposal.";
    } else {
      const draft = buildSmartRenamePreviewDraft({
        sourcePath: videoPath,
        filenameSuggestion,
      });
      proposedFilename = draft.suggestedName ? stripExtensionForDisplay(draft.suggestedName, videoPath) : undefined;
      proposedTargetPath = draft.targetPath;
      renameWarnings = [...draft.warnings];
      if (await targetExists(draft.targetPath, videoPath)) {
        renameWarnings.push("Target path already exists.");
      }
      renamePreviewAvailable = draft.readyForLevel2Preview && renameWarnings.length === 0;
      renamePreviewStatus = renamePreviewAvailable ? "ready" : "blocked";
      renameBlocker = renamePreviewAvailable ? undefined : renameWarnings.join(" ") || "Rename preview is blocked.";
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
    tags,
    qualityBadges,
    modelName: modelIdentity.name,
    modelSource: modelIdentity.source,
    nameReason: nameReasonForItem(analysis, modelIdentity.name),
    visualTaggingAvailable: analysisVisualTagsAvailable(analysis),
    approvedTagCount,
    rejectedTagCount,
    pendingTagCount,
    renamePreviewAvailable,
    renamePreviewStatus,
    proposedFilename,
    proposedTargetPath,
    renameBlocker,
    renameWarnings,
    sidecarRef: analysis?.pathKey ? `analysis/${analysis.pathKey.slice(0, 12)}.json` : undefined,
    analyzedAt: analysis?.analyzedAt,
  };
}

function addDuplicateTargetWarnings(items: SpiritFlixSmartBatchItem[]): SpiritFlixSmartBatchItem[] {
  const targetGroups = new Map<string, SpiritFlixSmartBatchItem[]>();
  for (const item of items) {
    if (!item.proposedTargetPath) continue;
    const key = item.proposedTargetPath.toLowerCase();
    targetGroups.set(key, [...(targetGroups.get(key) ?? []), item]);
  }

  for (const group of targetGroups.values()) {
    if (group.length < 2) continue;
    for (const item of group) {
      item.renameWarnings = [...new Set([...item.renameWarnings, "Duplicate target path in this batch."])];
      item.renameBlocker = item.renameWarnings.join(" ");
      if (item.renamePreviewStatus !== "provisional") {
        item.renamePreviewStatus = "blocked";
      }
      item.renamePreviewAvailable = false;
    }
  }

  return items;
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
        tags: [],
        qualityBadges: [],
        modelName: "Unknown Model",
        modelSource: "unknown",
        visualTaggingAvailable: false,
        approvedTagCount: 0,
        rejectedTagCount: 0,
        pendingTagCount: 0,
        renamePreviewAvailable: false,
        renamePreviewStatus: "unavailable",
        renameBlocker: "Batch item failed before rename preview could be prepared.",
        renameWarnings: [],
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
    counts: summarize(addDuplicateTargetWarnings(items)),
    visualContentTaggingEnabled: items.some((item) => item.visualTaggingAvailable),
    visualContentTaggingMessage: "Analyze folder samples frames and asks the local visual model for review-required content tags. No tags or names are applied until confirm.",
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
      const legacyVisualSidecar = isLegacyVisualSidecar(current);
      if (current && !options.force && !legacyVisualSidecar) {
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
        visualAnalysis: options.visualAnalysis,
        visualModel: options.visualModel,
        visualModelTimeoutMs: options.visualModelTimeoutMs,
      });
      const finalAnalysis = legacyVisualSidecar && analysis.visualAnalysis?.tags.length
        ? (await writeSmartAnalysis(
            {
              ...analysis,
              status: "needs_review",
              reviewedMetadata: undefined,
              safety: {
                ...analysis.safety,
                safeToSuggest: false,
                requiresHumanReview: true,
                reasons: [...new Set([...analysis.safety.reasons, "Legacy smart sidecar refreshed with visual tags; operator review required."])],
              },
            },
            mediaRoot ? { mediaRoot } : undefined,
          )).analysis
        : analysis;
      const preservedReview = beforeReview && analysis.reviewedMetadata?.reviewedAt === beforeReview.reviewedAt;
      const reason = beforeReview && !preservedReview ? "Analysis refreshed; review metadata changed." : undefined;
      items.push(await itemFromAnalysis(videoPath, finalAnalysis, "analyzed", legacyVisualSidecar ? "Legacy sidecar refreshed with S9 visual tags." : reason));
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
        tags: [],
        qualityBadges: [],
        modelName: "Unknown Model",
        modelSource: "unknown",
        visualTaggingAvailable: false,
        approvedTagCount: 0,
        rejectedTagCount: 0,
        pendingTagCount: 0,
        renamePreviewAvailable: false,
        renamePreviewStatus: "unavailable",
        renameBlocker: "Batch item failed before rename preview could be prepared.",
        renameWarnings: [],
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
    counts: summarize(addDuplicateTargetWarnings(items)),
    visualContentTaggingEnabled: items.some((item) => item.visualTaggingAvailable),
    visualContentTaggingMessage: items.some((item) => item.visualTaggingAvailable)
      ? "Local sampled-frame content tags are present and waiting for operator review."
      : "Local visual analysis ran or was skipped, but no sampled-frame content tags were produced for this batch.",
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
        tags: [],
        qualityBadges: [],
        modelName: "Unknown Model",
        modelSource: "unknown",
        visualTaggingAvailable: false,
        approvedTagCount: 0,
        rejectedTagCount: 0,
        pendingTagCount: 0,
        renamePreviewAvailable: false,
        renamePreviewStatus: "unavailable",
        renameBlocker: "Batch item failed before rename preview could be prepared.",
        renameWarnings: [],
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
    counts: summarize(addDuplicateTargetWarnings(items)),
    visualContentTaggingEnabled: items.some((item) => item.visualTaggingAvailable),
    visualContentTaggingMessage: items.some((item) => item.visualTaggingAvailable)
      ? "Local sampled-frame content tags are present and waiting for operator review."
      : "No local sampled-frame content tags are currently active in this reviewed batch.",
  };
}
