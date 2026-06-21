// ── SpiritFlix smart scanner orchestrator (S2) ─────────────────────
// One video only. Analysis sidecar + frame cache writes — never mutates media.

import fs from "node:fs/promises";
import path from "node:path";
import { createSmartAnalysisPathKey } from "./analysis-paths";
import {
  createEmptySmartAnalysis,
  readSmartAnalysis,
  writeSmartAnalysis,
} from "./analysis-store";
import { SpiritFlixSmartScannerError } from "./errors";
import { probeSpiritFlixVideo } from "./probe";
import { extractSpiritFlixFrameSample, planSpiritFlixSampleTimestamps } from "./sampler";
import { validateSpiritFlixSmartAnalysis, type SpiritFlixSmartAnalysis, type SpiritFlixSmartSample } from "./types";

export const SPIRITFLIX_SMART_ANALYZER_VERSION_S2 = "spiritflix-smart/s2";

export interface SpiritFlixScanOneVideoOptions {
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

export async function scanOneSpiritFlixVideoEvidence(
  videoPath: string,
  options?: SpiritFlixScanOneVideoOptions,
): Promise<SpiritFlixSmartAnalysis> {
  const pathOpts = pathOptions(options?.mediaRoot);

  let stat;
  try {
    stat = await fs.stat(videoPath);
  } catch {
    throw new SpiritFlixSmartScannerError("Video file is not readable.");
  }
  if (!stat.isFile()) {
    throw new SpiritFlixSmartScannerError("Video path must be a file.");
  }

  const fileName = path.basename(videoPath);
  const pathInput = {
    videoPath,
    fileSizeBytes: stat.size,
    mtimeMs: stat.mtimeMs,
  };

  const existing = await readSmartAnalysis(pathInput, pathOpts);
  const base =
    existing ??
    createEmptySmartAnalysis(
      {
        videoPath,
        fileName,
        fileSizeBytes: stat.size,
        mtimeMs: stat.mtimeMs,
        analyzerVersion: SPIRITFLIX_SMART_ANALYZER_VERSION_S2,
      },
      pathOpts,
    );

  let probeResult;
  try {
    probeResult = await probeSpiritFlixVideo(videoPath, {
      mediaRoot: options?.mediaRoot,
      ffprobePath: options?.ffprobePath,
      timeoutMs: options?.probeTimeoutMs,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "ffprobe failed.";
    throw new SpiritFlixSmartScannerError(message);
  }

  const durationSeconds = probeResult.durationSeconds ?? 1;
  const timestamps = planSpiritFlixSampleTimestamps(durationSeconds, {
    maxSamples: options?.maxSamples,
  });

  const analysisKey = createSmartAnalysisPathKey({
    videoPath: base.videoPath,
    fileSizeBytes: base.fileSizeBytes,
    mtimeMs: base.mtimeMs,
  });

  const samples: SpiritFlixSmartSample[] = [];
  const frameFailures: string[] = [];

  for (const timestampSeconds of timestamps) {
    try {
      const frame = await extractSpiritFlixFrameSample(videoPath, timestampSeconds, {
        mediaRoot: options?.mediaRoot,
        ffmpegPath: options?.ffmpegPath,
        timeoutMs: options?.frameTimeoutMs,
        analysisKey,
      });
      samples.push({
        timestampSeconds: frame.timestampSeconds,
        timestampLabel: frame.timestampLabel,
        cacheKey: frame.cacheKey,
        observations: ["sampled frame"],
        tags: [],
        confidence: 0,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "frame extraction failed";
      frameFailures.push(`${timestampSeconds}s: ${message}`);
    }
  }

  const notesParts: string[] = ["technical metadata collected"];
  if (frameFailures.length > 0) {
    notesParts.push(`frame failures: ${frameFailures.slice(0, 12).join("; ")}`);
  }

  const updated = validateSpiritFlixSmartAnalysis({
    ...base,
    analyzedAt: new Date().toISOString(),
    analyzerVersion: SPIRITFLIX_SMART_ANALYZER_VERSION_S2,
    status: "needs_review",
    safety: {
      safeToSuggest: false,
      reasons: ["Scanner evidence requires human review before suggestions."],
      requiresHumanReview: true,
    },
    media: {
      durationSeconds: probeResult.durationSeconds,
      width: probeResult.width,
      height: probeResult.height,
      codec: probeResult.codec,
      container: probeResult.container ?? probeResult.formatName,
    },
    samples,
    suggestedTags: [],
    suggestedCategory: undefined,
    suggestedFilename: undefined,
    suggestedTargetFolder: undefined,
    confidence: 0,
    notes: notesParts.join(" | "),
  });

  const { analysis } = await writeSmartAnalysis(updated, pathOpts);
  return analysis;
}
