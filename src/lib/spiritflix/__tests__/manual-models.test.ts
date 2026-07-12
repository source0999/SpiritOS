import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createHash } from "node:crypto";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  canonicalizeSpiritFlixManualModelName,
  getSpiritFlixManualModelForItem,
  getSpiritFlixManualModelIndex,
  setSpiritFlixManualModelForItem,
} from "../manual-models";

describe("SpiritFlix manual models", () => {
  let rootDir: string;

  beforeEach(async () => {
    rootDir = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-manual-models-"));
  });

  afterEach(async () => {
    await fs.rm(rootDir, { recursive: true, force: true });
  });

  it("canonicalizes model names without lowercasing display text", () => {
    expect(canonicalizeSpiritFlixManualModelName("  Sava   Schultz  ")).toBe("Sava Schultz");
  });

  it("saves model assignments and reuses an existing model casing", async () => {
    await setSpiritFlixManualModelForItem(
      {
        itemId: "video-1",
        filePath: "/mnt/spirit-8tb/media/yes/sava/video.mkv",
        modelName: "Sava Schultz",
      },
      { rootDir },
    );

    const second = await setSpiritFlixManualModelForItem(
      {
        itemId: "video-2",
        modelName: " sava   schultz ",
        knownModelNames: ["Sava Schultz"],
      },
      { rootDir },
    );

    expect(second.record.modelName).toBe("Sava Schultz");
    await expect(getSpiritFlixManualModelForItem("video-1", { rootDir })).resolves.toEqual(
      expect.objectContaining({
        itemId: "video-1",
        filePath: "/mnt/spirit-8tb/media/yes/sava/video.mkv",
        modelName: "Sava Schultz",
      }),
    );

    await expect(getSpiritFlixManualModelIndex({ rootDir })).resolves.toEqual(
      expect.objectContaining({
        models: [expect.objectContaining({ modelName: "Sava Schultz", count: 2 })],
      }),
    );
  });

  it("recovers a saved model assignment by file path when Jellyfin item id changes", async () => {
    await setSpiritFlixManualModelForItem(
      {
        itemId: "old-video-id",
        filePath: "/mnt/spirit-8tb/media/yes/sava/video.mkv",
        modelName: "Sava Schultz",
      },
      { rootDir },
    );

    await expect(
      getSpiritFlixManualModelForItem("new-video-id", {
        rootDir,
        lookupFilePath: "/mnt/spirit-8tb/media/yes/sava/video.mkv",
      }),
    ).resolves.toEqual(
      expect.objectContaining({
        itemId: "new-video-id",
        filePath: "/mnt/spirit-8tb/media/yes/sava/video.mkv",
        modelName: "Sava Schultz",
      }),
    );
  });

  it("merges model index aliases and profile handles into the canonical model", async () => {
    const modelIndexPath = path.join(rootDir, "model_index.json");
    await fs.writeFile(
      modelIndexPath,
      JSON.stringify({
        models: [
          {
            name: "Sendnudesx",
            slug: "sendnudesx",
            aliases: ["Sendnudes", "sendnudes"],
            profile_handles: [{ platform: "onlyfans", handle: "sendnudes" }],
          },
        ],
      }),
      "utf8",
    );

    await setSpiritFlixManualModelForItem(
      { itemId: "video-1", modelName: "Sendnudes" },
      { rootDir, modelIndexPath },
    );
    await setSpiritFlixManualModelForItem(
      { itemId: "video-2", modelName: "sendnudesx" },
      { rootDir, modelIndexPath },
    );
    const handleSave = await setSpiritFlixManualModelForItem(
      { itemId: "video-3", modelName: "sendnudes" },
      { rootDir, modelIndexPath },
    );

    expect(handleSave.record.modelName).toBe("Sendnudesx");
    await expect(getSpiritFlixManualModelIndex({ rootDir, modelIndexPath })).resolves.toEqual(
      expect.objectContaining({
        models: [expect.objectContaining({ modelName: "Sendnudesx", count: 3 })],
      }),
    );
    await expect(getSpiritFlixManualModelForItem("video-1", { rootDir })).resolves.toEqual(
      expect.objectContaining({ modelName: "Sendnudesx" }),
    );
  });

  it("preserves catalog aliases and status in restored model summaries", async () => {
    const modelIndexPath = path.join(rootDir, "model_index.json");
    await fs.writeFile(
      modelIndexPath,
      JSON.stringify({
        models: [
          {
            name: "Lexi Marvel",
            slug: "lexi-marvel",
            aliases: ["LexiMarvell"],
            status: "needs-review",
            video_count: 5,
          },
        ],
      }),
      "utf8",
    );

    await expect(getSpiritFlixManualModelIndex({ rootDir, modelIndexPath })).resolves.toEqual(
      expect.objectContaining({
        models: [
          expect.objectContaining({
            modelName: "Lexi Marvel",
            count: 0,
            catalogCount: 5,
            aliases: ["lexi-marvel", "LexiMarvell"],
            catalogStatus: "needs-review",
          }),
        ],
      }),
    );
  });

  it("canonicalizes legacy saved aliases when reading manual model records", async () => {
    const modelIndexPath = path.join(rootDir, "model_index.json");
    await fs.writeFile(
      modelIndexPath,
      JSON.stringify({
        models: [{ name: "Sendnudesx", slug: "sendnudesx", aliases: ["Sendnudes"] }],
      }),
      "utf8",
    );
    const recordPath = path.join(rootDir, "items", `${createHash("sha256").update("video-legacy").digest("hex")}.json`);
    await fs.mkdir(path.dirname(recordPath), { recursive: true });
    await fs.writeFile(
      recordPath,
      JSON.stringify({
        schema: "spiritflix-manual-model/v1",
        itemId: "video-legacy",
        modelName: "sendnudes",
        updatedAt: "2026-06-21T00:00:00.000Z",
        source: "manual",
      }),
      "utf8",
    );

    await expect(getSpiritFlixManualModelForItem("video-legacy", { rootDir, modelIndexPath })).resolves.toEqual(
      expect.objectContaining({ modelName: "Sendnudesx" }),
    );
  });

  it("matches compact alias variants with spaces and punctuation", async () => {
    const modelIndexPath = path.join(rootDir, "model_index.json");
    await fs.writeFile(
      modelIndexPath,
      JSON.stringify({
        models: [
          {
            name: "Cute Geekie",
            slug: "cute-geekie",
            aliases: ["cutefru", "cut fru", "cute fru"],
            profile_handles: [{ platform: "onlyfans", handle: "cutegeekie" }],
          },
        ],
      }),
      "utf8",
    );

    await setSpiritFlixManualModelForItem(
      { itemId: "video-1", modelName: "Cut Fru" },
      { rootDir, modelIndexPath },
    );
    await setSpiritFlixManualModelForItem(
      { itemId: "video-2", modelName: "cute-geekie" },
      { rootDir, modelIndexPath },
    );
    await setSpiritFlixManualModelForItem(
      { itemId: "video-3", modelName: "cutegeekie" },
      { rootDir, modelIndexPath },
    );

    await expect(getSpiritFlixManualModelIndex({ rootDir, modelIndexPath })).resolves.toEqual(
      expect.objectContaining({
        models: [expect.objectContaining({ modelName: "Cute Geekie", count: 3 })],
      }),
    );
  });

  it("merges corrected model spellings over old misspelled names", async () => {
    const modelIndexPath = path.join(rootDir, "model_index.json");
    await fs.writeFile(
      modelIndexPath,
      JSON.stringify({
        models: [
          {
            name: "Aaliyah Yasin",
            slug: "aaliyah-yasin",
            aliases: ["Aaliyah Yasan", "aaliyah-yasan", "aaliyah yasan"],
          },
        ],
      }),
      "utf8",
    );

    await setSpiritFlixManualModelForItem(
      { itemId: "video-1", modelName: "Aaliyah Yasan" },
      { rootDir, modelIndexPath },
    );
    await setSpiritFlixManualModelForItem(
      { itemId: "video-2", modelName: "aaliyah-yasan" },
      { rootDir, modelIndexPath },
    );

    await expect(getSpiritFlixManualModelIndex({ rootDir, modelIndexPath })).resolves.toEqual(
      expect.objectContaining({
        models: [expect.objectContaining({ modelName: "Aaliyah Yasin", count: 2 })],
      }),
    );
  });

  it("rejects empty model names", async () => {
    await expect(
      setSpiritFlixManualModelForItem({ itemId: "video-1", modelName: " " }, { rootDir }),
    ).rejects.toThrow(/empty/i);
  });
});
