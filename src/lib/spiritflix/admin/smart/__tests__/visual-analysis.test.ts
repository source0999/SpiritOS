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
    expect(updated.visualAnalysis).toMatchObject({
      status: "complete",
      modelName: "test-vision",
      sampledFrameCount: 1,
      analyzedFrameCount: 1,
      tags: ["watermark"],
    });
    expect(updated.notes).toContain("test-vision");
  });

  it("drops generic scene visual tags while preserving relevant content tags", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Response.json({
      response: JSON.stringify({
        tags: [
          { id: "solo", confidence: 0.9 },
          { id: "indoor", confidence: 0.8 },
          { id: "brunette", confidence: 0.78 },
          { id: "duo", confidence: 0.76 },
          { id: "group", confidence: 0.74 },
          { id: "outdoor", confidence: 0.72 },
          { id: "curvy", confidence: 0.68 },
        ],
        observations: ["second person visible outdoors"],
        confidence: 0.76,
      }),
    })));

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

    const ids = updated.samples[0].tags.map((tag) => tag.id);
    expect(ids).toEqual(["curvy"]);
    expect(ids).not.toContain("solo");
    expect(ids).not.toContain("duo");
    expect(ids).not.toContain("group");
    expect(ids).not.toContain("indoor");
    expect(ids).not.toContain("outdoor");
    expect(ids).not.toContain("brunette");
  });
});
