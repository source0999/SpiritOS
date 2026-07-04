import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { planSpiritFlixConversionOutput, runSpiritFlixConversionBridge } from "../conversion-bridge";

describe("SpiritFlix worker conversion bridge", () => {
  let mediaRoot = "";
  let videoPath = "";

  beforeEach(async () => {
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-conversion-"));
    await fs.mkdir(path.join(mediaRoot, "yes"), { recursive: true });
    videoPath = path.join(mediaRoot, "yes", "clip.mkv");
    await fs.writeFile(videoPath, "fake-video");
  });

  afterEach(async () => {
    await fs.rm(mediaRoot, { recursive: true, force: true });
  });

  it("plans deterministic output under the worker conversion root", () => {
    expect(planSpiritFlixConversionOutput({ mediaRoot, jobId: "sf-job-abc" })).toBe(
      path.join(mediaRoot, ".spiritflix-admin", "conversions", "sf-job-abc-mobile.mp4"),
    );
  });

  it("defaults conversion output to the SpiritFlix media admin root", () => {
    expect(planSpiritFlixConversionOutput({ jobId: "sf-job-default" })).toBe(
      "/mnt/spirit-8tb/media/.spiritflix-admin/conversions/sf-job-default-mobile.mp4",
    );
  });

  it("queues conversion with a receipt while preserving the original source", async () => {
    const stat = await fs.stat(videoPath);
    const receipt = await runSpiritFlixConversionBridge({
      mediaRoot,
      jobId: "sf-job-abc",
      videoPath,
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
      mode: "enqueue",
    });

    expect(receipt).toEqual(expect.objectContaining({
      schema: "spiritflix-conversion-receipt/v1",
      jobId: "sf-job-abc",
      status: "queued",
      mode: "enqueue",
      sourcePath: videoPath,
      originalPreserved: true,
    }));
    expect(receipt.outputPath).toBe(path.join(mediaRoot, ".spiritflix-admin", "conversions", "sf-job-abc-mobile.mp4"));
    expect(receipt.rollback).toEqual({ deleteOutputPath: receipt.outputPath, sourceUntouched: true });
    expect(await fs.readFile(videoPath, "utf8")).toBe("fake-video");
  });

  it("records conversion command failures without deleting the original source", async () => {
    const stat = await fs.stat(videoPath);
    const receipt = await runSpiritFlixConversionBridge({
      mediaRoot,
      jobId: "sf-job-fail",
      videoPath,
      fileSizeBytes: stat.size,
      mtimeMs: stat.mtimeMs,
      mode: "execute",
      command: "missing-ffmpeg-for-test",
      timeoutMs: 1_000,
    });

    expect(receipt.status).toBe("failed");
    expect(receipt.errorReason).toMatch(/missing-ffmpeg-for-test|spawn/i);
    expect(await fs.readFile(videoPath, "utf8")).toBe("fake-video");
  });
});
