import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { SPIRITFLIX_MEDIA_ROOT } from "../constants";
import { getSpiritFlixAdminAllowedRoots, resolveSpiritFlixAdminPath } from "../paths";
import {
  assertWritableSpiritFlixAdminPath,
  isProtectedSpiritFlixAdminPath,
} from "../path-rules";

let tempRoot = "";
let originalRoots: string | undefined;

describe("SpiritFlix admin path safety", () => {
  beforeEach(async () => {
    originalRoots = process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-admin-"));
    process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = tempRoot;
  });

  afterEach(async () => {
    if (originalRoots === undefined) {
      delete process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS;
    } else {
      process.env.SPIRITFLIX_ADMIN_ALLOWED_ROOTS = originalRoots;
    }
    await fs.rm(tempRoot, { force: true, recursive: true });
  });

  it("uses the configured allowlisted roots", () => {
    expect(getSpiritFlixAdminAllowedRoots()).toEqual([path.resolve(tempRoot)]);
  });

  it("rejects path traversal before resolving the target", async () => {
    await expect(resolveSpiritFlixAdminPath(`${tempRoot}${path.sep}..${path.sep}outside`)).rejects.toThrow(/traversal/i);
  });

  it("rejects absolute paths outside the allowlisted root", async () => {
    const outside = await fs.mkdtemp(path.join(os.tmpdir(), "spiritflix-outside-"));
    await expect(resolveSpiritFlixAdminPath(outside)).rejects.toThrow(/outside/i);
    await fs.rm(outside, { force: true, recursive: true });
  });

  it("rejects hidden system segments under an allowed root", async () => {
    const hidden = path.join(tempRoot, ".env");
    await fs.writeFile(hidden, "SECRET=blocked");
    await expect(resolveSpiritFlixAdminPath(hidden)).rejects.toThrow(/hidden/i);
  });

  it("marks protected library roots", () => {
    expect(isProtectedSpiritFlixAdminPath(SPIRITFLIX_MEDIA_ROOT)).toBe(true);
    expect(isProtectedSpiritFlixAdminPath(`${SPIRITFLIX_MEDIA_ROOT}/yes`)).toBe(true);
    expect(isProtectedSpiritFlixAdminPath(`${SPIRITFLIX_MEDIA_ROOT}/yes/nested`)).toBe(false);
  });

  it("blocks destructive operations on protected roots", () => {
    expect(() => assertWritableSpiritFlixAdminPath(`${SPIRITFLIX_MEDIA_ROOT}/movies`, "rename")).toThrow(/protected/i);
    expect(() => assertWritableSpiritFlixAdminPath("/var/lib/jellyfin/config/system.xml", "move")).toThrow(/Jellyfin system/i);
  });
});
