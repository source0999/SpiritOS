import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  canonicalizeSpiritFlixManualTag,
  findSpiritFlixManualTaggedItems,
  getSpiritFlixManualTagIndex,
  getSpiritFlixManualTagsForItem,
  getSpiritFlixManualTagScope,
  applySpiritFlixModelScopedTagChanges,
  setSpiritFlixManualTagsForItem,
} from "../manual-tags";

describe("SpiritFlix manual tags", () => {
  let rootDir: string;

  beforeEach(async () => {
    rootDir = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-manual-tags-"));
  });

  afterEach(async () => {
    await fs.rm(rootDir, { recursive: true, force: true });
  });

  it("canonicalizes user-entered tags", () => {
    expect(canonicalizeSpiritFlixManualTag("  Big   Ass  ")).toBe("big ass");
  });

  it("classifies model descriptor tags separately from video action tags", () => {
    expect(getSpiritFlixManualTagScope("big ass")).toBe("model");
    expect(getSpiritFlixManualTagScope("curvy")).toBe("model");
    expect(getSpiritFlixManualTagScope("asian")).toBe("model");
    expect(getSpiritFlixManualTagScope("white")).toBe("model");
    expect(getSpiritFlixManualTagScope("paki")).toBe("model");
    expect(getSpiritFlixManualTagScope("pakistani")).toBe("model");
    expect(getSpiritFlixManualTagScope("middle eastern")).toBe("model");
    expect(getSpiritFlixManualTagScope("south asian")).toBe("model");
    expect(getSpiritFlixManualTagScope("southeast asian")).toBe("model");
    expect(getSpiritFlixManualTagScope("filipina")).toBe("model");
    expect(getSpiritFlixManualTagScope("eyes")).toBe("model");
    expect(getSpiritFlixManualTagScope("big tits brunette")).toBe("model");
    expect(getSpiritFlixManualTagScope("backshot")).toBe("video");
    expect(getSpiritFlixManualTagScope("public")).toBe("video");
    expect(getSpiritFlixManualTagScope("feet")).toBe("video");
    expect(getSpiritFlixManualTagScope("handjob")).toBe("video");
    expect(getSpiritFlixManualTagScope("hijab")).toBe("video");
    expect(getSpiritFlixManualTagScope("white handjob")).toBe("video");
    expect(getSpiritFlixManualTagScope("blowjob")).toBe("video");
  });

  it("adds and toggles manual tags without overwriting smart metadata sidecars", async () => {
    const first = await setSpiritFlixManualTagsForItem(
      {
        itemId: "video-1",
        filePath: "/mnt/spirit-8tb/media/yes/model/video.mkv",
        manualTags: ["Busty", " wet   noises "],
      },
      { rootDir },
    );

    expect(first.record.manualTags).toEqual(["busty", "wet noises"]);
    expect(first.addedTags).toEqual(["busty", "wet noises"]);
    expect(first.removedTags).toEqual([]);

    const second = await setSpiritFlixManualTagsForItem(
      {
        itemId: "video-1",
        manualTags: ["busty"],
      },
      { rootDir },
    );

    expect(second.previousManualTags).toEqual(["busty", "wet noises"]);
    expect(second.record.manualTags).toEqual(["busty"]);
    expect(second.removedTags).toEqual(["wet noises"]);
    expect(await getSpiritFlixManualTagsForItem("video-1", { rootDir })).toEqual(
      expect.objectContaining({
        itemId: "video-1",
        filePath: "/mnt/spirit-8tb/media/yes/model/video.mkv",
        manualTags: ["busty"],
        source: "manual",
      }),
    );
  });

  it("rejects empty and duplicate malformed tags", async () => {
    await expect(
      setSpiritFlixManualTagsForItem({ itemId: "video-1", manualTags: [" "] }, { rootDir }),
    ).rejects.toThrow(/empty/i);
    await expect(
      setSpiritFlixManualTagsForItem({ itemId: "video-1", manualTags: ["blowjob", " Blowjob "] }, { rootDir }),
    ).rejects.toThrow(/duplicates/i);
  });

  it("builds a starter-tag index and filters tagged items", async () => {
    await setSpiritFlixManualTagsForItem({ itemId: "video-1", manualTags: ["busty"] }, { rootDir });
    await setSpiritFlixManualTagsForItem({ itemId: "video-2", manualTags: ["busty", "asmr"] }, { rootDir });

    const index = await getSpiritFlixManualTagIndex({ rootDir });
    expect(index.tags).not.toEqual(expect.arrayContaining([expect.objectContaining({ tag: "curvy" })]));
    expect(index.tags).toEqual(expect.arrayContaining([expect.objectContaining({ tag: "backshot", count: 0 })]));
    expect(index.tags).toEqual(expect.arrayContaining([expect.objectContaining({ tag: "asmr", count: 1 })]));
    expect(index.modelAttributes).toEqual(expect.arrayContaining([expect.objectContaining({ tag: "busty", count: 2 })]));

    await expect(findSpiritFlixManualTaggedItems("asmr", { rootDir })).resolves.toHaveLength(1);
    await expect(findSpiritFlixManualTaggedItems("busty", { rootDir })).resolves.toHaveLength(0);
  });

  it("propagates model attributes to related videos without putting them in the action index", async () => {
    await setSpiritFlixManualTagsForItem({ itemId: "video-1", manualTags: ["big ass", "feet", "handjob"] }, { rootDir });
    await applySpiritFlixModelScopedTagChanges(
      [{ itemId: "video-2" }, { itemId: "video-3" }],
      ["big ass", "feet", "handjob"],
      [],
      { rootDir },
    );

    await expect(getSpiritFlixManualTagsForItem("video-2", { rootDir })).resolves.toEqual(
      expect.objectContaining({ manualTags: ["big ass"] }),
    );
    await expect(getSpiritFlixManualTagsForItem("video-3", { rootDir })).resolves.toEqual(
      expect.objectContaining({ manualTags: ["big ass"] }),
    );
    await expect(getSpiritFlixManualTagIndex({ rootDir })).resolves.toEqual(
      expect.objectContaining({
        tags: expect.not.arrayContaining([expect.objectContaining({ tag: "big ass" })]),
        modelAttributes: expect.arrayContaining([expect.objectContaining({ tag: "big ass" })]),
      }),
    );
  });

  it("rebuilds the global index from sidecars so custom tags cannot stay hidden", async () => {
    await setSpiritFlixManualTagsForItem({ itemId: "video-1", manualTags: ["cumshot"] }, { rootDir });
    await fs.writeFile(
      path.join(rootDir, "index.json"),
      `${JSON.stringify({
        schema: "spiritflix-manual-tag-index/v1",
        updatedAt: "2026-06-20T00:00:00.000Z",
        tags: [{ tag: "blowjob", label: "blowjob", count: 1 }],
      })}\n`,
      "utf8",
    );

    await expect(getSpiritFlixManualTagIndex({ rootDir })).resolves.toEqual(
      expect.objectContaining({
        tags: expect.arrayContaining([expect.objectContaining({ tag: "cumshot", count: 1 })]),
      }),
    );
  });
});
