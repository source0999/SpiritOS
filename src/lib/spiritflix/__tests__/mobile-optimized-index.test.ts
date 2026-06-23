import fs from "node:fs/promises";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

let tempRoot = "";

async function loadMobileOptimized() {
  vi.resetModules();
  process.env.SPIRITFLIX_MOBILE_OPTIMIZED_ROOT = tempRoot;
  return import("@/lib/spiritflix/mobile-optimized");
}

describe("mobile optimized receipt index", () => {
  beforeEach(async () => {
    tempRoot = await fs.mkdtemp(path.join(process.cwd(), ".tmp-spiritflix-mobile-index-"));
  });

  afterEach(async () => {
    delete process.env.SPIRITFLIX_MOBILE_OPTIMIZED_ROOT;
    await fs.rm(tempRoot, { recursive: true, force: true });
  });

  it("finds receipts by itemId without rescanning on every lookup", async () => {
    const outputPath = path.join(tempRoot, "20260622", "fast-item.mp4");
    const receiptPath = path.join(tempRoot, "20260622", "fast-item.json");
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, "0123456789");
    await fs.writeFile(
      receiptPath,
      JSON.stringify({
        itemId: "fast-item",
        sourcePathSha256: "abc",
        outputPath,
        outputKey: "fast-item",
        encoder: "mac-videotoolbox-h264-mobile",
        status: "ok",
      }),
    );

    const { findMobileOptimizedReceipt, clearMobileOptimizedReceiptIndexCache } = await loadMobileOptimized();
    const first = await findMobileOptimizedReceipt({ itemId: "fast-item" });
    const second = await findMobileOptimizedReceipt({ itemId: "fast-item" });
    clearMobileOptimizedReceiptIndexCache();
    const third = await findMobileOptimizedReceipt({ itemId: "fast-item" });

    expect(first?.key).toBe("fast-item");
    expect(second?.key).toBe("fast-item");
    expect(third?.key).toBe("fast-item");
  });
});
