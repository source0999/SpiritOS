import fs from "node:fs/promises";
import path from "node:path";
import {
  assertWritableSpiritFlixAdminPath,
  isProtectedSpiritFlixAdminPath,
  isSpiritFlixAdminTrashPath,
  normalizeSpiritFlixAdminPath,
  SPIRITFLIX_ADMIN_PROTECTED_PATHS,
} from "./path-rules";

export {
  assertWritableSpiritFlixAdminPath,
  isProtectedSpiritFlixAdminPath,
  isSpiritFlixAdminTrashPath,
  normalizeSpiritFlixAdminPath,
  SPIRITFLIX_ADMIN_PROTECTED_PATHS,
};

const DEFAULT_ALLOWED_ROOTS = [
  "/mnt/spirit-8tb/media",
  "/mnt/spirit-8tb/media/anime",
  "/mnt/spirit-8tb/media/movies",
  "/mnt/spirit-8tb/media/tv",
  "/mnt/spirit-8tb/media/music",
  "/mnt/spirit-8tb/media/other",
  "/mnt/spirit-8tb/media/yes",
  "/mnt/spirit-8tb/media-inbox",
];

const BLOCKED_SEGMENTS = new Set([".env", ".git", ".ssh", "config", "secrets"]);
const ALLOWLISTED_HIDDEN_ROOTS = new Set<string>([
  ".spiritflix-admin-smoke",
  ".spiritflix-admin-receipts",
  ".spiritflix-admin",
  ".trash",
]);

function configuredRoots(): string[] {
  const raw = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
  if (!raw) return DEFAULT_ALLOWED_ROOTS;
  return raw
    .split(path.delimiter)
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function hasTraversalSegment(target: string): boolean {
  return target.split(/[\\/]+/).some((segment) => segment === "..");
}

function isSubPath(parent: string, child: string): boolean {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function hasBlockedSegment(target: string, allowedRoot: string): boolean {
  const relative = path.relative(allowedRoot, target);
  if (!relative) return false;
  return relative.split(path.sep).some((segment) => {
    const lower = segment.toLowerCase();
    if (BLOCKED_SEGMENTS.has(lower)) return true;
    return lower.startsWith(".") && !ALLOWLISTED_HIDDEN_ROOTS.has(lower);
  });
}

export function getSpiritFlixAdminAllowedRoots(): string[] {
  return configuredRoots().map((root) => path.resolve(root));
}

export async function resolveSpiritFlixAdminPath(candidate = ""): Promise<{ allowedRoot: string; targetPath: string; realPath: string }> {
  if (hasTraversalSegment(candidate)) {
    throw new Error("Path traversal is not allowed.");
  }

  const allowedRoots = getSpiritFlixAdminAllowedRoots();
  const targetPath = path.resolve(candidate || allowedRoots[0] || "/");
  const allowedRoot = allowedRoots.find((root) => isSubPath(root, targetPath));

  if (!allowedRoot) {
    throw new Error("Path is outside the SpiritFlix admin allowlist.");
  }

  if (hasBlockedSegment(targetPath, allowedRoot)) {
    throw new Error("Hidden or system paths are not available in the SpiritFlix admin explorer.");
  }

  const [realPath, realRoot] = await Promise.all([fs.realpath(targetPath), fs.realpath(allowedRoot)]);

  if (!isSubPath(realRoot, realPath)) {
    throw new Error("Symlink escape is not allowed.");
  }

  return { allowedRoot: realRoot, targetPath, realPath };
}

/** Validate a path under allowlist even when the target file does not exist yet (restore/move targets). */
export async function validateSpiritFlixAdminPathCandidate(candidate = ""): Promise<string> {
  if (hasTraversalSegment(candidate)) {
    throw new Error("Path traversal is not allowed.");
  }

  const allowedRoots = getSpiritFlixAdminAllowedRoots();
  const targetPath = path.resolve(candidate || allowedRoots[0] || "/");
  const allowedRoot = allowedRoots.find((root) => isSubPath(root, targetPath));

  if (!allowedRoot) {
    throw new Error("Path is outside the SpiritFlix admin allowlist.");
  }

  if (hasBlockedSegment(targetPath, allowedRoot)) {
    throw new Error("Hidden or system paths are not available in the SpiritFlix admin explorer.");
  }

  try {
    const [realPath, realRoot] = await Promise.all([fs.realpath(targetPath), fs.realpath(allowedRoot)]);
    if (!isSubPath(realRoot, realPath)) {
      throw new Error("Symlink escape is not allowed.");
    }
    return realPath;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    const parent = path.dirname(targetPath);
    const [realParent, realRoot] = await Promise.all([fs.realpath(parent), fs.realpath(allowedRoot)]);
    if (!isSubPath(realRoot, realParent) || !isSubPath(realParent, targetPath)) {
      throw new Error("Symlink escape is not allowed.");
    }
    return targetPath;
  }
}

export async function getAdminRootForPath(candidate?: string): Promise<string> {
  if (!candidate) return fs.realpath(getSpiritFlixAdminAllowedRoots()[0]);
  return resolveSpiritFlixAdminPath(candidate).then((result) => result.allowedRoot);
}

export function isSpiritFlixAdminPathError(error: unknown): error is Error {
  return error instanceof Error && /allowlist|traversal|Hidden|Symlink|protected|Jellyfin system/.test(error.message);
}
