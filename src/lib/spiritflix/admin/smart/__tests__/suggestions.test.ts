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

    expect(result.suggestedDisplayTitle).toBe("Unknown Model - Untitled 01");
    expect(result.suggestedFilename).toBe("Unknown Model - Untitled 01");
    expect(result.notes.some((note) => /insufficient filename context/i.test(note))).toBe(true);
    expect(result.notes.some((note) => /needs title cleanup status/i.test(note))).toBe(true);
    expect(result.suggestedTags.some((tag) => tag.id === "needs-title-cleanup")).toBe(false);
    expect(result.suggestedTags.some((tag) => tag.id === "unknown-performer")).toBe(false);
    expect(result.performerIdentity.name).toBe("Unknown Model");
  });

  it("preserves readable titles while excluding technical metadata from primary tags", () => {
    const messyPath = path.join(mediaRoot, "yes", "Example.Site.Name.1080p.x264.mp4");
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: messyPath,
      fileName: "Example.Site.Name.1080p.x264.mp4",
      parentPath: path.join(mediaRoot, "yes"),
      media: { width: 1920, height: 1080, durationSeconds: 600 },
    });

    expect(result.suggestedDisplayTitle).toBe("Example Site Name");
    expect(result.suggestedFilename).toBe("Example Site Name");
    expect(result.suggestedTags.some((tag) => tag.id === "full-hd")).toBe(false);
    expect(result.contentTagEvidence.find((entry) => entry.source === "metadata")?.tags).toContain("full-hd");
    expect(result.suggestedCategory).toBe("yes");
    expect(result.confidence).toBeGreaterThan(0);
  });

  it("uses visual content tags for recommended names even when the source title is readable", () => {
    const readablePath = path.join(mediaRoot, "yes", "models", "aaliyah-yasan", "Readable Scene Title.mkv");
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: readablePath,
      fileName: "Readable Scene Title.mkv",
      parentPath: path.dirname(readablePath),
    }, {
      analysis: validateSpiritFlixSmartAnalysis({
        version: 1,
        videoPath: readablePath,
        pathKey: "readable",
        fileName: "Readable Scene Title.mkv",
        fileSizeBytes: 10,
        mtimeMs: 1,
        analyzedAt: "2026-06-20T00:00:00.000Z",
        analyzerVersion: "spiritflix-smart/s9",
        status: "needs_review",
        safety: { safeToSuggest: false, reasons: ["visual"], requiresHumanReview: true },
        media: {},
        samples: [{
          timestampSeconds: 5,
          timestampLabel: "5s",
          cacheKey: "frame-key",
          observations: ["vlm"],
          tags: [
            { id: "solo", label: "solo", group: "scene", confidence: 0.8, evidenceTimestamps: [5], reviewRequired: true },
            { id: "indoor", label: "indoor", group: "scene", confidence: 0.7, evidenceTimestamps: [5], reviewRequired: true },
          ],
          confidence: 0.8,
        }],
        suggestedTags: [],
        confidence: 0,
      }),
    });

    expect(result.suggestedDisplayTitle).toBe("Aaliyah Yasan - solo indoor 01");
  });

  it("omits file extension in suggested display filename", () => {
    const mkvPath = path.join(mediaRoot, "movies", "title.mkv");
    const filename = buildSuggestedFilename(
      { videoPath: mkvPath, fileName: "title.mkv" },
      [],
    );
    expect(filename).toBe("title");
  });

  it("sanitizes suggested filename", () => {
    const filename = buildSuggestedFilename(
      { videoPath, fileName: 'bad:name?.mp4' },
      [],
    );
    expect(filename).not.toMatch(/[:?]/);
    expect(filename).not.toMatch(/\.mp4$/);
  });

  it("keeps suggested filename concise", () => {
    const longStem = "a".repeat(200);
    const filename = buildSuggestedFilename(
      { videoPath, fileName: `${longStem}.mp4` },
      [],
    );
    expect(filename.length).toBeLessThanOrEqual(120);
  });

  it("sets reviewRequired on uncertain source tags", () => {
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: path.join(mediaRoot, "yes", "onlyfans.clip.mp4"),
      fileName: "onlyfans.clip.mp4",
      parentPath: path.join(mediaRoot, "yes"),
    });
    expect(result.suggestedTags.find((tag) => tag.id === "site-token")).toBeUndefined();
    expect(result.contentTagEvidence.find((entry) => entry.source === "metadata")?.tags).toContain("site-token");
  });

  it("uses model folder identity for random/hash filenames", () => {
    const randomPath = path.join(mediaRoot, "yes", "models", "aaliyah-yasan", "HkkzMtwQexuQzwkQMekM.mkv");
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: randomPath,
      fileName: "HkkzMtwQexuQzwkQMekM.mkv",
      parentPath: path.dirname(randomPath),
    });

    expect(result.performerIdentity).toMatchObject({ name: "Aaliyah Yasan", source: "path" });
    expect(result.suggestedDisplayTitle).toBe("Aaliyah Yasan - Untitled 01");
    expect(result.suggestedFilename).toBe("Aaliyah Yasan - Untitled 01");
  });

  it("uses model and visual tags for source-spam filenames", () => {
    const spamPath = path.join(mediaRoot, "yes", "models", "aaliyah-yasan", "Visit onlyshare.io for MORE 130.mkv");
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: spamPath,
      fileName: "Visit onlyshare.io for MORE 130.mkv",
      parentPath: path.dirname(spamPath),
    }, {
      analysis: validateSpiritFlixSmartAnalysis({
        version: 1,
        videoPath: spamPath,
        pathKey: "abc",
        fileName: "Visit onlyshare.io for MORE 130.mkv",
        fileSizeBytes: 10,
        mtimeMs: 1,
        analyzedAt: "2026-06-20T00:00:00.000Z",
        analyzerVersion: "spiritflix-smart/s9",
        status: "needs_review",
        safety: { safeToSuggest: false, reasons: ["visual"], requiresHumanReview: true },
        media: {},
        samples: [{
          timestampSeconds: 5,
          timestampLabel: "5s",
          cacheKey: "frame-key",
          observations: ["vlm: indoor scene"],
          tags: [
            { id: "solo", label: "solo", group: "scene", confidence: 0.8, evidenceTimestamps: [5], reviewRequired: true },
            { id: "indoor", label: "indoor", group: "scene", confidence: 0.7, evidenceTimestamps: [5], reviewRequired: true },
          ],
          confidence: 0.8,
        }],
        suggestedTags: [],
        confidence: 0,
      }),
    });

    expect(result.performerIdentity).toMatchObject({ name: "Aaliyah Yasan", source: "path" });
    expect(result.suggestedDisplayTitle).toBe("Aaliyah Yasan - solo indoor 130");
  });

  it("uses useful numeric source ids before quality tokens for visual tag names", () => {
    const numericPath = path.join(mediaRoot, "yes", "models", "aaliyah-yasan", "540598_720p.mkv");
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: numericPath,
      fileName: "540598_720p.mkv",
      parentPath: path.dirname(numericPath),
    }, {
      analysis: validateSpiritFlixSmartAnalysis({
        version: 1,
        videoPath: numericPath,
        pathKey: "numeric",
        fileName: "540598_720p.mkv",
        fileSizeBytes: 10,
        mtimeMs: 1,
        analyzedAt: "2026-06-20T00:00:00.000Z",
        analyzerVersion: "spiritflix-smart/s9",
        status: "needs_review",
        safety: { safeToSuggest: false, reasons: ["visual"], requiresHumanReview: true },
        media: {},
        samples: [{
          timestampSeconds: 5,
          timestampLabel: "5s",
          cacheKey: "frame-key",
          observations: ["sampled frame"],
          tags: [
            { id: "solo", label: "solo", group: "scene", confidence: 0.8, evidenceTimestamps: [5], reviewRequired: true },
            { id: "indoor", label: "indoor", group: "scene", confidence: 0.7, evidenceTimestamps: [5], reviewRequired: true },
          ],
          confidence: 0.8,
        }],
        suggestedTags: [],
        confidence: 0,
      }),
    });

    expect(result.suggestedDisplayTitle).toBe("Aaliyah Yasan - solo indoor 540598");
  });

  it("uses Unknown Model fallback for numeric filenames without useful tags", () => {
    const result = buildSpiritFlixReviewSuggestions({
      videoPath: path.join(mediaRoot, "yes", "442642.mkv"),
      fileName: "442642.mkv",
      parentPath: path.join(mediaRoot, "yes"),
    });

    expect(result.performerIdentity).toMatchObject({ name: "Unknown Model", source: "unknown" });
    expect(result.suggestedDisplayTitle).toBe("Unknown Model - Untitled 01");
  });

  it("uses read-only face identity when supplied by safe evidence lookup", () => {
    const result = buildSpiritFlixReviewSuggestions(
      {
        videoPath: path.join(mediaRoot, "yes", "HkkzMtwQexuQzwkQMekM.mkv"),
        fileName: "HkkzMtwQexuQzwkQMekM.mkv",
        parentPath: path.join(mediaRoot, "yes"),
      },
      {
        performerIdentity: {
          name: "Chloe Lamb",
          source: "face_rec",
          confidence: 1,
          evidenceRef: "scripts/media/performer_verification.json",
          requiresReview: false,
        },
      },
    );

    expect(result.performerIdentity).toMatchObject({ name: "Chloe Lamb", source: "face_rec" });
    expect(result.suggestedDisplayTitle).toBe("Chloe Lamb - Untitled 01");
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
    expect(updated.suggestedTags.some((tag) => tag.id === "hd")).toBe(false);
    expect(updated.contentTagEvidence?.find((entry) => entry.source === "metadata")?.tags).toContain("hd");
    expect(updated.performerIdentity?.name).toBe("Unknown Model");
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
    expect(updated.contentTagEvidence?.find((entry) => entry.source === "metadata")?.tags).toContain("full-hd");
    expect(updated.suggestedTags.some((tag) => tag.id === "hd")).toBe(false);
  });
});
