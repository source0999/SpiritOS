import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createSmartAnalysisPathKey, getSmartAnalysisRoot } from "../analysis-paths";
import { writeSmartAnalysis } from "../analysis-store";
import {
  applySpiritFlixReviewSuggestionsToAnalysis,
  buildSpiritFlixReviewSuggestions,
  buildSuggestedFilename,
  updateSmartAnalysisWithHeuristicSuggestions,
} from "../suggestions";
import { validateSpiritFlixSmartAnalysis } from "../types";

describe("SpiritFlix smart suggestions", () => {
  let mediaRoot = "";
  let videoPath = "";

  beforeEach(async () => {
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-s3-"));
    const videoDir = path.join(mediaRoot, "yes", "nested");
    await fs.mkdir(videoDir, { recursive: true });
    videoPath = path.join(videoDir, "360 1.mp4");
    await fs.writeFile(videoPath, "fake-video");
  });

  afterEach(async () => {
    await fs.rm(mediaRoot, { force: true, recursive: true });
  });

  it("builds review-only suggestions for short ambiguous filenames", () => {
    const result = buildSpiritFlixReviewSuggestions({
      videoPath,
      fileName: "360 1.mp4",
      parentPath: path.dirname(videoPath),
    });

    expect(result.suggestedDisplayTitle).toBe("360 1");
    expect(result.suggestedFilename).toBe("360 1.mp4");
    expect(result.notes.some((note) => /insufficient filename context/i.test(note))).toBe(true);
    expect(result.suggestedTags.some((tag) => tag.id === "needs-title-cleanup")).toBe(true);
    expect(result.suggestedTags.some((tag) => tag.id === "unknown-performer")).toBe(true);
  });

  it("builds richer suggestions for site/quality filenames", () => {
    const messyPath = path.join(mediaRoot, "yes", "Example.Site.Name.1080p.x264.mp4");
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: messyPath,
      fileName: "Example.Site.Name.1080p.x264.mp4",
      parentPath: path.join(mediaRoot, "yes"),
      media: { width: 1920, height: 1080, durationSeconds: 600 },
    });

    expect(result.suggestedDisplayTitle).toBe("Example Site Name");
    expect(result.suggestedFilename).toMatch(/Example Site Name.*\.mp4$/);
    expect(result.suggestedTags.some((tag) => tag.id === "full-hd")).toBe(true);
    expect(result.suggestedCategory).toBe("yes");
    expect(result.confidence).toBeGreaterThan(0);
  });

  it("preserves file extension in suggested filename", () => {
    const mkvPath = path.join(mediaRoot, "movies", "title.mkv");
    const filename = buildSuggestedFilename(
      { videoPath: mkvPath, fileName: "title.mkv" },
      [],
    );
    expect(filename.endsWith(".mkv")).toBe(true);
  });

  it("sanitizes suggested filename", () => {
    const filename = buildSuggestedFilename(
      { videoPath, fileName: 'bad:name?.mp4' },
      [],
    );
    expect(filename).not.toMatch(/[:?]/);
    expect(filename.endsWith(".mp4")).toBe(true);
  });

  it("keeps suggested filename concise", () => {
    const longStem = "a".repeat(200);
    const filename = buildSuggestedFilename(
      { videoPath, fileName: `${longStem}.mp4` },
      [],
    );
    expect(path.basename(filename, ".mp4").length).toBeLessThanOrEqual(120);
  });

  it("sets reviewRequired on uncertain source tags", () => {
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: path.join(mediaRoot, "yes", "onlyfans.clip.mp4"),
      fileName: "onlyfans.clip.mp4",
      parentPath: path.join(mediaRoot, "yes"),
    });
    const siteTag = result.suggestedTags.find((tag) => tag.id === "site-token");
    expect(siteTag?.reviewRequired).toBe(true);
  });

  it("sets needs_review or suggested, never approved", () => {
    const base = validateSpiritFlixSmartAnalysis({
      version: 1,
      videoPath,
      pathKey: "abc",
      fileName: "360 1.mp4",
      fileSizeBytes: 10,
      mtimeMs: 1,
      analyzedAt: new Date().toISOString(),
      analyzerVersion: "spiritflix-smart/s2",
      status: "needs_review",
      safety: { safeToSuggest: false, reasons: [], requiresHumanReview: true },
      media: {},
      samples: [],
      suggestedTags: [],
      confidence: 0,
    });

    const suggestions = buildSpiritFlixReviewSuggestions({ videoPath, fileName: "360 1.mp4" });
    const updated = applySpiritFlixReviewSuggestionsToAnalysis(base, suggestions);
    expect(["needs_review", "suggested"]).toContain(updated.status);
    expect(updated.status).not.toBe("approved");
  });

  it("preserves S2 media metadata and samples when applying suggestions", () => {
    const base = validateSpiritFlixSmartAnalysis({
      version: 1,
      videoPath,
      pathKey: "abc",
      fileName: "clip.mp4",
      fileSizeBytes: 10,
      mtimeMs: 1,
      analyzedAt: new Date().toISOString(),
      analyzerVersion: "spiritflix-smart/s2",
      status: "needs_review",
      safety: { safeToSuggest: false, reasons: [], requiresHumanReview: true },
      media: { durationSeconds: 90, width: 1280, height: 720, codec: "h264", container: "mp4" },
      samples: [
        {
          timestampSeconds: 12,
          timestampLabel: "12s",
          cacheKey: "frame-key",
          observations: ["sampled frame"],
          tags: [],
          confidence: 0,
        },
      ],
      suggestedTags: [],
      confidence: 0,
      notes: "technical metadata collected",
    });

    const suggestions = buildSpiritFlixReviewSuggestions({
      videoPath,
      fileName: "clip.mp4",
      media: base.media,
    });
    const updated = applySpiritFlixReviewSuggestionsToAnalysis(base, suggestions);

    expect(updated.media).toEqual(base.media);
    expect(updated.samples).toEqual(base.samples);
    expect(updated.notes).toContain("technical metadata collected");
    expect(updated.suggestedTags.length).toBeGreaterThan(0);
  });

  it("writes sidecar only under analysis root", async () => {
    const stat = await fs.stat(videoPath);
    const analysis = await updateSmartAnalysisWithHeuristicSuggestions(
      {
        videoPath,
        fileName: "360 1.mp4",
        fileSizeBytes: stat.size,
        mtimeMs: stat.mtimeMs,
      },
      { mediaRoot },
    );

    const sidecarPath = path.join(getSmartAnalysisRoot({ mediaRoot }), `${analysis.pathKey}.json`);
    await expect(fs.stat(sidecarPath)).resolves.toBeDefined();
    expect(sidecarPath.startsWith(getSmartAnalysisRoot({ mediaRoot }))).toBe(true);
    expect(path.dirname(sidecarPath)).not.toBe(path.dirname(videoPath));
  });

  it("does not import or call Level 2 actions", async () => {
    const source = await fs.readFile(path.join(process.cwd(), "src/lib/spiritflix/admin/smart/suggestions.ts"), "utf8");
    expect(source).not.toMatch(/level-?2|executeSpiritFlix|previewAction|confirmAction|from "\.\.\/actions"/i);
  });

  it("rejects traversal/outside-root through existing path helpers", async () => {
    await expect(
      updateSmartAnalysisWithHeuristicSuggestions(
        { videoPath: "/tmp/outside.mp4", fileName: "outside.mp4" },
        { mediaRoot },
      ),
    ).rejects.toThrow(/outside/i);
  });

  it("updates existing sidecar while preserving prior scanner notes and samples", async () => {
    const stat = await fs.stat(videoPath);
    const pathKey = createSmartAnalysisPathKey({
      videoPath,
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
    });
    const existing = validateSpiritFlixSmartAnalysis({
      version: 1,
      videoPath,
      pathKey,
      fileName: "360 1.mp4",
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
      analyzedAt: new Date().toISOString(),
      analyzerVersion: "spiritflix-smart/s2",
      status: "needs_review",
      safety: { safeToSuggest: false, reasons: ["scanner"], requiresHumanReview: true },
      media: { durationSeconds: 45, width: 720, height: 1280 },
      samples: [
        {
          timestampSeconds: 5,
          timestampLabel: "5s",
          cacheKey: "cached-frame",
          observations: ["sampled frame"],
          tags: [],
          confidence: 0,
        },
      ],
      suggestedTags: [],
      confidence: 0,
      notes: "technical metadata collected",
    });

    await writeSmartAnalysis(existing, { mediaRoot });

    const updated = await updateSmartAnalysisWithHeuristicSuggestions(
      {
        videoPath,
        fileName: "360 1.mp4",
        fileSizeBytes: stat.size,
        mtimeMs: stat.mtimeMs,
        media: { durationSeconds: 45, width: 720, height: 1280 },
      },
      { mediaRoot },
    );

    expect(updated.samples).toHaveLength(1);
    expect(updated.samples[0]?.cacheKey).toBe("cached-frame");
    expect(updated.media.durationSeconds).toBe(45);
    expect(updated.notes).toContain("technical metadata collected");
    expect(updated.suggestedTags.length).toBeGreaterThan(0);
  });
});
