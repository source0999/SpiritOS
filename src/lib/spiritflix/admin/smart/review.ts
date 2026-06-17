// ── SpiritFlix S4 review orchestration ───────────────────────────────
// Combines S2 scanner + S3 heuristics. Sidecar writes only — no Level 2.

import fs from "node:fs/promises";
import path from "node:path";
import { readSmartAnalysis, writeSmartAnalysis } from "./analysis-store";
import { scanOneSpiritFlixVideoEvidence } from "./scanner";
import { updateSmartAnalysisWithHeuristicSuggestions } from "./suggestions";
import { validateSpiritFlixSmartAnalysis, type SpiritFlixSmartAnalysis } from "./types";

export const SPIRITFLIX_SMART_ANALYZER_VERSION_S4 = "spiritflix-smart/s4";

export interface SpiritFlixSmartReviewOptions {
  mediaRoot?: string;
  ffprobePath?: string;
  ffmpegPath?: string;
  maxSamples?: number;
  probeTimeoutMs?: number;
  frameTimeoutMs?: number;
}

function pathOptions(mediaRoot?: string) {
  return mediaRoot ? { mediaRoot } : undefined;
}

function mergeNotes(existing: string | undefined, addition: string): string {
  const parts = new Set<string>();
  if (existing?.trim()) parts.add(existing.trim());
  if (addition.trim()) parts.add(addition.trim());
  return [...parts].join(" | ").slice(0, 8_000);
}

export async function runSpiritFlixSmartReviewPipeline(
  videoPath: string,
  options?: SpiritFlixSmartReviewOptions,
): Promise<SpiritFlixSmartAnalysis> {
  const scanned = await scanOneSpiritFlixVideoEvidence(videoPath, options);
  const stat = await fs.stat(videoPath);

  return updateSmartAnalysisWithHeuristicSuggestions(
    {
      videoPath,
      fileName: path.basename(videoPath),
      parentPath: path.dirname(videoPath),
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
      media: scanned.media,
    },
    pathOptions(options?.mediaRoot),
  );
}

export async function markSpiritFlixSmartAnalysisReviewed(
  videoPath: string,
  options?: { mediaRoot?: string },
): Promise<SpiritFlixSmartAnalysis> {
  const pathOpts = pathOptions(options?.mediaRoot);
  const stat = await fs.stat(videoPath);
  const pathInput = { videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs };
  const existing = await readSmartAnalysis(pathInput, pathOpts);
  if (!existing) {
    throw new Error("No smart analysis sidecar exists to mark reviewed.");
  }

  const updated = validateSpiritFlixSmartAnalysis({
    ...existing,
    analyzedAt: new Date().toISOString(),
    analyzerVersion: SPIRITFLIX_SMART_ANALYZER_VERSION_S4,
    status: "suggested",
    safety: {
      ...existing.safety,
      requiresHumanReview: true,
      safeToSuggest: false,
      reasons: [...new Set([...existing.safety.reasons, "Marked reviewed in admin UI — apply actions still gated."])],
    },
    notes: mergeNotes(existing.notes, "marked reviewed in SpiritFlix admin (S4 UI only, no rename/move applied)"),
  });

  const { analysis } = await writeSmartAnalysis(updated, pathOpts);
  return analysis;
}
