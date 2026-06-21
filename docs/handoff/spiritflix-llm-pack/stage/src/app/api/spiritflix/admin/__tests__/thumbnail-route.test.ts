import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "../thumbnail/route";

vi.mock("@/lib/spiritflix/admin/thumbnail", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/spiritflix/admin/thumbnail")>();
  return {
    ...actual,
    getOrGenerateAdminVideoThumbnail: vi.fn(actual.getOrGenerateAdminVideoThumbnail),
  };
});

import { getOrGenerateAdminVideoThumbnail } from "@/lib/spiritflix/admin/thumbnail";

let tempRoot = "";
let originalRoots: string | undefined;

function thumbnailRequest(targetPath: string) {
  return new Request(`http://localhost/api/spiritflix/admin/thumbnail?path=${encodeURIComponent(targetPath)}`) as never;
}

describe("SpiritFlix admin thumbnail API", () => {
  beforeEach(async () => {
    originalRoots = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-admin-thumb-"));
    process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = tempRoot;
    vi.mocked(getOrGenerateAdminVideoThumbnail).mockReset();
  });

  afterEach(async () => {
    if (originalRoots === undefined) {
      delete process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    } else {
      process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = originalRoots;
    }
    await fs.rm(tempRoot, { force: true, recursive: true });
  });

  it("rejects path traversal", async () => {
    const response = await GET(thumbnailRequest(`${tempRoot}${path.sep}..${path.sep}outside/video.mp4`));
    const body = await response.json();
    expect(response.status).toBe(400);
    expect(body.error).toMatch(/traversal/i);
  });

  it("rejects paths outside the allowed root", async () => {
    const outside = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-admin-outside-"));
    const response = await GET(thumbnailRequest(`${outside}/clip.mp4`));
    const body = await response.json();
    expect(response.status).toBe(400);
    expect(body.error).toMatch(/outside/i);
    await fs.rm(outside, { force: true, recursive: true });
  });

  it("rejects non-video files", async () => {
    const textPath = path.join(tempRoot, "notes.txt");
    await fs.writeFile(textPath, "hello");
    const response = await GET(thumbnailRequest(textPath));
    const body = await response.json();
    expect(response.status).toBe(404);
    expect(body.error).toMatch(/unavailable/i);
  });

  it("returns cached image when cache exists", async () => {
    const cacheFile = path.join(tempRoot, "cached.jpg");
    await fs.writeFile(cacheFile, Buffer.from([0xff, 0xd8, 0xff, 0xd9]));
    vi.mocked(getOrGenerateAdminVideoThumbnail).mockResolvedValue({
      cachePath: cacheFile,
      cacheKey: "cached",
    });

    const response = await GET(thumbnailRequest(path.join(tempRoot, "clip.mp4")));
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("image/jpeg");
    const bytes = Buffer.from(await response.arrayBuffer());
    expect(bytes.length).toBeGreaterThan(0);
  });

  it("attempts generation only for valid video paths", async () => {
    const videoPath = path.join(tempRoot, "generate.mp4");
    await fs.writeFile(videoPath, "fake-video");
    const cacheFile = path.join(tempRoot, "generated.jpg");
    await fs.writeFile(cacheFile, Buffer.from([0xff, 0xd8, 0xff, 0xd9]));
    vi.mocked(getOrGenerateAdminVideoThumbnail).mockResolvedValue({
      cachePath: cacheFile,
      cacheKey: "abc",
    });

    const response = await GET(thumbnailRequest(videoPath));
    expect(getOrGenerateAdminVideoThumbnail).toHaveBeenCalledWith(videoPath);
    expect(response.status).toBe(200);
  });
});
