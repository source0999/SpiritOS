import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { EventEmitter } from "node:events";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createSmartAnalysisPathKey } from "../analysis-paths";

const mockSpawn = vi.hoisted(() => vi.fn());

vi.mock("../process", () => ({
  spawn: mockSpawn,
}));

import {
  buildSpiritFlixFrameCacheFileName,
  extractSpiritFlixFrameSample,
  getSpiritFlixFrameCachePath,
  planSpiritFlixSampleTimestamps,
} from "../sampler";

describe("SpiritFlix smart sampler", () => {
  let mediaRoot = "";
  let videoPath = "";
  let analysisKey = "";

  beforeEach(async () => {
    mockSpawn.mockReset();
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-sampler-"));
    const videoDir = path.join(mediaRoot, "yes", "nested");
    await fs.mkdir(videoDir, { recursive: true });
    videoPath = path.join(videoDir, "clip.mp4");
    await fs.writeFile(videoPath, "fake-video");
    const stat = await fs.stat(videoPath);
    analysisKey = createSmartAnalysisPathKey({
      videoPath,
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
    });
  });

  afterEach(async () => {
    await fs.rm(mediaRoot, { force: true, recursive: true });
  });

  it("plans timestamps for short, medium, and long videos", () => {
    const short = planSpiritFlixSampleTimestamps(12);
    const medium = planSpiritFlixSampleTimestamps(180);
    const long = planSpiritFlixSampleTimestamps(3_600);

    expect(short.length).toBeLessThanOrEqual(3);
    expect(medium.length).toBeLessThanOrEqual(6);
    expect(long.length).toBeLessThanOrEqual(16);
    expect(short.length).toBeGreaterThan(0);
  });

  it("never produces negative or past-duration timestamps", () => {
    const duration = 42;
    const timestamps = planSpiritFlixSampleTimestamps(duration);
    for (const value of timestamps) {
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThanOrEqual(duration);
    }
  });

  it("de-dupes and stays deterministic", () => {
    const first = planSpiritFlixSampleTimestamps(120);
    const second = planSpiritFlixSampleTimestamps(120);
    expect(first).toEqual(second);
    expect(new Set(first).size).toBe(first.length);
  });

  it("builds deterministic frame cache paths under analysis-cache/frames", () => {
    const framePath = getSpiritFlixFrameCachePath(analysisKey, 12_345, { mediaRoot });
    expect(framePath).toContain(path.join(".spiritflix-admin", "analysis-cache", "frames"));
    expect(path.basename(framePath)).toBe(buildSpiritFlixFrameCacheFileName(analysisKey, 12_345));
    expect(framePath.endsWith("-v1.jpg")).toBe(true);
  });

  it("uses different paths for different timestamps", () => {
    const a = getSpiritFlixFrameCachePath(analysisKey, 1_000, { mediaRoot });
    const b = getSpiritFlixFrameCachePath(analysisKey, 2_000, { mediaRoot });
    expect(a).not.toBe(b);
  });

  it("rejects traversal through invalid analysis keys", () => {
    expect(() => getSpiritFlixFrameCachePath("../evil", 0, { mediaRoot })).toThrow(/sha256/i);
  });

  it("returns cached frame without spawn when cache exists", async () => {
    const framePath = getSpiritFlixFrameCachePath(analysisKey, 5_000, { mediaRoot });
    await fs.mkdir(path.dirname(framePath), { recursive: true });
    await fs.writeFile(framePath, Buffer.from("cached-jpeg"));

    const sample = await extractSpiritFlixFrameSample(videoPath, 5, {
      mediaRoot,
      analysisKey,
    });
    expect(sample.framePath).toBe(framePath);
    expect(mockSpawn).not.toHaveBeenCalled();
  });

  it("extracts via temp file then atomic rename", async () => {
    mockSpawn.mockImplementation((_cmd, args) => {
      const outputPath = args?.[args.length - 1] as string;
      const emitter = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter; kill: () => void };
      emitter.stdout = new EventEmitter();
      emitter.stderr = new EventEmitter();
      emitter.kill = vi.fn();
      queueMicrotask(async () => {
        await fs.writeFile(outputPath, Buffer.from("fresh-jpeg"));
        emitter.emit("close", 0);
      });
      return emitter;
    });

    const sample = await extractSpiritFlixFrameSample(videoPath, 3.5, {
      mediaRoot,
      ffmpegPath: "/usr/bin/ffmpeg",
      analysisKey,
    });
    const stat = await fs.stat(sample.framePath);
    expect(stat.size).toBeGreaterThan(0);
    expect(sample.framePath).not.toBe(path.dirname(videoPath));
    expect(sample.cacheKey).toContain(analysisKey);
  });

  it("handles ffmpeg timeout and cleans temp file", async () => {
    mockSpawn.mockImplementation(() => {
      const emitter = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter; kill: () => void };
      emitter.stdout = new EventEmitter();
      emitter.stderr = new EventEmitter();
      emitter.kill = vi.fn();
      return emitter;
    });

    await expect(
      extractSpiritFlixFrameSample(videoPath, 1, { mediaRoot, ffmpegPath: "/usr/bin/ffmpeg", timeoutMs: 1, analysisKey }),
    ).rejects.toThrow(/timed out/i);

    const framesRoot = path.join(mediaRoot, ".spiritflix-admin", "analysis-cache", "frames");
    const entries = await fs.readdir(framesRoot);
    expect(entries.some((entry) => entry.includes(".tmp.jpg"))).toBe(false);
  });

  it("cleans temp file on ffmpeg failure", async () => {
    mockSpawn.mockImplementation(() => {
      const emitter = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter; kill: () => void };
      emitter.stdout = new EventEmitter();
      emitter.stderr = new EventEmitter();
      emitter.kill = vi.fn();
      queueMicrotask(() => emitter.emit("close", 1));
      return emitter;
    });

    await expect(
      extractSpiritFlixFrameSample(videoPath, 2, { mediaRoot, ffmpegPath: "/usr/bin/ffmpeg", analysisKey }),
    ).rejects.toThrow(/failed/i);
  });

  it("rejects non-video and outside-root paths", async () => {
    const txtPath = path.join(mediaRoot, "yes", "notes.txt");
    await fs.writeFile(txtPath, "nope");
    await expect(extractSpiritFlixFrameSample(txtPath, 1, { mediaRoot })).rejects.toThrow(/video files/i);
    await expect(extractSpiritFlixFrameSample("/tmp/outside.mp4", 1, { mediaRoot })).rejects.toThrow(/outside/i);
  });

  it("does not write beside the video file", async () => {
    mockSpawn.mockImplementation((_cmd, args) => {
      const outputPath = args?.[args.length - 1] as string;
      const emitter = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter; kill: () => void };
      emitter.stdout = new EventEmitter();
      emitter.stderr = new EventEmitter();
      emitter.kill = vi.fn();
      queueMicrotask(async () => {
        await fs.writeFile(outputPath, Buffer.from("jpeg"));
        emitter.emit("close", 0);
      });
      return emitter;
    });

    const sample = await extractSpiritFlixFrameSample(videoPath, 4, { mediaRoot, analysisKey });
    expect(path.dirname(sample.framePath)).not.toBe(path.dirname(videoPath));
  });
});
