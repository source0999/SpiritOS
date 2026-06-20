// ── SpiritFlix S3 review-only suggestion builder ─────────────────────
// Writes analysis sidecar suggestions only. Never mutates media.

import fs from "node:fs/promises";
import path from "node:path";
import { assertSmartVideoPathCandidate } from "./analysis-paths";
import {
  createEmptySmartAnalysis,
  readSmartAnalysis,
  writeSmartAnalysis,
} from "./analysis-store";
import {
  buildHeuristicNotes,
  inferCategoryHint,
  inferFormatTags,
  inferQualityTags,
  inferSourceTags,
  isAmbiguousSpiritFlixFilename,
  isPrimarySmartContentTag,
  isRandomOrHashSpiritFlixFilename,
  isTechnicalOrStatusTag,
  modelIdentityFromPath,
  normalizeSpiritFlixTitle,
  stripVideoExtension,
  titleCaseSlug,
  unknownModelIdentity,
  type SpiritFlixSmartHeuristicInput,
} from "./heuristics";
import {
  validateSpiritFlixSmartAnalysis,
  type SpiritFlixSmartAnalysis,
  type SpiritFlixSmartContentTagEvidence,
  type SpiritFlixSmartPerformerIdentity,
  type SpiritFlixSmartTag,
} from "./types";

export const SPIRITFLIX_SMART_ANALYZER_VERSION_S3 = "spiritflix-smart/s3";

const MAX_FILENAME_STEM_LENGTH = 120;
const UNSAFE_FILENAME_CHARS = /[\\/:*?"<>|]/g;
const FACE_VERIFICATION_RELATIVE_PATH = path.join("scripts", "media", "performer_verification.json");

export interface SpiritFlixSmartSuggestionResult {
  suggestedTags: SpiritFlixSmartTag[];
  suggestedCategory?: string;
  suggestedCollections: string[];
  suggestedDisplayTitle?: string;
  suggestedFilename?: string;
  contentTagEvidence: SpiritFlixSmartContentTagEvidence[];
  performerIdentity: SpiritFlixSmartPerformerIdentity;
  suggestedFilenameReason: string;
  confidence: number;
  notes: string[];
}

function pathOptions(mediaRoot?: string) {
  return mediaRoot ? { mediaRoot } : undefined;
}

function dedupeTags(tags: SpiritFlixSmartTag[]): SpiritFlixSmartTag[] {
  const byId = new Map<string, SpiritFlixSmartTag>();
  for (const tag of tags) {
    const existing = byId.get(tag.id);
    if (!existing || tag.confidence > existing.confidence) {
      byId.set(tag.id, tag);
    }
  }
  return [...byId.values()];
}

function averageConfidence(tags: SpiritFlixSmartTag[]): number {
  if (tags.length === 0) return 0.2;
  const total = tags.reduce((sum, tag) => sum + tag.confidence, 0);
  return Math.min(1, Math.max(0, total / tags.length));
}

function sanitizeFilenameStem(value: string): string {
  const cleaned = value
    .replace(UNSAFE_FILENAME_CHARS, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, MAX_FILENAME_STEM_LENGTH);
  return cleaned || "untitled";
}

function topContentLabels(tags: SpiritFlixSmartTag[]): string[] {
  return tags
    .filter(isPrimarySmartContentTag)
    .sort((left, right) => right.confidence - left.confidence)
    .slice(0, 3)
    .map((tag) => tag.label.toLowerCase());
}

function sourceSequence(input: SpiritFlixSmartHeuristicInput): string {
  if (input.modelSequenceNumber && Number.isFinite(input.modelSequenceNumber) && input.modelSequenceNumber > 0) {
    return String(Math.floor(input.modelSequenceNumber)).padStart(2, "0");
  }
  return "01";
}

function nameDescriptorLabels(tags: SpiritFlixSmartTag[]): string[] {
  const nameworthyIds = new Set([
    "hotel-room",
    "threesome",
    "traditional-dress",
    "dress",
    "smoking",
    "toy",
    "oral",
    "manual",
    "intercourse",
    "anal",
    "lesbian",
    "massage",
    "riding",
    "missionary",
    "doggy",
    "standing",
    "seated",
    "cosplay",
    "pov",
    "watermark",
  ]);
  const labels = tags
    .filter((tag) => isPrimarySmartContentTag(tag) && nameworthyIds.has(tag.id))
    .sort((left, right) => right.confidence - left.confidence)
    .filter((tag, _index, sorted) => !(tag.id === "dress" && sorted.some((entry) => entry.id === "traditional-dress")))
    .slice(0, 3)
    .map((tag) => tag.label.toLowerCase());
  return labels;
}

function readableTitle(input: SpiritFlixSmartHeuristicInput): string {
  const title = normalizeSpiritFlixTitle(input.fileName) || stripVideoExtension(input.fileName);
  return sanitizeFilenameStem(title);
}

function shouldUseFallbackName(input: SpiritFlixSmartHeuristicInput): boolean {
  const title = readableTitle(input);
  const compact = title.replace(/[^a-z0-9]/gi, "");
  const normalized = title.toLowerCase();
  if (/\bvisit\b.*\bmore\b/.test(normalized)) return true;
  if (/\bonlyshare\b|\bonlyfans\b|\bfansly\b/.test(normalized)) return true;
  if (isRandomOrHashSpiritFlixFilename(input)) return true;
  if (!compact || compact.length < 3) return true;
  if (/^\d+$/.test(compact)) return true;
  return false;
}

export function buildSuggestedFilename(
  input: SpiritFlixSmartHeuristicInput,
  tags: SpiritFlixSmartTag[],
  performerIdentity: SpiritFlixSmartPerformerIdentity = modelIdentityFromPath(input) ?? unknownModelIdentity(),
): string {
  const modelName = sanitizeFilenameStem(performerIdentity.name || "Unknown Model");
  const sequence = sourceSequence(input);
  const hasKnownModel = performerIdentity.source !== "unknown";
  if (!shouldUseFallbackName(input)) {
    return hasKnownModel
      ? sanitizeFilenameStem(`${modelName} ${sequence} - ${readableTitle(input)}`)
      : readableTitle(input);
  }

  const descriptor = nameDescriptorLabels(tags).join(" ");
  if (descriptor) {
    return hasKnownModel
      ? sanitizeFilenameStem(`${modelName} ${sequence} - ${descriptor}`)
      : sanitizeFilenameStem(`${modelName} - ${descriptor} ${sequence}`);
  }

  return hasKnownModel
    ? sanitizeFilenameStem(`${modelName} ${sequence} - Untitled`)
    : sanitizeFilenameStem(`${modelName} - Untitled ${sequence}`);
}

function filenameReason(input: SpiritFlixSmartHeuristicInput, tags: SpiritFlixSmartTag[], performerIdentity: SpiritFlixSmartPerformerIdentity): string {
  if (!shouldUseFallbackName(input)) {
    return "Readable source title preserved with model-folder sequence; extension is kept only for target-path preview.";
  }
  if (nameDescriptorLabels(tags).length > 0) {
    return `${performerIdentity.name} fallback uses a short visual descriptor and model-folder sequence; extension is kept only for target-path preview.`;
  }
  if (topContentLabels(tags).length > 0) {
    return `${performerIdentity.name} fallback has reviewable tags but no title-worthy descriptor; extension is kept only for target-path preview.`;
  }
  return `${performerIdentity.name} fallback uses model identity with Untitled because the filename is random or ambiguous.`;
}

function tagsFromSamples(analysis: SpiritFlixSmartAnalysis | undefined): SpiritFlixSmartTag[] {
  return dedupeTags((analysis?.samples ?? []).flatMap((sample) => sample.tags).filter(isPrimarySmartContentTag));
}

function contentEvidenceFor(
  input: SpiritFlixSmartHeuristicInput,
  tags: SpiritFlixSmartTag[],
  technicalTags: SpiritFlixSmartTag[],
  analysis: SpiritFlixSmartAnalysis | undefined,
  performerIdentity: SpiritFlixSmartPerformerIdentity,
): SpiritFlixSmartContentTagEvidence[] {
  const frameEvidenceTags = tagsFromSamples(analysis).map((tag) => tag.id);
  const firstFrameRef = analysis?.samples.find((sample) => sample.cacheKey)?.cacheKey ?? null;
  const existingVisualEvidence = (analysis?.contentTagEvidence ?? []).filter((entry) => entry.source === "vlm" || entry.source === "ocr");
  return [
    {
      source: "filename",
      tags: tags.filter((tag) => tag.evidenceTimestamps.length === 0).map((tag) => tag.id),
      confidence: tags.length > 0 ? averageConfidence(tags) : 0.2,
      evidenceRef: path.basename(input.fileName),
      requiresReview: true,
    },
    {
      source: "path",
      tags: performerIdentity.source === "path" ? [performerIdentity.name] : [],
      confidence: performerIdentity.source === "path" ? performerIdentity.confidence : 0.2,
      evidenceRef: performerIdentity.evidenceRef ?? input.parentPath ?? null,
      requiresReview: true,
    },
    {
      source: "metadata",
      tags: technicalTags.map((tag) => tag.id),
      confidence: technicalTags.length > 0 ? averageConfidence(technicalTags) : 0.2,
      evidenceRef: null,
      requiresReview: true,
    },
    {
      source: "frame_sample",
      tags: frameEvidenceTags,
      confidence: frameEvidenceTags.length > 0 ? averageConfidence(tagsFromSamples(analysis)) : 0,
      evidenceRef: firstFrameRef,
      requiresReview: true,
    },
    ...existingVisualEvidence,
  ];
}

function suggestionsFromExistingFrameEvidence(analysis: SpiritFlixSmartAnalysis | undefined): SpiritFlixSmartTag[] {
  return tagsFromSamples(analysis);
}

function hasAmbiguousFilename(input: SpiritFlixSmartHeuristicInput): boolean {
  return isAmbiguousSpiritFlixFilename(input);
}

function normalizeIdentityPath(value: string): string {
  return value
    .replace(/\\/g, "/")
    .replace(/^\/mnt\/spirit-8tb\/media\/yes(?=\/|$)/i, "/DATA/yes")
    .replace(/^\/media\/yes(?=\/|$)/i, "/DATA/yes")
    .replace(/^\/home\/source\/SpiritOS\/DATA\/yes(?=\/|$)/i, "/DATA/yes")
    .toLowerCase();
}

function safeEvidenceSource(source: string | undefined): boolean {
  return Boolean(source && /manual|confirmed|face/i.test(source));
}

async function findReadOnlyFacePerformerIdentity(input: SpiritFlixSmartHeuristicInput): Promise<SpiritFlixSmartPerformerIdentity | undefined> {
  const evidencePath = path.join(process.cwd(), FACE_VERIFICATION_RELATIVE_PATH);
  let raw: string;
  try {
    raw = await fs.readFile(evidencePath, "utf8");
  } catch {
    return undefined;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return undefined;
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return undefined;
  const performers = (parsed as { performers?: unknown }).performers;
  if (!performers || typeof performers !== "object" || Array.isArray(performers)) return undefined;

  const target = normalizeIdentityPath(input.videoPath);
  let best: SpiritFlixSmartPerformerIdentity | undefined;
  for (const performer of Object.values(performers as Record<string, unknown>)) {
    if (!performer || typeof performer !== "object" || Array.isArray(performer)) continue;
    const record = performer as { name?: unknown; slug?: unknown; evidence?: unknown };
    const name = typeof record.name === "string" && record.name.trim()
      ? record.name.trim()
      : typeof record.slug === "string"
        ? titleCaseSlug(record.slug)
        : "";
    if (!name || !Array.isArray(record.evidence)) continue;

    for (const evidence of record.evidence) {
      if (!evidence || typeof evidence !== "object" || Array.isArray(evidence)) continue;
      const evidenceRecord = evidence as { video_path?: unknown; source?: unknown; confidence?: unknown; frame_path?: unknown; sidecar_path?: unknown };
      if (typeof evidenceRecord.video_path !== "string") continue;
      if (normalizeIdentityPath(evidenceRecord.video_path) !== target) continue;
      if (!safeEvidenceSource(typeof evidenceRecord.source === "string" ? evidenceRecord.source : undefined)) continue;
      const confidence = typeof evidenceRecord.confidence === "number" && Number.isFinite(evidenceRecord.confidence)
        ? Math.max(0, Math.min(1, evidenceRecord.confidence))
        : 0.7;
      const candidate: SpiritFlixSmartPerformerIdentity = {
        name,
        source: "face_rec",
        confidence,
        evidenceRef:
          (typeof evidenceRecord.sidecar_path === "string" && evidenceRecord.sidecar_path) ||
          (typeof evidenceRecord.frame_path === "string" && evidenceRecord.frame_path) ||
          FACE_VERIFICATION_RELATIVE_PATH,
        requiresReview: confidence < 0.95,
      };
      if (!best || candidate.confidence > best.confidence) best = candidate;
    }
  }

  return best;
}

export function buildSpiritFlixReviewSuggestions(
  input: SpiritFlixSmartHeuristicInput,
  options?: { analysis?: SpiritFlixSmartAnalysis; performerIdentity?: SpiritFlixSmartPerformerIdentity },
): SpiritFlixSmartSuggestionResult {
  const performerIdentity = options?.performerIdentity ?? modelIdentityFromPath(input) ?? unknownModelIdentity();
  const technicalTags = dedupeTags([
    ...inferQualityTags(input),
    ...inferFormatTags(input),
    ...inferSourceTags(input),
  ]).filter(isTechnicalOrStatusTag);
  const suggestedTags = dedupeTags(suggestionsFromExistingFrameEvidence(options?.analysis).filter(isPrimarySmartContentTag));
  const suggestedCategory = inferCategoryHint(input);
  const suggestedDisplayTitle = buildSuggestedFilename(input, suggestedTags, performerIdentity);
  const suggestedFilename = suggestedDisplayTitle;
  const confidence = suggestedTags.length > 0 ? averageConfidence(suggestedTags) : Math.max(0.2, performerIdentity.confidence * 0.6);
  const notes = buildHeuristicNotes(input);
  const suggestedFilenameReason = filenameReason(input, suggestedTags, performerIdentity);
  notes.push(suggestedFilenameReason);
  if (suggestedTags.length > 0) {
    notes.push("Visual content tags came from sampled-frame evidence and require operator review before confirm.");
  } else {
    notes.push("No sampled-frame content tags were produced; recommendations fall back to title, path, metadata, and face-rec evidence.");
  }
  if (technicalTags.length > 0) {
    notes.push(`technical metadata kept out of primary smart tags: ${technicalTags.map((tag) => tag.label).join(", ")}`);
  }
  if (performerIdentity.source === "face_rec") {
    notes.push(`performer identity from read-only face evidence: ${performerIdentity.name}`);
  } else if (performerIdentity.source === "path") {
    notes.push(`performer identity from model folder: ${performerIdentity.name}`);
  }

  if (hasAmbiguousFilename(input)) {
    notes.push("needs title cleanup status set; not emitted as a primary smart tag");
  }

  return {
    suggestedTags,
    suggestedCategory,
    suggestedCollections: suggestedCategory ? [suggestedCategory] : [],
    suggestedDisplayTitle,
    suggestedFilename,
    contentTagEvidence: contentEvidenceFor(input, suggestedTags, technicalTags, options?.analysis, performerIdentity),
    performerIdentity,
    suggestedFilenameReason,
    confidence,
    notes,
  };
}

function mergeNotes(existing: string | undefined, additions: string[]): string {
  const parts = new Set<string>();
  if (existing?.trim()) parts.add(existing.trim());
  for (const note of additions) {
    if (note.trim()) parts.add(note.trim());
  }
  return [...parts].join(" | ").slice(0, 8_000);
}

export function applySpiritFlixReviewSuggestionsToAnalysis(
  analysis: SpiritFlixSmartAnalysis,
  suggestions: SpiritFlixSmartSuggestionResult,
): SpiritFlixSmartAnalysis {
  const ambiguous = suggestions.suggestedTags.some((tag) => tag.reviewRequired) || suggestions.confidence < 0.55;
  const status = ambiguous ? "needs_review" : "suggested";

  return validateSpiritFlixSmartAnalysis({
    ...analysis,
    analyzedAt: new Date().toISOString(),
    analyzerVersion: SPIRITFLIX_SMART_ANALYZER_VERSION_S3,
    status,
    safety: {
      safeToSuggest: false,
      reasons: ["Heuristic suggestions require human review before any Level 2 action."],
      requiresHumanReview: true,
    },
    media: analysis.media,
    samples: analysis.samples,
    contentTagEvidence: suggestions.contentTagEvidence,
    performerIdentity: suggestions.performerIdentity,
    suggestedTags: suggestions.suggestedTags,
    pendingSmartTags: suggestions.suggestedTags,
    suggestedCategory: suggestions.suggestedCategory,
    suggestedCollections: suggestions.suggestedCollections.length > 0 ? suggestions.suggestedCollections : undefined,
    suggestedDisplayTitle: suggestions.suggestedDisplayTitle,
    suggestedFilename: suggestions.suggestedFilename,
    pendingDisplayName: suggestions.suggestedDisplayTitle,
    confidence: suggestions.confidence,
    notes: mergeNotes(analysis.notes, suggestions.notes),
  });
}

export async function updateSmartAnalysisWithHeuristicSuggestions(
  input: SpiritFlixSmartHeuristicInput,
  options?: { mediaRoot?: string },
): Promise<SpiritFlixSmartAnalysis> {
  const pathOpts = pathOptions(options?.mediaRoot);
  const videoPath = assertSmartVideoPathCandidate(input.videoPath, pathOpts);

  let fileSizeBytes = input.fileSizeBytes;
  let mtimeMs = input.mtimeMs;
  if (fileSizeBytes === undefined || mtimeMs === undefined) {
    const stat = await fs.stat(videoPath);
    fileSizeBytes = stat.size;
    mtimeMs = stat.mtimeMs;
  }

  const pathInput = { videoPath, fileSizeBytes, mtimeMs };
  const existing = await readSmartAnalysis(pathInput, pathOpts);
  const base =
    existing ??
    createEmptySmartAnalysis(
      {
        videoPath,
        fileName: input.fileName,
        fileSizeBytes,
        mtimeMs,
        analyzerVersion: SPIRITFLIX_SMART_ANALYZER_VERSION_S3,
      },
      pathOpts,
    );

  const heuristicInput: SpiritFlixSmartHeuristicInput = {
    ...input,
    videoPath,
    fileName: input.fileName,
    parentPath: input.parentPath ?? path.dirname(videoPath),
    fileSizeBytes,
    mtimeMs,
    media: input.media ?? base.media,
  };

  const performerIdentity =
    await findReadOnlyFacePerformerIdentity(heuristicInput) ??
    modelIdentityFromPath(heuristicInput) ??
    unknownModelIdentity();
  const suggestions = buildSpiritFlixReviewSuggestions(heuristicInput, {
    analysis: base,
    performerIdentity,
  });
  const updated = applySpiritFlixReviewSuggestionsToAnalysis(base, suggestions);
  const { analysis } = await writeSmartAnalysis(updated, pathOpts);
  return analysis;
}
