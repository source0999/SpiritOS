import fs from "node:fs/promises";
import path from "node:path";
import { SPIRITFLIX_MEDIA_ROOT } from "./constants";
import type { SpiritFlixAdminReceipt, SpiritFlixAdminReceiptStatus } from "./types";

const RECEIPTS_DIR = path.join(SPIRITFLIX_MEDIA_ROOT, ".spiritflix-admin-receipts");

function receiptFileFor(date = new Date()): string {
  const stamp = date.toISOString().slice(0, 10).replace(/-/g, "");
  return path.join(RECEIPTS_DIR, `${stamp}.jsonl`);
}

export function createReceiptId(): string {
  return `sf-admin-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export async function writeSpiritFlixAdminReceipt(
  input: Omit<SpiritFlixAdminReceipt, "id" | "timestamp" | "actor"> & { id?: string; timestamp?: string },
): Promise<SpiritFlixAdminReceipt> {
  const receipt: SpiritFlixAdminReceipt = {
    id: input.id ?? createReceiptId(),
    timestamp: input.timestamp ?? new Date().toISOString(),
    actor: "spiritflix-admin",
    action: input.action,
    status: input.status,
    sourcePath: input.sourcePath,
    targetPath: input.targetPath,
    affectedPaths: input.affectedPaths,
    jellyfinItemIds: input.jellyfinItemIds,
    reason: input.reason,
    reversible: input.reversible,
    rollbackHint: input.rollbackHint,
    previewId: input.previewId,
  };

  await fs.mkdir(RECEIPTS_DIR, { recursive: true });
  await fs.appendFile(receiptFileFor(new Date(receipt.timestamp)), `${JSON.stringify(receipt)}\n`, "utf8");
  return receipt;
}

export async function updateReceiptStatus(receiptId: string, status: SpiritFlixAdminReceiptStatus, reason?: string): Promise<void> {
  const file = receiptFileFor();
  try {
    const raw = await fs.readFile(file, "utf8");
    const lines = raw.split("\n").filter(Boolean);
    const updated = lines.map((line) => {
      const receipt = JSON.parse(line) as SpiritFlixAdminReceipt;
      if (receipt.id !== receiptId) return line;
      return JSON.stringify({ ...receipt, status, reason: reason ?? receipt.reason });
    });
    await fs.writeFile(file, `${updated.join("\n")}\n`, "utf8");
  } catch {
    // Receipt file may not exist yet for blocked previews.
  }
}

export function getReceiptsDirectory(): string {
  return RECEIPTS_DIR;
}
