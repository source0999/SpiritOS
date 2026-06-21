// ── SpiritFlix smart analysis path helpers (S1) ────────────────────
// Sidecars live under .spiritflix-admin/analysis — never beside videos.

import crypto from "node:crypto";
import path from "node:path";
import { SPIRITFLIX_MEDIA_ROOT } from "../constants";
import { assertWritableSpiritFlixAdminPath, normalizeSpiritFlixAdminPath } from "../path-rules";

export const SPIRITFLIX_SMART_ANALYSIS_DIR = "analysis";
export const SPIRITFLIX_SMART_ANALYSIS_CACHE_DIR = "analysis-cache";
export const SPIRITFLIX_SMART_ADMIN_SUBDIR = ".spiritflix-admin";

export interface SpiritFlixSmartPathInput {
  videoPath: string;
  fileSizeBytes: number;
  mtimeMs: number;
}

export interface SpiritFlixSmartPathOptions {
  mediaRoot?: string;
}

function resolveMediaRoot(options?: SpiritFlixSmartPathOptions): string {
  return path.resolve(options?.mediaRoot ?? SPIRITFLIX_MEDIA_ROOT);
}

function hasTraversalSegment(target: string): boolean {
  return target.split(/[\\/]+/).some((segment) => segment === "..");
}

function isSubPath(parent: string, child: string): boolean {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function jellyfinSystemPath(candidate: string): boolean {
  const normalized = normalizeSpiritFlixAdminPath(candidate);
  return [/jellyfin/i, /library\.db$/i, /system\.xml$/i, /\.sqlite$/i].some((pattern) => pattern.test(normalized));
}

export function normalizeSmartVideoPath(videoPath: string): string {
  return videoPath.replace(/\\/g, "/");
}

/** Deterministic cache key — mirrors thumbnail cache key shape. */
export function createSmartAnalysisPathKey(input: SpiritFlixSmartPathInput): string {
  const normalized = normalizeSmartVideoPath(input.videoPath);
  return crypto.createHash("sha256").update(`${normalized}|${input.fileSizeBytes}|${input.mtimeMs}`).digest("hex");
}

export function getSmartAnalysisRoot(options?: SpiritFlixSmartPathOptions): string {
  return path.join(resolveMediaRoot(options), SPIRITFLIX_SMART_ADMIN_SUBDIR, SPIRITFLIX_SMART_ANALYSIS_DIR);
}

export function getSmartAnalysisCacheRoot(options?: SpiritFlixSmartPathOptions): string {
  return path.join(resolveMediaRoot(options), SPIRITFLIX_SMART_ADMIN_SUBDIR, SPIRITFLIX_SMART_ANALYSIS_CACHE_DIR);
}

export function getSmartAnalysisPath(input: SpiritFlixSmartPathInput, options?: SpiritFlixSmartPathOptions): string {
  const key = createSmartAnalysisPathKey(input);
  return path.join(getSmartAnalysisRoot(options), `${key}.json`);
}

export function assertSmartVideoPathCandidate(videoPath: string, options?: SpiritFlixSmartPathOptions): string {
  if (!videoPath.trim()) throw new Error("videoPath is required.");
  if (hasTraversalSegment(videoPath)) throw new Error("Path traversal is not allowed.");
  if (jellyfinSystemPath(videoPath)) throw new Error("Cannot analyze Jellyfin system path.");

  const mediaRoot = resolveMediaRoot(options);
  const resolved = path.resolve(videoPath);
  if (!isSubPath(mediaRoot, resolved)) {
    throw new Error("Video path is outside the SpiritFlix media root.");
  }

  const analysisRoot = getSmartAnalysisRoot(options);
  if (isSubPath(path.dirname(resolved), analysisRoot) || resolved.startsWith(analysisRoot + path.sep)) {
    throw new Error("Analysis paths cannot point inside the analysis store.");
  }

  const adminSubdir = path.join(mediaRoot, SPIRITFLIX_SMART_ADMIN_SUBDIR);
  const relativeToAdmin = path.relative(adminSubdir, resolved);
  if (!relativeToAdmin.startsWith("..") && !path.isAbsolute(relativeToAdmin)) {
    throw new Error("Analysis cannot target SpiritFlix admin storage paths.");
  }

  try {
    assertWritableSpiritFlixAdminPath(resolved, "analyze");
  } catch (error) {
    if (error instanceof Error && /Jellyfin system/i.test(error.message)) {
      throw error;
    }
    // Protected roots are readable; only block Jellyfin paths above.
  }

  return resolved;
}

/** Ensure an analysis sidecar path stays under the analysis root. */
export function assertSmartAnalysisPathSafe(candidate: string, options?: SpiritFlixSmartPathOptions): string {
  if (!candidate.trim()) throw new Error("Analysis path is required.");
  if (hasTraversalSegment(candidate)) throw new Error("Path traversal is not allowed.");

  const resolved = path.resolve(candidate);
  const analysisRoot = path.resolve(getSmartAnalysisRoot(options));

  if (!isSubPath(analysisRoot, resolved)) {
    throw new Error("Analysis sidecar path must stay under the analysis root.");
  }

  if (path.basename(resolved).startsWith(".")) {
    throw new Error("Analysis sidecar filename is not allowed.");
  }

  if (path.extname(resolved).toLowerCase() !== ".json") {
    throw new Error("Analysis sidecar must use a .json extension.");
  }

  return resolved;
}

export function assertSmartAnalysisPathMatchesInput(
  sidecarPath: string,
  input: SpiritFlixSmartPathInput,
  options?: SpiritFlixSmartPathOptions,
): string {
  const safePath = assertSmartAnalysisPathSafe(sidecarPath, options);
  const expected = getSmartAnalysisPath(input, options);
  if (path.resolve(safePath) !== path.resolve(expected)) {
    throw new Error("Analysis sidecar path does not match the expected deterministic location.");
  }
  return safePath;
}
