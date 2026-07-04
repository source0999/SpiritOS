import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createSpiritFlixOrganizeReceipt } from "../organize-bridge";

describe("SpiritFlix organize bridge", () => {
  let mediaRoot = "";
  let videoPath = "";

  beforeEach(async () => {
    mediaRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-organize-"));
    await fs.mkdir(path.join(mediaRoot, "yes"), { recursive: true });
    videoPath = path.join(mediaRoot, "yes", "clip.mp4");
    await fs.writeFile(videoPath, "video");
  });

  afterEach(async () => {
    await fs.rm(mediaRoot, { recursive: true, force: true });
  });

  it("creates a duplicate-safe preview receipt without moving source media", async () => {
    await fs.mkdir(path.join(mediaRoot, "yes", "Sava Schultz"), { recursive: true });
    await fs.writeFile(path.join(mediaRoot, "yes", "Sava Schultz", "clip.mp4"), "existing");

    const receipt = await createSpiritFlixOrganizeReceipt({
      mediaRoot,
      videoPath,
      matchedModel: "Sava Schultz",
      confidence: 0.94,
      mode: "preview",
    });

    expect(receipt).toEqual(expect.objectContaining({
      schema: "spiritflix-organize-receipt/v1",
      mode: "preview",
      allowed: true,
      duplicateTarget: true,
      sourcePath: videoPath,
      reasonCode: "high_confidence_preview_ready",
    }));
    expect(receipt.targetPath).toBe(path.join(mediaRoot, "yes", "Sava Schultz", "clip (2).mp4"));
    expect(await fs.readFile(videoPath, "utf8")).toBe("video");
    expect(receipt.rollback).toEqual({ moveBackTo: videoPath, removeCreatedTarget: receipt.targetPath });
  });

  it("can execute safely on a temp fixture and records after/rollback state", async () => {
    const receipt = await createSpiritFlixOrganizeReceipt({
      mediaRoot,
      videoPath,
      matchedModel: "Sava Schultz",
      confidence: 0.94,
      mode: "execute",
    });

    expect(receipt.after).toEqual({ sourceExists: false, targetExists: true });
    expect(await fs.readFile(receipt.targetPath, "utf8")).toBe("video");
    await fs.rename(receipt.targetPath, receipt.rollback.moveBackTo);
    expect(await fs.readFile(videoPath, "utf8")).toBe("video");
  });

  it("does not allow low-confidence organize execution", async () => {
    const receipt = await createSpiritFlixOrganizeReceipt({
      mediaRoot,
      videoPath,
      matchedModel: "Maybe Model",
      confidence: 0.2,
      mode: "execute",
    });

    expect(receipt.allowed).toBe(false);
    expect(receipt.after).toBeUndefined();
    expect(await fs.readFile(videoPath, "utf8")).toBe("video");
  });
});
