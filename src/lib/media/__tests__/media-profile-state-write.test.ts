import { describe, expect, it } from "vitest";

import {
  writeMediaProfileCurationCheck,
  writeMediaProfilePlaybackAcceptance,
  writeMediaProfilePlaybackProgress,
  writeMediaProfileWatchlistEntry,
  type MediaProfileStateWritableTables,
} from "@/lib/media/media-profile-state-write";

function createWritableTableDoubles() {
  const writes: Array<{
    tableName: string;
    action: "put" | "delete";
    payload: unknown;
  }> = [];
  const tables: MediaProfileStateWritableTables = {
    watchlistEntries: {
      put: async (record) => {
        writes.push({
          tableName: "watchlistEntries",
          action: "put",
          payload: record,
        });
      },
      delete: async (key) => {
        writes.push({
          tableName: "watchlistEntries",
          action: "delete",
          payload: key,
        });
      },
    },
    playbackProgress: {
      put: async (record) => {
        writes.push({
          tableName: "playbackProgress",
          action: "put",
          payload: record,
        });
      },
    },
    curationChecks: {
      put: async (record) => {
        writes.push({
          tableName: "curationChecks",
          action: "put",
          payload: record,
        });
      },
    },
    playbackAcceptance: {
      put: async (record) => {
        writes.push({
          tableName: "playbackAcceptance",
          action: "put",
          payload: record,
        });
      },
    },
  };

  return { tables, writes };
}

describe("media-profile-state-write", () => {
  it("puts and deletes Watchlist entries", async () => {
    const { tables, writes } = createWritableTableDoubles();

    await expect(
      writeMediaProfileWatchlistEntry(
        tables,
        "britton",
        "movie-local-lights",
        true,
        "2026-05-23T20:30:00.000Z",
      ),
    ).resolves.toEqual({
      tableName: "watchlistEntries",
      action: "put",
      profileId: "britton",
      catalogItemId: "movie-local-lights",
    });
    await expect(
      writeMediaProfileWatchlistEntry(
        tables,
        "britton",
        "movie-local-lights",
        false,
        "2026-05-23T20:30:00.000Z",
      ),
    ).resolves.toEqual({
      tableName: "watchlistEntries",
      action: "delete",
      profileId: "britton",
      catalogItemId: "movie-local-lights",
    });

    expect(writes).toEqual([
      {
        tableName: "watchlistEntries",
        action: "put",
        payload: {
          profileId: "britton",
          catalogItemId: "movie-local-lights",
          createdAt: "2026-05-23T20:30:00.000Z",
        },
      },
      {
        tableName: "watchlistEntries",
        action: "delete",
        payload: ["britton", "movie-local-lights"],
      },
    ]);
  });

  it("writes rounded playback progress", async () => {
    const { tables, writes } = createWritableTableDoubles();

    await expect(
      writeMediaProfilePlaybackProgress(tables, "friend", {
        itemId: "movie-local-lights",
        seconds: 45.8,
        updatedAt: "2026-05-23T20:31:00.000Z",
      }),
    ).resolves.toEqual({
      tableName: "playbackProgress",
      action: "put",
      profileId: "friend",
      catalogItemId: "movie-local-lights",
      seconds: 45,
    });

    expect(writes[0]).toEqual({
      tableName: "playbackProgress",
      action: "put",
      payload: {
        profileId: "friend",
        catalogItemId: "movie-local-lights",
        seconds: 45,
        updatedAt: "2026-05-23T20:31:00.000Z",
      },
    });
  });

  it("writes curation checks and playback acceptance evidence", async () => {
    const { tables, writes } = createWritableTableDoubles();

    await expect(
      writeMediaProfileCurationCheck(tables, "guest", {
        itemId: "movie-local-lights",
        authorizedFileConfirmed: true,
        updatedAt: "2026-05-23T20:32:00.000Z",
      }),
    ).resolves.toEqual({
      tableName: "curationChecks",
      action: "put",
      profileId: "guest",
      catalogItemId: "movie-local-lights",
      authorizedFileConfirmed: true,
    });
    await expect(
      writeMediaProfilePlaybackAcceptance(tables, "guest", {
        itemId: "movie-local-lights",
        sourceReadyConfirmed: true,
        refreshProgressConfirmed: true,
        profileIsolationConfirmed: true,
        updatedAt: "2026-05-23T20:33:00.000Z",
      }),
    ).resolves.toEqual({
      tableName: "playbackAcceptance",
      action: "put",
      profileId: "guest",
      catalogItemId: "movie-local-lights",
      complete: true,
    });

    expect(writes.map((write) => write.tableName)).toEqual([
      "curationChecks",
      "playbackAcceptance",
    ]);
  });

  it("does not open IndexedDB directly", async () => {
    const { tables } = createWritableTableDoubles();

    await writeMediaProfileWatchlistEntry(
      tables,
      "britton",
      "movie-local-lights",
      true,
      "2026-05-23T20:30:00.000Z",
    );

    expect(typeof globalThis.indexedDB).toBe("undefined");
  });
});
