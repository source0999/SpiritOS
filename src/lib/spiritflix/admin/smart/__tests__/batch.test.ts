import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createSmartAnalysisPathKey } from "../analysis-paths";
import { previewSpiritFlixSmartBatch, reviewSpiritFlixSmartBatch, runSpiritFlixSmartBatch } from "../batch";
import { readSmartAnalysis } from "../analysis-store";
import { writeSmartAnalysis } from "../analysis-store";
import { validateSpiritFlixSmartAnalysis, type SpiritFlixSmartAnalysis } from "../types";

let tempRoot = "";
let originalRoots: string | undefined;

async function writeVideo(relativePath: string, content = "fake-video") {
  const videoPath = path.join(tempRoot, relativePath);
  await fs.mkdir(path.dirname(videoPath), { recursive: true });
  await fs.writeFile(videoPath, content);
  return videoPath;
}

async function currentAnalysis(videoPath: string, overrides: Partial<SpiritFlixSmartAnalysis> = {}) {
  const stat = await fs.stat(videoPath);
  const analysis = validateSpiritFlixSmartAnalysis({
    version: 1,
    videoPath,
    pathKey: createSmartAnalysisPathKey({ videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs }),
    fileName: path.basename(videoPath),
    fileSizeBytes: stat.size,
    mtimeMs: stat.mtimeMs,
    analyzedAt: "2026-06-18T00:00:00.000Z",
    analyzerVersion: "spiritflix-smart/s5",
    status: "suggested",
    safety: { safeToSuggest: false, reasons: ["test"], requiresHumanReview: true },
    media: { durationSeconds: 60 },
    samples: [],
    suggestedTags: [{ id: "hd", label: "HD", group: "quality", confidence: 0.8, evidenceTimestamps: [], reviewRequired: false }],
    suggestedDisplayTitle: "Clip",
    suggestedFilename: "Clip Better.mp4",
    confidence: 0.8,
    ...overrides,
  });
  await writeSmartAnalysis(analysis, { mediaRoot: tempRoot });
  return analysis;
}

describe("SpiritFlix smart batch analysis", () => {
  beforeEach(async () => {
    originalRoots = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-smart-batch-"));
    process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = tempRoot;
  });

  afterEach(async () => {
    if (originalRoots === undefined) delete process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    else process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = originalRoots;
    await fs.rm(tempRoot, { force: true, recursive: true });
  });

  it("previews eligible videos in a bounded folder scan", async () => {
    await writeVideo("yes/clip-a.mp4");
    await writeVideo("yes/clip-b.mkv");
    await fs.writeFile(path.join(tempRoot, "yes/readme.txt"), "skip");

    const preview = await previewSpiritFlixSmartBatch({ path: path.join(tempRoot, "yes"), maxItems: 1 });

    expect(preview.schema).toBe("spiritflix-smart-batch/v1");
    expect(preview.mode).toBe("preview");
    expect(preview.items).toHaveLength(1);
    expect(preview.counts.candidates).toBe(1);
    expect(preview.items[0].status).toBe("candidate");
  });

  it("skips current sidecars unless force is requested", async () => {
    const videoPath = await writeVideo("yes/current.mp4");
    await currentAnalysis(videoPath);
    const analyzeVideo = vi.fn();

    const result = await runSpiritFlixSmartBatch({
      path: path.join(tempRoot, "yes"),
      analyzeVideo,
    } as Parameters<typeof runSpiritFlixSmartBatch>[0]);

    expect(result.counts.already_current).toBe(1);
    expect(analyzeVideo).not.toHaveBeenCalled();
  });

  it("runs analysis and preserves existing reviewed metadata on refresh", async () => {
    const videoPath = await writeVideo("yes/reviewed.mp4");
    const reviewedMetadata = {
      reviewedAt: "2026-06-18T00:00:00.000Z",
      reviewedBy: "spiritflix-admin" as const,
      reviewStatus: "reviewed" as const,
      approvedTagIds: ["hd"],
      rejectedTagIds: [],
      editedFilenameSuggestion: "Reviewed Name.mp4",
    };
    const existing = await currentAnalysis(videoPath, { reviewedMetadata });
    const analyzeVideo = vi.fn(async () => validateSpiritFlixSmartAnalysis({
      ...existing,
      analyzedAt: "2026-06-18T01:00:00.000Z",
      reviewedMetadata,
      suggestedFilename: "Refreshed Name.mp4",
    }));

    const result = await runSpiritFlixSmartBatch({
      path: path.join(tempRoot, "yes"),
      force: true,
      analyzeVideo,
    } as Parameters<typeof runSpiritFlixSmartBatch>[0]);

    expect(result.counts.analyzed).toBe(1);
    expect(result.counts.rename_preview_available).toBe(1);
    expect(result.items[0].reviewStatus).toBe("reviewed");
    expect(analyzeVideo).toHaveBeenCalledWith(videoPath, expect.objectContaining({ mediaRoot: tempRoot }));
  });

  it("reports per-item failures without throwing the whole batch", async () => {
    await writeVideo("yes/broken.mp4");
    const analyzeVideo = vi.fn(async () => {
      throw new Error("ffprobe failed for test");
    });

    const result = await runSpiritFlixSmartBatch({
      path: path.join(tempRoot, "yes"),
      analyzeVideo,
    } as Parameters<typeof runSpiritFlixSmartBatch>[0]);

    expect(result.counts.failed).toBe(1);
    expect(result.items[0].reason).toMatch(/ffprobe failed/i);
  });

  it("batch approves suggested tags while preserving edited review fields", async () => {
    const videoPath = await writeVideo("yes/to-approve.mp4");
    await currentAnalysis(videoPath, {
      reviewedMetadata: {
        reviewedAt: "2026-06-18T00:00:00.000Z",
        reviewedBy: "spiritflix-admin",
        reviewStatus: "partially_reviewed",
        approvedTagIds: [],
        rejectedTagIds: [],
        editedDisplayTitle: "Keep Title",
        editedFilenameSuggestion: "Keep Filename.mp4",
      },
    });

    const result = await reviewSpiritFlixSmartBatch({
      path: path.join(tempRoot, "yes"),
      reviewMode: "approve_all_tags",
    });
    const stat = await fs.stat(videoPath);
    const saved = await readSmartAnalysis({ videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs }, { mediaRoot: tempRoot });

    expect(result.counts.analyzed).toBe(1);
    expect(saved?.reviewedMetadata?.reviewStatus).toBe("reviewed");
    expect(saved?.reviewedMetadata?.approvedTagIds).toEqual(["hd"]);
    expect(saved?.reviewedMetadata?.editedDisplayTitle).toBe("Keep Title");
  });

  it("batch rejects suggested tags and marks the video rejected", async () => {
    const videoPath = await writeVideo("yes/to-reject.mp4");
    await currentAnalysis(videoPath);

    await reviewSpiritFlixSmartBatch({
      path: path.join(tempRoot, "yes"),
      reviewMode: "reject_all_tags",
    });
    const stat = await fs.stat(videoPath);
    const saved = await readSmartAnalysis({ videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs }, { mediaRoot: tempRoot });

    expect(saved?.reviewedMetadata?.reviewStatus).toBe("rejected");
    expect(saved?.reviewedMetadata?.rejectedTagIds).toEqual(["hd"]);
  });

  it("batch mark reviewed skips videos without analysis sidecars", async () => {
    await writeVideo("yes/no-sidecar.mp4");

    const result = await reviewSpiritFlixSmartBatch({
      path: path.join(tempRoot, "yes"),
      reviewMode: "mark_reviewed",
    });

    expect(result.counts.skipped).toBe(1);
    expect(result.items[0].reason).toMatch(/no smart analysis/i);
  });
});
