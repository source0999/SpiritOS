import { describe, expect, it } from "vitest";

import {
  createMediaProfileStorageKey,
  MEDIA_SELECTED_PROFILE_STORAGE_KEY,
  readMediaLocalStorageSnapshot,
} from "@/lib/media/media-local-storage-snapshot";

function createStorage(items: Record<string, string>) {
  return {
    getItem: (key: string) => items[key] ?? null,
  };
}

describe("readMediaLocalStorageSnapshot", () => {
  it("reads selected profile and profile states from storage keys", () => {
    const storage = createStorage({
      [MEDIA_SELECTED_PROFILE_STORAGE_KEY]: JSON.stringify("friend"),
      [createMediaProfileStorageKey("friend")]: JSON.stringify({
        watchlistIds: ["movie-local-lights"],
        progress: {
          "movie-local-lights": {
            itemId: "movie-local-lights",
            seconds: 20,
            updatedAt: "2026-05-22T10:00:00.000Z",
          },
        },
      }),
    });

    expect(readMediaLocalStorageSnapshot(storage, ["britton", "friend"])).toEqual({
      selectedProfileId: "friend",
      profileStates: [
        {
          profileId: "britton",
          watchlistIds: [],
          progress: {},
          curationChecks: {},
          playbackAcceptance: {},
        },
        {
          profileId: "friend",
          watchlistIds: ["movie-local-lights"],
          progress: {
            "movie-local-lights": {
              itemId: "movie-local-lights",
              seconds: 20,
              updatedAt: "2026-05-22T10:00:00.000Z",
            },
          },
          curationChecks: {},
          playbackAcceptance: {},
        },
      ],
    });
  });

  it("falls back to empty profile states when storage is missing or invalid", () => {
    const storage = createStorage({
      [MEDIA_SELECTED_PROFILE_STORAGE_KEY]: "not-json",
      [createMediaProfileStorageKey("guest")]: "not-json",
    });

    expect(readMediaLocalStorageSnapshot(storage, ["guest"], "guest")).toEqual({
      selectedProfileId: "guest",
      profileStates: [
        {
          profileId: "guest",
          watchlistIds: [],
          progress: {},
          curationChecks: {},
          playbackAcceptance: {},
        },
      ],
    });
  });

  it("does not mutate localStorage keys", () => {
    const writes: string[] = [];
    const storage = {
      getItem: () => null,
      setItem: (key: string) => {
        writes.push(key);
      },
      removeItem: (key: string) => {
        writes.push(key);
      },
    };

    readMediaLocalStorageSnapshot(storage, ["britton"]);

    expect(writes).toEqual([]);
  });
});
