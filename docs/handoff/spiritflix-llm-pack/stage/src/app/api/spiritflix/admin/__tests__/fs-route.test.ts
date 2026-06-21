import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { GET } from "../fs/route";

let tempRoot = "";
let originalRoots: string | undefined;

describe("SpiritFlix admin filesystem API", () => {
  beforeEach(async () => {
    originalRoots = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-admin-fs-"));
    process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = tempRoot;
    await fs.mkdir(path.join(tempRoot, "Movies"));
    await fs.writeFile(path.join(tempRoot, "Movies", "clip.mp4"), "video");
  });

  afterEach(async () => {
    if (originalRoots === undefined) {
      delete process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    } else {
      process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = originalRoots;
    }
    await fs.rm(tempRoot, { force: true, recursive: true });
  });

  it("returns read-only normalized filesystem records", async () => {
    const response = await GET(new Request(`http://localhost/api/spiritflix/admin/fs?path=${encodeURIComponent(tempRoot)}`) as never);
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.schema).toBe("spiritflix-admin-fs/v1");
    expect(body.items[0]).toEqual(expect.objectContaining({ name: "Movies", type: "folder", parentPath: expect.any(String) }));
  });

  it("rejects path traversal", async () => {
    const response = await GET(
      new Request(`http://localhost/api/spiritflix/admin/fs?path=${encodeURIComponent(`${tempRoot}${path.sep}..${path.sep}outside`)}`) as never,
    );
    const body = await response.json();

    expect(response.status).toBe(400);
    expect(body.error).toMatch(/traversal/i);
  });

  it("rejects paths outside the allowed root", async () => {
    const outside = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-admin-outside-"));
    const response = await GET(new Request(`http://localhost/api/spiritflix/admin/fs?path=${encodeURIComponent(outside)}`) as never);
    const body = await response.json();

    expect(response.status).toBe(400);
    expect(body.error).toMatch(/outside/i);
    await fs.rm(outside, { force: true, recursive: true });
  });
});
