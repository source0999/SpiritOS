import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  inferFormatTags,
  inferQualityTags,
  inferSourceTokens,
  isPrimarySmartContentTag,
  isRandomOrHashSpiritFlixFilename,
  normalizeSpiritFlixTitle,
  modelIdentityFromPath,
  stripKnownNoiseTokens,
  tokenizeSpiritFlixName,
  type SpiritFlixSmartHeuristicInput,
} from "../heuristics";

function input(overrides: Partial<SpiritFlixSmartHeuristicInput> & Pick<SpiritFlixSmartHeuristicInput, "fileName">): SpiritFlixSmartHeuristicInput {
  const fileName = overrides.fileName;
  const videoPath = overrides.videoPath ?? path.join("/mnt/spirit-8tb/media/yes", fileName);
  return {
    ...overrides,
    videoPath,
    fileName,
    parentPath: overrides.parentPath ?? path.dirname(videoPath),
  };
}

describe("SpiritFlix smart heuristics", () => {
  it("tokenizes filename and path segments", () => {
    const tokens = tokenizeSpiritFlixName("/mnt/media/yes/Example.Site.Name.1080p.x264.mp4");
    expect(tokens).toContain("example");
    expect(tokens).toContain("site");
    expect(tokens).toContain("1080p");
    expect(tokens).toContain("x264");
  });

  it("strips common codec and quality noise", () => {
    expect(stripKnownNoiseTokens("clip.1080p.x264.h264.mkv")).toBe("clip");
    expect(stripKnownNoiseTokens("final.copy.webrip.mp4")).toBe("");
  });

  it("keeps meaningful title tokens", () => {
    expect(normalizeSpiritFlixTitle("Example.Site.Name.1080p.x264.mp4")).toBe("Example Site Name");
    expect(normalizeSpiritFlixTitle("vacation_day_one.mkv")).toBe("vacation day one");
  });

  it("infers container format tags from extension and metadata", () => {
    const tags = inferFormatTags(input({ fileName: "clip.mkv", media: { container: "matroska,webm" } }));
    expect(tags.some((tag) => tag.id === "mkv-container")).toBe(true);
  });

  it("infers vertical from width/height metadata", () => {
    const tags = inferQualityTags(input({ fileName: "clip.mp4", media: { width: 1080, height: 1920 } }));
    expect(tags.some((tag) => tag.id === "vertical")).toBe(true);
  });

  it("infers quality from resolution and filename tokens", () => {
    const fromMeta = inferQualityTags(input({ fileName: "clip.mp4", media: { width: 1920, height: 1080 } }));
    expect(fromMeta.some((tag) => tag.id === "full-hd")).toBe(true);

    const fromName = inferQualityTags(input({ fileName: "clip.720p.mp4" }));
    expect(fromName.some((tag) => tag.id === "hd")).toBe(true);
  });

  it("does not infer visual scene tags from frames", () => {
    const tags = [
      ...inferQualityTags(input({ fileName: "clip.mp4", media: { width: 1920, height: 1080, durationSeconds: 600 } })),
      ...inferFormatTags(input({ fileName: "clip.mp4", media: { durationSeconds: 600 } })),
    ];
    const visualSceneIds = ["oral", "missionary", "doggy", "indoor", "outdoor", "pov"];
    for (const id of visualSceneIds) {
      expect(tags.some((tag) => tag.id === id)).toBe(false);
    }
  });

  it("does not fabricate performer identity", () => {
    const tokens = tokenizeSpiritFlixName("Jane_Doe_Special.1080p.mp4");
    expect(tokens).not.toContain("known-performer");
    expect(inferSourceTokens(input({ fileName: "Jane_Doe_Special.1080p.mp4" }))).toEqual([]);
  });

  it("detects literal source/site tokens only", () => {
    expect(inferSourceTokens(input({ fileName: "onlyfans.leak.clip.mp4" }))).toContain("onlyfans");
    expect(inferSourceTokens(input({ fileName: "random.home.video.mp4" }))).toEqual([]);
  });

  it("handles messy filenames", () => {
    expect(normalizeSpiritFlixTitle("www.site.com___clip.final.copy.1080p.WEB-DL.x265.mp4")).toBe("site clip");
  });

  it("handles short names like 360 1.mp4", () => {
    expect(normalizeSpiritFlixTitle("360 1.mp4")).toBe("360 1");
    expect(stripKnownNoiseTokens("360 1.mp4")).toBe("360 1");
  });

  it("classifies technical/status tags as non-primary smart content", () => {
    const tags = [
      ...inferQualityTags(input({ fileName: "clip.1080p.mp4", media: { width: 1920, height: 1080, durationSeconds: 3600 } })),
      ...inferFormatTags(input({ fileName: "clip.mkv", media: { container: "matroska,webm", durationSeconds: 3600 } })),
      { id: "unknown-performer", label: "unknown performer", group: "performer" as const, confidence: 0.6, evidenceTimestamps: [], reviewRequired: false },
      { id: "needs-title-cleanup", label: "needs title cleanup", group: "safety" as const, confidence: 0.8, evidenceTimestamps: [], reviewRequired: true },
    ];
    const labels = tags.map((tag) => tag.label);
    expect(labels).toEqual(expect.arrayContaining(["full HD", "mkv", "long", "unknown performer", "needs title cleanup"]));
    expect(tags.every((tag) => !isPrimarySmartContentTag(tag))).toBe(true);
  });

  it("detects random/hash filenames and model folder identity", () => {
    expect(isRandomOrHashSpiritFlixFilename(input({ fileName: "HkkzMtwQexuQzwkQMekM.mkv" }))).toBe(true);
    expect(isRandomOrHashSpiritFlixFilename(input({ fileName: "442642.mkv" }))).toBe(true);
    expect(isRandomOrHashSpiritFlixFilename(input({ fileName: "Readable Human Title.mkv" }))).toBe(false);
    expect(modelIdentityFromPath(input({
      fileName: "clip.mkv",
      videoPath: "/mnt/spirit-8tb/media/yes/models/chloe-lamb/clip.mkv",
      parentPath: "/mnt/spirit-8tb/media/yes/models/chloe-lamb",
    }))).toMatchObject({ name: "Chloe Lamb", source: "path" });
  });
});
