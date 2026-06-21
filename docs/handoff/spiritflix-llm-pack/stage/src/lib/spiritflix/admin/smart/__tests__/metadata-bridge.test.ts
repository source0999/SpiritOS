import { describe, expect, it } from "vitest";
import { projectApprovedSmartMetadata, metadataSidecarPath } from "../metadata-bridge";
import { validateSpiritFlixSmartAnalysis } from "../types";

const baseAnalysis = validateSpiritFlixSmartAnalysis({
  version: 1,
  videoPath: "/mnt/spirit-8tb/media/yes/clip.mp4",
  pathKey: "abc",
  fileName: "clip.mp4",
  fileSizeBytes: 100,
  mtimeMs: 1,
  analyzedAt: "2026-06-16T00:00:00.000Z",
  analyzerVersion: "spiritflix-smart/s5",
  status: "approved",
  safety: { safeToSuggest: false, reasons: ["scanner"], requiresHumanReview: true },
  media: { durationSeconds: 90, width: 1280, height: 720, codec: "h264" },
  samples: [],
  suggestedTags: [
    { id: "hd", label: "HD", group: "quality", confidence: 0.8, evidenceTimestamps: [], reviewRequired: false },
    { id: "short", label: "short", group: "format", confidence: 0.7, evidenceTimestamps: [], reviewRequired: false },
  ],
  suggestedDisplayTitle: "Original Title",
  suggestedFilename: "Original Title.mp4",
  suggestedCategory: "original-cat",
  suggestedCollections: ["collection-a"],
  confidence: 0.75,
  reviewedMetadata: {
    reviewedAt: "2026-06-17T00:00:00.000Z",
    reviewedBy: "spiritflix-admin",
    reviewStatus: "reviewed",
    approvedTagIds: ["hd"],
    rejectedTagIds: ["short"],
    editedDisplayTitle: "Edited Title",
    editedFilenameSuggestion: "Edited Title.mp4",
    editedCategory: "edited-cat",
    editedCollections: ["collection-b"],
    notes: "user note",
  },
});

const unreviewedAnalysis = validateSpiritFlixSmartAnalysis({
  version: 1,
  videoPath: "/mnt/spirit-8tb/media/yes/unreviewed.mp4",
  pathKey: "def",
  fileName: "unreviewed.mp4",
  fileSizeBytes: 200,
  mtimeMs: 2,
  analyzedAt: "2026-06-16T00:00:00.000Z",
  analyzerVersion: "spiritflix-smart/s3",
  status: "suggested",
  safety: { safeToSuggest: true, reasons: [], requiresHumanReview: false },
  media: {},
  samples: [],
  suggestedTags: [
    { id: "hd", label: "HD", group: "quality", confidence: 0.9, evidenceTimestamps: [], reviewRequired: false },
  ],
  suggestedDisplayTitle: "Auto Title",
  suggestedFilename: "Auto Title.mp4",
  suggestedCategory: "auto-cat",
  suggestedCollections: ["auto-coll"],
  confidence: 0.9,
});

describe("SpiritFlix smart metadata bridge", () => {
  it("prefers edited values over suggestions", () => {
    const projection = projectApprovedSmartMetadata(baseAnalysis);
    expect(projection.displayTitle).toBe("Edited Title");
    expect(projection.filenameSuggestion).toBe("Edited Title.mp4");
    expect(projection.category).toBe("edited-cat");
    expect(projection.collections).toEqual(["collection-b"]);
    expect(projection.notes).toBe("user note");
  });

  it("falls back to suggestions when no edits exist", () => {
    const projection = projectApprovedSmartMetadata(unreviewedAnalysis);
    expect(projection.displayTitle).toBe("Auto Title");
    expect(projection.filenameSuggestion).toBe("Auto Title.mp4");
    expect(projection.category).toBe("auto-cat");
    expect(projection.collections).toEqual(["auto-coll"]);
  });

  it("approved tags come only from approvedTagIds and vocabulary", () => {
    const projection = projectApprovedSmartMetadata(baseAnalysis);
    expect(projection.approvedTags).toHaveLength(1);
    expect(projection.approvedTags[0].id).toBe("hd");
  });

  it("rejected tags are recorded but not active", () => {
    const projection = projectApprovedSmartMetadata(baseAnalysis);
    expect(projection.rejectedTagIds).toEqual(["short"]);
    // short is rejected, so it should NOT be in approvedTags
    expect(projection.approvedTags.find((t) => t.id === "short")).toBeUndefined();
  });

  it("reviewStatus comes from reviewedMetadata", () => {
    const projection = projectApprovedSmartMetadata(baseAnalysis);
    expect(projection.reviewStatus).toBe("reviewed");
    expect(projection.reviewedAt).toBe("2026-06-17T00:00:00.000Z");
  });

  it("defaults reviewStatus to unreviewed when no reviewedMetadata", () => {
    const projection = projectApprovedSmartMetadata(unreviewedAnalysis);
    expect(projection.reviewStatus).toBe("unreviewed");
    expect(projection.reviewedAt).toBeUndefined();
  });

  it("sourcePath comes from analysis.videoPath", () => {
    const projection = projectApprovedSmartMetadata(baseAnalysis);
    expect(projection.sourcePath).toBe("/mnt/spirit-8tb/media/yes/clip.mp4");
  });

  it("metadata sidecar path stays under .spiritflix-admin/metadata", () => {
    const sidecarPath = metadataSidecarPath("/mnt/spirit-8tb/media/yes/clip.mp4");
    expect(sidecarPath).toContain(".spiritflix-admin/metadata");
    expect(sidecarPath).not.toContain("/yes/");
    expect(sidecarPath).toMatch(/\.json$/);
  });

  it("metadata sidecar path uses sha256 of normalized path", () => {
    const path1 = metadataSidecarPath("/mnt/spirit-8tb/media/yes/clip.mp4");
    const path2 = metadataSidecarPath("C:\\mnt\\spirit-8tb\\media\\yes\\clip.mp4"); // windows-ish
    const path3 = metadataSidecarPath("/mnt/spirit-8tb/media/yes/clip.mp4");
    // Same path lowercase normalized -> same hash
    expect(path1).toBe(path3);
    // Forward slash normalization should make path1 == path2
    expect(path1).toBe(path2);
  });

  it("metadata sidecar path supports custom mediaRoot", () => {
    const sidecarPath = metadataSidecarPath("/media/test.mp4", "/media");
    expect(sidecarPath).toContain("/media/.spiritflix-admin/metadata");
  });

  it("filename suggestion is metadata-only (not mutating real files)", () => {
    const projection = projectApprovedSmartMetadata(baseAnalysis);
    // The projection contains a filenameSuggestion field — it is a suggestion string, not a file operation.
    expect(typeof projection.filenameSuggestion).toBe("string");
    expect(projection.filenameSuggestion).toBe("Edited Title.mp4");
  });
});
