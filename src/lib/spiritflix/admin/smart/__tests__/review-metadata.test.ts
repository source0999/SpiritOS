import { describe, expect, it } from "vitest";
import {
  applySmartReviewToAnalysis,
  sanitizeEditedFilenameSuggestion,
  validateSpiritFlixSmartReviewInput,
} from "../review-metadata";
import { validateSpiritFlixSmartAnalysis } from "../types";

const baseAnalysis = validateSpiritFlixSmartAnalysis({
  version: 1,
  videoPath: "/mnt/spirit-8tb/media/yes/clip.mp4",
  pathKey: "abc",
  fileName: "clip.mp4",
  fileSizeBytes: 100,
  mtimeMs: 1,
  analyzedAt: "2026-06-16T00:00:00.000Z",
  analyzerVersion: "spiritflix-smart/s3",
  status: "suggested",
  safety: { safeToSuggest: false, reasons: ["scanner"], requiresHumanReview: true },
  media: { durationSeconds: 90, width: 1280, height: 720, codec: "h264" },
  samples: [
    {
      timestampSeconds: 5,
      timestampLabel: "5s",
      cacheKey: "frame",
      observations: ["sampled frame"],
      tags: [],
      confidence: 0,
    },
  ],
  suggestedTags: [
    { id: "hd", label: "HD", group: "quality", confidence: 0.8, evidenceTimestamps: [], reviewRequired: false },
    { id: "short", label: "short", group: "format", confidence: 0.7, evidenceTimestamps: [], reviewRequired: false },
  ],
  suggestedDisplayTitle: "Clip",
  suggestedFilename: "Clip.mp4",
  suggestedCategory: "yes",
  confidence: 0.75,
  notes: "technical metadata collected | S3 heuristics used filename, path, and technical metadata only.",
});

describe("SpiritFlix smart review metadata", () => {
  it("applies valid review metadata to analysis", () => {
    const updated = applySmartReviewToAnalysis(baseAnalysis, {
      approvedTagIds: ["hd"],
      rejectedTagIds: ["short"],
      editedDisplayTitle: "Reviewed Clip",
      editedFilenameSuggestion: "Reviewed Clip.mp4",
      editedCategory: "yes",
      editedCollections: ["yes"],
      notes: "looks good",
    });

    expect(updated.reviewedMetadata?.reviewStatus).toBe("reviewed");
    expect(updated.reviewedMetadata?.approvedTagIds).toEqual(["hd"]);
    expect(updated.suggestedDisplayTitle).toBe("Clip");
    expect(updated.samples).toEqual(baseAnalysis.samples);
    expect(updated.notes).toContain("technical metadata collected");
  });

  it("rejects unknown tag ids", () => {
    expect(() =>
      validateSpiritFlixSmartReviewInput({ approvedTagIds: ["not-a-real-tag"], rejectedTagIds: [] }),
    ).toThrow(/known tag id/i);
  });

  it("rejects approved/rejected overlap", () => {
    expect(() =>
      validateSpiritFlixSmartReviewInput({ approvedTagIds: ["hd"], rejectedTagIds: ["hd"] }),
    ).toThrow(/overlap/i);
  });

  it("rejects tag ids not present in suggestedTags", () => {
    expect(() =>
      applySmartReviewToAnalysis(baseAnalysis, { approvedTagIds: ["solo"], rejectedTagIds: [] }),
    ).toThrow(/not in suggestedTags/i);
  });

  it("sanitizes edited filename suggestion and preserves extension", () => {
    expect(sanitizeEditedFilenameSuggestion('bad:name?.mp4', "clip.mp4")).toBe("bad name.mp4");
    expect(sanitizeEditedFilenameSuggestion("Title Only", "clip.mp4")).toBe("Title Only.mp4");
  });

  it("marks all rejected tags as rejected review status", () => {
    const updated = applySmartReviewToAnalysis(baseAnalysis, {
      approvedTagIds: [],
      rejectedTagIds: ["hd", "short"],
    });
    expect(updated.reviewedMetadata?.reviewStatus).toBe("rejected");
    expect(updated.status).toBe("rejected");
  });
});
