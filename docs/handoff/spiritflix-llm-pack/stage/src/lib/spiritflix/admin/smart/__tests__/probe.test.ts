import path from "node:path";
import { EventEmitter } from "node:events";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixSmartProbeError } from "../errors";

const mockSpawn = vi.hoisted(() => vi.fn());

vi.mock("../process", () => ({
  spawn: mockSpawn,
}));

import { parseFfprobeJson, parseRationalFrameRate, probeSpiritFlixVideo } from "../probe";

const SAMPLE_FFPROBE = {
  format: {
    duration: "125.456",
    format_name: "matroska,webm",
    bit_rate: "4500000",
  },
  streams: [
    {
      codec_type: "audio",
      codec_name: "aac",
    },
    {
      codec_type: "video",
      codec_name: "h264",
      width: 1920,
      height: 1080,
      avg_frame_rate: "30000/1001",
      r_frame_rate: "30000/1001",
    },
  ],
};

function mockSpawnEmitter(onReady: (emitter: EventEmitter & { stdout: EventEmitter; stderr: EventEmitter }) => void) {
  mockSpawn.mockImplementation(() => {
    const emitter = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter; kill: () => void };
    emitter.stdout = new EventEmitter();
    emitter.stderr = new EventEmitter();
    emitter.kill = vi.fn();
    queueMicrotask(() => onReady(emitter));
    return emitter;
  });
}

describe("SpiritFlix smart probe", () => {
  beforeEach(() => {
    mockSpawn.mockReset();
  });

  it("parses representative ffprobe JSON", () => {
    const result = parseFfprobeJson(SAMPLE_FFPROBE);
    expect(result.durationSeconds).toBeCloseTo(125.456);
    expect(result.width).toBe(1920);
    expect(result.height).toBe(1080);
    expect(result.codec).toBe("h264");
    expect(result.container).toBe("matroska,webm");
    expect(result.bitRate).toBe(4_500_000);
    expect(result.frameRate).toBeCloseTo(29.97, 1);
  });

  it("parses rational frame rate like 30000/1001", () => {
    expect(parseRationalFrameRate("30000/1001")).toBeCloseTo(29.97, 1);
    expect(parseRationalFrameRate("24/1")).toBe(24);
    expect(parseRationalFrameRate("0/0")).toBeUndefined();
  });

  it("handles missing duration", () => {
    const result = parseFfprobeJson({
      format: { format_name: "mp4" },
      streams: [{ codec_type: "video", codec_name: "hevc", width: 1280, height: 720 }],
    });
    expect(result.durationSeconds).toBeUndefined();
    expect(result.codec).toBe("hevc");
  });

  it("rejects non-video extension", async () => {
    const mediaRoot = "/tmp/spiritflix-probe-media";
    const txtPath = path.join(mediaRoot, "yes", "notes.txt");
    await expect(
      probeSpiritFlixVideo(txtPath, { mediaRoot, ffprobePath: "/usr/bin/ffprobe" }),
    ).rejects.toThrow(/video files/i);
  });

  it("rejects traversal/outside root", async () => {
    const mediaRoot = "/tmp/spiritflix-probe-media";
    await expect(probeSpiritFlixVideo("/etc/passwd", { mediaRoot })).rejects.toThrow(/outside/i);
    await expect(
      probeSpiritFlixVideo(`${mediaRoot}/../outside.mp4`, { mediaRoot }),
    ).rejects.toThrow(/traversal/i);
  });

  it("uses shell false / argument array where testable", async () => {
    const mediaRoot = "/tmp/spiritflix-probe-media";
    const videoPath = path.join(mediaRoot, "yes", "clip.mp4");
    mockSpawnEmitter((emitter) => {
      emitter.stdout.emit("data", Buffer.from(JSON.stringify(SAMPLE_FFPROBE)));
      emitter.emit("close", 0);
    });

    const result = await probeSpiritFlixVideo(videoPath, { mediaRoot, ffprobePath: "/usr/bin/ffprobe" });
    expect(result.codec).toBe("h264");
    expect(mockSpawn).toHaveBeenCalledWith(
      "/usr/bin/ffprobe",
      expect.arrayContaining(["-print_format", "json", "-show_format", "-show_streams", videoPath]),
      { shell: false },
    );
  });

  it("handles timeout", async () => {
    const mediaRoot = "/tmp/spiritflix-probe-media";
    const videoPath = path.join(mediaRoot, "yes", "clip.mp4");
    mockSpawn.mockImplementation(() => {
      const emitter = new EventEmitter() as EventEmitter & { stdout: EventEmitter; stderr: EventEmitter; kill: () => void };
      emitter.stdout = new EventEmitter();
      emitter.stderr = new EventEmitter();
      emitter.kill = vi.fn();
      return emitter;
    });

    await expect(
      probeSpiritFlixVideo(videoPath, { mediaRoot, ffprobePath: "/usr/bin/ffprobe", timeoutMs: 1 }),
    ).rejects.toThrow(/timed out/i);
  });

  it("handles invalid JSON", async () => {
    const mediaRoot = "/tmp/spiritflix-probe-media";
    const videoPath = path.join(mediaRoot, "yes", "clip.mp4");
    mockSpawnEmitter((emitter) => {
      emitter.stdout.emit("data", Buffer.from("not-json"));
      emitter.emit("close", 0);
    });

    await expect(
      probeSpiritFlixVideo(videoPath, { mediaRoot, ffprobePath: "/usr/bin/ffprobe" }),
    ).rejects.toThrow(/invalid JSON/i);
  });

  it("handles missing ffprobe", async () => {
    const mediaRoot = "/tmp/spiritflix-probe-media";
    const videoPath = path.join(mediaRoot, "yes", "clip.mp4");
    mockSpawnEmitter((emitter) => {
      emitter.emit("error", Object.assign(new Error("spawn ENOENT"), { code: "ENOENT" }));
    });

    await expect(
      probeSpiritFlixVideo(videoPath, { mediaRoot, ffprobePath: "/missing/ffprobe" }),
    ).rejects.toThrow(/not available/i);
  });

  it("throws typed probe errors", () => {
    expect(() => parseFfprobeJson(null)).toThrow(SpiritFlixSmartProbeError);
    expect(new SpiritFlixSmartProbeError("x").name).toBe("SpiritFlixSmartProbeError");
  });
});
