// ── SpiritFlix S5 reviewed metadata (analysis sidecar only) ─────────
// Human review of suggestions — never mutates media files.

import { isKnownSmartTagId } from "./vocabulary";
import {
  validateSpiritFlixSmartAnalysis,
  type SpiritFlixSmartAnalysis,
  type SpiritFlixSmartReviewedMetadata,
  type SpiritFlixSmartReviewInput,
  type SpiritFlixSmartReviewStatus,
} from "./types";

export const SPIRITFLIX_SMART_ANALYZER_VERSION_S5 = "spiritflix-smart/s5";

const UNSAFE_FILENAME_CHARS = /[\\/:*?"<>|]/g;
const MAX_FILENAME_STEM_LENGTH = 120;

function fileExtension(fileName: string): string {
  const match = fileName.match(/(\.[^./\\]+)$/);
  return match ? match[1].toLowerCase() : "";
}

const ALLOWED_REVIEW_KEYS = new Set([
  "approvedTagIds",
  "rejectedTagIds",
  "editedDisplayTitle",
  "editedFilenameSuggestion",
  "editedCategory",
  "editedCollections",
  "notes",
]);

export function assertSpiritFlixSmartReviewPayload(value: unknown): SpiritFlixSmartReviewInput {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("review must be an object.");
  }
  const record = value as Record<string, unknown>;
  for (const key of Object.keys(record)) {
    if (!ALLOWED_REVIEW_KEYS.has(key)) {
      throw new Error(`review contains unknown field "${key}".`);
    }
  }

  const serialized = JSON.stringify(record);
  if (serialized.length > 32_768) {
    throw new Error("review payload is too large.");
  }

  return validateSpiritFlixSmartReviewInput(record);
}

function sanitizeText(value: string | undefined, maxLength: number): string | undefined {
  if (value === undefined) return undefined;
  const trimmed = value.replace(/\0/g, "").trim();
  if (!trimmed) return undefined;
  return trimmed.slice(0, maxLength);
}

export function sanitizeEditedFilenameSuggestion(
  value: string | undefined,
  originalFileName: string,
): string | undefined {
  if (value === undefined) return undefined;
  const extension = fileExtension(originalFileName) || ".mp4";
  const raw = value.replace(UNSAFE_FILENAME_CHARS, " ").replace(/\s+/g, " ").trim();
  if (!raw) return undefined;
  const stem = raw.endsWith(extension) ? raw.slice(0, -extension.length).trim() : raw;
  const cleanedStem = stem.slice(0, MAX_FILENAME_STEM_LENGTH).trim() || "untitled";
  return `${cleanedStem}${extension}`;
}

function uniqueIds(ids: string[]): string[] {
  return [...new Set(ids)];
}

function computeReviewStatus(
  analysis: SpiritFlixSmartAnalysis,
  input: SpiritFlixSmartReviewInput,
): SpiritFlixSmartReviewStatus {
  const suggestedIds = analysis.suggestedTags.map((tag) => tag.id);
  const approved = uniqueIds(input.approvedTagIds);
  const rejected = uniqueIds(input.rejectedTagIds);
  const decided = new Set([...approved, ...rejected]);
  const pendingCount = suggestedIds.filter((id) => !decided.has(id)).length;

  const hasEdits = Boolean(
    input.editedDisplayTitle ||
      input.editedFilenameSuggestion ||
      input.editedCategory ||
      (input.editedCollections && input.editedCollections.length > 0) ||
      input.notes,
  );

  if (suggestedIds.length > 0 && rejected.length === suggestedIds.length && !hasEdits) {
    return "rejected";
  }

  if (pendingCount === 0 && (approved.length > 0 || hasEdits)) {
    return "reviewed";
  }

  if (approved.length > 0 || rejected.length > 0 || hasEdits) {
    return "partially_reviewed";
  }

  return "unreviewed";
}

function computeAnalysisStatus(
  analysis: SpiritFlixSmartAnalysis,
  reviewStatus: SpiritFlixSmartReviewStatus,
): SpiritFlixSmartAnalysis["status"] {
  if (reviewStatus === "rejected") return "rejected";
  if (reviewStatus === "reviewed") return "approved";
  if (reviewStatus === "partially_reviewed") return "suggested";
  return analysis.status === "not_analyzed" ? "needs_review" : analysis.status;
}

export function applySmartReviewToAnalysis(
  analysis: SpiritFlixSmartAnalysis,
  input: SpiritFlixSmartReviewInput,
): SpiritFlixSmartAnalysis {
  const validatedInput = validateSpiritFlixSmartReviewInput(input);
  const suggestedIds = new Set(analysis.suggestedTags.map((tag) => tag.id));

  for (const id of [...validatedInput.approvedTagIds, ...validatedInput.rejectedTagIds]) {
    if (!suggestedIds.has(id)) {
      throw new Error(`Tag id "${id}" is not in suggestedTags.`);
    }
  }

  const reviewStatus = computeReviewStatus(analysis, validatedInput);
  const reviewedMetadata: SpiritFlixSmartReviewedMetadata = {
    reviewedAt: new Date().toISOString(),
    reviewedBy: "spiritflix-admin",
    reviewStatus,
    approvedTagIds: validatedInput.approvedTagIds,
    rejectedTagIds: validatedInput.rejectedTagIds,
    editedDisplayTitle: sanitizeText(validatedInput.editedDisplayTitle, 512),
    editedFilenameSuggestion: sanitizeEditedFilenameSuggestion(validatedInput.editedFilenameSuggestion, analysis.fileName),
    editedCategory: sanitizeText(validatedInput.editedCategory, 256),
    editedCollections: validatedInput.editedCollections,
    notes: sanitizeText(validatedInput.notes, 8_192),
  };

  return validateSpiritFlixSmartAnalysis({
    ...analysis,
    analyzedAt: new Date().toISOString(),
    analyzerVersion: SPIRITFLIX_SMART_ANALYZER_VERSION_S5,
    status: computeAnalysisStatus(analysis, reviewStatus),
    safety: {
      ...analysis.safety,
      safeToSuggest: false,
      requiresHumanReview: true,
      reasons: [
        ...new Set([
          ...analysis.safety.reasons,
          "S5 metadata review saved — file rename/move not executed.",
        ]),
      ],
    },
    reviewedMetadata,
    samples: analysis.samples,
    suggestedTags: analysis.suggestedTags,
    suggestedCategory: analysis.suggestedCategory,
    suggestedCollections: analysis.suggestedCollections,
    suggestedDisplayTitle: analysis.suggestedDisplayTitle,
    suggestedFilename: analysis.suggestedFilename,
    notes: analysis.notes,
  });
}

export function buildEmptyReviewDraft(analysis: SpiritFlixSmartAnalysis | null): SpiritFlixSmartReviewInput {
  const reviewed = analysis?.reviewedMetadata;
  return {
    approvedTagIds: [...(reviewed?.approvedTagIds ?? [])],
    rejectedTagIds: [...(reviewed?.rejectedTagIds ?? [])],
    editedDisplayTitle: reviewed?.editedDisplayTitle ?? analysis?.suggestedDisplayTitle ?? "",
    editedFilenameSuggestion: reviewed?.editedFilenameSuggestion ?? analysis?.suggestedFilename ?? "",
    editedCategory: reviewed?.editedCategory ?? analysis?.suggestedCategory ?? "",
    editedCollections: [...(reviewed?.editedCollections ?? analysis?.suggestedCollections ?? [])],
    notes: reviewed?.notes ?? "",
  };
}

export function countReviewTagStates(
  analysis: SpiritFlixSmartAnalysis,
  draft: SpiritFlixSmartReviewInput,
): { approved: number; rejected: number; pending: number } {
  const suggestedIds = analysis.suggestedTags.map((tag) => tag.id);
  const approved = new Set(draft.approvedTagIds);
  const rejected = new Set(draft.rejectedTagIds);
  let approvedCount = 0;
  let rejectedCount = 0;
  let pendingCount = 0;
  for (const id of suggestedIds) {
    if (approved.has(id)) approvedCount += 1;
    else if (rejected.has(id)) rejectedCount += 1;
    else pendingCount += 1;
  }
  return { approved: approvedCount, rejected: rejectedCount, pending: pendingCount };
}

export function tagReviewState(
  tagId: string,
  draft: SpiritFlixSmartReviewInput,
): "approved" | "rejected" | "pending" {
  if (draft.approvedTagIds.includes(tagId)) return "approved";
  if (draft.rejectedTagIds.includes(tagId)) return "rejected";
  return "pending";
}

export function validateSpiritFlixSmartReviewInput(value: unknown): SpiritFlixSmartReviewInput {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("review must be an object.");
  }
  const record = value as Record<string, unknown>;

  if (!Array.isArray(record.approvedTagIds)) throw new Error("approvedTagIds must be an array.");
  if (!Array.isArray(record.rejectedTagIds)) throw new Error("rejectedTagIds must be an array.");
  if (record.approvedTagIds.length > 200 || record.rejectedTagIds.length > 200) {
    throw new Error("review tag id lists are too large.");
  }

  const approvedTagIds = record.approvedTagIds.map((entry, index) => {
    if (typeof entry !== "string" || !entry.trim()) throw new Error(`approvedTagIds[${index}] must be a non-empty string.`);
    if (!isKnownSmartTagId(entry)) throw new Error(`approvedTagIds[${index}] is not a known tag id.`);
    return entry;
  });

  const rejectedTagIds = record.rejectedTagIds.map((entry, index) => {
    if (typeof entry !== "string" || !entry.trim()) throw new Error(`rejectedTagIds[${index}] must be a non-empty string.`);
    if (!isKnownSmartTagId(entry)) throw new Error(`rejectedTagIds[${index}] is not a known tag id.`);
    return entry;
  });

  const overlap = approvedTagIds.find((id) => rejectedTagIds.includes(id));
  if (overlap) throw new Error("approvedTagIds and rejectedTagIds must not overlap.");

  let editedCollections: string[] | undefined;
  if (record.editedCollections !== undefined) {
    if (!Array.isArray(record.editedCollections)) throw new Error("editedCollections must be an array.");
    if (record.editedCollections.length > 50) throw new Error("editedCollections is too large.");
    editedCollections = record.editedCollections.map((entry, index) => {
      if (typeof entry !== "string" || !entry.trim()) throw new Error(`editedCollections[${index}] must be a non-empty string.`);
      return entry.trim().slice(0, 256);
    });
  }

  const editedDisplayTitle =
    record.editedDisplayTitle === undefined
      ? undefined
      : typeof record.editedDisplayTitle === "string"
        ? record.editedDisplayTitle.trim().slice(0, 512)
        : (() => {
            throw new Error("editedDisplayTitle must be a string.");
          })();

  const editedFilenameSuggestion =
    record.editedFilenameSuggestion === undefined
      ? undefined
      : typeof record.editedFilenameSuggestion === "string"
        ? record.editedFilenameSuggestion.trim().slice(0, 512)
        : (() => {
            throw new Error("editedFilenameSuggestion must be a string.");
          })();

  const editedCategory =
    record.editedCategory === undefined
      ? undefined
      : typeof record.editedCategory === "string"
        ? record.editedCategory.trim().slice(0, 256)
        : (() => {
            throw new Error("editedCategory must be a string.");
          })();

  const notes =
    record.notes === undefined
      ? undefined
      : typeof record.notes === "string"
        ? record.notes.trim().slice(0, 8_192)
        : (() => {
            throw new Error("notes must be a string.");
          })();

  return {
    approvedTagIds: [...new Set(approvedTagIds)],
    rejectedTagIds: [...new Set(rejectedTagIds)],
    editedDisplayTitle: editedDisplayTitle || undefined,
    editedFilenameSuggestion: editedFilenameSuggestion || undefined,
    editedCategory: editedCategory || undefined,
    editedCollections,
    notes: notes || undefined,
  };
}
