// ── SpiritFlix smart analysis sidecar store (S1) ───────────────────
// Read/write analysis JSON only. No scanner, no media mutation.

import fs from "node:fs/promises";
import path from "node:path";
import {
  assertSmartAnalysisPathMatchesInput,
  assertSmartVideoPathCandidate,
  createSmartAnalysisPathKey,
  getSmartAnalysisRoot,
  type SpiritFlixSmartPathInput,
  type SpiritFlixSmartPathOptions,
} from "./analysis-paths";
import {
  parseSpiritFlixSmartAnalysisJson,
  validateSpiritFlixSmartAnalysis,
  type SpiritFlixSmartAnalysis,
} from "./types";

export const SPIRITFLIX_SMART_ANALYZER_VERSION_S1 = "spiritflix-smart/s1";

export interface CreateEmptySmartAnalysisInput {
  videoPath: string;
  fileName: string;
  fileSizeBytes: number;
  mtimeMs: number;
  analyzerVersion?: string;
}

export function createEmptySmartAnalysis(
  input: CreateEmptySmartAnalysisInput,
  options?: SpiritFlixSmartPathOptions,
): SpiritFlixSmartAnalysis {
  const videoPath = assertSmartVideoPathCandidate(input.videoPath, options);
  const pathKey = createSmartAnalysisPathKey({
    videoPath,
    fileSizeBytes: input.fileSizeBytes,
    mtimeMs: input.mtimeMs,
  });

  return validateSpiritFlixSmartAnalysis({
    version: 1,
    videoPath,
    pathKey,
    fileName: input.fileName,
    fileSizeBytes: input.fileSizeBytes,
    mtimeMs: input.mtimeMs,
    analyzedAt: new Date().toISOString(),
    analyzerVersion: input.analyzerVersion ?? SPIRITFLIX_SMART_ANALYZER_VERSION_S1,
    status: "not_analyzed",
    safety: {
      safeToSuggest: true,
      reasons: [],
      requiresHumanReview: false,
    },
    media: {},
    samples: [],
    suggestedTags: [],
    confidence: 0,
  });
}

function resolveOptions(input: SpiritFlixSmartPathInput, options?: SpiritFlixSmartPathOptions) {
  const videoPath = assertSmartVideoPathCandidate(input.videoPath, options);
  const normalizedInput: SpiritFlixSmartPathInput = {
    videoPath,
    fileSizeBytes: input.fileSizeBytes,
    mtimeMs: input.mtimeMs,
  };
  const sidecarPath = assertSmartAnalysisPathMatchesInput(
    path.join(getSmartAnalysisRoot(options), `${createSmartAnalysisPathKey(normalizedInput)}.json`),
    normalizedInput,
    options,
  );
  return { normalizedInput, sidecarPath };
}

export async function readSmartAnalysis(
  input: SpiritFlixSmartPathInput,
  options?: SpiritFlixSmartPathOptions,
): Promise<SpiritFlixSmartAnalysis | null> {
  const { normalizedInput, sidecarPath } = resolveOptions(input, options);

  try {
    const raw = await fs.readFile(sidecarPath, "utf8");
    const analysis = parseSpiritFlixSmartAnalysisJson(raw);
    const expectedKey = createSmartAnalysisPathKey(normalizedInput);
    if (analysis.pathKey !== expectedKey) {
      throw new Error("Analysis sidecar pathKey does not match the video identity.");
    }
    return analysis;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

export async function writeSmartAnalysis(
  analysis: SpiritFlixSmartAnalysis,
  options?: SpiritFlixSmartPathOptions,
): Promise<{ path: string; analysis: SpiritFlixSmartAnalysis }> {
  const validated = validateSpiritFlixSmartAnalysis(analysis);
  const videoPath = assertSmartVideoPathCandidate(validated.videoPath, options);

  const input: SpiritFlixSmartPathInput = {
    videoPath,
    fileSizeBytes: validated.fileSizeBytes,
    mtimeMs: validated.mtimeMs,
  };

  const expectedKey = createSmartAnalysisPathKey(input);
  if (validated.pathKey !== expectedKey) {
    throw new Error("Analysis pathKey does not match video path, size, and mtime.");
  }

  const sidecarPath = assertSmartAnalysisPathMatchesInput(
    path.join(getSmartAnalysisRoot(options), `${expectedKey}.json`),
    input,
    options,
  );

  const analysisRoot = getSmartAnalysisRoot(options);
  await fs.mkdir(analysisRoot, { recursive: true });

  const payload = `${JSON.stringify(validated, null, 2)}\n`;
  const tempPath = path.join(analysisRoot, `.${expectedKey}.tmp.json`);

  await fs.writeFile(tempPath, payload, "utf8");
  await fs.rename(tempPath, sidecarPath);

  return { path: sidecarPath, analysis: validated };
}
