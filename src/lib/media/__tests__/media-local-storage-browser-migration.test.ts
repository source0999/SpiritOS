import { describe, expect, it } from "vitest";

import type { MediaLocalStorageMigratedRecords } from "@/lib/media/media-local-storage-migration";
import { runMediaLocalStorageBrowserMigration } from "@/lib/media/media-local-storage-browser-migration";
import {
  createMediaProfileStorageKey,
  MEDIA_SELECTED_PROFILE_STORAGE_KEY,
} from "@/lib/media/media-local-storage-snapshot";

const migratedAt = "2026-05-23T20:05:00.000Z";
const migrationWriteOrder: Array<keyof MediaLocalStorageMigratedRecords> = [
  "watchlistEntries",
  "playbackProgress",
  "curationChecks",
  "playbackAcceptance",
];

function createStorage(items: Record<string, string>) {
  const writes: string[] = [];
  return {
    storage: {
      getItem: (key: string) => items[key] ?? null,
      setItem: (key: string) => {
        writes.push(key);
      },
      removeItem: (key: string) => {
        writes.push(key);
      },
    },
    writes,
  };
}

function createFakeDb() {
  const writes: Array<{
    tableName: keyof MediaLocalStorageMigratedRecords;
    recordCount: number;
  }> = [];
  const db = Object.fromEntries(
    migrationWriteOrder.map((tableName) => [
      tableName,
      {
        bulkPut: async (
          records: MediaLocalStorageMigratedRecords[typeof tableName],
        ) => {
          writes.push({
            tableName,
            recordCount: records.length,
          });
        },
      },
    ]),
  );

  return { db, writes };
}

describe("runMediaLocalStorageBrowserMigration", () => {
  it("returns unavailable when localStorage is unavailable", async () => {
    await expect(
      runMediaLocalStorageBrowserMigration({
        storage: null,
        db: null,
        migratedAt,
      }),
    ).resolves.toEqual({
      status: "unavailable",
      reason: "local-storage-unavailable",
    });
  });

  it("returns unavailable when IndexedDB/Dexie is unavailable", async () => {
    const { storage } = createStorage({});

    await expect(
      runMediaLocalStorageBrowserMigration({
        storage,
        db: null,
        migratedAt,
      }),
    ).resolves.toEqual({
      status: "unavailable",
      reason: "indexeddb-unavailable",
    });
  });

  it("keeps explicit null DB separate from default browser DB lookup", async () => {
    const { storage } = createStorage({});

    await expect(
      runMediaLocalStorageBrowserMigration({
        storage,
        db: null,
        migratedAt,
      }),
    ).resolves.toEqual({
      status: "unavailable",
      reason: "indexeddb-unavailable",
    });
  });

  it("reads localStorage state and writes migrated records when DB is available", async () => {
    const { storage, writes: storageWrites } = createStorage({
      [MEDIA_SELECTED_PROFILE_STORAGE_KEY]: JSON.stringify("friend"),
      [createMediaProfileStorageKey("friend")]: JSON.stringify({
        watchlistIds: ["movie-local-lights"],
        progress: {
          "movie-local-lights": {
            itemId: "movie-local-lights",
            seconds: 25,
            updatedAt: "2026-05-22T10:00:00.000Z",
          },
        },
      }),
    });
    const { db, writes } = createFakeDb();

    await expect(
      runMediaLocalStorageBrowserMigration({
        storage,
        db: db as never,
        migratedAt,
      }),
    ).resolves.toMatchObject({
      status: "migrated",
      plan: {
        source: "media-local-storage",
        selectedProfileId: "friend",
        migratedAt,
        skippedEntries: [],
      },
      summary: {
        source: "media-local-storage",
        selectedProfileId: "friend",
        migratedAt,
        skippedEntryCount: 0,
      },
    });
    expect(writes.map((write) => write.tableName)).toEqual(migrationWriteOrder);
    expect(writes.map((write) => write.recordCount)).toEqual([1, 1, 0, 0]);
    expect(storageWrites).toEqual([]);
  });
});
