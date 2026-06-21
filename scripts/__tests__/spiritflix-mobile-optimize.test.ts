import { describe, expect, it } from "vitest";
import {
  buildFfmpegArgs,
  buildOutputPaths,
  PROFILES,
  selectProfile,
} from "../spiritflix-mobile-optimize.mjs";

describe("spiritflix-mobile-optimize profile planning", () => {
  it("selects faststart remux for mobile-safe MP4s with late moov atoms", () => {
    expect(
      selectProfile({
        sourceProbe: { videoCodec: "h264", audioCodec: "aac", width: 1280, height: 720 },
        faststartStatus: "moov-after-mdat",
      }),
    ).toBe("remux-faststart-only");
  });

  it("keeps already mobile-safe H.264/AAC Twitter MP4s on the remux path", () => {
    expect(
      selectProfile({
        sourceProbe: { videoCodec: "h264", audioCodec: "aac", width: 960, height: 720 },
        faststartStatus: "moov-before-mdat",
      }),
    ).toBe("remux-faststart-only");
  });

  it("selects audio-only when video is already H.264 but audio is not AAC", () => {
    expect(
      selectProfile({
        sourceProbe: { videoCodec: "h264", audioCodec: "opus", width: 1280, height: 720 },
        faststartStatus: "moov-before-mdat",
      }),
    ).toBe("audio-aac-only");
  });

  it("selects full mobile transcode for non-H.264 video", () => {
    expect(
      selectProfile({
        sourceProbe: { videoCodec: "hevc", audioCodec: "aac", width: 1920, height: 1080 },
        faststartStatus: "moov-before-mdat",
      }),
    ).toBe("mobile-720p");
  });

  it("builds contained MP4 output and JSON receipt paths", () => {
    const paths = buildOutputPaths({
      outputRoot: "/tmp/mobile-optimized",
      sourcePath: "/mnt/spirit-8tb/media/yes/example.mp4",
      itemId: "item-123",
      createdAt: "2026-06-20T20:00:00.000Z",
    });
    expect(paths.outputPath).toBe("/tmp/mobile-optimized/20260620/item-123.mp4");
    expect(paths.receiptPath).toBe("/tmp/mobile-optimized/20260620/item-123.json");
    expect(paths.outputPath).not.toContain(".m3u8");
    expect(paths.outputPath).not.toContain(".ts");
  });

  it("constructs remux, audio-only, and Mac transcode commands without HLS output", () => {
    const remux = buildFfmpegArgs({
      ffmpegPath: "/usr/local/bin/ffmpeg",
      profileName: "remux-faststart-only",
      encoderName: "h264_videotoolbox",
      sourcePath: "/tmp/in.mp4",
      outputPath: "/tmp/out.mp4",
    });
    expect(remux).toContain("-c");
    expect(remux).toContain("copy");

    const audio = buildFfmpegArgs({
      ffmpegPath: "/usr/local/bin/ffmpeg",
      profileName: "audio-aac-only",
      encoderName: "h264_videotoolbox",
      sourcePath: "/tmp/in.mp4",
      outputPath: "/tmp/out.mp4",
    });
    expect(audio).toContain("-c:v");
    expect(audio).toContain("copy");
    expect(audio).toContain("-c:a");
    expect(audio).toContain("aac");

    const transcode = buildFfmpegArgs({
      ffmpegPath: "/usr/local/bin/ffmpeg",
      profileName: "mobile-720p",
      encoderName: "h264_videotoolbox",
      sourcePath: "/tmp/in.mp4",
      outputPath: "/tmp/out.mp4",
    });
    expect(transcode).toContain("h264_videotoolbox");
    expect(transcode).toContain("-movflags");
    expect(transcode).toContain("+faststart");
    expect(transcode.join(" ")).not.toMatch(/\.m3u8|\.ts\b/);
  });

  it("exposes the four Phase 7 profiles", () => {
    expect(Object.keys(PROFILES).sort()).toEqual([
      "audio-aac-only",
      "mobile-1080p",
      "mobile-720p",
      "remux-faststart-only",
    ]);
  });
});
