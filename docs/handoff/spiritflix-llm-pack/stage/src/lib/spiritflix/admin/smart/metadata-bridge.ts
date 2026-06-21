// ── SpiritFlix Smart Metadata Bridge (S6) ─────────────────────────────
// Projects approved smart metadata into admin metadata sidecars.
// Writes under .spiritflix-admin/metadata/ only — never beside video.
// Never mutates actual filename. Never calls Level 2 execute.

import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { SPIRITFLIX_MEDIA_ROOT } from "../constants";
import { isKnownSmartTagId } from "./vocabulary";
import type {
  SpiritFlixSmartAnalysis,
  SpiritFlixSmartReviewStatus,
  SpiritFlixSmartTag,
} from "./types";

// ── Projection type ─────────────────────────────────────────────────────

export interface SpiritFlixApprovedMetadataProjection {
  sourcePath: string;
  displayTitle?: string;
  filenameSuggestion?: string;
  category?: string;
  collections: string[];
  approvedTags: Array<{
    id: string;
    label: string;
    group: string;
    confidence: number;
  }>;
  rejectedTagIds: string[];
  reviewStatus: string;
  reviewedAt?: string;
  notes?: string;
}

// ── Metadata sidecar path helper ───────────────────────────────────────
// Mirrors the exact sha256(normalized-lowercased-forward-slash-path)
// convention used by Level 2 writeMetadata in actions.ts.

export function metadataSidecarPath(
  sourcePath: string,
  mediaRoot?: string,
): string {
  const root = path.resolve(mediaRoot ?? SPIRITFLIX_MEDIA_ROOT);
  const normalizedSourcePath = sourcePath
    .replace(/\\/g, "/")
    .replace(/^[A-Za-z]:(?=\/)/, "")
    .toLowerCase();
  const hash = crypto
    .createHash("sha256")
    .update(normalizedSourcePath)
    .digest("hex");
  return path.join(root, ".spiritflix-admin", "metadata", `${hash}.json`);
}

// ── Pure projection ───────────────────────────────────────────────────

export function projectApprovedSmartMetadata(
  analysis: SpiritFlixSmartAnalysis,
): SpiritFlixApprovedMetadataProjection {
  const reviewed = analysis.reviewedMetadata;
  const reviewStatus: SpiritFlixSmartReviewStatus =
    reviewed?.reviewStatus ?? "unreviewed";

  // Approved tags: must be in suggestedTags AND approvedTagIds AND vocabulary-valid
  const approvedSet = new Set(reviewed?.approvedTagIds ?? []);
  const approvedTags: SpiritFlixApprovedMetadataProjection["approvedTags"] =
    analysis.suggestedTags
      .filter((tag) => approvedSet.has(tag.id) && isKnownSmartTagId(tag.id))
      .map((tag) => ({
        id: tag.id,
        label: tag.label,
        group: tag.group,
        confidence: tag.confidence,
      }));

  // Edited values override suggestions
  const displayTitle = reviewed?.editedDisplayTitle ?? analysis.suggestedDisplayTitle;
  const filenameSuggestion = reviewed?.editedFilenameSuggestion ?? analysis.suggestedFilename;
  const category = reviewed?.editedCategory ?? analysis.suggestedCategory;
  const collections = reviewed?.editedCollections ?? analysis.suggestedCollections ?? [];
  const notes = reviewed?.notes;

  return {
    sourcePath: analysis.videoPath,
    displayTitle,
    filenameSuggestion,
    category,
    collections,
    approvedTags,
    rejectedTagIds: reviewed?.rejectedTagIds ?? [],
    reviewStatus,
    reviewedAt: reviewed?.reviewedAt,
    notes,
  };
}

// ── Write admin metadata sidecar ───────────────────────────────────────
// Writes to the same Level 2 metadata sidecar store:
//   .spiritflix-admin/metadata/<sha256>.json
// Preserves any existing sidecar fields (read-merge-write).
// Stores the full smart projection under `smartApproved` key.

export async function writeApprovedSmartMetadataSidecar(
  analysis: SpiritFlixSmartAnalysis,
  options?: { mediaRoot?: string },
): Promise<{ path: string; metadata: SpiritFlixApprovedMetadataProjection }> {
  const projection = projectApprovedSmartMetadata(analysis);
  const targetPath = metadataSidecarPath(projection.sourcePath, options?.mediaRoot);

  // Read existing sidecar to preserve non-smart fields
  let existing: Record<string, unknown> = {};
  try {
    const raw = await fs.readFile(targetPath, "utf-8");
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      existing = parsed as Record<string, unknown>;
    }
  } catch {
    // No existing sidecar — that's fine
  }

  // Build merged sidecar: Level 2 fields + smart projection
  const merged: Record<string, unknown> = {
    ...existing,
    sourcePath: projection.sourcePath,
    displayTitle: projection.displayTitle,
    displayNameOverride: projection.displayTitle,
    smartDisplayName: projection.displayTitle,
    customTags: projection.approvedTags.map((tag) => tag.label),
    smartTagIds: projection.approvedTags.map((tag) => tag.id),
    collection: projection.category,
    notes: projection.notes,
    smartApproved: projection,
  };

  // Atomic write: temp file + rename (mirrors actions.ts pattern)
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  const tmpPath = `${targetPath}.tmp-${Date.now()}`;
  await fs.writeFile(tmpPath, JSON.stringify(merged, null, 2), "utf-8");
  await fs.rename(tmpPath, targetPath);

  return { path: targetPath, metadata: projection };
}
