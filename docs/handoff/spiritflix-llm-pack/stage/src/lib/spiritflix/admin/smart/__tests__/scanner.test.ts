import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { EventEmitter } from "node:events";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getSmartAnalysisRoot } from "../analysis-paths";
import { readSmartAnalysis } from "../analysis-store";

const mockSpawn = vi.hoisted(() => vi.fn());

vi.mock("../process", () => ({
  spawn: mockSpawn,
}));

import { scanOneSpiritFlixVideoEvidence, SPIRITFLIX_SMART_ANALYZER_VERSION_S2 } from "../scanner";

const SAMPLE_FFPROBE = {
  format: { duration: "90.0", format_name: "mp4", bit_rate: "2000000" },
  streams: [{ codec_type: "video", codec_name: "h264", width: 1280, height: 720, avg_frame_rate: "24/1" }],
};

describe("SpiritFlix smart scanner", () => {
  let mediaRoot = "";
  let videoPath = "";

  beforeEach(async () => {
    mockSpawn.mockReset();
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-scanner-"));
    const videoDir = path.join(mediaRoot, "yes", "nested");
    await fs.mkdir(videoDir, { recursive: true });
    videoPath = path.join(videoDir, "sample.mp4");
    await fs.writeFile(videoPath, "fake-video-bytes");
  });

  afterEach(async () => {
    await fs.rm(mediaRoot, { force: true, recursive: true });
  });

  function mockProbeAndFrames(frameSuccess = true) {
    mockSpawn.mockImplementation((_cmd, args) => {
      const emitter = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter; kill: () => void };
      emitter.stdout = new EventEmitter();
      emitter.stderr = new EventEmitter();
      emitter.kill = vi.fn();

      const isFfprobe = Array.isArray(args) && args.includes("-show_streams");
      queueMicrotask(async () => {
        if (isFfprobe) {
          emitter.stdout.emit("data", Buffer.from(JSON.stringify(SAMPLE_FFPROBE)));
          emitter.emit("close", 0);
          return;
        }
        const outputPath = args?.[args.length - 1] as string;
        if (frameSuccess) {
          await fs.writeFile(outputPath, Buffer.from("jpeg"));
          emitter.emit("close", 0);
        } else {
          emitter.emit("close", 1);
        }
      });
      return emitter;
    });
  }

  it("updates media metadata and writes sidecar under temp media root", async () => {
    mockProbeAndFrames();
    const analysis = await scanOneSpiritFlixVideoEvidence(videoPath, {
      mediaRoot,
      ffprobePath: "/usr/bin/ffprobe",
      ffmpegPath: "/usr/bin/ffmpeg",
      maxSamples: 3,
    });

    expect(analysis.media.durationSeconds).toBe(90);
    expect(analysis.media.codec).toBe("h264");
    expect(analysis.analyzerVersion).toBe(SPIRITFLIX_SMART_ANALYZER_VERSION_S2);

    const stat = await fs.stat(videoPath);
    const stored = await readSmartAnalysis(
      { videoPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs },
      { mediaRoot },
    );
    expect(stored?.pathKey).toBe(analysis.pathKey);
    const sidecarPath = path.join(getSmartAnalysisRoot({ mediaRoot }), `${analysis.pathKey}.json`);
    await expect(fs.stat(sidecarPath)).resolves.toBeDefined();
  });

  it("creates bounded samples with empty tags and needs_review status", async () => {
    mockProbeAndFrames();
    const analysis = await scanOneSpiritFlixVideoEvidence(videoPath, {
      mediaRoot,
      ffprobePath: "/usr/bin/ffprobe",
      ffmpegPath: "/usr/bin/ffmpeg",
      maxSamples: 4,
    });

    expect(analysis.status).toBe("needs_review");
    expect(analysis.samples.length).toBeGreaterThan(0);
    expect(analysis.samples.length).toBeLessThanOrEqual(4);
    for (const sample of analysis.samples) {
      expect(sample.observations).toContain("sampled frame");
      expect(sample.tags).toEqual([]);
      expect(sample.confidence).toBe(0);
      expect(sample.cacheKey).toBeTruthy();
    }
  });

  it("leaves suggested tags/filename/category empty", async () => {
    mockProbeAndFrames();
    const analysis = await scanOneSpiritFlixVideoEvidence(videoPath, {
      mediaRoot,
      ffprobePath: "/usr/bin/ffprobe",
      ffmpegPath: "/usr/bin/ffmpeg",
      maxSamples: 2,
    });

    expect(analysis.suggestedTags).toEqual([]);
    expect(analysis.suggestedFilename).toBeUndefined();
    expect(analysis.suggestedCategory).toBeUndefined();
    expect(analysis.confidence).toBe(0);
    expect(analysis.safety.requiresHumanReview).toBe(true);
  });

  it("does not import Level 2 action executors", async () => {
    const scannerSource = await fs.readFile(path.join(process.cwd(), "src/lib/spiritflix/admin/smart/scanner.ts"), "utf8");
    expect(scannerSource).not.toMatch(/level-?2|executeSpiritFlix|previewAction|confirmAction/i);
  });

  it("handles partial sample failure while keeping metadata sidecar", async () => {
    let ffmpegCalls = 0;
    mockSpawn.mockImplementation((_cmd, args) => {
      const emitter = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter; kill: () => void };
      emitter.stdout = new EventEmitter();
      emitter.stderr = new EventEmitter();
      emitter.kill = vi.fn();
      const isFfprobe = Array.isArray(args) && args.includes("-show_streams");
      queueMicrotask(async () => {
        if (isFfprobe) {
          emitter.stdout.emit("data", Buffer.from(JSON.stringify(SAMPLE_FFPROBE)));
          emitter.emit("close", 0);
          return;
        }
        ffmpegCalls += 1;
        const outputPath = args?.[args.length - 1] as string;
        if (ffmpegCalls % 2 === 0) {
          await fs.writeFile(outputPath, Buffer.from("jpeg"));
          emitter.emit("close", 0);
        } else {
          emitter.emit("close", 1);
        }
      });
      return emitter;
    });

    const analysis = await scanOneSpiritFlixVideoEvidence(videoPath, {
      mediaRoot,
      ffprobePath: "/usr/bin/ffprobe",
      ffmpegPath: "/usr/bin/ffmpeg",
      maxSamples: 4,
    });

    expect(analysis.media.codec).toBe("h264");
    expect(analysis.status).toBe("needs_review");
    expect(analysis.samples.length).toBeGreaterThan(0);
    expect(analysis.samples.length).toBeLessThan(4);
    expect(analysis.notes).toMatch(/frame failures/i);
  });
});
