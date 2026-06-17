import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { getSmartAnalysisRoot } from "../analysis-paths";
import {
  createEmptySmartAnalysis,
  readSmartAnalysis,
  writeSmartAnalysis,
} from "../analysis-store";
import { validateSpiritFlixSmartAnalysis } from "../types";

describe("SpiritFlix smart analysis store", () => {
  let mediaRoot = "";
  let videoPath = "";

  beforeEach(async () => {
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-smart-store-"));
    const videoDir = path.join(mediaRoot, "yes", "nested");
    await fs.mkdir(videoDir, { recursive: true });
    videoPath = path.join(videoDir, "sample.mp4");
    await fs.writeFile(videoPath, "fake-video-bytes");
  });

  afterEach(async () => {
    await fs.rm(mediaRoot, { force: true, recursive: true });
  });

  const pathInput = async () => {
    const stat = await fs.stat(videoPath);
    return {
      videoPath,
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
    };
  };

  it("builds a not_analyzed empty record", () => {
    const analysis = createEmptySmartAnalysis(
      {
        videoPath,
        fileName: "sample.mp4",
        fileSizeBytes: 16,
        mtimeMs: 1_700_000_000_000,
      },
      { mediaRoot },
    );

    expect(analysis.status).toBe("not_analyzed");
    expect(analysis.version).toBe(1);
    expect(analysis.samples).toEqual([]);
    expect(analysis.suggestedTags).toEqual([]);
    expect(analysis.confidence).toBe(0);
  });

  it("returns null when the sidecar is missing", async () => {
    const input = await pathInput();
    const result = await readSmartAnalysis(input, { mediaRoot });
    expect(result).toBeNull();
  });

  it("writes and reads an analysis sidecar atomically under the analysis root", async () => {
    const input = await pathInput();
    const empty = createEmptySmartAnalysis(
      {
        videoPath: input.videoPath,
        fileName: "sample.mp4",
        fileSizeBytes: input.fileSizeBytes,
        mtimeMs: input.mtimeMs,
      },
      { mediaRoot },
    );

    const suggested = validateSpiritFlixSmartAnalysis({
      ...empty,
      status: "suggested",
      suggestedDisplayTitle: "Unknown — Indoor Scene",
      suggestedTags: [
        {
          id: "indoor",
          label: "indoor",
          group: "scene",
          confidence: 0.72,
          evidenceTimestamps: [12],
          reviewRequired: false,
        },
      ],
      confidence: 0.72,
    });

    const written = await writeSmartAnalysis(suggested, { mediaRoot });
    expect(written.path.startsWith(getSmartAnalysisRoot({ mediaRoot }))).toBe(true);
    expect(path.dirname(written.path)).not.toBe(path.dirname(videoPath));

    const readBack = await readSmartAnalysis(input, { mediaRoot });
    expect(readBack?.status).toBe("suggested");
    expect(readBack?.suggestedDisplayTitle).toBe("Unknown — Indoor Scene");
    expect(readBack?.suggestedTags).toHaveLength(1);
  });

  it("rejects invalid analysis payloads and pathKey mismatches", async () => {
    const input = await pathInput();
    const empty = createEmptySmartAnalysis(
      {
        videoPath: input.videoPath,
        fileName: "sample.mp4",
        fileSizeBytes: input.fileSizeBytes,
        mtimeMs: input.mtimeMs,
      },
      { mediaRoot },
    );

    await expect(
      writeSmartAnalysis(
        validateSpiritFlixSmartAnalysis({
          ...empty,
          pathKey: "deadbeef",
        }),
        { mediaRoot },
      ),
    ).rejects.toThrow(/pathKey/i);

    expect(() =>
      validateSpiritFlixSmartAnalysis({
        ...empty,
        status: "definitely-not-valid",
      }),
    ).toThrow(/status/i);

    expect(() =>
      validateSpiritFlixSmartAnalysis({
        ...empty,
        suggestedTags: [
          {
            id: "indoor",
            label: "indoor",
            group: "scene",
            confidence: 2,
            evidenceTimestamps: [],
            reviewRequired: false,
          },
        ],
      }),
    ).toThrow(/confidence/i);
  });

  it("rejects prototype pollution keys during validation", () => {
    const polluted = {
      constructor: { polluted: true },
      version: 1,
      videoPath: path.join(mediaRoot, "yes", "nested", "sample.mp4"),
      pathKey: "abc",
      fileName: "sample.mp4",
      fileSizeBytes: 1,
      mtimeMs: 1,
      analyzedAt: new Date().toISOString(),
      analyzerVersion: "test",
      status: "not_analyzed",
      safety: { safeToSuggest: true, reasons: [], requiresHumanReview: false },
      media: {},
      samples: [],
      suggestedTags: [],
      confidence: 0,
    };

    expect(() => validateSpiritFlixSmartAnalysis(polluted)).toThrow(/Unsafe key/i);
  });
});
