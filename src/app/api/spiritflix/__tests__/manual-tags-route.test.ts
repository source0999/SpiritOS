import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const approval = vi.hoisted(() => ({ consume: vi.fn(), finalize: vi.fn() }));
vi.mock("@/lib/coding/spiritflix-admin-approval-authority", () => ({
  consumeSpiritFlixAdminApproval: approval.consume,
  finalizeSpiritFlixAdminApproval: approval.finalize,
}));
import { GET as getLibraryByTag } from "../library/route";
import { GET as getTags } from "../tags/route";
import { PUT as putVideoModel } from "../videos/[itemId]/model/route";
import { GET as getVideoTags, PUT as putVideoTags } from "../videos/[itemId]/tags/route";

describe("SpiritFlix manual tag API", () => {
  let rootDir: string;
  let modelRootDir: string;
  let previousRoot: string | undefined;
  let previousModelRoot: string | undefined;

  beforeEach(async () => {
    previousRoot = process.env.SPIRITFLIX_MANUAL_TAG_ROOT;
    previousModelRoot = process.env.SPIRITFLIX_MANUAL_MODEL_ROOT;
    rootDir = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-manual-tag-api-"));
    modelRootDir = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-manual-model-api-"));
    process.env.SPIRITFLIX_MANUAL_TAG_ROOT = rootDir;
    process.env.SPIRITFLIX_MANUAL_MODEL_ROOT = modelRootDir;
    approval.consume.mockResolvedValue({ ok: true, value: { generation: 1 } });
    approval.finalize.mockResolvedValue({ ok: true, value: {} });
  });

  afterEach(async () => {
    if (previousRoot === undefined) {
      delete process.env.SPIRITFLIX_MANUAL_TAG_ROOT;
    } else {
      process.env.SPIRITFLIX_MANUAL_TAG_ROOT = previousRoot;
    }
    if (previousModelRoot === undefined) {
      delete process.env.SPIRITFLIX_MANUAL_MODEL_ROOT;
    } else {
      process.env.SPIRITFLIX_MANUAL_MODEL_ROOT = previousModelRoot;
    }
    await fs.rm(rootDir, { recursive: true, force: true });
    await fs.rm(modelRootDir, { recursive: true, force: true });
  });

  it("sets, gets, indexes, and filters manual tags", async () => {
    const putResponse = await putVideoTags(
      new NextRequest("http://localhost/api/spiritflix/videos/video-1/tags", {
        method: "PUT",
        body: JSON.stringify({
          filePath: "/mnt/spirit-8tb/media/yes/model/video.mkv",
          manualTags: ["Solo"],
          approval_id: "server-issued-fixture-approval",
        }),
      }),
      { params: Promise.resolve({ itemId: "video-1" }) },
    );
    const putBody = await putResponse.json();

    expect(putResponse.status).toBe(200);
    expect(putBody.record.manualTags).toEqual(["solo"]);
    expect(approval.consume).toHaveBeenCalledWith(
      "server-issued-fixture-approval",
      "metadata.mutation",
      "spiritflix:videos:video-1:tags",
      { field: "manualTags", count: 1 },
    );

    const getResponse = await getVideoTags(
      new NextRequest("http://localhost/api/spiritflix/videos/video-1/tags"),
      { params: Promise.resolve({ itemId: "video-1" }) },
    );
    await expect(getResponse.json()).resolves.toEqual(expect.objectContaining({ manualTags: ["solo"] }));

    const tagsResponse = await getTags(new NextRequest("http://localhost/api/spiritflix/tags?includeItems=1"));
    const tagsBody = await tagsResponse.json();
    expect(tagsBody.tags).toEqual(expect.arrayContaining([expect.objectContaining({ tag: "solo", count: 1 })]));
    expect(tagsBody.items).toEqual(expect.arrayContaining([expect.objectContaining({ itemId: "video-1" })]));

    const libraryResponse = await getLibraryByTag(new NextRequest("http://localhost/api/spiritflix/library?tag=solo"));
    await expect(libraryResponse.json()).resolves.toEqual(expect.objectContaining({ itemIds: ["video-1"] }));
  });

  it("returns model-scoped tags for canonical model name variants", async () => {
    await putVideoModel(
      new NextRequest("http://localhost/api/spiritflix/videos/video-2/model", {
        method: "PUT",
        body: JSON.stringify({ modelName: "Luna x pearl", approval_id: "server-issued-fixture-approval" }),
      }),
      { params: Promise.resolve({ itemId: "video-2" }) },
    );
    await putVideoTags(
      new NextRequest("http://localhost/api/spiritflix/videos/video-2/tags", {
        method: "PUT",
        body: JSON.stringify({
          manualTags: ["BBW", "curvy", "handjob"],
          approval_id: "server-issued-fixture-approval",
        }),
      }),
      { params: Promise.resolve({ itemId: "video-2" }) },
    );

    const response = await getTags(new NextRequest("http://localhost/api/spiritflix/tags?modelName=Luna-X%20PEARL"));
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.modelTags).toEqual(["bbw", "curvy"]);
    expect(body.itemIds).toEqual(["video-2"]);
  });

  it("does not propagate descriptor tags to related videos", async () => {
    const putResponse = await putVideoTags(
      new NextRequest("http://localhost/api/spiritflix/videos/video-1/tags", {
        method: "PUT",
        body: JSON.stringify({
          manualTags: ["big ass", "handjob"],
          propagateToModelItems: [{ itemId: "video-2" }, { itemId: "video-3" }],
          approval_id: "server-issued-fixture-approval",
        }),
      }),
      { params: Promise.resolve({ itemId: "video-1" }) },
    );
    const putBody = await putResponse.json();

    expect(putResponse.status).toBe(200);
    expect(putBody.propagated).toEqual({ tags: [], itemIds: [] });

    const relatedResponse = await getVideoTags(
      new NextRequest("http://localhost/api/spiritflix/videos/video-2/tags"),
      { params: Promise.resolve({ itemId: "video-2" }) },
    );
    await expect(relatedResponse.json()).resolves.toEqual(expect.objectContaining({ manualTags: [] }));
  });

  it("rejects empty and duplicate manual tags", async () => {
    const emptyResponse = await putVideoTags(
      new NextRequest("http://localhost/api/spiritflix/videos/video-1/tags", {
        method: "PUT",
        body: JSON.stringify({ manualTags: [" "] }),
      }),
      { params: Promise.resolve({ itemId: "video-1" }) },
    );
    expect(emptyResponse.status).toBe(400);

    const duplicateResponse = await putVideoTags(
      new NextRequest("http://localhost/api/spiritflix/videos/video-1/tags", {
        method: "PUT",
        body: JSON.stringify({ manualTags: ["busty", " Busty "] }),
      }),
      { params: Promise.resolve({ itemId: "video-1" }) },
    );
    expect(duplicateResponse.status).toBe(400);
  });
});
