import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { applyLocalVisualAnalysisToSpiritFlixAnalysis } from "../visual-analysis";
import { validateSpiritFlixSmartAnalysis } from "../types";

describe("SpiritFlix local visual analysis", () => {
  let mediaRoot = "";
  let videoPath = "";

  beforeEach(async () => {
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-visual-"));
    videoPath = path.join(mediaRoot, "yes", "clip.mp4");
    await fs.mkdir(path.dirname(videoPath), { recursive: true });
    await fs.writeFile(videoPath, "fake-video");
    await fs.mkdir(path.join(mediaRoot, ".spiritflix-admin", "analysis-cache", "frames"), { recursive: true });
    await fs.writeFile(path.join(mediaRoot, ".spiritflix-admin", "analysis-cache", "frames", "frame-key.jpg"), "jpeg");
    vi.stubGlobal("fetch", vi.fn(async () => Response.json({
      response: JSON.stringify({
        tags: [{ id: "watermark", confidence: 0.74, evidence: "visible logo" }],
        observations: ["visible logo"],
        confidence: 0.74,
      }),
    })));
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    await fs.rm(mediaRoot, { force: true, recursive: true });
  });

  it("turns cached frame model output into review-required sample tags and VLM evidence", async () => {
    const analysis = validateSpiritFlixSmartAnalysis({
      version: 1,
      videoPath,
      pathKey: "abc",
      fileName: "clip.mp4",
      fileSizeBytes: 10,
      mtimeMs: 1,
      analyzedAt: "2026-06-20T00:00:00.000Z",
      analyzerVersion: "spiritflix-smart/s2",
      status: "needs_review",
      safety: { safeToSuggest: false, reasons: ["scanner"], requiresHumanReview: true },
      media: { durationSeconds: 60 },
      samples: [{
        timestampSeconds: 5,
        timestampLabel: "5s",
        cacheKey: "frame-key",
        observations: ["sampled frame"],
        tags: [],
        confidence: 0,
      }],
      suggestedTags: [],
      confidence: 0,
    });

    const updated = await applyLocalVisualAnalysisToSpiritFlixAnalysis(analysis, {
      mediaRoot,
      ollamaModel: "test-vision",
      timeoutMs: 1_000,
    });

    expect(updated.samples[0].tags[0]).toMatchObject({
      id: "watermark",
      reviewRequired: true,
      evidenceTimestamps: [5],
    });
    expect(updated.contentTagEvidence?.find((entry) => entry.source === "vlm")).toMatchObject({
      tags: ["watermark"],
      evidenceRef: "test-vision",
      requiresReview: true,
    });
    expect(updated.notes).toContain("test-vision");
  });
});
