import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { SPIRITFLIX_ADMIN_THUMBNAIL_CACHE_ROOT } from "./constants";
import { resolveSpiritFlixAdminPath, isSpiritFlixAdminPathError } from "./paths";

export const VIDEO_THUMBNAIL_EXTENSIONS = new Set([".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"]);

const FFMPEG_TIMEOUT_MS = 18_000;

export function isVideoThumbnailExtension(extension: string): boolean {
  return VIDEO_THUMBNAIL_EXTENSIONS.has(extension.toLowerCase());
}

export function computeThumbnailCacheKey(normalizedPath: string, sizeBytes: number, mtimeMs: number): string {
  return crypto.createHash("sha256").update(`${normalizedPath}|${sizeBytes}|${mtimeMs}`).digest("hex");
}

export function thumbnailCacheFilePath(cacheKey: string): string {
  return path.join(SPIRITFLIX_ADMIN_THUMBNAIL_CACHE_ROOT, `${cacheKey}.jpg`);
}

export async function ensureThumbnailCacheDirectory(): Promise<void> {
  await fs.mkdir(SPIRITFLIX_ADMIN_THUMBNAIL_CACHE_ROOT, { recursive: true });
}

function formatSeek(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function runFfmpeg(inputPath: string, outputPath: string, seekSeconds: number): Promise<boolean> {
  return new Promise((resolve) => {
    const args = [
      "-hide_banner",
      "-loglevel",
      "error",
      "-ss",
      formatSeek(seekSeconds),
      "-i",
      inputPath,
      "-frames:v",
      "1",
      "-vf",
      "scale=480:-1",
      "-q:v",
      "5",
      "-y",
      outputPath,
    ];

    const proc = spawn("ffmpeg", args, { shell: false });
    const timer = setTimeout(() => {
      proc.kill("SIGKILL");
      resolve(false);
    }, FFMPEG_TIMEOUT_MS);

    proc.on("close", (code) => {
      clearTimeout(timer);
      resolve(code === 0);
    });
    proc.on("error", () => {
      clearTimeout(timer);
      resolve(false);
    });
  });
}

export async function getOrGenerateAdminVideoThumbnail(videoPath: string): Promise<{ cachePath: string; cacheKey: string } | null> {
  const extension = path.extname(videoPath).toLowerCase();
  if (!isVideoThumbnailExtension(extension)) {
    return null;
  }

  let resolved;
  try {
    resolved = await resolveSpiritFlixAdminPath(videoPath);
  } catch (error) {
    if (isSpiritFlixAdminPathError(error)) throw error;
    return null;
  }

  const stat = await fs.stat(resolved.realPath);
  if (!stat.isFile()) {
    return null;
  }

  const normalizedPath = resolved.realPath.replace(/\\/g, "/");
  const cacheKey = computeThumbnailCacheKey(normalizedPath, stat.size, stat.mtimeMs);
  const cachedPath = thumbnailCacheFilePath(cacheKey);

  try {
    await fs.access(cachedPath);
    return { cachePath: cachedPath, cacheKey };
  } catch {
    // Cache miss — generate below.
  }

  await ensureThumbnailCacheDirectory();
  const tempPath = path.join(SPIRITFLIX_ADMIN_THUMBNAIL_CACHE_ROOT, `.${cacheKey}.tmp.jpg`);

  const seekAttempts = [5, 1, 0];
  let generated = false;
  for (const seek of seekAttempts) {
    await fs.rm(tempPath, { force: true }).catch(() => undefined);
    generated = await runFfmpeg(resolved.realPath, tempPath, seek);
    if (generated) break;
  }

  if (!generated) {
    await fs.rm(tempPath, { force: true }).catch(() => undefined);
    return null;
  }

  try {
    await fs.rename(tempPath, cachedPath);
  } catch {
    await fs.rm(tempPath, { force: true }).catch(() => undefined);
    return null;
  }

  return { cachePath: cachedPath, cacheKey };
}
