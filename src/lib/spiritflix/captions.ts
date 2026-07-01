import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import "server-only";
import type { SpiritFlixCaptionManifest, SpiritFlixCaptionManifestTrack } from "@/lib/spiritflix-types";

const DEFAULT_CAPTION_ROOT = "/mnt/spirit-8tb/media/.spiritflix-admin/captions";

export function getSpiritFlixCaptionRoot(): string {
  return path.resolve(process.env.SPIRITFLIX_CAPTION_ROOT || DEFAULT_CAPTION_ROOT);
}

export function getSpiritFlixCaptionCacheRoot(): string {
  return path.join(getSpiritFlixCaptionRoot(), "cache");
}

export function getSpiritFlixCaptionGeneratedRoot(): string {
  return path.join(getSpiritFlixCaptionRoot(), "generated");
}

export function getSpiritFlixCaptionManifestRoot(): string {
  return path.join(getSpiritFlixCaptionRoot(), "manifests");
}

export function getSpiritFlixMediaKey(mediaPath: string): string {
  return crypto.createHash("sha256").update(mediaPath).digest("hex").slice(0, 24);
}

function isSafeKey(value: string): boolean {
  return /^[a-f0-9]{24}$/.test(value);
}

function isSafeTrackId(value: string): boolean {
  return /^[a-zA-Z0-9._-]+$/.test(value) && !value.includes("..");
}

function isSubPath(parent: string, child: string): boolean {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function normalizeMediaPath(value?: string | null): string {
  if (!value) return "";
  if (value.startsWith("/media/")) return `/mnt/spirit-8tb/media/${value.slice("/media/".length)}`;
  return value;
}

export function resolveCaptionManifestKey(params: {
  mediaPath?: string | null;
  sourcePath?: string | null;
  key?: string | null;
}): string | null {
  if (params.key) return isSafeKey(params.key) ? params.key : null;
  const mediaPath = normalizeMediaPath(params.mediaPath || params.sourcePath);
  return mediaPath ? getSpiritFlixMediaKey(mediaPath) : null;
}

export function getPublicCaptionUrl(track: Pick<SpiritFlixCaptionManifestTrack, "id">, mediaKey: string): string {
  return `/api/spiritflix/captions/file?key=${encodeURIComponent(mediaKey)}&track=${encodeURIComponent(track.id)}`;
}

export async function findSpiritFlixCaptionManifest(params: {
  mediaPath?: string | null;
  sourcePath?: string | null;
  key?: string | null;
}): Promise<SpiritFlixCaptionManifest | null> {
  const key = resolveCaptionManifestKey(params);
  if (!key) return null;
  const manifestPath = path.join(getSpiritFlixCaptionManifestRoot(), `${key}.json`);
  const root = path.resolve(getSpiritFlixCaptionManifestRoot());
  const resolvedManifest = path.resolve(manifestPath);
  if (!isSubPath(root, resolvedManifest)) return null;
  try {
    const parsed = JSON.parse(await fs.readFile(resolvedManifest, "utf-8")) as SpiritFlixCaptionManifest;
    const tracks = Array.isArray(parsed.tracks) ? parsed.tracks : [];
    return {
      mediaPath: parsed.mediaPath || normalizeMediaPath(params.mediaPath || params.sourcePath),
      mediaKey: key,
      generatedAt: parsed.generatedAt || "",
      tracks: tracks.map((track) => ({ ...track, publicUrl: getPublicCaptionUrl(track, key) })),
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
    return null;
  }
}

export async function getSpiritFlixCaptionManifestResponse(params: {
  mediaPath?: string | null;
  sourcePath?: string | null;
  key?: string | null;
}): Promise<SpiritFlixCaptionManifest> {
  const key = resolveCaptionManifestKey(params) || "";
  const manifest = await findSpiritFlixCaptionManifest(params);
  if (manifest) return manifest;
  return {
    mediaPath: normalizeMediaPath(params.mediaPath || params.sourcePath),
    mediaKey: key,
    generatedAt: "",
    tracks: [],
  };
}

export async function resolveCaptionFilePath(key: string, track: string): Promise<string | null> {
  if (!isSafeKey(key) || !isSafeTrackId(track)) return null;
  const candidateNames = [`${track}.vtt`, track.endsWith(".vtt") ? track : ""].filter(Boolean);
  const roots = [getSpiritFlixCaptionCacheRoot(), getSpiritFlixCaptionGeneratedRoot()].map((root) => path.resolve(root));
  for (const root of roots) {
    for (const name of candidateNames) {
      const candidate = path.resolve(root, key, name);
      if (!isSubPath(root, candidate)) continue;
      const stat = await fs.stat(candidate).catch(() => null);
      if (stat?.isFile()) return candidate;
    }
  }
  return null;
}
