import { describe, expect, it } from "vitest";

import {
  writeMediaProfileCurationCheckWhenAvailable,
  writeMediaProfilePlaybackAcceptanceWhenAvailable,
  writeMediaProfilePlaybackProgressWhenAvailable,
  writeMediaProfileWatchlistEntryWhenAvailable,
} from "@/lib/media/media-profile-state-browser-write";

function createFakeDb() {
  const writes: Array<{
    tableName: string;
    action: "put" | "delete";
    payload: unknown;
  }> = [];

  return {
    db: {
      watchlistEntries: {
        put: async (record: unknown) => {
          writes.push({
            tableName: "watchlistEntries",
            action: "put",
            payload: record,
          });
        },
        delete: async (key: unknown) => {
          writes.push({
            tableName: "watchlistEntries",
            action: "delete",
            payload: key,
          });
        },
      },
      playbackProgress: {
        put: async (record: unknown) => {
          writes.push({
            tableName: "playbackProgress",
            action: "put",
            payload: record,
          });
        },
      },
      curationChecks: {
        put: async (record: unknown) => {
          writes.push({
            tableName: "curationChecks",
            action: "put",
            payload: record,
          });
        },
      },
      playbackAcceptance: {
        put: async (record: unknown) => {
          writes.push({
            tableName: "playbackAcceptance",
            action: "put",
            payload: record,
          });
        },
      },
    },
    writes,
  };
}

describe("media-profile-state-browser-write", () => {
  it("returns unavailable when IndexedDB/Dexie is not available", async () => {
    await expect(
      writeMediaProfileWatchlistEntryWhenAvailable(
        "britton",
        "movie-local-lights",
        true,
        "2026-05-23T20:40:00.000Z",
        null,
      ),
    ).resolves.toEqual({
      status: "unavailable",
      reason: "indexeddb-unavailable",
    });
  });

  it("writes Watchlist changes when a DB boundary is available", async () => {
    const { db, writes } = createFakeDb();

    await expect(
      writeMediaProfileWatchlistEntryWhenAvailable(
        "britton",
        "movie-local-lights",
        true,
        "2026-05-23T20:40:00.000Z",
        db as never,
      ),
    ).resolves.toMatchObject({
      status: "written",
      summary: {
        tableName: "watchlistEntries",
        action: "put",
      },
    });
    expect(writes).toHaveLength(1);
  });

  it("writes progress, curation, and playback acceptance when available", async () => {
    const { db, writes } = createFakeDb();

    await writeMediaProfilePlaybackProgressWhenAvailable(
      "friend",
      {
        itemId: "movie-local-lights",
        seconds: 14,
        updatedAt: "2026-05-23T20:41:00.000Z",
      },
      db as never,
    );
    await writeMediaProfileCurationCheckWhenAvailable(
      "friend",
      {
        itemId: "movie-local-lights",
        authorizedFileConfirmed: true,
        updatedAt: "2026-05-23T20:42:00.000Z",
      },
      db as never,
    );
    await writeMediaProfilePlaybackAcceptanceWhenAvailable(
      "friend",
      {
        itemId: "movie-local-lights",
        sourceReadyConfirmed: true,
        refreshProgressConfirmed: false,
        profileIsolationConfirmed: true,
        updatedAt: "2026-05-23T20:43:00.000Z",
      },
      db as never,
    );

    expect(writes.map((write) => write.tableName)).toEqual([
      "playbackProgress",
      "curationChecks",
      "playbackAcceptance",
    ]);
  });
});
