import { describe, expect, it } from "vitest";
import {
  SPIRITFLIX_ADMIN_NAV,
  SPIRITFLIX_MEDIA_INBOX,
  SPIRITFLIX_MEDIA_ROOT,
} from "../constants";
import { computeThumbnailCacheKey, isVideoThumbnailExtension } from "../thumbnail";

describe("SpiritFlix admin thumbnail helpers", () => {
  it("recognizes supported video extensions", () => {
    expect(isVideoThumbnailExtension(".mp4")).toBe(true);
    expect(isVideoThumbnailExtension(".MKV")).toBe(true);
    expect(isVideoThumbnailExtension(".json")).toBe(false);
  });

  it("builds deterministic cache keys from path size and mtime", () => {
    const left = computeThumbnailCacheKey("/mnt/spirit-8tb/media/yes/clip.mp4", 1024, 1710000000000);
    const right = computeThumbnailCacheKey("/mnt/spirit-8tb/media/yes/clip.mp4", 1024, 1710000000000);
    const changed = computeThumbnailCacheKey("/mnt/spirit-8tb/media/yes/clip.mp4", 2048, 1710000000000);
    expect(left).toBe(right);
    expect(left).not.toBe(changed);
  });
});

describe("SpiritFlix admin nav path mapping", () => {
  it("maps media root and library folders to expected absolute paths", () => {
    const byLabel = Object.fromEntries(SPIRITFLIX_ADMIN_NAV.map((entry) => [entry.label, entry.path]));
    expect(byLabel.media).toBe(SPIRITFLIX_MEDIA_ROOT);
    expect(byLabel.yes).toBe(`${SPIRITFLIX_MEDIA_ROOT}/yes`);
    expect(byLabel.anime).toBe(`${SPIRITFLIX_MEDIA_ROOT}/anime`);
    expect(byLabel.movies).toBe(`${SPIRITFLIX_MEDIA_ROOT}/movies`);
    expect(byLabel.tv).toBe(`${SPIRITFLIX_MEDIA_ROOT}/tv`);
    expect(byLabel.music).toBe(`${SPIRITFLIX_MEDIA_ROOT}/music`);
    expect(byLabel.other).toBe(`${SPIRITFLIX_MEDIA_ROOT}/other`);
    expect(byLabel["media-inbox"]).toBe(SPIRITFLIX_MEDIA_INBOX);
  });
});
