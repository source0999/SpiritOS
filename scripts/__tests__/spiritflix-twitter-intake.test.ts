import { describe, expect, it } from "vitest";
import {
  DEFAULT_LIBRARY_DIR,
  isIgnoredTempFile,
  sanitizeLibraryFilename,
} from "../spiritflix-twitter-intake.mjs";

describe("spiritflix-twitter-intake guardrails", () => {
  it("imports Twitter videos into the existing videos from x folder", () => {
    expect(DEFAULT_LIBRARY_DIR).toBe("/mnt/spirit-8tb/media/yes/videos from x");
    expect(DEFAULT_LIBRARY_DIR).not.toBe("/mnt/spirit-8tb/media/yes/videos");
  });

  it("ignores incomplete downloader artifacts", () => {
    expect(isIgnoredTempFile("/mnt/spirit-8tb/media/tempTwitter/file.mp4.part")).toBe(true);
    expect(isIgnoredTempFile("/mnt/spirit-8tb/media/tempTwitter/file.mp4.ytdl")).toBe(true);
    expect(isIgnoredTempFile("/mnt/spirit-8tb/media/tempTwitter/file.mp4.part-Frag25.part")).toBe(true);
    expect(isIgnoredTempFile("/mnt/spirit-8tb/media/tempTwitter/file.fhls-1095.mp4")).toBe(true);
    expect(isIgnoredTempFile("/mnt/spirit-8tb/media/tempTwitter/file.fhls-audio-128000-Audio.mp4")).toBe(true);
    expect(isIgnoredTempFile("/mnt/spirit-8tb/media/tempTwitter/file.mp4")).toBe(false);
  });

  it("sanitizes library filenames and always writes MP4", () => {
    expect(sanitizeLibraryFilename('bad:name?.mkv')).toBe("bad name.mp4");
    expect(sanitizeLibraryFilename("already fine.mp4")).toBe("already fine.mp4");
  });
});
