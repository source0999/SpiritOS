import fs from "node:fs/promises";
import path from "node:path";

export type SpiritFlixOrganizeMode = "preview" | "execute";

export interface SpiritFlixOrganizeOptions {
  mediaRoot?: string;
  videoPath: string;
  matchedModel: string;
  confidence: number;
  mode?: SpiritFlixOrganizeMode;
}

export interface SpiritFlixOrganizeReceipt {
  schema: "spiritflix-organize-receipt/v1";
  mode: SpiritFlixOrganizeMode;
  allowed: boolean;
  sourcePath: string;
  targetPath: string;
  duplicateTarget: boolean;
  sourceBefore: {
    fileSizeBytes: number;
    mtimeMs: number;
  };
  after?: {
    sourceExists: boolean;
    targetExists: boolean;
  };
  rollback: {
    moveBackTo: string;
    removeCreatedTarget: string;
  };
  reasonCode: string;
}

function safeSegment(value: string): string {
  return value
    .replace(/[<>:"/\\|?*\u0000-\u001f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 120) || "Unknown Performer";
}

async function uniqueTargetPath(targetPath: string): Promise<{ targetPath: string; duplicateTarget: boolean }> {
  try {
    await fs.stat(targetPath);
  } catch {
    return { targetPath, duplicateTarget: false };
  }
  const parsed = path.parse(targetPath);
  for (let index = 2; index < 10_000; index += 1) {
    const candidate = path.join(parsed.dir, `${parsed.name} (${index})${parsed.ext}`);
    try {
      await fs.stat(candidate);
    } catch {
      return { targetPath: candidate, duplicateTarget: true };
    }
  }
  throw new Error("Unable to find a unique SpiritFlix organize target path.");
}

export async function createSpiritFlixOrganizeReceipt(options: SpiritFlixOrganizeOptions): Promise<SpiritFlixOrganizeReceipt> {
  const mode = options.mode ?? "preview";
  const sourcePath = path.resolve(options.videoPath);
  const stat = await fs.stat(sourcePath);
  const mediaRoot = path.resolve(options.mediaRoot ?? path.dirname(path.dirname(sourcePath)));
  const modelFolder = safeSegment(options.matchedModel);
  const planned = path.join(mediaRoot, "yes", modelFolder, path.basename(sourcePath));
  const target = await uniqueTargetPath(planned);
  const receipt: SpiritFlixOrganizeReceipt = {
    schema: "spiritflix-organize-receipt/v1",
    mode,
    allowed: options.confidence >= 0.86,
    sourcePath,
    targetPath: target.targetPath,
    duplicateTarget: target.duplicateTarget,
    sourceBefore: {
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
    },
    rollback: {
      moveBackTo: sourcePath,
      removeCreatedTarget: target.targetPath,
    },
    reasonCode: options.confidence >= 0.86 ? "high_confidence_preview_ready" : "confidence_too_low",
  };
  if (mode === "execute" && receipt.allowed) {
    await fs.mkdir(path.dirname(target.targetPath), { recursive: true });
    await fs.rename(sourcePath, target.targetPath);
    receipt.after = {
      sourceExists: await exists(sourcePath),
      targetExists: await exists(target.targetPath),
    };
  }
  return receipt;
}

async function exists(filePath: string): Promise<boolean> {
  try {
    await fs.stat(filePath);
    return true;
  } catch {
    return false;
  }
}
