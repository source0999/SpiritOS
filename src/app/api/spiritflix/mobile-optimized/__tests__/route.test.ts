import fs from "node:fs/promises";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

let tempRoot = "";

async function loadRoute() {
  vi.resetModules();
  process.env.SPIRITFLIX_MOBILE_OPTIMIZED_ROOT = tempRoot;
  return import("../route");
}

describe("SpiritFlix mobile optimized route", () => {
  beforeEach(async () => {
    tempRoot = await fs.mkdtemp(path.join(process.cwd(), ".tmp-spiritflix-mobile-"));
  });

  afterEach(async () => {
    delete process.env.SPIRITFLIX_MOBILE_OPTIMIZED_ROOT;
    await fs.rm(tempRoot, { recursive: true, force: true });
  });

  it("returns verified receipt metadata and serves byte ranges", async () => {
    const outputPath = path.join(tempRoot, "20260620", "item-1.mp4");
    const receiptPath = path.join(tempRoot, "20260620", "item-1.json");
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, "0123456789");
    await fs.writeFile(
      receiptPath,
      JSON.stringify({
        schema: "spiritflix-mobile-optimized/v1",
        itemId: "item-1",
        sourcePathSha256: "abc",
        outputPath,
        outputKey: "item-1",
        encoder: "mac-videotoolbox-h264-mobile",
        status: "ok",
        ffprobe: { videoCodec: "h264", audioCodec: "aac" },
      }),
    );

    const { GET } = await loadRoute();
    const metadata = await GET(new Request("http://localhost/api/spiritflix/mobile-optimized?itemId=item-1") as never);
    expect(metadata.status).toBe(200);
    await expect(metadata.json()).resolves.toMatchObject({
      available: true,
      mode: "mobile optimized",
      url: "/api/spiritflix/mobile-optimized?stream=1&key=item-1",
    });

    const range = await GET(
      new Request("http://localhost/api/spiritflix/mobile-optimized?stream=1&key=item-1", {
        headers: { Range: "bytes=2-5" },
      }) as never,
    );
    expect(range.status).toBe(206);
    expect(range.headers.get("Content-Range")).toBe("bytes 2-5/10");
    expect(await range.text()).toBe("2345");
  });

  it("rejects receipts whose output escapes the contained root", async () => {
    const receiptPath = path.join(tempRoot, "escape.json");
    await fs.writeFile(
      receiptPath,
      JSON.stringify({
        itemId: "item-2",
        outputPath: path.join(tempRoot, "..", "outside.mp4"),
        outputKey: "item-2",
        encoder: "mac-videotoolbox-h264-mobile",
        status: "ok",
      }),
    );

    const { GET } = await loadRoute();
    const response = await GET(new Request("http://localhost/api/spiritflix/mobile-optimized?itemId=item-2") as never);
    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ available: false });
  });

  it("reads Phase 7 v2 Mac optimizer receipts", async () => {
    const outputPath = path.join(tempRoot, "20260620", "phase7-item.mp4");
    const receiptPath = path.join(tempRoot, "20260620", "phase7-item.json");
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, "phase7-mp4");
    await fs.writeFile(
      receiptPath,
      JSON.stringify({
        schema: "spiritflix-mobile-optimized/v2",
        itemId: "phase7-item",
        sourcePath: "/mnt/spirit-8tb/media/yes/source.mp4",
        sourcePathSha256: "source-sha",
        sourceStableIdentity: { sizeBytes: 123, durationSeconds: 12.3 },
        outputPath,
        outputKey: "phase7-item",
        encoder: "h264_videotoolbox",
        profile: "mobile-720p",
        profileKind: "transcode",
        workerHost: "spirit-mac-mini",
        workerProof: {
          host: "spirit-mac-mini",
          ffmpegPath: "/usr/local/bin/ffmpeg",
          dellRole: "orchestration, ffprobe verification, scp only; no heavy ffmpeg encode",
        },
        status: "ok",
        outputFfprobe: { videoCodec: "h264", audioCodec: "aac", width: 720, height: 1280 },
        ffprobe: { videoCodec: "h264", audioCodec: "aac", width: 720, height: 1280 },
      }),
    );

    const { GET } = await loadRoute();
    const metadata = await GET(new Request("http://localhost/api/spiritflix/mobile-optimized?itemId=phase7-item") as never);
    expect(metadata.status).toBe(200);
    await expect(metadata.json()).resolves.toMatchObject({
      available: true,
      key: "phase7-item",
      receipt: {
        workerHost: "spirit-mac-mini",
        profile: "mobile-720p",
      },
    });
  });

  it("matches Phase 7 receipts across Jellyfin /media/yes and Dell /mnt aliases", async () => {
    const outputPath = path.join(tempRoot, "20260620", "alias-item.mp4");
    const receiptPath = path.join(tempRoot, "20260620", "alias-item.json");
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, "alias-mp4");
    await fs.writeFile(
      receiptPath,
      JSON.stringify({
        schema: "spiritflix-mobile-optimized/v2",
        sourcePath: "/mnt/spirit-8tb/media/yes/Alias Clip.mp4",
        sourcePathSha256: "feae58a96cc97cfbd8663340e837b3e58a1a4f8c6ca5601472bc4f3ab734c4d8",
        outputPath,
        outputKey: "alias-item",
        encoder: "h264_videotoolbox",
        profile: "mobile-720p",
        workerHost: "spirit-mac-mini",
        status: "ok",
      }),
    );

    const { GET } = await loadRoute();
    const response = await GET(
      new Request("http://localhost/api/spiritflix/mobile-optimized?sourcePath=/media/yes/Alias%20Clip.mp4") as never,
    );
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      available: true,
      key: "alias-item",
    });
  });
});
