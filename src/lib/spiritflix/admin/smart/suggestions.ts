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
  inferPerformerTags,
  inferQualityTags,
  inferSourceTags,
  isAmbiguousSpiritFlixFilename,
  normalizeSpiritFlixTitle,
  type SpiritFlixSmartHeuristicInput,
} from "./heuristics";
import { findSmartTagDefinition } from "./vocabulary";
import { validateSpiritFlixSmartAnalysis, type SpiritFlixSmartAnalysis, type SpiritFlixSmartTag } from "./types";

export const SPIRITFLIX_SMART_ANALYZER_VERSION_S3 = "spiritflix-smart/s3";

const MAX_FILENAME_STEM_LENGTH = 120;
const UNSAFE_FILENAME_CHARS = /[\\/:*?"<>|]/g;

export interface SpiritFlixSmartSuggestionResult {
  suggestedTags: SpiritFlixSmartTag[];
  suggestedCategory?: string;
  suggestedCollections: string[];
  suggestedDisplayTitle?: string;
  suggestedFilename?: string;
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

function qualitySuffixForFilename(tags: SpiritFlixSmartTag[]): string | undefined {
  const priority = ["uhd", "full-hd", "hd", "site-token"];
  for (const id of priority) {
    const tag = tags.find((entry) => entry.id === id);
    if (tag) {
      const definition = findSmartTagDefinition(id);
      return definition?.label ?? id;
    }
  }
  return undefined;
}

export function buildSuggestedFilename(input: SpiritFlixSmartHeuristicInput, tags: SpiritFlixSmartTag[]): string {
  const extension = path.extname(input.fileName).toLowerCase() || ".mp4";
  const title = sanitizeFilenameStem(normalizeSpiritFlixTitle(input.fileName));
  const suffix = qualitySuffixForFilename(tags);
  const stem = suffix && suffix !== title ? `${title} - ${suffix}` : title;
  return `${sanitizeFilenameStem(stem)}${extension}`;
}

function hasAmbiguousFilename(input: SpiritFlixSmartHeuristicInput): boolean {
  return isAmbiguousSpiritFlixFilename(input);
}

export function buildSpiritFlixReviewSuggestions(input: SpiritFlixSmartHeuristicInput): SpiritFlixSmartSuggestionResult {
  const suggestedTags = dedupeTags([
    ...inferQualityTags(input),
    ...inferFormatTags(input),
    ...inferSourceTags(input),
    ...inferPerformerTags(input),
  ]);

  if (hasAmbiguousFilename(input)) {
    const needsCleanup = findSmartTagDefinition("needs-title-cleanup");
    if (needsCleanup) {
      suggestedTags.push({
        id: needsCleanup.id,
        label: needsCleanup.label,
        group: needsCleanup.group,
        confidence: 0.85,
        evidenceTimestamps: [],
        reviewRequired: true,
      });
    }
  }

  const suggestedCategory = inferCategoryHint(input);
  const suggestedDisplayTitle = normalizeSpiritFlixTitle(input.fileName) || path.basename(input.fileName, path.extname(input.fileName));
  const suggestedFilename = buildSuggestedFilename(input, suggestedTags);
  const confidence = averageConfidence(suggestedTags);
  const notes = buildHeuristicNotes(input);

  if (suggestedFilename === input.fileName) {
    notes.push("suggested filename matches original stem; review before rename");
  }

  return {
    suggestedTags,
    suggestedCategory,
    suggestedCollections: suggestedCategory ? [suggestedCategory] : [],
    suggestedDisplayTitle,
    suggestedFilename,
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
    suggestedTags: suggestions.suggestedTags,
    suggestedCategory: suggestions.suggestedCategory,
    suggestedCollections: suggestions.suggestedCollections.length > 0 ? suggestions.suggestedCollections : undefined,
    suggestedDisplayTitle: suggestions.suggestedDisplayTitle,
    suggestedFilename: suggestions.suggestedFilename,
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

  const suggestions = buildSpiritFlixReviewSuggestions(heuristicInput);
  const updated = applySpiritFlixReviewSuggestionsToAnalysis(base, suggestions);
  const { analysis } = await writeSmartAnalysis(updated, pathOpts);
  return analysis;
}
