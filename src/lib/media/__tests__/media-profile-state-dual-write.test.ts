import { describe, expect, it } from "vitest";

import {
  writeProfileCurationCheckBestEffort,
  writeProfilePlaybackAcceptanceBestEffort,
  writeProfilePlaybackProgressBestEffort,
  writeProfileWatchlistEntryBestEffort,
} from "@/lib/media/media-profile-state-dual-write";

describe("media-profile-state-dual-write", () => {
  it("keeps localStorage marked written when Dexie is unavailable", async () => {
    await expect(
      writeProfileWatchlistEntryBestEffort(
        "britton",
        "movie-local-lights",
        true,
        "2026-05-23T20:55:00.000Z",
      ),
    ).resolves.toEqual({
      localStorage: "written",
      dexie: {
        status: "unavailable",
        reason: "indexeddb-unavailable",
      },
    });
  });

  it("skips missing derived records while preserving local write status", async () => {
    await expect(
      writeProfilePlaybackProgressBestEffort("britton", undefined),
    ).resolves.toEqual({
      localStorage: "written",
      dexie: {
        status: "skipped",
      },
    });
    await expect(
      writeProfileCurationCheckBestEffort("britton", undefined),
    ).resolves.toEqual({
      localStorage: "written",
      dexie: {
        status: "skipped",
      },
    });
    await expect(
      writeProfilePlaybackAcceptanceBestEffort("britton", undefined),
    ).resolves.toEqual({
      localStorage: "written",
      dexie: {
        status: "skipped",
      },
    });
  });

  it("does not open IndexedDB directly in Node", async () => {
    await writeProfileWatchlistEntryBestEffort(
      "britton",
      "movie-local-lights",
      true,
      "2026-05-23T20:55:00.000Z",
    );

    expect(typeof globalThis.indexedDB).toBe("undefined");
  });
});
