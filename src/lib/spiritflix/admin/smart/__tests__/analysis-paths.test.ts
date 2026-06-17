import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  assertSmartAnalysisPathSafe,
  assertSmartVideoPathCandidate,
  createSmartAnalysisPathKey,
  getSmartAnalysisCacheRoot,
  getSmartAnalysisPath,
  getSmartAnalysisRoot,
} from "../analysis-paths";

describe("SpiritFlix smart analysis paths", () => {
  let mediaRoot = "";

  beforeEach(async () => {
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-smart-media-"));
    await fs.mkdir(path.join(mediaRoot, "yes", "nested"), { recursive: true });
  });

  afterEach(async () => {
    await fs.rm(mediaRoot, { force: true, recursive: true });
  });

  const sampleVideo = () => path.join(mediaRoot, "yes", "nested", "clip.mp4");

  const sampleInput = (overrides: Partial<{ videoPath: string; fileSizeBytes: number; mtimeMs: number }> = {}) => ({
    videoPath: overrides.videoPath ?? sampleVideo(),
    fileSizeBytes: overrides.fileSizeBytes ?? 1_024,
    mtimeMs: overrides.mtimeMs ?? 1_700_000_000_000,
  });

  it("creates deterministic keys and sidecar paths under the analysis root", () => {
    const input = sampleInput();
    const keyA = createSmartAnalysisPathKey(input);
    const keyB = createSmartAnalysisPathKey(input);
    expect(keyA).toBe(keyB);

    const sidecarPath = getSmartAnalysisPath(input, { mediaRoot });
    expect(sidecarPath).toBe(path.join(getSmartAnalysisRoot({ mediaRoot }), `${keyA}.json`));
    expect(sidecarPath.startsWith(getSmartAnalysisRoot({ mediaRoot }))).toBe(true);
    expect(sidecarPath.endsWith(".json")).toBe(true);
    expect(path.dirname(sidecarPath)).not.toBe(path.dirname(input.videoPath));
  });

  it("changes the key when size or mtime changes", () => {
    const base = sampleInput();
    const changedSize = createSmartAnalysisPathKey({ ...base, fileSizeBytes: base.fileSizeBytes + 1 });
    const changedMtime = createSmartAnalysisPathKey({ ...base, mtimeMs: base.mtimeMs + 1 });
    expect(changedSize).not.toBe(createSmartAnalysisPathKey(base));
    expect(changedMtime).not.toBe(createSmartAnalysisPathKey(base));
  });

  it("exposes the analysis cache root without writing frames in S1", () => {
    expect(getSmartAnalysisCacheRoot({ mediaRoot })).toBe(
      path.join(mediaRoot, ".spiritflix-admin", "analysis-cache"),
    );
  });

  it("rejects traversal and paths outside the media root", () => {
    expect(() => assertSmartVideoPathCandidate(`${mediaRoot}/../outside.mp4`, { mediaRoot })).toThrow(/traversal/i);
    expect(() => assertSmartVideoPathCandidate("/tmp/outside.mp4", { mediaRoot })).toThrow(/outside/i);
  });

  it("rejects Jellyfin config paths", () => {
    const jellyfinPath = path.join(mediaRoot, "yes", "jellyfin-config", "system.xml");
    expect(() => assertSmartVideoPathCandidate(jellyfinPath, { mediaRoot })).toThrow(/Jellyfin/i);
  });

  it("rejects admin storage paths and paths inside the analysis root", () => {
    const adminPath = path.join(mediaRoot, ".spiritflix-admin", "metadata", "abc.json");
    expect(() => assertSmartVideoPathCandidate(adminPath, { mediaRoot })).toThrow(/admin storage/i);

    const analysisPath = path.join(getSmartAnalysisRoot({ mediaRoot }), "abc.json");
    expect(() => assertSmartVideoPathCandidate(analysisPath, { mediaRoot })).toThrow(/analysis store/i);
  });

  it("keeps sidecar paths inside the analysis root and rejects traversal", () => {
    const safe = path.join(getSmartAnalysisRoot({ mediaRoot }), "abc123.json");
    expect(assertSmartAnalysisPathSafe(safe, { mediaRoot })).toBe(path.resolve(safe));

    const traversal = path.join(getSmartAnalysisRoot({ mediaRoot }), "..", "escape.json");
    expect(() => assertSmartAnalysisPathSafe(traversal, { mediaRoot })).toThrow(/analysis root/i);

    const outside = path.join(mediaRoot, "yes", "nested", "beside-video.json");
    expect(() => assertSmartAnalysisPathSafe(outside, { mediaRoot })).toThrow(/analysis root/i);
  });
});
