import fs from "node:fs/promises";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  buildPathItemKey,
  clearSpiritFlixAdminPreviewStore,
  getSmokeRoot,
  handleSpiritFlixAdminAction,
  moveSpiritFlixAdminPath,
  validateOrderItemKey,
} from "../actions";
import { SPIRITFLIX_MEDIA_ROOT } from "../constants";
import { getReceiptsDirectory } from "../receipts";

const smokeRoot = getSmokeRoot();

async function countReceiptLines(): Promise<number> {
  const receiptsDir = getReceiptsDirectory();
  const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const file = path.join(receiptsDir, `${stamp}.jsonl`);
  try {
    const raw = await fs.readFile(file, "utf8");
    return raw.split("\n").filter(Boolean).length;
  } catch {
    return 0;
  }
}

describe("SpiritFlix admin actions", () => {
  let receiptBaseline = 0;

  beforeEach(async () => {
    clearSpiritFlixAdminPreviewStore();
    await fs.mkdir(smokeRoot, { recursive: true });
    receiptBaseline = await countReceiptLines();
  });

  afterEach(async () => {
    clearSpiritFlixAdminPreviewStore();
    await fs.rm(smokeRoot, { force: true, recursive: true });
  });

  it("validates custom order item keys", () => {
    expect(validateOrderItemKey("jellyfin:abc123")).toBe(true);
    expect(validateOrderItemKey(buildPathItemKey("/mnt/spirit-8tb/media/other/test.mkv"))).toBe(true);
    expect(validateOrderItemKey("bad-key")).toBe(false);
  });

  it("previews createFolder without writing receipts", async () => {
    const preview = await handleSpiritFlixAdminAction({
      action: "createFolder",
      mode: "preview",
      parentPath: smokeRoot,
      name: "preview-only-folder",
    });

    expect(preview.allowed).toBe(true);
    expect(preview.previewId).toBeTruthy();
    expect(await countReceiptLines()).toBe(receiptBaseline);
    await expect(fs.stat(path.join(smokeRoot, "preview-only-folder"))).rejects.toThrow();
  });

  it("previews and executes create folder inside the smoke root", async () => {
    const preview = await handleSpiritFlixAdminAction({
      action: "createFolder",
      mode: "preview",
      parentPath: smokeRoot,
      name: "cursor-smoke-folder",
    });

    expect(preview.allowed).toBe(true);

    const executed = await handleSpiritFlixAdminAction({
      action: "createFolder",
      mode: "execute",
      confirmToken: preview.previewId,
      parentPath: smokeRoot,
      name: "cursor-smoke-folder",
    });

    expect(executed.allowed).toBe(true);
    expect(executed.receipt?.status).toBe("executed");
    const created = await fs.stat(path.join(smokeRoot, "cursor-smoke-folder"));
    expect(created.isDirectory()).toBe(true);
    expect(await countReceiptLines()).toBeGreaterThan(receiptBaseline);
  });

  it("previews and executes rename preserving video extension", async () => {
    const sourcePath = path.join(smokeRoot, "clip.mkv");
    await fs.writeFile(sourcePath, "smoke");

    const preview = await handleSpiritFlixAdminAction({
      action: "rename",
      mode: "preview",
      sourcePath,
      name: "cursor-smoke-renamed",
    });

    expect(preview.allowed).toBe(true);
    expect(preview.preview?.targetPath).toContain("cursor-smoke-renamed.mkv");

    const executed = await handleSpiritFlixAdminAction({
      action: "rename",
      mode: "execute",
      confirmToken: preview.previewId,
      sourcePath,
      name: "cursor-smoke-renamed",
    });

    expect(executed.allowed).toBe(true);
    await expect(fs.stat(path.join(smokeRoot, "cursor-smoke-renamed.mkv"))).resolves.toBeTruthy();
  });

  it("previews and executes move within smoke root", async () => {
    const nested = path.join(smokeRoot, "move-src");
    const dest = path.join(smokeRoot, "move-dest");
    await fs.mkdir(nested, { recursive: true });
    await fs.mkdir(dest, { recursive: true });
    const filePath = path.join(nested, "disposable.txt");
    await fs.writeFile(filePath, "move me");

    const preview = await handleSpiritFlixAdminAction({
      action: "move",
      mode: "preview",
      sourcePath: filePath,
      targetPath: dest,
    });
    expect(preview.allowed).toBe(true);

    const executed = await handleSpiritFlixAdminAction({
      action: "move",
      mode: "execute",
      confirmToken: preview.previewId,
      sourcePath: filePath,
      targetPath: dest,
    });
    expect(executed.allowed).toBe(true);
    await expect(fs.stat(path.join(dest, "disposable.txt"))).resolves.toBeTruthy();
  });

  it("softDelete moves into .trash and restore rejects overwrite", async () => {
    const filePath = path.join(smokeRoot, "trash-me.txt");
    await fs.writeFile(filePath, "trash");

    const deletePreview = await handleSpiritFlixAdminAction({
      action: "softDelete",
      mode: "preview",
      sourcePath: filePath,
    });
    expect(deletePreview.allowed).toBe(true);
    expect(deletePreview.preview?.targetPath).toContain(`${path.sep}.trash${path.sep}`);

    const deleted = await handleSpiritFlixAdminAction({
      action: "softDelete",
      mode: "execute",
      confirmToken: deletePreview.previewId,
      sourcePath: filePath,
    });
    expect(deleted.allowed).toBe(true);
    const trashPath = deleted.preview?.targetPath as string;
    await expect(fs.stat(filePath)).rejects.toThrow();

    const restorePreview = await handleSpiritFlixAdminAction({
      action: "restore",
      mode: "preview",
      sourcePath: trashPath,
    });
    expect(restorePreview.allowed).toBe(true);
    const restoreTarget = restorePreview.preview?.targetPath as string;

    await fs.writeFile(restoreTarget, "blocker");
    const blockedRestore = await handleSpiritFlixAdminAction({
      action: "restore",
      mode: "preview",
      sourcePath: trashPath,
    });
    expect(blockedRestore.allowed).toBe(false);

    await fs.rm(restoreTarget);
    const restored = await handleSpiritFlixAdminAction({
      action: "restore",
      mode: "execute",
      confirmToken: restorePreview.previewId,
      sourcePath: trashPath,
    });
    expect(restored.allowed).toBe(true);
    await expect(fs.stat(restoreTarget)).resolves.toBeTruthy();
  });

  it("moveSpiritFlixAdminPath copies then deletes when rename hits EXDEV", async () => {
    const sourcePath = path.join(smokeRoot, "exdev-source.txt");
    const targetPath = path.join(smokeRoot, "nested", "exdev-target.txt");
    await fs.mkdir(path.dirname(targetPath), { recursive: true });
    await fs.writeFile(sourcePath, "cross-device");

    const exdev = Object.assign(new Error("EXDEV: cross-device link not permitted"), { code: "EXDEV" }) as NodeJS.ErrnoException;
    const renameSpy = vi.spyOn(fs, "rename").mockRejectedValueOnce(exdev);

    await moveSpiritFlixAdminPath(sourcePath, targetPath);

    expect(renameSpy).toHaveBeenCalled();
    await expect(fs.readFile(targetPath, "utf8")).resolves.toBe("cross-device");
    await expect(fs.stat(sourcePath)).rejects.toThrow();
    renameSpy.mockRestore();
    await fs.rm(targetPath);
    await fs.rm(path.dirname(targetPath), { recursive: true, force: true });
  });

  it("writeMetadata rejects unknown fields and writes only under metadata root", async () => {
    const sourcePath = path.join(smokeRoot, "meta-target.txt");
    await fs.writeFile(sourcePath, "meta");

    const blocked = await handleSpiritFlixAdminAction({
      action: "writeMetadata",
      mode: "preview",
      sourcePath,
      metadata: { displayTitle: "ok", evilField: "nope" } as never,
    });
    expect(blocked.allowed).toBe(false);

    const preview = await handleSpiritFlixAdminAction({
      action: "writeMetadata",
      mode: "preview",
      sourcePath,
      metadata: { displayTitle: "Smoke title", notes: "disposable" },
    });
    expect(preview.allowed).toBe(true);
    expect(preview.preview?.targetPath).toContain(`${path.sep}.spiritflix-admin${path.sep}metadata${path.sep}`);

    const executed = await handleSpiritFlixAdminAction({
      action: "writeMetadata",
      mode: "execute",
      confirmToken: preview.previewId,
      sourcePath,
      metadata: { displayTitle: "Smoke title", notes: "disposable" },
    });
    expect(executed.allowed).toBe(true);
    expect(executed.preview?.targetPath).not.toContain(smokeRoot);
  });

  it("saveOrder validates stable keys and writes order.json", async () => {
    const key = buildPathItemKey(path.join(smokeRoot, "order-item.txt"));
    const blocked = await handleSpiritFlixAdminAction({
      action: "saveOrder",
      mode: "preview",
      order: { version: 1, updatedAt: new Date().toISOString(), groups: [{ id: "g1", name: "G", itemKeys: ["bad"] }] },
    });
    expect(blocked.allowed).toBe(false);

    const preview = await handleSpiritFlixAdminAction({
      action: "saveOrder",
      mode: "preview",
      order: { version: 1, updatedAt: new Date().toISOString(), groups: [{ id: "g1", name: "Smoke", itemKeys: [key] }] },
    });
    expect(preview.allowed).toBe(true);

    const executed = await handleSpiritFlixAdminAction({
      action: "saveOrder",
      mode: "execute",
      confirmToken: preview.previewId,
      order: { version: 1, updatedAt: new Date().toISOString(), groups: [{ id: "g1", name: "Smoke", itemKeys: [key] }] },
    });
    expect(executed.allowed).toBe(true);
    expect(executed.preview?.targetPath).toContain("order.json");
  });

  it("rejects path traversal and outside roots", async () => {
    const traversal = await handleSpiritFlixAdminAction({
      action: "rename",
      mode: "preview",
      sourcePath: `${smokeRoot}/../outside`,
      name: "blocked",
    });
    expect(traversal.allowed).toBe(false);

    const outside = await handleSpiritFlixAdminAction({
      action: "rename",
      mode: "preview",
      sourcePath: "/etc/passwd",
      name: "blocked",
    });
    expect(outside.allowed).toBe(false);
  });

  it("rejects protected media root destructive actions", async () => {
    const blocked = await handleSpiritFlixAdminAction({
      action: "softDelete",
      mode: "preview",
      sourcePath: SPIRITFLIX_MEDIA_ROOT,
    });
    expect(blocked.allowed).toBe(false);
    expect(blocked.message).toMatch(/protected/i);

    const blockedLibrary = await handleSpiritFlixAdminAction({
      action: "rename",
      mode: "preview",
      sourcePath: `${SPIRITFLIX_MEDIA_ROOT}/yes`,
      name: "renamed-yes",
    });
    expect(blockedLibrary.allowed).toBe(false);
  });

  it("requires preview token before execute", async () => {
    const executed = await handleSpiritFlixAdminAction({
      action: "createFolder",
      mode: "execute",
      confirmToken: "missing-token",
      parentPath: smokeRoot,
      name: "no-preview",
    });
    expect(executed.allowed).toBe(false);
  });

  it("gates Jellyfin rescan when credentials are unavailable", async () => {
    const originalKey = process.env.JELLYFIN_API_KEY;
    delete process.env.JELLYFIN_API_KEY;
    const preview = await handleSpiritFlixAdminAction({
      action: "requestJellyfinRescan",
      mode: "preview",
      rescanPath: smokeRoot,
    });
    if (originalKey) process.env.JELLYFIN_API_KEY = originalKey;
    expect(preview.allowed).toBe(false);
    expect(preview.message).toMatch(/not active yet/i);
  });
});
