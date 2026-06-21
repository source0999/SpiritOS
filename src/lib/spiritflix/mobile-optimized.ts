import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";

export const MOBILE_OPTIMIZED_ROOT =
  process.env.SPIRITFLIX_MOBILE_OPTIMIZED_ROOT ||
  "/mnt/spirit-8tb/media/.spiritflix-admin/mobile-optimized";

export interface MobileOptimizedReceipt {
  schema?: string;
  itemId?: string;
  sourcePath?: string;
  sourceStableIdentity?: {
    path?: string;
    sizeBytes?: number;
    durationSeconds?: number;
    mtime?: string;
  };
  sourcePathSha256?: string;
  sourceIdentitySha256?: string;
  sourceContentSha256?: string;
  sourceSize?: number;
  sourceMtime?: string;
  outputPath: string;
  outputKey?: string;
  encoder: string;
  encoderPreference?: string;
  profile?: string;
  profileKind?: string;
  workerHost?: string;
  workerProof?: {
    host?: string;
    ffmpegPath?: string;
    ffprobePath?: string;
    videotoolboxAvailable?: boolean;
    x264Available?: boolean;
    dellRole?: string;
  };
  commandSummary?: string[];
  inputFfprobe?: {
    container?: string;
    videoCodec?: string;
    audioCodec?: string;
    width?: number;
    height?: number;
    duration?: number;
    bitrate?: number;
    hasVideo?: boolean;
    hasAudio?: boolean;
  };
  outputFfprobe?: {
    container?: string;
    videoCodec?: string;
    audioCodec?: string;
    width?: number;
    height?: number;
    duration?: number;
    bitrate?: number;
    hasVideo?: boolean;
    hasAudio?: boolean;
  };
  startedAt?: string;
  created_at?: string;
  completedAt?: string;
  durationMs?: number;
  duration?: number;
  outputSize?: number;
  optimizedSize?: number;
  percentSaved?: number;
  percentageSaved?: number;
  ffprobe?: {
    container?: string;
    videoCodec?: string;
    audioCodec?: string;
    width?: number;
    height?: number;
    duration?: number;
  };
  status: "ok" | "failed" | "dry-run";
  error?: string;
  rollbackOriginalPreservationNote?: string;
}

export interface MobileOptimizedMatch {
  key: string;
  receiptPath: string;
  receipt: MobileOptimizedReceipt;
}

export function getSourcePathSha256(sourcePath: string): string {
  return crypto.createHash("sha256").update(sourcePath).digest("hex");
}

export function expandSpiritFlixSourcePathAliases(sourcePath: string): string[] {
  const aliases = new Set<string>();
  const trimmed = sourcePath.trim();
  if (!trimmed) return [];
  aliases.add(trimmed);
  if (trimmed.startsWith("/media/yes/")) {
    aliases.add(trimmed.replace(/^\/media\/yes\//, "/mnt/spirit-8tb/media/yes/"));
  }
  if (trimmed.startsWith("/mnt/spirit-8tb/media/yes/")) {
    aliases.add(trimmed.replace(/^\/mnt\/spirit-8tb\/media\/yes\//, "/media/yes/"));
  }
  return Array.from(aliases);
}

function isInside(root: string, candidate: string): boolean {
  const resolvedRoot = path.resolve(root);
  const resolvedCandidate = path.resolve(candidate);
  const relative = path.relative(resolvedRoot, resolvedCandidate);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

export function isContainedMobileOutput(outputPath: string): boolean {
  return isInside(MOBILE_OPTIMIZED_ROOT, outputPath);
}

async function collectReceiptPaths(dir: string): Promise<string[]> {
  let entries: Array<import("node:fs").Dirent>;
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return [];
  }

  const nested = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(dir, entry.name);
      if (entry.isDirectory()) return collectReceiptPaths(entryPath);
      return entry.isFile() && entry.name.endsWith(".json") ? [entryPath] : [];
    }),
  );
  return nested.flat();
}

function keyFromReceipt(receipt: MobileOptimizedReceipt, receiptPath: string): string {
  return receipt.outputKey || receipt.sourcePathSha256 || path.basename(receiptPath, ".json");
}

async function readReceipt(receiptPath: string): Promise<MobileOptimizedMatch | null> {
  try {
    const receipt = JSON.parse(await fs.readFile(receiptPath, "utf8")) as MobileOptimizedReceipt;
    if (receipt.status !== "ok" || !receipt.outputPath || !isContainedMobileOutput(receipt.outputPath)) {
      return null;
    }
    await fs.access(receipt.outputPath);
    return { key: keyFromReceipt(receipt, receiptPath), receiptPath, receipt };
  } catch {
    return null;
  }
}

export async function findMobileOptimizedReceipt(criteria: {
  itemId?: string;
  sourcePathSha256?: string;
  sourcePath?: string;
  key?: string;
}): Promise<MobileOptimizedMatch | null> {
  const receiptPaths = await collectReceiptPaths(MOBILE_OPTIMIZED_ROOT);
  const sourcePathShaCandidates = new Set<string>();
  if (criteria.sourcePathSha256) sourcePathShaCandidates.add(criteria.sourcePathSha256);
  for (const sourcePath of expandSpiritFlixSourcePathAliases(criteria.sourcePath ?? "")) {
    sourcePathShaCandidates.add(getSourcePathSha256(sourcePath));
  }
  for (const receiptPath of receiptPaths) {
    const match = await readReceipt(receiptPath);
    if (!match) continue;
    if (criteria.key && match.key === criteria.key) return match;
    if (criteria.itemId && match.receipt.itemId === criteria.itemId) return match;
    if (match.receipt.sourcePathSha256 && sourcePathShaCandidates.has(match.receipt.sourcePathSha256)) {
      return match;
    }
  }
  return null;
}
