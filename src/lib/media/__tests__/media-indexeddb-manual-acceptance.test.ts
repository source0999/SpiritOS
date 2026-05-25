import { describe, expect, it } from "vitest";

import { MEDIA_DB_SEED_ORDER } from "@/lib/media/media-db-seed";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";
import type { MediaLocalStorageMigratedRecords } from "@/lib/media/media-local-storage-migration";
import { createMediaIndexedDbManualAcceptanceReport } from "@/lib/media/media-indexeddb-manual-acceptance";
import {
  createMediaProfileStorageKey,
  MEDIA_SELECTED_PROFILE_STORAGE_KEY,
} from "@/lib/media/media-local-storage-snapshot";

const checkedAt = "2026-05-23T20:20:00.000Z";
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
    tableName: keyof DurableMediaLibraryRecords | keyof MediaLocalStorageMigratedRecords;
    recordCount: number;
  }> = [];
  const tableNames = Array.from(
    new Set([...MEDIA_DB_SEED_ORDER, ...migrationWriteOrder]),
  );
  const db = Object.fromEntries(
    tableNames.map((tableName) => [
      tableName,
      {
        bulkPut: async (records: unknown[]) => {
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

describe("createMediaIndexedDbManualAcceptanceReport", () => {
  it("reports needs-browser-run when IndexedDB is unavailable", async () => {
    const { storage } = createStorage({});

    await expect(
      createMediaIndexedDbManualAcceptanceReport({
        storage,
        db: null,
        checkedAt,
      }),
    ).resolves.toMatchObject({
      source: "media-indexeddb-manual-acceptance",
      checkedAt,
      status: "needs-browser-run",
      seedResult: {
        status: "unavailable",
        reason: "indexeddb-unavailable",
      },
      migrationResult: {
        status: "unavailable",
        reason: "indexeddb-unavailable",
      },
      checklist: {
        metadataSeeded: false,
        profileStateMigrated: false,
        skippedEntriesReviewed: true,
        localStoragePreserved: true,
      },
    });
  });

  it("allows omitted dependencies to use browser defaults", async () => {
    await expect(
      createMediaIndexedDbManualAcceptanceReport({
        checkedAt,
      }),
    ).resolves.toMatchObject({
      status: "needs-browser-run",
      seedResult: {
        status: "unavailable",
        reason: "indexeddb-unavailable",
      },
    });
  });

  it("passes when metadata seed and profile-state migration both succeed", async () => {
    const { storage, writes: storageWrites } = createStorage({
      [MEDIA_SELECTED_PROFILE_STORAGE_KEY]: JSON.stringify("britton"),
      [createMediaProfileStorageKey("britton")]: JSON.stringify({
        watchlistIds: ["movie-local-lights"],
      }),
    });
    const { db, writes } = createFakeDb();

    await expect(
      createMediaIndexedDbManualAcceptanceReport({
        storage,
        db: db as never,
        checkedAt,
      }),
    ).resolves.toMatchObject({
      source: "media-indexeddb-manual-acceptance",
      checkedAt,
      status: "passed",
      seedResult: {
        status: "seeded",
      },
      migrationResult: {
        status: "migrated",
      },
      checklist: {
        metadataSeeded: true,
        profileStateMigrated: true,
        skippedEntriesReviewed: true,
        localStoragePreserved: true,
      },
    });
    expect(writes.map((write) => write.tableName)).toEqual([
      ...MEDIA_DB_SEED_ORDER,
      ...migrationWriteOrder,
    ]);
    expect(storageWrites).toEqual([]);
  });

  it("blocks acceptance when migration reports skipped entries", async () => {
    const { storage } = createStorage({
      [MEDIA_SELECTED_PROFILE_STORAGE_KEY]: JSON.stringify("guest"),
      [createMediaProfileStorageKey("guest")]: JSON.stringify({
        watchlistIds: ["unknown-item"],
      }),
    });
    const { db } = createFakeDb();

    const report = await createMediaIndexedDbManualAcceptanceReport({
      storage,
      db: db as never,
      checkedAt,
    });

    expect(report.status).toBe("blocked");
    expect(report.checklist).toEqual({
      metadataSeeded: true,
      profileStateMigrated: true,
      skippedEntriesReviewed: false,
      localStoragePreserved: true,
    });
  });
});
