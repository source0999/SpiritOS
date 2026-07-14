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
import { GET as getModels } from "../model-index/route";
import { GET as getVideoModel, PUT as putVideoModel } from "../videos/[itemId]/model/route";

describe("SpiritFlix manual model API", () => {
  let rootDir: string;
  let previousRoot: string | undefined;

  beforeEach(async () => {
    previousRoot = process.env.SPIRITFLIX_MANUAL_MODEL_ROOT;
    rootDir = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-manual-model-api-"));
    process.env.SPIRITFLIX_MANUAL_MODEL_ROOT = rootDir;
    approval.consume.mockResolvedValue({ ok: true, value: { generation: 1 } });
    approval.finalize.mockResolvedValue({ ok: true, value: {} });
  });

  afterEach(async () => {
    if (previousRoot === undefined) {
      delete process.env.SPIRITFLIX_MANUAL_MODEL_ROOT;
    } else {
      process.env.SPIRITFLIX_MANUAL_MODEL_ROOT = previousRoot;
    }
    await fs.rm(rootDir, { recursive: true, force: true });
  });

  it("sets, gets, and indexes manual model names", async () => {
    const putResponse = await putVideoModel(
      new NextRequest("http://localhost/api/spiritflix/videos/video-1/model", {
        method: "PUT",
        body: JSON.stringify({
          filePath: "/mnt/spirit-8tb/media/yes/model/video.mkv",
          modelName: "sava schultz",
          knownModelNames: ["Sava Schultz"],
          approval_id: "server-issued-fixture-approval",
        }),
      }),
      { params: Promise.resolve({ itemId: "video-1" }) },
    );
    const putBody = await putResponse.json();

    expect(putResponse.status).toBe(200);
    expect(putBody.record.modelName).toBe("Sava Schultz");
    expect(approval.consume).toHaveBeenCalledWith(
      "server-issued-fixture-approval",
      "metadata.mutation",
      "spiritflix:videos:video-1:model",
      { field: "modelName", value: "sava schultz" },
    );

    const getResponse = await getVideoModel(
      new NextRequest("http://localhost/api/spiritflix/videos/video-1/model"),
      { params: Promise.resolve({ itemId: "video-1" }) },
    );
    await expect(getResponse.json()).resolves.toEqual(expect.objectContaining({ modelName: "Sava Schultz" }));

    const modelsResponse = await getModels(new NextRequest("http://localhost/api/spiritflix/model-index?includeItems=1"));
    const modelsBody = await modelsResponse.json();
    expect(modelsBody.models).toEqual(expect.arrayContaining([expect.objectContaining({ modelName: "Sava Schultz", count: 1 })]));
    expect(modelsBody.items).toEqual(expect.arrayContaining([expect.objectContaining({ itemId: "video-1" })]));
  });

  it("rejects empty model names", async () => {
    const emptyResponse = await putVideoModel(
      new NextRequest("http://localhost/api/spiritflix/videos/video-1/model", {
        method: "PUT",
        body: JSON.stringify({ modelName: " " }),
      }),
      { params: Promise.resolve({ itemId: "video-1" }) },
    );
    expect(emptyResponse.status).toBe(400);
  });
});
