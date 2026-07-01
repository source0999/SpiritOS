import fs from "node:fs/promises";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

let tempRoot = "";

async function loadManifestRoute() {
  vi.resetModules();
  process.env.SPIRITFLIX_CAPTION_ROOT = tempRoot;
  return import("../manifest/route");
}

async function loadFileRoute() {
  vi.resetModules();
  process.env.SPIRITFLIX_CAPTION_ROOT = tempRoot;
  return import("../file/route");
}

describe("SpiritFlix caption routes", () => {
  beforeEach(async () => {
    tempRoot = await fs.mkdtemp(path.join(process.cwd(), ".tmp-spiritflix-captions-"));
  });

  afterEach(async () => {
    delete process.env.SPIRITFLIX_CAPTION_ROOT;
    await fs.rm(tempRoot, { recursive: true, force: true });
  });

  it("returns a stable empty manifest when no caption manifest exists", async () => {
    const { GET } = await loadManifestRoute();
    const response = await GET(
      new Request("http://localhost/api/spiritflix/captions/manifest?sourcePath=/mnt/spirit-8tb/media/anime/Missing.mp4") as never,
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      mediaPath: "/mnt/spirit-8tb/media/anime/Missing.mp4",
      tracks: [],
    });
  });

  it("returns cached VTT tracks with safe public URLs", async () => {
    const key = "0123456789abcdef01234567";
    await fs.mkdir(path.join(tempRoot, "manifests"), { recursive: true });
    await fs.writeFile(
      path.join(tempRoot, "manifests", `${key}.json`),
      JSON.stringify({
        mediaPath: "/mnt/spirit-8tb/media/anime/Test.mp4",
        mediaKey: key,
        generatedAt: "2026-06-27T00:00:00.000Z",
        tracks: [
          {
            id: "caption-one",
            sourceType: "embedded",
            sourceFormat: "mov_text",
            outputFormat: "vtt",
            language: "eng",
            label: "English",
            kind: "subtitles",
            default: true,
            cachePath: path.join(tempRoot, "cache", key, "caption-one.vtt"),
            reviewStatus: "source",
          },
        ],
      }),
    );

    const { GET } = await loadManifestRoute();
    const response = await GET(new Request(`http://localhost/api/spiritflix/captions/manifest?key=${key}`) as never);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      mediaKey: key,
      tracks: [
        {
          id: "caption-one",
          publicUrl: `/api/spiritflix/captions/file?key=${key}&track=caption-one`,
        },
      ],
    });
  });

  it("serves cached VTT files with the correct content type", async () => {
    const key = "0123456789abcdef01234567";
    const captionPath = path.join(tempRoot, "cache", key, "caption-one.vtt");
    await fs.mkdir(path.dirname(captionPath), { recursive: true });
    await fs.writeFile(captionPath, "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello\n");

    const { GET } = await loadFileRoute();
    const response = await GET(new Request(`http://localhost/api/spiritflix/captions/file?key=${key}&track=caption-one`) as never);

    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("text/vtt; charset=utf-8");
    expect(await response.text()).toContain("WEBVTT");
  });

  it("rejects traversal and unknown caption files", async () => {
    const { GET } = await loadFileRoute();
    const traversal = await GET(
      new Request("http://localhost/api/spiritflix/captions/file?key=0123456789abcdef01234567&track=..%2Fsecret") as never,
    );
    const unknown = await GET(
      new Request("http://localhost/api/spiritflix/captions/file?key=0123456789abcdef01234567&track=missing") as never,
    );

    expect(traversal.status).toBe(404);
    expect(unknown.status).toBe(404);
  });
});
