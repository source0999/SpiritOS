import { describe, expect, it } from "vitest";

import type { MediaProfileState } from "@/components/media/media-types";
import {
  createMediaLocalStorageMigrationPlan,
  type MediaLocalStorageMigratedRecords,
} from "@/lib/media/media-local-storage-migration";
import {
  writeMediaLocalStorageMigrationPlan,
  type MediaLocalStorageMigrationWritableTables,
} from "@/lib/media/media-local-storage-migration-write";

const migratedAt = "2026-05-23T19:55:00.000Z";
const migrationWriteOrder: Array<keyof MediaLocalStorageMigratedRecords> = [
  "watchlistEntries",
  "playbackProgress",
  "curationChecks",
  "playbackAcceptance",
];

function createProfileState(
  profileState: Partial<MediaProfileState> & Pick<MediaProfileState, "profileId">,
): MediaProfileState {
  return {
    watchlistIds: [],
    progress: {},
    curationChecks: {},
    playbackAcceptance: {},
    ...profileState,
  };
}

function createWritableTableDoubles() {
  const writes: Array<{
    tableName: keyof MediaLocalStorageMigratedRecords;
    recordCount: number;
  }> = [];
  const tables = Object.fromEntries(
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
  ) as MediaLocalStorageMigrationWritableTables;

  return { tables, writes };
}

describe("writeMediaLocalStorageMigrationPlan", () => {
  it("writes migrated localStorage records in stable user-state order", async () => {
    const plan = createMediaLocalStorageMigrationPlan(
      {
        selectedProfileId: "britton",
        profileStates: [
          createProfileState({
            profileId: "britton",
            watchlistIds: ["movie-local-lights"],
            progress: {
              "movie-local-lights": {
                itemId: "movie-local-lights",
                seconds: 33,
                updatedAt: "2026-05-22T10:00:00.000Z",
              },
            },
          }),
        ],
      },
      {
        migratedAt,
        catalogItemIds: ["movie-local-lights"],
      },
    );
    const { tables, writes } = createWritableTableDoubles();

    await writeMediaLocalStorageMigrationPlan(tables, plan);

    expect(writes.map((write) => write.tableName)).toEqual(migrationWriteOrder);
    expect(writes.map((write) => write.recordCount)).toEqual([1, 1, 0, 0]);
  });

  it("returns a summary with skipped entry count", async () => {
    const plan = createMediaLocalStorageMigrationPlan(
      {
        selectedProfileId: "guest",
        profileStates: [
          createProfileState({
            profileId: "guest",
            watchlistIds: ["missing-item"],
          }),
        ],
      },
      {
        migratedAt,
        catalogItemIds: ["movie-local-lights"],
      },
    );
    const { tables } = createWritableTableDoubles();

    await expect(writeMediaLocalStorageMigrationPlan(tables, plan)).resolves.toEqual({
      source: "media-local-storage",
      selectedProfileId: "guest",
      migratedAt,
      skippedEntryCount: 1,
      entries: [
        {
          tableName: "watchlistEntries",
          recordCount: 0,
        },
        {
          tableName: "playbackProgress",
          recordCount: 0,
        },
        {
          tableName: "curationChecks",
          recordCount: 0,
        },
        {
          tableName: "playbackAcceptance",
          recordCount: 0,
        },
      ],
    });
  });

  it("does not open IndexedDB directly", async () => {
    const plan = createMediaLocalStorageMigrationPlan(
      {
        selectedProfileId: "britton",
        profileStates: [createProfileState({ profileId: "britton" })],
      },
      {
        migratedAt,
      },
    );
    const { tables } = createWritableTableDoubles();

    await writeMediaLocalStorageMigrationPlan(tables, plan);

    expect(typeof globalThis.indexedDB).toBe("undefined");
  });
});
